# Revisión completa del sitio (2026-09-01 →)

Petición del autor: revisar cada página, cada enlace, cada menú, en cada
dispositivo/resolución, de principio a fin.

## Alcance real y lo que esta auditoría puede y no puede cubrir

- Cobertura automática ya existente en CI (todo en verde sobre `main`
  `b8b97baf` al iniciar esta auditoría): `check-links` (enlaces rotos),
  `pa11y-baseline` (accesibilidad básica), `reflow-sitewide` (overflow a
  320/390/768px y zoom 200%), `lighthouse` (rendimiento), `csp-browser-qa`
  (Content-Security-Policy), `browser-qa`/`funnel-qa`/`ladder-qa` (flujos
  funcionales). Esta auditoría manual NO repite ese trabajo desde cero:
  parte de que ya está cubierto y se centra en lo que la automatización no
  puede juzgar.
- Lo que esta auditoría SÍ cubre: consistencia visual entre páginas
  (homogeneización real, no solo "no hay overflow"), calidad y corrección
  del contenido, navegación/menús en la práctica, breakpoints intermedios,
  jerarquía y legibilidad, cosas que un test automático no sabe evaluar.
- Limitación honesta: esta sesión solo tiene acceso a un navegador
  Chromium con emulación de viewport (móvil/tablet/desktop), no a
  dispositivos físicos reales. Emular un iPhone cambia el ancho de
  pantalla pero NO reproduce bugs específicos del motor WebKit real (el
  bug del vídeo de intro en Low Power Mode, encontrado hoy, es un ejemplo
  exacto de un fallo que esta sesión NUNCA habría detectado sin el aviso
  del autor desde su iPhone real). Cualquier hallazgo "confirmado visual"
  aquí es fiable; cualquier "no reproducido" en Chromium NO es garantía
  de que no ocurra en Safari/iOS real.

## Metodología por página

1. Cargar la página en 3 anchos (375 móvil, 768 tablet, 1440 desktop).
2. Revisar consola (errores JS) y red (fallos de recursos).
3. Revisar cada enlace/menú visible.
4. Comparar contra el sistema de diseño compartido (v1-tokens.css,
   v1-base.css, v1-site-cohesion-v6.css) para detectar inconsistencias.
5. Leer el HTML/CSS/JS específico de la página si algo no cuadra.
6. Corregir bugs claros directamente; señalar decisiones de diseño
   ambiguas al autor en vez de rediseñar por mi cuenta.

## Estado por página

Leyenda: ⬜ pendiente · 🔎 en revisión · ✅ revisada sin hallazgos ·
🛠️ revisada con corrección aplicada · 🚩 revisada con hallazgo pendiente
de decisión del autor.

### Home / núcleo
- ✅ `/` (index.html) — auditoría extensa ya realizada hoy mismo (ver
  resto de esta sesión): flicker de encabezados, padding de Obras,
  márgenes de Universo publicado, vídeo de intro en Low Power Mode,
  overflow del grid por el FAQ `<details>`. Pendiente solo un pase final
  en tablet (768px), no hecho aún hoy.
- ✅ `/autor.html` — sin hallazgos de código; el "typo" que parecía verse
  en pantalla ("Respuessta"/"Oué") es el renderizado de la fuente
  cursiva a tamaño pequeño, verificado contra el HTML fuente real.
- 🚩 `/asistente/` — hero homogeneizado y verificado (colores/fuente del
  botón de envío y el h1 usan ya el azul/Manrope/Instrument Serif del
  sitio). Búsqueda local probada end-to-end: responde con resultados
  reales y enlaces correctos. Pero las burbujas de chat
  (`.assistant-message--user`/`--assistant`) siguen sin ningún estilo
  propio (fondo transparente, sin diferenciación visual entre usuario y
  asistente) — confirma que el rediseño más allá del hero, ya señalado
  como pendiente, sigue sin hacerse. No es un bug nuevo, es la misma
  brecha ya conocida, ahora verificada con datos concretos en vez de
  una impresión.
- ✅ `/mapa-del-sitio/` — 67 enlaces internos, sin overflow; cobertura de
  enlaces rotos ya la hace `check-links` en CI (0 errores/5812 checks).
- ✅ `/404.html` — sin hallazgos.
- ✅ `/offline.html` — sin hallazgos, el mensaje de estado online/offline
  es dinámico vía JS y funciona.

