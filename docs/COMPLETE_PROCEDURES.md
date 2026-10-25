# Procedimientos completos, explicaciones y seguimientos

Entrega local del 25 de octubre de 2026, a partir de las conversaciones del
filtro de combustible y la junta entre la bajada y el resto del escape.

## Secuencia documental y respuesta

`manual_flow.py` prepara el orden de regiones de lectura de cada tema sin
publicar su OCR. `procedure-sequences-v1.json` agrega secuencias y límites
visualmente cotejados con hashes de las páginas originales. Esa revisión de
estructura no certifica aplicabilidad ni equivale a una aprobación mecánica.

Para el filtro se cotejaron PDF 137–139: preparación y advertencia, V.14,
liberación del soporte, V.15, sustitución, V.16. Se identificaron las dos figuras
que estaban sin epígrafe y se mantuvo la tercera; se excluyen el sensor V.13 y el
cable del acelerador V.17. Los 598 archivos de recortes conservan sus bytes y
hashes anteriores; cambian las identificaciones y el manifiesto de navegación.

En una solicitud de procedimiento con secuencia revisada, Gemini redacta los
tramos de texto en `procedure_texts`. **El servidor construye `blocks`** con sus
párrafos, figuras y citas en el orden del manual; el modelo no decide cuántas
figuras conservar ni dónde moverlas. Las respuestas públicas siguen usando el
formato de párrafos e ilustraciones ya compatible con la interfaz.

Cada párrafo conserva `manual_block_ids`. Se comprueban orden, completitud,
vinculación con la página y grupos de conceptos revisados para no sustituir la
liberación del soporte por una segunda explicación de los conectores. Estos
controles léxicos detectan algunas omisiones; las exclusiones revisadas rechazan
indicaciones de sentido de flujo que no aparecen en esos tramos. Estos controles no prueban por sí solos fidelidad
semántica. El esquema permite hasta 24 bloques y ocho figuras, con un presupuesto
menor en cada solicitud cuando corresponde.

La exigencia de secuencia completa se aplica a temas que tienen una secuencia
revisada, actualmente el filtro. Las demás secciones reciben orden de lectura,
pero no se presentan como procedimientos completos automáticamente validados.
Una pregunta puntual de ubicación o significado no obliga a repetir las tres
figuras del procedimiento.

## Seguimientos y límites visibles

El estado conversacional pasa a versión 2 y conserva tipo de filtro, unión e
intención: procedimiento, ubicación, explicación o información. Los estados
anteriores se reconstruyen desde los mensajes disponibles; no se reescriben
respuestas guardadas. Cambiar a filtro de aire/aceite inicia otro componente.
«Dónde está el filtro» y «no lo encuentro» mantienen el filtro de combustible.
La aclaración sobre encendido/batería no se convierte en una consulta distinta
del procedimiento. Las precisiones sobre la junta original permanecen en el
historial del usuario y no cambian los datos globales del vehículo.

Se distinguen la unión posterior de la bajada y el procedimiento del múltiple.
La recuperación de una junta posterior no arrastra los pasos de desmontaje del
múltiple ni capítulos de válvulas; la consulta de pasajes aprobados se acota al
sistema de escape para evitar coincidencias con palabras genéricas.

`evidence_status` y `evidence_gap` distinguen respaldo completo, parcial,
insuficiencia y aclaración. El límite debe ser visible en el cuerpo, no solo en
un resumen que la interfaz no muestra. La insuficiencia descarta comprobaciones
y procedimientos sin respaldo; conserva una explicación concreta de lo que
falta en vez de pedir otra vez identificar una pieza ya indicada.

Hay límites revisados para estas páginas: un despiece del escape no demuestra
un método para asentar la junta torcida; los primeros planos del filtro no
establecen su posición exacta en el chasis; la frase del encendido no define por
sí sola una operación sobre la llave o los bornes. Esos casos reciben una
respuesta local con la referencia pertinente, sin inventar instrucciones ni
repetir preguntas sobre las modificaciones. **No se afirma haber encontrado la
ubicación exacta ni un método documentado de montaje de esa junta.** Para ampliar
esa cobertura hacen falta otras fuentes verificables.

## Presupuesto visual

Las vistas enviadas al modelo recortan los píxeles originales a las regiones
pertinentes, sin reducir resolución ni reescribir cifras. Las figuras ya
adjuntadas no se duplican dentro de las vistas de texto. Una página que solo
aporta una figura adjunta no se vuelve a enviar completa. Tablas o dibujos no
adjuntados permanecen en las áreas originales recuperadas cuando corresponden.

El snapshot conserva regiones, indicador de recorte y hash de la vista; se
puede reconstruir en el mismo entorno de la API. Los límites continúan en
12 MB de páginas, 4 MB de figuras y 18 MB de imágenes codificadas en conjunto.
Los enlaces del usuario abren las páginas completas originales.

## Instalación local

Desde la raíz, con los bundles anteriores y layouts privados disponibles:

```powershell
.venv/Scripts/python.exe scripts/prepare_manual_figures.py --library data/private/manuals/library-v1 --output data/private/manuals/figures-v6 --reuse data/private/manuals/figures-v5
.venv/Scripts/python.exe scripts/prepare_manual_sections.py --library data/private/manuals/library-v1 --figures data/private/manuals/figures-v6 --layouts data/private/manuals/reviewed --output data/private/manuals/sections-v12
```

