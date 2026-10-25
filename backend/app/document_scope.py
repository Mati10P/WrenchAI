"""Factory vehicle manuals are not documentation for an installed device."""

from .assistant import Answer


def requires_equipment_document(resolution):
    return bool((resolution.get("frame") or {}).get("equipment_specific"))


def equipment_answer(resolution):
    details_given = resolution.get("awaiting_equipment", False)
    resolution["awaiting_equipment"] = True
    return Answer(
        summary="Los manuales disponibles corresponden al vehículo original. No tengo documentación del equipo instalado para confirmar ese dato."
        if not details_given
        else "Para confirmar ese dato necesito la documentación correspondiente al equipo que indicaste. Los manuales del vehículo original no respaldan esa configuración específica.",
        hypotheses=[],
        checks=[],
        citation_ids=[],
        questions=["¿Cuál es la marca y el modelo exactos del equipo?"]
        if not details_given
        else ["¿Tenés una referencia al manual específico del equipo?"],
    )
