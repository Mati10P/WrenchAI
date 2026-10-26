# Búsqueda web como complemento del manual

La revisión documental busca primero en el manual. Si identifica información faltante, usa Google Search mediante Gemini para encontrar documentación primaria y URL Context para leer hasta tres páginas. Solo acepta HTTPS en los dominios de fabricantes permitidos en `backend/app/web_evidence.py`, resultados vinculados a grounding y URLs con lectura `URL_RETRIEVAL_STATUS_SUCCESS`. Un enlace escrito por el modelo o un resultado de búsqueda sin lectura no basta.

En consultas de procedimiento, los tramos relevantes del manual aparecen numerados con sus ilustraciones en el orden documental. Cada explicación web se coloca antes del tramo que complementa; las explicaciones generales aparecen al comienzo. Los identificadores de ubicación se validan en el servidor. Cada complemento conserva su propia cita, enlace, fecha de consulta, alcance y huella del resumen. La huella identifica el resumen y su URL, no una copia íntegra de la página.

El paso a paso incluye las acciones documentadas y señala explícitamente lo que falta verificar. La revisión examina herramientas, condiciones, acciones, comprobación final y aplicabilidad. La web aporta explicaciones generales; no valida por sí sola pares, RPM, conexiones, compatibilidad ni ajustes del vehículo. Por eso una respuesta parcial no se convierte automáticamente en completa al encontrar una web. La lectura y el resumen son automáticos, sin certificación mecánica ni comprobación independiente de cada afirmación.

## Configuración y límites

Se necesita `GEMINI_API_KEY`, un modelo compatible con las herramientas y `WEB_SEARCH_ENABLED=true`; Compose y `.env.example` ya habilitan la opción. `VISUAL_EVIDENCE_REVIEW=true` activa el flujo de revisión. Actualmente la búsqueda complementaria se ejecuta en ese flujo cuando hay fuentes con orden de lectura y vacíos detectados; no es un buscador independiente para consultas sin manual recuperado. Desactivar la revisión visual evita este flujo.

La búsqueda pública recibe consultas técnicas y la referencia documental, sin historial ni imágenes del manual. La llamada posterior de lectura recibe además las explicaciones revisadas de los tramos, para decidir dónde ubicar el complemento. Se usa el mismo proveedor Gemini. Puede haber consumo adicional de cuota y latencia dentro del presupuesto de 150 segundos del flujo completo. Sin tiempo, sin resultados válidos o ante error del proveedor, se conserva la evidencia del manual y se explicita el límite. No se inventan fuentes para cubrir el fallo.

## Verificación

`backend/tests/test_evidence_review.py` prueba el circuito con proveedor simulado: búsqueda con grounding, lectura confirmada, inserción junto al paso, citas, conservación de figuras y límites, rechazo de fuentes no verificadas, ubicaciones inexistentes y tipos inválidos, y conservación del manual ante cuota agotada. Las pruebas no demuestran disponibilidad ni calidad de búsqueda real del proveedor.

Referencias del contrato consultadas: [Google Search](https://ai.google.dev/gemini-api/docs/generate-content/google-search) y [URL Context](https://ai.google.dev/gemini-api/docs/url-context).
