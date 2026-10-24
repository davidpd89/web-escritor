# PR #743 (reloj del radar 2026-10-24) fusionada y verificada (2026-10-24)

Merge: `8a2db548ec6810a819685da243af0e9e2b10ea63`. Despliegue de Pages: run `40075442531` (correcto).

## Cambios
- PR #743 (abierta por `github-actions[bot]`) fusionada en main. Rama actualizada con la API de GitHub (sin force push); eso relanzó los checks sin `action_required`.
- Commit `f0d868b7`: 4 avisos npm dev transitivos (`body-parser`, `undici` x2, `zod`) añadidos a `data/npm-supply-chain-baseline.json` como `accept-temporarily` hasta 2026-12-29. Vienen de `@lhci/cli` y `pa11y-ci`; producción tiene 0 vulnerabilidades. Ya fallaban en main antes de la PR.
- Los textos de alcance y títulos de esas 4 entradas los redactó el agente: revisar.

## Verificado
- 19/19 checks de la PR, incl. contratos, enlaces, Pa11y, Lighthouse, reflow, CSP, hora pública, regresión visual y "Convocatorias browser QA".
- `check-radar-clock-current.py`: CURRENT para 2026-10-24 (73 activas, 13 en vigilancia).
- `tests/test-npm-supply-chain-baseline.py`: pasa.
- Producción: `opportunities.json` e `index.html` idénticos a main; `.ics` idéntico salvo CRLF; canonical correcto; `pagefind-entry.json` igual. 1280 px y 390 px sin errores de consola ni scroll horizontal.

## No verificado
- Uso manual de filtros, descarga del `.ics` y buscador (solo `pagefind.js` 200 y enlace al `.ics` presente).
- Diff manual de los archivos de Pagefind.

## Fallos
- `action_required` x18 (PR de bot): resuelto al actualizar la rama.
- "Required merge gate": baseline npm (ver arriba): resuelto.

## Pendientes
- Decidir actualizar las dependencias dev antes del 2026-12-29.
- Revisar la redacción de las 4 entradas del baseline.
- Sin tocar: stash `wip: other session - book-cover…` y ficheros `.codex-*` sin rastrear.
- Procesos temporales: ninguno lanzado en esta tarea.
