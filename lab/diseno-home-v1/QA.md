# QA — LAB HOME V1

Este checklist valida el sistema nuevo antes de tocar la Home pública. Drive es autoridad de preparación; la futura prueba HTTP se hace contra `implementacion-web-2026`.

Baseline verificado en esta pasada: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

## 0. Preflight de rama

- [ ] refrescar HEAD antes de integrar;
- [ ] si cambió, revisar `BRANCH-AUDIT.md` y rutas/assets afectados;
- [ ] `main` no es destino de escritura del lab;
- [ ] `/lab/diseno-home-v1/` no existe previamente o se compara antes de sobrescribir nada;
- [ ] `python scripts/validate_lab.py` = PASS.

## 1. Gate 0 — identidad sin media

Abrir `components.html` sin fotografías/portadas.

- [ ] todavía se reconoce una gramática propia;
- [ ] no depende de una cuadrícula de cards;
- [ ] Instrument/Manrope/Newsreader cumplen roles distintos;
- [ ] escala editorial desigual;
- [ ] filetes/rutas ayudan a leer estructura;
- [ ] espacio negativo no parece vacío arbitrario;
- [ ] botones rectangulares, sin pills rutinarias;
- [ ] ledger no parece ecommerce/SaaS;
- [ ] estados se entienden sin colores semánticos inventados;
- [ ] ocultar logo no destruye toda la identidad.

FAIL automático humano: «solo queda una web beige limpia».

## 2. A/B limpio

- [ ] mismo HTML/copy/rutas/assets;
- [ ] Explore y navegación idénticos;
- [ ] ninguna variante oculta contenido;
- [ ] una variante no añade más CTA/credenciales/media;
- [ ] fixtures producen exactamente los mismos datos en A y B;
- [ ] no mezclar A+B sin nueva prueba.

## 3. Viewports

Capturas mínimas:

- [ ] 320 stress;
- [ ] 390 primer viewport;
- [ ] 390 mapa/río/newsletter;
- [ ] 768 hero + cartografía;
- [ ] 1024 hero + mapa;
- [ ] 1440 primer viewport;
- [ ] 1440 página completa;
- [ ] 1728 primer viewport.

Comprobar:

- [ ] sin horizontal scroll;
- [ ] mobile recompone, no encoge desktop;
- [ ] título no fuerza escalas comerciales pequeñas;
- [ ] portada conserva ratio;
- [ ] targets >=44 CSS px donde corresponda;
- [ ] safe area/landscape según doc 36.

## 4. Rutas del mapa

En staging de la rama objetivo:

- [ ] `/las-manecillas-del-recuerdo/` → 200;
- [ ] `/libros/samuel-entre-mundos/` → 200;
- [ ] `/autor.html` → 200;
- [ ] `/cuaderno/` → 200;
- [ ] `/herramientas/` → 200;
- [ ] `/prensa.html` → 200;
- [ ] `/eventos.html` → 200;
- [ ] `/donde-empieza-la-jaula/` NO se considera aprobada mientras siga 404.

Si Jaula sigue sin ruta, la Home pública no puede promocionarse con un enlace roto. El lab sí puede conservar el nodo `data-route-planned="true"` para probar composición.

## 5. Assets

En staging:

- [ ] `/assets/portada-las-manecillas-del-recuerdo-320.webp` → 200;
- [ ] 512 → 200;
- [ ] 768 → 200;
- [ ] 1024 → 200;
- [ ] portrait candidato → 200;
- [ ] LCP no lazy;
- [ ] width/height o ratio reservado;
- [ ] no se carga `manecillas-book-mockup.webp` en el lab V1;
- [ ] no existen referencias del lab a `/assets/las-manecillas/` en GitHub.

## 6. Explore `<dialog>`

Teclado:

- [ ] botón abre;
- [ ] foco entra en diálogo;
- [ ] Tab/Shift+Tab no pierde control;
- [ ] Esc cierra;
- [ ] foco vuelve al disparador;
- [ ] close visible;
- [ ] enlaces reales;
- [ ] coarse pointer no requiere hover previo.

Fallback:

- [ ] sin JS la navegación primaria sigue disponible;
- [ ] el mapa sigue teniendo links HTML reales;
- [ ] no aparece un botón muerto como única vía.

## 7. Focus / teclado / zoom

