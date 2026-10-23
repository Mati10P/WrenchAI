# Corpus documental de la primera versión

## Decisión de alcance

La primera versión de WrenchAI usará un conjunto acotado de páginas bien revisadas de los dos manuales candidatos. No se requiere completar la revisión profunda de ambos manuales antes de construir el MVP. Esa revisión completa queda pendiente para una etapa posterior.

El OCR y la separación por regiones cubren las 532 páginas, pero eso no equivale a una validación de su contenido. La selección inicial comprende 22 páginas: 19 de contenido y contexto técnico y 3 de identificación. Se inspeccionaron sus imágenes para seleccionar temas y contexto; no se completó el cotejo técnico de esas páginas. Ninguna está habilitada como evidencia técnica para RAG.

## Selección inicial - 2026-10-23

Todos los números PDF son posiciones desde 1 en los archivos registrados en [MANUAL_SOURCES.md](MANUAL_SOURCES.md), con sus SHA-256. `P` identifica propietario y `R` reparación. Los números impresos de la tabla se leyeron visualmente para localizar el material; todavía deben incorporarse al registro de revisión por página. Los archivos privados conservan el nombre `page-NNNN` correspondiente al número PDF.

| Grupo | Manual y páginas PDF | Numeración impresa | Contenido seleccionado y motivo |
| --- | --- | --- | --- |
| I1 | P 1, 12 | Portada sin número; 1-03 | Identidad del manual y ubicación del número del motor. Ayudan a distinguir fuente y vehículo sin publicar identificadores personales. No son evidencia de diagnóstico. |
| I2 | R 3 | Sin número visible | Portadilla con edición y cobertura declarada. Sirve para documentar límites de cobertura; no demuestra compatibilidad de cada procedimiento. |
| P1 | P 28–29 | 2-15–2-16 | Indicador de temperatura del tablero de 200 km/h y continuación de su advertencia. Mantener juntas explicación e ilustración. |
| P2 | P 30 | 2-17 | Testigos de presión de aceite y carga del tablero de 200 km/h. Permiten distinguir el estado de contacto del motor en marcha. |
| P3 | P 31 | 2-18 | Testigo de freno de estacionamiento/nivel de fluido de ese tablero, con figura y continuación de la advertencia. |
| P4 | P 32–34 | 2-19–2-21 | Identificación de los tableros de 220/240 km/h y advertencia de temperatura. Evitan reutilizar números de testigos de otra variante. |
| P5 | P 35–36 | 2-22–2-23 | Carga, presión de aceite y testigo de freno en esos tableros. La advertencia de aceite continúa en la segunda página. |
| P6 | P 87 | 5-05 | Diagrama del compartimiento AP-1600/AP-1800/AP-2000, con leyenda de depósitos y varilla. Permite vincular ilustración y texto; la figura no confirma por sí sola la instalación real del vehículo. |
| P7 | P 89–90 | 5-07–5-08 | Lectura de varilla, límites y reposición de aceite. Aporta una comprobación documentable y condiciones de medición. No se selecciona el cambio de aceite como reparación guiada. |
| P8 | P 91 | 5-09 | Solo sección de refrigeración: nivel, pérdidas recurrentes y advertencias. Se excluyen transmisión y sustitución de filtro, presentes en la misma página. |
| P9 | P 92 | 5-10 | Solo depósito de fluido de frenos y su ilustración. Se excluyen dirección hidráulica y depósito auxiliar de combustible. |
| R1 | R 69 | 71 | Vista general de refrigeración y leyenda, para distinguir componentes sin asumir una causa de falla. |
| R2 | R 72–73 | 74–75 | Dos despieces de radiador/electroventilador con sus leyendas. Debe identificarse a qué montaje corresponde cada uno antes de recuperar fragmentos. Se excluyen torques y desmontaje del alcance del MVP. |
| R3 | R 74–75 | 76–77 | Contexto del interruptor térmico y tabla de funcionamiento con/sin aire acondicionado. Se selecciona para revisar la tabla y evaluar abstención cuando falte variante; no se habilitan todavía sus umbrales. Se excluyen la prueba de presión y el desmontaje del radiador de las instrucciones al usuario. |

Son 16 páginas de propietario (14 técnicas y 2 de identificación) y 6 de reparación (5 técnicas y 1 de identificación), sin duplicados. Los pasajes excluidos en páginas mixtas deberán quedar fuera de los futuros fragmentos habilitados. Elegir una página para revisión no aprueba todo su contenido.

### Por qué este conjunto

Lubricación, refrigeración, frenos y carga comparten una estructura útil para el proyecto: síntoma observado, estado del motor, condición de medición, posible prioridad y fuente. Permiten mostrar persistencia de incidencias, preguntas pertinentes, citas verificables y reglas de seguridad sin desarrollar un taller virtual completo. Hay situaciones normales que ayudan a comprobar que la aplicación no eleva todas las consultas a alarma.

Se conserva la comparación entre tableros porque una respuesta debe depender de la variante identificada. El propietario aporta advertencias y observaciones; reparación aporta diagramas y una tabla acotada. Su coincidencia temática no demuestra que cubran la misma versión.

La página R 10, aunque tiene 69 celdas cotejadas, queda fuera del corpus inicial: contiene especificaciones de motor, encendido y transmisión cuya aplicabilidad al MI no está resuelta y que no son necesarias para estos casos. Su trabajo previo se conserva. También quedan fuera arranque auxiliar, mapas de fusibles, inyección, distribución, desmontajes y reparaciones internas. No se darán números de fusible, torques ni instrucciones de puenteo a partir de referencias fuera del conjunto.

Las especificaciones históricas de productos, proporciones, capacidades y tolerancias no se convierten en recomendaciones actuales por aparecer legibles. Cualquier uso requiere resolver primero transcripción, contexto y aplicabilidad. En particular, el pasaje de presión de R 74 no permite completar una unidad por intuición.

Los 20 escenarios y sus criterios de aceptación están en [MVP_CASES.md](MVP_CASES.md). Son un diseño de evaluación pendiente de implementación y ejecución.

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

El siguiente bloque será cotejar los grupos P1–P9 e I1–I2, comenzando por testigos, advertencias y sus continuaciones; después R1–R3 y sus tablas/leyendas. Registrar por sección transcripción, relaciones con figuras, aplicabilidad y exclusiones antes de preparar fragmentos para RAG. Las páginas de identificación se usan para procedencia y compatibilidad, no como citas de una hipótesis mecánica. Si una variante no puede establecerse, el caso correspondiente debe abstenerse; no se agregan páginas automáticamente para intentar justificar una respuesta.

Los casos que queden sin documentación suficiente deberán expresar esa ausencia en lugar de inventar especificaciones. El conjunto permite avanzar con el modelo de datos y la API mientras continúa la revisión. El diagnóstico respaldado por documentos depende de la aprobación explícita de sus fragmentos.

La revisión profunda del resto de los dos manuales se mantendrá en el seguimiento posterior. Los originales, transcripciones y recortes permanecen en `data/private`, excluidos de Git. La demo y las pruebas públicas usarán material redistribuible.
