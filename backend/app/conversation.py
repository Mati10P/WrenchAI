"""Resolve conversational references from user messages, never model prose.

This is bounded navigation state, not a new source of vehicle/technical facts.
Unknown complete questions reset the topic; ambiguous references ask the user.
"""

import re

from .assistant import normalize

# Narrow subjects precede their parent system. Each family is matched once.
SUBJECTS = [
    (
        "fuel",
        "filtro de combustible",
        r"filtro (?:de |del )?(?:combustible|nafta|gasolina)",
    ),
    ("air_filter", "filtro de aire", r"filtro (?:de |del )?aire"),
    ("oil_filter", "filtro de aceite", r"filtro (?:de |del )?aceite"),
    (
        "exhaust",
        "junta entre la bajada y el resto del escape",
        r"junta.{0,50}(?:bajada|escape)|(?:bajada|escape).{0,35}junta",
    ),
    ("brakes", "líquido de frenos", r"liquido (?:de )?frenos?|fluido (?:de )?frenos?"),
    ("brakes", "cilindro de freno", r"cilindros? (?:de |del )?frenos?"),
    ("brakes", "pastillas de freno", r"pastillas?"),
    ("brakes", "zapatas de freno", r"zapatas?|cintas? (?:de )?freno"),
    ("brakes", "frenos", r"frenos?|servofreno|mordaza|caliper"),
    ("gearbox", "aceite de caja de cambios", r"aceite.{0,25}(?:caja|transmision)"),
    ("oil", "aceite del motor", r"aceite (?:del? )?motor"),
    ("oil", "aceite", r"aceite|lubricacion"),
    ("coolant", "refrigerante", r"refrigerante|refrigeracion|deposito de expansion"),
    (
        "belt",
        "correa dentada de distribución",
        r"correa (?:dentada|de distribucion)|distribucion|puesta a punto",
    ),
    ("belt", "correa Poly V", r"poly[ -]?v"),
    ("belt", "correa trapezoidal", r"correa trapezoidal"),
    ("belt", "correa", r"correas?|polea tensora"),
    ("clutch", "embrague", r"embrague|desembrague"),
    ("tires", "neumáticos", r"neumaticos?|cubiertas?|llantas?|ruedas?"),
    ("wiper", "limpiaparabrisas", r"limpiaparabrisas|escobillas?|palhetas?"),
    ("fuses", "fusibles", r"fusibles?"),
    ("radio", "radio", r"radio|autoradio|bluetooth|multimedia|estereo"),
    ("alarm", "alarma", r"alarmas?|inmovilizador"),
    ("lights", "faros antiniebla", r"antiniebla|neblina"),
    ("lights", "luces", r"faros?|luces|lamparas?|bombillas?|indicador de giro"),
    ("battery", "batería", r"bateria|alternador"),
    ("suspension", "suspensión", r"suspension|amortiguadores?|espirales?"),
    ("steering", "dirección", r"direccion|cremallera"),
    ("coolant", "termostato", r"termostato|radiador|electroventilador"),
    ("fuel", "combustible", r"combustible|nafta|gasolina|inyectores?|inyeccion"),
    ("ignition", "encendido", r"bujias?|encendido|distribuidor|bobina"),
    ("gearbox", "caja de cambios", r"caja de cambios|transmision"),
    ("doors", "puertas", r"puertas?|cerradura|manija|vidrio|ventana"),
    ("exhaust", "escape", r"escape|catalizador"),
]
AXIS = {"front": r"adelante|delanter[oa]s?", "rear": r"atras|traser[oa]s?"}
AXIS_WORD = {"front": "delanteros", "rear": "traseros"}
ROOTS = {"brakes": "frenos", "tires": "neumáticos", "suspension": "suspensión"}
GENERIC = {
    "belt": "correa",
    "oil": "aceite",
    "fuel": "combustible",
    "exhaust": "escape",
    **ROOTS,
}
DEPENDENT = r"^(?:y\b|entonces\b|en ese caso\b|eso\b|esa\b|ese\b|lo mismo\b|donde\b)|\b(?:lo|la|los|las) (?:saco|quito|cambio|ajusto|compruebo|reviso|hago)\b|\b(?:cuanto|cuanta|cuantos|cuantas)\b|\b(?:tension|torque|apriete|holgura|capacidad|cantidad|compruebo|comprueba|comprueban|comprobar|verifico|verifica|verificar|con carga|sin carga|en frio|en caliente)\b"


