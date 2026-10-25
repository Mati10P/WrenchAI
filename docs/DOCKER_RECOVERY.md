# Incidente local de Docker Desktop - 2026-10-23

Al iniciar Docker para probar PostgreSQL, Desktop falló antes de levantar el motor. El registro apuntaba a `initializing Inference manager` y a un archivo `dockerInference` que Windows no permitía eliminar. La inspección local mostró un punto de reanálisis en el directorio temporal de ejecución. Coincide con el [incidente reportado en Docker Desktop](https://github.com/docker/desktop-feedback/issues/554).

Con Desktop detenido y sin procesos de backend, se conservaron las carpetas de ejecución `Docker/run` y `docker-secrets-engine` bajo nombres con sufijo `.wrenchai-backup-20261023-132700`, dentro de sus directorios originales de datos locales del usuario. Se recrearon las carpetas vacías y se inició Docker normalmente. No se eliminaron sockets individualmente ni se usó restablecimiento de fábrica, limpieza de volúmenes o desregistro de WSL.

`docker info` volvió a responder con Engine 29.6.2. Se comprobó que seguían visibles el contenedor `n8n` y los volúmenes existentes `n8n_data` y `trivy-cache`. No se arrancó n8n ni se inspeccionó su contenido. Las carpetas de respaldo se conservaron; no forman parte del repositorio.

Esta reparación corresponde al error observado, no es un paso rutinario de instalación de WrenchAI. No automatizarla al iniciar la aplicación ni aplicarla ante cualquier fallo de Docker. No se cambiaron opciones del Model Runner ni se enviaron diagnósticos a terceros.

## Recurrencia del 25 de octubre de 2026

Desktop volvió a fallar por `dockerInference`; después apareció el mismo tipo de
fallo en `%LOCALAPPDATA%/docker-secrets-engine/engine.sock`. Se detuvo Desktop con
`docker desktop stop --force --timeout 20` y se comprobaron los dos directorios
de ejecución. Se verificaron sus rutas absolutas y los destinos de respaldo
antes de actuar.

Se renombraron de forma atómica con `Rename-Item`, dentro de sus respectivos
padres, a respaldos con sufijo `.wrenchai-backup-20261025-121330`. Antes de
recrear cada directorio se comprobó que el origen había desaparecido; antes de
iniciar Desktop se comprobaron los directorios vacíos. Un intento anterior con
`Move-Item` había conservado el origen del directorio de Secrets Engine, por lo
que no bastaba con asumir que la operación había limpiado la ruta de ejecución.
Los respaldos de esos intentos también se conservaron.

Engine 29.6.2 volvió a responder; PostgreSQL quedó healthy y los tres servicios
de WrenchAI recuperaron funcionamiento. Se comprobaron los volúmenes
`wrenchai_postgres_data`, `n8n_data` y `trivy-cache`, sin inspeccionar ni modificar
datos de otras aplicaciones. La auditoría posterior confirmó que los datos y
modificaciones del vehículo original se conservaron. No se usó Reset to factory
defaults ni se eliminaron volúmenes.

La primera ejecución de pruebas falló por conexión a PostgreSQL durante este
incidente. Tras recuperar Docker se repitió la suite con éxito. El fixture de
pruebas limita ahora a cinco segundos la conexión administrativa a PostgreSQL,
para que una indisponibilidad no demore minutos antes de informar el problema.
