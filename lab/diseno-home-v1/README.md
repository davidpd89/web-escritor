# LAB HOME V1 — paquete ejecutable de Drive

Estado: paquete de preparación para integrar primero en `/lab/diseno-home-v1/` de `implementacion-web-2026`. No modifica por sí mismo Home pública, `styles.css`, `script.js` ni `main`.

Baseline técnico verificado: `davidpd89/web-escritor@implementacion-web-2026` · HEAD `5c4a9afca7c009bd78d5dd44ca4b6c656239527c` (21/08/2026). Refrescar antes de cualquier escritura si la rama cambia.

## Qué contiene

- una base HTML semántica común para V1-A/V1-B;
- diferencias A/B solo por tokens/CSS autorizados;
- shell con `Explorar` mediante `<dialog>`;
- hero con una única acción primaria;
- cartografía de siete territorios;
- ruta móvil propia;
- río editorial breve;
- estados H0/H1/H6;
- fixtures hostiles;
- Gate 0 sin media mediante `components.html`;
- contratos machine-readable de rutas y media;
- auditoría de la rama activa;
- mapa exacto de migración;
- validador estático sin dependencias.

## Árbol de autoridad

```text
37 — LAB HOME V1 — CÓDIGO LISTO PARA INTEGRAR/
  index.html
  components.html
  README.md
  INTEGRATION.md
  BRANCH-AUDIT.md
  QA.md
  css/
    fonts-lab.css
    tokens.css
    home.css
    variants.css
    components.css
  js/
    fixtures.js
    lab.js
  data/
    media-manifest.json
    routes.json
  scripts/
    validate_lab.py
  assets/las-manecillas/
    ...copias Drive de procedencia/respaldo...
```

Las copias de `assets/las-manecillas/` en Drive NO significan crear esa jerarquía en GitHub. La rama activa ya tiene las cubiertas oficiales en `/assets/portada-las-manecillas-del-recuerdo-*.webp` y el lab se ha corregido para reutilizarlas.

## Estado de rutas

Confirmadas en la rama objetivo: Manecillas, Samuel, Autor, Cuaderno, Herramientas, Prensa y Eventos.

`/herramientas/` ya existe, reúne 17 utilidades y está en el sitemap de `implementacion-web-2026`; deja de ser un bloqueo.

Estado Jaula: `/donde-empieza-la-jaula/` todavía no existe en la rama, pero ya hay contenido público autorizado y scaffold (`book-jaula.html` + `JAULA-PUBLIC-SPEC.md` + `data/jaula-preservation.json`). Puede construirse en staging; no puede llegar a navegación/sitemap/producción hasta verificar ruta 200 y gates.

## Gate 0 — identidad sin media

`components.html` elimina fotografía y portada para comprobar si la firma se sostiene mediante tipografía, escala, filetes, ritmo, controles, ledger y jerarquía desigual.

Si al ocultar logo/media queda «una web beige limpia», el sistema falla aunque la Home con cubierta impresione.

## Diferencias A/B permitidas

A y B comparten:

- HTML;
- copy;
- rutas;
- shell;
- `<dialog>`;
- contenido;
- estados;
- fixtures;
- assets.

Solo cambian las dimensiones expresamente aprobadas por el contrato 19. `variants.css` no puede reestilizar Explore/nav ni ocultar contenido para favorecer una variante.

## Fixtures

Parámetros de lab:

- `?variant=a|b`
- `?state=h0|h1|h6`
- `?fixture=long|extreme|no-media|sparse|font-fallback`

Los fixtures prueban composición; no modifican arquitectura ni se publican.

## Media

El lab apunta a los assets reales ya presentes en la rama:

- `/assets/portada-las-manecillas-del-recuerdo-320.webp`
- `/assets/portada-las-manecillas-del-recuerdo-512.webp`
- `/assets/portada-las-manecillas-del-recuerdo-768.webp`
- `/assets/portada-las-manecillas-del-recuerdo-1024.webp`
- `/assets/david-porto-foto-portada-sinfondo.webp` como retrato A/B seleccionado y trazado. El archivo es RGBA 433×577 y el CSS lo limita a 430 px de ancho máximo, por lo que no existe upscale destructivo en desktop; en móvil siempre reduce.

