# 01 — Estado real, modelo de riesgo y decisión de prioridad

Fecha de corte: **27/08/2026**  
Snapshot auditado: `main@b3db6b63f8993ecd88493139f20e7622ff4a6261`

## 1. Resumen

El riesgo dominante no es que falten comprobaciones. Es que **la relación entre comprobaciones, merge y despliegue no está gobernada**.

El sistema actual tiene tres capas fuertes:

1. validación fuente/CI;
2. builder allowlist-first;
3. GitHub Pages deployment.

Pero antes de esta PR faltaban dos propiedades de cierre:

- no era obligatorio pasar por PR/checks antes de modificar `main`;
- una vez desplegado, no había una prueba automática sobre el dominio público.

## 2. Evidencia de repositorio

### 2.1 `main` sin protección

La API de GitHub devolvió para `main`:

```json
{
  "protected": false,
  "protection": {
    "enabled": false,
    "required_status_checks": {
      "enforcement_level": "off",
      "contexts": [],
      "checks": []
    }
  }
}
```

Además, el endpoint de repository rulesets devolvió:

```json
[]
```

Por tanto no hay que inferir que «como usamos PR normalmente, main está protegido». No lo está.

### 2.2 El caso real del último HEAD

El commit:

`b3db6b63f8993ecd88493139f20e7622ff4a6261`

entró como push a `main` y no aparece asociado a una PR.

El cambio incluía piezas capaces de producir regresión visible/runtime:

- avatar de Home;
- nueva social card;
- cambio de versión del service worker;
- copy de instalación.

Consultar Actions por ese SHA devolvió únicamente dos runs:

- `Editorial facts check`;
- `Deploy Pages`.

Ambos fueron verdes.

Lo importante no es que ese commit esté roto. No se ha demostrado que lo esté. El hallazgo es que **un cambio de ese tipo tuvo un camino válido hasta producción sin ejecutar como barrera la mayor parte de la QA que sí habría aparecido en una PR**.

### 2.3 El despliegue actual sí construye el artifact correcto

`deploy-pages.yml` ya hace bien varias cosas críticas:

1. checkout;
2. Python 3.12;
3. `build-public-dist.py --out .preview-dist`;
4. `build-public-dist.py --check-contents --out .preview-dist`;
5. `.nojekyll`;
6. upload del artifact exacto;
7. `actions/deploy-pages@v4`.

Esto es una mejora estructural muy importante frente a publicar el árbol bruto del repositorio.

No se debe sustituir ni degradar.

### 2.4 Hueco post-deploy

Antes de esta PR el último paso real era:

```text
Deploy to GitHub Pages -> success
```

Eso demuestra que el servicio de deployment aceptó/publicó el artifact. No demuestra por sí solo:

- que `davidportodiaz.com` responde 200;
- que el custom domain sirve el release esperado;
- que las rutas públicas críticas responden;
- que el CDN/DNS no está sirviendo una topología inesperada;
- que las rutas internas siguen ausentes por HTTP;
- que canonical y machine-readable siguen visibles;
- que un problema de propagación/routing no dejó producción parcialmente rota.

## 3. Cobertura existente que NO hay que reconstruir

La decisión de priorizar release integrity se apoya precisamente en que ya existe una base extensa.

### Artifact / publicación

- `public-artifact-contract.yml`;
- `build-public-dist.py` allowlist-first;
- `.assetsignore` generado/contrastado;
- `test-public-artifact-contract.py`;
- `test-staging-publication-gate.py`.

### Contenido / autoridad

- content indexes;
- machine authority;
- editorial facts;
- proyección pública de hechos;
- sitemap/feed/shell builders;
- assistant registry parity;
- recommendations evidence.

### UX / navegador

- Sitewide Reflow QA;
- Cross-engine smoke;
- múltiples suites browser por familia;
- navegación/Explorar;
- herramientas;
- Cuaderno;
- identidad;
- Manecillas/Samuel.

### Accesibilidad / performance

- Pa11y;
- Lighthouse;
- responsive image gate;
- image format ladder;
- CLS/reflow gates.

### Seguridad / privacidad

- CSP;
- runtime scoping;
- private tools audit;
- newsletter/Worker contracts;
- no-store/origin/rate-limit contracts;
- public artifact isolation.

### Descubrimiento

- broken links/Lychee;
- internal graph;
- navigation coverage;
- global discoverability;
- AI discoverability;
- social-card checks.

La intervención correcta no es duplicar esas suites en otros treinta scripts. Es hacer que la promoción a `main` dependa de una capa pequeña, universal y no saltable.

## 4. Modelo de riesgo

### R1 — Direct push a producción

**Probabilidad actual:** real/demostrada.  
**Impacto:** alto.  
**Motivo:** `main` dispara deploy.

