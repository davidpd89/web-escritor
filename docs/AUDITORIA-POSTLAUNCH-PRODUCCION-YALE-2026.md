# Auditoría post-lanzamiento 2026 — producción, UX, diseño y QA

**Estado:** backlog ejecutable. Esta rama/PR **no modifica producción** ni propone un rediseño nuevo. Documenta comprobaciones y correcciones pendientes después del lanzamiento.

**Base auditada al abrir este documento:** `main@6445ae8167d9931a272e52838fe4e00ef5fbba52` (26/08/2026).

**Objetivo:** dejar la web publicada estable, verificable y coherente. No añadir funciones por añadir. Si una comprobación ya está cubierta y verde, no duplicarla. Si aparece un bug reproducible, corregirlo en una PR pequeña con prueba de regresión.

---

## 0. Qué NO hay que rehacer

El release actual ya tiene una cobertura técnica muy amplia. En el HEAD previo al último lote post-launch pasaron en ejecución real, entre otros:

- Lighthouse CI.
- Pa11y / accesibilidad automática.
- Cross-engine Chromium, Firefox y WebKit.
- Sitewide Reflow.
- Check external links / Lychee.
- Content indexes y grafo interno.
- Global discoverability / machine authority.
- CSP public shell.
- Runtime scoping, focus, reduced motion y back-to-top.
- PWA offline.
- Tool engines, tools browser y publishing tools.
- Cuaderno, recomendaciones, identidad, privacidad, ferias y Explore.
- Manecillas funnel, fragmentos y paridad de contenido.
- Image format ladder.
- Analytics taxonomy.
- Assistant hardening y copy QA.

Por tanto, esta auditoría no debe convertirse en una excusa para reconstruir Home, Libro, Cuaderno, Herramientas o Autor. La prioridad es **producción real + coherencia entre familias + prevención de regresiones**.

---

## 1. Cómo se usa Yale como referencia

No se pretende copiar la identidad visual de Yale ni convertir davidportodiaz.com en una web universitaria. Yale se usa como referencia por su disciplina de sistema:

1. **Consistencia visual y de interacción:** una misma función debe mantener etiqueta, ubicación, aspecto y comportamiento. La consistencia reduce decisiones innecesarias y permite que el usuario forme expectativas.
2. **Navegación simple:** evitar capas innecesarias, demasiadas opciones equivalentes y rutas que obligan a reaprender la arquitectura en cada página.
3. **Diseño por sistema, no por página:** colores, tipografía, espaciado y componentes salen de un sistema común; cada familia puede tener composición propia sin parecer otra web.
4. **Accesibilidad integrada:** WCAG AA, teclado, zoom, contraste y pruebas manuales representativas además de validadores automáticos.
5. **QA de lanzamiento real:** Yale recomienda comprobar enlaces, formularios y redirects en el frontend real después de cambios de contenido/lanzamiento.
6. **Regresión visual:** el YaleSites Design System utiliza pruebas de regresión visual (Percy) junto a tests automáticos; la lección aplicable aquí es congelar contratos visuales representativos y detectar drift antes de publicar.

Fuentes oficiales de referencia:

- https://yalesites.yale.edu/development/design-system
- https://yalesites.yale.edu/design/accessibility-guidelines
- https://yalesites.yale.edu/design/color
- https://yalesites.yale.edu/content-management/yale-site-content-administrators-checklist
- https://usability.yale.edu/web-accessibility/accessibility-yale/guidelines
- https://usability.yale.edu/web-accessibility/articles/visual-consistency

**Regla:** Yale sirve para justificar principios y criterios de aceptación, no para copiar HTML, CSS, colores, tipografías o composición.

---

# P0 — comprobar producción real

## P0.1 — Smoke test de PRODUCCIÓN, no solo staging

### Hallazgo

Existe `tests/test-staging-smoke.mjs` y `.github/workflows/staging-smoke-test.yml`, pero el workflow está orientado al preview de staging. Después de haber sustituido la web anterior, necesitamos la misma evidencia contra `https://davidportodiaz.com`.

