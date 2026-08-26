# Asistente editorial V2 — UX, conversación y navegación

Fecha de inicio: 2026-08-24  
Base auditada: `implementacion-web-2026@3232283155fc93369e6501488fba4476cd26d873`.

## Objetivo

Esta PR corrige tres problemas observables del asistente existente sin reescribir su motor seguro ni duplicar los owners ya abiertos:

1. **Lenguaje visual genérico de chatbot**: burbujas redondeadas, chips/pills, panel flotante con pulso y sombra pronunciada. Funciona, pero no pertenece al lenguaje editorial que está adoptando el resto de la web.
2. **Conversación demasiado literal**: consultas sociales normales como `Hola`, `Buenas tardes`, `Gracias` o `¿Qué puedes hacer?` no tienen intención local propia. Caen en búsqueda Pagefind/registry y pueden responder con páginas «relacionadas» que no tienen sentido conversacional.
3. **Navegación rota dentro del widget**: los enlaces de fuentes se crean como `<a href="…">` sin `target`. Como el chat vive en un iframe same-origin, el destino se abre dentro de ese rectángulo y el usuario pierde el asistente y la navegación principal.

La solución mantiene intactos los contratos de seguridad, privacidad, fuentes canónicas, kill switches, Turnstile, cuotas y fallback local/remoto ya auditados.

## Qué NO hace esta PR

- No sustituye Pagefind ni duplica la PR #91.
- No cambia el Worker, los modelos remotos, Turnstile, rate limiting ni cuotas.
- No modifica la taxonomía de contenido ni inventa nuevas fuentes.
- No convierte el asistente en un bot generalista: sigue limitado a orientar dentro de `davidportodiaz.com`.
- No toca `main`, no despliega y no activa IA remota.
- No invalida #88: esta PR materializa el caso concreto del Asistente; #88 sigue siendo owner del lenguaje final de la familia Herramientas.

## Investigación y referencias

### Navegación desde iframe

MDN documenta que `_top` carga el destino en el contexto de navegación superior. Es exactamente el comportamiento esperado aquí: el usuario pulsa una fuente dentro del iframe y navega por la web completa, no dentro del chat.

- https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/base
- https://developer.mozilla.org/en-US/docs/Web/API/HTMLBaseElement/target
- https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/a

La implementación usa `<base target="_top">` únicamente en `asistente/embed.html`. La página completa `/asistente/` no cambia de contexto. No se fuerza `_blank`: abrir pestañas nuevas de forma inesperada tampoco es una mejora de UX.

### Fuentes separadas de la respuesta

ChatGPT Search expone respuestas y una superficie clara de fuentes/citas; la fuente es algo que el usuario puede abrir para comprobar el contenido. Esa separación guía aquí el tratamiento visual: respuesta primero, fuentes después como filas editoriales visibles, no pills incrustadas que parecen tags.

- https://help.openai.com/es-es/articles/9237897-b%C3%BAsqueda-de-chatgpt

### Referencias de dirección visual

No se copia código de estas webs. Se toman como referencias públicas de jerarquía, tipografía, aire, líneas editoriales y contención visual:

- https://mubi.com/es/notebook
- https://www.lrb.co.uk/
- https://www.theparisreview.org/
- https://yalereview.org/

El objetivo es que el asistente parezca una pieza de la publicación digital de David Porto Díaz, no una miniapp SaaS incrustada.

## Contrato visual V2

### Panel

- Fondo blanco, tinta y hairlines.
- Exterior casi plano: sin tarjeta redondeada pesada.
- Sombra solo en el widget flotante y con intensidad baja, porque necesita separarse físicamente de la página que cubre.
- Cabecera del widget como cabecera editorial, no barra de app.
- Se elimina el pulso perpetuo del launcher.

### Conversación

