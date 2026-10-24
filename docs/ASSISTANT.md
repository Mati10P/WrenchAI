# Asistente: integración preparada

## Activar Gemini después

El propietario decidió configurar la clave más adelante. Agregar en `.env` de la raíz (excluido de Git):

```dotenv
GEMINI_API_KEY=tu_clave
GEMINI_MODEL=gemini-3.8-flash
```

No colocar claves en React, capturas ni commits. Aplicar desde la raíz:

```powershell
docker compose up -d --force-recreate api frontend
```

Abrir un chat y enviar un problema. Si el mensaje ya quedó guardado, usar **Generar respuesta**. El estado «configurado» comprueba presencia de clave, no permisos, cuota ni conectividad. La primera respuesta real sigue pendiente de validación.

Se usa generateContent por REST, clave en cabecera y salida JSON validada con Pydantic. Referencias: [salida estructurada](https://ai.google.dev/gemini-api/docs/generate-content/structured-output?hl=en) y [modelo](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash). El modelo es configurable.

## Qué hace este bloque

- Guarda primero el mensaje y después solicita la respuesta. Una falla de Gemini no pierde la conversación.
- Envía marca, modelo, año, combustible, motor, mercado, kilometraje, modificaciones y notas disponibles; problema original, últimos 20 mensajes con respuestas y últimas 12 tareas de ese auto. No inventa campos desconocidos.
- Guarda respuesta estructurada, modelo, fuentes citadas y copia del contexto utilizado. La copia queda en PostgreSQL y no se expone en la respuesta pública del endpoint.
- Muestra hipótesis, preguntas y observaciones sugeridas. No modifica automáticamente kilometraje, datos del auto ni checks del To-do.
- Sin fuentes compatibles, identifica la orientación como general. No tiene búsqueda web.

Al habilitar Gemini, ese contexto se envía a Google. No se envían PDF completos ni costos. Usar datos sintéticos para demos públicas. No publicar la base local.

## Evidencia documental

No hay fragmentos reales aprobados habilitados. Los dos manuales completos siguen pendientes de revisión profunda; para la primera versión se aceptará un subconjunto revisado y compatible, según CORPUS_ACCEPTANCE.md.

La ingesta administrativa valida el contrato de cada fragmento y la huella del original, y persiste el conjunto en PostgreSQL. La recuperación textual filtra requisitos contra datos conocidos del vehículo. El chat ya no lee APPROVED_CORPUS_PATH en cada solicitud. Ver [RAG.md](RAG.md) para el procedimiento actual, el material didáctico y los límites: todavía no hay búsqueda semántica con pgvector ni fragmentos privados habilitados.

## Errores, concurrencia y límites

GET /assistant/status informa presencia de clave, validez/cantidad del corpus y ausencia de búsqueda web. POST /messages/{id}/reply devuelve una respuesta existente o genera para el último mensaje. GET /incidents/{id}/replies permite recuperar respuestas paginadas.

Un bloqueo de la incidencia evita llamadas concurrentes para el mismo caso; otra solicitud recibe 409. Cada mensaje tiene como máximo una respuesta persistida. No hay reintentos automáticos de llamadas pagas: el usuario decide reintentar. Un fallo después de recibir al proveedor pero antes de guardar podría requerir otra llamada; no se promete facturación exactamente una vez. El transporte tiene timeout de 60 segundos y limita el tamaño leído. Contextos mayores de 80.000 caracteres se rechazan explícitamente.

Cuatro reglas detectan algunas expresiones de riesgo de frenos, combustible, presión de aceite y temperatura. Producen una advertencia fija, identificada como regla, sin llamar al modelo ni necesitar clave. Son heurísticas conservadoras: pueden detectar una negación como riesgo, conservar un aviso por el historial o no detectar otras expresiones. No certifican seguridad, no cubren todos los riesgos y no sustituyen las evaluaciones mecánicas de los 20 casos. Las instrucciones al modelo tampoco garantizan obediencia perfecta.

## Verificación

35 pruebas automatizadas pasaron contra PostgreSQL temporal, incluyendo migración 0005, persistencia, contexto, reintentos, bloqueo concurrente, errores del proveedor, citas desconocidas y exclusión de fragmentos incompatibles. El proveedor está simulado: no se ejecutaron llamadas reales a Gemini. Compilación TypeScript/Vite verificada. Quedan pendientes la clave, prueba real, aceptación documental, pgvector, búsqueda web y evaluación completa de los 20 escenarios.

Verificación local adicional: Docker reconstruyó e inició API y frontend conservando PostgreSQL. GET /assistant/status devolvió configured=false, approved_passages=0 y web_search=false, coherente con la configuración pendiente. Pasaron Ruff, formato del frontend y git diff --check. La revisión visual de este bloque no pudo completarse porque el navegador está deshabilitado en Work; no se presenta como realizada.

## Actualización: corpus persistido

La lectura directa de APPROVED_CORPUS_PATH fue sustituida por importación administrativa a PostgreSQL. El importador ahora comprueba los archivos originales contra sus huellas; el chat recupera desde la base. El contrato de fragmento y el requisito de aprobación se conservan. Instrucciones actuales y límites: [RAG.md](RAG.md). No hay corpus privado habilitado ni búsqueda semántica todavía.


## Ajuste por demora real de Gemini

Se comprobó conectividad y acceso al modelo con la clave configurada. Una generación real con el mensaje sintético «hola» tardó 54,23 segundos y produjo JSON válido; el límite anterior de 25 segundos era insuficiente. Se amplía el timeout de transporte a 60 segundos y el proxy a 90. Se distingue timeout (504) de fallo de conexión (502), conservando mensajes y sin reintentos automáticos.

Para gemini-3.8-flash se solicita thinkingLevel=low, opción documentada para reducir latencia: https://ai.google.dev/gemini-api/docs/latest-model. No garantiza un tiempo máximo de respuesta. Pasaron 13 pruebas del adaptador, incluidas las categorías de errores de transporte. La prueba real no valida diagnósticos mecánicos ni el corpus.

Se reintentó el mensaje ya guardado a través del proxy de la aplicación: respuesta HTTP exitosa en 40,01 segundos, con gemini-3.8-flash. La respuesta quedó persistida en la conversación existente. Continúa pendiente mejorar la latencia percibida; no se presenta este resultado como respuesta instantánea.