### Libros / universo editorial
- ✅ `/libros/` — sin hallazgos.
- ✅ `/libros/samuel-entre-mundos/` — sin hallazgos en desktop y móvil
  (390px), enlaces de compra/capítulo funcionan.
- ✅ `/las-manecillas-del-recuerdo/` — pase completo (desktop + móvil,
  scroll completo hasta el pie): sinopsis, cita, temas, newsletter
  (nota sin casilla renderizando bien), botón "Compartir ficha"
  verificado funcionando (llama a `navigator.share` con título/URL
  correctos — el bug histórico de `[hidden]` de esta sesión sigue
  arreglado). El botón "Comprar" del header está deliberadamente
  ausente en esta página (código en `build-site-shell.py`: el CTA
  sitewide apunta siempre a Amazon de Samuel, y se oculta aquí a
  propósito para no enlazar el libro equivocado desde la ficha de
  Manecillas) — no es un fallo.
- ✅ `/las-manecillas-del-recuerdo/fragmentos/` — sin hallazgos.
- ✅ `/fragmento/` — sin hallazgos; formulario de newsletter probado
  (email + enviar, sin casilla, pasa la validación correctamente).
- ✅ `/samuel-entre-mundos.html` — stub de redirección limpio (noindex +
  canonical + refresh + enlace de respaldo).
- ✅ `/donde-empieza-la-jaula/` — sin hallazgos; el "cover" gris con
  "En desarrollo" es intencional (libro sin portada aún), contraste
  correcto, correctamente oculto a lectores de pantalla porque la misma
  información ya está en texto accesible cerca.
- ✅ `/universo/noveris/` — sin hallazgos.

### Cuaderno (blog editorial)
- ✅ `/cuaderno/` — sin hallazgos; newsletter probada, "05 piezas
  publicadas" cuenta bien (1 destacada + 4 numeradas 02-05).
- ✅ `/cuaderno/temas/` — sin hallazgos.
- ✅ `/cuaderno/temas/fantasia-de-portales/` — sin hallazgos.
- ✅ `/cuaderno/que-es-el-portal-fantasy/` — sin hallazgos; contenido
  histórico-literario contrastado (Narnia, Alicia, Mago de Oz) correcto.
- ✅ `/cuaderno/portal-fantasy-vs-fantasia-epica/` — sin hallazgos.
- ✅ `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/` — sin
  hallazgos.
- 🚩 `/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/` — ver
  hallazgo #0, datos de terceros no verificables/incorrectos.
