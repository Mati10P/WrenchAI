# Matriz de aceptación del corpus inicial

Revisión: 2026-10-24. Esta matriz distingue integridad de evidencia, cotejo de transcripción y aceptación para responder sobre un vehículo. El propietario ya seleccionó el registro objetivo y aclaró que los demás eran pruebas del mismo auto. La selección, los datos declarados y sus modificaciones se conservan en `data/private/manuals/acceptance-target.json`, fuera de Git. El código de motor continúa desconocido; los datos declarados no prueban por sí solos cobertura del manual.

Una modificación registrada del instrumental impide asumir el tablero original del manual. Los ocho pasajes de testigos y el contexto de tablero quedan fuera del primer lote para este vehículo mientras no exista evidencia específica de correspondencia. Las reglas determinísticas propias de la aplicación siguen siendo independientes de esos pasajes. No se infieren equivalencias de sensores, cableado, numeración ni funcionamiento a partir del cambio declarado.

## Comprobación ejecutada

Se ejecutó `validate_passage` sobre los 22 artefactos privados actuales. Pasaron las comprobaciones de huellas del PDF, metadatos, imagen de página, OCR original, coordenadas y recortes; dimensiones de recortes, idioma y composición del texto. El informe privado es `data/private/manuals/acceptance-integrity-2026-10-24.json` e incluye la huella de cada artefacto cotejado.

Resultado: 22 pasajes con integridad comprobada, cero habilitados para RAG. Esta ejecución no vuelve a revisar visualmente las páginas ni confirma compatibilidad, vigencia o exactitud técnica. El cotejo visual anterior está documentado en `MVP_REVIEW_LOG.md`.

## Decisión por grupo

P = manual de propietario; R = manual de reparación. Las páginas son las del PDF.

| Pasajes | Páginas | Decisión para el primer conjunto | Evidencia o trabajo pendiente |
| --- | --- | --- | --- |
| `owner-source-cover`, `owner-engine-identification`, `repair-source-title` | P 1, P 12; R 3 | Solo identificación; fuera del corpus de diagnóstico | Completar edición/cobertura. Las ubicaciones ilustradas no identifican el motor real. |
| `owner-220-240-context` | P 32 | Referencia visual de variante; fuera del corpus de diagnóstico | Identificar el tablero real antes de asociar sus números con los testigos. |
| `repair-pressure-ambiguity` | R 74 | Excluido de instrucciones y de evidencia técnica habilitada | La unidad impresa está incompleta. Conservarlo para el caso de abstención X04, sin completar ni convertir cifras. |
| `owner-200-temperature`, `owner-220-240-temperature` | P 28–29, P 33–34 | Pendientes; seleccionar únicamente la variante compatible | Confirmar tablero y alcance del manual. Recortar referencias a fusibles fuera del conjunto y excepciones no aplicables; conservar advertencias y continuidad. |
| `owner-200-charging`, `owner-220-240-charging` | P 30, P 35 | Pendientes; seleccionar únicamente la variante compatible | Confirmar tablero. Excluir instrucciones de correa fuera del alcance y afirmaciones de causa que no estén comprobadas para el caso. |
| `owner-200-oil`, `owner-220-240-oil` | P 30, P 35–36 | Pendientes; seleccionar únicamente la variante compatible | Confirmar tablero y contexto de nivel/reposición. Mantener distinción entre presión y nivel y conservar advertencias. |
| `owner-200-brakes`, `owner-220-240-brakes` | P 31, P 36 | Pendientes; seleccionar únicamente la variante compatible | Confirmar tablero y contexto del depósito. No convertir una indicación histórica en autorización para seguir circulando. |
| `owner-engine-bay` | P 87 | Pendiente como contexto de componentes | Verificar montaje/motor y correspondencia de la figura. Mantener la discrepancia de referencia de frenos como anotación separada. |
| `owner-oil-level`, `owner-oil-topup` | P 89–90 | Candidatos a primer lote, todavía pendientes | Confirmar motor/varilla y cobertura. Delimitar lectura de nivel conservando advertencias; no transformar zonas en volúmenes ni adoptar productos o porciones históricas sin validación. |
| `owner-coolant-level`, `owner-brake-fluid` | P 91–92 | Candidatos a primer lote, todavía pendientes | Confirmar cobertura y depósito/montaje. Separar productos y proporciones históricas; conservar advertencias. No añadir especificaciones ausentes ni deducir umbrales. |
| `repair-cooling-overview`, `repair-cooling-fan-a`, `repair-cooling-fan-b` | R 69, R 72–73 | Pendientes; postergar respecto del primer lote | Establecer montaje y variante con evidencia. No asignar aire acondicionado por la apariencia del dibujo ni mezclar numeración. |
| `repair-thermal-switch-context` | R 74–75 | Pendiente; postergar respecto del primer lote | Identificar interruptor, etapas, montaje y aire acondicionado; resolver escala de unidad con evidencia. La tabla no define umbrales de seguridad del motor. |

Los grupos cubren los 22 IDs una sola vez: tres de identificación, uno de contexto de variante, uno excluido y 17 pasajes técnicos pendientes. Que un candidato pueda formar parte del primer lote no constituye aprobación.

## Preparación de la ingesta

1. Usar el registro objetivo confirmado en el archivo privado y mantener explícitos los datos desconocidos. No combinar hechos de registros de prueba. Mercado de fabricación y mercado de comercialización no se intercambian por inferencia.
2. Resolver la cobertura y los requisitos específicos del primer lote; registrar la evidencia de cada decisión. No exigir tablero para un fragmento que no dependa de él, ni omitir montaje/varilla cuando sí condicionen el contenido.
3. Delimitar fragmentos con página, texto original, advertencias y vínculo al pasaje cotejado. Un fragmento que atraviesa páginas necesita citas que conserven todas sus páginas; el contrato actual solo tiene `page` singular.
4. Registrar aprobación, responsable, referencia de revisión y requisitos compatibles. El contrato actual solo filtra marca, modelo, año, combustible, código de motor y mercado: no permite representar tablero, varilla o montaje. Antes de habilitar un fragmento condicionado por esos datos, ampliar el contrato y registrar esos hechos, o mantenerlo pendiente. No ocultar esos requisitos en notas libres.
5. Validar el conjunto y sus originales; conservar una copia del corpus activo antes de reemplazarlo mediante el importador administrativo.
6. Probar recuperación compatible, rechazo de variantes incompatibles/desconocidas y citas persistentes en una base temporal. Para fuentes portuguesas, evaluar también la recuperación con consultas españolas antes de considerar completo el circuito.

## Resultado de este bloque

La integridad de los 22 pasajes queda verificada, el vehículo objetivo está seleccionado y el primer lote se concentra en niveles y depósitos, conservando sus requisitos pendientes. La aceptación/importación real sigue pendiente de aplicabilidad y delimitación de fragmentos. No se modificaron hechos del auto, transcripciones, aprobaciones ni el corpus de la aplicación.
