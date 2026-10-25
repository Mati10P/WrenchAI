# Respuestas con fuentes e ilustraciones

## Comportamiento vigente — 2026-10-25

El asistente responde de forma profesional y directa, con voseo natural. El prompt evita «che», saludos iniciales repetitivos y listas de diagnóstico innecesarias en preguntas informativas. Una normalización final retira saludos/muletillas y traduce términos residuales conocidos como `palheta`, conservando cifras, unidades, citas y contexto documental.

Las modificaciones se mencionan si interfieren con la aplicación de la información, cambian el procedimiento o el usuario pregunta por su influencia. La pregunta por pastillas no justifica hablar de suspensión, escape o comodidad de acceso. Ante una consulta explícita sobre una palanca modificada, el asistente distingue el procedimiento original de una equivalencia que los documentos no evalúan.

Cada fuente incluye `document`: identificador, título, tipo, autoría conocida o desconocida y estado de oficialidad. El manual de reparación de Gabriel Ferrer se distingue del manual del propietario, cuyo autor no se completa por inferencia. La referencia del auto de fábrica no convierte al libro de reparación en una publicación oficial.

El cuerpo nuevo usa `blocks`: párrafos con `source_ids` e ilustraciones con `figure_id` y pie. El frontend intercala los bloques, ofrece enlaces a la página PDF y mantiene la sección de fuentes. Las respuestas anteriores que solo tienen `summary` siguen siendo legibles. La estructura persiste en los JSON existentes; no requiere migración.

Los IDs de figuras y sus páginas deben pertenecer a las fuentes recuperadas. El servidor completa la unión de citas desde los párrafos, las figuras y sus páginas de contexto previamente registradas, y rechaza referencias ajenas, figuras repetidas o más de tres ilustraciones. El modelo no elige URLs ni coordenadas. La imagen servida se comprueba por SHA-256, incluyendo el hash del snapshot solicitado por el frontend. Si falla, la interfaz conserva el enlace al original.

Si se recuperaron páginas pero el generador no puede citar ninguna para responder, se aplica el guard `document-coverage-v2`: indica insuficiencia de las páginas consultadas, sin afirmar ausencia del tema en el manual completo. La advertencia determinística de seguridad sigue teniendo prioridad y no adjunta imágenes de reparación.

## Preparación privada de figuras

Se extraen las regiones `picture` del layout existente, con umbral 0,8 y área mínima del 1,5 % de la página. Las coordenadas se cotejan con las dimensiones del escaneo orientado, se agrega un margen y se recorta la imagen original a 240 dpi. No se generan dibujos ni se aprueba el OCR pendiente.

El bundle contiene **598 figuras de 407 páginas**, con hashes del recorte, de la página y del layout. Siete identificaciones de figuras de las páginas propietario 95/100 y reparación 83 se verificaron visualmente y se registraron en `docs/figure-labels-v1.json`. Sus etiquetas se usan también para localizar partes descritas visualmente; el resto de los recortes sigue siendo extracción automática y requiere comprobar su selección. Las etiquetas no validan todos los procedimientos del manual.

Desde la raíz, con Pillow disponible en el entorno documental:

```powershell
.venv/Scripts/python.exe scripts/prepare_manual_figures.py --library data/private/manuals/library-v1 --output data/private/manuals/figures-v1
```

El destino debe ser nuevo. El script escribe el manifest de activación solo después de completar el proceso y rechaza etiquetas que pertenezcan a otro hash de página. La biblioteca y sus vectores no se alteran ni requieren reindexarse.

En `.env` para Docker:

```dotenv
MANUAL_FIGURES_PATH=/manual-figures
MANUAL_FIGURES_DIRECTORY=./data/private/manuals/figures-v1
```

Compose monta ese directorio como solo lectura. La instalación actual usa `figures-v3`, conservando las exportaciones anteriores para auditoría. Para ejecutar el backend desde el host, `MANUAL_FIGURES_PATH` debe apuntar a la ruta absoluta local.

```powershell
docker compose up -d --build api frontend
```

Se ofrecen hasta tres candidatos grandes por página, doce recortes en total por consulta y tres ilustraciones finales. Los recortes deben sumar como máximo 4 MB, y las imágenes codificadas de páginas y figuras juntas no pueden superar 18 MB. Si se excede el límite, se solicita una consulta más específica. Se adjuntan al proveedor las páginas y figuras seleccionadas; se persisten metadatos y hashes, sin guardar base64 en el contexto.

## Verificación y límites

`docs/fidelity-cases-v1.json` define doce consultas y criterios antes de la primera ejecución. El evaluador crea un vehículo sintético aislado con el contexto autorizado de referencia, preserva cada intento y registra la revisión semántica como pendiente hasta cotejarla con las fuentes.

```powershell
.venv/Scripts/python.exe scripts/evaluate_answer_fidelity.py --vehicle VEHICLE_ID --output data/private/manuals/fidelity-live-new.json
```

- Primera ronda: dos respuestas rechazadas por validación y varios fallos de selección/cita. Se conservó la evidencia y se corrigieron la unión de referencias y la identificación de figuras.
- Segunda ronda: once de doce casos superaron las comprobaciones automáticas. El dibujo de antiniebla seguía sin localizarse correctamente; las etiquetas revisadas se incorporaron a la navegación.
- Tercera ronda: los doce casos superaron los controles automáticos de tono, modificaciones ajenas al tema, fuentes, imágenes esperadas e integridad. La revisión de contenido detectó que la respuesta sobre la palanca modificada repetía el procedimiento sin contestar su transferencia. Un reintento con la instrucción reforzada respondió la incertidumbre y conservó las citas 82/83 y la figura correcta. El caso del refrigerante cita fielmente la advertencia, pero explica solo parcialmente el «por qué»; no se considera una explicación mecánica completa.
- La revisión contrastó el texto, las unidades y las figuras utilizadas con las páginas originales. La prueba de pastillas conserva 9,8 mm, 40 Nm y 100 Nm tal como aparecen en PDF 198; no certifica aplicabilidad a todas las variantes. Las consultas explícitas de modificaciones no justifican inferir equivalencias nuevas.
- Backend: **95 pruebas pasaron**, incluidas integridad, bundles desactualizados, citas de párrafos/figuras, unión de fuentes, compatibilidad con respuestas anteriores, guard de falta de respaldo y estilo sin alterar valores. Frontend: TypeScript/Vite y formato correctos.
- Se verificaron las 598 imágenes y sus hashes; el índice de 546 vectores sigue disponible. Se comprobaron doce respuestas persistidas y la conservación de modificaciones, sin blobs de imágenes en el snapshot.
- Navegador: figura original de pastillas entre párrafos, pie y enlaces, persistencia tras recarga y apertura de la página completa PDF 198. Captura local privada: `data/private/manuals/ui-illustrated-answer.png`.

Evidencia privada: `fidelity-live-v1.json`, `fidelity-live-v2.json`, `fidelity-live-v3.json` y `fidelity-recheck-v4.json`. Se retiraron solo los dos vehículos sintéticos de las rondas superadas; queda la evaluación final disponible en la aplicación. Los registros originales del usuario no se modificaron.

Estos casos terminaron sirviendo para ajustar el sistema: constituyen una suite de regresión, no una evaluación independiente ni garantía de fidelidad universal. El modelo aún puede omitir matices, escribir errores menores o seleccionar mal un recorte no rotulado; siguen pendientes preguntas nuevas, evaluación mecánica profesional y cotejo completo de tablas/OCR. La búsqueda de preguntas elípticas de seguimiento continúa en el próximo bloque.
