# 02 — Ruleset de `main` y checks obligatorios

## 1. Objetivo

Convertir `main` en una rama de producción gobernada: los cambios normales deben llegar mediante PR y pasar una selección pequeña de gates universales antes del merge.

La configuración de GitHub es una acción de cuenta/repositorio, no código versionado. Esta PR deja el contrato exacto, pero **no activa el ruleset automáticamente**.

## 2. Por qué ruleset y no «acordarnos de usar PR»

Un convenio humano sirve hasta que hay prisa, un agente tiene permisos de push o una corrección aparentemente trivial parece segura.

El estado observado el 27/08 demuestra que el camino directo existe y se usa.

La protección debe estar en la plataforma que controla el ref, no solo en documentación.

## 3. Orden seguro de implantación

1. Mergear esta PR solo cuando sus checks estén verdes.
2. Confirmar en GitHub el nombre real del nuevo context `Required merge gate`.
3. Confirmar que `Public artifact contract`, `Sitewide Reflow QA` y `Accessibility baseline (Pa11y)` aparecen en una PR normal.
4. Crear el ruleset para `main` en modo `Evaluate` si la UI/plan lo permite y resulta útil; si no, configurarlo en `Active` solo después de verificar los contexts.
5. Probar con una PR mínima no destructiva.
6. Confirmar que el push directo normal queda bloqueado y que una PR verde sí puede mergearse.
7. Registrar fecha y settings finales en este documento o en evidencia operativa.

## 4. Ruleset recomendado

### Nombre

`main-production-integrity`

### Enforcement

`Active` después de la prueba inicial.

### Target

Rama por nombre:

```text
main
```

No aplicar a todas las ramas de trabajo.

## 5. Reglas P0

### 5.1 Restrict deletions

**ON**.

No debe poder borrarse `main` accidentalmente.

### 5.2 Block force pushes

**ON**.

El historial de producción no debe reescribirse como flujo normal.

### 5.3 Require a pull request before merging

**ON**.

Objetivo: cerrar el camino ordinario `push -> main -> deploy`.

#### Aprobaciones

Mientras el repositorio tenga un único mantenedor operativo:

```text
required approvals: 0
```

La seguridad aquí proviene de la PR + CI + trazabilidad, no de obligar al propietario a conseguir una aprobación que quizá no exista.

Si en el futuro hay un segundo revisor real y estable, subir a 1 aprobación puede tener sentido.

No crear un requisito decorativo que termine generando bypass sistemático.

### 5.4 Require conversation resolution before merging

**ON** si GitHub permite combinarlo con el modelo actual de PR.

Un hilo de revisión abierto debe resolverse o quedar explícitamente tratado antes de promover.

### 5.5 Require status checks to pass

**ON**.

## 6. Set de required checks recomendado

El objetivo no es convertir todos los workflows en required. Deben elegirse contexts que:

- corran en toda PR a `main`;
- sean deterministas;
- tengan señal alta;
- no dependan de servicios externos inestables;
- no se salten por path filters.

### P0 — Required merge gate

Workflow:

`.github/workflows/required-merge-gate.yml`

Job/context esperado:

`Required merge gate`

Debe ser required.

Cubre contrato estático consolidado + artifact final.

### P0 — Public artifact contract

Workflow:

`.github/workflows/public-artifact-contract.yml`

No tiene `paths:` y se ejecuta en cualquier PR a `main`.

Se recomienda mantenerlo required al menos durante la ventana del lanzamiento, aunque parte de su trabajo se replique deliberadamente en `Required merge gate`.

La duplicación aquí es defensa en profundidad de una frontera P0: repo privado/técnico frente a artifact público.

Más adelante, si se demuestra redundancia operacional, se puede decidir mantener solo uno.

### P0 — Sitewide Reflow QA

Workflow:

`.github/workflows/sitewide-reflow-qa.yml`

Su trigger `pull_request:` es universal.

Se recomienda required porque un problema serio de layout/overflow/zoom puede afectar cualquier familia y el proyecto hace cambios visuales frecuentes.

Context de job actual:

`reflow-sitewide`

Antes de seleccionarlo en el ruleset, confirmar en una ejecución real cómo lo presenta GitHub en el selector.

### P0 — Accessibility baseline (Pa11y)

Workflow:

`.github/workflows/pa11y-baseline.yml`

También se ejecuta en toda PR.

Se recomienda required durante esta fase porque audita todas las URLs del sitemap contra WCAG2AA y ya tiene baseline limpia según el historial del proyecto.

Context de job actual:

`pa11y-baseline`

Confirmar nombre exacto en GitHub antes de guardar el ruleset.

## 7. Qué NO marcar required ahora

### Cross-engine smoke

Es muy valioso, pero actualmente usa `paths:`.

No debe marcarse required universal en ese estado porque una PR que no coincida con esos paths podría no crear el context.

Opciones futuras:

A. mantenerlo advisory/path-scoped;

B. quitar path filters y hacerlo universal, aceptando el coste de instalar Chromium + Firefox + WebKit en cada PR;

C. incorporar un smoke cross-engine más pequeño dentro del required gate.

No tomar B/C sin medir tiempo/coste/fiabilidad primero.

### Lighthouse CI

También está path-filtered y además es comparativamente más costoso/ruidoso.

Debe seguir siendo gate del cambio cuando corre, pero no required universal mientras pueda saltarse.

