# Plan de implementación

## Ampliación vigente — manuales completos, 2026-10-24

Por pedido del propietario se amplía la cobertura a los dos PDF completos: 532 páginas. El OCR sin revisar solo localiza páginas; Gemini lee las imágenes originales recuperadas y sus continuaciones. Esto amplía el acceso documental sin aprobar las transcripciones pendientes. Los cinco fragmentos revisados siguen activos y las modificaciones reales se conservan.

- [x] Exportar 144 páginas del propietario y 388 de reparación, con hashes y correspondencia al PDF.
- [x] Implementar navegación bilingüe y lectura visual de páginas originales con Gemini.
- [x] Distinguir las páginas de lectura automática de los pasajes revisados y permitir abrir la imagen citada.
- [x] Mantener referencia de fábrica, modificaciones y reglas de seguridad incluso si la biblioteca falla.
- [x] Probar respuestas reales sobre neumáticos, embrague y fusibles. La primera consulta de fusibles agotó el timeout; el reintento respondió con cita. Registro privado conservado.
- [ ] Revisar técnicamente todo el OCR y las tablas; disponer de los PDF completos no equivale a validar todo su contenido.
- [ ] Añadir recuperación semántica y evaluar más preguntas y variantes.
- [ ] Completar recorrido visual de la interfaz en navegador.

Detalle reproducible, pruebas y límites: [FULL_MANUAL_LIBRARY.md](docs/FULL_MANUAL_LIBRARY.md). La sección siguiente conserva el alcance del MVP anterior.

## Decisión vigente del MVP — referencia de fábrica, 2026-10-24

Por indicación del propietario, la búsqueda documental usará el Gol G2 1.6 MI 1998 en configuración original de fábrica como referencia de trabajo. Las modificaciones no bloquearán la recuperación de los manuales base. Esta referencia es una suposición explícita de búsqueda: los datos reales y las modificaciones del auto se conservan y se entregan a Gemini para contextualizar la respuesta.

Flujo objetivo: pregunta → consulta del subconjunto revisado de manuales usando la referencia de fábrica → fragmentos con páginas y procedencia → Gemini responde apoyándose en esas fuentes y explica cómo las modificaciones conocidas podrían afectar su aplicación. La interpretación de modificaciones debe distinguirse del contenido del manual. Sin evidencia suficiente, se declara el límite de cobertura y no se inventan citas.

La entrega inmediata debe demostrar este circuito con algunas partes revisadas del manual. No requiere resolver cada modificación ni incorporar todos los manuales, pgvector o búsqueda web primero. Se conservan el cotejo del texto, las advertencias y las unidades originales; las ambigüedades documentales no se corrigen por inferencia. Los fragmentos para otros motores o variantes no se presentan como especificaciones confirmadas del auto.

Esta decisión reemplaza los bloqueos anteriores basados en modificaciones del vehículo, incluida la exclusión automática de pasajes del tablero original. Las entradas históricas se conservan como registro del trabajo anterior.

### Próximo bloque y criterio de cierre

- [x] Preparar y aprobar para referencia de fábrica un lote pequeño de pasajes ya cotejados, con texto, páginas y alcance explícitos; comenzar por niveles y depósitos y ampliar a otros temas revisados según las preguntas de prueba.
- [x] Incorporar la referencia de búsqueda de fábrica separada de los hechos reales; conservar modificaciones en el contexto de Gemini y registrar la referencia usada con la respuesta.
- [x] Importar el lote real a PostgreSQL y comprobar recuperación para preguntas en español, incluyendo los pasajes portugueses. Resolver lo necesario para esa cobertura acotada; la implementación vectorial completa sigue en un bloque posterior.
- [ ] Verificar respuestas reales con Gemini y desde el chat: fuentes relevantes, páginas correctas, distinción entre manual e interpretación de modificaciones y aviso cuando el tema no esté cubierto.
- [x] Demostrar que una modificación registrada no bloquea la consulta base, que se conserva en el contexto y que un fragmento de otro motor no se usa como especificación del vehículo.

