# Resultado de la separación documental

Ejecución local: 2026-10-23. Esta es una auditoría de organización y conservación de datos, no una medición de exactitud mecánica.

| Manual | Páginas | Palabras OCR conservadas | Regiones de ilustración | Regiones de tabla | Palabras sin asignación |
| --- | ---: | ---: | ---: | ---: | ---: |
| Propietario | 144 | 29.271 | 228 | 26 | 523 |
| Reparación | 388 | 44.273 | 457 | 69 | 94 |
| Total | 532 | 73.544 | 685 | 95 | 617 |

Los números de regiones son propuestas del modelo y ajustes de límites, no un inventario definitivo de figuras o tablas impresas. Una región amplia puede contener varias tablas.

Se revisaron visualmente muestras con procedimientos, ilustraciones y tablas, además de seis páginas con mayor proporción de palabras sin asignar. Esto permitió localizar tablas sin bordes que el modelo había tratado como texto, ampliar una leyenda, reunir etiquetas y valores y distinguir ruido de los anillos de encuadernación. Las correcciones de límites se registran en `ocr-layout-overrides.json`; no modifican cifras del OCR.

La página PDF 19 del manual de reparación se comprobó como regresión: el procedimiento permanece en el borrador narrativo, el rótulo conserva su figura y las palabras reconocidas dentro del dibujo permanecen en su región visual. Los fragmentos espurios no vuelven a intercalarse en el procedimiento.

Validaciones ejecutadas:

- Diez pruebas sobre etiquetas y unidades, tablas, columnas, notas al pie y correcciones de regiones.
- Auditoría completa de las 532 páginas: todas las palabras del TSV aparecen una vez, conservando texto y coordenadas.
- Verificación de límites de recortes, relaciones entre palabras y regiones, rótulos y archivos derivados.
- Comprobación de referencias locales del visor y sintaxis de su JavaScript.
- Lint de los módulos de separación y compilación de los scripts Python.

Las palabras sin asignación siguen disponibles para cotejo. Las asociaciones de rótulos por proximidad, la estructura interna de tablas, los valores y las unidades siguen pendientes de revisión. Todos los resultados mantienen `rag_eligible=false`.