- [ ] Tab completo desde skip link a footer;
- [ ] focus visible sobre Paper/Ink;
- [ ] hover tiene paridad con focus;
- [ ] 200 % zoom sin pérdida funcional;
- [ ] 320 CSS px reflow;
- [ ] ningún control crítico usa ellipsis;
- [ ] focus no queda tapado por header/dialog.

## 8. Hostile fixtures

Probar:

- [ ] `long`;
- [ ] `extreme`;
- [ ] `no-media`;
- [ ] `sparse`;
- [ ] `font-fallback`;
- [ ] H0;
- [ ] H1;
- [ ] H6.

No corregir el fixture para salvar el diseño. Si rompe, corregir componente/tokens.

## 9. Motion

Normal:

- [ ] feedback 120–180 ms;
- [ ] estado 180–260 ms;
- [ ] reveal 360–520 ms;
- [ ] sin parallax;
- [ ] sin magnetic/follow-cursor;
- [ ] sin split chars;
- [ ] sin fade-up universal.

Reduced:

- [ ] jerarquía intacta;
- [ ] diálogo usable;
- [ ] mapa completo;
- [ ] ninguna información depende del movimiento.

## 10. Tipografía

- [x] Instrument Serif = display; fuente/licencia/archivo oficial fijados en `data/font-contract.json`;
- [x] Manrope = UI/metadata; pesos 400/500/600/700 fijados;
- [x] Newsreader = lectura; 400/600 + italic 400 real cargada en lab;
- [ ] fallback no destruye jerarquía;
- [ ] 58–72ch aprox. en lectura larga cuando corresponda;
- [x] sin cuarta fuente decorativa;
- [x] self-hosting pendiente antes de producción está registrado como gate y remote import queda vetado fuera de `fonts-lab.css`.

## 11. Contraste / color

- [ ] componentes consumen roles semánticos;
- [ ] no hex históricos dentro de componentes nuevos;
- [ ] no información solo por color;
- [ ] metales no se usan como texto pequeño sin contraste;
- [ ] no gradientes como firma del sistema;
- [ ] no global dark impuesto por herencia del CSS anterior.

## 12. Performance

El lab puede usar fuente remota provisional, pero la dirección debe ser viable:

- [ ] sin librería de animación;
- [ ] sin vídeo hero;
- [ ] sin previews multimedia precargadas;
- [ ] sin CLS grande por media;
- [ ] cubierta LCP desde markup inicial;
- [ ] no carga `styles.css`, `manecillas-extras.css` ni `script.js`.

## 13. Staging y fuga del lab

Mientras se prueba:

- [ ] `/lab/diseno-home-v1/` sirve por HTTP en staging;
- [ ] meta robots contiene `noindex`;
- [ ] lab NO está en `sitemap.xml`;
- [ ] lab NO está en nav pública;
- [ ] `.assetsignore` todavía puede permitirlo durante QA.

Preproducción:

- [ ] elegir eliminar lab del conjunto promovido o añadir `lab/` a `.assetsignore`;
- [ ] comprobar por HTTP que producción no lo sirve si debe quedar oculto;
- [ ] no bloquear staging prematuramente añadiendo `lab/` antes de terminar QA.

## 14. No regresión de la Home activa

Antes/después:

- [ ] canonical;
- [ ] title/meta;
- [ ] OG/Twitter;
- [ ] `WebSite`/`WebPage`/`Person`/`Book` schema;
- [ ] `@id` canónicos;
- [ ] copy permanente `Publicada el 3 de septiembre de 2026`;
- [ ] descriptor global `Escritor`;
- [ ] enlaces Manecillas/Samuel;
- [ ] newsletter backend/privacidad;
- [ ] analytics aprobados;
- [ ] sitemap;
- [ ] Lighthouse/CWV.

## 15. Score

Aplicar doc 28:

- >=88/100 para extensión;
- >=92/100 como umbral interno de candidatura;
- navegación/mobile/accesibilidad/función nunca pueden compensarse con «impacto visual».

Una Home vistosa con un enlace 404, foco roto o móvil mediocre falla.


## Preflight de migración

Antes de cualquier parche de producción:

- `MIGRATION-MATRIX.md` y `data/migration-map.json` deben corresponder al HEAD objetivo actual;
- la matriz debe seguir incluyendo Explore legacy, mobile bottom nav, hooks del newsletter Home, `source=home`, `styles.css`, `manecillas-extras.css` y el gate de Jaula;
- una eliminación legacy necesita cumplir `remove_when` + `tests`;
- ninguna limpieza puede ejecutarse por nombre de clase compartido sin inventario de consumidores.