El bloque se cierra con un corpus real no vacío y preguntas de ejemplo respondidas usando sus fuentes. La ampliación al contenido de los manuales completos se hará después, por lotes revisados. El lote v1 ya está importado y probado con Gemini real por HTTP. Sigue pendiente el recorrido visual en navegador, bloqueado por las herramientas disponibles.

## Checklist consolidada — revisión 2026-10-24

Estado contrastado con código, migraciones, pruebas y servicios locales. `[x]` indica alcance implementado; los bloques con pendientes permanecen abiertos. Las entradas posteriores conservan el historial y pueden describir estados anteriores.

### Preparación documental (parcial)
- [x] Comparar checkout con GitHub y reparar origin/main.
- [x] Buscar fuentes y descargar candidatos fuera de Git.
- [ ] Verificar edición, autoría, cobertura y calidad de cada PDF.
- [x] Conservar originales y generar OCR con correspondencia por página para ambos manuales.
- [x] Seleccionar un conjunto acotado de páginas para los casos de la primera versión: 22 páginas y 20 escenarios documentados, pendientes de aprobación técnica y ejecución.
- [ ] Cotejar en ese conjunto texto, tablas, unidades, cifras, ilustraciones y aplicabilidad; registrar incertidumbre sin completarla por inferencia.
- [x] Cotejar 22 pasajes y 41 tramos del conjunto seleccionado; conservar evidencia y bloqueos. Esto no aprueba páginas completas ni aplicabilidad.
- [x] Crear un corpus didáctico propio redistribuible para probar ingesta y recuperación: `backend/examples/rag`, exclusivo del vehículo ficticio RAG-DEMO.
- [ ] Ampliar el corpus didáctico para cubrir los 20 escenarios y la demo pública.
- [x] Aceptar e importar un subconjunto revisado como referencia del Gol de fábrica según la decisión vigente; las modificaciones se contextualizan en la respuesta. El corpus activo contiene cinco fragmentos reales; ver docs/MVP_REAL_CORPUS.md.
- [x] Verificar nuevamente la integridad de los 22 pasajes y preparar una matriz de aceptación por fragmento: `docs/MVP_ACCEPTANCE_MATRIX.md`. El propietario confirmó el vehículo objetivo; sus modificaciones y selección se conservan en privado. La exclusión automática por instrumental modificado fue reemplazada por la referencia de fábrica del MVP.

### A — API y persistencia (completo para el alcance acordado)
- [x] FastAPI/Pydantic, SQLAlchemy, PostgreSQL y migraciones Alembic 0001–0006.
- [x] Vehículos, incidencias, síntomas, mediciones por API, estados, resolución e historial persistente.
- [x] Contexto del auto: marca, modelo, año, kilometraje, modificaciones y campos desconocidos opcionales.
- [x] Conversaciones persistentes; primer mensaje crea un pendiente y los reintentos no duplican el mensaje.
- [x] To-do con checks reversibles, fecha, kilómetros, notas, costo decimal y total de importes registrados.
- [x] Docker Compose con PostgreSQL, API y frontend. Persistencia tras reinicio documentada en el bloque original.

### B — Asistente y fuentes (parcial)
- [x] Adaptador Gemini, contexto del auto/historial y respuestas estructuradas persistentes.
- [x] Manejo de errores, reintento manual sin duplicar mensajes y control de concurrencia.
- [x] Selector de modelo en el chat, validado en backend y conservado por navegador.
- [x] Pruebas reales de conectividad y generación registradas; mejora puntual de latencia con Flash-Lite. No equivalen a evaluación mecánica.
- [x] Cuatro reglas determinísticas de advertencia y validación de identificadores de citas.
- [x] Ingesta administrativa transaccional con aprobación explícita y comprobación SHA-256.
- [x] Recuperación textual en PostgreSQL, filtrado de compatibilidad y consulta de fuentes sin Gemini.
- [x] Citas de varias páginas en ingesta, recuperación, contexto, respuestas persistentes e interfaz; lectura compatible con citas antiguas de una página.
- [ ] Habilitar el lote real de referencia de fábrica y verificar el circuito completo, con modificaciones como contexto para Gemini.
- [ ] Embeddings y recuperación semántica con pgvector; hoy se usa búsqueda textual.
- [ ] Estrategia multilingüe y evaluación de relevancia para consultas en español y fuentes en portugués.
- [ ] Búsqueda web complementaria con fuentes explícitas cuando falte evidencia documental.

