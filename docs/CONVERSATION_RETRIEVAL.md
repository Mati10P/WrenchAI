# Recuperación con contexto de conversación

Actualización vigente: [procedimientos completos, estado conversacional v2 y vistas compactas](COMPLETE_PROCEDURES.md). Los bundles y resultados inferiores documentan las entregas anteriores.

Entrega local del 25 de octubre de 2026. Cierra el bloque de seguimientos y el
pendiente del PIN de una radio instalada que citaba el autoradio original.

## Comportamiento

La consulta actual se resuelve antes de buscar documentos. Se mantiene un tema
de navegación por chat, derivado de mensajes del usuario. Por ejemplo:

- «Cómo agrego aceite al motor» → «¿Cuánto lleva?» busca capacidad de aceite del
  motor. Al preguntar después por refrigerante, deja de agregar aceite a la
  consulta. «¿Y con el motor caliente?» conserva el nuevo tema de refrigerante.
- «Cómo ajusto la correa dentada» → «¿Cómo compruebo la tensión?» vuelve a
  consultar esa correa y puede mostrar la figura de comprobación de PDF 60.
- «Cómo cambio las pastillas delanteras» → «¿Y atrás?» pide precisar la pieza
  trasera. No transforma automáticamente un cambio de pastillas en la remoción
  del cilindro. Responder «las zapatas, las cintas» conserva cambio y eje trasero
  y recupera ese procedimiento.
- «Aceite del motor y refrigerante» → «¿Cuánto lleva?» pide elegir el componente.
  Una referencia sin antecedente, como «¿y atrás?» en un chat nuevo, también pide
  aclaración. Identificar solo el componente no autoriza inventar una operación.

Las preguntas completas sobre otro componente reemplazan el tema anterior,
incluyendo componentes desconocidos para el vocabulario del resolvedor. Los
temas de otros chats, las tareas del auto y el texto generado por Gemini no se
usan para completar la consulta documental.

## Estado y fuentes

`conversation.py` usa vocabulario mecánico y reglas acotadas en español para
identificar componente, familia, operación, eje y referencias. No llama a otro
modelo ni agrega LangChain. Las cantidades, modificaciones y especificaciones
no se deducen de respuestas anteriores.

El estado versionado se persiste en
`AssistantReply.context_snapshot.retrieval.conversation`, con consulta resuelta,
modo, mensajes de referencia y tema activo. Se retoma tras reiniciar la API y
conserva un ancla aunque los mensajes originales salgan de la ventana de veinte
mensajes. Las respuestas antiguas sin ese estado se interpretan a partir de los
mensajes de usuario disponibles. Un mensaje nuevo sin respuesta también puede
cambiar el tema: no se vuelve al último tema que tuvo una generación exitosa.
No requiere migración ni altera las respuestas ya guardadas.

La consulta resuelta se utiliza tanto en PostgreSQL para los pasajes revisados
como en la biblioteca de páginas/secciones y pgvector. Se recuperan fuentes
nuevas; no se reutilizan páginas antiguas como evidencia por haber sido citadas
en el historial. Gemini recibe el historial y la resolución como contexto de
navegación, y debe volver a respaldar texto e imágenes con las fuentes actuales.

Las referencias ambiguas se responden localmente, sin búsqueda ni generación.
Las reglas de seguridad conservan prioridad sobre aclaraciones y límites de
cobertura. Si Gemini necesita aclarar algo y no puede citar evidencia, se
conservan sus preguntas y se descarta el cuerpo no respaldado.

## Límite de documentación de equipos instalados

Los manuales locales son del vehículo original; no son la documentación de una
radio Bluetooth o alarma instalada. `document_scope.py` responde sin citar ni
adjuntar figuras del equipo original cuando se pide una credencial específica
o una configuración de un equipo instalado que requiere su propia documentación.

El caso «¿Cuál es el PIN exacto de emparejamiento de la radio Bluetooth que
instalé?» solicita marca/modelo. Si el usuario responde con esos datos, solicita
una referencia al manual del equipo, en vez de volver a preguntar marca/modelo.
No inventa PIN comunes ni concluye que el manual completo carece de información.
Un cambio posterior a aceite, frenos u otro tema sale de ese estado.

El límite no excluye procedimientos de fábrica por el solo hecho de que el auto
esté modificado: siguen permitidos, por ejemplo, consultar el fusible original
o comparar la regulación original de embrague con una modificación. La frontera
implementada cubre credenciales/configuración de radio y alarma; no representa
un catálogo completo de todos los equipos de terceros. Todavía no hay un flujo
de incorporación de sus manuales ni búsqueda web.

La interfaz omite nombres técnicos de respuestas locales y mensajes genéricos
de diagnóstico en esos pedidos de aclaración. Mantiene el indicador de modelo
para las respuestas reales de Gemini y las fuentes que efectivamente se citan.

## Ajustes de recuperación y evaluación

La primera ronda real conservó el tema de aceite pero recuperó una variante
diésel para la cantidad. Se agregó equivalencia de navegación entre
cantidad/capacidad y quantidade/quantidades/capacidade para recuperar también las
cantidades de abastecimiento del propietario. No se aprobaron cifras por esta
equivalencia: se leen las páginas originales.

