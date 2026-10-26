# Navegación visual persistente y especificaciones

La consulta «cuanto torque llevan las ruedas?» recuperaba diferencial y distribución:
el ranking premiaba «torque» y no relacionaba la fijación de la rueda con el dato
ubicado dentro de una reparación de frenos. La imagen original de la página PDF
198 contiene explícitamente 100 Nm para la fijación de la rueda, y distingue ese
valor de los 40 Nm de los tornillos guía. Esto es una lectura del documento; no
certifica las fijaciones realmente instaladas ni convierte el manual independiente
en documentación oficial de Volkswagen.

## Cambios

- La recuperación de especificaciones busca componente, fijación y unidad dentro
  del texto, aunque el título pertenezca a otro procedimiento. Los candidatos
  conservan las imágenes originales. No se guarda un valor fijo en el código.
- Se distinguen fijaciones de rueda, tuerca de maza, rodamientos y rueda tensora.
  El OCR «roda mientos» no equivale a una rueda en portugués.
- Una coincidencia de especificación limita las páginas y evita expandir todo
  el árbol del procedimiento. La consulta repetida con contexto conversacional
  también mantiene el componente.
- Una fuente cuyo texto y figuras se declararon irrelevantes no puede citarse
  en el resumen. La revisión puede regenerar una salida inválida.
- Las consultas puntuales de apriete usan una respuesta concentrada en el resumen
  documentado, sin repetir los procedimientos circundantes.
- «Purgar», «purgado», «sangrar» y «sangría» comparten vocabulario de navegación.

## Pasada visual

`scripts/enrich_manual_navigation.py` revisa las imágenes originales de todas las
páginas y todos los recortes de figuras. Guarda tema, pasajes con referencias a
regiones, descripciones de cada ilustración, legibilidad y relación con texto.
Exige una decisión para cada figura y rechaza IDs desconocidos o duplicados.
Cada caché se vincula con los hashes de página, layout, figuras, prompt y modelo.

La salida tiene estado `model_navigation_only`: se usa para localizar evidencia,
no como transcripción técnicamente aprobada. La generación de respuestas vuelve
a leer los originales. No reemplaza las imágenes ni los cinco pasajes aprobados.

Desde la raíz, con la clave en el entorno, sin imprimirla:

```powershell
.venv/Scripts/python.exe scripts/enrich_manual_navigation.py --library data/private/manuals/library-v1 --figures data/private/manuals/figures-v7 --layouts data/private/manuals/reviewed --output data/private/manuals/navigation-v1 --workers 4
```

Los reintentos son acotados. La caché permite reanudar sin repetir páginas completas.
Solo una pasada completa publica `navigation.json` mediante reemplazo atómico.
`last-run.json` registra páginas completadas y errores; una ejecución parcial no
debe habilitarse. Todo el contenido permanece en `data/private`, fuera de Git.

## Activación

El backend admite `MANUAL_NAVIGATION_PATH=/manual-navigation` y Compose monta la
carpeta indicada por `MANUAL_NAVIGATION_DIRECTORY`. Sin la variable, funciona el
índice anterior junto con la corrección de especificaciones.

La navegación se agrega al índice BM25, a los fragmentos de sección mediante
coordenadas originales y al texto de los embeddings. El hash vectorial incorpora
la nueva navegación, de modo que un índice anterior queda obsoleto y se usa el
fallback léxico hasta completar la reindexación. Reconstruir los vectores con
`python -m app.vector_search --cache RUTA_PRIVADA` usando el mismo overlay; la
transacción solo reemplaza el índice cuando termina todo el lote.

`GET /assistant/status` expone disponibilidad y cobertura del índice visual.
Tener todas las páginas procesadas no garantiza que cada descripción automática
sea correcta: los tests de integridad no sustituyen la evaluación de recuperación
ni la revisión visual de respuestas reales.

## Evidencia de esta corrección

Los resultados de búsqueda y respuestas reales se guardan en
`data/private/manuals/navigation-before-v1.json` y `wheel-torque-live-v*.json`.
Se conservan también los intentos fallidos, sin sobrescribirlos. El plan registra
el estado final de procesamiento, indexación y pruebas.

La extracción exhaustiva usa `prepare_manual_figures.py --include-all --reuse RUTA_ANTERIOR`: conserva recortes existentes e incluye símbolos pequeños y regiones de baja confianza para revisión. El estado automático permanece explícito. Las figuras sin texto asociado también aportan navegación por su pertenencia geométrica a la sección.

## Ejecución completa — 26 de octubre de 2026

- Lectura completa: 532/532 páginas, dos manuales, 4.369 pasajes de navegación y 685/685 regiones de imagen descritas. La extracción anterior tenía 598 recortes: se conservaron sus hashes y se agregaron 87 regiones antes omitidas. Hay 566 figuras marcadas legibles, 118 parciales y una ilegible; esas marcas son automáticas.
- Bundles activos: `library-v1`, `figures-v7`, `sections-v14` y `navigation-v1`. Se mantienen 572 secciones; 679 figuras tienen una sección asignada. Las otras seis permanecen descritas y vinculadas a su página original.
- Vectores: 720 fragmentos de las 532 páginas, `gemini-embedding-001`, 768 dimensiones. Índice completo activado en PostgreSQL/pgvector; el estado de la API confirma coincidencia entre cantidad real y esperada.
- La cuota diaria interrumpió la primera pasada. Se conservaron las cachés verificadas: 487 páginas usan Flash-Lite 3.5, 31 Flash-Lite 3.1 y 14 Flash 3.5. Cada entrada conserva su modelo y fingerprint. La pasada completa final terminó sin errores.
- Las respuestas reales se probaron con el modelo predeterminado Flash-Lite 3.5 en un vehículo sintético independiente: torque de ruedas, purgado, escobillas, filtro de combustible, ubicación de la tabla de presión y Bluetooth fuera de cobertura. Las seis respuestas usaron fuentes dentro de los conjuntos comprobados; Bluetooth no citó fuentes. El torque fue 100 Nm y no agregó los pares de 40/30 Nm ni ilustraciones de otra reparación.
- La revisión de fuentes corrigió dos falsos negativos del criterio inicial: las páginas 137–139 también documentan el filtro de combustible y la 109 explica comprobar la presión en frío. Se conservaron los informes iniciales y la explicación de la corrección. La tabla numérica de presión se evalúa además con una consulta específica cuyo objetivo sigue siendo la 129.
- El ranking de secciones conserva ahora señales semánticas fuertes y equivalencias de escobillas/vidrio en español y portugués. Las respuestas de ubicación se concentran en la ubicación y sus figuras; no agregan consejos generales de mantenimiento por compartir componente.

Evidencia privada: `navigation-complete-audit-v1.json`, `navigation-vector-build-v1.json`, `navigation-retrieval-evaluation-v*.json`, `navigation-source-evaluation-v2.json` y `navigation-evaluation-source-review.json`, dentro de `data/private/manuals`. Estas evaluaciones sirven para calibración y regresión: no son una validación mecánica exhaustiva ni una medida de todas las preguntas posibles.

Resultado final: búsqueda léxica 12/14; híbrida 14/14 en la muestra de calibración/regresión, con controles negativos sin resultados. Los dos casos de torque solo recuperaron páginas de fijaciones de rueda, incluido el seguimiento. Las seis respuestas reales devolvieron exactamente las fuentes citadas en sus tarjetas visibles; ninguna añadió tarjetas ajenas. Pasaron 284 tests del backend y 38 de herramientas; Ruff sobre la aplicación y scripts modificados y `git diff --check` correctos. Informe consolidado privado: `navigation-final-verification.json`.
