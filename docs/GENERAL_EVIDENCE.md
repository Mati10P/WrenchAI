# Revisión general de procedimientos y fuentes complementarias

## Cambio

La selección visual deja de depender de una secuencia especial para el filtro. Se ofrecen las figuras contenidas geométricamente en los temas recuperados, incluidas las anónimas, y se exige una decisión y motivo para cada una. El servidor conserva el orden documental. Cada grupo de texto entre figuras se envía como recorte separado de píxeles originales, identificado por ID y hash. Los originales y sus enlaces permanecen disponibles. El catálogo local sections-v13 contiene 572 temas y 597 asociaciones; no cambia los 598 recortes originales.

La revisión distingue equipo, condiciones, acciones, comprobación y aplicabilidad. Puede ampliar una vez la búsqueda documental dentro del presupuesto. Un valor aislado no se declara procedimiento completo. La revisión visual sigue siendo de un modelo, no revisión humana ni garantía de exactitud mecánica.

## Web

WEB_SEARCH_ENABLED habilita Google Search de Gemini; VISUAL_EVIDENCE_REVIEW habilita la revisión general. Docker activa ambos. Se envían consultas técnicas y referencia de fábrica, no historial bruto, notas privadas ni páginas del manual. Se admiten dominios de fabricantes enumerados en web_evidence.py. Una fuente requiere respaldo en groundingMetadata y lectura URL con estado SUCCESS. Las explicaciones web se muestran con URL, fecha y alcance general: no confirman parámetros ni conexiones de una variante del Gol. Las sugerencias de Google se muestran en iframe aislado.

Referencia de integración: https://ai.google.dev/gemini-api/docs/generate-content/google-search y https://ai.google.dev/gemini-api/docs/generate-content/url-context.

El 25 de octubre la llamada real de búsqueda devolvió HTTP 429 RESOURCE_EXHAUSTED. La interfaz informa este límite y conserva la respuesta documental. **No hay una búsqueda web exitosa real validada en este bloque**. Hace falta disponibilidad de cuota del proyecto para cerrar esa prueba y comprobar la calidad del complemento. No se cambió facturación ni credenciales.

## Evidencia

- Backend: 255 pruebas aprobadas; herramientas: 30. Ruff y compilación Docker/frontend correctos.
- Casos públicos: general-evidence-cases-v1.json, cuatro conversaciones/cinco turnos.
- Resultados privados: data/private/manuals/general-evidence-live-v1.json y general-evidence-live-v2.json. Ambas rondas devolvieron cinco HTTP 200 con controles automáticos correctos.
- Revisión textual de v2: encendido muestra V.58, texto de lectura de RPM y V.59; filtro muestra V.14, liberar soporte, V.15, sustitución y V.16; correa incluye ajuste y comprobación; cilindro trasero excluye servofreno.
- La primera ronda mezcló el texto de RPM con el fragmento anterior; los recortes separados corrigen esa asociación en la segunda ronda.
- La respuesta sobre encendido sigue siendo parcial: no se verificaron condiciones completas, uso de la lámpara ni compatibilidad del valor con el motor del usuario. No confundir aprobación de imágenes/estructura con aprobación semántica de un procedimiento completo. Hay repetición y preguntas mejorables que requieren reevaluación con el complemento disponible.

## Reproducción

Desde backend: `../.venv/Scripts/python.exe -m pytest -q`. Desde raíz: `.venv/Scripts/python.exe -m pytest scripts/tests -q` y `git diff --check`.

Evaluación real: `scripts/evaluate_conversation.py --vehicle <vehículo> --cases docs/general-evidence-cases-v1.json --output data/private/manuals/<archivo-nuevo>.json`, ejecutado con Python del entorno. Crea un vehículo sintético de evaluación; no modifica el vehículo original. Requiere API local, catálogo privado y cuota Gemini; tiene costo de proveedor. No publicar salidas privadas.

Las respuestas guardadas no se reescriben. Probar mediante una nueva pregunta/generación.
