"""Reply lifecycle. A transaction lock prevents duplicate provider calls per case."""

import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from . import (
    assistant,
    conversation,
    corpus,
    document_scope,
    manual_figures,
    manual_library,
)
from .models import AssistantReply, Incident, Message, Vehicle
from .references import retrieval_reference


def reply_to(db, message_id, requested_model=None):
    if requested_model is not None:
        try:
            assistant.selected_model(requested_model)
        except assistant.AssistantError as exc:
            raise HTTPException(exc.status, exc.message) from None
    message = db.get(Message, message_id)
    if message is None:
        raise HTTPException(404, "Message not found")
    existing = db.get(AssistantReply, message_id)
    if existing:
        return existing
    try:
        incident = db.scalar(
            select(Incident)
            .where(Incident.id == message.incident_id)
            .with_for_update(nowait=True)
        )
    except OperationalError:
        db.rollback()
        raise HTTPException(
            409,
            "Ya se está preparando una respuesta para este caso. Esperá y actualizá la conversación.",
        ) from None
    # Recheck after acquiring the lock (another request may have just committed).
    existing = db.get(AssistantReply, message_id)
    if existing:
        return existing
    history = list(
        reversed(
            db.scalars(
                select(Message)
                .where(Message.incident_id == incident.id)
                .order_by(Message.created_at.desc(), Message.id.desc())
                .limit(20)
            ).all()
        )
    )
    if not history or history[-1].id != message_id:
        raise HTTPException(409, "Respondé al último mensaje de la conversación.")
    vehicle = db.get(Vehicle, incident.vehicle_id)
    fields = (
        "make",
        "model",
        "year",
        "fuel",
        "engine_code",
        "market",
        "mileage",
        "modifications",
        "notes",
    )
    facts = {name: getattr(vehicle, name) for name in fields}
    prior_replies = list(
        db.scalars(
            select(AssistantReply).where(
                AssistantReply.message_id.in_([m.id for m in history])
            )
        )
    )
    previous = {r.message_id: r.content for r in prior_replies}
    saved_navigation = {
        str(r.message_id): r.context_snapshot.get("retrieval", {}).get("conversation")
        for r in prior_replies
    }
    resolution = conversation.resolve(
        [{"id": str(m.id), "user": m.content} for m in history],
        saved_navigation,
        modifications=vehicle.modifications or "",
    )
    warning = assistant.safety_warning(
        incident.description + " " + " ".join(m.content for m in history)
    )
    retrieval = {"conversation": resolution}
    equipment_scope = document_scope.requires_equipment_document(resolution)
    needs_clarification = bool(resolution["clarification"])
    try:
        sources = (
            []
            if warning or equipment_scope or needs_clarification
            else corpus.search(db, vehicle, resolution["query"])
        )
        if not warning and not equipment_scope and not needs_clarification:
            sources += manual_library.search(
                vehicle, resolution["query"], db=db, diagnostics=retrieval
            )
            sources = manual_figures.attach(manual_library.identify_sources(sources))
    except assistant.AssistantError as exc:
        raise HTTPException(exc.status, exc.message) from None
    tasks = db.scalars(
        select(Incident)
        .where(Incident.vehicle_id == vehicle.id, Incident.id != incident.id)
        .order_by(Incident.created_at.desc(), Incident.id)
        .limit(12)
    ).all()
    context = {
        "retrieval": retrieval,
        "vehicle": facts,
        "retrieval_reference": retrieval_reference(vehicle),
        "problem": {
            "description": incident.description,
            "symptoms": incident.symptoms,
            "mileage": incident.mileage,
        },
        "history": [
            {"user": m.content, "assistant": previous.get(m.id)} for m in history
        ],
        "tasks": [
            {
                "title": t.title,
                "status": t.status,
                "work_notes": t.work_notes,
                "performed_on": str(t.performed_on) if t.performed_on else None,
                "work_mileage": t.work_mileage,
            }
            for t in tasks
        ],
        "sources": sources,
        "limits": "Últimos 20 mensajes y 12 tareas; fuentes revisadas y páginas originales de lectura automática bajo retrieval_reference, con alcance indicado en scope. OCR solo para localizar páginas; nunca evidencia validada. Sin búsqueda web.",
    }
    # Bound context size and avoid silently clipping away safety-critical text.
    if len(json.dumps(context, ensure_ascii=False)) > 80000:
        raise HTTPException(
            422,
            "Esta conversación es demasiado larga para responder de forma completa. Iniciá un nuevo chat con un resumen del problema.",
        )
    if warning:
        answer = assistant.Answer(
            summary=warning,
            hypotheses=[],
            checks=[],
            questions=["¿El vehículo está detenido en un lugar seguro?"],
            citation_ids=[],
        )
        model = "safety-rules-v1"
    elif needs_clarification:
        answer = assistant.Answer(
            summary="Necesito precisar a qué te referís para buscar el procedimiento correspondiente.",
            hypotheses=[],
            checks=[],
            questions=[resolution["clarification"]],
            citation_ids=[],
        )
        model = "conversation-clarification-v1"
    elif equipment_scope:
        answer = document_scope.equipment_answer(resolution)
        retrieval["scope"] = "equipment_specific_document_required"
        model = "document-scope-v1"
    elif not sources and context["retrieval_reference"]["mode"] == "factory_reference":
        answer = assistant.Answer(
            summary="No encontré páginas relevantes en los manuales disponibles para esta consulta. Esto no demuestra que el tema esté ausente del manual: la búsqueda puede fallar por vocabulario u OCR.",
            hypotheses=[],
            checks=[],
            questions=["¿Podés indicar el componente o reformular la pregunta?"],
            citation_ids=[],
        )
        model = "document-coverage-v1"
    else:
        try:
            answer = (
                assistant.generate(context, model=requested_model)
                if requested_model is not None
                else assistant.generate(context)
            )
            model = requested_model or assistant.model_name()
            if (
                not answer.citation_ids
                and context["retrieval_reference"]["mode"] == "factory_reference"
            ):
                context["retrieval"]["generation_model"] = model
                answer = assistant.Answer(
                    summary="Necesito precisar la consulta antes de respaldar la respuesta con los manuales."
                    if answer.questions
                    else "No encontré respaldo suficiente para responder esa consulta en las páginas consultadas. Esto no permite concluir que el tema esté ausente del manual completo.",
                    hypotheses=[],
                    checks=[],
                    questions=answer.questions
                    or [
                        "¿Podés aportar la referencia exacta del componente o su documentación específica?"
                    ],
                    citation_ids=[],
                )
                model = "document-coverage-v2"
        except assistant.AssistantError as exc:
            raise HTTPException(exc.status, exc.message) from None
    used = [source for source in sources if source["id"] in answer.citation_ids]
    reply = AssistantReply(
        message_id=message.id,
        incident_id=incident.id,
        content=answer.model_dump(),
        sources=used,
        context_snapshot=context,
        model=model,
        safety_warning=warning,
    )
    db.add(reply)
    db.commit()
    return reply
