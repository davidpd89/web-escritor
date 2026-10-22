# UX e integración de «Apoya el contenido»: contrato para Claude

**Base actual:** sitio estático; `scripts/build-site-shell.py` / `data/navigation.json` / `data/content-registry.json` generan cabecera, diálogo y pie. El CSS V1 está en `assets/v1-shell.css` y hojas importadas; hay builders para herramientas/catálogos. **No tocar sus HTML derivados como fuente**.

## Alcance de esta PR

Investigación aplicada + piezas de HTML/CSS listas para adaptar. No crear botones vivos sin URLs reales; no publicar página vacía ni enlaces ficticios. **Este archivo no es ejecutado por la web**. Esta hija también prepara la ruta futura `/apoyar/` y aporta una **vista previa generable en `lab/`**, fuera del sitio publicado. No modifica navegación ni cobro: la ruta pública solo se activará al tener enlace verificado.

## Pieza funcional incorporada: vista previa segura

**Problema:** una página en `apoyar/index.html` sin proveedor verificado podría publicarse o generar un enlace roto; un simple `noindex` no la protegería de visitas directas.

**Solución implementada:** `scripts/build-support-preview.py` genera la página **en `lab/donaciones-preview/index.html`**, no en `/apoyar/`. Usa `scripts/site_shell.py` para inyectar **cabecera, Explorar, pie y CSP reales**, conservando la arquitectura del repo. Lleva `noindex,nofollow,noarchive`, texto definitivo y un aviso explícito de que no hay cobros; no incorpora SDK, **formularios de pago** ni enlaces de cobro de ejemplo; **el shell sí conserva el formulario existente de newsletter en el diálogo «Explorar»**. El CSS contextual queda contenido en esa vista previa: no hay que invalidar CSS/preloads de todas las páginas.

```bash
python scripts/build-support-preview.py
python scripts/build-support-preview.py --check
python tests/test-support-preview.py
# Para verla localmente, servir el root del repo; NO desplegar lab/.
python -m http.server 8000
# Abrir http://localhost:8000/lab/donaciones-preview/
```

`tests/test-support-preview.py` comprueba el shell real, estado noindex, H1 único, no presencia de URL/SDK/captura de pagos y que `lab/` está excluido del constructor público. **Añadido; requiere ejecutar en el árbol real**. Se han inspeccionado en GitHub los dos archivos de código y validado estructuralmente las referencias (8 comprobaciones estáticas OK); esto **no** sustituye a los tests Python/CI ni a una inspección visual.

**Activación posterior (no hacer antes de validar receptor):** combinar la página previsualizada con el HTML de `scripts/support_paypal_link.py` de la PR **#700**, proporcionando exclusivamente la URL auténtica del panel; añadir `apoyar/index.html` a las fuentes registradas como `public`, `support-project` al pie, regenerar shell y sitemap y verificar artefacto. No copiar la URL ficticia del test. **No se ha creado** `apoyar/index.html` ni `data/navigation.json` modificado en esta PR.

**Test reforzado tras revisar el shell real (22/10/2026):** `render_explore()` añade al HTML final un `<form class="explore-subscribe">` de newsletter; no es un checkout. `tests/test-support-preview.py` distingue el formulario existente del diálogo y comprueba **sobre el `<main>` realmente renderizado**, no solo el HTML fuente, que no haya formularios de pago ni enlaces PayPal/Stripe/Ko-fi. También busca SDK y marcadores de claves en el HTML final. La lógica de detección de `<main>` se ha probado fuera de Actions con tres fixtures (newsletter legítima / formulario de pago / enlace de cobro), resultados esperados. **No está ejecutado aún el generador con los JSON completos del sitio.**

## Cierre por defecto de la URL de apoyo: publicación y Cloudflare

**Problema reproducible del contrato anterior:** haber añadido `apoyar/` a `PUBLIC_DIR_PREFIXES` y `!/apoyar/` a `.assetsignore` hacía publicable cualquier HTML situado allí, **aunque `support-project` ni siquiera existiera en el registro**. No basta con el test de activación: si no se ejecuta, una preview puede filtrarse por URL directa.

