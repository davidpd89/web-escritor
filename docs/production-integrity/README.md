# Production Integrity Gate 2026

**Estado:** IMPLEMENTACIÓN + RUNBOOK · PR dedicada  
**Corte de evidencia:** 2026-08-27  
**Base auditada:** `main@b3db6b63f8993ecd88493139f20e7622ff4a6261`  
**Objetivo:** hacer que la calidad ya construida en el repositorio sea una barrera real entre un cambio y producción.

## 1. Decisión

La mayor necesidad actual del proyecto no es otra funcionalidad, otro bloque SEO ni otra capa de diseño. Es **integridad de release**.

El repositorio tiene una cobertura de QA excepcionalmente amplia para una web estática: artifact boundary, content indexes, navegación, discoverability, CSP, runtime scoping, Lighthouse, Pa11y, reflow, cross-engine, PWA, herramientas, privacidad, contratos editoriales, asistente, Manecillas, analytics y enlaces externos.

El problema es de gobernanza y cierre del ciclo:

```text
cambio -> PR -> checks -> merge -> build -> deploy -> producción verificada
```

Hoy esa cadena no está garantizada de extremo a extremo.

### Evidencia determinante del 27/08/2026

- `main` está `protected:false`.
- No existe ningún repository ruleset (`[]`).
- No hay required status checks activos.
- El HEAD auditado `b3db6b6...` entró por push directo a `main`, sin PR.
- Ese push solo disparó dos workflows asociados al SHA: `Editorial facts check` y `Deploy Pages`.
- `Deploy Pages` construyó correctamente el artifact allowlist-first y desplegó correctamente.
- El workflow terminaba después de `actions/deploy-pages`; no comprobaba el dominio público una vez publicado.
- El smoke existente estaba dedicado únicamente a staging y se ejecutaba manualmente/programado, no como verificación del deploy de producción.

Esto crea una asimetría peligrosa: el proyecto ha invertido mucho en detectar regresiones, pero todavía permite un camino que evita gran parte de esos detectores.

## 2. Qué implementa esta PR

### 2.1 Check universal de merge

Nuevo workflow:

`/.github/workflows/required-merge-gate.yml`

Propiedades:

- se ejecuta en **toda PR hacia `main`**;
- no tiene `paths:` ni `paths-ignore:`;
- produce evidencia de release estática;
- comprueba shell generado;
- comprueba sitemap generado;
- comprueba proyección pública de hechos editoriales;
- comprueba paridad del índice del asistente;
- ejecuta regresiones de frontera pública;
- ejecuta regresiones del publication gate;
- comprueba `.assetsignore` generado;
- construye el artifact público real;
- vuelve a inspeccionar el artifact construido.

Su nombre estable de job es:

`Required merge gate`

Este es el candidato principal para convertirse en required status check después de demostrar una primera ejecución verde.

### 2.2 Smoke HTTP reutilizable staging/producción

`tests/test-staging-smoke.mjs` se mantiene con el nombre existente para no romper llamadas históricas, pero pasa a tener contrato genérico:

```text
SITE_BASE_URL     -> destino genérico nuevo
STAGING_BASE_URL  -> compatibilidad legacy
SMOKE_LABEL       -> STAGING / PRODUCTION / otro
CANONICAL_ORIGIN  -> autoridad canonical esperada
```

También conserva `STAGING_SMOKE_INSECURE_TLS` solo por compatibilidad y añade el nombre neutral `SMOKE_INSECURE_TLS`.

Producción **nunca** activa TLS inseguro en el workflow.

El smoke comprueba:

- rutas públicas críticas con `200`;
- `<title>` no vacío;
- JSON-LD parseable en Home y Manecillas;
- canonical exacto esperado en Home y Manecillas;
- `robots.txt`, `sitemap.xml` y `llms.txt` disponibles y reconocibles;
- rutas técnicas/internas/gated con `404`.

La lista negativa incluye ahora, además de la histórica:

- `/docs/`;
- `/qa/`;
- `/lab/`;
- `/migrations/`;
- Workers fuente;
- Wrangler;
- `package*.json`;
- Lighthouse config;
- `press-kit/package-manifest.json`;
- la ruta gated `donde-empieza-la-jaula`.

