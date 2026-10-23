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

## Próximo lote

Cotejar P 32–36 para el otro grupo de tableros, preservando sus diferencias y continuaciones. Después revisar P 87 y 89–92 para cerrar el contexto de depósitos, varilla y advertencias. Identificar el vehículo y la cobertura documental antes de aprobar fragmentos para RAG. La revisión profunda de ambos manuales completos continúa pendiente.
