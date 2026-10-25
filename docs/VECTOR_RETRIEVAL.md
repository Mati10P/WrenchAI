# Búsqueda híbrida de manuales

La recuperación combina BM25 sobre el OCR con similitud semántica en PostgreSQL/pgvector. Las páginas seleccionadas se entregan a Gemini como imágenes originales, manteniendo las citas y el perfil de referencia de fábrica. El OCR y sus vectores siguen siendo navegación sin aprobación técnica.

## Implementación

- Modelo `gemini-embedding-001`, 768 dimensiones, vectores normalizados. Las páginas se dividen en tramos de hasta 2400 caracteres con 200 de solapamiento, conservando texto y números. Los documentos usan `RETRIEVAL_DOCUMENT`; las consultas, `RETRIEVAL_QUERY`, según la [API de embeddings de Gemini](https://ai.google.dev/api/embeddings).
- Migración 0008: habilita la extensión `vector` y crea `manual_embeddings`, separada del corpus aprobado. Guarda modelo, página, hash del texto, hash del bundle y vector. No copia el OCR a las fuentes aprobadas.
- Distancia coseno exacta con [pgvector para SQLAlchemy](https://github.com/pgvector/pgvector-python). El tamaño actual permite recorrer todos los vectores; no se añade HNSW antes de necesitarlo.
- Hasta 20 candidatos de cada método; fusión por rango recíproco (RRF, constante 60). La selección conserva un primer resultado léxico, otro candidato de la fusión y dos semánticos para admitir coincidencias conceptuales que el OCR por palabras deja afuera. Son cuatro páginas principales y sus continuaciones, máximo ocho imágenes. Sin candidatos semánticos, se conserva el top léxico. Los fragmentos revisados conservan su recuperación existente.
- La similitud mínima de 0,62 se calibró con esta biblioteca y sus controles. Es un filtro de recuperación, no una probabilidad de relevancia ni una validación mecánica. Gemini debe abstenerse si las imágenes no responden la pregunta. Se normaliza el regionalismo «cubiertas» a «neumáticos» en la consulta semántica y se agrega al vocabulario léxico; no se modifica el texto documental.
- El índice solo se utiliza cuando coincide el hash del bundle, el modelo y la cantidad esperada de fragmentos. Cambiar biblioteca o particionado requiere reindexar. Las páginas sin texto OCR permanecen disponibles como imágenes y continuaciones, pero no tienen vector propio.
- Si falta el índice o el proveedor de embeddings falla, se conserva la búsqueda BM25. `/sources` y el snapshot de la respuesta registran el método y la causa del fallback. Una advertencia de seguridad se resuelve antes de consultar vectores.
- La consulta enviada al servicio de embeddings contiene hasta los primeros 3000 caracteres del mensaje actual; no incluye datos del vehículo ni historial. El mensaje original y el contexto de modificaciones se conservan para generar la respuesta. La caché de hasta 128 consultas vive en memoria del proceso.

Este bloque usa el adaptador Gemini y SQLAlchemy directamente. No incorpora LangChain: la combinación de rankings y el circuito de citas permanecen explícitos y comprobables.

## Indexación y activación

Instalar `backend/requirements.txt` en el entorno local y migrar PostgreSQL. El contenedor de base de datos existente ya usa la imagen pgvector. Configurar las variables en la sesión sin imprimir claves: `DATABASE_URL`, `GEMINI_API_KEY` y `MANUAL_LIBRARY_PATH` con la ruta absoluta del bundle cuando se ejecuta desde el host.

Desde `backend`:

```powershell
../.venv/Scripts/python.exe -m alembic upgrade head
../.venv/Scripts/python.exe -m app.vector_search --cache ../data/private/manuals/vector-cache-v1
```

La preparación guarda cada lote en la caché privada. Usa pausas de 12 segundos y hasta cinco intentos por lote frente a 429 o errores temporales. Un corte permite repetir el comando sin regenerar los lotes terminados. El snapshot de PostgreSQL se reemplaza en una transacción únicamente después de completar todos los vectores y comprobar que la biblioteca no cambió. Una clave sin cuota suficiente requiere esperar su recuperación; la indexación no cambia de proveedor ni compra créditos.

Agregar `HYBRID_RETRIEVAL=true` al `.env` local y reconstruir la API:

```powershell
docker compose up -d --build api
```

`GET /assistant/status` expone `vector_search`: habilitación, disponibilidad, cantidad esperada/real, modelo y dimensiones. `HYBRID_RETRIEVAL=false` permite volver a la búsqueda léxica sin eliminar los vectores.

## Evaluación

Con las mismas variables de la sesión local, ejecutar desde la raíz:

```powershell
.venv/Scripts/python.exe scripts/evaluate_manual_search.py --output data/private/manuals/vector-evaluation-v1.json
```

El script compara BM25 y búsqueda híbrida con ocho preguntas documentales y dos controles fuera de cobertura. Sus objetivos son páginas PDF explícitas, incluyendo formulaciones indirectas y español sobre documentos portugueses. Cuenta si el conjunto de páginas recuperadas incluye al menos una página objetivo; incluye continuaciones. Esta muestra sirve para detectar regresiones y mejoras concretas, sin medir exhaustivamente precisión, todos los motores ni calidad de las respuestas generadas.

Los originales, la caché de vectores y los resultados detallados permanecen en `data/private`, fuera de Git. Los resultados sobre estas mismas diez preguntas son calibración; hace falta ampliar la evaluación con consultas nuevas para estimar el comportamiento general.

## Ejecución local — 2026-10-25

- Migración 0008 aplicada; índice completo importado y búsqueda híbrida activada en Docker. Se generaron 546 vectores para 530 páginas con texto. Las páginas propietario 10 y reparación 16 tienen OCR vacío; siguen disponibles como imágenes y no tienen vector propio.
- El primer intento de preparación llegó a 80 fragmentos y recibió HTTP 429. Se reanudó desde la caché, con pausas y reintentos; se completó sin cambiar el proveedor ni la cuota.
- Calibración inicial, umbral 0,50 y RRF sin cupos: BM25 8/10, híbrida 6/10, por falsos candidatos en controles y candidatos conceptuales desplazados. Se conservaron los resultados de este intento.
- Calibración final, umbral 0,62, selección con cupos y normalización regional: BM25 9/10, híbrida 10/10. El cambio de vocabulario explica la mejora léxica en «cubiertas»; el aporte vectorial recupera la página 95 para «las gomas que barren el vidrio», que BM25 sigue omitiendo. Los dos controles negativos quedan sin candidatos.
- Prueba real por el proxy de frontend: respuesta de escobillas en 6,56 s con cita `gol-owner-candidate-0095`; Bluetooth en 0,08 s sin fuentes y con el guard de cobertura, tras el sondeo de búsqueda que ya había generado su vector de consulta. Se verificaron el método híbrido persistido y las modificaciones originales del vehículo en ambos snapshots. No se verificó visualmente el chat en navegador.
- Limitación de generación observada: la respuesta de escobillas mezcló el nombre del autor del libro de reparación con el manual del propietario y enumeró escape/suspensión sin relevancia clara. La página citada y el resultado de recuperación son correctos; la redacción automática requiere una mejora aparte y no se considera validada por estas pruebas.
- Backend completo: **87 pruebas pasaron**; incluye migraciones verificadas contra el modelo SQLAlchemy, similitud coseno en PostgreSQL, caché, reemplazo atómico, índice incompleto o desactualizado, fallback, límites del proveedor, vocabulario regional y prioridad de seguridad. Ruff y `git diff --check` correctos.

Evidencia privada: `vector-evaluation-v1.json`, `vector-evaluation-v2.json`, `vector-evaluation-v3.json` y `vector-live-v1.json`, dentro de `data/private/manuals`. El estado de revisión del OCR y el corpus de cinco pasajes aprobados permanecen separados del índice vectorial.
