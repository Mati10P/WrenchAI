# API de incidencias y reparaciones

Primer bloque funcional: FastAPI + Pydantic + SQLAlchemy + Alembic + PostgreSQL. La aplicación registra trabajo mecánico; todavía no diagnostica con IA ni consulta manuales. No calcula si una medición es normal o peligrosa.

## Ejecutar con Docker

Requiere Docker Desktop con motor Linux funcionando y puertos locales 8000/55432 disponibles. Desde la raíz:

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://localhost:8000/ready
```

Abrir `http://localhost:8000/docs` para probar la API con su interfaz OpenAPI. `/health` comprueba el proceso; `/ready` comprueba acceso a la tabla de vehículos, incluida la necesidad de migraciones. En Compose se aplican las migraciones antes de arrancar la API.

Compose usa credenciales de desarrollo explícitas y puertos ligados a `127.0.0.1`. `.env.example` permite configurar otra instancia local; no es una configuración de producción. No hay autenticación ni aislamiento por usuario. La imagen de PostgreSQL incluye pgvector, pero todavía no se creó la extensión ni se implementó búsqueda vectorial.

Los datos quedan en el volumen `wrenchai_postgres_data`. `docker compose stop` detiene servicios sin borrar el volumen; `docker compose start` los vuelve a iniciar. No usar `docker compose down -v` para detener la aplicación si se quiere conservar su historial.

## Flujo de ejemplo

Datos sintéticos: las observaciones y la resolución son entradas del ejemplo, no diagnósticos ni reparaciones efectuadas.

```powershell
$apiBase = 'http://localhost:8000'
$vehicleBody = @{name='Gol de ejemplo'; model='Gol G2'; year=1998} | ConvertTo-Json
$vehicle = Invoke-RestMethod "$apiBase/vehicles" -Method Post -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($vehicleBody))

$incidentBody = @{title='Pérdida recurrente de refrigerante'; description='Caso sintético: el nivel vuelve a bajar.'; symptoms=@('Descenso recurrente'); mileage=120000} | ConvertTo-Json
$incident = Invoke-RestMethod "$apiBase/vehicles/$($vehicle.id)/incidents" -Method Post -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($incidentBody))

$resolutionBody = @{title=$incident.title; description=$incident.description; symptoms=$incident.symptoms; mileage=$incident.mileage; status='RESOLVED'; resolution='Ejemplo sintético: se registró una intervención del taller y su seguimiento.'} | ConvertTo-Json
Invoke-RestMethod "$apiBase/incidents/$($incident.id)" -Method Put -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($resolutionBody))
Invoke-RestMethod "$apiBase/vehicles/$($vehicle.id)/incidents?status=RESOLVED"
```

El detalle de incidencia incluye sus mediciones. Para agregar una, usar `POST /incidents/{id}/measurements` con `name`, `value`, `unit` y opcionalmente `conditions`. Los valores se almacenan como decimales, hasta catorce dígitos totales y cuatro decimales, sin redondear entradas con mayor precisión. Las unidades se registran como texto aportado por el usuario; no se convierten ni se infieren. La fecha de observación se asigna al registrar la medición en esta versión, no permite cargar mediciones retrospectivas con su fecha original.

## Contrato y decisiones

| Recurso | Operaciones |
| --- | --- |
| Vehículos | `POST /vehicles`, `GET /vehicles`, `GET/PUT/DELETE /vehicles/{id}` |
| Incidencias de vehículo | `POST/GET /vehicles/{id}/incidents`; filtro opcional `status` |
| Incidencia individual | `GET/PUT/DELETE /incidents/{id}` |
| Mediciones | `POST /incidents/{id}/measurements`; lectura dentro del detalle de incidencia |