- Se conservan las clases y semántica actuales para no romper QA ni accesibilidad, pero se cambia su gramática visual.
- Respuestas del asistente: bloque editorial de ancho completo, sin burbuja.
- Mensajes del usuario: bloque secundario contenido, identificado como `Tú`, sin globo oscuro redondeado.
- Separadores horizontales y etiquetas tipográficas sustituyen a las colas de bocadillo.
- El transcript mantiene `role="log"` y `aria-live="polite"`.

### Fuentes

- Lista vertical de filas con título y flecha.
- La fuente se reconoce como navegación, no como badge.
- En el iframe, cualquier fuente navega a la página superior gracias a `<base target="_top">`.
- El código sigue aceptando solo rutas internas validadas por `isSafeInternalPath()`.

### Preguntas sugeridas

- Tres acciones editoriales, no pills.
- En móvil pasan a una columna.
- Siguen siendo botones reales, con touch target >=44 px y foco visible.

### Composer

- Caja limpia con línea inferior y acción de envío cuadrada.
- Sin cápsula redondeada.
- `Enter` envía y `Shift+Enter` mantiene salto de línea.
- El textarea conserva `font-size >=16px` para evitar zoom involuntario en móvil.

## Contrato conversacional V2

Antes de buscar por Pagefind o intentar IA remota, el motor local reconoce interacciones básicas que no requieren ninguna fuente documental:

- saludos: `Hola`, `Buenas`, `Buenos días`, `Buenas tardes`, `Buenas noches`, `Hey`, etc.;
- capacidad/identidad: `¿Quién eres?`, `¿Qué puedes hacer?`, `¿Para qué sirves?`, `¿Cómo puedes ayudarme?`;
- agradecimientos: `Gracias`, `Muchas gracias`, etc.;
- despedidas: `Adiós`, `Hasta luego`, `Nos vemos`.

Estas respuestas **no inventan citas** ni intentan buscar una página absurda. Cuando aporta utilidad, ofrecen hasta tres siguientes acciones reales: libros, fragmentos y herramientas.

El asistente sigue sin pretender conversar sobre cualquier tema externo. Si una consulta no pertenece al corpus, conserva el fallback de búsqueda local y explica que no ha encontrado una respuesta exacta.

## QA / anti-regresión

Esta PR añade un gate pequeño y dirigido para comprobar:

- `Hola` ya responde como saludo local y no devuelve fuentes falsas;
- `¿Qué puedes hacer?` explica su función;
- `Gracias` y despedidas reciben respuesta conversacional;
- un saludo seguido de una consulta real (`Hola, ¿de qué trata Las manecillas...?`) no secuestra la intención editorial;
- las intenciones editoriales existentes siguen resolviendo normalmente;
- `asistente/embed.html` contiene `<base target="_top">`;
- el workflow del asistente ejecuta este test en cada cambio relevante.

El Browser QA existente sigue siendo la autoridad para responsive, XSS, CSP, privacidad, teclado, no-JS, fuentes canónicas y remote mock.

## Coordinación con PR abiertas

- **#88 — Herramientas**: owner del lenguaje visual global de Herramientas. Esta PR es una implementación concreta y compatible del Asistente.
- **#91 — Pagefind**: owner de la materialización del índice local; no se duplica ni modifica su arquitectura.
- **#67 — microcopy**: mantiene autoridad de las cadenas compartidas. Aquí se añaden respuestas locales de conversación, no una segunda autoridad para hero/placeholder.
- **#92 — Cloudflare**: mantiene la infraestructura de zona/Worker/Turnstile.

## Definition of Done

- `Hola` ya no produce un fallback absurdo.
- una fuente pulsada desde el widget abre la página real de la web, no dentro del rectángulo del chat.
- el asistente deja de parecer un clon genérico de chat y adopta una composición editorial coherente con la web.
- no se pierden fuentes, validaciones, privacidad, accesibilidad ni fallback local.
- QA del asistente y checks relevantes en verde sobre el HEAD final de la rama.
