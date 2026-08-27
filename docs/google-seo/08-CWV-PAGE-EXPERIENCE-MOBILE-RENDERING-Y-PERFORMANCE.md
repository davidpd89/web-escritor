# 08 — Core Web Vitals, Page Experience, mobile, rendering y performance

## Principio

Google usa Core Web Vitals dentro de sus sistemas de ranking, pero afirma expresamente que conseguir buenas métricas **no garantiza** estar arriba.

El orden correcto es:

1. contenido útil/relevante;
2. página accesible/indexable;
3. experiencia sólida;
4. rendimiento.

No sacrificar contenido o UX para perseguir un Lighthouse 100 ornamental.

---

# 1. Core Web Vitals 2026

Umbrales de referencia de Google, en percentil 75:

- **LCP**: Good <= 2,5 s;
- **INP**: Good <= 200 ms;
- **CLS**: Good <= 0,1.

## Fuente de verdad operativa

Field data:

- Search Console Core Web Vitals;
- CrUX cuando haya suficiente muestra.

Lab data:

- Lighthouse CI;
- local profiling.

Lab explica y reproduce. Field decide cómo viven usuarios reales la página.

---

# 2. Estado repo

Existe:

- `.github/workflows/lighthouse-ci.yml`;
- image-format ladder;
- responsive QA;
- Pa11y;
- sitewide reflow;
- asset optimization;
- preloads/fetchpriority selectivos.

No duplicar Lighthouse en un nuevo workflow SEO.

---

# 3. LCP

Candidatos actuales:

- foto del autor/home;
- portada Manecillas;
- portada Samuel;
- hero image de artículos.

## Buenas prácticas

- imagen hero en HTML;
- preload solo cuando realmente es LCP;
- `fetchpriority=high` para el candidato principal;
- responsive dimensions;
- evitar CSS background si el asset es contenido principal;
- no lazy-load LCP;
- CSS crítico razonable;
- fuentes no bloquear más de lo necesario.

## Auditar

Por template/familia, no solo home.

Una home rápida no compensa una herramienta o artículo lento si son las landing pages orgánicas reales.

---

# 4. INP

La web tiene:

- asistente;
- menú/dialog;
- herramientas;
- formularios newsletter;
- scripts de interacción.

## Riesgos

- listeners globales pesados;
- cálculo síncrono grande en herramientas;
- DOM excesivo;
- JS de terceros;
- tareas no críticas en main thread.

El repo ya utiliza estrategias como scheduling/background en scripts.

Preservar.

## Herramientas

Para textos grandes:

- medir input responsiveness;
- debounce cuando proceda;
- Web Worker si el análisis se vuelve costoso;
- no bloquear cada keystroke.

---

# 5. CLS

Requisitos:

- width/height/aspect-ratio de imágenes;
- espacio reservado para widgets;
- fuentes con fallback razonable;
- no inyectar banners encima del contenido;
- newsletter/popup no desplazar layout;
- nav móvil estable.

Especial cuidado al lanzar:

- banner de libro;
- purchase CTA;
- eventos;
- nuevos componentes de Preferred Sources.

---

# 6. Page Experience

Google ya no lo presenta como un único score.

Aspectos útiles:

- CWV;
- HTTPS;
- mobile usability;
- evitar interstitials intrusivos;
- contenido principal fácilmente distinguible;
- navegación segura.

No crear un KPI ficticio `Page Experience Score`.

---

# 7. Mobile-first

Google indexa mobile-first.

## Contrato

Mobile debe contener:

- mismo contenido principal;
- mismo title/meta/canonical;
- mismo structured data relevante;
- mismas imágenes importantes;
- enlaces principales;
- alt;
- datos factuales.

No ocultar para mobile un bloque clave de contenido con `display:none` si eso deja una versión semánticamente empobrecida.

Acordeones/tabs de UX son válidos; contenido dinámicamente ocultable no es por sí mismo spam.

---

# 8. Responsive

Ya existe fuerte trabajo responsive.

SEO QA debe centrarse en:

- viewport;
- reflow 320px+;
- no horizontal overflow;
- tap targets;
- overlays;
- images responsive;
- menú accesible;
- book hero sin cortar información fundamental.

No hay necesidad de m-dot URLs.

---

# 9. JavaScript SEO

Google renderiza JS, pero la web debe mantener su ventaja static-first.

## Contenido crítico en HTML

- title/meta;
- H1;
- texto;
- internal links;
- book facts;
- event facts;
- methodology;
- legal/consent.

## JS para

- interacción;
- filtros;
- tool computation;
- progressive enhancement;
- assistant.

No mover contenido indexable al cliente sin necesidad.

---

# 10. Tool pages

El output dinámico que un usuario genera con su propio texto no necesita ser indexable.

No crear URL por:

- resultado del contador;
- análisis de repeticiones;
- texto pegado;
- query params con contenido del usuario.

La landing/metodología es lo indexable.

---

# 11. Third-party scripts

Actuales:

- GoatCounter;
- Metricool;
- Cloudflare Turnstile en contextos específicos.

Cada tercero debe justificar:

- bytes;
- main-thread;
- privacy;
- CSP;
- utilidad.

No añadir:

- 5 trackers SEO;
- heatmaps siempre activos;
- chat adicional;
- tag managers complejos;

si no aportan decisiones.

