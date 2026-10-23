# Plan de implementación

## Preparación documental (en curso)
- [x] Comparar checkout con GitHub y reparar origin/main.
- [x] Buscar fuentes y descargar candidatos fuera de Git.
- [ ] Verificar edición, autoría, cobertura y calidad de cada PDF.
- [ ] Preparar el manual completo, conservando original y correspondencia por página.
- [ ] Revisar tablas, unidades y cifras; marcar incertidumbre sin completarla por inferencia.
- [ ] Crear corpus didáctico redistribuible para pruebas.

## Bloques posteriores
- [ ] A: API, PostgreSQL, migraciones, vehículos, incidencias y mediciones; persistencia tras reinicio.
- [ ] B: ingesta administrativa, Gemini, pgvector, citas y seguridad; diagnóstico real verificable.
- [ ] C: interfaz en español; completar registro, diagnóstico y resolución desde navegador.
- [ ] D: 20 casos, pruebas determinísticas, evaluación real separada y CI.
- [ ] E: exportación de casos para demo de lectura en GitHub Pages, capturas y guion de video.

## Decisiones
- Monolito modular y RAG propio; sin agentes ni frameworks de orquestación.
- Backend local con Docker; demo pública estática sin claves ni llamadas a IA.
- Sin fotos, chat abierto, búsqueda web automática ni OCR dentro del producto.
- La preparación completa del manual es una etapa previa, fuera de los 3–5 días orientativos.
- Los commits y pushes son manuales y corresponden al propietario.
