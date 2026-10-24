# Chat y menú Mi auto

La entrada principal es http://localhost:5173. La interfaz guarda mensajes y respuestas en PostgreSQL. La integración con Gemini requiere una clave del servidor; sin ella conserva los mensajes y muestra el error. No hay evidencia documental aprobada habilitada ni búsqueda web. Ver ASSISTANT.md.

## Recorrido

1. Abrir **Mi auto → Datos** y completar marca, modelo, año, kilometraje y modificaciones conocidas. Marca, modelo, año y kilometraje están visibles en Datos y al editar. Los demás datos técnicos son opcionales y se despliegan al editar. Se recuerda el auto seleccionado en este navegador.
2. Escribir un problema y enviar. El primer mensaje crea una conversación y un pendiente por detrás, sin pedir título, síntomas ni estado en formularios.
3. Agregar observaciones en el mismo chat. Se conservan en el mismo caso; no se crea una avería por cada mensaje. Enter envía y Shift + Enter agrega una línea.
4. Consultar **Mi auto → To-do** o **Conversaciones** para retomar un caso. Al recargar permanecen los mensajes.
5. Si se resolvió, usar **Ya lo resolví** y describir qué se hizo. También se puede registrar mantenimiento independiente desde **Mi auto → To-do → Agregar tarea**.
6. Usar **Nuevo chat** para otro problema. El borrador no enviado se descarta al cambiar de conversación o vehículo.

Los registros anteriores, sus mediciones y resoluciones siguen disponibles. Se retiró la acción Agregar medición del chat a pedido del propietario. Los estados internos OPEN/IN_PROGRESS se agrupan como pendientes en el menú. El kilometraje se carga explícitamente: no se deduce del texto, del historial ni de los manuales.

## Ejecución y desarrollo

Desde la raíz:

```powershell
docker compose up --build -d
```

Compose aplica migraciones antes de iniciar la API y sirve React con Nginx en 5173. `/api` se deriva al backend. La documentación técnica permanece en http://localhost:8000/docs.

Para desarrollo, iniciar `docker compose up -d db api`, detener solo el frontend de Compose con `docker compose stop frontend` y ejecutar desde `frontend`:

```powershell
npm ci
npm run dev
```

Vite usa 5173 y un proxy a 127.0.0.1:8000. Detener Vite antes de volver a iniciar el contenedor frontend.

```powershell
npm run build
npm run format:check
```

El build comprueba TypeScript. Se versiona package-lock.json; node_modules y dist se excluyen. Las fuentes se empaquetan localmente. No hay claves en el cliente.

## Organización

- `src/App.tsx`: selección del auto, conversación, navegación y menú secundario.
- `src/api.ts`: contratos, mensajes de error y paginación de lecturas.
- `src/components/Modal.tsx` y `EditorFields.tsx`: diálogos y edición secundaria del contexto y resolución.
- `src/style.css`: chat con cuadro de escritura fijo dentro del espacio disponible y adaptación a pantallas pequeñas.
- `nginx.conf`, `Dockerfile` y `vite.config.ts`: entrega y proxy local.

Las rutas anteriores con IDs de vehículo/incidencia abren ahora su conversación. Los reintentos del mensaje conservan su ID mientras permanezcan en el mismo borrador/contexto, evitando duplicaciones si se perdió la respuesta del servidor. El backend valida el contexto y guarda la incidencia y el primer mensaje en una transacción.

## Alcance siguiente

Conectar el asistente con el contexto persistido del auto, sus modificaciones e historial; consultar primero manuales compatibles y usar búsqueda web complementaria si falta evidencia. Mostrar fuentes, incertidumbre y preguntas concretas de seguimiento. El guardado actual no implica comprensión del mensaje ni una respuesta mecánica. Tampoco se actualizan automáticamente datos del auto por escribirlos en el chat.

La revisión profunda de ambos manuales completos continúa pendiente. Solo podrán respaldar respuestas los fragmentos aceptados; la nueva interfaz no cambia esa condición. No hay autenticación ni despliegue público en este bloque.

