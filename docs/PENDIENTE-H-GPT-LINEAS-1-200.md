# Pendiente H — Auditoría de `pendiente funcionalidad gpt.txt`, líneas 1–200

Fecha de auditoría: 2026-08-23  
Rama base auditada: `implementacion-web-2026`  
HEAD auditado: `4694799edc6d9c9e729b896cadda1eef9726d083`

> Esta PR nace de contrastar **las primeras 200 líneas** de `pendiente funcionalidad gpt.txt` contra el repositorio real, no de asumir que el TXT sigue vigente. Su objetivo es recoger únicamente deuda funcional/técnica que continúa siendo real y que **no está ya cubierta por otra PR abierta**. No autoriza `main`, producción ni despliegue.

## 1. Resultado de la auditoría

### 1.1 Correcto o sustancialmente cerrado — no reabrir

En el alcance de las líneas 1–200 se comprobó que ya existe o quedó absorbido por trabajo posterior:

- normalización editorial y machine-readable de Samuel;
- reconstrucción de los contenidos de portal fantasy y magia con coste;
- cuarentena técnica del contenido 2025–2026 (`noindex` y fuera de superficies de descubrimiento); la decisión editorial definitiva sigue siendo contenido, no un bug de runtime;
- separación de Manecillas y Samuel en arquitectura y navegación;
- `/empieza-aqui/` y shell/navegación V1;
- PWA/manifest y baterías actuales de CI/QA;
- RSS, sitemap, redirects, JSON-LD, discoverability y módulos relacionados ya presentes en la rama;
- la antigua observación de `eventos.html` con `data-newsletter-source="eventos"` está **obsoleta**: el HTML actual ya no contiene ese source, por lo que no hay que ampliar `SOURCE_MAP` por ese motivo.

### 1.2 Ya está cubierto por PR abiertas — NO duplicar

- **Rate limiting / honeypot / retorno DOI de Brevo:** PR #55.
- **Triggers del popup de newsletter (60 % / timer / exit-intent frente a la spec):** PR #56.
- **Smoke test real post-deploy y `build-public-dist --check-contents` en CI:** PR #58.
- **Inventario de assets sin referenciar:** PR #60. Esta PR no debe convertir ese informe en borrado automático.

### 1.3 Gates externos/editoriales — no convertir en bug de código

- `purchaseUrl` y selector real de tiendas de Manecillas: dependen de URLs comerciales verificadas. No crear ofertas ni tiendas ficticias.
- validación visual final, dirección fotográfica y materiales de marca: gate humano/diseño.
- permisos/activos editoriales de prensa: gate externo.
- artículo 2025–2026 en cuarentena: falta decisión/revisión editorial antes de reindexarlo, no infraestructura de indexación.
- cluster editorial de Manecillas todavía no publicado: trabajo de contenido; la arquitectura puede existir sin inventar artículos.
- confirmación end-to-end de DOI en Brevo: la parte de código está siendo tratada en #55; la automatización/configuración real sigue siendo externa.

---

# 2. DEUDA NUEVA REAL

## H.1 — `script.js` sigue siendo un runtime global monolítico y el popup mantiene CSS dentro de JavaScript

### Evidencia actual

`script.js` continúa concentrando responsabilidades que no pertenecen a todas las páginas:

- cliente de newsletter;
- registro de service worker;
- navegación móvil legacy;
- botón «volver arriba»;
- progreso de lectura;
- quiz completo de Noveris;
- popup de newsletter;
- modal de compra de Samuel;
- instrumentación GoatCounter y handlers de enlaces.

El popup sigue creando un `<style>` en runtime con un bloque CSS grande. Además, sus estados de éxito/duplicado continúan inyectando estilos inline con `font-family:Cormorant Garamond,Georgia,serif`, de modo que la afirmación del TXT de que esa parte seguía legacy **no está completamente cerrada** pese a limpiezas posteriores.

El modal de compra de Samuel también sigue dentro del runtime global. Esto deja código específico de Samuel/Noveris/newsletter en un fichero cargado por superficies que no necesitan esas funciones.

### Implementación requerida

