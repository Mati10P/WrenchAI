# Investigación documental

Fecha de consulta: 2026-10-22. Vehículo objetivo declarado: Volkswagen Gol G2 1.6 MI 1998, motor AP. La compatibilidad exacta por mercado, combustible y código de motor sigue pendiente.

## Candidatos descargados (privados, todavía no aprobados para RAG)

1. Manual de propietario: https://onlycars.com.br/wp-content/uploads/2024/02/manual-proprietario-gol-bola-g2-vw.pdf
   - Local: data/private/manuals/originals/gol-owner-candidate.pdf
   - Portal de descubrimiento: https://onlycars.com.br/2024/02/manual-do-proprietario-volkswagen-gol-bola-g2.html
   - El portal lo describe como primera edición de agosto de 1997, línea 1998. Esta descripción aún requiere cotejo con el propio documento.
   - Es un manual de propietario, no prueba de cobertura de procedimientos de taller.
2. Manual de reparación: https://www.volkspage.net/technik/manuaisecatalogos/02/manualdereparacionysjustes_vwgolg2.pdf
   - Local: data/private/manuals/originals/gol-repair-candidate.pdf
   - Pendiente verificar editor, edición, cobertura de inyección multipunto y compatibilidad. No afirmar que sea un manual original de Volkswagen.

## Otras fuentes consultadas

- Catálogo oficial: https://www.vw.com.br/pt/servicos-e-acessorios/servicos-e-produtos/manuais-e-garantia/manuais.html
- Propietario que declara haber escaneado su manual: https://golbola98.blogspot.com/2015/07/dica-manual-de-instrucoes-gol-bola.html
- Archivo enlazado por ese propietario: https://drive.google.com/file/d/0B7sRqZVIEikuckdQSkxoeVBSbW8/view?resourcekey=0-hmQ2cUD7b-_iXuRJRQUeEQ&usp=sharing

## Proceso de aceptación

Conservar el PDF original y su SHA-256. Inventariar cada página con número PDF y número impreso. Extraer texto o aplicar OCR fuera de la aplicación. Mantener portugués original; cualquier traducción será derivada y separada. Revisar tablas visualmente, no inferir columnas o valores. Cada página tendrá estado pendiente, revisada o excluida y motivo. Solo fragmentos revisados y compatibles podrán respaldar respuestas.

La descarga pública no demuestra permiso de redistribución. No incluir los PDFs ni sus transcripciones en GitHub. Los manuales de propietario y reparación tendrán roles separados en el corpus.

## Inspección local inicial

- Propietario: 144 páginas, ninguna con texto extraíble. Portada revisada: Manual de Instruções Gol con marca VW; escaneo girado. Edición interior y compatibilidad exacta todavía pendientes.
- Reparación: 388 páginas, ninguna con texto extraíble. Portada revisada: Gabriel Ferrer, Reparación y ajuste de automóviles; menciona motores nafteros 1.6/1.8/2.0 y diésel 1.6, inyección monopunto y multipunto. No clasificar como publicación original del fabricante.
- Ambos requieren OCR y verificación visual antes de RAG. No se ha completado la limpieza.
- Inventario con hashes: data/private/manuals/inventory.json.
- SHA-256 propietario: bf515cb34cf95ad8093166defbf87d13fb74551fe7580da93f7f28efc1e55034
- SHA-256 reparación: e20fd2fc3e23db4d996f24ca10fbe91e96b366ae7f992b0d9e95792a3ce3a284

## Revisión OCR - 2026-10-23

El propietario confirmó que ambos manuales son adecuados para trabajar. Se generó una segunda versión de OCR de 532 páginas con correcciones de orientación y trazabilidad de imágenes, texto y coordenadas. La aprobación de los manuales no sustituye la revisión técnica de cada transcripción. Ver OCR_WORKFLOW.md e IMPLEMENTATION_PLAN.md para el estado real.
