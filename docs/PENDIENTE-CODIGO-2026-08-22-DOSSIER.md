# Pendiente de código — revisión file-by-file del dossier

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Destino: esta PR

> **Para quién es esto.** Para la sesión que va a implementar. Esta lista sale
> de una revisión **fichero a fichero** de `WEB DAVID PORTO nuevas ideas/`
> (dossier de ~40 documentos) contra el HEAD real de esta rama — no es un
> resumen de lo que dice el dossier, es lo que sigue faltando después de
> comprobarlo con `grep`/`find`/lectura directa. Cada punto trae la evidencia.
>
> Los ficheros del dossier que ya estaban 100% resueltos se han movido a
> `WEB DAVID PORTO nuevas ideas/COMPLETADO/`. Esta PR cubre solo lo que
> quedó pendiente en los que se quedaron fuera.
>
> **Lo que NO entra aquí:** diseño visual final, contenido editorial (artículos,
> fichas, investigación), decisiones de negocio (fecha/PVP/tiendas de
> Manecillas), y cualquier cosa que dependa de que David lea/decida/autorice
> algo primero. Eso se marca como "no-código" en cada punto.

---

## Reglas de la casa (las mismas de siempre, no cambian)

1. **Una puerta que no se dispara se ve igual que una que pasa.** Si tocas un
   workflow, rómpelo a propósito, mira el job en rojo, revierte, y dilo en la
   PR.
2. **Escribir la assertion no es cumplirla.** Si añades un contrato, dejar el
   producto cumpliéndolo en la misma PR o marcar la PR como DRAFT explicando
   qué falta.
3. **No debilitar una assertion para poner CI en verde.** Si algo falla, el
   fallo es la información.
4. **No se toca `main` ni se despliega el Worker.** Esta PR va contra
   `implementacion-web-2026`.
5. No inventes un PASS. Si no puedes probar algo (falta de navegador, falta de
   acceso, falta de contenido real), dilo explícitamente.

---

## A. Doble autoridad sobre `sitemap.xml` — BLOQUEANTE, confirmado 6 veces

### El problema

`.github/workflows/update-dates.yml` **sigue en el repo** y sigue teniendo
`contents: write` + auto-commit a `main`. Su objetivo original (mantener
`lastmod` del sitemap) ya lo cubre `scripts/build-sitemap.py`, que usa
`dateModified` del JSON-LD como única fuente y se verifica con `--check` dentro
de `.github/workflows/content-index-check.yml`.

Esto no es una opinión mía: el propio dossier lo documenta como decisión ya
tomada y pendiente de aplicar en al menos 6 ficheros distintos (`00_INDICE_Y_DECISIONES.md`
§"Decisión técnica 16/08", `01_AUDITORIA_ACTUAL.md` P2, `15_REGISTRO_DE_CORRECCIONES.md`
C-073, `16_IMPLEMENTACION_CODIGO_LISTA.md`, `18_AUDITORIA_REPOSITORIO_SEGUNDA_VUELTA.md`,
`27_REPOSITORIOS_Y_MEJORAS_IMPLEMENTABLES_2026-08-16.md` §18).

Verificado en HEAD:

```bash
$ ls .github/workflows/update-dates.yml
.github/workflows/update-dates.yml        # todavía existe
```

Es un accidente que hoy sea inofensivo: su `sed` ya no encaja con el formato
de una sola línea que usa el `sitemap.xml` actual, así que no está escribiendo
nada — pero sigue armado, y un cambio de formato del sitemap lo reactivaría
sin que nadie lo note, con dos sistemas escribiendo `lastmod` distinto para la
misma URL.

### Qué hacer

1. Eliminar `.github/workflows/update-dates.yml`.
2. Confirmar que `content-index-check.yml` sigue ejecutando
   `build-sitemap.py --check` (ya lo hace) y que es el único punto que toca
   `sitemap.xml`.