Un error pequeño en HTML/CSS/JS/PWA puede entrar sin PR y llegar al deployment.

### R2 — «CI verde» entendido de forma incorrecta

Un repositorio con muchos checks puede producir falsa confianza si no existe una política explícita de cuáles son obligatorios y cuándo corren.

Un workflow con `paths:` puede ser excelente para su área, pero no es un buen candidato a required check universal si puede no ejecutarse.

### R3 — Deploy success ≠ production health

El despliegue puede completar mientras el custom domain tiene un problema temporal o permanente.

Sin post-deploy verify, el incidente solo lo descubre una persona/crawler/usuario después.

### R4 — Superficie privada publicada accidentalmente

El builder reduce mucho este riesgo. Falta demostrarlo también desde fuera, sobre el dominio servido, porque el HTTP final es la autoridad de exposición.

### R5 — Stale release / stale asset

El service worker ya ha demostrado ser capaz de conservar bytes antiguos hasta un cambio de cache namespace. Hay más capas de caché fuera del repositorio.

Un smoke no resuelve toda la coherencia de caché, pero añade una señal de disponibilidad/contrato al release real.

### R6 — Gate tan complejo que se evita

Una mala solución sería exigir 30 contexts inestables y terminar animando a bypasses.

Por eso se diseña:

- un **required merge gate universal**;
- un conjunto pequeño de gates universales adicionales ya maduros;
- suites especializadas que siguen apareciendo por cambios relevantes;
- un runbook de bypass de emergencia excepcional y auditable, no el camino normal.

## 5. Matriz de prioridad frente a otras iniciativas

| Frente | Valor | Urgencia pre-03/09 | Cobertura actual | Riesgo si se pospone | Decisión |
|---|---:|---:|---:|---:|---|
| Integridad de release | Muy alto | Muy alta | Parcial | Muy alto | **P0 ahora** |
| Limpieza repo | Medio/alto | Media | PR #115 | Bajo/medio inmediato | seguir separada |
| Diseño/UX | Alto | Alta | muy trabajado + #114 | Medio | continuar tras gate |
| SEO técnico | Alto | Media | fuerte | Medio | medir, no reinventar |
| IA discoverability | Alto | Media | plan maestro reciente | Medio | ejecutar backlog selectivo |
| Brevo/CRM | Alto negocio | Media | plan + runtime base | Medio | cerrar live config aparte |
| Nuevas herramientas/features | Variable | Baja | amplia superficie existente | aumenta riesgo | **no ampliar ahora** |

## 6. Principios técnicos elegidos

### 6.1 No depender de un único mega-script opaco

El required gate reutiliza autoridades existentes y produce evidencia.

### 6.2 No hacer required un workflow que pueda saltarse por `paths:`

Si el context no se crea para una PR, algunas configuraciones de required checks pueden dejar el merge pendiente indefinidamente. Los required checks base deben ser universales.

### 6.3 No confundir smoke con QA completa

El production smoke es deliberadamente estrecho:

- HTTP;
- rutas críticas;
- canonical;
- machine files;
- ausencia de clases privadas.

No sustituye Lighthouse, Pa11y, Playwright ni revisión visual.

### 6.4 No auto-rollback en la primera versión

Un rollback automático puede empeorar un incidente si:

- el fallo es de DNS/CDN externo;
- el release anterior ya no es compatible con una configuración live;
- el smoke tiene un falso positivo;
- existe una migración backend no reversible.

Primero: detectar bien, congelar, diagnosticar y revertir explícitamente.

### 6.5 No activar branch protection a ciegas desde el mismo cambio

La protección es P0, pero debe configurarse **después** de que el nuevo context exista en GitHub y haya pasado al menos una PR real. Así se evita seleccionar un nombre incorrecto o bloquear `main` con un check que GitHub todavía no conoce.

## 7. Condición para cambiar de prioridad

Después de cerrar esta iniciativa, la siguiente prioridad puede volver a diseño/UX y launch readiness de Manecillas.

No debería abrirse otra gran iniciativa transversal antes de que se pueda responder “sí” a estas preguntas:

1. ¿Puede una modificación normal llegar a `main` sin PR? → **No**.
2. ¿Hay al menos un required check universal que siempre aparezca? → **Sí**.
3. ¿El artifact exacto de Pages se construye con allowlist? → **Sí**.
4. ¿Tras deploy se consulta automáticamente producción? → **Sí**.
5. ¿Un leak técnico HTTP vuelve rojo el release? → **Sí**.
6. ¿Existe runbook de rollback con SHA y verificación posterior? → **Sí**.

Hasta entonces, optimizar más capas del producto aumenta la superficie sobre una cadena de release todavía incompleta.
