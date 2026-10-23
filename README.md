# WrenchAI

Proyecto de portfolio para conseguir una primera experiencia laboral: una aplicación de mantenimiento mecánico con persistencia, diagnóstico asistido por IA y fuentes documentales verificables.

## Estado actual

Existe un prototipo de consola en `maintenance_demo.py`: valida fecha, kilometraje y descripción y guarda mantenimiento en SQLite. Se conserva como antecedente educativo. La aplicación web, PostgreSQL, RAG y Gemini todavía no están implementados.

## MVP acordado

- Crear y editar vehículos e incidencias con síntomas y mediciones.
- Estados OPEN, IN_PROGRESS y RESOLVED, con registro de la solución aplicada.
- Diagnóstico estructurado mediante Gemini, con hipótesis, evidencia, pruebas sugeridas, advertencias e información faltante.
- RAG con PostgreSQL y pgvector, citas verificadas y documentación compatible con el vehículo.
- Historial persistente de incidencias y diagnósticos.
- Reglas determinísticas de seguridad que el modelo no puede reducir.
- Evaluación reproducible sobre 20 casos, separando tests simulados de pruebas con Gemini real.

Tres áreas de interfaz: vehículos/incidencias, detalle de incidencia y consulta de documentación. La ingesta documental será un comando administrativo.

## Stack previsto

React + TypeScript + Vite; Python + FastAPI + Pydantic + SQLAlchemy + Alembic; PostgreSQL + pgvector; Gemini; Pytest + Docker Compose + GitHub Actions.

SQLite pertenece únicamente al prototipo anterior. No se migrarán automáticamente sus datos personales.

## Documentación técnica

El manual original aún debe aportarse. Se preparará completo conservando páginas, secciones, unidades y trazabilidad. El contenido dudoso no respaldará respuestas técnicas. Los manuales privados permanecerán fuera de Git; las pruebas públicas usarán un corpus didáctico redistribuible.

Las respuestas son hipótesis, no diagnósticos confirmados. La ausencia de evidencia se mostrará explícitamente. Las reglas no certifican la seguridad mecánica del vehículo.

## Fuera de alcance

Fotos, análisis visual, chat abierto, búsqueda web automática, OCR dentro de la aplicación, multiusuario, pagos, OBD-II, entrenamiento de modelos y sistemas multiagente.

## Entrega y etapas

1. Preparar el manual, convenciones y decisiones de arquitectura.
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

La búsqueda inicial, candidatos y límites de compatibilidad están registrados en [docs/MANUAL_SOURCES.md](docs/MANUAL_SOURCES.md). Se descargaron dos candidatos privados; ambos requieren OCR y revisión. Ver [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) para el avance y [AGENTS.md](AGENTS.md) para las convenciones.

### Preparación del corpus

El OCR y su revisión se ejecutan con herramientas locales documentadas en [docs/OCR_WORKFLOW.md](docs/OCR_WORKFLOW.md). El análisis por regiones separa borradores de texto, figuras y tablas, conservando los originales. La preparación técnica del corpus sigue en curso y todavía no se considera evidencia validada para RAG.
