# 12 — Spam policies, mitos y anti-patrones

## Objetivo

Evitar que futuros trabajos de «SEO» degraden una web que ya tiene una base sólida.

Google define spam como técnicas destinadas a engañar usuarios o manipular sus sistemas para destacar contenido, incluyendo intentos de manipular respuestas de IA generativa en Search.

Las infracciones pueden producir:

- demotion algorítmica;
- pérdida de rich-result eligibility;
- acción manual;
- desaparición parcial o total de Search.

---

# 1. Keyword stuffing

## No hacer

- repetir `escritor David Porto Díaz Madrid escritor gallego autor...`;
- listas de ciudades/keywords sin contenido;
- alt stuffed;
- anchors exact-match artificiales;
- footer con cientos de términos.

## Sí

Usar las palabras que los usuarios emplean, de forma natural, en:

- title;
- H1;
- headings;
- body;
- alt;
- links.

---

# 2. Hidden text / hidden links

Prohibido:

- texto blanco sobre blanco;
- `font-size:0`;
- opacity 0;
- off-screen para keywords;
- links en caracteres invisibles.

Permitido por UX:

- acordeones;
- tabs;
- sliders;
- contenido mostrado tras interacción.

No confundir componentes accesibles con hidden-text spam.

---

# 3. Cloaking

No servir:

- una página SEO a Googlebot;
- otra a humanos.

No detectar user-agent para inyectar más keywords/schema.

Excepciones legítimas de progressive enhancement no deben alterar la esencia del contenido.

---

# 4. Doorway abuse

No crear:

- `escritor-fantasia-madrid`;
- `escritor-fantasia-pontevedra`;
- `escritor-fantasia-galicia`;
- cientos de ciudades que conducen a la misma bio.

No crear variaciones:

- `editoriales-fantasia-madrid`;
- `editoriales-fantasia-barcelona`;

si el contenido es prácticamente idéntico.

La localización solo merece página cuando existe una necesidad/entidad/evento local real.

---

# 5. Scaled content abuse

Google deja claro que el problema no es si el contenido lo creó IA o una persona. Es crear muchas páginas principalmente para manipular rankings y con poco valor.

## Riesgo real del proyecto

- editoriales;
- convocatorias;
- herramientas;
- perfiles;
- recomendaciones;
- long-tail articles.

## Defensa

Quality gate + registry + noindex hasta cumplirlo.

No publicar 500 fichas por tener datos scrapeados.

---

# 6. Scraping

No:

- copiar fichas de editoriales;
- importar feeds de concursos y republicarlos sin valor;
- reescribir artículos de competidores;
- combinar sinónimos de varias fuentes.

Sí:

- usar fuente primaria para verificar un hecho;
- sintetizar con valor añadido;
- añadir estado/fecha/metodología/comparación;
- enlazar fuente.

---

# 7. Site reputation abuse

No abrir davidportodiaz.com a contenido de terceros creado principalmente para aprovechar la autoridad futura del dominio.

Ejemplo peligroso:

- casino/préstamos/cupones/temas ajenos publicados por terceros bajo una subcarpeta porque «el dominio tiene autoridad».

Guest/editorial content relevante no es automáticamente abuso; la intención y relación importan.

---

# 8. Link spam

No:

- comprar dofollow;
- vender links para ranking;
- exchanges masivos;
- guest posts a escala con anchors exactos;
- automated link building;
- directorios basura;
- footer/sitewide links pagados no cualificados.

Sí:

- cobertura editorial;
- referencias naturales;
- `sponsored` para paid/affiliate;
- `ugc` cuando corresponda.

---

# 9. Fake reviews

No:

- comprar opiniones;
- pedir solo 5 estrellas;
- crear usuarios falsos;
- schema de Amazon como propio;
- aggregateRating manual de plataformas externas.

P0 de esta auditoría: retirar reviews Amazon del Book JSON-LD de Samuel.

---

# 10. Misleading functionality

Especialmente relevante para herramientas.

No crear una página que dice:

- «analiza tu manuscrito»

pero después no funciona o solo muestra anuncios/CTA.

Las herramientas actuales tienen funcionalidad real. Preservar.

---

# 11. Fake freshness

No:

- cambiar `dateModified` cada día;
- título `2026` automático sin revisión;
- re-publicar idéntico con fecha nueva;
- lastmod de build.

Sí:

- actualizar hechos;
- documentar verificación;
- cambiar fecha cuando hay modificación material.

---

# 12. Expired domain abuse

No comprar un dominio antiguo de libros/medios con enlaces solo para volcar contenido y redirigir autoridad.

Si se adquiere un dominio por razones de marca legítimas, evaluar migración normalmente.

---

# 13. Hacked content

No es «SEO negativo» que se resuelve con noindex.

Si ocurre:

- seguridad;
- limpiar;
- credenciales;
- Search Console Security Issues;
- review.

---

