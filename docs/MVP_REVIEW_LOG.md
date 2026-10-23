# Registro de cotejo del conjunto inicial

## Lote 1 - 2026-10-23

Alcance: secciones seleccionadas de las páginas PDF 28–31 del manual de propietario, impresas 2-15–2-18, para el tablero con velocímetro de 200 km/h. Se cotejaron las imágenes completas y los recortes de cada tramo de texto. No se revisó todo el contenido de estas páginas ni se aprobó su aplicabilidad al vehículo objetivo.

| Pasaje privado | Páginas PDF | Cotejo realizado | Pendientes que impiden habilitarlo para RAG |
| --- | --- | --- | --- |
| `owner-200-temperature` | 28–29 | Sección de temperatura completa en cinco tramos, con orden entre columnas y páginas. Se recuperó texto de una advertencia que el OCR había perdido. Figura del tablero vinculada al indicador 1. | Confirmar tablero/variante; cotejar contexto de refrigeración en PDF 91. La referencia al mapa de fusibles queda fuera del alcance aprobado. |
| `owner-200-charging` | 30 | Sección de carga completa, diferenciando el nombre del sistema del pictograma de batería. Figura del tablero de PDF 28 vinculada al testigo 9. | Confirmar tablero/variante. La referencia al ajuste/sustitución de correa corresponde a material fuera del conjunto inicial; no habilita una reparación guiada. |
| `owner-200-oil` | 30 | Sección de presión de aceite completa, preservando la distinción entre presión y nivel. Figura de PDF 28 vinculada al testigo 10. | Confirmar tablero/variante y cotejar PDF 89–90 para interpretar medición y reposición de nivel. |
| `owner-200-brakes` | 31 | Sección de freno completa en tres tramos, incluyendo la continuación en el recuadro superior derecho que el OCR había mutilado. Figura vinculada al testigo 11. | Confirmar tablero/variante y cotejar depósito de fluido en PDF 92. Separar el pasaje histórico de las reglas conservadoras del producto. |

Resultado: cuatro pasajes transcritos y cotejados en cuatro páginas seleccionadas. No significa cuatro páginas completamente limpias o aprobadas. Todos conservan `applicability_status=pending` y `rag_eligible=false`. Las otras 18 páginas seleccionadas no se cotejaron en este lote. Las 69 celdas de R 10 siguen siendo un trabajo anterior fuera del corpus inicial.

## Criterios aplicados

- Mantener el portugués original y sus cifras/referencias. No se produjo una traducción ni una recomendación mecánica nueva.
- Unir saltos de renglón y palabras partidas solo tras comprobar el escaneo. Las uniones entre columnas o páginas se declaran explícitamente en el registro privado, sin pedir al algoritmo que adivine texto faltante.
- Conservar los pictogramas como evidencia visual. Las descripciones de símbolos y la correspondencia con números del diagrama son anotaciones separadas; no se insertan caracteres OCR inventados como si estuvieran impresos.
- Preservar el OCR original, sus coordenadas y la limpieza anterior. La nueva transcripción vive en otra capa y aparece primero en el visor, identificada como cotejo parcial.
- Conservar en privado las referencias históricas fuera del alcance; no confundir fidelidad de transcripción con aprobación para dar esas instrucciones al usuario.

## Evidencia y reproducción

El registro privado es `data/private/manuals/review/passage-definitions.json`. Cada pasaje define título, alcance, tramos ordenados, páginas PDF/impresas, límites normalizados, figuras y pendientes. `join_next` permite declarar continuación de frase, palabra partida o nuevo párrafo. En los títulos textuales no se transcriben los pictogramas: sus imágenes quedan vinculadas por separado.

```powershell
.\.venv\Scripts\python.exe scripts/build_reviewed_passages.py
.\.venv\Scripts\python.exe scripts/build_ocr_review.py
.\.venv\Scripts\python.exe -m unittest discover -s scripts/tests -v
```

El constructor genera JSON y recortes en `data/private/manuals/reviewed/gol-owner-candidate/passages/`. Registra huellas SHA-256 del PDF original, imagen de página, metadatos, OCR original, TSV y cada recorte. Comprueba límites, dimensiones, orden de lectura y estado sin aprobación para RAG. El visor vuelve a comprobar esa evidencia antes de mostrarla; una fuente modificada requiere regenerar y volver a cotejar el pasaje, no confiar en la transcripción antigua.

Sin el registro privado no se reconstruyen estos pasajes: el repositorio público contiene herramientas, pruebas y este informe, no transcripciones ni escaneos. Los resultados locales se consultan en `page-0028.html` a `page-0031.html` del propietario, no en la página 19 del manual de reparación.

Se inspeccionaron visualmente los diez recortes de texto y las figuras en las páginas originales. Pasaron 22 pruebas de herramientas (incluidas cinco nuevas de pasajes), Ruff y la comprobación de enlaces locales del visor. Estas comprobaciones no constituyen evaluación de Gemini ni certificación de compatibilidad. No se comprobó el renderizado del visor en un navegador automatizado.

## Lote 2 - 2026-10-23

Se cotejaron las secciones seleccionadas de P 32–36 (impresas 2-19–2-23), P 87 (5-05) y P 89–92 (5-07–5-10). Se incorporaron diez pasajes privados nuevos, con quince tramos de texto y quince recortes de figuras. Se inspeccionaron las imágenes completas y los recortes; se ampliaron límites que cortaban la última línea de cuatro tramos antes de cerrar la revisión.

