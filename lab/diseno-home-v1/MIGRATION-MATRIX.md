# MATRIZ DE MIGRACIÓN EXACTA — `implementacion-web-2026` → V1

Estado: contrato de integración. No ejecuta cambios en GitHub.
Rama objetivo verificada: `implementacion-web-2026`
HEAD de referencia: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`
Regla: si cambia HEAD, revalidar esta matriz antes de aplicar parches.

## 1. Principio

La migración no se hace sustituyendo `styles.css`, `script.js` o `index.html` completos. Cada función/selector actual se clasifica como PRESERVAR, SUSTITUIR, RETIRAR CUANDO HAYA PARIDAD o FUERA DE HOME. El código viejo solo desaparece cuando el equivalente V1 ha pasado su prueba específica.

## 2. Shell y navegación

| Origen actual | Función actual | Destino V1 | Decisión | Condición para retirar legacy | Prueba obligatoria |
|---|---|---|---|---|---|
| `index.html .site-header` | cabecera sticky global | `.site-header` V1 + `.site-header__inner` | SUSTITUIR markup/estilos, no la tarea | shell V1 montado en Home y una interna | teclado, 320, 200%, landscape, scroll |
| `.brand`, `.brand-mark`, `.brand-text` | identidad + vuelta al inicio | `.brand`, `.brand__name`, `.brand__role` | SUSTITUIR presentación; PRESERVAR enlace/identidad | logo/imagen ya no necesarios para reconocimiento | test sin logo + focus + enlace `/` |
| `.site-nav` | navegación desktop | `.primary-nav` | SUSTITUIR presentación | rutas principales accesibles sin Explorar | teclado + coarse pointer + no-JS |
| `.nav-toggle` + bloque `Mobile nav` de `script.js` | menú móvil | shell móvil V1 responsive sin drawer en Home lab | RETIRAR CUANDO HAYA PARIDAD | navegación principal cabe/recompone en 320/390 y no necesita menú oculto | 320/390 + zoom + orientación |
| IIFE `GLOBAL EXPLORE MENU` | inyecta botón/panel Explore en `.site-nav` | `<button data-explore-open>` + `<dialog data-explore-dialog>` | SUSTITUIR | dialog V1 probado y disponible en shell global | Escape, retorno foco, backdrop, tab order, no-JS |
| `.explore-nav/.explore-panel` | panel custom | `.explore-dialog` | RETIRAR tras reemplazo | no quedan dos Explore simultáneos | DOM: 1 trigger + 1 dialog |
| footer sitemap injection IIFE | añade `/mapa-del-sitio/` por JS | footer HTML estable | CONSOLIDAR | todas las plantillas llevan enlace estático donde corresponda | no-JS + broken links |
| `.mobile-bottom-nav` IIFE | navegación fija móvil con 5 acciones | ninguna por defecto V1 | RETIRAR tras QA | shell/cartografía permiten llegar a tareas sin barra fija | task test móvil + safe-area |
| `.back-to-top` IIFE | volver arriba | no Home V1 por defecto | FUERA DE HOME | Home no demuestra necesidad | recorrido móvil/desktop |
| `syncHashScroll()` | corrige anclas tras load | comportamiento nativo + `scroll-margin` | PRESERVAR SOLO SI SIGUE HACIENDO FALTA | hash funciona sin doble salto en shell V1 | deep-link anchors + Back |

## 3. Home

| Origen actual | Función | Destino V1 | Decisión | Nota |
|---|---|---|---|---|
| `.hero.home-hero-launch` | hero de identidad/lanzamiento | `.home-hero` | SUSTITUIR | conservar hechos/copy SEO útil; no copiar composición legacy |
| `.hero-bg` + `manecillas-hero-bg.webp` | fondo visual full hero | superficies V1 + media real como objeto | DESCARTAR COMO GRAMÁTICA V1 | no background cinematográfico obligatorio |
| `.hero-content` | identidad + lead + acciones | `.home-hero__copy` | SUSTITUIR composición | H1/obra/fecha siguen en HTML |
| `.hero-author-photo` | retrato + mockup | `.hero-media` con retrato + cubierta plana | SUSTITUIR | portada plana oficial; mockup 3D no es V1 |
| `.hero-book-peek-img` / `manecillas-book-mockup.webp` | peek 3D | `.hero-cover` con portada plana | RETIRAR EN V1 | View Transition futura usa cubierta plana inequívoca |
| `.hero-actions` con 3 CTA | conversión + newsletter + Samuel | una `.primary-action` + rutas en cartografía/río | REDUCIR | no tres CTA hermanos en hero |
| `.trust-strip` | credenciales en cards | ledger/río editorial según contenido real | RECOMPONER | no cards uniformes |
| `.creds-strip` | cifras/credenciales | señales editoriales/ledger | RECOMPONER | evitar KPI strip corporativa |
| `.start-here-section/.start-grid/.start-card` | tres accesos | `.cartography` | SUSTITUIR | mapa/rutas reemplaza grid de cards |
| secciones extensas Samuel/Sobre mí/Proyectos en Home | contenido profundo | `.editorial-river` + destinos internos | REDUCIR EN HOME, NO BORRAR DEL SITIO | el contenido migra a páginas propias/enlaces; SEO se preserva según snapshot |
| `.sigueme-section#newsletter` | newsletter real | `.newsletter` V1 | SUSTITUIR SOLO UI | backend/IDs/source contract se preservan al integrar |

