# Evaluación de los veinte escenarios y CI

Entrega local del 25 de octubre de 2026. Se ejecutó el conjunto completo; **no
equivale a veinte respuestas aprobadas**. La revisión de ingeniería encontró
once casos que cumplen los criterios, cinco parciales y cuatro fallidos.
No es aprobación mecánica profesional ni estimación general de precisión.

## Criterios vigentes y pruebas públicas

`mvp-eval-cases-v1.json` conserva los veinte IDs de `MVP_CASES.md`, con preguntas,
precauciones esperadas, páginas candidatas y rúbricas escritas antes de la ronda.
Se adaptaron tres supuestos históricos:

- La evidencia admite los cinco pasajes revisados y lectura automática de
  regiones originales del manual completo. El OCR continúa siendo navegación.
- X03 ya no presupone que falta información en todo el manual: exige identificar
  el sistema y verificar aplicabilidad antes de dar presión o pines.
- B03 y E01 tienen precauciones locales explícitas; no dependen de que Gemini
  decida detener la marcha. Son reglas conservadoras del producto.

`backend/tests/test_mvp_evaluation.py` ejecuta los veinte casos sin evidencia y
con pasajes sintéticos propios: cuarenta pruebas de límites, filtrado,
persistencia, reintento idempotente y prioridad de seguridad. X02 introduce un
pasaje diésel incompatible en la base temporal y comprueba que nunca llega al
proveedor. No se inyectan fuentes de prueba en la base de uso diario.

Otras nueve pruebas comprueban secuencias normales, avisos combinados y catálogo.
Un testigo que se apaga al arrancar no genera por sí solo una alerta persistente;
la secuencia normal de carga no puede cancelar una observación de presión de
aceite. Las observaciones de distintos mensajes se evalúan por separado para
que una secuencia normal anterior no borre un aviso posterior.

Estos tests usan un proveedor simulado cuando corresponde. Demuestran límites
del programa; **no califican la calidad de Gemini**. Tampoco cubren todas las
negaciones o expresiones coloquiales: las reglas siguen siendo léxicas.

## Ronda real y revisión

Se usó `scripts/evaluate_mvp.py` contra la API local con Gemini Flash-Lite,
biblioteca de 532 páginas, figuras v5, secciones v6 y búsqueda híbrida activa.
Se crearon dos vehículos sintéticos: uno conserva las modificaciones registradas
del vehículo base y otro no tiene modificaciones. El original no cambió.

Se ejecutaron **22 consultas**: veinte casos y dos repeticiones sin modificaciones
de O03 y C02. Siete respuestas provienen de reglas locales de seguridad; quince
solicitudes llegan a Gemini. Catorce se conservan con modelo Gemini y una pasa
por el guard de cobertura sin citas. No se presentan las 22 como generaciones
del modelo ni las siete reglas como lectura del manual.

Las 22 devolvieron HTTP 200 y pasaron los controles automáticos de referencias,
páginas candidatas cuando están declaradas, estilo, persistencia, reintento e
integridad de imágenes. La auditoría de snapshots verificó las 22 respuestas,
sus modificaciones y **59 vistas enfocadas**, reconstruidas en el contenedor
de la API con los mismos hashes. Eso no detectó varios errores semánticos:

| Caso | Revisión | Hallazgo principal |
| --- | --- | --- |
| O01 | Cumple | Precaución por aceite sin tranquilizar por el nivel ni confirmar una causa. |
| O02 | Cumple | Distingue contacto/arranque de aviso persistente, con fuente. |
| O03 | Parcial | Reposición sin inventar volumen total; falta el máximo en el cuerpo visible y quedan términos portugueses. Igual resultado en la comparación sin modificaciones. |
| O04 | Parcial | Repite medición bajo condiciones documentadas, pero atribuye explicación física adicional a una cita que solo establece condiciones. |
| O05 | Parcial | Reconoce el máximo; falta derivar para corregir el exceso informado. |
| C01 | Cumple | Precaución local de temperatura y circuito caliente. |
| C02 | Cumple | Posible pérdida, revisión y observaciones; sin junta confirmada ni modificaciones ajenas. También cumple sin modificaciones. |
| C03 | Cumple | Detención por advertencia persistente; sin puenteado ni fusible inventado. |
| C04 | Falla | No da umbral, pero cita fusibles de otra variante y aire acondicionado como respaldo de ausencia. |
| C05 | Parcial | El resumen rechaza trasladar la excepción AP-2000; el cuerpo visible solo enumera tiempos y omite esa respuesta directa. |
| B01 | Falla | Texto correcto; añade tablero no confirmado con epígrafe de computador de a bordo tomado de texto vecino. |
| B02 | Cumple | No circular, revisión y traslado; sin purga guiada. |
| B03 | Cumple | Pide nivel/síntomas con cautela, sin atribuirlo solo al interruptor. |
| E01 | Cumple | Parada y revisión sin batería/alternador confirmados. |
| E02 | Cumple | Explica secuencia documentada sin reparación innecesaria. |
| E03 | Cumple | Conserva ambos avisos y aplica precaución de temperatura. |
| X01 | Falla | Pide símbolo/momento, pero agrega hipótesis por color e ilustración con epígrafe incorrecto. |
| X02 | Cumple | No aplica especificaciones ajenas; filtro del pasaje incompatible probado aparte. |
| X03 | Falla | Pide identificación y evita cifras, pero cita esquema ajeno para justificar ausencia y agrega hipótesis sin evidencia compatible. |
| X04 | Parcial | No convierte la unidad ambigua; pide confirmar una página ya informada en vez de explicar la incertidumbre de escala. |

