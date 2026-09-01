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
- ⬜ `/privacidad.html`
- ⬜ `/aviso-legal.html`
- ⬜ `/accesibilidad/`
- ⬜ `/publicar-web/`
- ⬜ `/empieza-aqui/`
- ⬜ `/gracias-suscripcion/`
- ⬜ `/recursos/ficha-historia-objeto-heredado/`
- ⬜ `/recursos/herramientas-para-escritores/`

## Hallazgos

(se añaden aquí a medida que se confirman, con página, descripción,
severidad y estado: corregido / pendiente de decisión)
