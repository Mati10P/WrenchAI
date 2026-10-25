# WrenchAI

La biblioteca local permite consultar **532 páginas de dos manuales completos**, mediante búsqueda de páginas y lectura visual de Gemini. Incorpora [búsqueda híbrida con pgvector](docs/VECTOR_RETRIEVAL.md), [recuperación por temas con figuras correspondientes](docs/SECTION_RETRIEVAL.md) y [respuestas con ilustraciones intercaladas](docs/ILLUSTRATED_ANSWERS.md), con acceso a la página original. Conserva aparte cinco fragmentos revisados; el OCR restante no se presenta como evidencia validada. Instalación, estado y límites: [biblioteca completa](docs/FULL_MANUAL_LIBRARY.md).

Proyecto de portfolio para conseguir una primera experiencia laboral: una aplicación de mantenimiento mecánico con persistencia, diagnóstico asistido por IA y fuentes documentales verificables.

## Estado actual

La pantalla principal es un chat por problema. Al escribir, se guarda la conversación y se registra un pendiente en PostgreSQL. **Mi auto** reúne los datos del vehículo, modificaciones, trabajos y costos. Gemini responde con citas y figuras de los manuales, usando el Gol original como referencia documental y considerando las modificaciones pertinentes. La recuperación combina BM25, pgvector y secciones del manual; conserva el tema en preguntas de seguimiento y pide aclaración si la referencia es ambigua. Ver [contexto conversacional y límites de equipos instalados](docs/CONVERSATION_RETRIEVAL.md).

Se ejecutaron los veinte escenarios y dos comparaciones: la revisión encontró 11 casos que cumplen, 5 parciales y 4 fallidos. La CI está preparada y verificada localmente en Linux con 208 pruebas backend, 30 de herramientas y build/formato frontend; su primera ejecución remota queda pendiente del push. Ver [resultados y límites de la evaluación](docs/MVP_EVALUATION.md). La prioridad es corregir esos fallos; revisión mecánica profesional, búsqueda web y demo siguen pendientes. El avance está en la [checklist del plan](IMPLEMENTATION_PLAN.md).

El prototipo de consola `maintenance_demo.py` se conserva como antecedente educativo con SQLite. Sus datos no se migran automáticamente a la API.

## Probar la aplicación

Con Docker Desktop funcionando, desde la raíz del repositorio:

```powershell
docker compose up --build -d
```

Abrí [WrenchAI en tu navegador](http://localhost:5173), completá lo que conozcas en **Mi auto** y escribí el problema. Los mensajes siguientes continúan el mismo caso; **Nuevo chat** inicia otro. Los pendientes y trabajos se consultan desde el menú, sin formularios de avería para empezar. El aviso junto al cuadro de texto muestra si falta configurar Gemini o evidencia documental. Configuración y límites en [docs/ASSISTANT.md](docs/ASSISTANT.md).

Uso, desarrollo y verificación de la interfaz en [docs/FRONTEND.md](docs/FRONTEND.md). La pantalla técnica de la API sigue en `http://localhost:8000/docs`; su contrato, pruebas y decisiones están en [docs/BACKEND.md](docs/BACKEND.md). La falta de datos de variante no bloquea el registro del trabajo mecánico. Las especificaciones documentales siguen requiriendo evidencia compatible.

## MVP acordado

El circuito inicial con cinco fragmentos revisados se amplió a los dos manuales completos: 532 páginas disponibles para lectura visual automática, con fuentes y acceso a los originales. Las modificaciones reales del auto se conservan y se mencionan cuando afectan la consulta. Disponer de los PDF completos no equivale a validar todas sus cifras, procedimientos o variantes. El lote inicial y sus pruebas quedan registrados en [MVP_REAL_CORPUS.md](docs/MVP_REAL_CORPUS.md).

- Crear y editar vehículos e incidencias con síntomas y mediciones.
- Estados OPEN, IN_PROGRESS y RESOLVED, con registro de la solución aplicada.
- Diagnóstico estructurado mediante Gemini, con hipótesis, evidencia, pruebas sugeridas, advertencias e información faltante.
- RAG con PostgreSQL y pgvector, citas verificadas y documentación compatible con el vehículo.
- Historial persistente de incidencias y diagnósticos.
- Reglas determinísticas de seguridad que el modelo no puede reducir.
- Evaluación reproducible sobre 20 casos, separando tests simulados de pruebas con Gemini real.

El chat recupera pasajes revisados de PostgreSQL y secciones de las páginas originales. El OCR se usa para navegación; las imágenes son la evidencia de lectura automática. La búsqueda híbrida con pgvector ya funciona. La búsqueda web complementaria sigue pendiente. Se usa recuperación documental (RAG), sin entrenar un modelo con los PDF.

## Stack previsto

React + TypeScript + Vite; Python + FastAPI + Pydantic + SQLAlchemy + Alembic; PostgreSQL + pgvector; Gemini; Pytest + Docker Compose + GitHub Actions.

SQLite pertenece únicamente al prototipo anterior. No se migrarán automáticamente sus datos personales.

## Documentación técnica

Se procesaron los dos manuales privados con OCR y separación por regiones. Hay cinco pasajes revisados habilitados y una biblioteca completa para lectura visual automática. El resto del OCR mantiene el estado de navegación sin revisión técnica. Los originales, páginas, cifras y unidades se conservan; las dudas y variantes no se completan por inferencia.

Los manuales privados permanecen fuera de Git. Las pruebas públicas usan datos sintéticos redistribuibles. La revisión profunda del contenido y su aplicabilidad sigue pendiente. Ver [criterios del corpus inicial](docs/MVP_CORPUS.md) y [biblioteca completa](docs/FULL_MANUAL_LIBRARY.md).

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

Se puede importar un conjunto aprobado y consultar sus fuentes desde PostgreSQL sin clave de IA. Incluye un ejemplo didáctico propio, aislado por vehículo ficticio. La biblioteca real y la recuperación híbrida se configuran por separado; generar respuestas con lectura visual requiere Gemini. Instrucciones en [RAG.md](docs/RAG.md), [FULL_MANUAL_LIBRARY.md](docs/FULL_MANUAL_LIBRARY.md) y [VECTOR_RETRIEVAL.md](docs/VECTOR_RETRIEVAL.md).

### Procedimientos ilustrados y seguimientos

El filtro de combustible conserva las tres figuras y sus explicaciones en orden documental. Los seguimientos mantienen componente e intención; las respuestas explicitan los datos que no pueden verificarse. Instalación, pruebas y límites en [COMPLETE_PROCEDURES.md](docs/COMPLETE_PROCEDURES.md). La validación completa de secuencias está habilitada para los procedimientos revisados, actualmente el filtro; no implica que todo el manual esté validado.
