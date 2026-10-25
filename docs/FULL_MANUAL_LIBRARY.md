# Biblioteca de manuales completos

La biblioteca privada incorpora las 144 páginas del manual del propietario y las 388 del manual de reparación de Gabriel Ferrer. Este último no se presenta como un manual oficial Volkswagen. La identidad exacta de edición y la aplicabilidad de cada variante siguen requiriendo comprobación.

## Flujo y límites

1. Se conserva el corpus de cinco fragmentos revisados en PostgreSQL.
2. Un índice local de las 532 páginas usa OCR exclusivamente para navegación. El ranking BM25 incluye vocabulario español/portugués. No hay embeddings ni LangChain en este bloque.
3. Se recuperan hasta cuatro páginas y sus continuaciones inmediatas, como máximo ocho imágenes. Gemini recibe imágenes renderizadas directamente del PDF, a 240 dpi, con la orientación registrada. No recibe el OCR sin revisar como evidencia.
4. Gemini responde desde las imágenes legibles y los fragmentos revisados, cita las páginas utilizadas y contextualiza las modificaciones conservadas del vehículo. La referencia de fábrica sigue siendo una suposición documental. Una tabla de otro motor no confirma una especificación del auto.
5. El chat identifica las fuentes visuales como lectura automática y ofrece **Ver página original**. El snapshot conserva IDs y hashes, sin guardar base64 ni OCR. Las imágenes se verifican por SHA-256 antes de enviarlas o servirlas.

Cobertura documental completa significa que todas las páginas están disponibles para recuperación. **No significa que todas estén transcritas, revisadas o técnicamente validadas**. No se modifican sus estados de revisión ni se introducen en `document_passages` como aprobadas. La lectura visual automática puede fallar; las cifras, unidades o variantes ilegibles deben quedar sin resolver. La búsqueda léxica puede omitir sinónimos y páginas compuestas solo por diagramas; no encontrar una página no demuestra ausencia del tema. El contexto anterior no se utiliza para reformular preguntas elípticas. Tampoco se envían los dos libros completos en cada consulta.

La API utiliza imágenes inline de Gemini, según la [documentación de imágenes de Google](https://ai.google.dev/gemini-api/docs/generate-content/image-understanding). Se envían únicamente las páginas recuperadas junto con el contexto de la conversación al proveedor ya configurado. El límite de imágenes es 12 MB antes de base64; si se excede, se pide una consulta más específica. El timeout del proveedor sigue siendo 60 segundos.

## Instalación local reproducible

Desde la raíz, con las dependencias documentales `pymupdf` y `Pillow` del entorno local:

```powershell
.venv/Scripts/python.exe scripts/prepare_manual_library.py --output data/private/manuals/library-v1
```

El destino debe ser nuevo. El script verifica hashes y cantidades contra ambos PDF, renderiza cada página y escribe `library.json` solo al completar las 532. Un fallo deja una carpeta parcial sin manifest; no se debe activar. La biblioteca es privada y está ignorada por Git. Sus originales y los artefactos de OCR deben estar presentes para reproducirla.

En `.env`, activar `MANUAL_LIBRARY_PATH=/manual-library` para Docker. Compose monta `data/private/manuals/library-v1` en modo lectura. En ejecución del backend desde el host, usar la ruta absoluta local. La variable vacía desactiva esta ampliación y conserva el corpus revisado anterior.

```powershell
docker compose up -d --build api frontend
```

`GET /assistant/status` distingue `approved_passages` de `manual_library.pages`. `GET /vehicles/{id}/sources?q=...` separa `sources` revisadas de `page_candidates` para lectura visual. `GET /manual-pages/{id}` devuelve la imagen comprobada, sin aceptar rutas de archivos. Estos endpoints mantienen el alcance local del MVP; no publicar esta instalación ni los manuales.

Para reemplazar una edición, crear otro bundle e instalarlo explícitamente; no editar imágenes activas en sitio. La integridad del snapshot anterior no debe confundirse con validación mecánica del contenido.

## Evidencia de ejecución

- Exportación completa: 532 imágenes; manifest SHA-256 `7222d50c955ba2ab51de61aaa42dc9e800b095445aa3c61a49114768b7d423e6`.
- Backend: 71 pruebas pasaron al introducir la biblioteca, incluyendo aislamiento del OCR, recuperación bilingüe, imágenes enviadas, rechazo de integridad alterada, citas, modificaciones conservadas y servicio de páginas.
- Frontend: TypeScript y build Vite correctos.
- Tras endurecer el manejo de fallos de biblioteca, pasaron otras 21 pruebas del asistente y biblioteca, incluida la prioridad de seguridad sin archivos disponibles.
- Evaluación real a través del proxy del frontend: neumáticos, 14,19 s, citas PDF propietario 129 y 109; embrague, 7,06 s, cita reparación 83; fusibles, primer intento agotó 60 s y reintento respondió en 8,66 s con cita propietario 118. Se comprobaron visualmente páginas 118, 129 y 83, además de 100 y reparación 80. Las respuestas conservaron el contexto de modificaciones. Esto no valida las otras páginas ni todos los efectos mecánicos inferidos.
- Se reforzó después el prompt para distinguir el manual de Ferrer de un manual oficial y citar juntas texto y figura cuando la explicación dependa de ambos. La primera respuesta de embrague solo citó la figura 83, aunque también recuperó el texto 82; se conserva como límite observado, no se altera el registro.
- Evidencia privada: `data/private/manuals/library-live-v1.json`. Conversación de prueba explícitamente titulada «Prueba de biblioteca completa», sin registrar síntomas mecánicos reales. No se ejecutó una evaluación exhaustiva ni un recorrido visual del chat en navegador.
