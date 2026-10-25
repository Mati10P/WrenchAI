# WrenchAI

La biblioteca local permite consultar **532 páginas de dos manuales completos**, mediante búsqueda de páginas y lectura visual de Gemini. Incorpora [búsqueda híbrida con pgvector](docs/VECTOR_RETRIEVAL.md), que combina significado y palabras clave. Conserva aparte cinco fragmentos revisados; el OCR restante no se presenta como evidencia validada. Instalación, estado y límites: [biblioteca completa](docs/FULL_MANUAL_LIBRARY.md).

Proyecto de portfolio para conseguir una primera experiencia laboral: una aplicación de mantenimiento mecánico con persistencia, diagnóstico asistido por IA y fuentes documentales verificables.

## Estado actual

La pantalla principal es un chat por problema. Al escribir, se guarda la conversación y se registra un pendiente en PostgreSQL. El menú **Mi auto** reúne marca, modelo, año, kilometraje, modificaciones y un **To-do** con pendientes, trabajos realizados y costos. Gemini usa el contexto del auto y conserva las respuestas; el chat permite elegir modelo. Requiere una clave en el servidor y ya se registraron pruebas reales de generación. La evaluación mecánica completa sigue pendiente. Hay cinco fragmentos reales de los manuales habilitados mediante recuperación textual, con citas y referencia del Gol de fábrica. Gemini conserva el contexto de modificaciones. Falta búsqueda semántica con pgvector y búsqueda web. El avance verificado y los pendientes están en la [checklist del plan](IMPLEMENTATION_PLAN.md).

El prototipo de consola `maintenance_demo.py` se conserva como antecedente educativo con SQLite. Sus datos no se migran automáticamente a la API.

## Probar la aplicación

Con Docker Desktop funcionando, desde la raíz del repositorio:

```powershell
docker compose up --build -d
```

