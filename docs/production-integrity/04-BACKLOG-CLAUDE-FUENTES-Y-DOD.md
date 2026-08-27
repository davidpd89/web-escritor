# 04 — Backlog ejecutable para Claude, fuentes y Definition of Done

## 1. Estado al crear esta PR

### PRINCIPIO OPERATIVO NO NEGOCIABLE

La protección de `main` debe ser **agent-operable end to end**.

Claude/ChatGPT/agentes autorizados deben poder:

1. crear rama;
2. crear/actualizar PR;
3. leer CI;
4. corregir fallos;
5. reejecutar checks;
6. actualizar la rama si `main` avanzó;
7. mergear la PR verde;
8. comprobar el deploy.

El propietario **no debe tener que aprobar, resolver conversaciones, pulsar Merge ni hacer mantenimiento rutinario de GitHub**.

Por tanto, al configurar el ruleset:

- `required approvals = 0`;
- `Require conversation resolution = OFF` en el modelo actual;
- ninguna restricción de actor que impida a los agentes autorizados mergear;
- auto-merge es compatible y puede usarse cuando resulte conveniente;
- cualquier regla que en la práctica obligue al propietario a intervenir se considera una regresión operacional y debe retirarse o rediseñarse.

### IMPLEMENTADO EN CÓDIGO DE ESTA PR

- [x] smoke HTTP reutilizable para staging/producción;
- [x] ampliación de clases privadas verificadas por HTTP;
- [x] machine routes en smoke;
- [x] canonical crítico en smoke;
- [x] producción con TLS estricto;
- [x] `Deploy Pages` con `verify-production` posterior;
- [x] reintentos de propagación acotados;
- [x] nuevo workflow universal `Required merge gate`;
- [x] validación sintáctica del smoke dentro del gate;
- [x] evidencia de release estática subida como artifact;
- [x] builder/public-artifact revalidado dentro del gate universal.

### REQUIERE EVIDENCIA DE CI DE ESTA PR

- [ ] `Required merge gate` aparece y pasa sobre el HEAD final;
- [ ] `Public artifact contract` pasa;
- [ ] `Sitewide Reflow QA` pasa;
- [ ] `Accessibility baseline (Pa11y)` pasa;
- [ ] specialized checks atribuibles al diff quedan verdes;
- [ ] revisar cualquier rojo real; no llamarlo flaky sin logs.

### REQUIERE ACCIÓN DE CONFIGURACIÓN DESPUÉS DEL MERGE

- [ ] crear/activar ruleset de `main`;
- [ ] seleccionar contexts exactos ya observados;
- [ ] exigir PR;
- [ ] `required approvals = 0`;
- [ ] `conversation resolution = OFF`;
- [ ] bloquear force push/deletion;
- [ ] no restringir merge a un actor que excluya Claude/ChatGPT;
- [ ] probar push directo rechazado;
- [ ] probar PR verde **mergeada por un agente sin intervención del propietario**.

No ejecutar esa parte antes de conocer el context real del nuevo workflow.

## 2. Backlog por prioridad

---

# P0 — cerrar antes de considerar terminada la iniciativa

## PI-001 — CI real del nuevo gate

**Actor:** REPO / GitHub Actions / agente  
**Estado inicial:** pendiente hasta que esta PR ejecute.

### Pasos

1. abrir PR con esta rama;
2. dejar que GitHub cree los checks;
3. inspeccionar el job `Required merge gate`;
4. si falla, leer el paso exacto;
5. corregir causa real;
6. no eliminar assertions para obtener verde;
7. repetir sobre HEAD final.

### Aceptación

- HEAD final tiene `Required merge gate: success`.

---

## PI-002 — comprobar compatibilidad staging del smoke generalizado

**Actor:** REPO / CI / agente

El script mantiene `STAGING_BASE_URL`, por lo que el workflow existente no necesita cambiar.

### Verificar

```text
Staging smoke test -> success
```

Si el staging actual devuelve un status distinto en una ruta privada, investigar si se trata de un leak, WAF o diferencia legítima. No cambiar a `status != 200` sin entenderlo.

### Aceptación

- scheduled/manual staging smoke sigue operativo;
- output usa `STAGING SMOKE PASS`;
- no se ha debilitado TLS por defecto.

