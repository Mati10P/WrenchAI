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

El adaptador provisional carga una lista JSON desde APPROVED_CORPUS_PATH. Cada entrada exige id, title, page (página PDF desde 1), text, approved=true, approved_by, review_reference, source_sha256 y requirements. Los requisitos admiten make, model, year, fuel, engine_code y market; al menos uno es obligatorio y todos deben coincidir con datos conocidos del vehículo. La aprobación debe ser una decisión documental real, no un cambio de bandera para habilitar OCR.

La huella valida formato, no coteja automáticamente el PDF original. El responsable debe verificar contenido, procedencia y aplicabilidad antes de publicar el archivo. Se rechaza el corpus inválido; no se utiliza parcialmente. Máximo 200 fragmentos y 2 MB. Recuperación provisional por coincidencia de palabras, hasta cuatro fragmentos: **todavía no es búsqueda semántica con pgvector**. La respuesta solo puede citar IDs recuperados; esto no demuestra por sí solo que cada afirmación esté respaldada.

Para desarrollo local se puede exportar APPROVED_CORPUS_PATH al proceso de la API. Compose no monta documentos privados por defecto: habilitarlo requiere un override local con volumen de solo lectura y esa variable apuntando al archivo dentro del contenedor. No copiar manuales ni secretos a la imagen. No se incluye un corpus ficticio como evidencia de producción; los tests sí usan fragmentos sintéticos.

## Errores, concurrencia y límites

GET /assistant/status informa presencia de clave, validez/cantidad del corpus y ausencia de búsqueda web. POST /messages/{id}/reply devuelve una respuesta existente o genera para el último mensaje. GET /incidents/{id}/replies permite recuperar respuestas paginadas.

Un bloqueo de la incidencia evita llamadas concurrentes para el mismo caso; otra solicitud recibe 409. Cada mensaje tiene como máximo una respuesta persistida. No hay reintentos automáticos de llamadas pagas: el usuario decide reintentar. Un fallo después de recibir al proveedor pero antes de guardar podría requerir otra llamada; no se promete facturación exactamente una vez. El transporte tiene timeout de 25 segundos y limita el tamaño leído. Contextos mayores de 80.000 caracteres se rechazan explícitamente.

Cuatro reglas detectan algunas expresiones de riesgo de frenos, combustible, presión de aceite y temperatura. Producen una advertencia fija, identificada como regla, sin llamar al modelo ni necesitar clave. Son heurísticas conservadoras: pueden detectar una negación como riesgo, conservar un aviso por el historial o no detectar otras expresiones. No certifican seguridad, no cubren todos los riesgos y no sustituyen las evaluaciones mecánicas de los 20 casos. Las instrucciones al modelo tampoco garantizan obediencia perfecta.

## Verificación

35 pruebas automatizadas pasaron contra PostgreSQL temporal, incluyendo migración 0005, persistencia, contexto, reintentos, bloqueo concurrente, errores del proveedor, citas desconocidas y exclusión de fragmentos incompatibles. El proveedor está simulado: no se ejecutaron llamadas reales a Gemini. Compilación TypeScript/Vite verificada. Quedan pendientes la clave, prueba real, aceptación documental, pgvector, búsqueda web y evaluación completa de los 20 escenarios.

Verificación local adicional: Docker reconstruyó e inició API y frontend conservando PostgreSQL. GET /assistant/status devolvió configured=false, approved_passages=0 y web_search=false, coherente con la configuración pendiente. Pasaron Ruff, formato del frontend y git diff --check. La revisión visual de este bloque no pudo completarse porque el navegador está deshabilitado en Work; no se presenta como realizada.
