# Chat y menú Mi auto

La entrada principal es http://localhost:5173. La interfaz guarda mensajes reales en PostgreSQL, pero todavía no tiene un modelo conectado ni consulta manuales o internet. El aviso junto al cuadro de texto lo indica explícitamente.

## Recorrido

1. Abrir **Mi auto → Datos** y completar nombre, kilometraje y modificaciones conocidas. Los datos técnicos son opcionales y se despliegan solo al editar. Se recuerda el auto seleccionado en este navegador.
2. Escribir un problema y enviar. El primer mensaje crea una conversación y un pendiente por detrás, sin pedir título, síntomas ni estado en formularios.
3. Agregar observaciones en el mismo chat. Se conservan en el mismo caso; no se crea una avería por cada mensaje. Enter envía y Shift + Enter agrega una línea.
4. Consultar **Mi auto → Pendientes** o **Conversaciones** para retomar un caso. Al recargar permanecen los mensajes.
5. Si se resolvió, usar **Ya lo resolví** y describir qué se hizo. También se puede registrar mantenimiento independiente desde **Mi auto → Trabajos → Anotar un trabajo realizado**.
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
