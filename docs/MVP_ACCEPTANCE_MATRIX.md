# Matriz de aceptación del corpus inicial

Revisión: 2026-10-24. Esta matriz distingue integridad de evidencia, cotejo de transcripción y aceptación para responder sobre un vehículo. El propietario ya seleccionó el registro objetivo y aclaró que los demás eran pruebas del mismo auto. La selección, los datos declarados y sus modificaciones se conservan en `data/private/manuals/acceptance-target.json`, fuera de Git. El código de motor continúa desconocido; los datos declarados no prueban por sí solos cobertura del manual.

Decisión vigente: se usa el Gol de fábrica como referencia de búsqueda para el MVP. Los ocho pasajes de testigos y el contexto de tablero pueden seleccionarse como referencia del manual original; no quedan excluidos por las modificaciones. Se mantiene explícita la variante descrita por cada fuente, sin mezclar numeraciones. Gemini recibe las modificaciones reales y distingue su interpretación del texto documentado. No se requiere confirmar equivalencias de sensores o cableado antes de probar la recuperación base.

## Comprobación ejecutada

Se ejecutó `validate_passage` sobre los 22 artefactos privados actuales. Pasaron las comprobaciones de huellas del PDF, metadatos, imagen de página, OCR original, coordenadas y recortes; dimensiones de recortes, idioma y composición del texto. El informe privado es `data/private/manuals/acceptance-integrity-2026-10-24.json` e incluye la huella de cada artefacto cotejado.

Resultado: 22 pasajes con integridad comprobada, cero habilitados para RAG. Esta ejecución no vuelve a revisar visualmente las páginas ni confirma compatibilidad, vigencia o exactitud técnica. El cotejo visual anterior está documentado en `MVP_REVIEW_LOG.md`.

## Inventario de revisión por grupo

La tabla conserva las comprobaciones de aplicabilidad exacta identificadas en la auditoría anterior. Para la entrega inmediata, las condiciones sobre el montaje real se tratan como límites de aplicación que Gemini debe contextualizar, no como requisitos que bloqueen toda consulta. La aceptación se realiza como referencia de fábrica conforme a `CORPUS_ACCEPTANCE.md`. Siguen vigentes las exclusiones por texto ambiguo y la necesidad de identificar la variante que describe cada fragmento.

P = manual de propietario; R = manual de reparación. Las páginas son las del PDF.