### C — Interfaz en español (parcial)
- [x] React/TypeScript: chat por problema, historial, Mi auto y To-do con costos.
- [x] Registro y edición del auto, tareas, resolución y respuestas del asistente.
- [x] Presentación de fuentes citadas y estados de error/falta de evidencia. Las mediciones se retiraron de la interfaz a pedido del propietario; permanecen en API e historial.
- [x] Recorridos manuales de navegador documentados en `docs/FRONTEND.md`.
- [ ] Comprobar desde navegador diagnóstico con manuales reales aprobados y búsqueda web, una vez completado B.

### D — Pruebas y evaluación (parcial)
- [x] Definir 20 escenarios y sus criterios en `docs/MVP_CASES.md`.
- [x] Suite automatizada de backend con proveedor simulado y PostgreSQL real: 46 pruebas pasan en esta revisión.
- [x] Herramientas documentales: 24 pruebas pasan en esta revisión.
- [x] Compilación TypeScript/Vite y formato del frontend correctos.
- [ ] Ejecutar los 20 escenarios de extremo a extremo; evaluar por separado citas, abstención, seguridad y recuperación.
- [ ] Evaluación mecánica real de Gemini y comparación de calidad/latencia entre modelos con casos representativos.
- [ ] Configurar CI con GitHub Actions.
- [ ] Revisar las 72 observaciones de Ruff detectadas con la configuración actual al ejecutar `python -m ruff check backend scripts` (48 C408, 18 I001 y seis restantes). No se corrigieron durante esta revisión documental.

### E — Demo y entrega (pendiente)
- [ ] Exportar casos sintéticos y respuestas guardadas para demo de lectura.
- [ ] Construir/publicar demo estática en GitHub Pages, sin claves ni llamadas a IA.
- [ ] Preparar capturas y guion de video; completar documentación de entrega.

### Evidencia de esta revisión

- Backend: desde `backend`, `..\.venv\Scripts\python.exe -m pytest -q`: **46 passed**, una advertencia de deprecación de Starlette/httpx. El fixture usa una base PostgreSQL temporal, aplica migraciones y comprueba diferencias con los modelos.
- Documentos: `.\.venv\Scripts\python.exe -m pytest -q scripts/tests`: **24 passed**.
- Frontend: `npm run build` y `npm run format:check`: correctos.
- `docker compose ps`: tres servicios activos, PostgreSQL healthy. `/ready`: ready. `/assistant/status`: configured=true, approved_passages=0, web_search=false; informa los dos modelos disponibles.
- `git diff --check`: sin errores de whitespace; Git avisa de futuras conversiones LF/CRLF.
- No se repitieron llamadas pagas a Gemini, reinicios de servicios ni recorridos de navegador en esta revisión. Las pruebas reales y visuales anteriores se distinguen de las ejecutadas hoy. Hay cambios locales previos sin commit; esta checklist incluye el estado del checkout.

Orden recomendado: lote real revisado + referencia de fábrica + recuperación de preguntas españolas + respuestas con citas y contexto de modificaciones → recuperación semántica/multilingüe con pgvector → ampliación por lotes de los manuales → búsqueda web → evaluación completa de 20 casos → CI y demo. El primer recorrido del chat con fuentes reales se comprueba en el primer bloque. La corrección de Ruff puede hacerse como bloque independiente.

