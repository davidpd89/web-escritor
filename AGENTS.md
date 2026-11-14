# Preferencias de trabajo

- Trabajar por tareas concretas y completar las comprobaciones necesarias; evitar auditorías, relecturas y relanzamientos duplicados sin cambios ni motivos nuevos.
- Al terminar cada tarea, cerrar los procesos temporales locales creados por el agente que ya no sean necesarios. Conservar los servicios del usuario y las ejecuciones remotas autorizadas, indicando qué sigue activo.
- Guardar un informe breve de continuidad en `.ci/` con fecha, cambios, verificaciones, fallos, pendientes y enlaces relevantes. No incluir secretos.
- Terminar con un resumen conciso, el enlace al informe y un prompt breve para continuar en un chat nuevo sin copiar el historial completo.
- Distinguir siempre lo comprobado de lo pendiente; una ejecución lanzada no equivale a una prueba aprobada.
- Preferir scripts y resultados resumidos para trabajo repetitivo. Mostrar solo los registros necesarios para diagnosticar fallos.

## Review guidelines

- Cambios en la carga nocturna de libros (`scripts/refresh-reading-catalogue.py`, `scripts/reading_*`,
  `scripts/materializar*`, `scripts/git_estado.py`, `scripts/check-reading-data.py`,
  `.github/workflows/reading-*`): tratar como P1 cualquier camino en el que un solo libro defectuoso tumbe el
  lote entero, se pierda el punto de control `automation/reading-datos-*` o se publique dos veces.
- Toda comprobación de datos que corra en la CI de la PR debe tener su contrato previo a la PR
  (`tests/test_*_smoke.py`) que nombre los ids de los libros afectados. Señalar las que falten.
- Preferir correcciones por clase de fallo; señalar parches para un libro o una fecha concretos.
- Señalar lecturas de logs o textos de error como mecanismo de control: son frágiles.
- Seguir la skill `.claude/skills/revisar-carga/SKILL.md` antes de fusionar.