---

## PI-003 — primera verificación de producción post-merge

**Actor:** GitHub Actions / agente

Al mergear la PR, `Deploy Pages` debe ejecutar:

```text
build
  -> deploy
     -> Verify production after deploy
```

El agente que realiza el merge debe consultar el resultado. No se exige que el propietario vigile el workflow manualmente.

### Aceptación

- los tres jobs se ejecutan en el mismo SHA;
- production smoke queda verde;
- si queda rojo, el agente lo trata como incidente y no declara iniciativa cerrada.

---

## PI-004 — activar `main-production-integrity`

**Actor:** agente autorizado con capacidad de configuración del repo  
**Dependencia:** PI-001 verde y nombres de contexts confirmados.

Si la integración disponible no permite escribir rulesets, dejar la configuración exacta documentada para un agente que sí disponga de esa capacidad. **No convertirlo en una aprobación por-PR del propietario.**

### Config recomendada

- target `main`;
- require pull request;
- `required approvals = 0`;
- `Require conversation resolution = OFF`;
- no force push;
- no delete;
- sin restricciones de actor que impidan a Claude/ChatGPT mergear PR verdes;
- required status checks:
  - `Required merge gate`;
  - `Public artifact contract`;
  - `reflow-sitewide` / nombre real mostrado;
  - `pa11y-baseline` / nombre real mostrado;
- branch up-to-date solo después de demostrar que los agentes pueden actualizar la rama automáticamente sin intervención del propietario.

### Aceptación

La configuración efectiva debe dejar de representar el estado sin protección:

```text
protected:false
required checks: []
rulesets: []
```

No es obligatorio que la API legacy `protected` refleje exactamente un ruleset moderno de la misma forma; la autoridad final es el ruleset activo + prueba conductual.

Además debe cumplirse:

```text
PR verde -> merge ejecutable por agente autorizado -> sin aprobación manual
```

---

## PI-005 — prueba conductual de protección

**Actor:** agente / Git

### Caso 1

Push normal directo a `main` con una prueba inocua y controlada.

Esperado: GitHub rechaza.

No dejar el commit de prueba en `main`.

### Caso 2

PR verde creada por agente.

Esperado: el mismo agente o un agente autorizado puede ejecutar `merge pull request` o auto-merge sin aprobación del propietario.

### Aceptación

- evidencia textual del rechazo del push directo;
- evidencia de PR protegida funcionando;
- evidencia de merge por agente sin paso humano obligatorio.

---

# P1 — siguiente capa recomendada

## PI-101 — hydrated DOM link contract

**Problema:** el grafo estático/Lychee no cubren todos los href que JS pueda crear/modificar.

**Implementación recomendada:** Playwright local contra artifact/site, extraer enlaces hidratados same-origin y detectar destinos imposibles/anchors vacíos.

### No hacer

- no duplicar requests externos de Lychee;
- no seguir todos los enlaces de Internet desde browser QA;
- no convertir links `mailto:`/tel en errores.

### Aceptación

- fixture deliberado falla;
- rutas públicas representativas pasan;
- cero navegación a rutas privadas/gated desde shell/runtime público salvo casos deliberados.

---

## PI-102 — headers y routing production contract

Verificar por HTTP real:

- HTTPS;
- HTTP→HTTPS;
- custom domain;
- content types;
- cache-control relevante;
- service worker;
- headers de seguridad reales de la capa servida;
- redirects legacy prioritarios.

Esto complementa el source QA.

---

## PI-103 — release identity

Estudiar una forma de correlacionar el SHA desplegado con producción.

Opciones:

- `/release.json` generado;
- metadata de deployment/API;
- hash del artifact.

Requisito: no introducir clock-driven content que cause diffs espurios ni filtrar información sensible.

---

## PI-104 — production form canary

Cerrar la diferencia entre contrato mock y backend live sin contaminar CRM.

Primero investigar soporte de canary/no-op. Si no existe, mantener prueba live controlada solo en hitos importantes y ejecutable por agente cuando exista autorización/capacidad.

No crear contactos ficticios en cada deploy.

---

## PI-105 — release tags y rollback targets

Crear convención:

```text
release/prelaunch-2026-09
release/manecillas-2026-09-03
release/postlaunch-stable-YYYY-MM-DD
```

Los nombres exactos pueden simplificarse. Lo importante es disponer de targets conocidos y evidencia asociada.

No convertir cada commit en release.

---

## PI-106 — observabilidad del deploy

Evaluar notificación/issue solo cuando:

- `Verify production after deploy` falle persistentemente;
- una tarea programada detecte producción caída;
- un internal leak smoke falle.

Evitar spam por fallos de una sola petición transitoria.

El objetivo es que el sistema y los agentes detecten el incidente; no que el propietario tenga que revisar Actions después de cada cambio.

---

# P2 — mejoras después del lanzamiento

## PI-201 — racionalizar CI

Una vez estabilizado el proyecto:

1. medir duración/frecuencia/fallos de los workflows;
2. detectar duplicación real;
3. consolidar checkers que prueben exactamente el mismo contrato;
4. conservar ownership por familia donde aporte diagnóstico;
5. no optimizar CI eliminando cobertura solo por reducir minutos.

Coordinar con PR #115 de higiene del repo.

---

## PI-202 — merge queue

Solo si crece el paralelismo de PR y aparecen carreras por base desactualizada.

Debe estudiarse como automatización, no como nueva tarea manual.

---

## PI-203 — signed commits

Investigar después. El estado actual contiene commits unsigned; necesita transición real, no switch súbito que bloquee a los agentes.

---

## PI-204 — environment protection avanzada

No activar approvals/reviewers de `github-pages` en el modelo operativo actual.

Solo reevaluar si aparece una necesidad real de separación de funciones y existe un mecanismo automatizable que no convierta al propietario en aprobador de cada despliegue.

---

## 3. Guía para Claude al desarrollar P1/P2

Antes de tocar código:

1. leer estos cinco documentos;
2. leer el workflow/script real vigente, no asumir que este backlog sigue exacto meses después;
3. consultar `main` fresco;
4. revisar PR abiertas para evitar duplicar ownership;
5. trabajar en rama nueva o continuar esta PR solo si sigue abierta y es la dueña clara;
6. añadir fixture rojo antes de endurecer un gate cuando sea razonable;
7. no desplegar producción para «probar» salvo autorización explícita cuando la acción implique infraestructura externa no reversible;
8. no cambiar DNS/Cloudflare/Brevo como efecto lateral de release integrity;
9. no tocar hechos/editorial de Manecillas salvo que el propio gate descubra drift real;
10. dejar evidencia de ejecución, no solo descripción teórica;
11. **si los checks están verdes y el trabajo está completo, mergear la PR desde el agente cuando el encargo incluya dejarlo integrado; no derivar al propietario una tarea administrativa de GitHub**.

## 4. Antipatrones

### «Hay muchos workflows, así que estamos protegidos»

Falso si `main` acepta push directo y los workflows no son required.

### «Deploy Pages verde significa web verde»

Solo demuestra éxito del workflow de deployment hasta el punto que ese workflow comprueba.

### «Hagamos required todos los checks»

No. Puede introducir deadlocks por path filters, terceros o jobs especializados.

### «Para estar seguros, que David apruebe cada PR»

No. Contradice el modelo operativo del proyecto. Seguridad debe venir de CI y trazabilidad, no de trasladar clics rutinarios al propietario.

### «Require conversation resolution siempre es más seguro»

No en este flujo. Puede crear un bloqueo administrativo residual sin añadir una verificación técnica equivalente. Se mantiene OFF mientras no sea completamente automatizable y útil.

### «Si production smoke falla por TLS, desactivamos TLS»

No.

### «Si una ruta interna devuelve 200 pero no tiene enlaces, da igual»

No. Es una violación del boundary.

### «Un 404 interno es seguridad suficiente para secretos»

No sustituye no versionar secretos. Es defensa adicional.

### «Auto-rollback siempre es más seguro»

No sin comprender failure modes y compatibilidad del release anterior.

### «La protección de main nos impide trabajar con agentes»

No debe hacerlo. El diseño correcto bloquea bypass y rojo, pero permite `agente -> PR -> verde -> merge`.

## 5. Fuentes oficiales investigadas