## 4. Newsletter y analytics — NO ROMPER

| Origen actual | Contrato | Destino V1 | Decisión | Gate |
|---|---|---|---|---|
| `NEWSLETTER_CONFIG.endpoint` | `subscribe.davidpd89.workers.dev` | mismo backend | PRESERVAR | nunca enviar desde staging |
| `STAGING_HOSTNAMES` / `IS_STAGING` | bloquea altas reales en preview | mismo contrato | PRESERVAR | staging devuelve copy de desactivado |
| `submitNewsletter(...)` | `{email, source}`; IDs por página | adapter V1 o binding equivalente | PRESERVAR FUNCIÓN | probar invalid/GDPR/staging/success/duplicate/error |
| `newsletter-form-home`, `nl-email-home`, `nl-gdpr-home`, `nl-status-home` | hooks actuales Home | preferir conservar IDs durante primera migración | PRESERVAR EN H2 | reduce riesgo de backend/eventos |
| `source: "home"` | atributo SOURCE de Brevo | mismo valor | PRESERVAR | Worker whitelist |
| `_gcEvent("newsletter-home", ...)` | evento GoatCounter | misma semántica o migración documentada | PRESERVAR | comprobar un solo evento |
| loader GoatCounter | pageviews/eventos | fuera del lab; producción conserva | PRESERVAR | no doble carga |
| Metricool loader | analytics actual | fuera del lab; producción conserva salvo decisión separada | PRESERVAR | privacidad/CSP |
| popup email IIFE | popup contextual en rutas sin inline form | no pertenece al lab Home | FUERA DE HOME | Home sigue excluida |

## 5. Funciones globales no pertenecientes al rediseño Home

No tocar al migrar Home salvo que un cambio de shell rompa su selector: quiz Noveris; `.copy-btn`; reading progress opt-in; FAQ legacy; `dp:analytics`; herramientas; email obfuscation; service worker; share/copy específicos; lógica de retailers.

Cada una se reaudita al migrar su familia. No se elimina porque «el nuevo diseño no la usa».

## 6. CSS legacy — frontera exacta

### No importar al lab

- `/styles.css`.
- `/assets/manecillas-extras.css`.

### No borrar todavía de la rama

Ambos siguen siendo consumidores de páginas actuales. El proceso correcto es:

1. introducir CSS V1 namespaced/aislado;
2. migrar Home;
3. migrar Manecillas piloto;
4. medir selectores legacy todavía consumidos;
5. eliminar por bloques solo cuando el inventario dé cero consumidores.

### Patrones legacy que V1 no debe copiar

`color-scheme:dark` global; fondos con múltiples gradientes; grid decorativa global; blur/glass de header como firma; `border-radius:999px` en botones/nav; shadow scale de cards; lift hover; CTA con gradiente; trust/start/review cards uniformes; colores hex históricos de Manecillas embebidos en componentes.