## Decisiones
- Monolito modular y RAG propio; sin agentes ni frameworks de orquestación.
- Backend local con Docker; demo pública estática sin claves ni llamadas a IA.
- Sin fotos ni OCR dentro del producto. La experiencia principal pasa a ser un chat de mantenimiento con contexto persistente del auto y búsqueda web complementaria; esta decisión reemplaza la exclusión inicial del chat y la web.
- La primera versión usará un conjunto acotado de páginas bien revisadas según `docs/MVP_CORPUS.md`. La revisión profunda de ambos manuales completos queda pendiente para una etapa posterior y no bloquea la implementación del MVP. La preparación documental queda fuera de los 3–5 días orientativos de construcción.
- Los commits y pushes son manuales y corresponden al propietario.

## Citas de varias páginas — 2026-10-24

Se completó el primer paso del bloque documental: `pages` conserva todas las páginas PDF de un fragmento durante ingesta, recuperación, envío de contexto, guardado de respuestas y presentación en el chat. `page` se conserva como primera página para compatibilidad; los documentos y respuestas anteriores siguen siendo legibles sin reescribir el historial. Se validan páginas positivas, enteras, únicas y ordenadas, sin completar páginas intermedias. No requiere migración SQL.

Pasaron 63 pruebas de backend contra PostgreSQL temporal, incluidas recuperación de páginas consecutivas y separadas, contexto enviado al proveedor simulado, persistencia al recrear la aplicación y retirar el corpus, lectura de registros antiguos y rechazo transaccional de listas inválidas. La advertencia de deprecación Starlette/httpx continúa. Pasaron build y formato del frontend, cuatro comprobaciones del HTML renderizado del componente de citas y Ruff sobre los dos archivos Python modificados. No se realizó un nuevo recorrido visual en navegador ni una llamada real a Gemini.

Docker construyó y actualizó API/frontend; `/ready` respondió ready y la interfaz HTTP respondió 200. La aplicación conserva cero fragmentos habilitados. Continúan pendientes la delimitación/aceptación del primer lote y los requisitos de compatibilidad para fuentes condicionadas por montaje o instrumental. Contrato y límites en `docs/RAG.md`.

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

## Prioridad mecánica y primer bloque de API - 2026-10-23

El propietario indicó que desconoce datos de variante y pidió priorizar usos mecánicos y arreglos. Se registran como desconocidos, sin detener la implementación del flujo de incidencias ni aprobar especificaciones por inferencia. Las decisiones documentales están en `docs/CORPUS_ACCEPTANCE.md`; no se habilitaron fragmentos para RAG.

Se implementó el bloque A con FastAPI/Pydantic, SQLAlchemy, migración Alembic y PostgreSQL en Docker: vehículos con campos opcionales, incidencias con síntomas/kilometraje, mediciones decimales con unidad/condiciones y resolución obligatoria para cerrar. Incluye consulta de historial por vehículo/estado y límites de integridad en API y base. Las mediciones no se interpretan como diagnósticos.

Pasaron 14 pruebas de integración en una base PostgreSQL temporal creada por el fixture: migración desde cero, repetición sin cambios pendientes, persistencia al recrear la aplicación, validación de entradas, restricciones de cierre, relaciones y borrados. Además se verificó un caso sintético vía HTTP en la API de Compose y se comprobó que su resolución y medición persistían tras reiniciar tanto API como PostgreSQL. Se conserva ese ejemplo local identificado como sintético; los datos de pruebas automatizadas se eliminaron con su base temporal.

Docker Desktop falló al iniciar por un socket de ejecución inaccesible; se recuperó conservando las carpetas temporales y sin restablecimiento de fábrica. Procedimiento y comprobación en `docs/DOCKER_RECOVERY.md`. La primera ejecución de pruebas se interrumpió al investigar una demora; se repitió exitosamente usando 127.0.0.1, y se retiró solo la base temporal de aquella ejecución. Las conexiones de la API tienen un tiempo máximo de conexión de cinco segundos.

