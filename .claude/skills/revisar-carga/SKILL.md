---
name: revisar-carga
description: "Usar antes de abrir o fusionar cualquier PR que toque la carga nocturna de libros (scripts/refresh-reading-catalogue.py, reading_*, materializar, git_estado, check-reading-data, workflows reading-*, tests/test_reading_*). Revisión de código, CI local y ensayo dry_run."
---

# Revisar un cambio de la carga nocturna

La carga es: API → transformar → subir. Cada cambio pasa estas cuatro puertas, en orden. No se abre la PR
si falla una; no se fusiona sin el ensayo.

1. **Revisión de código.** `/code-review high` sobre la rama (o pedir a Codex `@codex review` en la PR).
   En la PR revisan además, gratis y sin hacer commits, Gemini Code Assist (`/gemini review`), CodeRabbit
   (`@coderabbitai review`) y Codex. Antes de fusionar, leer sus comentarios
   (`gh pr view <n> --comments` y `gh api repos/{owner}/{repo}/pulls/<n>/comments`) y resolver o descartar
   razonadamente cada P1/P2.
   Aplicar los hallazgos confirmados. Si un hallazgo dice «el enfoque es frágil», cambiar el enfoque,
   no parchear el síntoma.
2. **Contratos de datos.** `python scripts/check-reading-data.py --fallos` debe salir vacío. Toda
   comprobación que corra en la CI de la PR sobre datos de libros debe existir también como contrato
   (`tests/test_*_smoke.py` o `test_market_*.py`) que **nombre los ids** de los libros que fallan, para que
   `assemble` los aparte en vez de tumbar el lote.
3. **CI local.** `python scripts/local-ci.py --baseline`. Solo cuentan los fallos nuevos frente a main.
4. **Ensayo real.** Tras subir la rama:
   `gh workflow run reading-catalogue-sync.yml --ref <rama> -f dry_run=true`
   y comprobar que el run termina en verde con el resumen de libros esperado. Un run lanzado no es un
   run aprobado.

Al fusionar: no durante una ingesta activa (`gh run list -w reading-catalogue-sync.yml -s in_progress`);
update-branch de una PR cada vez.

## Al revisar, buscar sobre todo

- Rutas de git: renombrados, ficheros nuevos sin seguimiento, `git status` en directorios que no son repo.
- Datos nuevos de la API: campos desconocidos, ISBN repetidos, fechas vacías o futuras, textos sin tildes.
- Reintentos: que un fallo conserve el punto de control (`automation/reading-datos-*`) y que el reintento
  no publique dos veces.
- Que la corrección cubra la clase de fallo, no el libro concreto de esta noche.

## Revisión del código existente (diaria)

`revision-existente.yml` abre cada mañana una PR «Revisión del código existente: <grupo>» contra
`revision/base-*`, que **no se fusiona nunca**, y un issue «Auditoría Jules: <grupo>». Al revisar la carga:
`gh pr list --search "head:revision/" --json number,title` y leer sus comentarios (mismos `gh api` que en la
puerta 1). Cada hallazgo real se arregla en una PR normal contra `main`, con su test, cubriendo la clase de
fallo. Los descartes se responden en el hilo con el motivo. Grupos: `python scripts/revision_existente.py grupos`.