def subjects(text):
    value = normalize(text)
    found = {}
    for family, subject, pattern in SUBJECTS:
        if family not in found and re.search(r"\b(?:" + pattern + r")\b", value):
            found[family] = subject
    # A named assembly may mention a wheel without asking about tires.
    if (
        "brakes" in found
        and not re.search(r"neumatic|cubierta|llanta", value)
        and re.search(r"pastilla|cilindro|zapatas?|cintas?|frenos?", value)
    ):
        found.pop("tires", None)
    if (
        "gearbox" in found
        and "motor" not in value
        and re.search(r"aceite.{0,25}(?:caja|transmision)", value)
    ):
        found.pop("oil", None)
    return found


def intent(text):
    value = normalize(text)
    if re.search(
        r"donde|ubicaci|localiz|no (?:lo|la) encuentro|en que (?:parte|lado)", value
    ):
        return "location"
    if re.search(
        r"que significa|eso significa|como seria|como seria|a que (?:se )?refiere|no entiendo|desconectar el encendido",
        value,
    ):
        return "explanation"
    if re.search(
        r"como.{0,30}(?:cambi|reemplaz|sustitu|ajust|regul|pon|pongo|coloc|mont|instal|sac|retir)",
        value,
    ):
        return "procedure"
    return "information"


def operation(text):
    value = normalize(text)
    for label, pattern in [
        ("presión", r"presion|inflad"),
        ("medida", r"\b(?:mm|cm|nm|bar|psi)\b|torque|apriete|holgura"),
        (
            "cantidad",
            r"cuant[oa]s?.{0,18}(?:lleva|entra|necesit|litros)|capacidad|cantidad",
        ),
        ("cambio", r"cambi[ao]|cambiar|reemplaz|sustitu"),
        ("montaje", r"pongo|poner|coloc|instal|montar"),
        ("ajuste", r"tens[ao]|ajust|regul"),
    ]:
        if re.search(pattern, value):
            return label
    return None


def equipment_request(text, modifications=""):
    """Device credentials/configuration require that device's documentation.

    Do not block factory procedures or comparisons just because a car is modified.
    """
    value = normalize(text)
    devices = subjects(value)
    if not ({"radio", "alarm"} & devices.keys()):
        return False
    credential = re.search(
        r"\bpin\b|contrasena|clave.{0,25}(?:emparej|bluetooth)", value
    )
    if re.search(
        r"cual|dame|decime|necesito|exacto|conseguir|obtener", value
    ) and re.search(r"codigo", value):
        credential = True
    feature = re.search(r"emparej|vincul|configur|programar", value)
    nonfactory = re.search(
        r"bluetooth|instal|aftermarket|multimedia|adaptad|que puse", value
    )
    if (
        not nonfactory
        and "radio" in devices
        and "bluetooth" in normalize(modifications)
    ):
        nonfactory = not re.search(r"original|fabrica", value)
    return bool(credential or (feature and nonfactory))


def resolve(history, saved=None, modifications=""):
    """Fold this chat's recent turns, resuming a trusted persisted state if present."""
    state = None
    saved = saved or {}
    for turn in history:
        prior = saved.get(turn["id"])
        if prior and prior.get("version") == 2:
            state = prior
        else:
            state = advance(state, turn["id"], turn["user"], modifications)
    return state


def axis_of(text):
    return next(
        (
            name
            for name, pattern in AXIS.items()
            if re.search(r"\b(?:" + pattern + r")\b", normalize(text))
        ),
        None,
    )


