"""Locate specifications in body text, independently of chapter headings.

Matches are navigation hints only. Values always require reading original pixels.
"""

import re

from .assistant import normalize

TORQUE = (
    r"\b(?:torque|apriete|aperto|apretar|aprieto|torquear|nm)\b|par de (?:ajuste|apriete)"
)
UNITS = r"\d[\d.,]*\s*(?:n\s*[.·]?\s*m|danm|kgf\s*[.·]?\s*m|kgm)\b"
FASTENER = r"\b(?:tornillos?|bulones?|pernos?|tuercas?|parafusos?|fijacion|sujecion)\b"
WHEEL = r"\b(?:ruedas?|rodas?|llantas?)\b"


def is_torque_query(query):
    return bool(re.search(TORQUE, normalize(query)))


def matching_windows(query, text):
    from .manual_sections import words

    if not is_torque_query(query):
        return []
    query = normalize(query)
    # Measurement intent and conversational filler must not become component IDs.
    anchors = words(re.sub(TORQUE, " ", query)) - words(
        "cuanto cuanta cuantos cuantas lleva llevan darle dar ajuste valor valores "
        "necesita necesitan cual tengo tengo que van va tornillo tornillos bulon "
        "bulones perno pernos tuerca tuercas"
    )
    wheel = bool(re.search(WHEEL + r"|\bneumaticos?\b", query)) and not re.search(
        r"rodamiento|cubo|maza|tensora|cilindro|engranaje", query
    )
    if wheel:
        anchors = words("rueda")
    if not anchors:
        return []
    # Join line wraps without changing the retained source text or any number.
    value = re.sub(r"\s+", " ", normalize(text))
    value = re.sub(r"\broda\s*-?\s+mientos?\b", "rodamiento", value)
    matches = []
    for sentence in re.split(r"(?<=[.;])\s+|\n\s*\n", value):
        for unit in re.finditer(UNITS, sentence):
            window = sentence[max(0, unit.start() - 180) : unit.end() + 60]
            if wheel and (
                not re.search(WHEEL, window)
                or not re.search(FASTENER, window)
                or re.search(r"rueda\s+(?:tensora|dentada)", window)
                or re.search(r"\b(?:maza|cubo|rodamiento)\b", window)
            ):
                continue
            overlap = anchors & words(window)
            if overlap == anchors:
                matches.append(window)
    return matches


def section_hits(query, sections):
    """Return bounded original pages; never expand an entire procedure for a value."""
    return (
        {
            s["id"]: list(
                dict.fromkeys(
                    c["page_id"]
                    for c in s["chunks"]
                    if matching_windows(query, c["text"])
                )
            )
            for s in sections
            if any(matching_windows(query, c["text"]) for c in s["chunks"])
        }
        if is_torque_query(query)
        else {}
    )