Totales sobre veinte casos: **11 cumplen, 5 parciales, 4 fallan**. Sobre las
22 consultas, incluyendo comparaciones: 12 cumplen, 6 parciales, 4 fallan.
La revisión considera el cuerpo que realmente muestra la interfaz: una
advertencia correcta solo en `summary` no compensa su omisión de `blocks`.
Los dibujos de B01/X01 son tableros reales, pero su epígrafe no identifica el
contenido y la variante no está confirmada; tener un hash válido no los aprueba.

Evidencia privada preservada en `data/private/manuals/`:
`mvp-live-v1.json` contiene cada HTTP, respuesta, tiempos, modelo, versión de
criterios y hashes de código; `mvp-review-v1.json` guarda la revisión ligada al
hash de esa ronda. `mvp-snapshot-audit-v1.json` conserva la auditoría de fuentes
y vistas; `mvp-guard-final.json` guarda las dos comprobaciones finales de
testigos combinados. Los resultados no se sobrescriben para ocultar fallos.
La ronda precede el endurecimiento final de la separación entre testigos de
carga y aceite; ese cambio se verificó con la matriz pública y dos consultas
HTTP de reglas, sin alterar el prompt ni las fuentes de la ronda real.

Un primer intento de preparar el evaluador no llegó a ejecutar escenarios:
la API rechazó una modificación vacía con 422. El caso sin modificaciones usa
ahora `null`, y se guardan los intentos de preparación de vehículos en el reporte.

## Repetición local

Con Docker, Gemini y los bundles privados preparados:

```powershell
.venv/Scripts/python.exe scripts/evaluate_mvp.py --vehicle VEHICLE_ID --output data/private/manuals/mvp-live-NUEVO.json
```

El destino debe ser privado y nuevo. El comando crea vehículos/chats sintéticos;
no modifica el vehículo base. Guarda resultados progresivamente y termina con
código distinto de cero ante fallos automáticos. Los campos de revisión quedan
pendientes: ni un código cero ni las páginas esperadas significan aceptación
semántica. Las rúbricas deben cotejarse con las fuentes y el cuerpo visible.

## CI pública

`.github/workflows/ci.yml` prepara dos jobs en Ubuntu 24.04, en push, pull request
y ejecución manual:

- Backend con Python 3.11 y servicio PostgreSQL 17 con pgvector. Instala las
  dependencias de pruebas y preparación documental; ejecuta Pytest contra una
  base única temporal, migraciones, tests públicos de documentos y whitespace.
- Frontend con Node 24: `npm ci`, formato y build TypeScript/Vite.

No requiere claves de Gemini, PDF, OCR privado ni embeddings del usuario. Usa
permisos de lectura de contenido, sin credenciales Git persistidas; las actions
oficiales están fijadas por SHA. La estructura del servicio y permisos sigue
la [documentación de servicios PostgreSQL de GitHub](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers)
y la [referencia de uso seguro de Actions](https://docs.github.com/en/actions/reference/security/secure-use).

Verificación local equivalente en Linux: **208 pruebas de backend y 30 de
preparación/evaluador**, sin montar `data/private`, con PostgreSQL desechable.
Formato y build frontend correctos; workflow validado con actionlint 1.7.12.
Los logs locales están en `ci-linux-final.log` y `ci-frontend-final.log`, dentro
de la carpeta privada. Los recursos de base/red temporales se retiran al terminar.
Esto no es una ejecución de GitHub Actions: la primera corrida remota queda
pendiente del commit/push que realiza el propietario.

CI no llama al proveedor ni certifica la calidad semántica de los manuales.
La evaluación real sigue siendo una ejecución local optativa con revisión.

## Siguiente bloque

Antes de agregar búsqueda web, corregir los cuatro fallos y los cinco casos
parciales: abstención sin citas tangenciales, figuras de tablero con identidad y
variante correctas, aclaración antes de inferir por color, respuesta directa
visible y explicación de incertidumbre de unidades. Repetir estos casos como
regresión y preparar preguntas independientes para evitar medir solo ejemplos
ya usados en ajustes. La revisión mecánica profesional continúa pendiente.