---

# 12. Fonts

La web usa tipografía editorial propia.

Auditar:

- formats modernos;
- preload solo fuentes críticas;
- `font-display`;
- subset si procede;
- no descargar familias/pesos no usados.

No cambiar branding tipográfico solo por microganar Lighthouse sin medir field impact.

---

# 13. CSS

El sistema V1 divide tokens/base/shell/components/family.

Mantener:

- no enormes CSS globales para componentes que solo existen en una página;
- purge manual/automatizado con cuidado;
- evitar style recalculation excesiva;
- critical rendering path razonable.

No inlinear todo CSS por obsesión con requests si empeora cache/mantenimiento/CSP.

---

# 14. Speculation Rules

Varias páginas usan prefetch/prerender.

Eso puede mejorar navegación percibida, pero debe vigilarse:

- bandwidth móvil;
- analytics side effects;
- forms/side-effect pages;
- páginas pesadas;
- cache.

No es un factor de ranking por sí mismo.

Usarlo para UX, no para «engañar CWV».

---

# 15. Service Worker / PWA

Existe service worker y offline support.

SEO risks:

- servir shell viejo tras deploy;
- cachear HTML factual demasiado agresivamente;
- stale redirects;
- interferir con Google fetch no debería ocurrir si SW solo afecta navegador controlado.

## Importante

Para usuarios, la caché puede mostrar hechos viejos aunque Google tenga nuevos.

Versionar/invalidar correctamente tras cambios críticos de libros.

---

# 16. HTTP caching/CDN

Cloudflare/CDN debe equilibrar:

- performance;
- frescura.

Para HTML factual:

- evitar TTL que retrase cambios críticos durante días;
- purgar tras releases de facts;
- verificar edge además de origin si se puede.

Para assets hashed/versioned:

- long cache.

---

# 17. Compression

Verificar producción:

- Brotli/Gzip para HTML/CSS/JS;
- images ya comprimidas;
- no comprimir doble assets.

No se deduce del repo; es gate live.

---

# 18. Status / headers

QA live:

- 200 correct;
- 404 correct;
- no 5xx;
- HTTPS;
- cache headers;
- content-type;
- security headers sin bloquear Google resources.

No confiar solo en `<meta http-equiv=CSP>` para todas las garantías de headers, pero eso es security/ops más que ranking.

---

# 19. Intrusive interstitials

Newsletter popup existe.

Revisar mobile:

- no cubrir inmediatamente contenido principal;
- cierre claro;
- no obligar a suscribirse para leer contenido público;
- no reabrirse de forma agresiva;
- accesible.

Google recomienda evitar interstitials intrusivos.

---

# 20. Ads

Actualmente no son el modelo central.

Si aparecen:

- no desplazar main content;
- no confundir editorial/comercial;
- no ratio agresivo;
- links qualified.

---

# 21. Performance budgets

Definir por familia, no un budget imposible global.

Ejemplo inicial orientativo, a validar:

- JS first-party inicial <150 KB gzip en editorial simple;
- hero image responsive adecuada al viewport;
- no >1 high-priority hero;
- 0 unexpected layout shifts por images;
- third-party minimal.

Estos budgets son ingeniería interna, no thresholds de Google.

---

# 22. Field monitoring

Mensual:

- Search Console CWV;
- groups Poor/Needs Improvement;
- templates afectados;
- mobile vs desktop;
- releases correlacionados.

Cuando aparece un grupo Poor:

1. sample URLs;
2. CrUX/PageSpeed;
3. lab reproduction;
4. template root cause;
5. fix once at component level;
6. validate fix en Search Console.

---

# 23. Lighthouse policy

No aceptar PR que empeora materialmente performance sin justificación.

Pero evitar:

- bloquear mejoras editoriales por 1 punto de Lighthouse;
- optimizar tests en vez del usuario;
- esconder componentes a Lighthouse.

---

# 24. Accessibility

Accesibilidad no se presenta como un único factor de ranking, pero:

- semántica;
- headings;
- alt;
- labels;
- enlaces;
- keyboard;

mejoran la página y coinciden con una arquitectura que Google puede comprender bien.

Preservar Pa11y/reflow.

---

# 25. Agent readiness

La documentación 2026 de Google sobre IA también empieza a hablar de agentes.

La misma semántica beneficia automatización:

- buttons son buttons;
- links son links;
- labels;
- DOM estable;
- acciones visibles.

Esto está cubierto en profundidad en `docs/ai-discoverability/`.

---

# 26. Tests propuestos

## `scripts/seo/audit-performance-contract.py`

No reemplaza Lighthouse. Comprueba estáticamente:

- hero preload count;
- image dimensions;
- lazy LCP warnings;
- excessive third-party hosts;
- missing viewport;
- duplicate JS;
- critical tool content present in HTML.

## CI

Reutilizar Lighthouse workflow existente.

No añadir un segundo Lighthouse con thresholds diferentes.

---

# 27. Acceptance criteria

- CWV se mira en field data;
- Lighthouse sigue verde/estable;
- LCP image no lazy;
- images dimensioned;
- newsletter no interstitial intrusivo;
- mobile parity factual;
- main content HTML;
- tools no generan URLs indexables por resultados;
- service worker no crea stale UX grave;
- third-party JS controlado;
- regressions se arreglan por template/componente.
