# E.5 · Revalidación de producción — performance budget determinista

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **IMPLEMENTED_IN_PR · DETERMINISTIC_ARTIFACT_BUDGET · BASELINE_CAPTURED · REQUIRED_GATE · NO_RUNTIME_CHANGE**.

## 1. Gap confirmado

`main` ya tenía Lighthouse CI, browser QA y múltiples contratos de asset/render, pero no una autoridad que respondiera de forma determinista a:

> ¿cuántos bytes y cuántos ficheros forman el shell y las familias runtime que queremos gobernar antes de mergear?

Lighthouse mide experiencia de laboratorio y puede variar por entorno. E.5 cubre una capa distinta: crecimiento del artifact versionado.

## 2. Implementación

La PR añade:

- `data/performance-budgets.json`: autoridad versionada de grupos, baseline y límites;
- `scripts/check-performance-budgets.py`: resolver de forma determinista entrypoints e imports locales;
- `tests/test-performance-budgets.py`: contrato de grafo, modo report y enforcement;
- `.github/workflows/performance-budget-qa.yml`: evidencia específica y artifact JSON;
- integración del checker dentro de `.github/workflows/required-merge-gate.yml`.

No se modifica runtime público.

## 3. Qué resuelve el grafo

El checker sigue transitivamente:

- `@import` CSS locales;
- `import`/`export ... from` estáticos de JS/MJS locales.

No sigue automáticamente `import()` dinámico. La razón es deliberada: una carga opcional/diferida no debe convertirse en shell crítico por una heurística del checker. Cuando esa carga importa para gobernanza se declara como entrypoint propio; por eso Home, interiores y widget del asistente tienen budgets separados.

Los specifiers externos/bare packages no se cuentan como bytes locales. Un import local declarado que no existe sí rompe el contrato.

## 4. Baseline real capturado por CI

La primera ejecución se hizo con `enforcement: report` y pasó 5 tests unitarios + medición sin errores.

| Budget | total bytes | CSS | JS | requests/ficheros |
| --- | ---: | ---: | ---: | ---: |
| `shell-v1` | 128349 | 107557 | 20792 | 12 |
| `home-runtime` | 33769 | 0 | 33769 | 1 |
| `interior-runtime` | 15673 | 0 | 15673 | 1 |
| `article-runtime` | 3629 | 0 | 3629 | 1 |
| `assistant-runtime` | 54256 | 9372 | 44884 | 7 |
| `assistant-widget-runtime` | 13795 | 4139 | 9656 | 3 |

Este baseline procede del branch real, no de cifras genéricas de terceros.

## 5. Límites adoptados

Política:

- bytes: ~10% de margen sobre baseline, redondeado hacia arriba a KiB;
- `request_count`: sin margen silencioso; un fichero/request nuevo obliga a revisar el budget.

Límites activos:

| Budget | total bytes máximo | requests máximo |
| --- | ---: | ---: |
| `shell-v1` | 141312 | 12 |
| `home-runtime` | 37888 | 1 |
| `interior-runtime` | 17408 | 1 |
| `article-runtime` | 4096 | 1 |
| `assistant-runtime` | 60416 | 7 |
| `assistant-widget-runtime` | 15360 | 3 |

El margen no intenta definir un estándar universal de rendimiento. Solo evita ruido por cambios pequeños mientras sigue haciendo visible un crecimiento material.

## 6. Dos fases verificadas

### Fase 1 — report

`Performance budget QA` run #1:

- 5/5 tests del checker: PASS;
- 6 budgets medidos;
- 0 errores;
- artifact `performance-budget-report` generado.

### Fase 2 — enforce

Después de fijar baseline/limits, `Performance budget QA` run #2 pasó en modo `enforce`. Eso demuestra que los límites describen el estado real y que el checker no estaba entrando verde únicamente porque no hubiera thresholds.

## 7. Required merge gate

El proyecto ya documenta que un workflow opcional rojo no debe coexistir con un Required merge gate verde para contratos universales. E.5 sigue esa misma regla.

La PR añade al gate requerido:

```bash
python scripts/check-performance-budgets.py --check --json .ci/performance-budget.json
```

Y conserva el JSON junto a `.ci/release-readiness.md` en el artifact `required-merge-gate-evidence`.

Así, una futura regresión de budget bloquea el contexto requerido; no depende de que alguien revise manualmente el workflow específico.

## 8. Cómo elevar un budget

No subir un límite solo para poner CI verde. Una modificación debe explicar:

1. qué fichero/contributor creció;
2. before/after;
3. por qué el coste es necesario;
4. si puede reutilizarse/eliminarse otra carga;
5. si cambia `request_count`, por qué el nuevo request está justificado;
6. si el cambio afecta experiencia, qué muestra Lighthouse/trace/Coverage cuando proceda.

El JSON específico de CI lista los ficheros y bytes del grafo para facilitar ese diagnóstico.

## 9. Límites del contrato

E.5 no sustituye:

- LCP/CLS/TBT/INP;
- compresión live E.7;
- Coverage;
- waterfall de preload/fetchpriority;
- third-party governance;
- tamaño total de todos los assets del repositorio.

Mide exclusivamente los grupos declarados. Si aparece una nueva familia significativa debe añadirse deliberadamente, no confiar en que el checker la adivine.

## 10. Estado para integración

E.5 pasa de backlog documental a implementación real de gobernanza. No hay cambio visual ni de comportamiento de la web; el valor está en impedir crecimiento accidental y convertir aumentos de payload/request count en decisiones explícitas.