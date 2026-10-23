# Corpus documental de la primera versión

## Decisión de alcance

La primera versión de WrenchAI usará un conjunto acotado de páginas bien revisadas de los dos manuales candidatos. No se requiere completar la revisión profunda de ambos manuales antes de construir el MVP. Esa revisión completa queda pendiente para una etapa posterior.

El OCR y la separación por regiones cubren las 532 páginas, pero eso no equivale a una validación de su contenido. La selección inicial todavía está pendiente; ninguna página está habilitada como evidencia técnica para RAG.

## Selección y aceptación

Se elegirán páginas según los problemas y casos de evaluación que realmente cubra el MVP. La cantidad dependerá de la cobertura que pueda revisarse y demostrarse, sin fijar un volumen artificial. Se incluirán las páginas de contexto necesarias para interpretar cada procedimiento, tabla, nota o ilustración.

Antes de habilitar cada página o sección se debe registrar:

- Manual, edición, página PDF, numeración impresa, sección y vínculo al escaneo conservado.
- Texto cotejado visualmente, sin ruido de diagramas mezclado con la narrativa.
- Cifras, signos, unidades, encabezados, celdas compartidas y notas cotejados; sin conversiones ni unidades inferidas.
- Ilustraciones y tablas vinculadas a su explicación, con etiquetas y referencias comprobadas.
- Motor, versión y condiciones a las que aplica la fuente, y las limitaciones conocidas. Una lectura legible no demuestra compatibilidad.
- Incertidumbres y exclusiones explícitas. Si impiden interpretar el pasaje, permanece fuera del corpus habilitado.

El cotejo de una tabla no aprueba automáticamente toda la página. Una página con contexto pendiente tampoco se habilita por tener algunas celdas transcritas. La futura ingesta deberá incluir únicamente el material aprobado de forma explícita; no recorrer automáticamente todos los borradores OCR. Este control de ingesta todavía no está implementado.

## Estado y próximos pasos

La página PDF 10 del manual de reparación (impresa 12) tiene 69 celdas cotejadas y evidencia privada por celda. Sigue pendiente verificar su aplicabilidad y el contexto técnico. Es un trabajo de preparación, no una página aprobada para el MVP.

El siguiente bloque será seleccionar páginas y casos concretos, completar su revisión y registrar la aprobación y sus límites antes de preparar fragmentos para RAG. Los casos que queden sin documentación suficiente deberán expresar esa ausencia en lugar de inventar especificaciones.

La revisión profunda del resto de los dos manuales se mantendrá en el seguimiento posterior. Los originales, transcripciones y recortes permanecen en `data/private`, excluidos de Git. La demo y las pruebas públicas usarán material redistribuible.
