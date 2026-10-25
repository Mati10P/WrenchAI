# Aceptación documental y prioridad del MVP

## Actualización funcional — 2026-10-24

Lote v1 habilitado: cinco fragmentos delimitados de los dos manuales, aceptados como referencia de fábrica. Las transcripciones originales mantienen su estado histórico; la aprobación está en un registro privado separado con hashes y offsets. No se aprobaron los manuales completos. Ver [MVP_REAL_CORPUS.md](MVP_REAL_CORPUS.md).

## Estado de aceptación — 2026-10-24

La decisión vigente está en [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md): para el MVP se consultan los manuales con el Gol de fábrica como referencia de trabajo, y Gemini contextualiza las modificaciones reales después de recuperar las fuentes. Las modificaciones, incluido el instrumental, dejan de ser bloqueos de recuperación. No se necesita modelar cada montaje real antes de probar este circuito.

La [matriz por fragmento](MVP_ACCEPTANCE_MATRIX.md) cubre los 22 pasajes cotejados. La aceptación del primer lote verifica fidelidad de transcripción, contexto, páginas y alcance como referencia de fábrica; no certifica la configuración física del auto. Se conservan exclusiones por unidades ambiguas y contenido fuera de alcance. La referencia asumida se mantendrá separada de los datos reales y los requisitos propios de cada fuente. Las citas de varias páginas están implementadas. Sigue pendiente preparar/importar el lote y comprobar respuestas reales con fuentes.

Ya existe material didáctico redistribuible en `backend/examples/rag`, limitado al vehículo ficticio RAG-DEMO. Falta ampliarlo para los 20 escenarios; el párrafo histórico sobre su ausencia describe el estado anterior a la ingesta documental.

## Decisión del propietario - 2026-10-23

Los apartados siguientes son históricos. Sus bloqueos por configuración exacta o modificaciones quedan sustituidos por la decisión vigente de referencia de fábrica; los hallazgos de transcripción y ambigüedad documental se conservan.

El propietario indicó que no conoce los datos de variante solicitados y pidió priorizar usos mecánicos y arreglos. No se deducen combustible, mercado, código de motor, tablero ni aire acondicionado a partir del modelo declarado. El Gol G2 1.6 MI 1998 continúa siendo una referencia declarada del proyecto, no una ficha técnica confirmada.

La primera entrega funcional prioriza registrar una avería, guardar síntomas y mediciones con sus condiciones, seguir su reparación y registrar cómo se resolvió. Los datos del vehículo que no se conocen se admiten como nulos. No se necesita resolver toda la investigación de los manuales para construir ese flujo.

## Decisiones sobre los pasajes cotejados

| Grupo | Decisión actual | Motivo y paso necesario |
| --- | --- | --- |
| Portada de propietario, identificación del motor y portadilla de reparación | Solo identificación documental | No respaldan una hipótesis mecánica. No prueban por sí solas compatibilidad ni edición completa. |
| Contexto visual de tableros 220/240 | Referencia de variante, pendiente | No elegir el tablero por año/modelo sin evidencia. |
| Testigos de los distintos tableros | Pendientes de aplicabilidad y separación por alcance | No mezclar numeración; separar advertencias de instrucciones de correa o fusibles fuera del alcance. |
| Compartimiento del motor y depósitos | Pendientes de aplicabilidad | La leyenda agrupa motores; conservar la discrepancia de referencia de frenos como anotación separada. |
| Varilla, reposición de aceite y refrigerante | Pendientes de aplicabilidad y recorte | Una lectura cotejada no transforma productos, cantidades o proporciones históricas en recomendaciones actuales. Mantener advertencias junto a su contexto. |
| Despieces de refrigeración | Contexto de componentes pendiente de aplicabilidad | No asignar un montaje o aire acondicionado por la apariencia del dibujo. Torques/desmontajes siguen fuera del alcance. |
| Tabla del interruptor térmico | Cotejada, pendiente de aplicabilidad y escala de unidad | No completar “grados” como Celsius, ni elegir umbrales sin montaje/configuración compatibles. |
| Pasaje ambiguo de presión | Excluido de instrucciones | No completar superficie de unidad ni convertir la cifra; conservar como ejemplo de abstención X04. |

No se habilitó ningún fragmento para RAG en este bloque. El registro de cotejo y la evidencia privada permanecen sin cambios. La lista de pasajes revisados tampoco es una lista de aceptación automática: la futura ingesta deberá comprobar aprobación, alcance y correspondencia con los hechos disponibles del vehículo.

## Trabajo mecánico que sí puede implementarse ahora

Se conservan los casos O03, C02, B02 y E01 como recorridos de demostración: observaciones de nivel, pérdida recurrente, incidencia de frenos e incidencia de carga. El registro del trabajo no exige que la aplicación afirme una causa. La resolución será un hecho informado por el usuario o un ejemplo sintético identificado, separado de una hipótesis de IA.

Primero se implementan vehículos, incidencias, síntomas, mediciones, estados y resolución persistente. Después se integrarán consultas documentales y diagnóstico, con abstención cuando falte evidencia. La interfaz y los casos deben centrarse en el problema, lo que se observó, qué se hizo y el resultado. No se agregan procedimientos de desmontaje ni especificaciones no verificadas para aparentar cobertura.

La preparación de material didáctico propio redistribuible continúa pendiente para pruebas y demo públicas. Los manuales y transcripciones privados no se publican. La revisión profunda de los dos manuales completos permanece fuera de la primera versión.