## Gate añadido — navegación móvil directa

FALLA si a ≤1023 px `.primary-nav` desaparece o si una ruta primaria solo queda accesible al abrir `Explorar`.

Comprobar en 320/390/768 y landscape de baja altura:

- marca + `Explorar` en primera fila;
- `Obra`, `Cuaderno` y `Herramientas` en segunda fila;
- targets ≥44 px;
- sin clipping horizontal destructivo;
- overflow horizontal de la fila permitido solo como resiliencia extrema, nunca para esconder el primer enlace;
- foco visible y orden DOM: marca → navegación → Explorar o, si el CSS reordena visualmente, sin alterar el orden de teclado esperado.

## Gate añadido — newsletter/consentimiento

Home y Libro deben reutilizar las primitivas de `base.css`; no se admiten implementaciones de controles duplicadas en CSS de familia.

Secuencia mínima de prueba:

1. submit vacío → error de email + foco en email;
2. email válido sin consentimiento → error específico + foco en checkbox;
3. email válido + consentimiento → status de éxito de laboratorio;
4. ninguna de las tres acciones realiza petición de red;
5. `role=status`/`aria-live` comunica resultado;
6. teclado móvil no tapa campo, consentimiento, error ni submit;
7. a 320 px el botón pasa a ancho completo y no aparece overflow.

## EJECUCIÓN REAL — 20/08/2026 — RENDER + INTERACCIÓN + RESILIENCIA

Esta sección registra pruebas ejecutadas sobre una reconstrucción local de los ficheros vigentes de Drive. No sustituye la review humana ni aprueba todavía una variante A/B.

### Matriz renderizada

- Home V1-A: 320, 390, 768, 1440.
- Home V1-B: 320, 390, 768, 1440.
- Home landscape/low-height: 667×375.
- Home hostile: título largo y no-media.
- Libro V1 Manecillas: 320, 390, 768, 1440.
- Libro hostile: título largo y metadata parcial.
- Gate 0 / components: 390.

Resultado geométrico: cero overflow horizontal en todos los escenarios anteriores.

### Fallos reales encontrados y corregidos

**VQ-01 — `hidden` resucitado por CSS de componente — CORREGIDO**

El fallback de portada de Libro tenía `hidden`, pero `.book-cover-fallback{display:grid}` anulaba el comportamiento nativo y mostraba simultáneamente portada + fallback. La base V1 incorpora ahora `[hidden]{display:none!important}`. El mismo gate protege related/context/fixtures y cualquier futuro componente con `display:*`.

**VQ-02 — toolbar de Libro contaminaba capturas — CORREGIDO**

Home ya soportaba `?capture=1`; Libro no. `book-manecillas.html` y `book.css` ya comparten el mismo contrato: el modo capture elimina exclusivamente controles de laboratorio, nunca contenido de usuario.

**VQ-03 — header móvil demasiado alto en landscape — CORREGIDO**

En 667×375 el shell ocupaba ~130 px sticky. Se añadió recomp específica de altura baja para 560–1023 px y ≤520 px de alto. Resultado medido: ~61 px, una sola fila, orden DOM/visual coherente y Obra + Cuaderno + Herramientas + Explorar visibles. No se bloquea orientación ni se pide girar el dispositivo.

### `<dialog>` Explorar — prueba interactiva

320×760:
- diálogo: 312×752;
- botón cerrar: 44×44;
- foco inicial en cerrar: PASS;
- Escape cierra: PASS;
- foco vuelve a Explorar: PASS.

667×375:
- diálogo: 659×367;
- botón cerrar: 44×44;
- foco inicial en cerrar: PASS;
- Escape cierra: PASS;
- foco vuelve a Explorar: PASS.

### Newsletter Home — secuencia funcional de laboratorio

1. submit vacío → «Introduce una dirección de correo válida.» y foco a `nl-email-home`;
2. email válido sin consentimiento → «Acepta la política de privacidad para continuar.» y foco a `nl-gdpr-home`;
3. email + consentimiento → estado de éxito de laboratorio;
4. cero `fetch`/petición de red en el lab.

Producción seguirá conservando el backend Brevo y analytics existentes; este test solo valida UI/semántica/errores.

### Fixtures Libro — visibilidad real

- normal: fallback de portada = `display:none`;
- `partial-meta`: PVP y páginas ocupan 0 px;
- `related-none`: módulo Related ocupa 0 px;
- `no-context`: bloque de contexto ocupa 0 px.

