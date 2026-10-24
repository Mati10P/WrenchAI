"""Reply lifecycle. A transaction lock prevents duplicate provider calls per case."""

import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from . import assistant, corpus
from .models import AssistantReply, Incident, Message, Vehicle


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
    sources = corpus.search(db, vehicle, incident.description + " " + message.content)
    previous = {
        r.message_id: r.content
        for r in db.scalars(
            select(AssistantReply).where(
                AssistantReply.message_id.in_([m.id for m in history])
            )
        )
    }
    tasks = db.scalars(
        select(Incident)
        .where(Incident.vehicle_id == vehicle.id, Incident.id != incident.id)
        .order_by(Incident.created_at.desc(), Incident.id)
        .limit(12)
    ).all()
    context = {
        "vehicle": facts,
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
        "limits": "Últimos 20 mensajes y 12 tareas; evidencia solo aprobada y compatible. Sin búsqueda web.",
    }
    # Bound context size and avoid silently clipping away safety-critical text.
    if len(json.dumps(context, ensure_ascii=False)) > 80000:
        raise HTTPException(
            422,
            "Esta conversación es demasiado larga para responder de forma completa. Iniciá un nuevo chat con un resumen del problema.",
        )
    warning = assistant.safety_warning(
        incident.description + " " + " ".join(m.content for m in history)
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
    else:
        try:
            answer = (
                assistant.generate(context, model=requested_model)
                if requested_model is not None
                else assistant.generate(context)
            )
            model = requested_model or assistant.model_name()
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
