# Incidente local de Docker Desktop - 2026-10-23

Al iniciar Docker para probar PostgreSQL, Desktop falló antes de levantar el motor. El registro apuntaba a `initializing Inference manager` y a un archivo `dockerInference` que Windows no permitía eliminar. La inspección local mostró un punto de reanálisis en el directorio temporal de ejecución. Coincide con el [incidente reportado en Docker Desktop](https://github.com/docker/desktop-feedback/issues/554).

Con Desktop detenido y sin procesos de backend, se conservaron las carpetas de ejecución `Docker/run` y `docker-secrets-engine` bajo nombres con sufijo `.wrenchai-backup-20261023-132700`, dentro de sus directorios originales de datos locales del usuario. Se recrearon las carpetas vacías y se inició Docker normalmente. No se eliminaron sockets individualmente ni se usó restablecimiento de fábrica, limpieza de volúmenes o desregistro de WSL.

`docker info` volvió a responder con Engine 29.6.2. Se comprobó que seguían visibles el contenedor `n8n` y los volúmenes existentes `n8n_data` y `trivy-cache`. No se arrancó n8n ni se inspeccionó su contenido. Las carpetas de respaldo se conservaron; no forman parte del repositorio.

Esta reparación corresponde al error observado, no es un paso rutinario de instalación de WrenchAI. No automatizarla al iniciar la aplicación ni aplicarla ante cualquier fallo de Docker. No se cambiaron opciones del Model Runner ni se enviaron diagnósticos a terceros.