1. Separar responsabilidades de `script.js` por alcance real de página, sin migrar de stack ni introducir framework/bundler.
2. Extraer el popup de newsletter a módulo/asset propio y mover su CSS a una hoja dedicada o al sistema visual autoritativo; no inyectar un stylesheet grande mediante `style.textContent`.
3. Eliminar la tipografía legacy del HTML de estados del popup y usar los tokens/fuentes vigentes del sistema V1.
4. Extraer el modal de compra de Samuel para que solo cargue donde exista un trigger válido de Samuel.
5. Extraer o cargar bajo demanda el quiz de Noveris únicamente en su superficie real.
6. Mantener `script.js` como núcleo pequeño para funciones verdaderamente sitewide; no fijar un umbral de bytes arbitrario si no se demuestra primero el coste, pero sí registrar before/after.
7. Preservar el contrato que resulte de #56; si #56 entra antes, rebasar esta rama y no reintroducir timer/scroll/exit-intent antiguos.

### Criterios de aceptación

- [ ] páginas sin popup no descargan/ejecutan el módulo del popup;
- [ ] páginas sin compra de Samuel no descargan/ejecutan el modal de Samuel;
- [ ] páginas fuera de Noveris no descargan/ejecutan el quiz de Noveris;
- [ ] el popup no crea su hoja principal mediante `style.textContent`;
- [ ] no queda `Cormorant Garamond`/`Inter` hardcodeado como tipografía legacy en el markup runtime del popup;
- [ ] newsletter, popup, modal de Samuel, fragmento, Noveris y navegación mantienen comportamiento y accesibilidad;
- [ ] `node --check` pasa sobre todos los módulos JS afectados;
- [ ] los tests/browser QA existentes afectados siguen en verde;
- [ ] añadir un test/check de **runtime scoping** que falle si una responsabilidad específica vuelve a cargarse globalmente donde no corresponde.

---

## H.2 — Falta un contrato completo y verificable del funnel de Manecillas en la analítica vigente

### Evidencia actual

Las líneas auditadas pedían un funnel equivalente a:

- inicio de muestra;
- final/lectura de muestra;
- apertura de compra;
- clic de compra.

No se debe introducir GA4 solo para conservar nombres históricos: la instrumentación vigente del repositorio usa GoatCounter/eventos propios.

En el HEAD auditado:

- el modal de compra emite un evento genérico de apertura y es específico de Samuel;
- existen clics genéricos de compra/fragmento;
- el tracking de profundidad que busca rutas con `/fragmento/` no cubre por sí mismo la ruta actual `/las-manecillas-del-recuerdo/fragmentos/`;
- la página de fragmentos de Manecillas no contiene un contrato explícito y probado que permita reconstruir el funnel completo por libro.

Por tanto, el requisito funcional sigue sin estar cerrado aunque existan eventos genéricos.

### Implementación requerida

1. Definir eventos semánticos en la analítica **actual**, con una dimensión estable `book=manecillas` (o equivalente documentado).
2. Instrumentar entrada/inicio de la muestra de Manecillas y un final/umbral de lectura que permita medir consumo sin doble conteo.
3. Preparar `buy_open`/`buy_click` para Manecillas **solo cuando exista una CTA/tienda real verificable**. Mientras no exista minorista, el evento correcto debe seguir siendo espera/newsletter, no «compra» ficticia.
4. Evitar que el funnel de Samuel y el de Manecillas se mezclen bajo eventos sin identidad de libro.
5. Añadir QA determinista/browser que compruebe nombres/dimensiones y ausencia de dobles disparos.

### Criterios de aceptación

- [ ] una visita a `/las-manecillas-del-recuerdo/fragmentos/` puede producir eventos de muestra identificados como Manecillas;
- [ ] el consumo significativo/final de muestra se registra una sola vez por condición prevista;
- [ ] un evento de compra nunca se genera si el CTA continúa siendo lista de espera;
- [ ] cuando haya tienda real, apertura y salida a tienda incluyen identidad de Manecillas y destino;
- [ ] los eventos de Samuel siguen diferenciados;
- [ ] test automatizado demuestra el contrato.

---

## H.3 — Falta un gate global y reproducible de imágenes responsive

### Evidencia actual

Hay optimizaciones y variantes responsive en piezas concretas, y Lighthouse/reflow están en CI. Sin embargo, en el HEAD auditado no existe un checker específico que recorra las superficies públicas y haga cumplir de forma reproducible la política pedida en las líneas 84–137 para imágenes editoriales: dimensiones intrínsecas y, cuando corresponde por tamaño/uso, `srcset`/`sizes`.

La PR #60 resuelve otra pregunta —assets no referenciados— y **no sustituye** este control.

