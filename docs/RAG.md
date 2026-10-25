# RAG documental: ingesta y recuperación local

## Estado de este bloque

La API recupera fragmentos persistidos en PostgreSQL antes de pedir una respuesta a Gemini. La consulta documental funciona sin clave ni llamadas externas. Este bloque implementa ingesta y recuperación textual; no incorpora todavía embeddings ni búsqueda semántica con pgvector. Tampoco habilita los manuales por defecto.

Se inventariaron los 22 pasajes privados cotejados y sus 30 vínculos a figuras: ninguno tiene rag_eligible=true. El informe local data/private/manuals/rag-readiness.json conserva páginas y bloqueos. Continúan pendientes los recortes de alcance y la aplicabilidad enumerados en CORPUS_ACCEPTANCE.md. No se modificaron las transcripciones, imágenes, tablas ni aprobaciones. La primera versión usará un subconjunto aprobado; revisar ambos manuales completos sigue fuera del MVP.

## Importación administrativa

### Próximo bloque acordado: referencia de fábrica

El MVP usará un subconjunto real revisado del manual y una referencia explícita del Gol de fábrica para recuperar fuentes. Las modificaciones del auto se conservarán en el contexto de Gemini para interpretar la respuesta después de la recuperación. Este cambio de criterio está planificado, todavía no implementado: el filtro descrito en «Recuperación y límites» refleja el código actual. No se debe convertir la suposición de fábrica en datos físicos confirmados ni presentar una interpretación de modificaciones como texto del manual.

La primera demostración debe recuperar fuentes para preguntas en español, responder con Gemini y mostrar páginas correctas; si el tema no aparece en el lote, debe indicar falta de cobertura. pgvector y la cobertura completa de ambos manuales se implementarán después de ese recorrido inicial. Ver el bloque de cierre en [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md).

La migración 0006 agrega document_passages. Un archivo JSON representa el conjunto completo activo, con el contrato de Passage en app/evidence.py. Cada fragmento requiere aprobación explícita, responsable, referencia de revisión, páginas PDF, texto, requisitos del vehículo y SHA-256 del original. Un PDF cotejado no queda aprobado automáticamente.

### Citas de varias páginas

Los conjuntos nuevos pueden declarar `"pages": [28, 29]` en lugar de `"page": 28`. Son números de página del PDF, comenzando en 1: entre 1 y 32 enteros positivos únicos, en orden ascendente. Se rechazan listas vacías, duplicadas, desordenadas, valores booleanos, decimales y cadenas. Una lista como `[28, 31]` cita exactamente esas páginas; no agrega las intermedias. La pertenencia y correspondencia de esas páginas con el fragmento se verifica durante el cotejo, no mediante el hash del archivo.

El formato anterior con `page` sigue aceptado y se lee como una lista de una página. La representación normalizada conserva `page` como primera página para clientes anteriores y agrega `pages` con la lista completa. Si se suministran ambos, `page` debe coincidir con el primer elemento. No se completa información desconocida de citas antiguas.

La recuperación entrega la lista completa al asistente y la respuesta guarda una copia de la fuente, incluidas sus páginas. La interfaz enumera esas páginas en cada cita y mantiene la lectura de respuestas antiguas que solo tienen `page`. No se necesita una migración SQL: fuentes y contexto ya están almacenados en JSONB. La lectura no reescribe documentos ni respuestas históricas.

Los originales se colocan en una carpeta de ingesta, cada archivo con su SHA-256 como nombre (sin extensión). Usar copias; conservar los originales y sus nombres en el archivo documental privado. El importador lee y comprueba la huella del original antes de escribir. La huella confirma identidad del archivo, no exactitud de la transcripción, correspondencia de página ni suficiencia de la aprobación: eso pertenece al cotejo documental. Figuras/tablas no se convierten en texto ni se aprueban por esta operación.

Desde backend, con DATABASE_URL configurada para una base local migrada:

```powershell
..\.venv\Scripts\python.exe -m app.corpus import RUTA_AL_CORPUS.json --sources RUTA_A_ORIGINALES_POR_HASH
```

La importación reemplaza el corpus activo en una transacción; repetir el mismo archivo produce el mismo conjunto. Un archivo inválido deja el conjunto anterior intacto. Un conjunto vacío retira todos los fragmentos. Las respuestas anteriores conservan su copia de las citas para auditoría; retirar un fragmento no reescribe la historia. Importaciones concurrentes se serializan. Conservar el JSON aprobado anterior permite restaurarlo mediante otra importación.

APPROVED_CORPUS_PATH ya no controla las consultas del chat: se reemplazó la lectura del archivo en cada solicitud por esta ingesta explícita. No hay importación automática al iniciar ni un endpoint público de aprobación.

## Prueba redistribuible sin manuales ni Gemini

backend/examples/rag contiene un texto didáctico propio, un corpus y su archivo original identificado por hash. Solo coincide con el modelo ficticio RAG-DEMO; nunca respalda datos del Gol. Es material de prueba, no un manual ni una recomendación de reparación. No se importa por defecto.

En una base dedicada a demo, con Compose construido:

```powershell
docker compose exec api python -m app.corpus import examples/rag/corpus.json --sources examples/rag/sources
```

Este comando reemplaza el corpus de esa base; no ejecutarlo sobre un conjunto aprobado que se quiera conservar. Crear un vehículo ficticio con model=RAG-DEMO y consultar desde Swagger:

`GET /vehicles/{id}/sources?q=refrigerante`

Devuelve method=postgresql_full_text y fuentes con texto, páginas y procedencia. No genera diagnóstico ni requiere Gemini. Un vehículo incompatible o una consulta sin coincidencias devuelve sources vacío. GET /assistant/status informa el número total importado, que no equivale a fuentes compatibles con cada auto.

## Recuperación y límites

Se normalizan acentos y se busca con el diccionario español de PostgreSQL, combinación OR y ranking textual. Se comprueban todos los requisitos contra datos conocidos del auto antes de elegir hasta cuatro resultados. No se deduce compatibilidad de valores nulos. La consulta se limita a 100 tokens; los archivos a 2 MB y 200 fragmentos. Por ese alcance reducido se usa cálculo textual directo, sin un índice adicional aún.

No hay traducción portugués-español, comprensión semántica ni garantía de relevancia por aparecer primero. La futura evaluación debe medir recuperación sobre consultas representativas, incluyendo sinónimos, negativas y ausencia de evidencia. El corpus didáctico verifica el circuito técnico, no precisión mecánica. Para usar los textos portugueses harán falta una estrategia multilingüe y evaluación antes de aprobar su recuperación.

Referencia de implementación: [búsqueda textual de PostgreSQL 17](https://www.postgresql.org/docs/17/textsearch-controls.html). La etapa semántica con pgvector permanece en el plan; esta base textual permite probar persistencia, trazabilidad, compatibilidad y citas sin proveedor externo.

## Verificación

Pasaron las 40 pruebas existentes tras integrar persistencia y recuperación, y luego las seis pruebas del módulo documental, incluida una prueba adicional de cita persistida tras retirar el corpus: 41 pruebas distintas. Se verifican migración, reimportación, rechazo de huellas/aprobaciones/IDs duplicados, conservación del conjunto anterior, incompatibilidad, filtrado antes del límite, consulta HTTP y entrega de evidencia al adaptador de respuestas simulado. No se hicieron llamadas reales a Gemini ni se habilitaron fragmentos privados.

Comprobación final: 41 pruebas pasaron juntas, Ruff y git diff --check correctos. Docker construyó y arrancó la API con la migración 0006. La consulta HTTP local de fuentes devolvió una lista vacía y el estado informó cero fragmentos aprobados, coherente con no haber importado manuales pendientes ni el ejemplo didáctico a la base del usuario.