### Implementación recomendada

Preferible **parametrizar el test existente** en vez de duplicarlo:

- `BASE_URL` configurable.
- modo `staging`: admite/comprueba las rutas internas que staging debe ocultar.
- modo `production`: mismas rutas públicas + denylist real.

Cobertura mínima pública:

- `/`
- `/libros/`
- `/las-manecillas-del-recuerdo/`
- `/libros/samuel-entre-mundos/`
- `/cuaderno/`
- un artículo real del Cuaderno
- `/herramientas/`
- al menos 3 herramientas con motores distintos
- `/autor.html`
- `/prensa.html`
- `/eventos.html`
- `/lectores-beta/`
- `/recomendaciones/`
- `/editoriales/`
- `/convocatorias/` si está registrada como pública
- `/mapa-del-sitio/`
- `/privacidad.html`
- `/accesibilidad/` si continúa como ruta pública
- una URL inexistente que deba resolver en 404
- `/robots.txt`, `/sitemap.xml`, `/llms.txt`, `/llms-full.txt`

Por cada HTML público:

- HTTP 200 esperado.
- `<title>` no vacío.
- canonical presente y del host correcto.
- no `noindex` cuando el registry la define indexable.
- JSON-LD parseable cuando exista.
- assets same-origin críticos sin 404.
- ninguna excepción JS no controlada durante carga.

### Criterio de aceptación

Una ejecución verde sobre el dominio público **después del deploy** y con evidencia por SHA.

---

## P0.2 — Verificar que material interno NO está publicado

### Motivo

Los checks de `build-public-dist.py` validan el artefacto, pero después de un cambio de mecanismo de publicación hay que demostrar el resultado final por HTTP.

### Denylist mínima a comprobar en producción

Derivarla de la autoridad actual (`build-public-dist.py`, `.assetsignore`, registry) y comprobar al menos:

- `/scripts/`
- `/tests/`
- `/data/`
- `/lecturas/`
- `/publicar-web/`
- `/herramientas/auditor-web/` si sigue clasificada interna
- fuentes/config de backend que no deban servirse
- `editorial-facts.json` si la arquitectura final establece que no es público
- cualquier ruta `PRIVATE/INTERNAL` o `GATED`

No asumir que un `noindex` equivale a privacidad: una ruta interna debe ser realmente inaccesible si ese es el contrato.

### Criterio de aceptación

Todas las rutas de denylist devuelven 404/403 según contrato y ninguna aparece en sitemap, navegación, buscador ni Explore.

---

## P0.3 — Crawl de enlaces DESPUÉS de hidratar JavaScript

### Hallazgo

Lychee ya cubre muy bien enlaces estáticos y está verde, pero Home, shell, Explore, algunas tarjetas y otros elementos se construyen/alteran con JS. Un crawler de ficheros no demuestra que el DOM final tenga todos los destinos correctos.

### Nuevo test propuesto

`qa/hydrated-link-crawl.mjs` o equivalente Playwright:

1. cargar cada ruta pública;
2. esperar al estado estable de shell/fuentes;
3. extraer todos los `<a href>` del DOM final;
4. resolver relativos/canonicals;
5. comprobar enlaces same-origin;
6. validar que los hashes apuntan a IDs existentes;
7. detectar `href="#"`, `javascript:void(0)` usados como navegación, destinos vacíos y enlaces invisibles/fuera de tab order cuando deberían ser accionables;
8. detectar un mismo CTA con etiquetas contradictorias según la página;
9. guardar reporte ruta → texto → destino.

### Criterio de aceptación

0 enlaces internos rotos en DOM hidratado y 0 anclas rotas.

---

## P0.4 — Formularios: canary real de frontend a backend

### Base Yale

El checklist de administradores de Yale recomienda probar formularios desde el frontend real, incluyendo campos obligatorios, mensajes de error, lógica condicional y automatizaciones/emails posteriores.