No quedan huecos fantasma por contenido `hidden`.

### Text-spacing override — 320 CSS px

Aplicado a Home, Libro y components con aumento de line-height, letter-spacing, word-spacing y separación de párrafos. Resultado: `scrollWidth === 320` en los tres casos. PASS de reflow geométrico; la revisión visual humana sigue siendo obligatoria.

### No-JS — 320 CSS px

Home y Libro:
- contenido principal presente;
- Obra/Cuaderno/Herramientas visibles con targets de 44 px;
- Explorar oculto como enhancement JS;
- cero dependencia del diálogo para navegar.

PASS.

### LIMITACIONES DE ESTA PASADA — NO CONFUNDIR CON APROBACIÓN VISUAL

El renderer aislado no pudo cargar el import remoto de Instrument Serif + Manrope + Newsreader. Las capturas de esta ejecución usan fallbacks métricamente razonables y sirven para geometría/reflow, no para aprobar tipografía.

El retrato real `david-porto-foto-portada-sinfondo.webp` ya está incorporado y trazado. Intrínseco 433×577 RGBA; ancho CSS máximo 430 px. PASS técnico de resolución: no hay ampliación destructiva. Se revisaron tres fotografías reales de mayor resolución, pero conservan fondo y cambian la composición; quedan descartadas como reemplazo 1:1.

Por tanto:
- NO hay ganador A/B todavía;
- NO se aprueba acabado tipográfico todavía;
- NO se puntúa identidad final del hero hasta ejecutar el gate visual con las fuentes V1 efectivamente cargadas; el retrato ya no bloquea;
- sí quedan aprobados los fixes estructurales VQ-01/VQ-02/VQ-03 y los gates asociados.


### VQ-04 — Retrato real / resolución

Estado: CORREGIDO / PASS técnico.

- asset: `/assets/david-porto-foto-portada-sinfondo.webp`;
- Drive origen: `1Tb4HxsMokS-eiW4Dqr9pwhxlquV1Qxc9`;
- copia lab: `1EkUZKUv1r7xx9ZNS6abtTqfW-sh-1Nr_`;
- intrínseco: 433×577 RGBA;
- máximo CSS desktop: 430 px;
- no hay upscale destructivo;
- alternativas 4032×3024, 1122×1402 y 1086×1448 revisadas y descartadas como sustitutos técnicos porque incorporan fondo.

### VQ-05 — Cursiva literaria real

Estado: CORREGIDO / PASS de configuración.

`fonts-lab.css` no cargaba Newsreader italic; el navegador podía sintetizarla. Ahora carga Newsreader 400/600 normal + 400 italic real. `data/font-contract.json` y `validate_lab.py` impiden que vuelva a desaparecer.

### Gate tipográfico pendiente

La configuración ya es correcta y verificable, pero no se convierte en aprobación estética. Falta comparar render real 390/768/1440 con fuentes cargadas y fallback, incluyendo Home, header, cartografía, Manecillas, fragmento y una herramienta. Hasta entonces A/B permanece sin ganador.


## POLÍTICA DE DRIFT DE RAMA — 20/08/2026

Último HEAD auditado para este paquete: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

Este SHA es una baseline informativa, no un bloqueo rígido. Antes de cualquier integración se compara este HEAD con el HEAD actual de `implementacion-web-2026`. Solo se reabre una decisión V1 si el delta toca archivos/contratos relevantes para esa decisión. Cambios aislados de CI, herramientas u otras familias no obligan a rehacer Home o Libro. `main` no es destino de integración.


## PASS DRIVE-SOURCE — JAULA + HEAD DRIFT + MANECILLAS CONTRACTS — 20/08/2026

- Jaula: estado editorial visible y no interactivo en Home/Libro; cero enlace a ruta ausente.
- Reconstrucción desde ficheros vigentes de Drive: `validate_lab.py` = PASS antes de este delta.
- Rama objetivo reauditada: `f9b0646884d4ebc4a29664e4144798b5094286ea`; 13 commits desde baseline anterior, sin cambios en página Manecillas, `script.js` ni cubiertas.
- Home: marcador `data-newsletter-source="home"`.
- Manecillas: marcador `data-newsletter-source="manecillas"`; género visible preservado; success copy permanente definido; gate comercial del 03/09 separado del estado editorial.
- PASS posterior a sincronización: reconstrucción con `index.html`, `book-manecillas.html`, manifests y `validate_lab.py` recién descargados de Drive → `LAB VALIDATION: OK` (27/27).


