"""Bounded Gemini transport shared by evidence review and public web lookup."""

import json
import os
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def call(model, payload, deadline):
    from .assistant import AssistantError

    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise AssistantError(
            503, "Falta configurar la clave de Gemini. Tu mensaje está guardado."
        )
    remaining = deadline - monotonic()
    if remaining < 1:
        raise AssistantError(
            504, "La consulta superó el tiempo disponible. Tu mensaje está guardado."
        )
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=min(55, remaining)) as response:
            raw = response.read(500001)
        if len(raw) > 500000:
            raise ValueError("Oversized response")
        body = json.loads(raw)
        candidate = body["candidates"][0]
        if candidate.get("finishReason") != "STOP":
            raise ValueError("Incomplete response")
        return candidate
    except HTTPError as exc:
        raise AssistantError(
            429 if exc.code == 429 else 502,
            "No se pudo completar la consulta al proveedor. Tu mensaje está guardado; podés reintentar.",
        ) from None
    except (TimeoutError, URLError):
        raise AssistantError(
            504,
            "La consulta al proveedor no terminó a tiempo. Tu mensaje está guardado.",
        ) from None
    except (ValueError, KeyError, IndexError):
        raise AssistantError(
            502,
            "El proveedor devolvió una respuesta incompleta. Tu mensaje está guardado.",
        ) from None


def text(candidate):
    return "".join(
        p.get("text", "") for p in candidate["content"]["parts"] if not p.get("thought")
    )