Uso y límites del backend: `docs/BACKEND.md`. Siguen pendientes frontend, IA, ingesta, corpus didáctico y CI. El siguiente bloque puede construir la interfaz del flujo mecánico sobre esta API, antes de incorporar diagnóstico documental.

## Interfaz del registro mecánico - 2026-10-23

Se incorporó React/TypeScript con Vite y estilos adaptables en español. La entrada principal es `http://localhost:5173`; Swagger en el puerto 8000 sigue disponible como herramienta técnica. Compose construye la interfaz y la sirve con Nginx, que deriva `/api` al backend existente. No se modificó el modelo de datos ni se agregaron diagnósticos simulados.

Incluye alta/edición de vehículos con datos desconocidos opcionales, registro/edición de averías, síntomas, kilometraje, mediciones con unidad/condiciones, estado en reparación, cierre con resolución y corrección de la resolución. El historial permite búsqueda y filtros por estado. La lectura recorre la paginación de la API. No se implementó borrado de averías en la interfaz.

Pasaron compilación TypeScript/Vite, comprobación de formato y construcción de la imagen Docker. Se recorrió la aplicación en navegador con datos sintéticos: alta y edición, rechazo de exceso de decimales, guardado exacto de `1,2500`, cierre obligatorio, edición de una avería cerrada conservando resolución y recarga del detalle persistido. También se verificaron búsqueda/filtros, error de registro inexistente y disposición en escritorio y pantalla pequeña. Son comprobaciones manuales asistidas, no una suite automatizada de frontend. Detalles y pasos reproducibles en `docs/FRONTEND.md`.

Continúan pendientes Gemini, RAG, aceptación documental, corpus didáctico, evaluación real y CI. El bloque C permanece parcial hasta integrar diagnóstico y fuentes.

## Cambio de experiencia: chat y contexto del auto

El propietario pidió una experiencia utilizable mientras arregla el auto: describir el problema en un chat, conservar kilometraje y modificaciones y registrar pendientes por detrás. Se reemplaza el tablero principal por una conversación y el menú Mi auto (datos, pendientes, trabajos y conversaciones). El backend de vehículos, incidencias, mediciones y resoluciones se conserva.

La migración 0002 agrega kilometraje/modificaciones opcionales y mensajes persistentes. El primer mensaje crea una incidencia con el kilometraje informado del auto; los siguientes se agregan al mismo caso. Los reintentos de un mismo mensaje usan un identificador estable para no crear otro pendiente. Los trabajos realizados pueden registrarse desde el menú. Los registros anteriores siguen accesibles.

Esta entrega cambia la interfaz y el registro persistente, pero no conecta un modelo. Las confirmaciones de guardado están identificadas como tales. El próximo bloque debe incorporar el asistente: contexto del auto e historial, consulta de manuales compatibles, búsqueda web complementaria con fuentes explícitas, preguntas de seguimiento y reglas de seguridad. No se considera que el modelo esté entrenado con los manuales ni que los fragmentos pendientes estén aprobados.

Validación: 17 pruebas de integración de backend, compilación del frontend y construcción Docker. Se comprobó en navegador el contexto del auto, el primer mensaje con creación automática de pendiente, un seguimiento persistido tras recarga y un trabajo independiente desde el menú. Los registros previos siguen visibles. Detalle y límites en `docs/FRONTEND.md`.

## Simplificación del chat: mediciones

Se retiraron el botón Agregar medición, su formulario y su envío desde la interfaz a pedido del propietario. La conversación conserva la acción para registrar cómo se resolvió el problema. Los datos históricos de mediciones y su contrato de API se conservan.

## Datos principales y tareas unificadas

Marca, modelo, año y kilometraje quedan visibles en Datos del auto y en su edición. Pendientes y trabajos se unifican en Tareas, con checks reversibles, pendientes primero y fecha, kilómetros y notas del trabajo. La migración 0003 separa estos metadatos del registro original de la avería; los datos antiguos se conservan sin inferir valores desconocidos.