def advance(previous, identifier, text, modifications=""):
    value = normalize(text).strip(" ¿?¡!.,\n")
    detected = subjects(text)
    frame = previous.get("frame") if previous else None
    # Filter type is a component; mentioning its fluid does not change topics.
    if "oil_filter" in detected:
        detected.pop("oil", None)
    current_intent = intent(text)
    if frame and not re.search(
        r"otro tema|otra consulta|otra pregunta|cambiando de tema", value
    ):
        if (
            len(frame["subjects"]) == 1
            and re.search(r"\bfiltro\b", value)
            and not detected
        ):
            family, subject = next(iter(frame["subjects"].items()))
            if subject.startswith("filtro de"):
                detected = {family: subject}
        if (
            set(frame["subjects"]) == {"exhaust"}
            and not detected
            and re.search(r"junta|dona|bajada", value)
        ):
            detected = dict(frame["subjects"])
        if (
            current_intent == "explanation"
            and (
                not detected
                or set(detected) - {"ignition", "battery"} <= set(frame["subjects"])
            )
            and len(frame["subjects"]) == 1
        ):
            detected = {
                k: v for k, v in detected.items() if k not in {"ignition", "battery"}
            }
    axis = axis_of(text)
    op = (
        "ubicación"
        if current_intent == "location"
        else "aclaración"
        if current_intent == "explanation"
        else operation(text)
    )
    state = {
        "version": 2,
        "intent": current_intent,
        "message_id": identifier,
        "query": text,
        "mode": "standalone",
        "parent_message_id": None,
        "clarification": None,
        "pending_question": None,
    }
    reset = bool(
        re.search(r"cambiando de tema|otro tema|otra consulta|otra pregunta", value)
    )
    dependent = (
        bool(
            current_intent in {"location", "explanation"}
            or re.search(
                r"no (?:lo|la) encuentro|queda torcid|queda apretad|se (?:mueve|desplaza)",
                value,
            )
            or re.search(DEPENDENT, value)
            or re.fullmatch(
                r"como (?:se )?(?:hace|regula|ajusta|cambia|saca|retira|instala|monta|revisa|comprueba|verifica)",
                value,
            )
        )
        and not reset
    )
    motor_condition = bool(
        re.search(
            r"(?:con|si|cuando).{0,18}motor.{0,18}(?:caliente|frio|apagado|encendido|en marcha)",
            value,
        )
    )
    if (
        motor_condition
        and detected == {"ignition": "encendido"}
        and re.match(r"^(?:y )?(?:con|si|cuando)\b", value)
    ):
        detected = {}  # engine running is a condition, not a new ignition topic
    if motor_condition and not reset and not detected:
        dependent = True
    new_objects = re.findall(r"\b(?:el|la|los|las|un|una|del)\s+(\w+)", value)
    if (
        any(
            word
            not in {
                "mismo",
                "misma",
                "mismos",
                "mismas",
                "tension",
                "torque",
                "par",
                "apriete",
                "holgura",
                "capacidad",
                "cantidad",
                "saco",
                "quito",
                "cambio",
                "ajusto",
                "compruebo",
                "reviso",
                "hago",
                "negativo",
                "bateria",
                "encendido",
            }
            for word in new_objects
            if not (word == "motor" and motor_condition)
            and not (word == "filtro" and current_intent == "location")
        )
        and not detected
        and current_intent != "explanation"
    ):
        dependent = False  # an unknown named object must not inherit the old one
    frame = previous.get("frame") if previous else None
    if (
        previous
        and previous.get("awaiting_equipment")
        and not reset
        and frame
        and set(detected) <= set(frame["subjects"])
        and not re.search(
            r"\b(?:como|cual|donde|quiero|original|fabrica|cambiar|cambio|sacar|quitar)\b",
            value,
        )
    ):
        detected = {}  # brand/model reply, even when it repeats the word radio
        dependent = True
    if detected:
        new_frame = {
            "subjects": detected,
            "axis": axis,
            "operation": op,
            "anchor_message_id": identifier,
            "equipment_specific": equipment_request(text, modifications),
            "equipment_question": text,
        }
        if (
            frame
            and set(detected) == set(frame["subjects"])
            and (
                detected == frame["subjects"]
                or re.search(r"\b(?:esa|ese|esas|esos|mismo|misma)\b", value)
            )
        ):
            family = next(iter(detected))
            if detected[family] == GENERIC.get(family) or detected == frame["subjects"]:
                new_frame.update(
                    subjects=frame["subjects"],
                    axis=axis or frame.get("axis"),
                    operation=op or frame.get("operation"),
                )
                state.update(
                    mode="followup",
                    parent_message_id=previous["message_id"],
                    query=text
                    + "\nTema de la consulta: "
                    + " ".join(new_frame["subjects"].values()),
                )
        if (
            previous
            and previous.get("pending_question")
            and len(detected) == 1
            and not reset
        ):
            pending_axis = axis or axis_of(previous["pending_question"])
            pending_operation = (
                operation(previous["pending_question"])
                or op
                or (previous.get("frame") or {}).get("operation")
            )
            state.update(
                mode="clarification_reply",
                parent_message_id=previous["message_id"],
                query=" ".join(
                    filter(
                        None,
                        [
                            previous["pending_question"],
                            pending_operation,
                            " ".join(detected.values()),
                            AXIS_WORD.get(pending_axis),
                        ],
                    )
                ),
            )
            new_frame["operation"] = pending_operation
            new_frame["axis"] = pending_axis
            if (
                pending_operation is None
                and axis_of(previous["pending_question"])
                and not previous.get("frame")
            ):
                state.update(
                    mode="clarification",
                    clarification="¿Qué querés consultar sobre ese componente?",
                    pending_question=previous["pending_question"],
                )
        elif frame and set(detected) != set(frame["subjects"]):
            state["mode"] = "topic_switch"
        if (
            frame
            and set(detected) == set(frame["subjects"])
            and detected == frame["subjects"]
        ):
            new_frame["anchor_message_id"] = frame["anchor_message_id"]
        state["frame"] = new_frame
        return state
    if dependent:
        if not frame or len(frame["subjects"]) != 1:
            choices = " o ".join(frame["subjects"].values()) if frame else None
            state.update(
                mode="clarification",
                parent_message_id=previous["message_id"] if previous else None,
                clarification=f"¿Te referís a {choices}?"
                if choices
                else "¿A qué componente o procedimiento te referís?",
                pending_question=text,
                frame=frame,
            )
            return state
        family, subject = next(iter(frame["subjects"].items()))
        if (
            re.search(r"\bcuant[oa]s?\b", value)
            and op is None
            and frame.get("operation") not in {"cantidad", "presión", "medida"}
        ):
            state.update(
                mode="clarification",
                parent_message_id=previous["message_id"],
                clarification="¿Te referís a una cantidad, una medida u otro dato?",
                pending_question=text,
                frame=frame,
            )
            return state
        if op == "cantidad" and family not in {"oil", "coolant", "gearbox"}:
            state.update(
                mode="clarification",
                parent_message_id=previous["message_id"],
                clarification="¿Qué cantidad o medida querés conocer y de qué componente?",
                pending_question=text,
                frame=frame,
            )
            return state
        if axis and family not in ROOTS:
            state.update(
                mode="clarification",
                parent_message_id=previous["message_id"],
                clarification="¿A qué componente delantero o trasero te referís?",
                pending_question=text,
                frame=None,
            )
            return state
        frame = dict(frame)
        if axis and frame.get("axis") != axis:
            subject = ROOTS[family]
            frame["subjects"] = {family: subject}
            if family == "brakes" and frame.get("operation") == "cambio":
                frame["axis"] = axis
                state.update(
                    mode="clarification",
                    parent_message_id=previous["message_id"],
                    query="frenos " + AXIS_WORD[axis],
                    clarification="¿Qué pieza del freno trasero querés cambiar: las zapatas/cintas, el cilindro u otra?"
                    if axis == "rear"
                    else "¿Qué pieza del freno delantero querés cambiar?",
                    pending_question=text,
                    frame=frame,
                )
                return state
        frame["axis"] = axis or frame.get("axis")
        frame["operation"] = op or frame.get("operation")
        if equipment_request(text + " " + subject, modifications):
            frame["equipment_specific"] = True
            frame["equipment_question"] = text + " " + subject
        anchor = " ".join(
            filter(
                None, [frame["operation"], subject, AXIS_WORD.get(frame.get("axis"))]
            )
        )
        # A device model/brand reply continues the pending equipment question.
        if frame.get("equipment_specific"):
            anchor = frame["equipment_question"]
        state.update(
            mode="followup",
            parent_message_id=previous["message_id"],
            frame=frame,
            query=text + "\nTema de la consulta: " + anchor,
        )
        state["awaiting_equipment"] = previous.get("awaiting_equipment", False)
        return state
    # Unknown but complete questions also replace the active topic. Their own
    # words are a navigation anchor, not an inferred component or technical fact.
    state["mode"] = "topic_switch" if previous else "standalone"
    state["frame"] = {
        "subjects": {"unspecified": text[:600]},
        "axis": axis,
        "operation": op,
        "anchor_message_id": identifier,
        "equipment_specific": False,
        "equipment_question": None,
    }
    return state
