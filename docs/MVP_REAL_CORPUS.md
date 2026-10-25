# Primer RAG con manuales reales — 2026-10-24

El corpus local activo contiene cinco fragmentos de dos originales privados. La referencia de fábrica está seleccionada en el vehículo objetivo autorizado por el propietario; sus campos y modificaciones se conservaron. Los demás vehículos no reciben este perfil automáticamente.

| Fragmento | Página PDF | Alcance |
| --- | --- | --- |
| mvp-owner-oil-level | 89 | Procedimiento de medición y advertencias de máximo; excluye clasificación de varillas por zonas. |
| mvp-owner-oil-topup | 90 | Reposición y advertencia de incendio; la porción histórica no determina cuánto falta. |
| mvp-owner-coolant-level | 91 | Nivel, pérdida recurrente y tapa caliente; excluye producto, proporción y reposición de emergencia. |
| mvp-owner-brake-fluid | 92 | Depósito, descenso y mezcla; excluye recomendación comercial. No prescribe DOT ni autoriza circular. |
| mvp-repair-cooling-overview | 69 | Leyenda de componentes de la figura II.75; sin torques, desmontajes ni atribución del montaje real. |

Se inspeccionaron los ocho recortes de texto utilizados y se verificó nuevamente su integridad con `validate_passage`. Los extractos son cadenas exactas del texto cotejado; las omisiones se marcan con `[…]`. El original portugués se conserva y se muestra en las citas. Las etiquetas españolas de búsqueda son metadatos, no traducciones presentadas como evidencia.

## Preparación y reproducción local

La decisión privada `data/private/manuals/acceptance-decisions-v1.json` incluye hash del pasaje revisado, extractos, alcance, responsable y aprobación para referencia de fábrica. No modifica las capas OCR ni transforma su estado histórico en aprobación de páginas completas.

Desde la raíz, exportar a una carpeta nueva:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_accepted_corpus.py --decisions data/private/manuals/acceptance-decisions-v1.json --output data/private/manuals/accepted-v1
```

La carpeta `accepted-v1` ya existe en esta máquina. Para reproducir usar otro nombre; el exportador no sobrescribe. Produce corpus.json, audit.json con offsets y sources con copias de originales por hash. Valida los extractos antes de escribir. Todos estos archivos permanecen excluidos de Git y fuera de las imágenes Docker.

Con `DATABASE_URL` configurada para la instancia local, desde `backend`:

```powershell
..\.venv\Scripts\python.exe -m app.corpus import ../data/private/manuals/accepted-v1/corpus.json --sources ../data/private/manuals/accepted-v1/sources
```

El importador reemplaza el corpus completo. Se respaldó el conjunto anterior vacío en `data/private/manuals/pre-rag-v1-corpus.json`. En Mi auto → Editar datos → Datos técnicos opcionales, elegir «Gol G2 1.6 MI 1998 de fábrica». Se guarda como `manual_reference`, independiente de los hechos reales. La migración 0007 deja los vehículos existentes sin perfil hasta selección explícita.

## Recuperación y generación

Los fragmentos con `reference_profile` usan los hechos del perfil explícito (marca, modelo, año y combustible). No inventa código de motor ni mercado: requisitos que esos hechos no satisfagan siguen excluidos. Los fragmentos anteriores sin perfil conservan comparación contra hechos del vehículo. `scope` es obligatorio para referencias de fábrica.

PostgreSQL busca el mensaje actual con ranking textual OR sobre texto, título y etiquetas españolas revisadas. Se filtran palabras genéricas como «manual» y «Gol». Esto mejora el lote acotado; no implementa embeddings, traducción universal ni comprensión semántica. Puede recuperar fuentes secundarias por palabras compartidas como «nivel»; Gemini debe utilizar solo las pertinentes. Las consultas elípticas de seguimiento pueden necesitar reformular el tema explícitamente.

El contexto persistido incluye `retrieval_reference`, hechos reales, modificaciones y fuentes. Gemini responde con citas y contextualiza modificaciones pertinentes sin atribuirlas al manual. Las reglas de riesgo siguen teniendo prioridad y pueden responder sin llamar al modelo. Si el perfil de fábrica no recupera ninguna fuente, una respuesta fija `document-coverage-v1` declara el límite del lote sin atribuir contenido al manual completo; no llama a Gemini.

## Verificación y límites observados

- 66 pruebas completas de backend contra PostgreSQL temporal y 26 de herramientas documentales pasaron. Se cubren migración, perfil explícito, consulta española de texto portugués, conservación de modificaciones, exclusión de motor incompatible, cambio de tema y persistencia de citas.
- Build TypeScript/Vite, formato, Ruff de módulos modificados y construcción Docker correctos. API/frontend actualizados localmente.
- Cinco búsquedas HTTP por el proxy comprobaron aceite, refrigerante, frenos, componentes y ausencia de resultados para Bluetooth. Los resultados pertinentes aparecieron primero.
- Cinco llamadas reales a Gemini se registraron en `data/private/manuals/rag-live-v1.json`, con latencias de 1,98 a 2,94 segundos. Aceite citó P 89 y refrigerante P 91; las respuestas quedaron persistidas. Son muestras puntuales, no una evaluación de los 20 escenarios.
- El primer ejemplo de aceite distinguió la medición del manual de una hipótesis sobre la suspensión. En refrigerante aparecieron menciones innecesarias de modificaciones y términos portugueses; se reforzó el prompt, pero la pertinencia de esa contextualización sigue requiriendo evaluación.
- Gemini afirmó ausencia de Bluetooth en el manual completo aunque no había fuentes, incluso tras reforzar el prompt. Por eso la ausencia total de resultados bajo el perfil usa ahora el mensaje fijo de cobertura. Las pruebas anteriores se conservan como evidencia de la limitación, no como ejemplos aprobados de conducta final.
- No se completó el recorrido visual: el navegador integrado estaba deshabilitado y Computer Use se detuvo al no poder verificar con certeza la URL del navegador Windows. Las pruebas reales usaron HTTP a través del mismo proxy de la interfaz.

Pendientes: revisión visual del chat, evaluación mecánica completa, mejora semántica con pgvector, ampliación por lotes y búsqueda web. El lote habilitado es útil para probar RAG real, no representa cobertura de ambos manuales completos.