- ✅ `/cuaderno/sistema-de-magia-noveris/` — contenido retirado a
  propósito (ver hallazgo #0, contexto); la página en sí funciona bien
  y comunica el retiro con claridad.
- ✅ `/cuaderno/worldbuilding-noveris-ciudad-magica/` — sin hallazgos;
  contenido es proceso creativo propio del autor, no verificable ni
  necesita serlo.
- ✅ `/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/` — sin
  hallazgos; las 4 imágenes que parecían rotas cargan bien
  (falso positivo de mi propio método de scroll instantáneo, no del
  sitio — confirmado con `scrollIntoView` en cada una).

### Herramientas (22 páginas reales, no 17 — ver nota)
Nota: el hub enlaza 20 herramientas públicas más su propia página, y
existe además `/herramientas/auditor-web/`, deliberadamente sin enlazar
desde ningún sitio (noindex, informe interno del propio autor sobre el
estado de la web) — no es un huérfano por error, es intencional.
- ✅ Las 20 herramientas públicas revisadas (desktop + 390px, sin
  overflow en ninguna). Probadas funcionalmente de extremo a extremo
  con datos reales: contador de palabras (recuento exacto), detector de
  repeticiones (detectó "perro" ×3, comienzos repetidos y frases que
  vuelven, con los números cuadrando), legibilidad (INFLESZ/Fernández-
  Huerta/Gutiérrez de Polini/Crawford calculados y coherentes), variedad
  léxica (TTR = formas/palabras exacto, guarda correctamente el aviso
  de "muestra corta" bajo 50/100 palabras), medidor de diálogo (30,4% =
  7/23 exacto), comprobador de nombres (Jaro-Winkler correcto, deduplicó
  bien un nombre repetido, no dio falsos positivos con "Elena"),
  generador de evento+calendario (JSON-LD Event válido con fechas ISO
  8601 y offset UTC correctos), "qué tipo de lector eres" (scoring 6/6
  consistente). El resto (distribución POV, personajes, manuscrito,
  limpiador, metadatos, JSON-LD escritores, auditor de página de libro,
  kit de prensa, tarjeta "estoy leyendo", entrevista familiar,
  convenciones de diálogo, tiempo de lectura en voz alta) verificadas en
  carga y diseño, sin prueba funcional profunda por límite de tiempo de
  esta sesión.

### Club de lectura / comunidad
- ✅ `/clubes-de-lectura/samuel-entre-mundos/` — sin hallazgos.
- ✅ `/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/` — sin
  overflow; estilos de impresión no verificados en esta pasada.
- ✅ `/clubes-de-lectura/preparar-sesion/` — sin hallazgos.
- ✅ `/lectores-beta/` — sin hallazgos, copy claro sobre las dos listas de
  consentimiento distintas (newsletter general vs lectores beta).
- ✅ `/lectores-beta/enviar-manuscrito/` — sin hallazgos, mailto con
  asunto/cuerpo precargados correctamente.
- ✅ `/recomendaciones/` — sin hallazgos; explica el sistema de "estado
  de evidencia" que el resto de la sección cumple con rigor real (ver
  hallazgo #0).
- ✅ `/recomendaciones/magia-con-coste/` — contrastada: cita
  correctamente la "primera ley" de Brandon Sanderson sobre magia dura.
- ✅ `/recomendaciones/portal-fantasy-espanol/` — contrastada: cita
  correctamente a Farah Mendlesohn (Rhetorics of Fantasy, 2008) y el
  ISBN 9788408099031 (El león, la bruja y el armario) verificado exacto
  contra fuentes reales.
- ✅ `/recomendaciones/politica-de-recomendaciones/` — sin hallazgos;
  documenta un precedente real de auto-corrección (23 de agosto de
  2026) que refuerza el hallazgo #0.

### Editoriales / prensa / eventos
- ✅ `/editoriales/` — sin hallazgos; editoriales reales (Minotauro,
  Nocturna, Duermevela) con fecha de comprobación por ficha.
- ✅ `/editoriales/minotauro/` — contrastado: email de envío
  (proyectosminotauro@planeta.es), requisitos (200 páginas, PDF/Word) y
  plazo de respuesta verificados exactos contra la fuente oficial de
  Planeta de Libros.
- ✅ `/editoriales/nocturna-ediciones/` — sin overflow.
- ✅ `/editoriales/duermevela-ediciones/` — sin overflow.
- ✅ `/prensa.html` — corregido (hallazgo #1).
- 🛠️ `/eventos.html` — corregido (ver hallazgo, año de publicación de
  Samuel entre mundos mal puesto como 2026 en el hito editorial).
- ✅ `/ferias.html` — sin hallazgos; fechas y datos de Aranjuez/Madrid
  coinciden con eventos.html.
- ✅ `/premios.html` — sin hallazgos; su propia línea de trayectoria ya
  tenía correcto "2025 · Debut novelístico publicado", lo que confirma
  independientemente que el error de eventos.html era un dato aislado,
  no una ambigüedad real sobre la fecha.
- ✅ `/metodologia-editorial/` — sin overflow.
- ✅ `/convocatorias-escritores/` — contrastada: Premios Literarios Kutxa
  Fundazioa (20.000 €/15.000 €, plazo 21/09/2026) verificado exacto
  contra la fuente oficial de la fundación.

### Legal / recursos / otros
- 🚩 `/privacidad.html` — corregida parcialmente (ver hallazgo #2); el
  párrafo de Brevo ya no afirma una casilla que no existe en ningún
  sitio.
- ✅ `/aviso-legal.html` — sin hallazgos.
- ✅ `/accesibilidad/` — sin hallazgos; declaración honesta, no
  sobreclama conformidad, lista limitaciones reales.
- ✅ `/publicar-web/` — página interna (noindex), checklist de desarrollo,
  sin problemas.
- ✅ `/empieza-aqui/` — sin hallazgos.
- ✅ `/gracias-suscripcion/` — sin hallazgos.
- ✅ `/recursos/ficha-historia-objeto-heredado/` — sin overflow.
- ✅ `/recursos/herramientas-para-escritores/` — sin overflow.

### Otras páginas revisadas
- ✅ `/ai/` — sin overflow (comprobado a 768px, el ancho exacto donde
  falló un CLS puntual en `/autor.html` — ver nota de flakiness).
- ✅ `/lecturas/` — sin hallazgos; contenido marcado explícitamente como
  "fixture de ejemplo, no es una ficha oficial", correctamente
  etiquetado.

### Código compartido (JS/CSS), no solo páginas individuales
- 🛠️ `script.js` — eliminado wiring muerto de un formulario
  (`newsletter-form-home-manecillas-card`) que no existe en ningún HTML
  del sitio; cada `getElementById`/`submitNewsletter` del archivo
  contrastado contra el corpus HTML completo.
- ✅ `assets/v1-shell.js`, `assets/newsletter-general.js`,
  `assets/newsletter-popup.js` — sintaxis verificada, sin otros
  problemas encontrados en esta pasada.
- ⚠️ CI flakiness detectada y descartada como bug real: `identity-public`
  falló una vez con CLS 0,23 en `/autor.html`@768px (umbral 0,1), pero
  el re-run del mismo commit exacto pasó limpio. No reproducible en
  local (Chromium en Windows, mismo `python -m http.server` que usa CI)
  ni tras 1,5s de espera adicional. Probablemente una carrera de carga
  de fuente web específica del runner de Ubuntu. Anotado por si vuelve
  a aparecer — no es algo que este commit haya causado (autor.html no
  tiene ningún cambio de contenido propio en esta sesión, solo la
  cabecera/pie compartidos).

## Hallazgos

0. **[URGENTE — decisión del autor, no corregido]**
   `/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/` ("selección
   2025-2026" de libros de fantasía juvenil española de OTROS autores,
   no de David). Contrastadas las 6 entradas que no son de David contra
   fuentes externas (búsqueda web):

   - **Laura Gallego · "Cuatro Lunas" · fechado 2024 en la web.** Real,
     pero el año está mal: el libro 1 de esta saga ("Mareas de magia")
     se publicó el 2 de abril de **2025** (Editorial SM), no 2024.
     Además "Cuatro Lunas" es el nombre de la SAGA (tetralogía), no de
     un libro suelto — el título exacto sería "Cuatro Lunas 1: Mareas
     de magia".
   - **José Antonio Cotrina · "El ciclo de la Luna Roja" · fechado 2025
     en la web.** Real, pero es una trilogía de **2009-2011** (Alfaguara/
     Hidra, reeditada en 2018) — no una novedad de 2025. Presentarla en
     una lista de "selección 2025-2026" es factualmente incorrecto.
   - **Clara Cortijo · "Los hijos del sol negro".** Búsqueda web no
     encuentra ninguna autora con ese nombre ni ese libro; solo aparece
     una autora distinta y real ("Clara Cortés", con bibliografía
     distinta). No he podido confirmar que esta autora o este libro
     existan.
   - **Ana Ballabriga · "El umbral de plata" · fechado 2026.** Ballabriga
     es autora real, pero de thriller/novela negra (con David Zaplana,
     "La ley del hambre"), no de fantasía juvenil; no se encuentra
     ningún libro con ese título en su bibliografía.
   - **Anabel Botella · "El último cántico".** Autora real con obra
     reciente confirmada (p. ej. "Después del ruido", oct. 2025), pero
     ese título específico no aparece en ninguna fuente encontrada, y
     su perfil conocido es más romántico/contemporáneo que fantasía
     oscura.
   - **Iria G. Parente & Selene M. Pascual · "Paralelo 40".** Autoras
     reales y muy prolíficas; no se ha podido confirmar ni descartar
     este título concreto (podría ser simplemente muy reciente/poco
     indexado — es el caso más dudoso, no el más grave).

   En resumen: de 6 recomendaciones de terceros, 2 tienen datos
   verificablemente incorrectos (año/naturaleza de la obra) sobre
   autores reales, y 2-3 no se pueden verificar en absoluto pese a que
   los autores sí son reales. Esto no es un matiz de estilo: es un
   artículo que atribuye libros/fechas a personas reales y con nombre,
   en la web profesional del autor. Si estos datos no vienen de una
   fuente que David confirmó personalmente al escribir el artículo,
   deberían corregirse o retirarse — no los he tocado porque no tengo
   forma de saber cuál era la intención/fuente original y no quiero
   sustituir una lista posiblemente inventada por otra lista que yo
   mismo tendría que inventar. Necesito que el autor confirme si esta
   lista se basó en investigación real y, si no, decida si prefiere
   corregir los datos (con fuente) o retirar las entradas no
   verificables.

   Contexto que refuerza la sospecha: `/cuaderno/sistema-de-magia-noveris/`
   ya pasó por esto exactamente. Su contenido fue retirado deliberadamente
   (noindex, fuera de sitemap) con esta nota explícita: "La versión
   anterior de esta página incluía detalles que no deben utilizarse aquí
   como referencia confirmada. No se sustituyen por otra explicación
   hasta disponer de respaldo editorial suficiente." Es decir: este
   sitio ya tuvo, al menos una vez, contenido no verificado que alguien
   detectó y retiró. La lista de libros de terceros con datos incorrectos
   encontrada ahora tiene toda la pinta de ser el mismo problema en un
   sitio distinto, todavía sin retirar.

   Más aún: `/recomendaciones/politica-de-recomendaciones/` documenta que
   este problema EXACTO ya ocurrió y se corrigió, con fecha explícita
   ("Corrección de evidencia — 23 de agosto de 2026"): "La autoría de una
   obra, su presencia en una lista o la existencia de una ficha no se
   consideran prueba de lectura personal (...) una edición marcada como
   verificada debe contar con una fuente bibliográfica reproducible."
   Las dos listas reales de Recomendaciones (`/recomendaciones/portal-
   fantasy-espanol/`, `/recomendaciones/magia-con-coste/`) sí cumplen ese
   estándar: cito ISBN reales que he verificado por búsqueda web (p. ej.
   9788408099031 = El león, la bruja y el armario, C.S. Lewis, correcto),
   citan fuentes académicas reales (Farah Mendlesohn, Brandon Sanderson)
   y declaran estado de evidencia por obra. El artículo del Cuaderno no
   sigue nada de este estándar ya existente en el propio sitio: no cita
   fuente, no declara estado de evidencia, no tiene ISBN. No es que falte
   un proceso — es que ese artículo no usó el proceso que el propio sitio
   ya tiene y ya aplicó correctamente en otro sitio.

1. **[Corregido]** `prensa.html`, FAQ de entrevistas ("¿En qué está
   trabajando ahora?"): usaba "se publica el 3 de septiembre de 2026" en
   vez de la redacción autorizada sitewide "publicada el 3 de septiembre
   de 2026" (contrato documentado explícitamente en `ai/index.html`).
   Corregido para que coincida con el resto del sitio.

2. **[Pendiente de decisión del autor]** Inconsistencia real entre
   `privacidad.html` y el comportamiento en producción: la política dice
   dos veces que "el formulario exige marcar la casilla de aceptación de
   esta política antes de poder enviarlo" (afirmación general, sin
   excepciones). Pero de los 9 formularios de newsletter del sitio
   (`script.js`, llamadas a `submitNewsletter`), exactamente 2 —
   `newsletter-form-home` (fallback estático) y `newsletter-form-home-yale`
   (versión mejorada por JS) — pasan `gdprId: null`: no tienen casilla,
   solo una nota "Al enviar tu email, aceptas la política de privacidad."
   Es decir, el ÚNICO formulario de newsletter sin casilla es,
   precisamente, el de la Home — la página con más tráfico del sitio.
   Todos los demás (fragmento, manecillas, home-manecillas-card ×2,
   cuaderno, explore) sí tienen casilla.
   Esto no es un bug de código: es una decisión de base legal (consent
   expreso vía checkbox de RGPD art. 6.1.a, tal y como dice la política,
   frente a "consentimiento por acción inequívoca" sin checkbox, que
   también es válido bajo RGPD pero requiere que el texto de la política
   lo describa así, no como una casilla que en la Home no existe).
   Dos salidas posibles, ninguna aplicada unilateralmente:
   (a) devolver la casilla al formulario de Home, o
   (b) reescribir esas dos frases de `privacidad.html` para describir con
       precisión el mecanismo real (nota de consentimiento por envío en
       Home, casilla en el resto).

   **Decisión del autor (2026-09-01): ninguna casilla en ningún sitio,
   solo email + enviar.** Implementado en PR #319: quitada la casilla de
   `fragmento`, `las-manecillas-del-recuerdo`, `cuaderno`, el diálogo
   Explorar compartido (regenerado en las 68 páginas vía
   `scripts/build-site-shell.py`) y el popup de scroll/exit-intent.
   Actualizada la validación en `assets/newsletter-general.js` y
   `assets/newsletter-popup.js` (si no, habrían bloqueado el envío para
   siempre al buscar una casilla que ya no existe). Corregida la frase de
   `privacidad.html` sobre Brevo que ahora era inexacta para las 9
   formularios, no solo 2. Tests actualizados y en verde en local.