**Corrección implementada en código real:** `support_page_authorized(root)` en `scripts/build-public-dist.py` exige **exactamente una** entrada `support-project`, con `url: "/apoyar/"`, `sourceFile: "apoyar/index.html"` y **`status: "public"` explícito**. El valor general `defaults.status = public` no autoriza por omisión esta página de cobro. Tanto `is_publishable()` como la generación de `.assetsignore` consultan la misma función. Hasta entonces:

- El builder de artefacto **excluye cualquier archivo** bajo `apoyar/`, aunque exista en git.
- Cloudflare conserva `!/apoyar/` como capacidad futura, pero agrega una regla final **`/apoyar/`**, que vuelve a bloquear la carpeta. La regla desaparece automáticamente al declarar la entrada pública correcta y regenerar `.assetsignore`.
- No se ha cambiado `gated_prefixes_from_registry()`, para no alterar tests o publicaciones de otras páginas.

**Prueba de regresión:** `tests/test-public-artifact-contract.py` comprueba el estado real todavía cerrado, y simula en directorios temporales: sin registro, gated, ruta equivocada, público bien definido y entradas duplicadas. Cuando llegue la activación, debe regenerarse `.assetsignore` y ejecutarse el gate completo de checkout **antes de fusionar**.

**Ejecutado en copia aislada de la lógica:** `py_compile`, nueve casos de autorización y dos configuraciones de reglas `git check-ignore --no-index`: **OK**. Verificado por lectura de GitHub que la entrada `support-project` aún no existe y que la última regla activa es `/apoyar/`. **No equivale a ejecutar la suite integral del repositorio ni a comprobar un despliegue Cloudflare real.**

## Sitemap: exclusión por carpeta, no solo por meta robots

**Fallo detectado al revisar el generador existente:** `scripts/build-sitemap.py` recorre el repositorio con `os.walk()`; su `EXCLUDE_DIRS` no incluía `lab`. Una futura vista previa con canonical `/apoyar/` podría contaminar el sitemap si alguien eliminase por error el `noindex`.

**Corrección aplicada:** `"lab"` en `EXCLUDE_DIRS`, y fixture en `tests/test-support-preview.py` que crea una página `lab/donaciones-preview/index.html` **intencionadamente sin `noindex`** junto a una home legítima; exige que `collect_urls()` descarte siempre la primera y conserve la segunda. El contrato es independiente de enlaces PayPal y Stripe y protege otros prototipos del repositorio.

**Verificación realizada:** lectura del builder y los archivos modificados en GitHub; `sitemap.xml` versionado (331 URL) sin `/lab/` ni `/apoyar/`; fixture aislado de la misma poda `os.walk` OK. **Pendiente:** ejecutar `python tests/test-support-preview.py` y `python scripts/build-sitemap.py --check` en el árbol completo. No declarar esos comandos como ejecutados.

## Indexación: directivas equivalentes y Googlebot

**Problema verificado con el test Python de esta PR:** el gate aceptaba `<meta name="robots" content="none">` e incluso `<meta name="googlebot" content="noindex">`. Según Google Search Central, **`none` equivale exactamente a `noindex,nofollow`**, y las directivas específicas de `googlebot` también se aplican. Eso permitiría publicar una página de aportaciones declarada indexable en el registry, pero excluida de la búsqueda.

**Corrección incorporada en `tests/test-support-release-gate.py`:** reconocer `robots` y `googlebot` sin distinguir mayúsculas; dividir directivas por comas y rechazar solo tokens `noindex` o `none` (no prohibir `nofollow` o `noimageindex`). El fixture incluye `none`, `NONE, follow`, `googlebot=noindex` y nombre `ROBOTS`. Una página sin meta robots sigue siendo válida. Documentación oficial: https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag (actualizada 24/03/2026).

**Reproducción local real:** fuente anterior copiada del blob Git `43f3aa7068a33ac43b85e86f249f20da28e00942`, casos `none` y `googlebot` incorrectamente aceptados. Archivo corregido con SHA `4384f4794103f9c35b61ba2324435d367d8286c4`, compilación y test completo del archivo con fixtures en directorios temporales: OK. Las pruebas no ejecutan un despliegue ni verifican cabeceras HTTP `X-Robots-Tag`; el checkout sigue pendiente.

