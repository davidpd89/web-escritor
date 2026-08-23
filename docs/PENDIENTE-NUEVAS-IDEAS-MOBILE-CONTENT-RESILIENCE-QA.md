# Auditoría WEB DAVID PORTO nuevas ideas — Mobile + Content Resilience QA

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`

## Motivo

La carpeta `WEB DAVID PORTO nuevas ideas/DISEÑO Y DEMÁS` contiene un contrato V1 ya cerrado para resiliencia editorial y móvil, especialmente:

- `34 — CONTENT RESILIENCE + EDGE STATES V1`
- `35 — MICROTIPOGRAFÍA EDITORIAL ES V1`
- `36 — MOBILE RUNTIME + VIEWPORT V1`
- `18 — QA DE NIVEL PREMIO`

El laboratorio `/lab/diseno-home-v1/` **sí existe** en la rama de integración; no se abre deuda por «lab ausente».

El repositorio también tiene un gate sitewide real:

- `.github/workflows/sitewide-reflow-qa.yml`
- `qa/sitewide-reflow-browser.mjs`

Por tanto la deuda no es crear otro sistema de QA, sino cerrar la diferencia entre ese gate y el contrato V1 documentado.

---

## Evidencia actual

`qa/sitewide-reflow-browser.mjs`:

- solo usa `390×900` y `768×1000`;
- activa `reducedMotion: 'reduce'`;
- inyecta text-spacing reforzado;
- aplica `zoom = 2`;
- mide desbordamiento horizontal sobre las rutas públicas recogidas de sitemap/registry/HTML;
- excluye `lab` expresamente;
- no prueba interacción con teclado ni foco;
- no prueba JavaScript desactivado;
- no prueba landscape ni viewport bajo;
- no prueba rotación;
- no simula teclado virtual/formularios;
- no cubre safe-area/touch/hover;
- no introduce contenido hostil o estados vacíos/error para comprobar crecimiento real de componentes.

El workflow instala además Playwright 1.55 de forma local. Esa parte ya tiene owner en **#65** y no debe resolverse aquí creando otra autoridad de dependencias.

La cobertura cross-engine pertenece a **#66 K.3**. Esta PR no debe convertir el gate de resiliencia en un segundo smoke Firefox/WebKit paralelo.

---

## Deuda 1 — cerrar la matriz mínima de reflow móvil

Ampliar el gate existente, no crear otro, para cubrir como mínimo:

1. `320×568` o altura equivalente representativa;
2. `390×900` como móvil normal;
3. landscape de altura baja, por ejemplo `667×375`;
4. viewport bajo `<=560 px` donde haya sticky/fixed/overlays;
5. text-spacing reforzado;
6. zoom 200 % / reflow.

Los escenarios deben ejecutarse de manera separable para que un fallo diga **qué contrato rompe**. No mezclar siempre text-spacing + zoom + reduced-motion en una sola fotografía porque impide aislar regresiones.

Criterio: cero overflow horizontal de página salvo superficies deliberadamente scrollables y accesibles.

---

## Deuda 2 — no-JS y reduced-motion como contratos independientes

Añadir al menos un smoke sitewide determinista con `javaScriptEnabled: false` para páginas públicas que declaren fallback/no-JS.

Reduced motion debe comprobar no solo que el contexto se crea con `reduce`, sino que:

- no aparecen animaciones esenciales bloqueantes;
- diálogos/menús siguen pudiendo abrirse/cerrarse;
- no se pierde contenido o acción por depender de una transición.

No convertir este scope en auditoría visual pixel-perfect.

---

## Deuda 3 — teclado, overlays y formularios en viewport pequeño

Los contratos 34/36 consideran blocker perder foco/acción cuando aparece teclado o cuando un overlay ocupa una pantalla baja.

Añadir pruebas focalizadas para las superficies públicas realmente presentes, al menos:

- búsqueda/asistente si ofrece input/overlay;
- diálogo `Explorar`;
- newsletter/footer form;
- cualquier formulario público central que exista en el HEAD vigente.

Verificar:

- foco visible y dentro del viewport;
- acción primaria alcanzable;
- `Escape` cierra donde el patrón lo exige en escritorio;
- no existe focus trap sin salida;
- no aparece overflow horizontal;
- un sticky/fixed no tapa el control enfocado.

No intentar emular un teclado móvil físico exacto si Playwright/Chromium no ofrece señal fiable; sí reducir viewport dinámicamente y probar la geometría observable.

---

## Deuda 4 — contenido hostil / edge states M01–M25

El gate sitewide actual solo observa el contenido real comprometido. Eso no demuestra resiliencia frente a los edge cases que el sistema visual declara obligatorios.

Crear una capa de fixtures o una página de harness **no publicable** para componentes/familias críticas con ejemplos como:

- títulos muy largos y muy cortos;
- >=7 tags;
- metadatos y breadcrumbs largos;
- CTA largo;
- footer con texto largo;
- media/imagen ausente;
- fragmento ausente;
- cero/próximos eventos;
- búsqueda vacía/sin resultados;
- error parcial;
- errores y outputs largos de herramientas;
- Unicode/URLs largas.

No contaminar contenido real ni inventar hechos editoriales. Los fixtures son QA, no copy publicado.

Reglas técnicas a comprobar donde aplican:

- no usar `overflow-x:hidden` en `html/body` como parche;
- hijos de grid/flex con `min-width:0` cuando lo necesiten;
- wrapping adecuado de strings/links/tags largos;
- no usar `overflow-wrap:anywhere` global;
- no usar ellipsis en headings/body/información crítica;
- cards/bloques de contenido sin alturas fijas dependientes del copy;
- `hyphens:auto` solo en texto controlado y con `lang="es"`.

---

## Deuda 5 — microtipografía como regresión verificable

Añadir checks simples y deterministas para las invariantes de `35` que sí son automatizables:

- `html[lang="es"]` en superficies editoriales públicas;
- detectar `hyphens:auto` aplicado globalmente o en UI crítica;
- detectar `overflow-wrap:anywhere` global;
- detectar ellipsis/clamp en headings o contenido crítico cuando el selector permita identificarlo;
- conservar URLs, ISBN, JSON-LD y código fuera de cualquier normalización tipográfica automática.

No crear un reescritor automático de signos/guiones/comillas sobre todo el repositorio: el propio contrato lo prohíbe por riesgo de corrupción.

---

## Deuda 6 — mobile runtime: reglas estáticas de alto riesgo

Añadir checker/lint enfocado a patrones que el contrato 36 marca como peligrosos, con allowlist explícita y pequeña:

- `100vw` en contenedores públicos cuando pueda provocar scrollbar;
- alturas/min-alturas de hero con `100vh/100dvh/100svh` sin justificación;
- sticky/fixed en superficies esenciales sin cobertura de QA;
- márgenes negativos en contenido esencial;
- `env(safe-area-inset-*)` usado como padding global indiscriminado.

El checker no debe prohibir estas primitivas de forma absoluta; debe exigir intención y cobertura.

---

## Coordinación obligatoria con PR existentes

- **#65**: instalación/versión/cache de Playwright. No tocar esa autoridad aquí salvo rebasing después de integración.
- **#66 K.3**: cross-engine Chromium/Firefox/WebKit. Esta PR cubre estados/matriz de resiliencia, no motores.
- **#61 H.1/H.3**: runtime scoping e imágenes responsive. Los fallos encontrados por el gate pueden terminar allí si la causa pertenece a esos scopes.
- **#58**: post-deploy/staging smoke. Este gate corre en repo/PR; #58 valida staging real.
- **#62**: CSP. No relajar CSP para hacer pasar fixtures/QA.

---

## Criterio de cierre

No considerar cerrado este frente hasta que:

- 320 px, landscape bajo, 200 % y text-spacing tengan escenarios reproducibles;
- exista no-JS real donde el contrato lo exige;
- overlays/forms críticos sobrevivan teclado/foco/viewport bajo;
- los edge states no dependan solo del contenido feliz publicado;
- las invariantes automatizables de microtipografía tengan regresión;
- cualquier excepción esté documentada por ruta/componente, no escondida mediante tolerancias globales;
- los fallos generen artefactos útiles (ruta, escenario, viewport, overflow/foco y screenshot cuando proceda).

## Fuera de alcance

- rediseñar Home/Books/Cuaderno: el lab ya existe;
- publicar Jaula;
- cambiar copy/editorial para hacer pasar tests;
- cross-engine (#66);
- dependencia Playwright (#65);
- staging post-deploy (#58);
- Metricool/publicación social.

No tocar `main`, no desplegar producción y no activar auto-merge.
