# Plan de implementación

## Preparación documental (en curso)
- [x] Comparar checkout con GitHub y reparar origin/main.
- [x] Buscar fuentes y descargar candidatos fuera de Git.
- [ ] Verificar edición, autoría, cobertura y calidad de cada PDF.
- [x] Conservar originales y generar OCR con correspondencia por página para ambos manuales.
- [x] Seleccionar un conjunto acotado de páginas para los casos de la primera versión: 22 páginas y 20 escenarios documentados, pendientes de aprobación técnica y ejecución.
- [ ] Cotejar en ese conjunto texto, tablas, unidades, cifras, ilustraciones y aplicabilidad; registrar incertidumbre sin completarla por inferencia.
- [ ] Crear corpus didáctico redistribuible para pruebas.

## Bloques posteriores
- [ ] A: API, PostgreSQL, migraciones, vehículos, incidencias y mediciones; persistencia tras reinicio.
- [ ] B: ingesta administrativa, Gemini, pgvector, citas y seguridad; diagnóstico real verificable.
- [ ] C: interfaz en español; completar registro, diagnóstico y resolución desde navegador.
- [ ] D: 20 casos, pruebas determinísticas, evaluación real separada y CI.
- [ ] E: exportación de casos para demo de lectura en GitHub Pages, capturas y guion de video.

## Decisiones
- Monolito modular y RAG propio; sin agentes ni frameworks de orquestación.
- Backend local con Docker; demo pública estática sin claves ni llamadas a IA.
- Sin fotos, chat abierto, búsqueda web automática ni OCR dentro del producto.
- La primera versión usará un conjunto acotado de páginas bien revisadas según `docs/MVP_CORPUS.md`. La revisión profunda de ambos manuales completos queda pendiente para una etapa posterior y no bloquea la implementación del MVP. La preparación documental queda fuera de los 3–5 días orientativos de construcción.
- Los commits y pushes son manuales y corresponden al propietario.

## Revisión del OCR - 2026-10-23

- Se regeneraron las 532 páginas en una versión privada separada, con coordenadas TSV comprobables.
- Se cambió la rotación de 173 páginas de reparación y 2 de propietario respecto del OCR inicial, tras comparar orientaciones y cotejar hojas de contacto.
- Se agregaron correcciones visuales explícitas para páginas con poco texto o diagramas en varias orientaciones.
- Se conservan 73.544 cajas de palabras vinculadas a sus imágenes orientadas.
- Se localizaron cinco tablas y una figura en dos páginas del manual de reparación. El resto conserva vínculos a contexto de página completa.
- Hay 44 páginas de reparación y 25 de propietario con confianza media OCR inferior a 75. Incluyen índices, aperturas de capítulos y esquemas; la puntuación no indica por sí sola si el contenido es aprovechable.
- La revisión de cifras, unidades, estructura de tablas y referencias técnicas sigue pendiente. No se marca el corpus como validado para RAG.

Ver `docs/OCR_WORKFLOW.md` para reproducir y auditar el procesamiento.

## Separación por regiones - 2026-10-23

Se incorporó una etapa local de análisis de páginas con un modelo de distribución documental. Conserva por separado texto narrativo, ilustraciones, tablas y palabras sin asignación, sin borrar el OCR de origen. Incluye pruebas de conservación de etiquetas y unidades y auditoría de palabras y enlaces. Los resultados son borradores pendientes de cotejo técnico; las tablas todavía necesitan transcripción estructurada y revisión de cifras.

La ejecución de separación se completó sobre 532 páginas y conservó las 73.544 palabras del OCR. El informe `docs/OCR_LAYOUT_REPORT.md` registra pruebas, correcciones visuales y contenido pendiente. El corpus continúa sin habilitación como evidencia técnica para RAG.

## Cotejo inicial de tablas - 2026-10-23

Se prepararon borradores espaciales para las 95 regiones de tabla, conservando 6.025 palabras. Se cotejaron 30 celdas de un bloque de la página PDF 10 del manual de reparación; las otras tablas y secciones permanecen pendientes. Las transcripciones incluyen evidencia por celda y no habilitan automáticamente el corpus para RAG. Procedimiento y limitaciones: `docs/OCR_TABLE_REVIEW.md`.

## Alcance documental de la primera versión y segundo cotejo - 2026-10-23