## PayPal: consultas de localización válidas en el checkout

**Defecto corregido con fuente oficial (11/09/2026):** el gate `tests/test-support-release-gate.py` rechazaba cualquier `?` de PayPal. Su documentación autoriza `locale.x` y `country.x` para evitar idioma/país erróneos: https://developer.paypal.com/payment-links-buttons/troubleshooting/ . El validador de esta PR admite el **par exacto**, con forma de valores controlada, y sigue rechazando parámetros inesperados, duplicados, fragmentos, dominios suplantados y `test_` en Stripe. `HTMLParser` decodifica correctamente `&amp;` en el `href`.

Caso real español válido: `?locale.x=es_ES&country.x=ES`; código oficial de España: https://developer.paypal.com/api/codes/locale/ . El helper de la PR #700 se ha actualizado en paralelo. **La comprobación aislada local de 5 enlaces válidos, 10 inválidos y decodificación HTML resultó OK; permanece pendiente el test integrado del repositorio y el checkout real.**

## Puerta de activación: prueba negativa y positiva

`tests/test-support-release-gate.py` verifica automáticamente dos estados válidos sin pagar ni consultar redes:

- **Sin activar:** no existe `apoyar/index.html`, ni entrada `support-project` en el registry, ni enlace en el footer.
- **Staging:** la página puede existir con `status: gated`/`noindex`, pero no debe enlazarse desde el pie; el builder público la excluye por `gated_prefixes_from_registry()`.
- **Público:** la entrada del registry debe ser `status: public`, apuntar a `apoyar/index.html`, aparecer exactamente una vez en `footer.Información`, tener canonical correcto, robots/googlebot sin `noindex` ni `none`, privacidad/aviso legal y **al menos un enlace de método** `support-method` al checkout PayPal o Stripe oficial, sin URL de prueba ni SDK.

El propio test monta casos aislados positivos y negativos para comprobar que fallan URL impostora, parámetros no documentados, `noindex` público y enlaces Stripe `test_`. Su validación de URL **solo prueba la forma**, nunca la titularidad, estado de cuenta, recepción de fondos ni exposición de datos personales en el recibo: esas comprobaciones siguen siendo manuales y obligatorias. **Fixture local aislado de este gate: `py_compile` + ejecución de casos privados, públicos y fallidos, resultado OK el 22/10/2026; no se ha ejecutado el árbol completo del repositorio ni CI.**

```bash
python tests/test-support-release-gate.py
```

**Estado:** código añadido a la rama, fixture aislado verificado; no se ha ejecutado la suite del repositorio ni Actions. La vista previa tiene su test propio, que **ya no impide** una activación correcta más adelante.

## Contrato de navegación (orden exacto recomendado)

1. Añadir una entidad `support-project` en `data/content-registry.json` siguiendo el esquema de `entries[]`, apuntando a `/apoyar/`, con label `Apoyar el proyecto` y contenido descriptivo real.
2. Añadir `support-project` **solo al array `footer.Información` de `data/navigation.json`** (no al menú principal `header`, no a `exploreTerritories`, no al CTA `header-buy`).
3. Ejecutar `python scripts/build-site-shell.py` cuando corresponda, revisar diffs y `--check` disponible, y actualizar la fuente/plantilla de páginas regeneradas para que las pruebas de paridad no reviertan el footer.
4. **La ruta está preparada pero bloqueada por defecto**: `scripts/build-public-dist.py` y `.assetsignore` requieren una entrada pública exacta `support-project` para permitir `/apoyar/`, aunque la carpeta ya figure en la allowlist. La protección y sus fixtures están en `tests/test-public-artifact-contract.py`. Cloudflare aplica `.assetsignore` con sintaxis gitignore: https://developers.cloudflare.com/workers/static-assets/binding/ . Al activar, regenerar `.assetsignore` desde el builder; **no borrar la regla a mano**.
5. Crear la página nativa `apoyar/index.html` coherente con shell V1, canonical `https://davidportodiaz.com/apoyar/`, un solo h1, estructura main, contenidos y métodos. Integrar sitemap con `scripts/build-sitemap.py`, navegación / mapa del sitio y `robots.txt` si aplica.
6. Solo después de tener proveedores confirmados, exponer enlaces desde el frontend. Deshabilitar/ocultar siempre los ausentes, nunca `href="#"`.