### Qué probar

- Newsletter global / Explore / popup si existen como superficies distintas.
- Formulario de lector beta.
- Flujo de autor/manuscrito si existe como formulario o CTA de contacto.
- Turnstile únicamente donde esté realmente activado.
- Cualquier formulario de contacto/prensa que siga público.

Para cada uno:

- email inválido;
- required vacío;
- consentimiento donde sea legalmente requerido;
- teclado móvil/inputmode;
- submit correcto;
- estado de loading;
- doble click / doble submit;
- error de red/backend;
- confirmación de éxito;
- recepción efectiva en Brevo/email/D1 según flujo;
- no duplicación de contacto/evento.

**No automatizar envíos reales a diario**. Usar test manual de release o un endpoint/cuenta de canary separada si se quiere automatizar.

---

## P0.5 — Las manecillas: gate comercial del 3/09

### Estado actual comprobado

`editorial-facts.json` mantiene `purchaseUrl: null`, de forma deliberada. Esto es correcto mientras no exista URL de compra verificada.

### Cuando exista la URL

- actualizar **una única fuente canónica**;
- ejecutar el mecanismo/script de transición ya existente si sigue siendo la autoridad;
- comprobar Home, header, `/libros/`, página de Manecillas, fragmentos y cualquier CTA relacionado;
- comprobar que no queda ningún placeholder de Samuel;
- activar `Offer`/schema comercial solo con URL/precio/disponibilidad reales;
- repetir hydrated link crawl + Manecillas funnel QA.

### Criterio de aceptación

No existe ninguna URL comercial inventada ni ningún CTA de Manecillas que termine en Samuel después de la activación.

---

## P0.6 — Cloudflare/DNS: verificar el estado REAL posterior al cutover

El último lote de `main` contiene cambios de Cloudflare/routing. No basta con tener docs/config en Git.

Comprobar desde red externa:

- apex `davidportodiaz.com` resuelve correctamente;
- `www` redirige al canonical previsto en **un solo salto**;
- HTTP → HTTPS en un salto;
- path y query se conservan;
- certificado válido;
- no hay loop GitHub Pages ↔ Cloudflare;
- DNS no mantiene registros antiguos/conflictivos;
- canonical HTML sigue siendo el apex;
- Worker routes no interceptan rutas que no les pertenecen.

Guardar salida de `dig/nslookup`, `curl -I` y navegador/DevTools.

---

## P0.7 — Protección de `main`

### Hallazgo confirmado el 26/08/2026

La API de GitHub devuelve actualmente:

- `main.protected = false`
- required status checks = off.

Para una web ya en producción esto permite que un push/merge accidental evite toda la batería de QA.

### Recomendación

Crear branch protection/ruleset para `main`:

- cambios por PR;
- impedir force-push/delete;
- exigir los gates esenciales, no necesariamente los 30+ jobs para cada typo;
- conjunto mínimo recomendado: content indexes, link/static integrity, Pa11y, reflow/cross-engine o un aggregate release gate, CSP/runtime y tests afectados por herramientas;
- permitir hotfix con procedimiento explícito, no desactivar protección.

### Criterio de aceptación

Un push directo normal a `main` no puede saltarse la revisión/gates definidos.

---

# P1 — UX y coherencia visual

## P1.1 — Regresión visual por snapshots (hueco real)

### Hallazgo

No se ha localizado una suite `visual regression` / `toHaveScreenshot` en el repo. Hay screenshots de QA y muchos asserts estructurales, pero no una comparación automática contra un baseline visual aprobado.

### Por qué importa

Es exactamente el hueco que permite errores tipo: una página carga bien, no tiene overflow y pasa accesibilidad, pero pierde el gutter, cambia la superficie, el header o el ritmo y deja de parecer parte de la misma web.

### Implementación propuesta

Preferencia: Playwright nativo `toHaveScreenshot` para no añadir un SaaS; Percy es válido si se prefiere infraestructura externa.