## PASS DRIVE-SOURCE CONFIRMADO — 20/08/2026

Después de subir el delta se volvieron a descargar desde Drive los HTML principales, `migration-map.json`, `manecillas-preservation.json`, `home-preservation.json`, `routes.json`, `media-manifest.json` y `validate_lab.py`. La reconstrucción ejecutó el validador con resultado `LAB VALIDATION: OK` y 27 archivos obligatorios.

Este PASS confirma coherencia de la fuente de trabajo en Drive; no equivale todavía a aprobación visual A/B ni autoriza promoción a producción.

## Delta QA — breadcrumb/primaryImage/muestra — 20/08/2026

Gate 3 añade estas comprobaciones:

- breadcrumb V1 visible = `Inicio → Libros → Las manecillas del recuerdo`;
- enlace intermedio = `/libros/`;
- contrato de preservación incluye `WebPage` canónico, `BreadcrumbList` y `primaryImageOfPage`;
- `primaryImageOfPage` = cubierta plana oficial 1024×1536;
- muestra mantiene `data-nosnippet` y link a `/las-manecillas-del-recuerdo/fragmentos/`;
- `validate_lab.py` falla si el scaffold pierde cualquiera de esas piezas;
- `check_preservation.py` falla en el candidato de producción si JSON-LD y breadcrumb dejan de coincidir.


## Gate Manecillas — compatibilidad de anchors y estado comercial

PASS automático requerido:

- existen `#aviso`, `#muestra`, `#sinopsis-editorial`, `#newsletter-manecillas`;
- aliases de anchors tienen `scroll-margin` y no añaden contenido duplicado;
- la dedicatoria pública aparece exactamente una vez;
- `manecillas-quote-band` no reaparece;
- mientras no haya retailers verificados, `Recibir novedades` enlaza a `#newsletter-manecillas`;
- no se inventan destinos comerciales.

Browser/manual pendiente: abrir cada hash directamente con header sticky en 390/768/1440 y comprobar que el encabezado/sección queda visible y enfocable/legible.

## Gate Libro 768 — corrección contra master 20

El primer CSS heredaba el layout 1024 hasta 767 px y dejaba el H1 con mínimo 72 px en 768, fuera del contrato 48–64 px. Corregido con breakpoint explícito 768–899:

- label + H1 + autor + fecha arriba;
- portada cols 1–5, máximo 280 px de ancho (~420 px alto para la cubierta 2:3);
- lead + CTA + metadata cols 6–12;
- H1 `clamp(3rem, 7vw, 4rem)`;
- lead 20–24 px aprox.;
- metadata 2 columnas y después vuelve a una en móvil.

El navegador real sigue siendo gate: comprobar que 768 no queda ni «desktop encogido» ni «mobile agrandado».

## Matriz de paridad — BOOK MASTER SPEC V1 (doc 20)