También se separaron pastillas y zapatas/cintas de cilindro, mordaza y
servofreno en el filtro de componentes. Los títulos genéricos del sistema pueden
dar contexto; un componente vecino con vocabulario compartido no se convierte
en el procedimiento pedido.

La segunda ronda pasó las comprobaciones HTTP, pero la auditoría del estado
detectó que «con el motor caliente» se trataba como tema nuevo, pese a recuperar
la página esperada. Se corrigió el tratamiento de condiciones del motor y se
repitió el conjunto completo. Se conservaron las tres rondas, incluyendo los
fallos y las respuestas anteriores usadas para calibrar.

La tercera ronda pasó los controles HTTP y de estado, pero la revisión visual
mostró otra falla: en el seguimiento de tensión, Gemini tomó la puesta a punto
de arriba de PDF 59, aunque las secciones y la figura seleccionadas eran correctas.
Los controles de cita y figura no demostraban fidelidad del texto. La ronda queda
conservada como fallo de contenido, no como validación completa.

## Lectura visual enfocada

Las páginas enviadas a Gemini conservan solamente los píxeles originales de las
regiones del tema seleccionado; el resto queda blanco. La imagen original y el
enlace visible para el usuario permanecen completos. La vista se genera como
PNG sin pérdidas, sin reescribir texto, cifras ni dibujos, y conserva el tamaño
de página para ubicar las regiones. Los recortes de figuras mantienen sus bytes
y hashes anteriores.

`visual_evidence.py` valida dimensiones, escala y límites de cada región antes
de usarla. Los rectángulos proceden del catálogo preparado en el servidor, nunca
de coordenadas propuestas por el modelo. Geometría ausente o incompatible produce
un error de preparación; no vuelve silenciosamente a exponer temas vecinos.
El snapshot guarda el hash de la vista enviada y su alcance visual. Es una barrera
contra contaminación entre temas, no una garantía de que toda segmentación sea
correcta: la detección automática de títulos todavía requiere ampliar el cotejo.

Se preparó `sections-v6`, esquema 2, con 572 temas y 1.259 regiones con dimensiones;
las 597 asociaciones de figuras se conservan. SHA-256 del manifiesto:
`eec0a026cb7d0254f8d7e7c9ba9cdb59c5955e5fecd0f851f3889cfea3cab892`.
Biblioteca, índice vectorial y figuras v5 siguen intactos. Preparación y variables
de montaje: [SECTION_RETRIEVAL.md](SECTION_RETRIEVAL.md).

Validación final de esta entrega:

- **159 pruebas** correctas contra PostgreSQL temporal, incluidas 35 de conversación
  y diez de enfoque visual. Comprueban persistencia, aislamiento, límites de
  documentación, aclaraciones, seguridad, conservación de píxeles y originales.
- Build TypeScript/Vite, formato frontend, Ruff de archivos cambiados y
  `git diff --check` correctos.
- Cuarta ronda: seis conversaciones, **17 turnos HTTP 200**, con todos los
  controles automáticos correctos; consultas, anclas del mismo chat, respuestas
  persistidas y modificaciones originales auditadas.
- Auditoría de las **47 vistas** de manual de la ronda: originales y hashes de
  las imágenes enviadas verificados en el mismo contenedor de la API. La
  compresión PNG puede variar entre plataformas; no se comparan como si sus
  codificaciones fueran idénticas entre Windows y Linux.
- Revisión del caso de correa en el chat tras recargar: figura de ajuste de
  PDF 59 y texto de tensora/torsión, sin la marca del cigüeñal ni el rotor del
  distribuidor del tema anterior. Los pedidos de Bluetooth quedaron sin citas
  o imágenes del equipo original. Aceite recuperó la capacidad del propietario.

La respuesta de comprobación todavía puede repetir la preparación del ajuste;
no se interpreta su presencia como un criterio cuantitativo de tensión que el
texto del manual no expresa. La evaluación ampliada debe medir también precisión
de la respuesta al seguimiento, además de fuente, figura y aislamiento temático.

Casos reproducibles: `conversation-cases-v1.json` conserva el conjunto inicial;
`conversation-cases-v2.json` registra los criterios afinados y el tercer turno
de zapatas. `conversation-cases-v3.json` añade controles orientativos de contenido
para distinguir torsión de correa de puesta a punto; requieren además revisión visual. Ejecución desde la raíz:

```powershell
.venv/Scripts/python.exe scripts/evaluate_conversation.py --vehicle VEHICLE_ID --cases docs/conversation-cases-v3.json --output data/private/manuals/conversation-live-v4.json
```

El destino debe ser un archivo privado nuevo. Cada escenario crea un chat en
un vehículo sintético separado; los resultados y tiempos quedan preservados.
Evidencia local: `conversation-live-v1.json`, `conversation-live-v2.json`,
`conversation-live-v3.json`, `conversation-live-v4.json`,
`conversation-audit-v3.json`, `conversation-audit-v4.json`,
`conversation-visual-audit-v4.json` y `ui-conversation-v4.png`, bajo
`data/private/manuals/`. Las pruebas no modificaron el vehículo original.

Estos casos ya se usaron para ajustes y son regresión/calibración. El resolvedor
no interpreta universalmente cualquier frase coloquial, y la preparación
automática de manuales no valida todo su contenido ni aplicabilidad mecánica.
Siguen pendientes los veinte escenarios completos, evaluación independiente y
CI. Los datos de variante desconocidos se mantienen como tales.