Se limita la primera versión a un conjunto de páginas bien revisadas; la revisión profunda de los dos manuales completos queda como trabajo posterior. Todavía faltan la selección y aprobación de ese conjunto, incluyendo aplicabilidad por variante.

Se extendió el cotejo de la página PDF 10 (impresa 12) a los bloques de bujías, embrague, caja y frenos: 69 celdas en seis estructuras, con valores compartidos representados una sola vez. Se restauró un punto decimal que la revisión anterior había cambiado indebidamente a coma. Es cotejo de transcripción; no certifica corrección técnica ni compatibilidad. Todas las páginas siguen sin habilitación para RAG.

## Selección del corpus y casos - 2026-10-23

Se seleccionaron 22 páginas (16 de propietario y 6 de reparación), con 19 de contenido/contexto técnico y 3 de identificación. Se inspeccionaron imágenes y borradores para elegir temas, continuaciones, diagramas y diferencias de tablero; esto no constituye cotejo profundo ni aprobación de los fragmentos. La selección y exclusiones están en `docs/MVP_CORPUS.md`.

Se definieron 20 escenarios sintéticos de lubricación, refrigeración, frenos, carga, información insuficiente e incompatibilidad documental en `docs/MVP_CASES.md`. Incluyen expectativas, fuentes candidatas y criterios para comprobar citas, abstención y seguridad. No se ejecutaron diagnósticos ni evaluaciones del modelo. La página de especificaciones R 10 se conserva como trabajo previo y queda fuera del corpus inicial por falta de aplicabilidad resuelta y de necesidad para estos casos.

## Primer lote de cotejo del conjunto seleccionado - 2026-10-23

Se cotejaron cuatro secciones de P 28–31, impresas 2-15–2-18, para tablero de 200 km/h: temperatura, carga, presión de aceite y freno. Se reconstruyó orden entre columnas/páginas y texto mutilado por OCR, conservando originales. Diez recortes de texto y figuras del tablero respaldan las transcripciones privadas. El visor distingue esta capa del borrador automático y comprueba huellas de evidencia. No se aprobaron páginas completas ni aplicabilidad para RAG.

Pasaron 22 pruebas de herramientas, incluidas cinco nuevas para continuidad entre tramos, conservación de cifras, límites y ausencia de aprobación automática. Registro y pendientes en `docs/MVP_REVIEW_LOG.md`. El próximo lote es P 32–36 y después el contexto de P 87 y 89–92.

## Segundo lote de cotejo - 2026-10-23

Se cotejaron las secciones seleccionadas de P 32–36, P 87 y P 89–92. Se añadieron diez pasajes con evidencia privada y se actualizaron los pendientes de contexto del primer lote. Se preservaron cambios de numeración entre tableros, la excepción para AP-2000 y una referencia interna de frenos discrepante, sin corregir el original por inferencia.

Acumulado: 14 pasajes y 25 tramos de texto en las 14 páginas técnicas de propietario seleccionadas. No se aprueban páginas completas ni aplicabilidad. Quedan identificación (tres páginas), refrigeración de reparación (cinco páginas) y decisiones de aceptación/exclusión antes de habilitar fragmentos para RAG. Se comprobó evidencia y enlaces; pasaron 22 pruebas existentes y `git diff --check`. Detalle en `docs/MVP_REVIEW_LOG.md`.

## Tercer lote: identificación y reparación - 2026-10-23

Se cotejaron los contenidos delimitados de las ocho páginas restantes del conjunto inicial, con ocho pasajes nuevos y doce celdas de R 75. Se separó el registro de presión ambiguo de las instrucciones y se conservó la unidad literal de la tabla. La herramienta de pasajes distingue portugués/español según fuente y rechaza idioma inconsistente.

Acumulado: 22 pasajes y 41 tramos de texto en las 22 páginas seleccionadas, sin aprobar páginas completas ni aplicabilidad. Las celdas cotejadas son 81 (69 previas de R 10 y 12 de R 75). Pasaron 24 pruebas, Ruff y auditorías de evidencia/enlaces/tablas. El siguiente paso documental es la aceptación por fragmento según vehículo y fuente; la API y persistencia pueden avanzar independientemente. Detalle en `docs/MVP_REVIEW_LOG.md`.