## Código HTML de tarjeta de apoyo (sin caja agresiva)

```html
<section class="support-page" aria-labelledby="support-title">
  <p class="eyebrow">Colaboración voluntaria</p>
  <h1 id="support-title">Apoya este proyecto</h1>
  <p>Las herramientas, guías y recursos de esta web son gratuitos. Si te han
     resultado útiles, puedes contribuir a mantenerlos y crear otros nuevos.</p>
  <div class="support-methods" role="group" aria-label="Elegir plataforma de pago">
    <!-- Inyectar únicamente enlaces de proveedor comprobados y activos -->
  </div>
  <p class="support-note">El pago se realiza en la plataforma elegida.
     No recogemos datos bancarios ni de tarjeta en esta web.</p>
  <p><a href="/privacidad.html">Privacidad</a> ·
     <a href="/aviso-legal.html">Aviso legal</a></p>
</section>
```

La nota no debe afirmar que el **proveedor** no pide datos; solo que nosotros no los recogemos directamente.

## CTA contextual, tras resultado o artículo

```html
<aside class="support-inline" aria-label="Apoyar el contenido gratuito">
  <p>¿Te ha servido esta herramienta? Si quieres, puedes
     <a href="/apoyar/">apoyar el proyecto</a> para ayudar a crear más recursos.</p>
</aside>
```

**No inyectar en cada página a ciegas.** Para herramientas individuales, insertar después de la zona final de resultados de dos herramientas piloto, sin tapar botones de copiar/descarga/reset. Para artículos, después del cuerpo, no entre párrafos. En el hub, en la parte final, sin competencia con los filtros. En el footer global, un único enlace legible, sin botón vistoso. En home, como máximo en cierre del flujo realmente construido por `assets/v1-home-editorial-v3.js`, no en el HTML fallback.

## CSS base propuesto (adaptar a tokens visuales reales)

```css
.support-page {
  width: min(100% - 2rem, 42rem);
  margin: 3rem auto 5rem;
}
.support-methods {
  display: grid;
  gap: .75rem;
  margin-block: 1.5rem;
}
.support-method {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  min-height: 48px;
  padding: 1rem 1.15rem;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  color: inherit;
  text-decoration: none;
}
.support-method:hover, .support-method:focus-visible {
  border-color: var(--color-accent);
  text-decoration: underline;
  outline-offset: 3px;
}
.support-method span, .support-note, .support-inline {
  color: var(--color-muted);
}
.support-inline {
  margin-block: 2.5rem 0;
  padding-block: 1rem;
  border-top: 1px solid var(--color-border);
  font-size: .92rem;
}
@media (max-width: 600px) {
  .support-method { flex-direction: column; align-items: stretch; }
}
```

CSS fragmento **original**, no importado de repos externos; usa tokens actuales comprobados en `assets/v1-*.css`. `assets/v1-base.css` ya define `html.v1 :focus-visible` con `outline:2px solid var(--focus-color)`: mantenerla y comprobar foco de teclado. Revisar WCAG contraste y zoom 200–400 %. Si se añade CSS nuevo a `v1-shell.css`, actualizar versionado/preloads con `scripts/add_v1_shell_preloads.py`.

## Contrato de configuración sin secretos, no dependiente de framework

```js
// Ejemplo de datos estáticos públicos; dejar SOLO proveedores verificados.
export const supportProviders = [
  // { id: 'paypal', label: 'PayPal', href: 'URL_REAL_VERIFICADA' },
  // { id: 'stripe', label: 'Tarjeta', href: 'https://buy.stripe.com/...' },
  // { id: 'kofi', label: 'Ko-fi', href: 'https://ko-fi.com/...' }
];
```