Abrí [WrenchAI en tu navegador](http://localhost:5173), completá lo que conozcas en **Mi auto** y escribí el problema. Los mensajes siguientes continúan el mismo caso; **Nuevo chat** inicia otro. Los pendientes y trabajos se consultan desde el menú, sin formularios de avería para empezar. El aviso junto al cuadro de texto muestra si falta configurar Gemini o evidencia documental. Configuración y límites en [docs/ASSISTANT.md](docs/ASSISTANT.md).

Uso, desarrollo y verificación de la interfaz en [docs/FRONTEND.md](docs/FRONTEND.md). La pantalla técnica de la API sigue en `http://localhost:8000/docs`; su contrato, pruebas y decisiones están en [docs/BACKEND.md](docs/BACKEND.md). La falta de datos de variante no bloquea el registro del trabajo mecánico. Las especificaciones documentales siguen requiriendo evidencia compatible.

## MVP acordado

La entrega actual habilita cinco fragmentos revisados de los manuales y usa el Gol original de fábrica como referencia de búsqueda. Gemini responderá con esas fuentes y luego contextualizará las modificaciones registradas, distinguiendo el contenido del manual de su interpretación. Los datos reales del auto se conservan. Primero se demostrará este circuito con citas reales y aviso de falta de cobertura; después se ampliarán los manuales y se incorporará búsqueda vectorial. El circuito ya se comprobó con Gemini real por HTTP; el recorrido visual está pendiente. Ver [cobertura y pruebas del lote](docs/MVP_REAL_CORPUS.md).

- Crear y editar vehículos e incidencias con síntomas y mediciones.
- Estados OPEN, IN_PROGRESS y RESOLVED, con registro de la solución aplicada.
- Diagnóstico estructurado mediante Gemini, con hipótesis, evidencia, pruebas sugeridas, advertencias e información faltante.
- RAG con PostgreSQL y pgvector, citas verificadas y documentación compatible con el vehículo.
- Historial persistente de incidencias y diagnósticos.
- Reglas determinísticas de seguridad que el modelo no puede reducir.
- Evaluación reproducible sobre 20 casos, separando tests simulados de pruebas con Gemini real.

El chat es la entrada principal y conserva el contexto del auto. Antes de generar una respuesta, recupera fragmentos aprobados y compatibles desde PostgreSQL mediante búsqueda textual. Falta habilitar los manuales reales, incorporar recuperación semántica y completar la búsqueda en internet cuando la evidencia resulte insuficiente, mostrando origen y límites. Se usa recuperación documental (RAG), no entrenamiento de un modelo con los PDF. La ingesta documental ya funciona como comando administrativo.

## Stack previsto

React + TypeScript + Vite; Python + FastAPI + Pydantic + SQLAlchemy + Alembic; PostgreSQL + pgvector; Gemini; Pytest + Docker Compose + GitHub Actions.

SQLite pertenece únicamente al prototipo anterior. No se migrarán automáticamente sus datos personales.

## Documentación técnica

Se descargaron dos manuales candidatos y se procesaron sus 532 páginas con OCR y separación por regiones. Para la primera versión se usará un conjunto acotado de páginas bien revisadas, seleccionado según los casos del MVP. La revisión profunda de ambos manuales completos queda pendiente para una etapa posterior; no es un requisito para comenzar la aplicación.

Cada página seleccionada deberá tener texto, cifras, unidades, tablas, ilustraciones y aplicabilidad cotejados, con trazabilidad al original y dudas registradas. Todavía no hay páginas habilitadas como evidencia para RAG. El contenido pendiente o dudoso no respaldará respuestas técnicas. Los manuales privados permanecerán fuera de Git; las pruebas públicas usarán un corpus didáctico redistribuible. Ver [criterios del corpus inicial](docs/MVP_CORPUS.md).

La selección inicial comprende 22 páginas y [20 escenarios concretos](docs/MVP_CASES.md) de lubricación, refrigeración, frenos, carga y límites de evidencia. Son alcance y criterios de aceptación documentados; su revisión técnica y evaluación real siguen pendientes.

Las respuestas son hipótesis, no diagnósticos confirmados. La ausencia de evidencia se mostrará explícitamente. Las reglas no certifican la seguridad mecánica del vehículo.

## Fuera de alcance

Fotos, análisis visual, conversación ajena al mantenimiento del auto, OCR dentro de la aplicación, multiusuario, pagos, OBD-II, entrenamiento de modelos y sistemas multiagente. El chat de mantenimiento y la búsqueda web complementaria pasan a formar parte del alcance por decisión del propietario.

## Entrega y etapas

1. Preparar el conjunto inicial de páginas revisadas, convenciones y decisiones de arquitectura.
2. Implementar API, migraciones y persistencia.
3. Integrar ingesta, RAG, Gemini y seguridad.
4. Construir la interfaz y el flujo de resolución.
5. Completar evaluaciones, CI, README, capturas y guion de demostración.

La aplicación completa se ejecutará localmente con Docker. GitHub Pages mostrará una demo de lectura con casos exportados y resultados guardados identificados como tales, sin claves ni llamadas a IA. Solo se publicará material redistribuible y sin datos privados.

El objetivo orientativo de 3–5 días de construcción excluye la limpieza completa del manual y el tiempo de aprendizaje y revisión.

## Ejecutar el prototipo anterior

Requiere Python 3.11. Desde la raíz del repositorio, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe maintenance_demo.py
```

Solicita fecha YYYY-MM-DD, kilometraje entero no negativo y descripción no vacía. Cada ejecución válida agrega un registro a `data/private/demo.db`, excluido de Git. Las entradas inválidas terminan con ValueError. Estos comandos ejecutan solo el prototipo.

## Forma de trabajo

Implementación por bloques explicados, con verificaciones y documentación. El propietario realiza manualmente todos los commits y pushes. No publicar secretos, datos personales ni manuales sin permiso de distribución.

## Seguimiento documental

La búsqueda inicial, candidatos y límites de compatibilidad están registrados en [docs/MANUAL_SOURCES.md](docs/MANUAL_SOURCES.md). Ambos candidatos privados tienen OCR; su revisión técnica sigue en curso. Ver [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) para el avance y [AGENTS.md](AGENTS.md) para las convenciones.

### Preparación del corpus

El OCR y su revisión se ejecutan con herramientas locales documentadas en [docs/OCR_WORKFLOW.md](docs/OCR_WORKFLOW.md). El análisis por regiones separa borradores de texto, figuras y tablas, conservando los originales. La preparación técnica del corpus sigue en curso y todavía no se considera evidencia validada para RAG.

### Ingesta y consulta documental sin Gemini

Ya se puede importar un conjunto aprobado y consultar sus fuentes desde PostgreSQL sin clave de IA. Incluye un ejemplo didáctico propio, aislado por modelo de vehículo ficticio. Es recuperación textual; la búsqueda semántica con pgvector y la habilitación de los manuales reales continúan pendientes. Instrucciones en [docs/RAG.md](docs/RAG.md).
