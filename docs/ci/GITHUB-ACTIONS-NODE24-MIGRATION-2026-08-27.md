# GitHub Actions · migración de runtimes Node 24 · 27/08/2026

## Por qué existe este pendiente

Los runs actuales del repositorio muestran el warning de GitHub Actions:

```text
Node 20 is being deprecated. This workflow is running with Node 24 by default.
...
actions/checkout@v4, actions/setup-python@v5 ... are being forced to run on Node.js 24
```

Eso no está rompiendo CI hoy, pero sí es una señal de mantenimiento con fecha: no debemos esperar a que GitHub retire la compatibilidad para descubrir incompatibilidades en decenas de workflows.

## Estado oficial consultado el 27/08/2026

Fuentes primarias:

- `actions/checkout` releases: https://github.com/actions/checkout/releases — latest observado `v7.0.1`;
- `actions/setup-node` releases: https://github.com/actions/setup-node/releases — latest observado `v7.0.0`;
- `actions/setup-python` releases: https://github.com/actions/setup-python/releases — latest observado `v7.0.0`;
- `actions/upload-artifact` releases: https://github.com/actions/upload-artifact/releases — latest observado `v7.0.1`;
- `actions/cache`: https://github.com/actions/cache — línea Node 24 `v5`, latest observado `v5.0.5`.

La documentación actual de `setup-python` ya usa ejemplos `actions/checkout@v7` + `actions/setup-python@v7`. `setup-python@v7` declara engine Node >=24. `actions/cache@v5` y `upload-artifact@v6+` requieren runner >=2.327.1; el runner hospedado observado en esta auditoría es 2.336.0, por encima de ese mínimo.

## Qué NO hacer

No ejecutar un search/replace global `@v4 -> @v7` sin revisar action por action.

Riesgos:

- cambios breaking de inputs/defaults;
- `checkout` introdujo cambios de seguridad en 2026 relacionados con `pull_request_target` / unsafe PR checkout;
- diferencias entre github.com y GHES;
- actions que todavía no tienen la misma major;
- workflows con comportamiento especial de artifact/cache;
- pinned SHA vs major tag.

## Inventario que Claude debe generar antes de cambiar

Para cada `.github/workflows/*.{yml,yaml}` extraer cada `uses:` y agrupar:

```text
action
major actual
SHA si está pinneada
major/latest oficial
runtime actual
breaking notes relevantes
nº de workflows afectados
privilege class del workflow
```

Prioridad inicial:

1. `actions/checkout@v4`;
2. `actions/setup-python@v5`;
3. `actions/setup-node@v4`;
4. `actions/upload-artifact@v4`;
5. `actions/cache@v4`;
6. cualquier otra action que todavía declare Node 20/16.

## Estrategia recomendada

### Fase 1 — inventario y compatibility matrix

Sin modificar workflows. Comparar release notes oficiales y detectar inputs incompatibles.

### Fase 2 — PR de migración pequeña

Migrar primero un grupo representativo de workflows no privilegiados:

- tool tests;
- Pa11y/Reflow;
- CSP/public artifact.

Ejecutar CI y confirmar artifacts/cache/browser install.

### Fase 3 — workflows sensibles

Revisar por separado:

- deploy Pages;
- workflows con permisos de Pages/id-token;
- cualquier `pull_request_target` si existiera;
- workflows con artifact transfer entre jobs;
- workflows usados como required status checks.

### Fase 4 — contrato preventivo

Añadir checker que identifique majors explícitamente prohibidas/deprecadas para actions críticas. No bloquear por no usar siempre «latest»: una major estable puede ser deliberada; bloquear solo la baseline que el proyecto haya declarado obsoleta.

## Seguridad de actions

Además del runtime, valorar pinning por SHA para workflows sensibles. Si se elige SHA pinning:

- conservar comentario con tag humano (`# v7.0.1`);
- actualizar mediante Dependabot/Renovate o revisión periódica;
- no convertir el SHA pinning en dependencias eternamente congeladas.

## DoD

- [ ] inventario completo de `uses:`;
- [ ] release notes/breaking changes revisadas por cada action migrada;
- [ ] no queda warning Node 20 provocado por actions que tengan migración compatible disponible;
- [ ] required checks mantienen exactamente sus nombres/contextos esperados por el ruleset;
- [ ] artifacts/cache siguen funcionando;
- [ ] deploy Pages probado sin alterar release identity;
- [ ] CI completo verde;
- [ ] rollback claro a la major anterior si aparece regresión;
- [ ] documentación/ruleset revisados si cambia el nombre de algún check.

## Owner

Abrir PR propia de **CI dependency/runtime maintenance** después de cerrar #129/#130. No mezclar esta migración masiva con el fix CLS ni con la revalidación de Claude Toolbox #120.