### Implementación requerida

Crear un auditor reproducible de imágenes de HTML público que clasifique, sin aplicar arreglos mecánicos:

- imágenes de contenido sin `width`/`height` cuando deberían reservar espacio;
- imágenes editoriales grandes servidas como un único fichero cuando existe/conviene una familia responsive;
- `srcset` sin `sizes` útil o candidatos rotos;
- referencias a variantes inexistentes;
- uso de eager/lazy/fetchpriority incoherente con la función de la imagen cuando el contrato pueda determinarlo con seguridad.

Debe distinguir iconos, SVG, elementos decorativos, imágenes pequeñas y casos deliberados para evitar falsos positivos.

### Criterios de aceptación

- [ ] checker con fixtures positivos y negativos;
- [ ] inventario/base real del sitio producido antes de endurecer CI;
- [ ] corregir los incumplimientos objetivos o documentar excepciones estrechas con motivo;
- [ ] después de sanear la baseline, el checker corre en CI sobre cambios relevantes;
- [ ] demostrar una vez que una regresión de fixture lo pone en rojo;
- [ ] Lighthouse, Pa11y y reflow siguen en verde tras las correcciones.

---

# 3. Orden recomendado dentro de esta PR

1. **H.1 runtime scoping**, porque reduce código global y evita seguir ampliando `script.js`.
2. **H.2 analítica Manecillas**, ya sobre el runtime resultante.
3. **H.3 imágenes responsive**, independiente pero agrupado aquí porque procede de la misma auditoría 1–200 y no tenía PR propia.

Si el volumen de H.3 hace que el diff deje de ser revisable, separar su implementación a una PR hija está permitido, pero este documento debe quedar como trazabilidad y enlazarla.

# 4. QA / no-regresiones obligatorias

Antes de declarar implementado:

- rebasar sobre el HEAD fresco de `implementacion-web-2026` después de integrar las PR que toquen áreas comunes;
- no debilitar tests existentes para poner CI verde;
- revisar diff completo;
- ejecutar suites de newsletter/runtime/herramientas afectadas;
- ejecutar browser QA relevante en móvil y escritorio;
- ejecutar Lighthouse, Pa11y y reflow cuando cambie carga/markup/CSS;
- comprobar que la PR no reintroduce ningún punto ya resuelto en #54–#60.

**No mergear esta PR automáticamente. No tocar `main`. No desplegar producción.**

---

# 5. Estado de implementación (2026-08-23)

## H.1 — Runtime scoping

- **Quiz de Noveris eliminado por completo** (no extraído: verificado por
  grep en todo el sitio que `id="quiz-noveris-app"` no existe en ningún
  HTML real, y `tests/test-samuel-ecosystem-parity.py:89` ya prohibía ese
  id explícitamente porque el quiz vigente es otro —
  `assets/samuel-quiz.js`, cargado solo en
  `libros/samuel-entre-mundos/index.html`—). Código muerto desde su
  creación, ~220 líneas retiradas.
- **Modal de compra de Samuel** extraído a `assets/samuel-buy-modal.js`,
  cargado únicamente donde existe `[data-buy-modal]`
  (`libros/samuel-entre-mundos/index.html`).
- **Popup de newsletter** extraído a `assets/newsletter-popup.js` +
  `assets/newsletter-popup.css` (ya no crea su hoja con
  `style.textContent`), cargado solo en las 13 páginas reales bajo
  `/cuaderno/`, `/recomendaciones/`, `/universo/noveris/` y
  `/clubes-de-lectura/`. Triggers alineados con la spec (70 % scroll, sin
  temporizador de 30 s, exit-intent gateado a `hover:hover`+`pointer:fine`).
  Estados de éxito/duplicado migrados de `style` inline con
  `Cormorant Garamond` hardcodeado a clases (`.nl-popup-result-title/-body`)
  con `var(--font-display)`.
- **Gate de runtime scoping nuevo**: `scripts/check-runtime-scoping.py`
  (+ `tests/test-check-runtime-scoping.py`, 5 casos) falla si el popup o el
  modal vuelven a reimplementarse en `script.js`, o si el contrato
  página↔script se rompe en cualquier dirección. Probado en rojo contra el
  repo real (ver evidencia abajo).
- `script.js`: 917 → 456 líneas.

## H.2 — Funnel de Manecillas

