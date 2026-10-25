# Referencias de figuras y procedimientos ilustrados

Corrección del 25 de octubre de 2026 para dos errores observados en el chat:
`Unknown illustration ID` y omisión del dibujo al preguntar «como tenso la
correa?», pese a recuperar el procedimiento correcto de PDF 59.

## Cambios

El esquema enviado a Gemini ahora enumera los identificadores de las figuras
**realmente adjuntadas en esa petición**, usando `enum` en `figure_id`. Cuando
no hay figuras disponibles, se elimina la alternativa de ilustración del
esquema. Los IDs que consideró la búsqueda pero que no llegaron a adjuntarse no
se exponen como opciones de salida en el contexto del proveedor. Los IDs de
páginas, secciones o figuras de respuestas anteriores nunca se convierten en
una figura válida por semejanza.

Gemini admite enums en su esquema de salida; la validación local sigue siendo
necesaria para comprobar el significado y las relaciones de los valores.
Referencia: [documentación oficial de salidas estructuradas](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).

Si una respuesta contiene un error de esquema o referencias, se vuelve a
generar **una sola vez**, con las mismas fuentes, imágenes y restricciones. No
se acepta la referencia original, no se adivina un ID sustituto y no se descarta
silenciosamente una imagen inválida. Ambas generaciones comparten el presupuesto
de 60 segundos del proveedor; si quedan menos de cinco segundos no se inicia la
corrección. Los errores de red, credenciales o cuota no disparan esta reparación.
Un fallo persistente de ilustración devuelve un aviso específico y conserva el
mensaje del usuario para reintentar.

El filtro de imágenes distinguía dibujos mediante coincidencias con su leyenda.
Cuando un tema tenía varios dibujos con leyendas como «Fig. II.60» y «Fig. II.61»,
ninguno coincidía con las palabras de la pregunta y se excluían todos. Ahora
esas figuras numeradas conservan su asociación con el tema y se ofrecen para
lectura visual. El epígrafe usa el título del tema, conservando por separado el
OCR original sin corregir por inferencia «11» a «II» ni otras cifras.

En «Ajuste de la correa dentada», esto recupera el accionamiento de la polea
tensora de PDF 59 y la comprobación por torsión de PDF 60. La figura superior de
PDF 59 pertenece al tema previo y continúa excluida. Se mantienen los límites
por sección, componente, eje y hashes de los recortes originales.

Para una explicación de procedimiento que cita un tema con dibujos disponibles,
se solicita una ilustración pertinente aunque el usuario no la pida. Si la
generación omite todas las figuras, se activa la corrección acotada. Las
respuestas de falta de cobertura o aclaración no están obligadas a mostrar
imágenes. Una omisión persistente de un procedimiento ilustrado también se
rechaza; no se fuerza un dibujo arbitrario para ocultar la incertidumbre.

## Evidencia

- Ocho pruebas nuevas cubren enums, opciones sin imágenes, referencias
  inventadas, límite de una corrección, omisión de figuras, aclaraciones,
  presupuesto de tiempo y varios dibujos numerados dentro del mismo tema.
- Suite completa: **114 pruebas correctas**. Ruff y `git diff --check` se
  ejecutaron sobre los cambios. La interfaz conserva su contrato anterior.
- Tres consultas reales declaradas en `figure-reliability-cases-v1.json`:
  las tres respondieron HTTP 200 con la figura
  `gol-repair-candidate-0059-region-001`. Una también incluyó el dibujo de
  comprobación de PDF 60. Tiempos: 6,38–8,72 segundos; hashes comprobados.
- Las cuatro consultas del bloque de frenos también respondieron HTTP 200 y
  pasaron sus comprobaciones: cilindro trasero (dos formulaciones), servofreno y
  mordaza. Mantienen las figuras VI.16, VI.17 y VI.15 respectivamente, sin mezcla.
- Se verificó en el navegador el resultado persistido de la pregunta literal,
  el dibujo correcto de la polea tensora y el enlace a PDF 59. Captura privada:
  `data/private/manuals/ui-belt-illustration-fixed.png`.
- Se ejecutaron los doce casos anteriores: todos respondieron HTTP 200 y once
  pasaron todas sus comprobaciones automáticas. El caso del PIN Bluetooth
  se abstuvo de inventar un PIN, pero citó innecesariamente el autoradio
  original, por lo que falló el criterio de ausencia de citas. Se conserva como
  pendiente de fidelidad; esta entrega no afirma haber resuelto esa selección de
  fuentes ni haber medido precisión general.

Se comprobaron por HTTP la persistencia de las diecinueve respuestas y los
hashes de todas las imágenes seleccionadas. Los dieciocho casos con criterios
completos correctos no convierten estos ensayos en una evaluación independiente.

Registros privados: `figure-reliability-live-v1.json`,
`figure-reliability-regression-v1.json` y `figure-reliability-brakes-v1.json`.
Las pruebas reales usan vehículos sintéticos separados del vehículo original.
Los casos conocidos son regresión/calibración, no evaluación independiente ni
certificación mecánica del contenido. Los bundles de páginas, figuras,
secciones y vectores conservan sus versiones; basta reconstruir el servicio API
para desplegar esta corrección. Las respuestas guardadas anteriormente no se
reescriben.