- Un nombre basta para registrar un vehículo. Marca, modelo, año, combustible, código de motor, mercado y notas son opcionales. Nulo significa desconocido; no se completa desde un manual. No se solicita patente, VIN ni número de motor completo.
- Una incidencia registra título, descripción, síntomas y kilometraje opcional. Comienza en `OPEN`; puede pasar a `IN_PROGRESS` y `RESOLVED`.
- `RESOLVED` exige resolución no vacía y guarda fecha de cierre. Los otros estados no admiten resolución. La validación se repite en la base con restricciones de integridad. La resolución es un registro informado, no una causa certificada.
- En esta primera versión no se reabre una incidencia resuelta; puede corregirse su descripción/resolución manteniendo el estado de cierre. No hay todavía bitácora de versiones o de cada transición.
- `PUT` reemplaza todos los campos editables del recurso. Enviar el objeto completo; los opcionales omitidos vuelven a su valor por defecto. No hay `PATCH` todavía.
- Borrar un vehículo con incidencias devuelve `409`. El borrado explícito de una incidencia elimina también sus mediciones; es permanente. La API no borra el historial al resolver un caso.
- Listas con `limit` entre 1 y 100 y `offset` no negativo. Recurso inexistente: `404`; entrada inválida: `422`; conflicto de integridad/estado: `409`.
- No hay conversión automática de datos del prototipo SQLite ni ingesta del OCR privado.

## Estructura para explicar en una entrevista

`schemas.py` valida lo que entra y define lo que se devuelve. `models.py` describe las tablas y sus restricciones. `main.py` implementa los recursos REST y usa una sesión de base por solicitud; `database.py` configura la conexión. Las migraciones versionadas crean la estructura: la API no crea tablas al importar el módulo. El estado y la resolución se guardan en una misma transacción.

La organización usa una aplicación pequeña y módulos explícitos. Se podrán separar rutas y servicios cuando llegue el diagnóstico; no se introducen repositorios genéricos ni agentes para este CRUD.

Referencias de implementación: [sesiones en FastAPI](https://fastapi.tiangolo.com/tutorial/sql-databases/), [transacciones y sesiones SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/session_basics.html), [migraciones Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

## Desarrollo y pruebas

Desde la raíz, después de iniciar PostgreSQL con `docker compose up -d db`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
$env:DATABASE_URL='postgresql+psycopg://wrenchai:wrenchai_local@127.0.0.1:55432/wrenchai'
Push-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Pop-Location
```

Si la API de Compose ya ocupa el puerto 8000, usar solo esa instancia o detener `api` antes de iniciar Uvicorn desde el host. Ctrl+C detiene Uvicorn.

Las pruebas requieren PostgreSQL real y permiso de crear bases. `TEST_DATABASE_URL` puede apuntar a una instancia local de pruebas; por defecto usan la de Compose. Crean una base de nombre aleatorio `wrenchai_test_<uuid>`, aplican la migración dos veces, comprueban diferencias contra modelos y eliminan únicamente esa base creada por el fixture al terminar. No ejecutarlas contra un servidor compartido de producción. El esquema de la aplicación no se crea con SQLite ni `create_all` para simular estas pruebas.

Las dependencias directas tienen versiones fijadas. Todavía no hay lock de dependencias transitivas ni CI implementada.

## Validación realizada - 2026-10-23

Pasaron 14 pruebas de integración contra PostgreSQL 17, usando migraciones y una base temporal exclusiva del fixture. Se comprobó repetición de migración y ausencia de diferencias pendientes entre modelos y esquema. La suite cubre cierre consistente, persistencia al recrear la aplicación, precisión/unidades de mediciones, entradas inválidas, relaciones, borrados y disponibilidad.

También se construyó la imagen de la API, se creó un ejemplo sintético por HTTP y se reiniciaron API y PostgreSQL con Compose. La resolución y la medición permanecieron disponibles, incluido el decimal exacto. Queda un vehículo/caso sintético en la base local como demostración; no representa una avería real. El identificador de la comprobación se guarda fuera de Git en `data/private/backend/persistence-smoke.json`.

La suite emite una advertencia de deprecación del cliente HTTP de Starlette respecto de `httpx`; las pruebas pasan y no se ocultó la advertencia. Se resolverá al actualizar el cliente de pruebas y sus dependencias. No se ejecutaron pruebas de Gemini ni se implementó autenticación, frontend o búsqueda documental en este bloque.