Los destinos deben ser nuevos. `--reuse` verifica y copia los recortes previos,
sin recomprimirlos. En `.env`, usar `MANUAL_FIGURES_DIRECTORY=./data/private/manuals/figures-v6`
y `MANUAL_SECTIONS_DIRECTORY=./data/private/manuals/sections-v12`; se conservan
`MANUAL_FIGURES_PATH=/manual-figures` y `MANUAL_SECTIONS_PATH=/manual-sections`.
Después: `docker compose up -d --build api`.

Figuras v6 SHA-256:
`78fa4424704e2b7f1095dd9a5f25f34e494a6e6a21a51330b2cd0b2abf10cb17`.
Secciones v12 SHA-256:
`750427f887cda24ea6c057811ff81ec3a312a61f18f9f36a06d729b4d7050b54`.
El manifiesto de secciones usa esquema 3 y conserva 572 temas y 597 asociaciones
de figuras. La biblioteca y los 546 vectores no se reconstruyen.

## Validación y fallos conservados

`procedure-cases-v1.json` y `procedure-cases-v2.json` registran tres conversaciones
con diez turnos: cambio/ubicación/aclaración del filtro, unión del escape y cambio
a filtro de aire. Se verifica el orden completo V.14/V.15/V.16, además de IDs,
hashes y consultas resueltas. Los reportes permanecen en `data/private/manuals/`.

Las primeras rondas incluyen fallos HTTP, mezcla de pasos y afirmaciones que no
estaban justificadas. El esquema combinado inicial produjo 400 del proveedor;
se acotaron campos y alternativas y después se separó la redacción de tramos
del armado de la secuencia. Se conservaron las rondas, incluyendo los rechazos
por texto que no correspondía a su región. Los tipos del esquema usan enums y
los campos de generación están explícitamente requeridos. Referencia técnica:
[salida estructurada de Gemini](https://ai.google.dev/gemini-api/docs/structured-output).

La regresión de los veinte escenarios anteriores tuvo 22 consultas HTTP 200 y
controles automáticos correctos durante este bloque. No es una nueva aprobación
semántica de los veinte casos ni cierra los fallos ajenos a esta entrega.

Las pruebas públicas cubren estructura, conservación del contexto, cambio de
filtro, estados anteriores, límites de evidencia, armado de la secuencia,
geometría, píxeles y rechazo de IDs o pasos fuera de orden. La revisión mecánica
profesional y la generalización a otros procedimientos siguen pendientes.

## Resultado de cierre local

- Backend: 239 pruebas pasaron (`cd backend; ../.venv/Scripts/python.exe -m pytest -q --tb=short`), con una advertencia de deprecación de Starlette/httpx.
- Herramientas públicas: 30 pruebas pasaron (`.venv/Scripts/python.exe -m unittest discover -s scripts/tests -q`). Ruff de los archivos modificados, formato/build del frontend y `git diff --check` correctos. El lint global también mostró convenciones de imports y llamadas dict preexistentes fuera del bloque; no se modificaron archivos ajenos para uniformarlas.
- Ronda final privada `procedure-live-v10.json`: diez turnos HTTP 200, todos los controles automáticos correctos; tres generaciones Gemini y siete respuestas documentales locales acotadas (dos de ubicación, una de término y cuatro de despiece).
- Revisión del texto del filtro: preparación y retirada de conductos, liberación del conjunto y sustitución ocupan sus posiciones entre V.14/V.15/V.16. Los seguimientos no inventan una ubicación exacta ni traducen encendido a una instrucción sobre bornes. Las consultas del escape no mezclan el desmontaje del múltiple ni sugieren selladores a partir de un despiece.
- Auditoría `procedure-audit-v10.json`: nueve vistas originales reconstruidas, 21 figuras ofrecidas verificadas, snapshots persistidos idénticos y modificaciones del vehículo real conservadas. Máximo de imágenes binarias en una generación: 4.794.887 bytes; se mantuvieron los límites configurados.
- Navegador: chat sintético recargado, V.14/V.15/V.16 renderizadas con sus párrafos intercalados, referencias a PDF 137–139 y aclaración del encendido persistida. Capturas privadas `ui-procedure-interleaved-v10.png`, `ui-procedure-support-v10.png` y `ui-procedure-connector-v10.png`.

Las rondas anteriores se conservan: V7 volvió a interpretar el encendido sin respaldo; V8 agregó consejos de selladores al despiece; V9 omitió retirar conductos en un tramo y agregó sentido de circulación. Esos hallazgos motivaron límites revisados y validación por tramo; no se reclasifican como éxitos por haber pasado controles automáticos.

Este cierre valida los casos de regresión descritos y sus límites de evidencia, no una tasa general de calidad ni la corrección mecánica de cualquier respuesta. El filtro de aire se usó para comprobar cambio de tema; su procedimiento no tiene aún una secuencia completa revisada. Continúan pendientes la ubicación exacta del filtro, el método de asiento de la junta, ampliar secuencias, revisar los nueve hallazgos semánticos del bloque anterior y ejecutar CI remoto después del push del propietario.
