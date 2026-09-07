# Google Preferred Sources — Search / AI Mode / AI Overviews

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · GOOGLE_DOCS_UPDATED_2026-09-03 · DOMAIN_ELIGIBILITY_CHECK_PENDING · READY_FOR_EXECUTION`

## Objetivo

Comprobar si `davidportodiaz.com` aparece en la herramienta oficial de **Fuentes preferidas** de Google y, si es elegible, facilitar de forma discreta que lectores reales lo marquen como fuente preferida.

Esta función puede ayudar a que el contenido del sitio se destaque para esos usuarios en:

- Noticias destacadas;
- Modo IA;
- Vistas creadas con IA / AI Overviews.

No es un hack de ranking general. El beneficio es personalizado para usuarios que eligen el sitio como fuente preferida.

## Estado oficial actual

Google actualizó la documentación de Search Central el **2026-09-03**.

Puntos confirmados:

- la función está disponible globalmente para Noticias destacadas;
- puede aparecer también en Modo IA y Vistas creadas con IA donde esas experiencias estén disponibles;
- solo dominios y subdominios son elegibles, no subdirectorios;
- el sitio debe aparecer en la herramienta oficial de preferencias de fuentes antes de implementar la invitación;
- Google recomienda un botón JavaScript oficial, pero también permite un enlace profundo sin JS.

Fuentes:

- https://developers.google.com/search/docs/appearance/preferred-sources?hl=es
- https://support.google.com/websearch/answer/16379181?hl=es

## Condición de elegibilidad importante

La ayuda de Google indica que fuentes que **no se actualizan periódicamente** pueden no aparecer en la herramienta.

Para `davidportodiaz.com`, la superficie que debe demostrar actividad editorial es principalmente el `Cuaderno`, no páginas estáticas de autor/libros.

Claude debe comprobar la elegibilidad del dominio completo:

`davidportodiaz.com`

No intentar registrar solo `/cuaderno/`, porque Google no admite subdirectorios como fuente independiente.

## Cómo comprobar elegibilidad

Abrir la herramienta de preferencias de fuentes con sesión Google y buscar:

`davidportodiaz.com`

Estados:

- `DOMAIN_FOUND_AND_SELECTABLE`
- `DOMAIN_NOT_FOUND`
- `FEATURE_NOT_AVAILABLE_IN_ACCOUNT/UI`

Si no aparece, no implementar ningún botón todavía. Documentar fecha y volver a comprobar tras más publicaciones/recrawl.

## Implementación oficial disponible

### Opción A — JavaScript estándar de Google

Google recomienda cargar:

`https://news.google.com/swg/js/v1/publisher.js`

y renderizar:

`<div google-add-preferred-source-btn></div>`

Permite tema `light`/`dark` e idioma localizado automáticamente.

### Opción B — enlace profundo, sin JS

Google documenta este formato:

`https://www.google.com/preferences/source?q=davidportodiaz.com`

Para este proyecto, **preferir primero el enlace profundo** salvo que el botón oficial aporte una mejora UX clara, porque:

- evita otro script de terceros;
- evita ampliar CSP innecesariamente;
- reduce coste de rendimiento;
- funciona también en newsletter/redes;
- es fácil de retirar si cambia la función.

Si se usa JavaScript, Claude debe revisar CSP, rendimiento, privacidad y fallos de carga antes de mergear.

## Dónde podría aparecer

No sitewide por defecto.

Prioridad:

1. `/cuaderno/`;
2. footer o bloque final de artículos del Cuaderno;
3. `/empieza-aqui/` si encaja naturalmente;
4. newsletter como enlace de texto;
5. eventualmente página de suscripción/recursos si el usuario ya mostró interés editorial.

No poner:

- popup;
- modal;
- banner fijo;
- Home hero;
- ficha de compra de Manecillas;
- todas las páginas por obligación.

Texto humano posible:

`¿Lees el Cuaderno desde Google? Puedes marcar davidportodiaz.com como fuente preferida.`

No prometer “saldré más en Google” ni pedir que manipulen resultados.

## QA

Si es elegible e implementamos:

- desktop 320/390/768/1024/1440;
- dark/light mode;
- usuario con sesión Google;
- usuario sin sesión;
- enlace vuelve/fluye correctamente;
- no rompe navegación;
- no bloquea render;
- CSP sin errores;
- teclado/focus;
- lector de pantalla;
- no duplicar control en cada artículo si el diseño ya lo incluye globalmente.

## Medición

Google no garantiza un informe específico de conversiones a `Preferred Source` en Search Console.

Por tanto medir indirectamente:

- clics en nuestro enlace/botón mediante analytics local;
- tráfico Search/Discover;
- impresiones y clics del Cuaderno;
- datos de IA generativa si Google los expone;
- evolución a 30/60/90 días.

No atribuir causalidad automáticamente.

## Relación con nuestra estrategia

Esta PR tiene especial interés porque Bing AI Performance ya mostró que artículos del Cuaderno son citados por sistemas de IA. Facilitar una señal voluntaria de preferencia dentro del propio ecosistema Google es coherente con esa estrategia y no requiere crear contenido artificial.

## Secuencia para Claude

1. comprobar dominio en herramienta oficial;
2. guardar captura/estado;
3. si no es elegible → cerrar `NOT_ELIGIBLE_YET` con fecha de revisión;
4. si es elegible → probar primero deeplink oficial;
5. elegir 1–2 ubicaciones editoriales, no sitewide;
6. implementar con tracking local mínimo;
7. QA accesibilidad/móvil;
8. CI + PR;
9. producción;
10. verificar flujo real;
11. registrar baseline Search Console para seguimiento.

## Criterio de cierre

Si elegible:

`DOMAIN_FOUND · DEEPLINK_OR_OFFICIAL_BUTTON_IMPLEMENTED · PLACEMENT_NON_INTRUSIVE · ANALYTICS_EVENT_VERIFIED · MOBILE_DESKTOP_A11Y_QA · PRODUCTION_VERIFIED`

Si no:

`NOT_ELIGIBLE_YET · CURRENT_CONTENT_FREQUENCY_REVIEWED · RECHECK_DATE_RECORDED · NO_FAKE_WORKAROUND`