# 14. Meta keywords

Google Web Search no usa `meta keywords`.

No añadir:

```html
<meta name="keywords" content="...">
```

como tarea SEO.

Schema `keywords` puede describir entidades/contenido, pero no es un sustituto ni un factor mágico de ranking.

---

# 15. Keyword density

No existe una densidad objetivo oficial del 1%, 2% o 3%.

No editar buena prosa para llegar a una cifra.

Usar vocabulario natural y suficiente contexto.

---

# 16. Word count

Google dice que no tiene un word count preferido.

Mito:

> todo artículo debe tener >2.000 palabras.

Falso.

Resolver la tarea.

---

# 17. Domain Authority / DR

DA, DR, TF y similares son métricas de terceros.

No son métricas internas de Google.

Pueden ayudar a comparar perfiles de links, pero no decir:

> necesitamos DA 40 para rankear.

---

# 18. SEO score

Lighthouse SEO, plugins y crawlers pueden detectar problemas técnicos.

Un `SEO score 100/100` no equivale a ranking.

No convertir un score agregado third-party en KPI ejecutivo.

---

# 19. Exact title length

No existe una penalización automática a 61 caracteres.

Google puede truncar/reformular según dispositivo/query.

Optimizar claridad, no semáforo de plugin.

---

# 20. Meta description como ranking factor

No documentar como factor directo.

Es un candidato de snippet y puede mejorar CTR/contexto.

---

# 21. CTR como factor directo universal

No afirmar:

> si conseguimos más clics, Google nos subirá.

CTR se usa aquí como métrica de rendimiento de la representación, no como palanca manipulable confirmada.

No hacer click farms.

---

# 22. Bounce rate / dwell time

No afirmar que Google Analytics bounce rate sea un factor directo de ranking.

Sí usar engagement propio para mejorar UX/contenido.

---

# 23. Core Web Vitals

Son parte de sistemas de ranking/page experience, pero Google dice que buenas métricas no garantizan top positions.

No sacrificar valor para pasar 100/100.

---

# 24. HTTPS

Necesario y positivo, pero no una ventaja competitiva suficiente por sí misma en 2026.

No dedicar roadmap a «hacer HTTPS SEO» cuando ya lo está.

---

# 25. Sitemap guarantee

Mito:

> si está en sitemap, Google lo indexará.

Falso.

Sitemap es señal de descubrimiento/canonical secundaria, no obligación.

---

# 26. Indexing request = ranking

Solicitar indexación no mejora ranking.

Úsalo para URLs importantes nuevas/corregidas, no repetidamente.

---

# 27. Indexing API para artículos/libros

No usar.

La Indexing API de Google se limita a JobPosting y BroadcastEvent en VideoObject.

No crear scripts para enviar todos los artículos.

---

# 28. `robots.txt` = noindex

Falso.

Bloquear rastreo puede impedir que Google vea noindex.

Usar robots meta/header para noindex y permitir crawl cuando corresponda.

---

# 29. `noindex,follow` = penalización

No.

Es una decisión editorial válida para contenido que no debe salir en Search.

No intentar indexar todo.

---

# 30. Duplicate content penalty

No existe una penalización general automática por tener algo de contenido duplicado normal.

Google consolida duplicados/canónicas.

El problema del proyecto es intención/valor/arquitectura, no perseguir un porcentaje de similitud.

---

# 31. Canonical como redirect

Canonical es hint/señal, no navegación para humanos.

Si una URL se mueve permanentemente, usar redirect.

No dejar dos páginas iguales y esperar que canonical arregle toda arquitectura.

---

# 32. 404 dañan el sitio

404 normales son parte de la web.

No redirigir todos los 404 a home.

---

# 33. Disavow routine

No subir cada mes un archivo con «spam domains».

Google dice que la mayoría de sitios no necesita esta herramienta.

Solo casos serios documentados.

---

# 34. Links nofollow inútiles

Un enlace puede aportar:

- tráfico;
- descubrimiento;
- reputación;
- relación editorial,

aunque esté nofollow/sponsored.

No rechazar cobertura porque no sea dofollow.

---

# 35. Press release links

No distribuir comunicados a cientos de sites automáticos con anchor exacto.

Una nota de prensa puede servir para información/PR; no como fábrica de PageRank.

---

# 36. Guest post farms

No comprar paquetes:

- 20 guest posts;
- DA 50+;
- anchor exact.

Esto es incompatible con estrategia.

---

# 37. PBN

No usar private blog networks.

---

# 38. Google Business Profile falso

Google exige que el negocio tenga un lugar físico que los clientes puedan visitar o viaje hasta sus clientes.

La condición de escritor residente en Madrid no basta para crear un perfil local ficticio en una vivienda privada.

Solo evaluar GBP si en el futuro existe una actividad empresarial/local que cumpla las reglas.

---

# 39. Preferred Sources = ranking boost general