La cubierta plana es la autoridad. `manecillas-book-mockup.webp` pertenece al sistema anterior y no entra en V1.

## Qué NO debe importarse del sistema actual

El lab no carga `styles.css`, `manecillas-extras.css` ni `script.js`. La rama activa todavía usa dark global, gradients, Cormorant/Inter, pills, card elevation, glass, mockup y Explore generado por JS. Es baseline funcional, no vocabulario V1.

Ver `BRANCH-AUDIT.md` para el delta exacto y `INTEGRATION.md` para la estrategia de retirada sin regresiones.

## Riesgo de staging/producción

`.assetsignore` de la rama activa no excluye `lab/`. Eso permite probar el lab por HTTP en staging cuando se integre. Antes de producción, después del QA, se decide eliminarlo del conjunto promovido o añadir `lab/` a `.assetsignore`.

Siempre: `noindex`, fuera de sitemap y fuera de nav pública.

## Validador

Ejecutar desde la raíz del paquete:

```bash
python scripts/validate_lab.py
```

Comprueba, entre otros:

- ficheros requeridos;
- un H1 por specimen;
- IDs duplicados;
- handlers inline;
- `noindex`;
- ausencia de CSS/JS de producción;
- `<dialog>` nativo;
- paleta histórica prohibida;
- ausencia de jerarquía duplicada `/assets/las-manecillas/` en el código de integración;
- cuatro tamaños de cubierta;
- siete territorios;
- Herramientas como ruta verificada en rama objetivo;
- Jaula marcada como contenido autorizado / ruta todavía no disponible en rama;
- variantes A/B sin contaminar navegación.

## Orden de trabajo

1. seguir mejorando Drive;
2. refrescar rama/HEAD antes de integración;
3. integrar solo lab cuando se autorice;
4. QA Gate 0 + A/B + responsive;
5. elegir variante;
6. migrar shell;
7. migrar Home;
8. migrar Manecillas;
9. extender familias;
10. limpieza/producción solo con gates.


## Matriz de migración ejecutable

- `MIGRATION-MATRIX.md`: relación humana exacta entre selectores/funciones actuales y componentes V1, con condición de retirada y QA.
- `data/migration-map.json`: la misma frontera en formato legible por máquina para impedir borrados masivos o integración contra la rama equivocada.

La matriz no autoriza eliminar `styles.css`, `script.js` ni `manecillas-extras.css`: identifica qué consumidores deben migrar primero y qué evidencia exige cada retirada.


## Actualización 20/08/2026 — navegación móvil y formularios compartidos

El lab ya no oculta la navegación primaria en tablet/móvil. `Obra`, `Cuaderno` y `Herramientas` siguen siendo enlaces directos en una segunda fila del header; `Explorar` amplía la arquitectura, no la sustituye. El shell debe conservar este comportamiento en cualquier familia.

Los controles de formulario compartidos se han centralizado en `css/base.css`: `form-field-label`, `form-row`, `form-input`, `form-submit`, `form-consent`, `form-help` y `form-status`. `home.css` y `book.css` solo pueden gobernar composición de la sección, no recrear inputs/botones/consentimiento.

El newsletter de Home del lab usa hooks próximos a producción (`newsletter-form-home`, `nl-email-home`, `nl-gdpr-home`, `nl-status-home`) y exige correo válido + consentimiento. `js/lab.js` valida ambos estados localmente y nunca hace `fetch` ni envía datos.

## Estado tras QA renderizado — 20/08/2026

El paquete ha pasado validación estática y una primera ejecución renderizada de geometría/interacción en Home A/B, Libro V1 y Gate 0. Se corrigieron tres fallos reales: semántica `hidden`, captura limpia de Libro y shell landscape de altura baja. También pasan dialog/focus, newsletter local, text-spacing y no-JS.

Esto NO selecciona variante A/B. El retrato real ya está incorporado y ha pasado el gate de resolución/composición técnica. La procedencia y configuración exacta de Instrument Serif + Manrope + Newsreader está congelada en `data/font-contract.json`, y `fonts-lab.css` carga también la italic 400 real de Newsreader. Sigue pendiente el gate VISUAL de esas fuentes cargadas; no se elige A/B por geometría con fallback.


