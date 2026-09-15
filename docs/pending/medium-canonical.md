# Medium — sindicación selectiva con canonical hacia davidportodiaz.com

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · CANONICAL_IMPORT_CONFIRMED · SELECTIVE_SYNDICATION_ONLY · READY_FOR_PILOT`

## Objetivo

Usar Medium únicamente como canal adicional de descubrimiento para algunos artículos propios que ya funcionan bien, sin ceder la URL canónica ni duplicar indiscriminadamente todo el Cuaderno.

## Por qué puede aportar valor

Medium mantiene distribución interna mediante:

- seguidores del autor;
- feeds y recomendaciones;
- publicaciones temáticas;
- Digest/email;
- sistema de distribución general y Boost.

Esto puede generar lectores nuevos fuera de Google/Bing y referrals hacia davidportodiaz.com.

No se plantea como sustituto del blog propio ni como autoridad SEO primaria.

## Canonical confirmado oficialmente

La ayuda oficial de Medium confirma dos vías:

### Import tool

`Import a story`:

1. pegar la URL original;
2. Medium importa el contenido;
3. retrofecha el post a la fecha original;
4. añade automáticamente un canonical hacia la fuente original.

Fuente:
- https://help.medium.com/hc/en-us/articles/214550207-Importing-a-post-to-Medium

### Canonical manual

Si la importación automática falla, se puede copiar el contenido manualmente y definir:

`More settings → Advanced Settings → This story was originally published elsewhere`

Fuente:
- https://help.medium.com/hc/en-us/articles/360033930293-Set-a-canonical-link

Después de publicar, hay que comprobar el HTML y verificar que el primer `rel="canonical"` apunta exactamente a la URL original de davidportodiaz.com.

## API

Medium ya no entrega nuevos integration tokens para su API. No diseñar automatización nueva basada en API antigua.

Fuente:
- https://help.medium.com/hc/en-us/articles/213480228-API-Importing

Por tanto el proceso será manual/import tool y de bajo volumen.

## Qué artículos probar primero

No republicar todo el Cuaderno.

Piloto con 2–3 piezas que ya tengan evidencia de interés en buscadores/IA, por ejemplo:

- artículo de fantasía juvenil española 2025–2026;
- qué es el portal fantasy;
- magia con coste / sistemas de magia;
- otro artículo que Bing AI/Search Console demuestre que funciona.

Evitar de inicio:

- páginas de producto de libros;
- contenido muy corto;
- noticias efímeras;
- artículos que necesiten navegación/UX específica de nuestra web;
- contenido cuyo valor dependa de herramientas interactivas.

## Perfil

Configurar perfil gratuito con:

- David Porto Díaz;
- foto coherente con identidad pública;
- bio corta factual;
- enlace a https://davidportodiaz.com/;
- sin exceso de CTA/promoción.

No importar suscriptores de Brevo a Medium ni mezclar listas.

## Publicaciones de Medium

Medium permite enviar historias a Publications que aceptan contributors/followers. Esto puede ampliar distribución más que publicar solo en el perfil.

Fuente:
- https://help.medium.com/hc/en-us/articles/213904978-How-to-submit-a-story-to-a-publication

Procedimiento:

1. buscar publicaciones activas relacionadas con escritura/fantasía/libros en español;
2. revisar sus Submission Guidelines;
3. enviar solo piezas que encajen;
4. no pagar por aceptación;
5. mantener canonical hacia la web original.

## Distribución / Boost

La guía actual de Medium (actualizada en 2026) indica que sus historias pueden entrar en:

- Network Distribution;
- General Distribution;
- Boost;
- distribución mediante Publications.

No optimizar artificialmente para Boost ni cambiar el tono del artículo solo por el algoritmo.

Fuente:
- https://help.medium.com/hc/en-us/articles/360006362473-Medium-s-Distribution-Guidelines-How-curators-review-stories-for-Boost-General-and-Network-Distribution

## Procedimiento Claude

1. comprobar si David ya tiene cuenta/perfil;
2. completar perfil y web oficial;
3. elegir 2–3 artículos piloto basándose en Search Console/Bing/AI Performance;
4. usar `Import a story` desde la URL original;
5. revisar formato, imágenes, enlaces y headings;
6. no alterar hechos/copy para hacerlo “Medium-like” si empeora la pieza;
7. publicar;
8. abrir source y verificar canonical exacto;
9. comprobar que los enlaces internos relevantes vuelven a davidportodiaz.com;
10. valorar envío a 1–2 Publications gratuitas y relevantes;
11. medir referrals/clics mediante Clarity/GoatCounter/analytics;
12. a 30–60 días decidir si merece continuar.

## Métricas de éxito

No basta con “tener Medium”. Registrar:

- views/reads internos;
- clicks hacia davidportodiaz.com;
- páginas destino;
- newsletter/book CTA posteriores cuando sean medibles;
- indexación/canonical correcto;
- tiempo invertido.

Si 2–3 pilotos no generan tráfico/descubrimiento útil, no escalar.

## Guardrails

- cero gasto;
- no Partner Program como objetivo;
- no duplicar todo el Cuaderno;
- no importar lista Brevo;
- no publicar antes en Medium que en nuestra web;
- no perder canonical;
- no crear versiones ligeramente reescritas solo para esquivar duplicación;
- no convertir Medium en fuente primaria de nuestros artículos.

## Criterio de cierre

`PROFILE_READY · PILOT_ARTICLES_SELECTED_FROM_REAL_DATA · IMPORTED_WITH_CANONICAL · CANONICAL_SOURCE_VERIFIED · PUBLICATION_OPPORTUNITY_REVIEWED · REFERRALS_MEASURED · SCALE_OR_STOP_DECISION_RECORDED`