| Pasaje privado | Páginas PDF | Alcance cotejado y vínculo visual |
| --- | --- | --- |
| `owner-220-240-context` | 32 | Encabezado de variantes y dos diagramas del tablero, con correspondencia de los cuatro indicadores seleccionados. No se transcriben tacómetro ni odómetros. |
| `owner-220-240-temperature` | 33–34 | Sección 4 y continuación completa de su advertencia. Conserva la excepción explícita para AP-2000 sin atribuirla al 1.6. Diagramas de P 32 vinculados. |
| `owner-220-240-charging` | 35 | Sección 11 completa, incluyendo el recuadro que no aparecía en el OCR. Diagramas de P 32 vinculados; la referencia a cambio de correa sigue fuera del alcance. |
| `owner-220-240-oil` | 35–36 | Sección 12 con la advertencia de la página siguiente, ausente del OCR, y la distinción entre presión y nivel. |
| `owner-220-240-brakes` | 36 | Sección 13 y su recuadro completo, que el OCR tampoco había recuperado. Se conserva el contexto histórico sin convertirlo en permiso para seguir circulando. |
| `owner-engine-bay` | 87 | Título y leyenda completa como contexto del diagrama 1770. Se cotejó la correspondencia visual de llenado de aceite, varilla, frenos y refrigerante. El resto de la leyenda se conserva como contexto, sin habilitar procedimientos de otros sistemas. |
| `owner-oil-level` | 89 | Medición y lectura de varillas A/B, zonas a/b/c y advertencia de máximo, vinculadas a figura 1917. No incluye recomendación de aceite ni cifra de consumo de otras columnas. |
| `owner-oil-topup` | 90 | Reposición de la columna izquierda y advertencia de incendio omitida por OCR, vinculadas a figura 1772. No incluye drenaje ni capacidades de cambio; no se vincula por error a la figura 1305 del drenaje. |
| `owner-coolant-level` | 91 | Sección de refrigeración y advertencias completas, con figura 1773. No incluye transmisión, aditivos de aceite ni cambio de filtro de la misma página. |
| `owner-brake-fluid` | 92 | Sección de depósito de frenos y figura 1774. Se excluyen texto y figuras de ATF y combustible auxiliar. |

### Diferencias y discrepancias registradas

| Indicador | Tablero de 200 km/h | Tableros de 220/240 km/h |
| --- | --- | --- |
| Temperatura | 1 | 4 |
| Carga | 9 | 11 |
| Presión de aceite | 10 | 12 |
| Freno/nivel de fluido | 11 | 13 |

La correspondencia se refiere a los diagramas de estas páginas, no confirma qué tablero equipa el vehículo real. Los símbolos siguen siendo evidencia visual, no cadenas OCR.

La leyenda 6 del compartimiento de motor en P 87 imprime una referencia a 5-09 para frenos. La sección titulada depósito de fluido de frenos está en 5-10, P 92; en 5-09 está refrigeración. Se conserva la referencia impresa y se registra la discrepancia, sin sustituirla dentro de la transcripción. La compatibilidad no se deduce de ese enlace.

Se preservan cifras, unidades, código histórico de producto, proporciones y redacción impresa. Por ejemplo, la errata `reabaster` no se corrige editorialmente. Los literales de producto/reposición no constituyen recomendaciones actuales aprobadas. Las capacidades totales de cambio y las cifras de consumo quedaron fuera de los pasajes seleccionados; no se usaron para inferir cuánto líquido agregar.

El contexto de nivel, reposición y depósitos que faltaba en el lote 1 tiene ahora transcripción cotejada en estos nuevos pasajes. Se actualizaron sus notas privadas para distinguir ese avance de la aplicabilidad, que sigue pendiente. Los mapas de fusibles y las instrucciones de correa continúan fuera del alcance inicial.

### Resultado acumulado y comprobaciones

Hay 14 pasajes privados con 25 tramos de texto y 19 vínculos a recortes de figuras, distribuidos en las 14 páginas técnicas seleccionadas del propietario. Es cotejo de las secciones delimitadas: no son 14 páginas aprobadas en su totalidad ni un manual completamente revisado. Todos mantienen `rag_eligible=false` y aplicabilidad pendiente.

Se reconstruyeron los pasajes y el visor con comprobación de hashes, límites, dimensiones y lectura continua. Se comprobaron los enlaces locales de las 14 páginas y la conservación de los estados sin aprobación. Pasaron las 22 pruebas existentes y `git diff --check`; no se agregaron tests nuevos porque este lote modifica transcripciones privadas y documentación, no el código de procesamiento. No se ejecutó Gemini ni se verificó el renderizado del HTML en un navegador automatizado.

## Trabajo siguiente

Quedan sin cotejo de este conjunto las tres páginas de identificación (P 1, P 12 y R 3) y las cinco técnicas de reparación (R 69, R 72–75). También falta resolver la correspondencia con motor, combustible, mercado y tablero del vehículo objetivo y decidir qué fragmentos pueden aprobarse, cuáles deben recortarse y cuáles excluirse. Ninguna página se habilita por haber completado una transcripción.

El trabajo puede continuar por identificación y refrigeración del manual de reparación; la API y la persistencia pueden implementarse independientemente. La revisión profunda de ambos manuales completos sigue pendiente para una etapa posterior.