**No** usar esta lista de comentarios como renderizador activo. En implementación real validar `new URL(href)`, HTTPS, hosts exactos y no concatenar nombres ni importes. Enlaces de configuración pública no son secretos, pero nunca mezclar con API secret keys.

## QA concreto (añadir a tests existentes, sin correr CI en esta investigación)

Tests recomendados para Claude (además del `tests/test-support-preview.py` ya incorporado):
- **Ya incorporado** en `tests/test-public-artifact-contract.py`: `/apoyar/index.html` preparado en la allowlist **pero bloqueado hasta activación explícita**, `.assetsignore` sincronizado y archivos privados (`README.md`, `.env`, `*.key`) excluidos dentro de `/apoyar/`. No depende de ninguna cuenta de cobro.
- `tests/test-support-navigation.py`: entidad en registry, enlace en footer.Information, builder no divergente de HTML publicados; idempotencia de `build-site-shell.py --check`.
- `tests/test-support-provider-links.py`: ninguna URL ficticia o `#`, solo HTTPS y hosts aprobados; sin `sk_`, `pk_` de pruebas, teléfono, IBAN ni email del titular; `target="_blank"` y `rel="noopener noreferrer"`.
- `tests/test-support-pages.py`: una h1, canonical /apoyar/, validación links internos, sitemap, no formulario de pago, sin <script> remoto de proveedor, textos voluntarios y sin promesas de desgravación.
- `tests/test-support-placement.py`: CTA después del resultado (no encima), no duplicado, no modal/pop-up; home sin intervención hero y catálogo sin CTA por ficha.
- Manual con navegador: no-JS y JS, Chrome móvil/desktop, Safari, teclado, lectores de pantalla, ancho 320 px, zoom 400 %, enlace externo, regresiones CLS/LCP y CSP; comprobar pagador simulado con flujo real sin guardar sus datos.

Comandos de verificación **para ejecutar solo cuando se autorice CI**:

```bash
python scripts/build-site-shell.py --check
python scripts/build-sitemap.py --check
python tests/test-home-header-navigation.py
python tests/test-aria-landmarks-sitewide.py
python tests/test-public-link-contracts.py
```

No se garantiza que todos los checks cubran de manera suficiente la funcionalidad nueva; las comprobaciones específicas de colocación y enlaces todavía requieren validación en el navegador real; el test de activación y la aserción de publicación sí están incorporados en esta PR.

### Verificación de despliegue imprescindible al integrar el HTML

`python scripts/build-public-dist.py --check-assetsignore` y `python tests/test-public-artifact-contract.py` deben pasar. Una vez generado el HTML de `/apoyar/` y registrado como fuente pública, **comprobar su presencia real** en `.preview-dist/apoyar/index.html` después de `python scripts/build-public-dist.py`, y comprobar `sitemap.xml` (sin declarar una ruta no publicada). Repetir también `python scripts/build-site-shell.py --check`. **No ejecutar Actions desde esta PR de investigación.**

## Opciones UX A/B

- **A, recomendada**: una sola página `/apoyar/` + enlace en footer y microtexto contextual; menos mantenimiento y mejor accesibilidad.
- **B, futura**: un botón compacto contextual que abra selector en diálogo nativo; más trabajo, más riesgo de interrupción y de problemas de foco. No hacer en V1 sin datos de necesidad.

Prioridad de implantación: A en footer/página central → prueba con dos herramientas → 1 artículo → medir clicks agregados anónimos (si la política de analytics lo permite) → decidir si ampliar. No usar conversiones con datos personales ni tracking de pagos.

## Dependencias y fuentes

- Código reutilizado de nuestro proyecto: `scripts/build-site-shell.py`, `data/navigation.json`, `data/content-registry.json`, `assets/v1-shell.css`, `assets/v1-home-editorial-v3.js`.
- APIs y checkout alojados, ver PR hijas PayPal/Stripe/Ko-fi.
- No se ha copiado código de librería ajena en esta PR: los ejemplos son HTML/CSS/JS originales, completos para la integración prevista y sin runtime secreto.