## Actualización 20/08/2026 — asset de autor + contrato tipográfico

El retrato A/B queda fijado en `david-porto-foto-portada-sinfondo.webp`. Se comparó con tres fotografías reales de mayor resolución, pero todas conservan fondo y alterarían la composición superpuesta; no son sustitutos técnicos equivalentes. `data/media-manifest.json` registra IDs de origen/copia, dimensiones, alpha, ancho CSS máximo, alternativas revisadas y motivo de selección.

`data/font-contract.json` convierte la decisión 07 en contrato ejecutable: Instrument Serif 400/italic; Manrope 400/500/600/700; Newsreader 400/600 + italic 400 real. El import de Google Fonts queda permitido SOLO en `fonts-lab.css`; producción debe self-host WOFF2 y no puede copiar ese import remoto. El validador falla ante una cuarta familia, pesos desviados, ausencia de Newsreader italic, remote import fuera del lab o cambio de la política self-host.

Estado: procedencia/configuración tipográfica = cerrada. Juicio visual tipográfico = pendiente. Ganador A/B = pendiente.


## POLÍTICA DE DRIFT DE RAMA — 20/08/2026

Último HEAD auditado para este paquete: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

Este SHA es una baseline informativa, no un bloqueo rígido. Antes de cualquier integración se compara este HEAD con el HEAD actual de `implementacion-web-2026`. Solo se reabre una decisión V1 si el delta toca archivos/contratos relevantes para esa decisión. Cambios aislados de CI, herramientas u otras familias no obligan a rehacer Home o Libro. `main` no es destino de integración.

### Estado añadido — Manecillas

La ficha Libro V1 preserva ya los deep links públicos `#aviso`, `#muestra`, `#sinopsis-editorial` y `#newsletter-manecillas`; mantiene la dedicatoria pública como una única pausa editorial y usa newsletter como CTA de hero mientras no existan retailers verificados. Estas reglas están en `data/manecillas-preservation.json`, `data/migration-map.json` y los validadores. La revisión visual real de hashes/scroll en 390/768/1440 sigue siendo gate manual; el entorno de ejecución actual bloquea Chromium/Playwright contra localhost y no se registra como PASS.

## Actualización 21/08/2026 — cobertura completa de familias para Claude

El paquete deja de terminar en Home/Manecillas/Cuaderno. Se incorpora la extensión V1 con scaffolds ejecutables para Autor, Prensa, Eventos/Ferias, Libros, Herramientas, referencias, companions, fragmentos, wayfinding y secundarias, más dos familias propias que no deben resolverse por reutilización oportunista:

- `book-samuel.html` + `css/samuel.css` + `data/samuel-preservation.json`;
- `awards.html` + `css/awards.css` + `data/awards-preservation.json`.

`data/route-inventory.json` cubre 55/55 rutas del sitemap, tres páginas operativas fuera del sitemap y Jaula como ruta adicional autorizada para staging, todavía fuera de sitemap/producción. `scripts/validate_extension.py` impide que la extensión reintroduzca clases/recursos típicos de tiles, pills, glass, gradientes o runtimes de motion globales.

El estado correcto es `CLAUDE_IMPLEMENT_READY = YES_FOR_STAGING_IMPLEMENTATION`, no `MERGE_READY`. Ver `CLAUDE-HANDOFF.md`.


## Actualización 21/08/2026 — absorción Perplexity 1 + Jaula

El informe temporal Perplexity 1 fue auditado completo y absorbido en los contratos maestros. El paquete NO adopta Lenis, GSAP/ScrollTrigger, Motion sin caso, reveals genéricos, nuevas fuentes, assets IA, Lottie/hero-video ni breakpoints por dispositivo. Sí conserva como refuerzo Stripe Press (ritmo de ficha), MagCulture (escala editorial desigual), link affordance y reglas de motion auditable (`transition` por propiedades concretas + cancelación dinámica con reduced motion).

Jaula deja de ser un placeholder sin contenido: el scaffold contiene el capítulo 1 extraído automáticamente del manuscrito canónico, con hash registrado en `data/jaula-preservation.json`. La fuente puede evolucionar; antes de publicar se vuelve a verificar el hash/corte contra el manuscrito vigente.