- `assets/manecillas-funnel.js` (cargado solo en
  `las-manecillas-del-recuerdo/fragmentos/index.html`): eventos
  `sample-start-manecillas` / `sample-complete-manecillas` con identidad de
  libro explícita en el nombre, sin doble conteo (`IntersectionObserver` +
  guard, verificado con scroll repetido).
- **Bug real corregido**: el tracker de clics de "leer fragmento" buscaba
  la subcadena `/fragmento/` (singular), que nunca coincidía con la ruta
  real de Manecillas (`/las-manecillas-del-recuerdo/fragmentos/`, plural) —
  esos clics no se contaban en absoluto. Separado en dos eventos con
  identidad de libro: `leer-fragmento-samuel` / `leer-fragmento-manecillas`.
- Sin `buy-open`/`buy-click` para Manecillas: no existe tienda real
  verificable todavía (documentado explícitamente en el propio código). El
  evento de conversión sigue siendo `newsletter-manecillas` (ya existente,
  ya con identidad de libro).

## H.3 — Gate de imágenes responsive

- `scripts/check-responsive-images.py` (+ `tests/test-check-responsive-images.py`,
  10 casos con fixtures positivos/negativos): clasifica `MISSING_DIMENSIONS`,
  `SRCSET_WITHOUT_SIZES`, `BROKEN_SRCSET_CANDIDATE` e `INCOHERENT_LOADING`
  en HTML público (excluye iconos/SVG/decorativos/noindex).
- **Inventario real**: 68 páginas públicas, 48 `<img>` en todo el repo,
  **0 incumplimientos** — el sitio ya declara `width`/`height` en todas sus
  imágenes de contenido reales. No hizo falta corregir nada; se deja el
  gate wireado para que no pueda regresar sin que CI lo detecte.
- Wireado en `.github/workflows/content-index-check.yml`.

## Evidencia de ejecución (real, pegada de las ejecuciones)

```
$ python scripts/check-runtime-scoping.py
PASS: runtime scoping OK (88 paginas HTML revisadas).

$ python scripts/check-responsive-images.py --check
Responsive images check: 68 paginas publicas revisadas, 0 incumplimiento(s).

$ python tests/test-check-runtime-scoping.py
  ok   repo correctamente scoped no reporta errores
  ok   popup reimplementado en script.js se detecta
  ok   modal de Samuel reimplementado en script.js se detecta
  ok   trigger sin script del modal se detecta
  ok   popup cargado fuera de ambito se detecta
tests/test-check-runtime-scoping: OK

$ python tests/test-check-responsive-images.py
  [10/10 casos OK]
tests/test-check-responsive-images: OK

$ node qa/runtime-scoping-browser.mjs
runtime-scoping-browser: PASS

$ node qa/manecillas-funnel-browser.mjs
manecillas-funnel-browser: PASS

$ node --check script.js && node --check assets/newsletter-popup.js && node --check assets/samuel-buy-modal.js && node --check assets/manecillas-funnel.js
(sin errores)

$ python scripts/check-heading-structure.py
Heading/skip-link structure: 68 ficheros HTML revisados; 0 problema(s).

$ python scripts/check-local-assets.py
Local asset check: 88 HTML files scanned; 0 broken local reference(s).

$ python scripts/check-internal-graph.py
Summary: 0 error(s), 0 warning(s)

$ python scripts/build-sitemap.py --check
SITEMAP OK: 54 URLs

$ python scripts/check-secrets.py
No obvious secrets found in tracked files.

$ python tests/test-samuel-ecosystem-parity.py   # exit 0
$ node tests/test-newsletter-client-contract.mjs
test-newsletter-client-contract: all assertions passed
```

**Pruebas en rojo realizadas antes de confiar en los checkers** (regla de
la casa #3 de este documento):
- `check-runtime-scoping.py`: se reintrodujo `document.getElementById("quiz-noveris-app")`
  en `script.js` → detectado y revertido.
- `check-responsive-images.py`: se quitó `width`/`height` de una imagen
  real de `ferias.html` → detectado (`MISSING_DIMENSIONS`) y revertido.
- `qa/manecillas-funnel-browser.mjs`: durante el desarrollo se detectó una
  condición de carrera real (el script externo `gc.zgo.at/count.js`
  sobrescribía el mock de GoatCounter a mitad de test) — corregida
  bloqueando esa red en el propio test, no es un bug de producción.