Baselines representativos, no todas las páginas:

- Home
- Obras
- Manecillas
- Samuel
- Autor
- Cuaderno
- un artículo largo
- Herramientas
- una herramienta de formulario
- una herramienta con preview/render
- Prensa
- Eventos
- Lectores beta
- Mapa del sitio
- Privacidad
- 404
- Asistente

Viewports mínimos:

- 390×844
- 768×1024
- 1440×900

Añadir 320 px y 844×390 como smoke específico si el coste es razonable.

Estabilizar capturas:

- esperar `document.fonts.ready`;
- desactivar/maskar contenido temporal/dinámico;
- `prefers-reduced-motion`;
- no exigir 0% de diferencia por antialiasing;
- revisar visualmente el baseline antes de aceptarlo.

### Criterio de aceptación

Una modificación de gutter/header/footer/tipografía/superficie dispara una diferencia visible antes de mergear.

---

## P1.2 — Contract test de diseño común

Crear un test de `getComputedStyle()` para las rutas representativas que compruebe, salvo excepciones declaradas:

- mismo `--page-gutter` efectivo;
- mismo `--layout-max`/ancho editorial por familia cuando corresponda;
- fondo/surface procedente de tokens;
- header común y altura/rules coherentes;
- footer común;
- tipografía de display/reading/UI correcta;
- color y grosor de reglas editoriales;
- focus-visible común;
- botones/links no redefinidos arbitrariamente;
- context bar consistente;
- line-height y ancho de lectura dentro del contrato.

**No obligar a que todas las páginas tengan la misma composición.** Libro, Cuaderno, Herramientas y Prensa pueden organizarse distinto; lo que no debe cambiar arbitrariamente es el lenguaje base.

---

## P1.3 — Scorecard manual “coherencia Yale” por familia

Usar Yale por su principio de consistencia, no por estética. Para cada vista representativa responder Sí/No:

1. ¿Reconozco en 2 segundos que sigo en davidportodiaz.com?
2. ¿Header, Explorar, footer y navegación contextual tienen el mismo comportamiento?
3. ¿Los márgenes laterales empiezan en la misma guía editorial?
4. ¿H1/H2/body/caption mantienen roles previsibles?
5. ¿Las líneas divisorias tienen el mismo peso/color?
6. ¿Botón primario/secundario/link se distinguen igual?
7. ¿Las tarjetas/superficies usan la misma lógica de borde/sombra/radio?
8. ¿El azul/acento significa lo mismo?
9. ¿Las imágenes respetan el mismo tratamiento (ratio/crop/caption)?
10. ¿En móvil el orden sigue siendo lógico sin bloques gigantes ni huecos absurdos?
11. ¿La página mantiene una acción principal clara en lugar de ofrecer 5 CTAs equivalentes?
12. ¿Volver/seguir/Explorar tienen etiquetas coherentes con el resto?

Guardar capturas 390 y 1440 junto al SHA auditado.

---

## P1.4 — Auditoría de navegación y carga cognitiva

Inspirada en la recomendación de Yale de simplificar menús y reducir capas.

Comprobar:

- nombre idéntico de territorios en header/Explorar/footer/mapa;
- `aria-current` o estado equivalente donde tenga sentido;
- no duplicar destinos con nombres que parezcan destinos distintos;
- Lectores beta: separar claramente “ser lector” de “enviar manuscrito” en todas las entradas;
- Obras: el hub debe ser la autoridad de las obras, aunque una ficha secundaria termine fuera;
- no esconder destinos públicos relevantes únicamente en footer;
- no convertir el menú en un inventario de toda la web: el mapa/Explorar pueden resolver profundidad.

---

## P1.5 — Auditoría visual de TODAS las rutas públicas, no solo muestras

Los tests pueden ser representativos; la revisión humana final debe recorrer la lista de sitemap/registry completa.

Para cada ruta registrar:

- familia;
- viewport 390 / 1440;
- shell correcto;
- gutter;
- H1 visible;
- CTA principal;
- navegación de salida;
- footer;
- overflow/crop;
- fondo/color/rules;
- links principales;
- estado de formularios si existen;
- resultado PASS / BUG / EXCEPCIÓN INTENCIONADA.

La lista **no debe mantenerse a mano**: generarla desde registry/sitemap para que cualquier nueva ruta entre automáticamente.

---

## P1.6 — No-JS ampliado

Ya existen pruebas no-JS representativas. Ampliar el contrato a una ruta por cada familia pública:

- contenido editorial único sigue visible;
- navegación esencial sigue disponible;
- links siguen siendo links;
- ninguna información SEO/lectura existe únicamente después de JS;
- herramientas pueden requerir JS para calcular, pero deben explicar su función y ofrecer salida/navegación sin romper el documento.

---

## P1.7 — Accesibilidad manual complementaria

Pa11y está verde, pero Yale recomienda combinar automatización y evaluación manual representativa.

Checklist mínima:

- teclado completo;
- VoiceOver (Safari/iOS/macOS) o NVDA/Firefox en muestra representativa;
- foco del dialog Explorar: entrada, trap y retorno;
- Asistente: lectura de mensajes/fuentes/estado;
- formularios: error asociado y anunciado;
- zoom 200%;
- text spacing WCAG;
- `prefers-reduced-motion`;
- targets táctiles;
- modo landscape móvil;
- teclado virtual iOS/Android sin ocultar composer/botones.

Actualizar la fecha de la declaración de accesibilidad **solo cuando se haga esta prueba real**.

---

## P1.8 — Legibilidad y densidad editorial

Basado en Yale: tipografía consistente, lectura legible y grids usados para contenido que se beneficia de agrupación, no para meter prosa larga en columnas pequeñas.

Revisar:

- párrafos no demasiado anchos;
- no proliferación de H1/H2 gigantes por página;
- cards no convertidas en contenedores de párrafos largos;
- al colapsar de 3/2 columnas a 1 columna, el orden tiene sentido;
- no aparecen huecos enormes creados por alturas mínimas pensadas para desktop;
- el Cuaderno conserva ritmo de lectura distinto de una herramienta, pero ambos comparten el sistema.

---

## P1.9 — “La memoria de las tierras del norte”

PR #101 dejó expresamente fuera una página interna dedicada. Actualmente es válido que la tarjeta de Obras salga a la editorial, pero rompe parcialmente el patrón “Obras → ficha interna → fuente/compra externa”.

**Decisión pendiente, no blocker:**

- si se crea ficha, usar únicamente hechos ya verificados;
- misma familia visual de Obras, sin inventar sinopsis/datos;
- publisher externo como CTA secundario;
- añadir canonical, sitemap, registry, Explore/relaciones solo si aporta navegación real.

No crear una página vacía solo por simetría.

---

# P1 — SEO, redirects y descubribilidad en vivo

## P1.10 — Sitemap/canonical/noindex LIVE

Crear `qa/production-seo-smoke.mjs`:

- descargar sitemap de producción;
- cada URL → 200;
- canonical coincide con URL final normalizada;
- no `noindex` en sitemap;
- rutas `noindex` no entran en sitemap;
- OG/Twitter image → 200;
- JSON-LD parsea;
- facts críticos no contradicen `editorial-facts.json`;
- `robots.txt` apunta al sitemap correcto;
- `llms.txt` y `llms-full.txt` responden.

Los checks estáticos ya pasan; este test demuestra el sitio servido.

---

## P1.11 — Auditoría de redirects y URLs antiguas

Base Yale: después de migraciones, comprobar redirects en navegador/network y distinguir 301 permanente de 302 temporal.

Construir inventario desde:

- URLs de la web anterior conocidas por Git/historial;
- Search Console;
- 404 reales de Cloudflare/servidor si están disponibles;
- backlinks importantes.

Comprobar:

- antiguo → nuevo correcto;
- 301 para cambios permanentes;
- máximo un salto cuando sea posible;
- no loops;
- path/query conservados cuando corresponda;
- el destino no termina en otra redirección innecesaria.

---

## P1.12 — Operación SEO postmigración

Manual, no código:

- reenviar sitemap en Google Search Console;
- inspeccionar Home, Obras, Manecillas, Cuaderno y Herramientas;
- revisar cobertura/404/canonical durante 1–2 semanas;
- Bing Webmaster Tools si se usa;
- no forzar IndexNow custom si Cloudflare Crawler Hints termina siendo la vía elegida;
- si se activa Crawler Hints, verificar primero que respeta la política de index/noindex y medir, no activarlo por cosmética.

---

# P1 — seguridad, backend y observabilidad

## P1.13 — Security headers EN PRODUCCIÓN

La CSP del HTML está auditada, pero Cloudflare puede alterar/añadir headers. Verificar por respuesta real:

- CSP efectiva;
- HSTS (solo cuando HTTPS esté estable);
- `X-Content-Type-Options: nosniff`;
- `Referrer-Policy`;
- `Permissions-Policy` si está definida;
- framing/`frame-ancestors` según embeds reales;
- no duplicar reglas incompatibles entre HTML/meta/Cloudflare;
- Turnstile y Worker siguen funcionando con la política final.

Guardar snapshot de headers en CI/artifact.

---

## P1.14 — Assistant remoto: decisión explícita y smoke

La infraestructura remota existe y en PR #101 estaba deliberadamente desactivada (`ASSISTANT_ENABLED=false`). No debe activarse solo porque esté desplegada.

Si permanece OFF:

- UI/copy no debe prometer capacidad remota;
- fallback local debe ser suficiente y pasar QA;
- privacidad no debe describir tratamiento remoto como si estuviera activo.

Si se activa:

- test de config/feature flag;
- rate limit por IP/usuario según contrato;
- cuota D1;
- Turnstile cuando proceda;
- CORS/origin;
- Workers AI → Groq → OpenRouter con fallos simulados;
- timeout y respuesta degradada;
- no exponer secrets;
- logging sin contenido sensible innecesario;
- actualizar privacidad/copy con el flujo real.

AI Search sigue siendo una decisión separada y no necesaria para estabilidad.

---

## P1.15 — Workers observability

Los Workers de newsletter/asistente son backend real. Añadir/verificar:

- logs de error útiles;
- correlation/request ID si no existe;
- métricas de 4xx/5xx/timeout;
- alerta básica de fallo sostenido;
- no loggear texto sensible completo por defecto;
- runbook: dónde mirar cuando un formulario “funciona” en frontend pero no llega.

No añadir un proveedor nuevo si Cloudflare Workers Logs/Real-time logs cubre el caso.

---

## P1.16 — Errores JS en producción

No se ha identificado un sistema de error telemetry de navegador como requisito actual.

Opción mínima sin nuevo proveedor:

- job sintético diario/por release que recorra sitemap representativo con Playwright;
- falla ante `pageerror`, errores de consola no allowlisted, request failed de assets same-origin y unhandled rejection;
- artifact con ruta + error + screenshot.

Esto da más valor que añadir Sentry por defecto.

---

## P1.17 — Uptime y dependencias

Mínimo:

- Home + Manecillas + Cuaderno + Herramientas;
- endpoint newsletter;
- endpoint/config Assistant;
- certificado TLS;
- DNS.

GitHub Actions horario puede servir como mínimo. Si se necesita SLA real, usar monitor externo; no ejecutar cada minuto desde Actions.

---

## P1.18 — Analítica real de producción

La taxonomía está verde, pero falta el canary operativo:

- una visita real genera page view;
- CTA principal genera el evento esperado una sola vez;
- navegación SPA/JS no duplica page views;
- GoatCounter/Metricool reciben producción;
- filtros de staging/bot funcionan;
- no registrar PII en eventos.