| Contrato doc 20 | Evidencia scaffold | Estado |
|---|---|---|
| Página editorial, no ecommerce | portada real + prosa + ledger + fragmento antes de disponibilidad | PASS |
| 1440: H1 72–96 px | base `clamp(4.5rem,6.5vw,6rem)` → ~93.6 px | PASS estático |
| 1440: portada 560–680 px alto | ancho máx. 430 px sobre ratio 2:3 → ~645 px | PASS estático |
| 1440: hero 760–900 sin 100vh | `min-height:clamp(720px,72vw,900px)` | PASS estático |
| 1024: H1 58–76 px | base min 72 px | PASS estático |
| 1024: lead 20–24 px | base ~21.6 px | PASS estático |
| 1024: metadata sale del margen | breakpoint `max-width:1199` la mueve bajo info | PASS estático |
| 768: H1 48–64 px | breakpoint 768–899, `clamp(3rem,7vw,4rem)` | PASS estático tras corrección |
| 768: recomposición propia | título/autor/fecha arriba + cubierta 5/12 + info 7/12 | PASS estático tras corrección |
| 390: gutter 20 px | tokens `--page-gutter` → 20 px | PASS estático |
| 390: H1 44–56 px | ~54.6 px | PASS estático |
| 390: lead 20–23 px | ~21 px | PASS estático |
| 390: portada 55–72vw | 68vw | PASS estático |
| 320: gutter 16–18 px | 16 px | PASS estático |
| 320: H1 40–50 px | 48 px | PASS estático |
| 320: portada 62–76vw | 72vw | PASS estático |
| Portada sin card/mockup/3D | `<picture>` de cubierta oficial, ratio natural | PASS |
| CTA pre-retailer real | `Recibir novedades` → `#newsletter-manecillas` | PASS |
| Metadata ledger, no chips | `<dl class="book-meta-ledger">` | PASS |
| Fragmento visible, no widget | extracto HTML Newsreader + `data-nosnippet` + enlace 3 fragmentos | PASS |
| Contexto real | texto de cubierta oficial | PASS |
| Prensa/eventos de la obra | no hay entradas específicas demostradas en el scaffold; no se inventan | N/A / GATE de contenido real |
| Disponibilidad independiente | `Edición y disponibilidad`, retailers solo tras verificación | PASS pendiente URLs reales |
| Relacionados no ecommerce | Samuel como otra obra + Autor/Cuaderno/Eventos; links HTML | PASS |
| Sharing P1 | Web Share + fallback copiar + status accesible | PASS estático |
| Print | shell/form/share ocultos; título/portada/prosa/metadata + URL | PASS estático |
| Motion | no requerido para comprensión; View Transition no implementada todavía | DEFERRED correcto |
| SEO/schema/head | contrato preservation + checker canónico | PASS estático; producción requiere diff final |
| Accesibilidad | landmarks, foco, reflow CSS, 320, reduced-motion contract | PASS estático / browser pendiente |
| Capturas 1440/1024/768/390/320/1728 | navegador bloqueado en entorno actual | GATE |
| hashes con sticky header | aliases + `scroll-margin`; falta abrirlos en navegador real | PARTIAL |

Conclusión: Gate 3 está **estáticamente alineado con doc 20**. No declararlo cerrado visualmente hasta completar capturas/browser, hashes, zoom 200 %, reduced motion y print preview reales.

## Gate adicional 21/08/2026 — familias completas

Baseline: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

Antes de declarar que Claude puede propagar V1:

- `scripts/validate_extension.py` PASS;
- 55/55 rutas sitemap con scaffold;
- 404/Privacidad/Aviso legal controladas;
- Jaula conserva el enlace público bloqueado mientras la ruta siga ausente, aunque contenido/scaffold ya están autorizados para staging;
- Samuel conserva 13 anchors críticos, datos bibliográficos, Book/WebPage/FAQ/reviews/quiz/retailers;
- Premios separa distinciones formales, selección editorial y trayectoria;
- Herramientas se valida desde builders/fuentes autoritativas cuando sean páginas generadas;
- ningún scaffold de extensión reintroduce card/badge/pill/bento/glass, gradientes decorativos o runtime motion global.

Este gate es estático. La selección A/B y `MERGE_READY` siguen exigiendo navegador/staging real.


## DELTA QA — JAULA AUTORIZADA PARA STAGING — 21/08/2026

El antiguo gate «Jaula bloqueada por falta de contenido» queda sustituido por dos gates separados:

1. **Content gate = PASS**: fuente Drive identificada; capítulo 1 extraído por headings; `jaula-preservation.json` registra source/chapter SHA-256, 133 párrafos y 2158 palabras; copy público limitado a datos soportados.
2. **Route/promotion gate = OPEN**: la ruta aún no existe en `implementacion-web-2026`. Debe fallar cualquier intento de enlazarla desde producción mientras no responda 200 en staging.

Antes de desbloquear: comprobar título/H1, `En desarrollo`, capítulo completo y ordenado, primer/último párrafo contra contrato, ausencia de fecha/editorial/ISBN/PVP/retailer/portada inventados, canonical/meta/schema factual, no-JS, 320/390/768/1440, teclado, lectura/print y cobertura en navegación vigente.

## DELTA JAULA — GATE EJECUTABLE 21/08/2026

`data/jaula-preservation.json` deja de ser un contrato solo documental. Tras materializar la ruta candidata se ejecuta:

`python scripts/check_preservation.py --jaula <staging>/donde-empieza-la-jaula/index.html`

Debe verificar: H1/autor/estado/copy autorizados, CTA, 133 párrafos, 2.158 palabras, SHA-256 exacto del capítulo, primer/último párrafo, `noindex` mientras `productionAllowed=false` y ausencia de metadata comercial/editorial prohibida. Cualquier FAIL bloquea promoción y sitemap.