Corte: 27/08/2026.

### Repository rulesets

`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets`

Uso: alcance y comportamiento de rulesets.

### Reglas disponibles

`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets`

Uso: pull requests, required checks, force pushes y reglas relacionadas.

### Protected branches

`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`

Uso: semántica de required status checks y branch protection.

### Troubleshooting required checks

`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/troubleshooting-required-status-checks`

Uso: estados pending/skipped y problemas de checks requeridos.

### GitHub Pages custom workflows

`https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages`

Uso: artifact/deploy Pages y environment.

### Environments

`https://docs.github.com/en/actions/deployment/targeting-different-environments/managing-environments-for-deployment`

Uso: deployment protection / branch restrictions / reviewers cuando proceda. En este proyecto no activar reviewers de environment de forma rutinaria.

## 6. Fuentes internas del repo que deben leerse junto a esta iniciativa

- `.github/workflows/deploy-pages.yml`;
- `.github/workflows/public-artifact-contract.yml`;
- `.github/workflows/sitewide-reflow-qa.yml`;
- `.github/workflows/pa11y-baseline.yml`;
- `.github/workflows/cross-engine-smoke.yml`;
- `.github/workflows/lighthouse-ci.yml`;
- `.github/workflows/staging-smoke-test.yml`;
- `tests/test-staging-smoke.mjs`;
- `scripts/build-public-dist.py`;
- `scripts/release-readiness.py`;
- `docs/AUDITORIA-POSTLAUNCH-PRODUCCION-YALE-2026.md`;
- `docs/production-integrity/*`.

## 7. Definition of Done global

### Código

- [ ] Required merge gate universal verde;
- [ ] no tiene filtros de paths;
- [ ] artifact allowlist-first sigue intacto;
- [ ] staging smoke no ha regresado;
- [ ] deploy añade verify-production;
- [ ] production verify usa custom domain;
- [ ] TLS estricto;
- [ ] bounded retries;
- [ ] fallo persistente deja rojo el workflow;
- [ ] canonical/machine/private-boundary cubiertos.

### GitHub

- [ ] ruleset activo sobre `main`;
- [ ] PR obligatoria;
- [ ] `required approvals = 0`;
- [ ] `Require conversation resolution = OFF`;
- [ ] required checks configurados con nombres reales;
- [ ] no path-filtered check requerido por error;
- [ ] force pushes bloqueados;
- [ ] deletions bloqueadas;
- [ ] ninguna restricción de actor impide merge a Claude/ChatGPT;
- [ ] prueba de push directo rechazada;
- [ ] prueba de PR verde **mergeada por agente sin intervención del propietario** realizada.

### Operación

- [ ] primer Deploy Pages post-merge completo verde incluido production verify;
- [ ] rollback entendido/documentado;
- [ ] no auto-rollback opaco;
- [ ] un fallo del production smoke se trata como incidente y no como warning;
- [ ] el propietario no necesita vigilar ni aprobar cada release.

### Disciplina

- [ ] ninguna suite existente se ha debilitado para cerrar esta iniciativa;
- [ ] no se ha usado esta PR para meter diseño/SEO/features no relacionadas;
- [ ] cualquier P1 no implementado queda aquí con owner y aceptación;
- [ ] después de activar el ruleset, esta documentación se actualiza con evidencia real y deja de describir `main` como no protegido.

## 8. Criterio de merge de esta PR

Esta PR puede mergearse cuando:

1. el HEAD está sincronizado/revisado contra `main` fresco;
2. `Required merge gate` está verde;
3. `Public artifact contract` está verde;
4. Sitewide Reflow está verde;
5. Pa11y está verde;
6. cualquier specialized check disparado por los cambios está verde o existe diagnóstico reproducible que demuestre que no es atribuible — no usar esta cláusula para ignorar rojo real;
7. el diff final contiene únicamente release integrity y documentación asociada;
8. no hay despliegue/configuración live no autorizada.

Cuando se cumpla, **el agente autorizado puede mergear esta PR a `main`; no se requiere aprobación manual del propietario**.

Después del merge queda una acción P0 inmediata: activar el ruleset de `main` usando los contexts observados en esta PR y validar que conserva el flujo agent-operable.