Validación de tareas: 19 pruebas de integración contra PostgreSQL, build TypeScript/Vite, Ruff y construcción Docker correctos. En navegador se verificaron los datos principales, el check de un caso sintético y la persistencia de fecha, kilómetros y notas tras recargar, con pendientes primero.

## To-do en tabla

Se renombra Tareas a To-do y se presenta como tabla con check, fecha del trabajo, descripción, kilómetros y costo. Pendientes primero; tocar una celda abre la edición de sus detalles. El costo es dinero ya pagado, en una misma moneda elegida por el usuario, y el total suma todos los importes cargados del auto, también los pendientes. Un costo vacío no significa cero y se indica cuántos faltan. PostgreSQL usa Numeric(14,2) y la suma visual usa centavos enteros. La migración 0004 conserva los registros anteriores con costo desconocido.

Verificación: 25 pruebas de integración y build TypeScript/Vite correctos. En navegador se guardó un costo sintético de 1234,56, se recargó la página y se comprobó el total 1.234,56. La tabla permite desplazamiento horizontal en pantallas estrechas.

## Asistente con contexto: integración preparada

Se implementó el adaptador Gemini, respuestas estructuradas persistentes (migración 0005), contexto del auto/historial, reintentos sin reenviar mensajes, validación de citas y cuatro reglas de advertencia. La interfaz muestra respuestas y distingue falta de clave o evidencia. El propietario configurará la clave después; no se probaron respuestas reales.

Pasaron 35 pruebas contra PostgreSQL con proveedor simulado y compilación TypeScript/Vite. El bloque B continúa parcial: recuperación provisional por palabras, sin corpus real aprobado habilitado, pgvector ni búsqueda web. La evaluación completa de los 20 escenarios sigue pendiente. Configuración, privacidad, contrato y límites en docs/ASSISTANT.md.

## Ingesta y recuperación documental local

Se incorporó la migración 0006, importador transaccional con comprobación SHA-256 del original, recuperación textual en PostgreSQL y consulta de fuentes por vehículo sin Gemini. El chat utiliza esas fuentes antes de generar la respuesta. Se agregó material didáctico propio limitado a un vehículo ficticio para reproducir el circuito.

Se inventariaron 22 pasajes cotejados y 30 vínculos a figuras; ninguno está aprobado para RAG. Se conservan sus bloqueos de aplicabilidad y no se importan a producción. El bloque B continúa parcial: faltan aceptación documental, recuperación semántica con pgvector, evaluación de relevancia, búsqueda web y prueba real de Gemini. Procedimiento y evidencia: docs/RAG.md.

## Corrección del timeout de Gemini

Una prueba real confirmó una generación de 54,23 segundos frente al límite anterior de 25. Se amplió el transporte a 60 segundos, el proxy a 90 y se configuró razonamiento low para Gemini 3.8 Flash. Se distinguen errores de conexión y timeout. Pasaron 13 pruebas del adaptador; el reintento real del mensaje guardado respondió en 40,01 segundos y se persistió. Detalles en docs/ASSISTANT.md.


## Velocidad conversacional

Se selecciona Gemini 3.5 Flash-Lite como modelo predeterminado tras comprobar disponibilidad y dos respuestas reales: 1,84 s con contexto mínimo y 3,91 s a través de la aplicación con contexto completo. El prompt solicita respuestas breves conservando advertencias. Pasaron 19 pruebas del asistente/corpus y Docker. Se conserva el contexto y siguen pendientes evaluación mecánica completa y mediciones de latencia representativas. Evidencia y límites: docs/ASSISTANT.md.

## Elección del modelo desde el chat

Se incorpora un selector junto al cuadro de mensaje, con preferencia persistida por navegador y validación en backend. La elección se aplica a próximas respuestas; las existentes conservan su modelo. Pasaron 15 pruebas del asistente y compilación TypeScript/Vite. Contrato y comportamiento en docs/ASSISTANT.md.