3. Ejecutar `python scripts/build-sitemap.py --check` en local para confirmar
   que el sitemap versionado sigue coincidiendo tras el retiro del workflow
   (no debería cambiar nada, porque el workflow ya estaba inerte).

### Criterio de aceptación

`update-dates.yml` no existe. `git log` de `sitemap.xml` no vuelve a tener
autoría del bot de Actions después de este cambio.

---

## B. Newsletter / Brevo: el flujo de doble confirmación está incompleto

Tres hallazgos independientes, todos verificados contra HEAD, todos dentro del
mismo flujo (alta → confirmación por email → retorno a la web).

### B.1 `/gracias-suscripcion/` no existe — el enlace de retorno del DOI apunta a nada

```bash
$ ls gracias-suscripcion/
ls: cannot access 'gracias-suscripcion/': No such file or directory

$ grep -n "gracias-suscripcion" script.js
645:  if (path.startsWith("/empieza-aqui/") || path.startsWith("/gracias-suscripcion/")) return false;
```

`script.js` ya tiene lógica que reconoce la ruta `/gracias-suscripcion/` (para
no reabrir el popup de newsletter en esa página), pero la página en sí nunca
se creó. El propio dossier (`22_BREVO_GUIA_TECNICA_API_Y_OPERACION.md`,
sección "Actualización 16/08/2026 — página de retorno DOI") ya lo señalaba
como pendiente y dejaba el orden exacto de despliegue:

1. crear `/gracias-suscripcion/index.html` — `noindex,follow`, fija el estado
   local (`localStorage nl-subscribed=1`) antes de cargar el runtime global
   para que el popup no reaparezca;
2. desplegar el Worker con `BREVO_DOI_REDIRECT_URL` apuntando a esa URL (esto
   sí requiere acceso a Cloudflare — no lo hagas sin autorización explícita,
   solo deja el código listo);
3. probar el recorrido solicitud → email → confirmación → retorno →
   `nl-subscribed=1` con una dirección de prueba, sin que eso cree un contacto
   real que haya que limpiar luego a mano.

Sin esta página, el flujo de doble opt-in que ya defiende el Worker
(C-040/C-042 en `15_REGISTRO_DE_CORRECCIONES.md`) termina en un 404 real para
cualquier lector que confirme su email.

### B.2 El Worker no tiene honeypot

```bash
$ grep -n "honeypot" cloudflare-worker-subscribe.js
(sin resultados)
```