## 7. Media

Usar directamente los assets ya presentes en la rama objetivo:

- `/assets/portada-las-manecillas-del-recuerdo-320.webp`
- `/assets/portada-las-manecillas-del-recuerdo-512.webp`
- `/assets/portada-las-manecillas-del-recuerdo-768.webp`
- `/assets/portada-las-manecillas-del-recuerdo-1024.webp`
- `/assets/david-porto-foto-portada-sinfondo.webp` como retrato candidato hasta Gate 30.

No crear `/assets/las-manecillas/` en el repo. Las copias de esa carpeta en Drive son solo respaldo/procedencia.

## 8. Rutas

Verificadas en `implementacion-web-2026`: Manecillas, Samuel, Autor, Cuaderno, Herramientas, Prensa y Eventos. `/herramientas/` está en sitemap y su hub declara 17 utilidades.

Estado Jaula: la ruta aún no existe en `implementacion-web-2026`, pero el contenido mínimo ya está autorizado y definido en `book-jaula.html` + `JAULA-PUBLIC-SPEC.md` + `data/jaula-preservation.json`. En lab el nodo sigue protegido mientras el target branch no tenga la ruta; el siguiente paso es crearla en staging y desbloquear promoción únicamente tras 200 + preservación + SEO/schema + cobertura de navegación.

## 9. Orden de parche cuando se autorice GitHub

H0. Revalidar HEAD y ejecutar `scripts/validate_lab.py`.

H1. Copiar solo `/lab/diseno-home-v1/` a `implementacion-web-2026`; mantener `noindex`, fuera de sitemap/nav. Verificar que `.assetsignore` permite servir el lab únicamente en staging.

H2. Ejecutar A/B y QA. No tocar Home pública.

H3. Elegir variante. Crear capa V1 production-ready namespaced; conservar `<head>`, JSON-LD, forms y analytics actuales.

H4. Migrar shell y Home por bloques. Retirar legacy únicamente contra esta matriz.

H5. Migrar Manecillas como primera interna. Solo entonces empezar limpieza de `manecillas-extras.css` y selectores globales legacy.

## 10. Stop conditions

Detener integración si ocurre cualquiera:

- HEAD cambió y no se reauditó;
- aparecen dos menús Explore;
- el newsletter deja de usar `source:"home"` o puede enviar desde staging;
- se pierde canonical/schema/OG/headings/texto útil;
- `/donde-empieza-la-jaula/` sigue 404 y el nodo se habilita en producción;
- una regla V1 requiere `!important` masivo para ganar a `styles.css`;
- se carga legacy CSS dentro del lab;
- una función global desaparece sin prueba de paridad;
- mobile necesita recuperar la bottom nav solo porque la nueva arquitectura no permite encontrar destinos.



## POLÍTICA DE DRIFT DE RAMA — 20/08/2026

Último HEAD auditado para este paquete: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

Este SHA es una baseline informativa, no un bloqueo rígido. Antes de cualquier integración se compara este HEAD con el HEAD actual de `implementacion-web-2026`. Solo se reabre una decisión V1 si el delta toca archivos/contratos relevantes para esa decisión. Cambios aislados de CI, herramientas u otras familias no obligan a rehacer Home o Libro. `main` no es destino de integración.


## DELTA MANECILLAS

| Legacy | Contrato que preservar | V1 | Acción | Gate |
|---|---|---|---|---|
| `submitNewsletter(..., "manecillas")` | payload `email + source` | `data-newsletter-source="manecillas"` + binding productivo existente | PRESERVAR SOURCE / CAMBIAR SOLO COPY | staging no envía; source exacto |
| success copy «Te avisaré… disponible» | verdad editorial permanente | «Te has suscrito correctamente. Recibirás las novedades de Las manecillas del recuerdo y de David Porto Díaz.» | SUSTITUIR COPY | no promesa automática |
| género visible actual | `Novela coral · Ficción especulativa` | ledger editorial | PRESERVAR | Book Gate 3 |
| enlaces comerciales pendientes | solo destinos verificados | `#disponibilidad` + CTA principal cuando exista | GATE | cero retailer inventado/404 |

