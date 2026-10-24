# Aceptación documental y prioridad del MVP

## Estado de aceptación — 2026-10-24

La [matriz por fragmento](MVP_ACCEPTANCE_MATRIX.md) cubre los 22 pasajes y delimita candidatos, identificación, contexto y exclusiones. Se verificó nuevamente la integridad de toda su evidencia. El propietario confirmó el registro objetivo y aclaró que los otros eran pruebas. Sus modificaciones se conservan en el registro privado de aceptación; una modificación del instrumental impide asumir correspondencia con el tablero original del manual. Sigue pendiente resolver aplicabilidad; no se habilitó ningún fragmento. Las citas de varias páginas ya están implementadas según `RAG.md`. El contrato de ingesta todavía no representa condiciones de tablero/montaje, que deben resolverse antes de aceptar contenido dependiente de ellas.

Ya existe material didáctico redistribuible en `backend/examples/rag`, limitado al vehículo ficticio RAG-DEMO. Falta ampliarlo para los 20 escenarios; el párrafo histórico sobre su ausencia describe el estado anterior a la ingesta documental.

## Decisión del propietario - 2026-10-23

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
