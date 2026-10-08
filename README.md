# WrenchAI

Asistente de mecánica para mi auto, un Volkswagen Gol G2 1.6 Mi 1998,
motor AP multipunto, dos puertas.

## Objetivo

Consultar documentación y especificaciones, explorar problemas
con texto y fotografías, y registrar mantenimiento.

## Funciones del MVP

- Chat con imagenes  y preguntas de seguimiento.
- Respuestas fundamentadas en manuales y documentación.
- Consulta de torque, threadlocker y como armar, diferenciando 
  especificaciones, recomendaciones y datos desconocidos.
- Búsqueda web en portugués de Brasil cuando falte evidencia local.
- Historial de mantenimiento.
- Clasificación de consultas por intención (torque, procedimiento, 
  síntoma o mantenimiento) y parte del auto (- frenos, motor,
  refrigeración, suspensión, etc.).

## Datos y fuentes

Los manuales compatibles con el vehículo van a respaldar
las especificaciones y procedimientos.

Se van a evaluar datasets de mecanica como fuentes
auxiliares para clasificación y pruebas. Sus soluciones no se
considerarán automáticamente aplicables al auto.

## Límites

Las imagenes ayudan a identificar componentes y describir
observaciones. No permiten confirmar por sí solas todos los
diagnósticos, medidas ni especificaciones.

## Estado

Inicio del proyecto. Todavía no hay funcionalidades implementadas.

## Desarrollo local

Requiere Python 3.11.

Crear el entorno:

```powershell
python -m venv .venv
```

Ejecutar la demo de mantenimiento:

```powershell
.\.venv\Scripts\python.exe maintenance_demo.py
```

El script te pide:
- Fecha del trabajo en formato YYYY-MM-DD.
- Kilometraje entero mayor o igual a cero.
- Descripción del trabajo no vacía.

Valida los datos y guarda el registro en SQLite.
Si una entrada es inválida, muestra un ValueError y termina.
Cada ejecución exitosa agrega un registro a data/private/demo.db.
La base se usa para pruebas y está excluida de git.