### Manecillas — compatibilidad pública añadida

| Área legacy | Destino V1 | Retirada | Test obligatorio |
|---|---|---|---|
| `#aviso` | `book-meta-ledger#aviso` | No retirar sin decisión explícita de alias/redirect | hash directo resuelve y no queda tapado por sticky header |
| `#muestra` | alias dentro de `#fragmento` | Mantener alias aunque cambie el id interno | `validate_lab.py` + browser hash |
| `#sinopsis-editorial` | alias dentro de `#contexto` | Mantener alias | `validate_lab.py` + browser hash |
| `#newsletter-manecillas` | newsletter V1 | Mantener | source `manecillas` + status accesible |
| `manecillas-quote-band` | `.book-dedication` | Retirar al migrar | dedicatoria exacta una vez; sin quote-band |
| CTA compra sin retailers | `Recibir novedades` | Cambiar solo tras URLs verificadas | commercial gate pending/active |

## DELTA REGISTRY + NAVIGATION — CONTRATO DE INTEGRACIÓN 21/08/2026

La rama objetivo ya contiene tres autoridades nuevas que el lab **no sustituye**:

| Archivo/contrato real | Función | Estado V1 | Regla de migración |
|---|---|---|---|
| `data/content-registry.json` | inventario canónico de contenido y discoverability | PRESERVAR + EXTENDER | cualquier ruta nueva se declara aquí con estado real; no duplicar otro registro paralelo |
| `data/navigation.json` | superficies visibles de navegación | PRESERVAR + EXTENDER | shell/Explorar/footer/Home deben resolver IDs canónicos; no hardcodear una segunda taxonomía divergente |
| `scripts/check-navigation-coverage.py` | sitemap ↔ registry ↔ herramientas ↔ navegación | PRESERVAR / GATE | debe pasar después de cualquier alta/baja/cambio de discoverability |
| `data/ux-feature-retention.json` | decisión PRESERVE/MOVE/SCOPE/REPLACE/RETIRE de funciones legacy | PRESERVAR | usarla antes de retirar JS/UI existente; no decidir por limpieza visual |
| `.github/workflows/content-index-check.yml` | CI de cobertura | PRESERVAR | incorporar el nuevo sistema sin desactivar el check para hacer pasar una migración |

### Jaula — secuencia exacta sin fuga pública

**J0 — estado actual:** la ruta no existe; no hay entrada `work-jaula` en el registry ni referencia navegable. Correcto.

**J1 — al crear la ruta en staging:** crear `donde-empieza-la-jaula/index.html` desde `book-jaula.html` + contenido canónico y añadir al registry una entrada equivalente a:

```json
{
  "id": "work-jaula",
  "url": "/donde-empieza-la-jaula/",
  "label": "Dónde empieza la jaula",
  "shortLabel": "Dónde empieza la jaula",
  "type": "work",
  "territory": "obras",
  "parentId": "works-hub",
  "hubId": "works-hub",
  "status": "noindex",
  "discoverability": "contextual",
  "searchIndex": false,
  "sitemap": false,
  "footerEligible": false,
  "audience": ["reader"],
  "jobs": ["conocer-obra", "leer-fragmento"],
  "sourceFile": "donde-empieza-la-jaula/index.html"
}
```

No añadirla aún a `data/navigation.json`: el checker exige que toda referencia navegable resuelva a contenido `public`.

**J2 — gates de staging:** ejecutar, como mínimo:

- `python scripts/check_preservation.py --jaula donde-empieza-la-jaula/index.html`;
- `python scripts/check-navigation-coverage.py`;
- HTML/schema/links/a11y/browser QA;
- HTTP 200 real de la ruta;
- comprobación de que sigue fuera de sitemap y navegación pública.

**J3 — promoción pública, solo tras aprobación humana:** cambiar el contrato Jaula a `productionAllowed:true`; entonces actualizar de forma atómica registry + sitemap + la superficie de navegación aprobada. El primer commit público no puede dejar alguno de esos tres sistemas desincronizado.

El lab puede mostrar Jaula como destino **planned/no-link** para probar composición; ese estado visual no se exporta a `navigation.json` mientras la entrada sea no pública.
