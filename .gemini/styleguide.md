# Guía de revisión (web-escritor)

Responde en español. Señala solo fallos reales (P1/P2); nada de estilo ni de gustos.

El objetivo del repositorio es una carga nocturna de libros 100 % autónoma: las APIs dan datos, los scripts los
transforman, la CI los publica. Cada fallo que no se vea en la revisión tumba una noche entera.

Busca sobre todo:

- **Un libro tumba el lote.** Cualquier camino en `scripts/refresh-reading-catalogue.py`, `scripts/reading_*`,
  `scripts/materializar*`, `scripts/git_estado.py`, `scripts/check-reading-data.py` o `.github/workflows/reading-*`
  donde un solo libro defectuoso (ISBN repetido, campo vacío, tilde, portada duplicada, ruta renombrada) haga fallar
  la publicación entera en vez de apartar ese libro a cuarentena.
- **Comprobaciones solo en la CI de la PR.** Toda regla de datos que corra en la CI debe tener antes su contrato
  `tests/test_*_smoke.py` que nombre los ids afectados, para que la carga los aparte antes de abrir la PR.
- **Pérdida de datos.** El punto de control `automation/reading-datos-*` no puede borrarse antes de una publicación
  verificada; nada puede publicarse dos veces.
- **Salida de git cortada a mano.** Las rutas cambiadas salen de `scripts/git_estado.py` (`-z`), nunca de
  `línea[3:]`, `slice(3)` ni `cut -c4-` sobre `git status --porcelain` (los renombrados salen como «a -> b»).
- **Fechas y zonas horarias.** Las ventanas nocturnas son de Madrid (`Europe/Madrid`), no UTC.
- **Parches puntuales.** Señala arreglos para un libro, ISBN o fecha concretos: hay que cubrir la clase de fallo.
- **Control por texto de logs.** Leer mensajes de error o logs como mecanismo de decisión es frágil.
- **Tests que no prueban nada.** Mocks que sustituyen justo la función que debería probarse.
