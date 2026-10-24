# Mantenimiento npm dev: avisos de #743 (2026-10-24)

## Cambios
- `npm audit fix` (sin `--force`): elimina body-parser, express, qs, undici, js-yaml y brace-expansion del lockfile.
- `pa11y-ci` 4.1.1 -> 5.0.0 (puppeteer 25.16, cheerio 1.2, zod 4.6.7). Pin del workflow `pa11y-baseline.yml` actualizado (Node 22 cumple `^22.13`).
- `@lhci/cli` 0.15.1 se mantiene: es la ultima publicada y fija lighthouse 12.6.1.
- Baseline `data/npm-supply-chain-baseline.json`: 18 -> 6 entradas. Eliminadas 12 resueltas; corregidos paths, alcance y titulo oficial de zod (GHSA-mrhx-c7xc-m3w5).
- `tests/test-npm-supply-chain-baseline.py`: usa los nodos que reporta `npm audit` (antes tomaba la primera copia del paquete, p. ej. el zod 4.6.7 seguro).
- Sin overrides nuevos.

## Excepciones que quedan (todas bajo `@lhci/cli` 0.15.1)
extract-zip x2 (via lighthouse > puppeteer-core), tmp x2 (inquirer 6 / tmp 0.1.0), uuid 8, zod 3.25.76 (chromium-bidi 14). Solucionarlas exige majors incompatibles (lighthouse 13, uuid 11, zod 4) que LHCI 0.15.1 no soporta; un override seria forzar versiones no probadas. Revisar cuando salga un `@lhci/cli` nuevo (reviewBy 2026-12-29).

## Verificado en local
- `npm audit`: 21 -> 12 avisos (todos via @lhci/cli). Produccion: 0.
- `test-npm-supply-chain-baseline.py`: OK.
- Pa11y-ci 5.0.0 con `.pa11yci` sobre 5 URLs (/, herramientas, convocatorias, libros, autor): 0 errores.
- `lhci collect` + `assert` (1 run, Windows): exit 0, 0 errores, 5 avisos de rendimiento (LCP/perf, esperables en local con 1 run). Fallo conocido de limpieza EPERM del tmp de chrome-launcher en Windows, ajeno al cambio.

## No verificado
- Pa11y sobre todo el sitemap y Lighthouse con 3 runs: lo valida CI.
- Resultado de CI/merge: ver PR.

## Continuidad
Informe de #743: `.ci/2026-10-24-pr743-radar-merge.md` (incluido en esta PR). Stash y `.codex-*` sin tocar.
