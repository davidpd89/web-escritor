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
- ⬜ `/autor.html`
- ⬜ `/asistente/` (solo el hero fue homogeneizado hoy; resto de la UI
  pendiente de auditoría completa)
- ⬜ `/mapa-del-sitio/`
- ⬜ `/404.html`
- ⬜ `/offline.html`

### Libros / universo editorial
- ⬜ `/libros/`
- ⬜ `/libros/samuel-entre-mundos/`
- ⬜ `/las-manecillas-del-recuerdo/`
- ⬜ `/las-manecillas-del-recuerdo/fragmentos/`
- ⬜ `/fragmento/`
- ⬜ `/samuel-entre-mundos.html`
- ⬜ `/donde-empieza-la-jaula/`
- ⬜ `/universo/noveris/`

### Cuaderno (blog editorial)
- ⬜ `/cuaderno/`
- ⬜ `/cuaderno/temas/`
- ⬜ `/cuaderno/temas/fantasia-de-portales/`
- ⬜ `/cuaderno/que-es-el-portal-fantasy/`
- ⬜ `/cuaderno/portal-fantasy-vs-fantasia-epica/`
- ⬜ `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/`
- ⬜ `/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/`
- ⬜ `/cuaderno/sistema-de-magia-noveris/`
- ⬜ `/cuaderno/worldbuilding-noveris-ciudad-magica/`
- ⬜ `/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/`

### Herramientas (17 páginas)
- ⬜ `/herramientas/`
- ⬜ `/herramientas/contador-palabras/`
- ⬜ `/herramientas/repeticiones/`
- ⬜ `/herramientas/variedad-lexica/`
- ⬜ `/herramientas/legibilidad/`
- ⬜ `/herramientas/dialogo/`
- ⬜ `/herramientas/dialogo-convenciones/`
- ⬜ `/herramientas/distribucion-pov/`
- ⬜ `/herramientas/personajes/`
- ⬜ `/herramientas/nombres-personajes/`
- ⬜ `/herramientas/manuscrito/`
- ⬜ `/herramientas/limpiador-manuscritos/`
- ⬜ `/herramientas/metadatos-libro/`
- ⬜ `/herramientas/json-ld-escritores/`
- ⬜ `/herramientas/auditor-web/`
- ⬜ `/herramientas/auditor-pagina-libro/`
- ⬜ `/herramientas/kit-prensa-escritores/`
- ⬜ `/herramientas/eventos-ics/`
- ⬜ `/herramientas/entrevista-familiar/`
- ⬜ `/herramientas/tiempo-lectura-voz-alta/`
- ⬜ `/herramientas/tarjeta-estoy-leyendo/`
- ⬜ `/herramientas/que-tipo-de-lector-eres/`

### Club de lectura / comunidad
- ⬜ `/clubes-de-lectura/samuel-entre-mundos/`
- ⬜ `/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/`
- ⬜ `/clubes-de-lectura/preparar-sesion/`
- ⬜ `/lectores-beta/`
- ⬜ `/lectores-beta/enviar-manuscrito/`
- ⬜ `/recomendaciones/`
- ⬜ `/recomendaciones/magia-con-coste/`
- ⬜ `/recomendaciones/portal-fantasy-espanol/`
- ⬜ `/recomendaciones/politica-de-recomendaciones/`

### Editoriales / prensa / eventos
- ⬜ `/editoriales/`
- ⬜ `/editoriales/minotauro/`
- ⬜ `/editoriales/nocturna-ediciones/`
- ⬜ `/editoriales/duermevela-ediciones/`
- ⬜ `/prensa.html`
- ⬜ `/eventos.html`
- ⬜ `/ferias.html`
- ⬜ `/premios.html`
- ⬜ `/metodologia-editorial/`
- ⬜ `/convocatorias-escritores/`

### Legal / recursos / otros
- 🚩 `/privacidad.html` — ver hallazgo #2, texto legal no coincide con el
  comportamiento real de 2 de los 9 formularios de newsletter del sitio.
- ⬜ `/aviso-legal.html`
- ⬜ `/accesibilidad/`
- ✅ `/publicar-web/` — página interna (noindex), checklist de desarrollo,
  sin problemas.
- ⬜ `/empieza-aqui/`
- ✅ `/gracias-suscripcion/` — sin hallazgos.
- ⬜ `/recursos/ficha-historia-objeto-heredado/`
- ⬜ `/recursos/herramientas-para-escritores/`

### Otras páginas no cubiertas por pa11y-baseline (fuera de las
categorías de arriba, revisadas por ser el hueco real de cobertura
automática)
- ✅ `/404.html` — sin hallazgos.
- ✅ `/offline.html` — sin hallazgos, el mensaje de estado online/offline
  es dinámico vía JS y funciona.
- ✅ `/samuel-entre-mundos.html` — stub de redirección limpio (noindex +
  canonical + refresh + enlace de respaldo).
- ✅ `/donde-empieza-la-jaula/` — sin hallazgos; el "cover" gris con
  "En desarrollo" es intencional (libro sin portada aún), contraste
  correcto, correctamente oculto a lectores de pantalla porque la misma
  información ya está en texto accesible cerca.
- ✅ `/lectores-beta/` — sin hallazgos, copy claro sobre las dos listas de
  consentimiento distintas (newsletter general vs lectores beta).
- ✅ `/lectores-beta/enviar-manuscrito/` — sin hallazgos, mailto con
  asunto/cuerpo precargados correctamente.
- ⬜ `/asistente/` (pendiente auditoría completa más allá del hero)

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