El contrato documentado del cliente incluye un campo `website` que actúa como
honeypot (`22_BREVO_GUIA_TECNICA_API_Y_OPERACION.md`: *"`website` es el
honeypot. Si contiene texto, el Worker responde de forma neutra y no crea
contacto."*). No hay ni el campo ni la lógica en el Worker actual.

### B.3 Sin rate limiting

El propio código del Worker lo admite en un comentario:

```js
// cross-site browser requests, but they are NOT rate limiting or bot
// ...
// add Turnstile and/or a KV-backed rate limit; neither is implemented here
```

Confirmado repetidamente en el dossier como puerta de publicación pendiente
(`23_AUDITORIA_WEB_TERCERA_VUELTA_2026-08-15.md`: *"Worker con rate
limiting"* dentro de "Puerta de publicación").

### Qué hacer

- Construir `/gracias-suscripcion/index.html` según el spec de 22_BREVO (no
  hace falta desplegar el Worker para dejar el HTML listo y probado en modo
  aislado).
- Añadir el campo honeypot `website` al contrato cliente→Worker y su
  validación en `cloudflare-worker-subscribe.js` (rechazo silencioso, sin
  revelar al bot que fue detectado).
- Dejar preparado (no necesariamente desplegado) un rate limit KV-backed o
  Turnstile en el Worker, documentando en la PR qué falta para activarlo en
  producción (requiere configuración en Cloudflare, fuera de esta PR).

### Criterio de aceptación

- `/gracias-suscripcion/` responde 200 en local, `noindex,follow`, no reabre
  el popup.
- Un test cubre que un `POST` con `website` relleno no crea contacto y
  responde igual que un alta legítima (sin revelar el motivo del rechazo).
- El código de rate limiting existe y tiene su propio test, aunque no esté
  activado en producción; documentar el gap de configuración de Cloudflare en
  la descripción de la PR.

---

## C. Popup de newsletter: el comportamiento en vivo contradice su propia spec

Hallazgo de la revisión del fichero `16_IMPLEMENTACION_CODIGO_LISTA.md`
(agente de verificación, no inferencia mía sin comprobar): el propio documento
fija una spec más específica en su sección final que el código actual no
cumple.

| | Spec documentada | Código actual |
|---|---|---|
| Scroll trigger | 70% de la página | 60% |
| Temporizador de fallback | **no debe existir** | 30 segundos, sí existe |
| Exit-intent (`mouseleave`) | solo con `hover:hover` + `pointer:fine` | sin filtro de puntero — puede dispararse en móvil |

### Qué hacer

Revisar `script.js` (bloque del popup de newsletter) contra la spec y decidir
**cuál de las dos versiones es la vigente** — puede que el 60%/30s sea una
iteración posterior deliberada que la documentación no llegó a actualizar. Si
es así, corregir la documentación, no el código. Si el código es el que está
desalineado, aplicar la spec documentada y añadir un test de comportamiento
(`qa/`) que cubra los tres puntos.

No toques esto sin decidir primero cuál versión es la correcta — no partas la
diferencia (p.ej. "65%, 15s") sin que quede una razón documentada.

---

## D. Contenido/SEO: piezas de infraestructura documentadas y nunca construidas

Confirmado con `grep` directo contra HEAD, no por lectura del dossier:

### D.1 Sin fecha "Última actualización" visible en artículos

```bash
$ grep -n "Última actualización\|Actualizado el" cuaderno/que-es-el-portal-fantasy/index.html
(sin resultados)
```

`scripts/check-article-dates.py` (C-087 en `15_REGISTRO_DE_CORRECCIONES.md`)
nunca se construyó. Los artículos pueden llevar `dateModified` en JSON-LD sin
que el lector vea ninguna fecha de revisión — riesgo de "frescura falsa" no
detectable a simple vista.

### D.2 Sin permalinks de sección en artículos

Ningún artículo tiene un mecanismo de enlace directo a un H2/H3 concreto
(C-086). `article-tools.js` genera IDs y un índice, pero compartir limpia
todos los hashes; no hay forma de enviar "esta sección exacta de esta guía".

### D.3 Sin vista humana del RSS

```bash
$ find . -iname "*rss-human*" -o -iname "feed.xsl"
(sin resultados, fuera de la carpeta del dossier)
```

`/cuaderno/feed.xml` sigue abriéndose como XML crudo en el navegador (C-088).
No es bloqueante — es UX de una URL de nicho — pero está documentado y
preparado en el dossier sin construir.

### D.4 `premios.html` es la única página que se quedó sin migrar el Speculation Rules

El resto del sitio migró de `prerender` de Samuel/Noveris a `prefetch`
conservador de Manecillas/Libros (C-055). `premios.html` no se tocó en esa
migración — sigue prerenderizando `/libros/samuel-entre-mundos/` y
`/universo/noveris/`.

### Qué hacer

- D.1 y D.4 son las dos con impacto real: D.1 porque toca confianza editorial
  (dato ya señalado como P0 de contenido en varios ficheros), D.4 porque es
  una inconsistencia mecánica fácil de corregir por copia del patrón ya
  aplicado en el resto del sitio.
- D.2 y D.3 son mejoras de UX de nicho, no bloqueantes. Inclúyelas solo si
  hay margen; si no, dejarlas explícitamente fuera y decirlo en la PR.

---

## E. QA / CI: huecos que ya estaban señalados como P0 y siguen sin nada

### E.1 `build-public-dist.py --check-contents` no está en ningún workflow

```bash
$ grep -rln "check-contents" .github/workflows/*.yml
(sin resultados)
```

El flag existe en el script (`scripts/build-public-dist.py`) pero solo se
ejecuta `--check-assetsignore` en CI. La verificación de que el dist público
no incluye rutas internas (`scripts/`, `tests/`, `data/`, `.env.example`,
`lecturas/`, `publicar-web/`, `editorial-facts.json`,
`cloudflare-worker-subscribe.js`) queda sin automatizar.

### E.2 Sin smoke test HTTP contra el despliegue de staging

Nada en `tests/` hace una petición real a la URL de preview para confirmar
que las rutas internas devuelven 404 y los assets públicos 200 después de un
deploy. Documentado como pendiente en `64_AUDITORIA_COMPLETITUD_REAL_Y_ORDEN_DE_EJECUCION_2026-08-20.md`,
ítem M.

### E.3 Sin regresión visual (Playwright) ni smoke test de producción

Ambos señalados como P0 en su día en `16_IMPLEMENTACION_CODIGO_LISTA.md` /
`27_REPOSITORIOS_Y_MEJORAS_IMPLEMENTABLES_2026-08-16.md` y ninguno de los dos
existe:

- No hay ninguna suite de regresión visual (`qa/` tiene pruebas funcionales de
  contrato, pero cero comparación de capturas antes/después).
- No hay ningún workflow que se dispare tras un deploy real y confirme que la
  web sigue viva (status 200 en rutas clave, sin errores de consola, JSON-LD
  válido en producción).

### Qué hacer

Con el lanzamiento fijado para el 3 de septiembre, prioriza E.2 y E.3 sobre
E.1: E.1 es una fuga de archivos internos si Cloudflare cambia de
comportamiento; E.2/E.3 es lo único que detectaría un despliegue roto el día
del lanzamiento. Un smoke test mínimo (curl a 5-6 rutas clave + comprobación
de status/JSON-LD) es más valioso ahora que una suite completa de Playwright.
Si el tiempo no da para las tres, dilo explícitamente en la PR y prioriza el
smoke test.

---

## F. Herramientas / features con investigación cerrada pero código incompleto

Estas son de menor urgencia — ninguna bloquea el lanzamiento del 3/09 — pero
quedaron confirmadas como código realmente pendiente, no como contenido a la
espera de decisión editorial.

### F.1 `scripts/build-autores-red.py` crashea

```
BuildError: autores/index.html: no se encontró pie para inyectar shell
```

Lanzado desde `scripts/site_shell.py`, que delega en
`scripts/build-site-shell.py:421`. Bloquea `/autores/` incluso el día en que exista contenido real de autores
invitados (hoy solo hay un registro de ejemplo marcado `"status": "draft"` y
`"NO PUBLICAR"`). Corregir el fallo de inyección de shell antes de que haga
falta usarlo.

### F.2 "Revisor de diálogo en español" nunca se construyó

`herramientas/dialogo/` existe pero es una herramienta distinta (mide
porcentaje de texto en diálogo). El comprobador de guion vs. raya, comillas
rectas y acotaciones sospechosas que pedía la investigación original
(`30_INVESTIGACION_RANDOM_CRECIMIENTO_ORGANICO_IA_COMUNIDAD_2026-08-17.md`,
punto 2.B) no tiene ningún código.

### F.3 Atlas literario: scaffolding completo, cero contenido, sin tests

`scripts/build-atlas-literario.py` + `data/atlas-literario.json` +
`assets/atlas-literario.{js,css}` existen y funcionan (validación estricta de
metadatos por imagen, tal como especifica el dossier). Los 12 ítems piloto
están todos en `status:"planned"` — ninguno publicado, no hay
`/atlas-literario/` en el sitio, no hay test para el builder. No hace falta
tocar nada de código aquí salvo, si hay margen, añadir
`tests/test-atlas-literario.py` siguiendo el patrón de los demás builders.

### F.4 `video-source.component.html` nunca se construyó

La plantilla y el validador del pipeline vídeo→artículo existen
(`scripts/templates/video-to-article.template.md`,
`scripts/validate-video-to-article.py`), pero falta el componente reusable de
"vídeo original / plataforma / fecha / aviso de versión editada" descrito en
`54_VIDEO_A_ACTIVO_EDITORIAL_TRANSCRIPCIONES_UTILES_2026-08-19.md` sección 11.
También falta `tests/test-validate-video-to-article.py`, que sí existe para
los pipelines editoriales hermanos (reader-question, decision-escritura).

### Qué hacer

Ninguno de los cuatro es bloqueante. Si hay tiempo tras A–E, arréglalos en
este orden: F.1 (es un bug real, aunque hoy inactivo) → F.4 (test que falta,
rápido) → F.2/F.3 (features nuevas, más esfuerzo).

---

## G. Ya resuelto — verificado en HEAD, no hace falta tocarlo

Para que no se reinvestigue: estos puntos aparecían como dudosos o pendientes
en varios ficheros del dossier y **ya están aplicados** en esta rama,
confirmado por lectura/grep directo, no por el propio dossier:

- `broken-links.yml` ya tiene `fail: true` (C-068 resuelto).
- `404.html` existe en la raíz (C-075 resuelto).
- `lighthouserc.json` + `.github/workflows/lighthouse-ci.yml` existen y están
  wireados como workflow propio (C-070 resuelto).
- `offline.html` ya no menciona Samuel/Noveris y es autocontenido en el
  `APP_SHELL` del service worker (C-081/C-082 resueltos).
- `manifest.json` tiene identidad neutral de autor (no "escritor de fantasía
  juvenil") y no fuerza `orientation: portrait-primary` (C-084/C-085
  resueltos).
- Los 3 assets de prensa (portada 1024×1536, fotos de autor) sí están en
  `assets/` (`assets/manecillas/source/portada-master-1024x1536.png`,
  `assets/david-porto-foto-portada*`, `assets/david-porto-diaz-retrato-editorial-prensa.webp`) —
  el punto que un agente de verificación había dejado como "sin confirmar" en
  C-061 está resuelto.
- `lab/diseno-home-v1/` en el repo real es el mismo paquete que aparece en
  `WEB DAVID PORTO nuevas ideas/DISEÑO Y DEMÁS/.../37 — LAB HOME V1/` — ya se
  integró como área de staging interna (`noindex`), no es un gap sin fusionar.

---

## Resumen para quien solo quiera la lista de tareas

1. Eliminar `.github/workflows/update-dates.yml` — **[A]**
2. Construir `/gracias-suscripcion/index.html` — **[B.1]**
3. Honeypot `website` en el Worker — **[B.2]**
4. Rate limiting/Turnstile en el Worker (código, no necesariamente activado) — **[B.3]**
5. Resolver la discrepancia de spec del popup (60%/30s/sin filtro puntero vs. 70%/sin timer/hover:hover) — **[C]**
6. Fecha "Última actualización" visible en artículos — **[D.1]**
7. Migrar `premios.html` de `prerender` a `prefetch` como el resto del sitio — **[D.4]**
8. Wireear `build-public-dist.py --check-contents` en CI — **[E.1]**
9. Smoke test HTTP mínimo post-deploy (prioridad alta, quedan ~12 días para el 3/09) — **[E.2/E.3]**
10. Arreglar el crash de `build-autores-red.py` — **[F.1]**
11. Test para `validate-video-to-article.py` — **[F.4]**
12. (Opcional, sin urgencia) permalinks de sección, RSS human view, revisor de diálogo, tests de Atlas literario — **[D.2, D.3, F.2, F.3]**

No toques nada de la sección G — ya está hecho.
