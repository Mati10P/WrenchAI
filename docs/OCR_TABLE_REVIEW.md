# Cotejo de cifras, unidades y celdas

Fecha: 2026-10-23. La separación espacial de palabras no confirma por sí sola una estructura de tabla.

## Resultado de esta primera pasada

- Se generaron borradores para las 95 regiones de tabla: 26 del manual de propietario y 69 del de reparación.
- Se conservaron las 6.025 palabras OCR asignadas a esas regiones, sin pérdidas ni duplicados.
- Se propusieron 2.806 grupos de palabras por posición. No se presentan como 2.806 celdas verificadas: pueden dividir una celda o mezclar filas, encabezados y notas.
- El primer lote cotejó 30 celdas de especificaciones de motor en la página PDF 10 del manual de reparación (impresa 12). El segundo amplió el cotejo a 69 celdas en seis estructuras: motor, bujías, tipo de embrague, diámetro de embrague, relaciones de caja y frenos.
- Se corrigieron dos encabezados donde el OCR confundía una letra de unidad con un dígito. Al ampliar el cotejo se detectó un error de nuestra primera transcripción: el valor de escape de la columna izquierda lleva un punto en `0,40 a 0.50 mm` en el original. Se restauró ese literal; no se uniforma la puntuación decimal. El OCR original permanece disponible.
- Los valores compartidos de bujías, tipo de embrague y frenos se representan una sola vez, con un recorte que abarca la zona compartida. Diámetros y relaciones conservan las columnas izquierda y derecha. No se agregan unidades a las relaciones ni se interpreta `DOT 4` como unidad numérica.
- La expresión impresa `monodisco secocon placa a diafragma` se conserva sin corregir editorialmente la unión de palabras. El contexto del título identifica el bloque; no se inventan filas vacías para sus encabezados de sección.

Se cotejaron los valores de los cinco bloques de especificaciones de esa página. Las tablas de las demás páginas siguen pendientes. Tampoco está confirmada la aplicabilidad al Gol G2 1.6 MI de 1998. Todo el conjunto conserva `rag_eligible=false`: cotejar celdas no habilita por sí solo la página ni sus procedimientos.

La primera versión usará un conjunto acotado de páginas bien revisadas. La revisión profunda de ambos manuales completos queda pendiente para una etapa posterior. Selección y criterios: [MVP_CORPUS.md](MVP_CORPUS.md).

## Procedimiento y evidencia

```powershell
.\.venv\Scripts\python.exe scripts/structure_ocr_tables.py
.\.venv\Scripts\python.exe scripts/audit_ocr_tables.py
.\.venv\Scripts\python.exe scripts/build_ocr_review.py
.\.venv\Scripts\python.exe -m unittest discover -s scripts/tests -v
```

Los artefactos están en `data/private/manuals/reviewed/<manual>/tables`, fuera de Git. Cada borrador referencia su región y sus palabras originales. Las definiciones cotejadas se guardan en `data/private/manuals/review/table-definitions.json`; si no existe este archivo, se generan únicamente borradores.

Una definición identifica página, región de origen, tabla, columnas con límites horizontales y filas con límites verticales normalizados. Cada fila conserva valores literales y unidades expresamente impresas. No se completan cifras desconocidas, casillas vacías ni abreviaturas por inferencia.

Cada celda cotejada incluye transcripción, contexto de fila/columna, posición, recorte, palabras del OCR de origen, diferencias respecto del OCR y huellas SHA-256 de la evidencia. No se convierten comas decimales, tolerancias, proporciones, signos o abreviaturas a valores numéricos de máquina. Una diferencia de escritura frente al OCR no siempre implica un error; requiere cotejo visual.

La primera definición solo registra unidades presentes literalmente en la celda. Las unidades expresadas exclusivamente en encabezados o notas deben vincularse explícitamente a su contexto cuando se revisen esas tablas; el borrador no las propaga automáticamente.

El visor de la página PDF 10 muestra las celdas cotejadas. Cada valor enlaza a su recorte y señala su posición en el escaneo al pasar el puntero. Las propuestas espaciales sin verificar quedan en un bloque desplegable distinto.

## Validación y trabajo pendiente

Pasaron 17 pruebas: etiquetas, unidades, orden de columnas y líneas, preservación de signos y comas, grupos vacíos, proporciones, abreviaturas y ausencia de unidades inferidas. La auditoría también comprueba hashes de fuentes, recortes, regiones y palabras.

Falta revisar el resto de las tablas: límites y celdas combinadas, encabezados que abarcan columnas, notas, signos pequeños, rangos, unidades compartidas y compatibilidad por variante. Una transcripción cotejada contra el escaneo no certifica la vigencia ni la corrección técnica del manual.
