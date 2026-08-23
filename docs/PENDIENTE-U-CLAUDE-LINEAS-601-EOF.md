# Pendiente U — Auditoría Claude líneas 601–EOF

Fecha de contraste: 2026-08-23  
Base auditada: `implementacion-web-2026` @ `4694799edc6d9c9e729b896cadda1eef9726d083`  
Fuente: `claude pending.txt`, líneas 601–746. **El fichero termina en la línea 746.**

> Las líneas 598–600 quedaron deliberadamente abiertas en la ronda anterior porque su clasificación dependía de la continuación 601+. Ese cierre de frontera también se registra aquí y se ha comunicado en #76.

## Regla de alcance

Esta PR solo registra deuda que siga siendo real después de contrastar:

- fuente Claude;
- documento 30 original de Drive cuando era necesaria su prioridad/semántica;
- HEAD actual de `implementacion-web-2026`;
- código, builders, datos y tests actuales;
- todas las PR abiertas refrescadas antes de empezar el tramo.

No duplicar owners existentes. No tocar `main`, no desplegar producción y no activar auto-merge.

---

# U.1 — Recursos embebibles: falta una primera implementación real

**Clasificación: DEUDA NUEVA / PRIORIDAD ALTA en la fuente original.**

La línea 600 de `claude pending.txt` detecta que no existe ningún recurso embebible ni una tarjeta «Estoy leyendo». Al leer la continuación y el documento 30 original, se confirma que no era una mención accidental: el apartado **«5. Recursos que otros escritores quieran incrustar — PRIORIDAD ALTA»** propone explícitamente activos reutilizables por terceros:

- tarjeta embebible de libro recomendado;
- mini ficha de autor;
- cita visual con código accesible;
- botón 88×31 de comunidad;
- tarjeta «Estoy leyendo…» generada desde navegador.

La misma fuente establece una regla clave: **el enlace a davidportodiaz.com debe ser opcional**; no puede convertirse en backlink exigido ni en intercambio de enlaces.

## Evidencia actual

No hay en el HEAD base:

- ruta pública dedicada a generar una tarjeta embebible;
- componente/embed generator equivalente;
- archivos cuyo nombre o contenido indiquen `embed`, «Estoy leyendo» o una funcionalidad equivalente;
- PR abierta que posea este producto.

`/lecturas/` no sustituye esta necesidad: hoy es una superficie de lectura personal con datos fixture/no publicables. Tampoco debe usarse como excusa para publicar contenido ficticio.

## Decisión de producto para V1

No construir cinco productos a la vez. El primer cierre debe ser **una sola herramienta pequeña, portable y comprobable**:

### «Tarjeta Estoy leyendo»

Recomendación de ruta canónica para implementación: `/herramientas/tarjeta-estoy-leyendo/`.

La ruta final puede ajustarse al patrón vigente del hub si durante la implementación aparece una autoridad más reciente, pero deben cumplirse estas propiedades:

1. **100 % local en navegador.**
2. El usuario introduce, como mínimo:
   - título del libro;
   - autor/a;
   - texto breve opcional («Estoy leyendo…», «Recomiendo…», etc. dentro de presets controlados o campo limitado).
3. La herramienta genera código portable para copiar/pegar.
4. **No requiere cuenta, email ni servidor.**
5. No sube el contenido introducido.
6. No almacena título/autor/texto en `localStorage`, cookies, IndexedDB ni analytics.
7. El resultado debe seguir siendo legible sin JavaScript en la web donde se incruste.
8. No cargar scripts remotos, iframes ni trackers desde el snippet generado.

## Formatos de salida

V1 debe ofrecer como mínimo:

- **HTML autocontenido y accesible**;
- opcionalmente **Markdown** si se puede mantener la misma semántica sin ampliar mucho el scope.

No exigir un iframe alojado en davidportodiaz.com: un iframe convertiría cada embed en dependencia runtime de la web, complica CSP/privacidad y hace más frágil el recurso.

El HTML generado debe:

- escapar cualquier contenido introducido por el usuario;
- usar elementos semánticos simples (`figure`, `blockquote`, `p`, `cite` o equivalente razonable);
- funcionar sin JS en el destino;
- evitar IDs globales que colisionen con la página receptora;
- usar clases prefijadas si son necesarias;
- no depender de `script.js`, `styles.css` ni assets privados del sitio para ser entendible;
- conservar contraste y legibilidad razonables incluso si el destino no carga CSS adicional.

## Enlace opcional — requisito SEO/ético no negociable

La fuente original prohíbe convertir esto en intercambio de enlaces.

Por tanto:

- la tarjeta debe poder generarse **sin ningún enlace a davidportodiaz.com**;
- si se ofrece una opción «Incluir referencia a la herramienta», debe ser un control explícito y desactivable;
- no se debe ocultar el enlace dentro de imágenes, CSS, tracking ni texto no visible;
- no se puede bloquear la copia/exportación por desactivar el enlace;
- no se puede cambiar el contenido del usuario para insertar anchor text SEO;
- ninguna métrica de producto debe depender de que el backlink permanezca.

