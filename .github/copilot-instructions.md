# Instrucciones para Copilot (revisión de código)

Responde en español y señala solo fallos reales. La guía completa está en `.gemini/styleguide.md` y en la sección
«Review guidelines» de `AGENTS.md`; las prioridades son:

1. Un solo libro defectuoso no puede tumbar la carga nocturna: va a cuarentena y el resto se publica.
2. Toda regla de datos de la CI de la PR tiene su contrato previo `tests/test_*_smoke.py` que nombra los ids.
3. Las rutas cambiadas salen de `scripts/git_estado.py`, nunca cortando `git status --porcelain`.
4. Horas nocturnas en `Europe/Madrid`; el punto de control `automation/reading-datos-*` no se borra antes de publicar.
5. Arreglos por clase de fallo, no para un libro o fecha concretos.