## Verificación del cambio

Pasaron 17 pruebas de integración del backend contra PostgreSQL real, incluyendo migraciones, persistencia de contexto y mensajes, reintentos sin duplicar pendientes, aislamiento de IDs por contexto y registro de trabajos. Se conserva la advertencia conocida de deprecación de httpx en el cliente de pruebas. También pasaron el build TypeScript/Vite y la construcción Docker.

En el navegador se guardaron kilometraje y modificaciones del vehículo sintético; se envió un problema, un seguimiento y se recargó para comprobar ambos mensajes. El menú mostró un único pendiente y permitió anotar un trabajo independiente, conservando también la reparación anterior. Se comprobó a 390 px que el documento no desborda horizontalmente y que el cuadro de escritura queda dentro del alto disponible. Son verificaciones manuales asistidas, no una suite automática ni una auditoría completa de accesibilidad. No se ejecutaron diagnósticos, búsqueda web ni llamadas a Gemini.

## Lista unificada de tareas

Pendientes y trabajos se reúnen en Tareas, con los pendientes primero y los completados debajo. Cada fila tiene check, título, fecha de alta, fecha del trabajo, kilometraje al realizarlo y notas. Se puede agregar una tarea manualmente o desde un chat. El primer check solicita los detalles del trabajo; desmarcarlo vuelve la tarea a pendiente conservando notas, fecha y kilómetros. Editar detalles permite corregir esos datos.

La fecha del trabajo es una fecha de calendario indicada por el usuario, separada del momento de registro. Los kilómetros del trabajo tampoco reemplazan el kilometraje original del problema ni el actual del auto. Datos desconocidos permanecen vacíos. La migración conserva las resoluciones anteriores como notas y no inventa fechas ni kilometrajes.

Validación de tareas: 19 pruebas de integración contra PostgreSQL, build TypeScript/Vite, Ruff y construcción Docker correctos. En navegador se verificaron los datos principales, el check de un caso sintético y la persistencia de fecha, kilómetros y notas tras recargar, con pendientes primero.

## To-do en tabla

Se renombra Tareas a To-do y se presenta como tabla con check, fecha del trabajo, descripción, kilómetros y costo. Pendientes primero; tocar una celda abre la edición de sus detalles. El costo es dinero ya pagado, en una misma moneda elegida por el usuario, y el total suma todos los importes cargados del auto, también los pendientes. Un costo vacío no significa cero y se indica cuántos faltan. PostgreSQL usa Numeric(14,2) y la suma visual usa centavos enteros. La migración 0004 conserva los registros anteriores con costo desconocido.

Verificación: 25 pruebas de integración y build TypeScript/Vite correctos. En navegador se guardó un costo sintético de 1234,56, se recargó la página y se comprobó el total 1.234,56. La tabla permite desplazamiento horizontal en pantallas estrechas.

## Respuestas del asistente

Después de guardar un mensaje se solicita su respuesta. Si falla, Generar respuesta permite reintentar sin reenviar el mensaje. Se muestran hipótesis, preguntas, comprobaciones y fuentes citadas cuando existan. Los avisos determinísticos se identifican como reglas de seguridad. No se modifican datos del auto ni se completan tareas automáticamente. Configuración y limitaciones actuales: [ASSISTANT.md](ASSISTANT.md).

Ajuste visual solicitado: el selector queda dentro del cuadro de escritura, en la fila inferior derecha junto al botón de enviar, con nombre corto y sin una etiqueta visible adicional. Conserva nombre accesible, selección por teclado y preferencia persistida.

El compositor arranca con una línea (36 px) y una fila inferior de controles de 32 px, para una altura aproximada de 96 px. El textarea crece con el texto hasta 144 px y luego permite desplazamiento; vuelve a compacto al enviar o borrar. Se elimina el margen heredado del selector y el botón de enviar pasa a circular. Compilación verificada; revisión visual pendiente por acceso al navegador deshabilitado.