No.

La selección es del usuario y hace más probable/highlighted la fuente para ese usuario en superficies compatibles.

Implementar solo si elegible y útil.

---

# 40. Knowledge Panel se crea con schema

No.

Google los genera automáticamente a partir de información de la web.

Schema ayuda a claridad de entidad, no garantiza panel.

---

# 41. Wikipedia page = SEO task

No.

Notabilidad/fuentes/políticas mandan.

No autopublicar promoción.

---

# 42. Wikidata stuffing

No llenar item con keywords/claims promocionales.

Datos neutrales y referenciados.

---

# 43. FAQ schema = más espacio

Ya no en Google Search desde mayo 2026.

No invertir por esa razón.

---

# 44. Schema = ranking

No.

Ayuda a comprensión/elegibilidad para features.

Puede perjudicar si es engañoso.

---

# 45. Product/Offer ficticio

No usar precio del retailer como Offer propia.

Manecillas PVP no implica stock/merchant.

---

# 46. Review markup externo

P0 prohibido según Google.

---

# 47. News Publisher Center submission

Tutorial obsoleto.

Desde marzo 2025 Google News genera publication pages automáticamente; el contenido elegible se considera sin submission manual tradicional.

---

# 48. Discover submission

No existe submission especial.

Elegibilidad automática.

---

# 49. Image sitemap obligatorio

No.

Puede ayudar en situaciones concretas; las imágenes accesibles en HTML ya pueden descubrirse.

---

# 50. Video por SEO

No crear vídeo vacío solo porque Google tiene video results.

Necesita valor editorial y estrategia real.

---

# 51. AMP obligatorio

No.

No implementar AMP solo por ranking/Top Stories.

---

# 52. Mobile separate site

No necesitamos `m.`.

Responsive/mobile-first parity.

---

# 53. Publicar todos los días

Google no exige frecuencia diaria.

Publicar cuando exista valor.

---

# 54. Actualizar cada artículo al año actual

No cambiar 2025→2026 si contenido no fue revisado.

---

# 55. Una página por People Also Ask

No.

Agrupar preguntas relacionadas en una página útil si comparten intent.

---

# 56. Exact match domains/pages

No crear dominios/subdominios/URLs absurdas para cada keyword.

URL descriptiva, estable, arquitectura lógica.

---

# 57. AI content automáticamente penalizado

No es lo que dice Google.

El problema es contenido escalado de poco valor destinado a manipular rankings, independientemente del método de creación.

IA puede ayudar en proceso; control humano/factual es obligatorio.

---

# 58. Human-written automáticamente bueno

Tampoco.

Contenido humano genérico/masivo puede ser igualmente pobre.

---

# 59. Competitor copying

No reescribir la página top y añadir 10% más palabras.

Encontrar contribución propia.

---

# 60. Keyword insertion después de escribir

No pasar una lista y forzar cada palabra 3 veces.

La cobertura semántica debe surgir de responder bien.

---

# 61. Internal link automation exact-match

No enlazar automáticamente todas las apariciones de una palabra.

Contextual + natural + útil.

---

# 62. Footer link cloud

No añadir 100 URLs SEO al footer.

Footer para navegación global real.

---

# 63. Local pages de ferias

No crear `escritor-en-madrid`, `escritor-en-aranjuez`, etc. por cada evento.

Crear event page del evento real.

---

# 64. Review list donde siempre gana nuestro libro

No.

La utilidad debe sobrevivir sin Samuel/Manecillas.

---

# 65. Google Ads mejora orgánico

No presentar publicidad pagada como mecanismo de aumentar ranking orgánico.

Ads puede generar exposición/demanda; es un canal separado.

---

# 66. Search Console score

Search Console no da un «SEO score» universal.

Usar reports concretos.

---

# 67. Core update panic

No hacer cambios masivos durante rollout por reacción diaria.

Esperar, segmentar, evaluar.

---

# 68. Spam update = penalización individual

No necesariamente.

Es un cambio de sistemas antispam. Revisar evidencias y policies.

---

# 69. Exact ranking guarantees

Ningún proveedor externo puede garantizar posición 1.

Google advierte que herramientas SEO de terceros no tienen acceso a sus datos internos de ranking.

---

# 70. «Secret ranking factors»

No construir roadmap alrededor de leaks, correlaciones o listas de 200 factores sin contexto.

Usar documentación oficial + datos propios + experiencia de usuario.

---

# 71. Acceptance criteria

- ninguna tarea SEO viola Search Essentials/spam policies;
- no scaled low-value pages;
- no fake reviews/links/freshness;
- no hidden/cloaked content;
- no doorway/local spam;
- no third-party SEO metrics como verdad de Google;
- no APIs/features obsoletas;
- no fake schema;
- todo contenido automatizado pasa value gate;
- todo paid/affiliate link se cualifica;
- cambios importantes se revisan contra políticas vigentes.