No añadir una tercera analítica salvo necesidad específica de RUM.

---

# P1 — PWA y rendimiento servido

## P1.19 — Service Worker después de un deploy

PWA offline QA está verde localmente. Añadir smoke de producción:

1. cargar versión N;
2. simular/publicar versión N+1 en staging;
3. comprobar actualización del SW;
4. no servir indefinidamente HTML/CSS antiguo;
5. offline fallback correcto;
6. `skipWaiting/clientsClaim` solo según estrategia deliberada;
7. limpiar caches obsoletas.

Especialmente importante después de un rediseño grande: “yo sigo viendo la web vieja” puede ser cache, no deploy.

---

## P1.20 — Rendimiento real, no perseguir una puntuación

Lighthouse CI ya está verde. Añadir control de producción con presupuestos estables:

- LCP/CLS/INP sintético donde sea posible;
- peso HTML/CSS/JS;
- número de fonts;
- imágenes hero/banner;
- cache headers;
- recursos duplicados;
- third parties.

No bloquear un release por variaciones mínimas de score. Bloquear por regresiones claras de presupuesto o CWV.

---

# P2 — deuda de sistema/mantenibilidad

## P2.1 — Documento canónico del sistema visual

Crear/actualizar una única autoridad tipo `docs/DESIGN-SYSTEM-V1.md` que explique:

- tokens;
- superficies;
- tipografía;
- gutter/layout;
- header/footer;
- context bar;
- reglas editoriales;
- CTA primario/secundario/link;
- focus;
- cards/ledgers;
- imágenes;
- excepciones de Libro/Cuaderno/Herramientas/Identidad.

Esto evita volver a “arreglar” una página con CSS aislado y reintroducir drift.

---

## P2.2 — Consolidar drift de tokens, sin rediseñar

`v1-site-cohesion-v6.css` usa materialidad `--dp-*` y el sistema global mantiene además tokens `--surface-*`, `--color-*`, etc. No es un bug visible por sí mismo, pero puede crear dos autoridades.

Auditar gradualmente:

- colores hardcoded fuera de ilustraciones/excepciones;
- duplicados semánticos;
- variables con mismo valor/rol;
- componentes que redefinen border/radius/shadow sin motivo.

No cambiar masivamente valores visuales en una sola PR. Primero inventario + contrato, luego migraciones pequeñas con visual regression.

---

## P2.3 — CSS ownership / clases sin hoja cargada

Crear QA estático que detecte por página:

- clases visuales utilizadas cuyo selector solo existe en CSS que esa página no carga;
- CSS family cargado pero no utilizado en ninguna ruta de esa familia;
- stylesheet inexistente/duplicado;
- orden de cascade distinto al contrato.

Este test previene fallos como el antiguo 404 sin gutter, donde el HTML era correcto pero faltaba la hoja propietaria del layout.

---

## P2.4 — Assets archivados

Se movieron cientos de imágenes huérfanas a `assets/no usadas/`.

Comprobar:

- ninguna está referenciada por runtime;
- esa carpeta no se publica si no necesita ser pública;
- no borrarla definitivamente hasta confirmar política de archivo/fuentes;
- el build público debe excluir material de trabajo no necesario.

---

## P2.5 — Paridad staging ↔ production

Añadir check que compare el artefacto/manifest del mismo SHA:

- mismas páginas/asset hashes;
- diferencias únicamente por config/feature flags declarados;
- no “funciona en preview” porque preview tenga archivos que producción no publica o viceversa.

---

## P2.6 — Release tag + rollback

Ahora que la web está publicada:

- etiquetar releases conocidos buenos (`web-2026-08-26`, o convención equivalente);
- documentar rollback de Pages/Cloudflare/Workers;
- guardar config exportable de DNS/rules relevantes;
- no depender de recordar “qué commit era el bueno”.

---

# Matriz mínima de revisión visual manual

La persona que ejecute esta auditoría debe generar la matriz desde registry/sitemap, pero como mínimo revisar estas familias:

| Familia | Rutas/vistas representativas | 390 | 768 | 1440 | Teclado | No-JS | Links | Visual |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Home | `/` | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Obras | `/libros/` | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Manecillas | página + fragmentos | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Samuel | ficha + lectura/recursos | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Autor | `/autor.html` | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Cuaderno | hub + artículo largo | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Herramientas | hub + 3 motores | ☐ | ☐ | ☐ | ☐ | n/a | ☐ | ☐ |
| Prensa | `/prensa.html` | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Eventos | `/eventos.html` + archivo si existe | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Beta | `/lectores-beta/` + manuscrito | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Recursos | editoriales / convocatorias / recomendaciones | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Findability | mapa + 404 | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Legal | privacidad + accesibilidad | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Assistant | overlay/página/embed donde corresponda | ☐ | ☐ | ☐ | ☐ | n/a | ☐ | ☐ |

**PASS visual significa:** misma identidad/sistema, no “idéntica composición”.

---

# Nuevos tests propuestos — orden de valor

1. `production-smoke` parametrizando el staging smoke existente. **P0**.
2. `hydrated-link-crawl` Playwright sobre sitemap/registry. **P0**.
3. denylist live / internal leak smoke. **P0**.
4. visual regression representativa por snapshots. **P1**.
5. production SEO/canonical/sitemap smoke. **P1**.
6. computed design contract QA. **P1**.
7. console/pageerror/network-failure synthetic crawl. **P1**.
8. redirect/legacy URL live QA. **P1**.
9. security headers live snapshot. **P1**.
10. form canary release checklist o entorno de test seguro. **P1**.
11. PWA update-after-deploy smoke. **P1**.
12. CSS ownership QA. **P2**.
13. staging/production artifact parity. **P2**.

No añadir tests que dupliquen exactamente Pa11y, Reflow, Cross-engine, Lychee o Tool Engines actuales.

---

# Definition of Done de esta auditoría

No se considera “terminada” porque todos los checkboxes tengan código. Se considera terminada cuando:

- producción real pasa rutas públicas y denylist;
- enlaces estáticos **y DOM hidratado** pasan;
- formularios críticos han sido enviados de extremo a extremo al menos una vez tras el lanzamiento;
- Manecillas tiene su URL real cuando exista y no hay placeholders cruzados;
- DNS/Cloudflare/HTTPS/canonical están verificados externamente;
- `main` queda protegido;
- existe una regresión visual representativa aprobada;
- la matriz visual no contiene una familia que parezca otra web sin excepción documentada;
- SEO live/redirects/headers están validados;
- analytics y backends han recibido un canary real;
- los cambios futuros pueden volver a ejecutar estos gates sin depender de memoria humana.

---

## Observación sobre la comprobación live realizada durante esta auditoría

El crawler web disponible devolvió una copia indexada antigua de algunas páginas públicas (por ejemplo Home), por lo que **no se usa esa copia cacheada como evidencia del estado visual publicado hoy**. Las rutas internas consultadas desde ese mismo mecanismo no ofrecieron contenido legible, pero tampoco se registra un PASS HTTP porque el instrumento no expone un status fiable en esos casos. Además, el entorno de ejecución directo no pudo resolver DNS en ese momento.

Por eso esta PR exige un smoke HTTP/browser reproducible desde GitHub Actions o una red externa contra el dominio actual. No inventar un “todo 200/404 correcto” basándose en caché de buscador.

---

## Regla de ejecución

- Corregir bugs reproducibles en PR pequeñas.
- No mezclar en una sola PR branch protection + DNS + rediseño + Worker + contenido.
- No activar Cloudflare/Assistant/analytics nuevos solo porque estén disponibles.
- No copiar Yale visualmente.
- No reabrir el diseño aprobado salvo drift o problema UX demostrado.
- Cada corrección visual debe añadir o actualizar una prueba/baseline para que no reaparezca.