## Imágenes y copyright

No convertir V1 en un descargador de cubiertas ni en un proxy de imágenes de terceros.

Para la primera versión:

- preferir una tarjeta **text-first**;
- si se permite imagen, que sea solo una imagen seleccionada localmente por el usuario y procesada localmente, o assets propios cuya reutilización esté autorizada;
- no hacer `fetch` de Amazon, Goodreads, editoriales, Google Books u otras fuentes para obtener portadas;
- no afirmar licencias que no consten en una fuente autorizada.

Así se evita introducir una dependencia legal/técnica ajena al objetivo principal.

## Privacidad y analítica

La herramienta debe seguir el espíritu del contrato local-only de las herramientas de manuscrito, aunque no procese manuscritos:

- los campos introducidos no salen del dispositivo;
- ningún evento analítico puede contener título, autor, comentario, HTML generado ni datos derivados del contenido;
- si se instrumenta con la taxonomía global de #63, limitarse a eventos agregados de producto como `tool_open` / `embed_copy` o los nombres canónicos que #63 establezca;
- si #63 aún no está integrado, es preferible lanzar sin analítica antes que crear nombres nuevos en paralelo.

## UX y accesibilidad

Criterio mínimo:

- formulario con `<label>` reales;
- preview accesible que no sea la única forma de entender el resultado;
- botón «Copiar HTML» con estado de éxito anunciado mediante `aria-live`;
- fallback visible si `navigator.clipboard` no está disponible;
- teclado completo;
- foco visible;
- funcionamiento a 320 px sin overflow horizontal;
- no depender exclusivamente de color para estados;
- si se añade personalización visual, limitar opciones para no generar combinaciones de contraste ilegibles.

## Seguridad

Tests/reglas obligatorios:

- `<script>`, atributos `on*`, URLs `javascript:` y HTML arbitrario introducido como texto deben quedar escapados, no ejecutarse;
- no usar `innerHTML` con contenido de usuario salvo sanitización explícita y testeada; preferir APIs DOM/textContent;
- el snippet exportado no puede contener scripts ejecutables;
- no interpolar parámetros de URL sin escape.

## Integración con el sitio

Cuando el producto exista realmente:

1. registrarlo en `data/tools-hub.json` o la autoridad de herramientas vigente;
2. integrarlo mediante el builder/shell actual, no copiando navegación/pie a mano;
3. `index,follow` solo cuando la herramienta esté funcional y pase QA;
4. sitemap/hub deben derivarse de la autoridad actual, no editarse a mano si el builder ya manda;
5. añadir explicación editorial breve: qué hace, privacidad, limitaciones y cómo usar el código generado;
6. no crear un nuevo «hub de embebibles» hasta que existan al menos dos o más recursos reales que justifiquen esa arquitectura.

## Relación con `/lecturas/`

No acoplar U.1 a `data/reading-list.json` ni activar `/lecturas/` para conseguir datos.

- `/lecturas/` permanece correctamente `noindex`/fixture hasta que existan notas reales;
- la tarjeta U.1 trabaja con datos introducidos localmente por quien la usa;
- en el futuro, cuando `/lecturas/` tenga contenido real, podría ofrecer un atajo «crear tarjeta desde esta lectura», pero eso es una extensión posterior y no debe bloquear V1.

## Test plan mínimo

Crear tests deterministas que cubran al menos:

1. campos obligatorios y límites;
2. escape de HTML/XSS;
3. generación sin backlink;
4. generación con referencia opcional cuando el usuario la activa;
5. ausencia de scripts/trackers en el snippet;
6. copia al portapapeles + fallback;
7. no persistencia/no red del contenido;
8. registro correcto en tools hub y privacidad declarada;
9. QA de navegador a 320 px y desktop;
10. teclado/foco/`aria-live`;
11. salida determinista para la misma entrada.

No se cierra U.1 con una maqueta estática o solo documentación: debe existir una herramienta usable y testeada.

---

# Clasificación del resto del tramo 601–746

## Líneas 601 y 603 — «Dónde empezar» / reading paths

**HECHO / SUPERADO POR EQUIVALENTE.**

`/empieza-aqui/` ya cubre el objetivo de enrutamiento por intención con una solución más completa. No recrear los textos históricos «Si vienes por…» por fidelidad nominal.

## Línea 602 — biblioteca de descargables

**PARCIAL / GATED EDITORIAL.**

Existe al menos el recurso de objeto heredado. Los checklists/fichas adicionales requieren contenido humano útil. No crear PDFs vacíos ni plantillas relleno solo para aumentar inventario.

## Línea 604 — investigación detrás de la novela

**GATED EDITORIAL.**