| Pasajes | Páginas | Decisión para el primer conjunto | Evidencia o trabajo pendiente |
| --- | --- | --- | --- |
| `owner-source-cover`, `owner-engine-identification`, `repair-source-title` | P 1, P 12; R 3 | Solo identificación; fuera del corpus de diagnóstico | Completar edición/cobertura. Las ubicaciones ilustradas no identifican el motor real. |
| `owner-220-240-context` | P 32 | Referencia visual de variante; fuera del corpus de diagnóstico | Identificar el tablero real antes de asociar sus números con los testigos. |
| `repair-pressure-ambiguity` | R 74 | Excluido de instrucciones y de evidencia técnica habilitada | La unidad impresa está incompleta. Conservarlo para el caso de abstención X04, sin completar ni convertir cifras. |
| `owner-200-temperature`, `owner-220-240-temperature` | P 28–29, P 33–34 | Pendientes; seleccionar únicamente la variante compatible | Confirmar tablero y alcance del manual. Recortar referencias a fusibles fuera del conjunto y excepciones no aplicables; conservar advertencias y continuidad. |
| `owner-200-charging`, `owner-220-240-charging` | P 30, P 35 | Pendientes; seleccionar únicamente la variante compatible | Confirmar tablero. Excluir instrucciones de correa fuera del alcance y afirmaciones de causa que no estén comprobadas para el caso. |
| `owner-200-oil`, `owner-220-240-oil` | P 30, P 35–36 | Pendientes; seleccionar únicamente la variante compatible | Confirmar tablero y contexto de nivel/reposición. Mantener distinción entre presión y nivel y conservar advertencias. |
| `owner-200-brakes`, `owner-220-240-brakes` | P 31, P 36 | Pendientes; seleccionar únicamente la variante compatible | Confirmar tablero y contexto del depósito. No convertir una indicación histórica en autorización para seguir circulando. |
| `owner-engine-bay` | P 87 | Pendiente como contexto de componentes | Verificar montaje/motor y correspondencia de la figura. Mantener la discrepancia de referencia de frenos como anotación separada. |
| `owner-oil-level`, `owner-oil-topup` | P 89–90 | Candidatos a primer lote, todavía pendientes | Confirmar motor/varilla y cobertura. Delimitar lectura de nivel conservando advertencias; no transformar zonas en volúmenes ni adoptar productos o porciones históricas sin validación. |
| `owner-coolant-level`, `owner-brake-fluid` | P 91–92 | Candidatos a primer lote, todavía pendientes | Confirmar cobertura y depósito/montaje. Separar productos y proporciones históricas; conservar advertencias. No añadir especificaciones ausentes ni deducir umbrales. |
| `repair-cooling-overview`, `repair-cooling-fan-a`, `repair-cooling-fan-b` | R 69, R 72–73 | Pendientes; postergar respecto del primer lote | Establecer montaje y variante con evidencia. No asignar aire acondicionado por la apariencia del dibujo ni mezclar numeración. |
| `repair-thermal-switch-context` | R 74–75 | Pendiente; postergar respecto del primer lote | Identificar interruptor, etapas, montaje y aire acondicionado; resolver escala de unidad con evidencia. La tabla no define umbrales de seguridad del motor. |

Los grupos cubren los 22 IDs una sola vez: tres de identificación, uno de contexto de variante, uno excluido y 17 pasajes técnicos pendientes. Que un candidato pueda formar parte del primer lote no constituye aprobación.

## Preparación de la ingesta

1. Usar el registro objetivo confirmado en el archivo privado y mantener explícitos los datos desconocidos. No combinar hechos de registros de prueba. Mercado de fabricación y mercado de comercialización no se intercambian por inferencia.
2. Seleccionar un lote pequeño de pasajes cotejados y registrar su alcance como referencia de fábrica. Conservar las condiciones de variante impresas en la fuente; las modificaciones reales se contextualizan en la respuesta sin impedir la búsqueda base.
3. Delimitar fragmentos con páginas, texto original, advertencias y vínculo al pasaje cotejado. El contrato admite `pages` con la lista completa de páginas PDF y conserva compatibilidad con `page` singular. Las nuevas citas deben declarar todas las páginas utilizadas, sin inferir las de citas históricas. Ver `RAG.md`.
4. Registrar aprobación para referencia de fábrica, responsable, referencia de revisión y alcance. Implementar una referencia de búsqueda separada de los hechos reales, conservando modificaciones en el contexto de Gemini. No es requisito ampliar primero el modelo de datos para cada tablero, varilla o montaje; sí preservar qué configuración describe la fuente y evitar atribuirla como hecho comprobado del auto.
5. Validar el conjunto y sus originales; conservar una copia del corpus activo antes de reemplazarlo mediante el importador administrativo.
6. Probar recuperación bajo la referencia de fábrica, conservación del contexto de modificaciones, rechazo de especificaciones de otros motores y citas persistentes. Comprobar preguntas españolas sobre las fuentes portuguesas del lote y respuestas reales en el chat. La falta de cobertura debe quedar explícita.

## Resultado de este bloque

La integridad de los 22 pasajes está verificada y el vehículo objetivo está seleccionado. El primer lote parte de niveles y depósitos, con posibilidad de incorporar otros pasajes cotejados como referencia de fábrica. Continúan pendientes delimitación, importación y prueba real del circuito. Esta actualización del plan no modifica hechos del auto, transcripciones, aprobaciones ni el corpus de la aplicación.
