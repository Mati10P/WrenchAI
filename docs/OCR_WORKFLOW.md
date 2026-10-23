# OCR y revisión de los manuales

El OCR original se conserva en `data/private/manuals/ocr`. La versión corregida está en `data/private/manuals/reviewed`. Ambos directorios son privados y están excluidos de Git.

## Ejecutar y reanudar

Requiere Python 3.11, las dependencias de `scripts/requirements-ocr.txt`, Tesseract 5 y modelos `por`, `spa`, `osd` en `data/private/manuals/tessdata`. Los modelos usados provienen de tessdata_fast del proyecto Tesseract. El nuevo flujo no usa OSD para decidir la orientación.

```powershell
.\.venv\Scripts\python.exe -m pip install -r scripts/requirements-ocr.txt
.\.venv\Scripts\python.exe scripts/review_ocr.py --workers 4
.\.venv\Scripts\python.exe scripts/apply_ocr_annotations.py
.\.venv\Scripts\python.exe scripts/build_ocr_review.py
.\.venv\Scripts\python.exe scripts/audit_ocr.py
```

`ocr_manuals.py` redirige al flujo corregido. `--manual repair` o `--manual owner` limita el procesamiento. Se reanudan páginas completas; si cambia una rotación explícita se reprocesa esa página. Si cambia el original respecto del manifiesto, el proceso se detiene para evitar mezclar versiones. No ejecutar dos reconstrucciones sobre el mismo destino.

## Orientación y limpieza

Se comparan dos orientaciones mediante OCR de prueba a 120 dpi. En páginas del manual de reparación que antes fueron detectadas como apaisadas se comparan cuatro giros. La puntuación favorece palabras alfabéticas reconocidas con confianza; no mide corrección mecánica. Casos ambiguos o con poco texto quedan señalados.

Las correcciones visuales explícitas están en `docs/ocr-orientation-overrides.json`. Tienen prioridad sobre la puntuación: en diagramas con texto en varios sentidos, una mayor confianza puede elegir una orientación incómoda para leer. El OCR definitivo se realiza a 240 dpi.

La limpieza automática normaliza Unicode, espacios finales y saltos de página. No reconstruye números, unidades, palabras cortadas ni columnas. Las correcciones puntuales de transcripción se guardan con antes, después y motivo en anotaciones privadas. El texto crudo permanece disponible.

## Texto, ilustraciones y tablas

Cada página conserva imagen completa a 240 dpi, texto crudo, texto limpio, TSV real de palabras y JSON con líneas, coordenadas y procedencia. Las coordenadas son píxeles de la página ya orientada; no corresponden directamente al PDF original sin aplicar la rotación y la escala.

El visor privado `reviewed/<manual>/index.html` permite navegar, abrir el original y señalar sobre el escaneo la posición de una línea de OCR. Las líneas muestran OCR crudo; debajo aparece el texto limpio con correcciones registradas.

Todas las páginas vinculan texto e imagen completa. Los rótulos detectados son candidatos, no asociaciones semánticas confirmadas. Las tablas conservan su disposición en la imagen; el texto lineal no se trata como una tabla validada.

Las regiones localizadas visualmente se guardan como recortes con su página, caja, etiqueta y líneas que se solapan con la región. Actualmente hay cinco tablas en PDF 10 y una figura en PDF 19 del manual de reparación. Las anotaciones están en `data/private/manuals/review/annotations.json`; ese archivo es una entrada privada opcional y no se distribuye con el código. El resto conserva contexto de página completa, sin afirmar una segmentación detallada que no se haya revisado.

## Verificación

`audit_ocr.py` comprueba las 532 páginas: hash del original, correspondencia de página, archivos, dimensiones, cajas de palabras/líneas y referencias de regiones. El resultado privado está en `data/private/manuals/review/audit.json`.

`ocr_contact_sheets.py --manual gol-repair-candidate` genera hojas de contacto para comprobar orientación. Estas hojas permiten revisar disposición y giros; no sirven para aprobar cifras pequeñas.

La orientación se revisó visualmente en hojas de contacto, con inspección ampliada de casos especiales. La revisión técnica detallada sigue pendiente: páginas impresas, valores, unidades, columnas y referencias entre páginas. Ninguna página pasa automáticamente a evidencia técnica validada por tener una confianza alta.

Commit sugerido para este bloque: `fix: rebuild OCR orientation and link text to page visuals`.

## Limpieza de ruido pendiente

Se comprobó que cinco fragmentos espurios de PDF 19 del manual de reparación pertenecían a la ilustración y aparecían intercalados en el texto del procedimiento. Se eliminaron únicamente de la transcripción limpia mediante correcciones privadas explícitas; el OCR crudo conserva el resultado original.

Ejecutar `python scripts/find_ocr_noise.py` para generar `data/private/manuals/review/noise-candidates.json`. Detecta líneas cortas, caracteres de reemplazo y texto dentro de regiones de ilustración ya localizadas. Es una cola de revisión, no un filtro de borrado: letras sueltas, unidades, etiquetas de figuras y celdas pueden ser contenido real.

El siguiente trabajo del corpus es localizar regiones de texto, ilustraciones y tablas en cada página; cotejar las candidatas contra el escaneo; excluir del texto narrativo el ruido confirmado de las figuras; y transcribir tablas conservando encabezados, columnas y unidades. Mantener trazabilidad de cada exclusión y revisión. Hasta entonces la limpieza de contenido no está completa.