### 2.3 Verificación real después de Deploy Pages

`.github/workflows/deploy-pages.yml` incorpora:

```text
build -> deploy -> verify-production
```

`verify-production`:

- espera a que `deploy` termine correctamente;
- hace checkout del mismo SHA;
- ejecuta el smoke contra `https://davidportodiaz.com`;
- usa TLS normal/estricto;
- permite hasta 3 intentos completos, separados 15 s, para absorber una convergencia breve de Pages/CDN;
- si el error persiste, el workflow de deploy queda rojo;
- no convierte el fallo en warning;
- no hace rollback automático.

## 3. Qué NO hace esta PR

No activa todavía un ruleset en GitHub.

Motivo: activar protección antes de que el nuevo check exista y haya ejecutado correctamente puede crear un bloqueo administrativo evitable. Primero debe existir la PR, aparecer el contexto real de check y quedar verde. Después se configura el ruleset con ese nombre exacto.

Tampoco:

- despliega manualmente;
- cambia DNS;
- cambia Cloudflare;
- toca Workers live;
- crea secretos;
- activa reviewers obligatorios imposibles para un repositorio de un solo mantenedor;
- exige commits firmados de golpe;
- activa auto-rollback;
- transforma todos los 30+ workflows en required checks;
- elimina QA existente;
- rediseña páginas;
- cambia hechos editoriales o estado comercial de Manecillas.

## 4. Por qué no atacar otra cosa antes

### Diseño/UX

El proyecto sigue teniendo recorrido visual, y la PR #114 ya concentra toolkit/diseño/QA visual. Pero los cambios visuales frecuentes aumentan precisamente la necesidad de una puerta de release segura.

### SEO / IA

Search Console, AI discoverability y machine-readable ya han recibido auditorías profundas recientes. El siguiente salto no es documentar más señales: es asegurar que cualquier corrección llegue a producción de forma verificable y no pueda saltarse QA.

### Brevo / CRM

Tiene backlog operativo real, pero no protege el sitio entero. Además las acciones live requieren configuración/credenciales externas.

### Limpieza del repo

La PR #115 la está abordando por separado. Es importante para mantenibilidad, pero no tiene el mismo riesgo inmediato que un push directo capaz de desplegar producción sin la batería de PR QA.

### Nuevas funcionalidades

Antes de ampliar superficie, hay que hacer confiable la cadena que publica cualquier superficie nueva.

## 5. Modelo de confianza resultante

Después de implementar esta PR y activar el ruleset recomendado:

```text
                     ┌─────────────────────────┐
                     │ cambio en rama de trabajo│
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │ PR obligatoria a main   │
                     └────────────┬────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
 Required merge gate       Sitewide Reflow         Accessibility
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  ▼
                        merge permitido
                                  │
                                  ▼
                  build allowlist-first exacto
                                  │
                                  ▼
                       Deploy GitHub Pages
                                  │
                                  ▼
                  smoke de producción real
                                  │
                     PASS ────────┴──────── FAIL
                      │                         │
                      ▼                         ▼
                release sano             incidente visible
                                         freeze + revert
```

## 6. Autoridades de esta iniciativa

1. `README.md` — decisión y mapa.
2. `01-ESTADO-RIESGO-Y-DECISION.md` — evidencia y threat model operacional.
3. `02-RULESET-MAIN-Y-CHECKS-OBLIGATORIOS.md` — configuración exacta recomendada de GitHub.
4. `03-DEPLOY-VERIFY-ROLLBACK-Y-OPERACION.md` — runbook de deploy e incidente.
5. `04-BACKLOG-CLAUDE-FUENTES-Y-DOD.md` — siguientes tareas, fuentes oficiales y Definition of Done.

## 7. Principio central

**Un check que existe pero puede saltarse no es un gate de producción.**

Y, simétricamente:

**un deploy que termina verde antes de consultar el dominio público acredita que GitHub publicó un artifact, no que la web servida esté sana.**

Esta PR cierra ambos huecos sin reconstruir la infraestructura de QA que ya funciona.