Memoria, procedencia, objetos heredados e historia oral requieren artículos reales y fuentes. No es un hueco de código.

## Líneas 605, 662–681 — vídeo → activo editorial

**YA DETECTADO — #59 F.4.**

La auditoría confirma:

- falta `video-source` reutilizable + CSS;
- falta test de `scripts/validate-video-to-article.py`;
- el contenido de vídeo real sigue demand/content-gated;
- `VideoObject` no debe aparecer hasta que exista vídeo real.

No duplicar PR.

## Línea 606 — índice público de fuentes

**HECHO.**

`/recursos/herramientas-para-escritores/` cubre el objetivo como directorio verificado y está enlazado desde `/empieza-aqui/`.

## Líneas 607 y 614 — «Qué estoy probando» / laboratorio público

**INFRAESTRUCTURA HECHA / PUBLICACIÓN GATED.**

La afirmación Claude queda desactualizada al contrastar HEAD:

- existe `data/web-lab-entries.json`;
- existen dos candidatos reales con `publish:false`;
- existe `scripts/build-web-lab-index.py`;
- el builder solo considera entradas `publish:true`, exige al menos dos piezas publicables, valida tipo/fecha/URL/resumen y genera `/cuaderno/laboratorio-web/`.

La ausencia de la ruta pública actual es correcta: todavía no hay dos piezas editoriales publicables. No crear una página vacía.

## Líneas 610–612 — autores-red y revisor de diálogo

**YA DETECTADO — #59 F.1/F.2.**

- crash de `build-autores-red.py` → F.1;
- revisor de diálogo español real → F.2;
- publicación de `/autores/` sigue gated hasta disponer de autores reales/autorizados.

## Líneas 613, 617 — Observatorio / Pregunta del mes

**GATED EDITORIAL/OPERATIVO.**

El documento 30 original confirma que no son meros shells:

- Observatorio = encuestas/estudios propios, metodología, resultados, gráficos, CSV anonimizado cuando proceda, limitaciones y licencia;
- Pregunta del mes = 8–12 respuestas reales, firma, perfil, obra, enlace oficial y moderación manual.

No fabricar datos, entrevistas ni páginas vacías.

## Líneas 621–644 — Atlas literario

**YA DETECTADO — #59 F.3.**

La infraestructura existe y los 12 items continúan `planned`.

El tramo añade matices ya comunicados a #59:

- test debe asegurar que `planned` no se publica;
- `published` incompleto debe fallar;
- salida determinista con fixture `published`;
- resolver explícitamente `dist/atlas-literario/` vs ruta servida antes de activar publicación;
- sitemap/nav solo cuando haya contenido real suficiente.

No publicar seeds ni inventar licencias/investigación.

## Líneas 645–660 — privacidad herramientas

**HECHO.**

Shell privado, auditor, manifest, CSP, test público/privado y wiring CI están presentes. No reabrir.

## Líneas 682–702 — `/lecturas/`

**PARCIAL / GATED EDITORIAL.**

Builder, CSS y fixture existen; la página sigue correctamente `noindex` con `publish:false` porque no hay notas reales. Sitemap/enlaces/Sorpréndeme deben activarse solo cuando exista contenido real suficiente.

No convertir el fixture en contenido oficial.

## Líneas 703–730 — auditoría 64

**MAYORITARIAMENTE SUPERADA; GAP TÉCNICO YA DETECTADO — #58.**

- `build-public-dist.py --check-contents` → #58;
- smoke HTTP real de staging → #58;
- CI/evidencia por SHA → práctica operativa recurrente;
- Rich Results + imports Apple/Google/Outlook → gates manuales externos.

No duplicar.

## Líneas 732–746 — resumen histórico / PR #53

**SNAPSHOT HISTÓRICO / SUPERADO COMO ESTADO VIVO.**

La referencia a «PR #53 abierta» y el resumen de blockers pertenece al estado de aquella auditoría. El estado vivo actual se determina consultando HEAD + todas las PR abiertas. Los elementos técnicos citados ya tienen owners actuales:

- `update-dates.yml` → #54;
- Brevo/DOI/honeypot/rate limit → #55;
- popup newsletter → #56;
- fechas/premios → #57;
- smoke/post-deploy → #58;
- autores/diálogo/Atlas/vídeo → #59;
- visual/mobile → #78;
- cross-engine → #66 K.3.

No resucitar #53 ni duplicar su inventario.

---

# Resultado del tramo final

`claude pending.txt` termina en la línea **746**.

Deuda nueva independiente real descubierta/cerrada como owner:

- **U.1 — primera herramienta de recursos embebibles, empezando por «Tarjeta Estoy leyendo», local, accesible, portable y sin backlink forzado.**

Todo lo demás del tramo queda:

- HECHO/SUPERADO;
- GATED por contenido/operativa real;
- o asignado a owners existentes (#54–#59, #66, #78).

No existe un bloque 747–800 que auditar.
