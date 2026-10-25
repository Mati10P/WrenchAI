# Recuperación por temas y correspondencia de ilustraciones

Actualizaciones posteriores: [referencias válidas y procedimientos ilustrados](FIGURE_RELIABILITY.md) y [contexto conversacional con lectura visual limitada al tema](CONVERSATION_RETRIEVAL.md).

Entrega local del 25 de octubre de 2026. Reemplaza la selección de figuras por
tamaño de página cuando está instalado el bundle de secciones.

## Problema y comportamiento

Una página puede terminar un procedimiento y empezar otro. En reparación PDF
211 aparece «Cilindro del freno (rueda trasera)» con la figura VI.16. Su lista de
piezas y procedimiento continúan en PDF 212, hasta «Servofreno», que inicia otro
tema con figura VI.17. La mordaza del freno a disco usa VI.15 en PDF 210 y su
leyenda continúa en PDF 211. El número impreso en el libro puede diferir del PDF;
los enlaces de la interfaz identifican explícitamente la página PDF.

Ahora se recupera el tema con sus áreas de lectura, continuaciones y figuras.
Preguntar por el cilindro trasero ofrece VI.16 y ambas páginas; no ofrece VI.15 ni
VI.17. Cada figura conserva su identidad documental: Gemini no puede renombrar
una mordaza como cilindro trasero mediante el epígrafe.

Las citas del cuerpo son referencias compactas [n], sin repetir enlaces largos
tras cada párrafo. La misma fuente solo recibe una referencia en el cuerpo y una
entrada en «Fuentes utilizadas». El clic abre el detalle sin modificar la ruta
del chat; la figura y la fuente conservan acceso al original. Se agrupan fuentes
equivalentes de un mismo documento y conjunto de páginas.

Las respuestas ya guardadas conservan su contenido y metadatos anteriores. La
correspondencia nueva se aplica al generar respuestas nuevas, no reescribe la
conversación del usuario.

## Preparación y recuperación

- `section_structure.py` reconstruye temas a partir de títulos, tipografía,
  columnas y orden de lectura. Un título del mismo nivel cierra el tema anterior;
  un subtítulo conserva la relación con su padre. No cruza documentos, páginas
  ausentes ni layouts ausentes. Las listas de piezas a dos columnas de las
  páginas verticales permanecen dentro del mismo tema; las páginas horizontales
  del propietario tienen flujos por columnas.
- Los fragmentos de navegación tienen hasta 2.000 caracteres con solapamiento.
  Retienen su sección, página y región. Los títulos, equivalencias de vocabulario
  español/portugués y etiquetas revisadas ayudan al ranking. Se descartan palabras
  genéricas de las preguntas y exclusiones negativas de las etiquetas.
- BM25 y los 546 vectores existentes siguen localizando candidatos de página.
  Ese ranking aporta una señal al ranking de fragmentos/secciones; después se
  expande dentro del tema elegido. **No se reconstruyó ni se presenta como nuevo
  un índice vectorial de fragmentos por sección.** No hace falta migración.
- Se recuperan como máximo ocho páginas y se declara
  `section_context_complete=false` si el tema excede ese límite. Gemini recibe
  las imágenes originales y las áreas de lectura, nunca el texto OCR de los
  fragmentos como evidencia técnica aprobada.
- Las figuras deben tener sección e identidad identificable. Se comprueban
  componente y eje, y se comparan las identidades dentro del tema para excluir
  ilustraciones vecinas. Una asociación ambigua, sin leyenda o que cruza un
  límite se omite. Sin bundle estructural solo se ofrecen identificaciones
  revisadas, no dibujos elegidos por tamaño.
- Algunos dibujos aparecen **antes** del título o abarcan dos columnas. Los
  enlaces revisados de `figure-labels-v1.json`, ligados al hash de la página,
  permiten indicar su tema explícitamente sin adivinar por proximidad.
- La validación comprueba pertenencia a la sección y citas, y fija el epígrafe a
  la identidad del catálogo. La explicación libre de Gemini queda en párrafos.
  Se mantienen los controles de SHA-256, originales privados y rechazo de IDs
  desconocidos. Un bundle incompatible falla con 503; no degrada silenciosamente
  a ilustraciones potencialmente incorrectas.

## Instalación reproducible

Desde la raíz del proyecto, con el entorno Python local y los layouts existentes:

```powershell
.venv/Scripts/python.exe scripts/prepare_manual_figures.py --library data/private/manuals/library-v1 --output data/private/manuals/figures-v5
.venv/Scripts/python.exe scripts/prepare_manual_sections.py --library data/private/manuals/library-v1 --figures data/private/manuals/figures-v5 --layouts data/private/manuals/reviewed --output data/private/manuals/sections-v6
```

Los destinos deben ser nuevos. Nunca se sobrescribe un bundle instalado. La
preparación verifica páginas, imágenes y hashes de las identificaciones
revisadas; el manifiesto se escribe después de completar la preparación.

Configuración local Docker (rutas privadas excluidas de Git):

```dotenv
MANUAL_FIGURES_PATH=/manual-figures
MANUAL_FIGURES_DIRECTORY=./data/private/manuals/figures-v5
MANUAL_SECTIONS_PATH=/manual-sections
MANUAL_SECTIONS_DIRECTORY=./data/private/manuals/sections-v6
```

Después: `docker compose up -d --build api frontend`.
`GET /assistant/status` informa también la disponibilidad y cantidad de temas.

Bundle instalado: 572 secciones automáticas y 597 asignaciones de figuras;
las asignaciones sin identidad suficiente permanecen excluidas. Se conservan
los 598 recortes y todas las páginas originales. Tres límites del caso de frenos
y diez identidades tienen revisión visual, cinco con enlace explícito al tema.

- Figuras v5 SHA-256:
  `145f08781556d8f9ed09a98ec764adf46e17039b8780151c7ce898ef30016bd6`.
- Secciones v6 (geometría original por región, esquema 2) SHA-256:
  `eec0a026cb7d0254f8d7e7c9ba9cdb59c5955e5fecd0f851f3889cfea3cab892`.
- La biblioteca original y su índice vectorial conservan sus versiones previas.

La versión v6 conserva los temas y figuras de v5 e incorpora las dimensiones
originales en 1.259 regiones para preparar la vista de Gemini. Requiere Pillow
en el backend. Los bundles anteriores sin geometría deben prepararse de nuevo;
no se reutilizan silenciosamente con lectura de página completa. Ver
[lectura visual enfocada](CONVERSATION_RETRIEVAL.md).

## Validación de la entrega original y límites

Se agregaron once casos automatizados con un manual sintético: continuación a la
página anterior, cierre en el título siguiente, temas vecinos, jerarquía,
columnas, enlaces revisados, exclusiones negativas, epígrafes y rechazo de
bundles desactualizados. La suite completa actual tiene **106 pruebas**.
Build TypeScript/Vite, formato frontend, Ruff y `git diff --check` también se
ejecutaron durante este bloque.

Se ejecutaron cuatro consultas reales declaradas en `section-cases-v1.json` y
los doce casos de regresión anteriores. En la primera ronda de frenos, dos
salidas de Gemini fueron rechazadas por el esquema (HTTP 502); las otras dos
respondieron correctamente. Los dos reintentos conservaron los mismos mensajes
y respondieron con VI.16 y citas PDF 211/212. Los doce casos anteriores
respondieron HTTP 200 y pasaron sus comprobaciones automáticas. Se inspeccionaron
las identidades de las imágenes devueltas, además de los resultados automáticos.
Los rechazos iniciales se preservan en la evidencia; no se presentan como un
primer intento exitoso ni se eliminan las validaciones para aceptarlos.

Evidencia privada: `section-fidelity-live-v1.json`,
`section-recheck-rear-v2.json`, `section-recheck-explicit-v2.json`,
`section-regression-live-v1.json`, `section-final-audit-v1.json` y
`ui-section-cylinder.png`, dentro de `data/private/manuals/`.
Se comprobó en el navegador la figura VI.16, la apertura de la fuente desde [2]
sin salir del chat y la recarga de una respuesta persistida. Las evaluaciones
usan vehículos sintéticos separados del vehículo real.

Los casos que sirvieron para ajustar el sistema son regresión/calibración, no
una medición independiente de precisión. La jerarquía y las columnas siguen
siendo un borrador automático fuera de los límites revisados; necesitan ampliar
el cotejo, particularmente en diagramas sin leyenda y layouts poco frecuentes.
No se aprobó todo el OCR ni se certificó la corrección mecánica del manual.
La pregunta sobre el motivo de no abrir el refrigerante caliente continúa
respondiendo principalmente la advertencia literal; no se da por cerrado ese
pendiente de explicación. También persisten pequeñas mezclas de vocabulario
portugués en algunas generaciones. Los errores de formato del proveedor siguen
siendo rechazados y admiten reintento; no se afirma disponibilidad perfecta.