### Broken links externos

Dependen de terceros y pueden fallar por 429/5xx/anti-bot sin que el release esté roto.

No deben bloquear siempre `main` salvo que se cambie a un contrato estable y se separe claramente enlace roto real de indisponibilidad externa.

### Staging smoke

Depende de un despliegue externo distinto del HEAD de la PR. Es una sonda operativa, no autoridad pre-merge.

### Workflows de una familia concreta

Cuaderno, Samuel, herramientas, recomendaciones, etc. deben seguir corriendo cuando sus paths aplican, pero no todos deben ser required universales.

## 8. Require branches to be up to date

Recomendación:

**ON después de que el required gate haya demostrado estabilidad.**

Ventaja: el SHA que se mergea está probado contra el `main` más reciente.

Coste: con mucha actividad paralela puede obligar a actualizar ramas frecuentemente.

Dado que `main` despliega directamente, la propiedad vale la pena, especialmente durante la semana de lanzamiento.

## 9. Bypass

### Regla normal

Ningún actor/agente debe tener bypass como camino habitual.

### Emergencia real

Puede definirse una vía de propietario/admin solo si GitHub lo exige para recuperación operacional, con estas condiciones:

1. incidente de producción real;
2. razón registrada;
3. cambio mínimo;
4. ejecutar el required gate en la rama de hotfix antes del push/bypass siempre que sea técnicamente posible;
5. verificar producción inmediatamente después;
6. abrir PR retrospectiva o registro del hotfix si el mecanismo de emergencia no produjo PR;
7. no usar bypass para «esto es solo CSS» o «solo cambia una imagen».

## 10. Reglas que no son P0 ahora

### Signed commits

No activar todavía.

El HEAD auditado está `verified:false / unsigned`. Activarlo de golpe bloquearía el flujo existente y no corrige el riesgo principal.

Puede investigarse más adelante con una transición deliberada.

### Linear history

Opcional.

Mejora legibilidad, pero no protege tanto como PR + required checks + no force push.

### Merge queue

No necesaria para el volumen actual salvo que empiecen a convivir muchas PR aprobadas simultáneamente.

### Required reviewer

No imponer 1 si no existe realmente una segunda persona que pueda aprobar de forma sostenida.

## 11. Por qué no requerir 30 checks

Una lista enorme de required contexts genera:

- mantenimiento administrativo alto;
- bloqueo cuando cambia un job name;
- dificultad para distinguir señal crítica de ruido;
- tentación de bypass;
- dependencia de servicios externos;
- problemas con workflows path-filtered.

La estrategia es una pirámide:

```text
                 REQUIRED
       ┌────────────────────────┐
       │ merge + artifact + a11y│
       │ + reflow               │
       └────────────────────────┘

               SPECIALIZED
   ┌────────────────────────────────┐
   │ cross-engine, Lighthouse, CSP, │
   │ Cuaderno, tools, Samuel, etc.  │
   └────────────────────────────────┘

               OPERATIONS
 ┌─────────────────────────────────────┐
 │ staging, production smoke, Lychee,  │
 │ external dashboards/monitoring      │
 └─────────────────────────────────────┘
```

## 12. Validación del ruleset

Después de activarlo, crear una rama de prueba y confirmar:

### Caso A — push directo

Intentar un push normal a `main` desde un clon/cliente sin bypass.

Resultado esperado: rechazado por GitHub.

No usar un cambio real de producto para esta prueba.

### Caso B — PR con Required merge gate rojo

Crear una PR de prueba que rompa deliberadamente un fixture seguro o usar una rama controlada.

Resultado esperado: merge bloqueado.

Revertir el fixture antes de cerrar la prueba.

### Caso C — PR verde

Todos los required contexts pasan.

Resultado esperado: merge habilitado.

### Caso D — specialized workflow rojo

Si el workflow no es required, GitHub puede permitir merge. La regla humana sigue siendo no mergear un rojo real atribuible al cambio.

Esto es deliberado: los required checks son el suelo técnico, no una licencia para ignorar el resto del CI.

## 13. Fuente oficial

Consultar siempre documentación actual de GitHub antes de cambiar el ruleset, especialmente si cambia el producto/plan:

- `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets`
- `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets`
- `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`
- `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/troubleshooting-required-status-checks`

Punto operativo importante de la documentación oficial: no diseñar required checks alrededor de workflows que puedan omitirse por filtros y quedarse sin un resultado utilizable para la regla.

## 14. Definition of Done del ruleset

- [ ] esta PR ha producido al menos una ejecución real del nuevo context;
- [ ] el context exacto se ha verificado en GitHub;
- [ ] ruleset `main-production-integrity` creado;
- [ ] PR obligatoria para `main`;
- [ ] force push bloqueado;
- [ ] branch deletion bloqueado;
- [ ] required status checks activos;
- [ ] Required merge gate seleccionado;
- [ ] Public artifact contract seleccionado o decisión explícita documentada de consolidación;
- [ ] Sitewide Reflow seleccionado;
- [ ] Pa11y seleccionado;
- [ ] path-filtered workflows NO seleccionados accidentalmente;
- [ ] prueba de direct push rechazada;
- [ ] prueba de PR verde completada;
- [ ] bypass normal inexistente o restringido al propietario para emergencia real;
- [ ] fecha/config final registrada.
