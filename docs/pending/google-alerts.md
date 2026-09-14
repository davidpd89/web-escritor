# Google Alerts — monitorización gratuita

Fecha de revisión: 2026-09-07 (ejecutado: 2026-09-14)

Estado: `EXECUTED · 9_ALERTS_ACTIVE · CLOSED`

## Ejecución (2026-09-14)

Creadas las 9 alertas recomendadas, todas con frecuencia "una vez al
día", fuentes "Automático", idioma español, región "Todas las
regiones" y cantidad "Todos los resultados", entregadas a
`davidportodiaz@gmail.com`:

**P0:**
- `"David Porto Díaz"`
- `"Las manecillas del recuerdo"`
- `"Samuel entre mundos"`
- `davidportodiaz.com`

**P1 — identificadores:**
- `"9798905149351"`
- `"9798906781925"`
- `"B0HHY9MYLM"`
- `"B0HHM71F46"`
- `"9791387659776"`

Nota técnica: la alerta de Manecillas quedó guardada con una comilla de
cierre duplicada al final de la consulta (`"...recuerdo""`) por un
artefacto de la UI de edición de Google Alerts que reintroduce la
comilla cada vez que se reabre para editar — no afecta a los resultados
en la práctica (la vista previa mostró coincidencias correctas), pero
queda anotado por si conviene revisarlo manualmente más adelante desde
un navegador normal.

Revisar en 30 días si las alertas P1 (identificadores) generan señal
útil; si no, según el propio criterio del documento, eliminarlas o
pasarlas a frecuencia semanal.

Cierre: `EXECUTED · 9_ALERTS_ACTIVE · REVIEW_IN_30_DAYS_FOR_P1_SIGNAL`

## Objetivo

Configurar Google Alerts como segunda capa gratuita para detectar nuevas menciones indexadas del autor, libros, ISBN y dominio, y convertir resultados útiles en:

- backlinks;
- prensa/entrevistas;
- fichas de libros;
- errores de metadata;
- nuevas superficies de autoridad;
- detección de copias o referencias inesperadas.

Complementa Talkwalker Alerts (#459); no necesitamos una tercera herramienta equivalente salvo que exista una carencia demostrada.

## Configuración disponible actualmente

Google Alerts permite ajustar:

- frecuencia: cuando se produzca / una vez al día / una vez a la semana;
- fuentes: automático, noticias, blogs, web, vídeo, libros, foros, finanzas;
- idioma;
- región;
- cantidad: mejores resultados o todos;
- cuenta/email receptor.

Fuentes oficiales:

- https://www.google.com/alerts?hl=es
- https://support.google.com/websearch/answer/4815696?hl=es

## Alertas recomendadas

### P0 — autor

`"David Porto Díaz"`

Configuración inicial:

- frecuencia: una vez al día;
- fuentes: automático;
- idioma: español;
- región: cualquier región;
- resultados: todos, al menos durante la primera fase.

Añadir `"David Porto Diaz"` sin tilde solo si se comprueba que genera menciones reales que la consulta canónica no recoge.

No crear `David Porto` sin comillas: demasiado ruido.

### P0 — Manecillas

`"Las manecillas del recuerdo"`

- una vez al día;
- fuentes automático;
- español;
- cualquier región;
- todos los resultados durante lanzamiento.

Esta alerta merece mantener frecuencia diaria mientras el libro está recién publicado.

### P0 — Samuel

`"Samuel entre mundos"`

### P0 — dominio

`"davidportodiaz.com"`

Especialmente útil para detectar backlinks o citas del dominio.

### P1 — identificadores

Crear inicialmente y revisar señal:

- `"9798905149351"`
- `"9798906781925"`
- `"B0HHY9MYLM"`
- `"B0HHM71F46"`
- `"9791387659776"`

Estas consultas pueden descubrir nuevas fichas en retailers, bibliotecas y catálogos antes de que las encontremos manualmente.

Si tras 30 días no generan nada útil, eliminar o pasar a semanal.

## Fuentes específicas que pueden aportar valor

No hace falta crear una alerta por cada tipo desde el principio.

Si `Automático` produce demasiado ruido o pierde señal, separar:

- `Libros` para fichas bibliográficas/comerciales;
- `Noticias` para prensa;
- `Blogs` para reseñas;
- `Vídeo` para menciones/entrevistas;
- `Foros` para conversaciones orgánicas.

## Configuración de ruido

Regla:

- títulos exactos → `Todos los resultados`;
- nombre de autor → empezar con todos, bajar a mejores si hay homónimos;
- ISBN/ASIN → todos;
- dominio → todos.

No restringir a región España si eso oculta tiendas, bibliotecas o medios latinoamericanos/internacionales que hablen de los libros en español.

## Flujo de revisión

Cada email/resultados nuevos se clasifica igual que #459:

- `NEW_BACKLINK`
- `PRESS_OR_INTERVIEW`
- `REVIEW`
- `BOOK_CATALOG_RECORD`
- `AUTHOR_PROFILE`
- `METADATA_ERROR`
- `COPY_OR_ATTRIBUTION_ISSUE`
- `DUPLICATE_NO_ACTION`
- `SPAM`

No crear una issue nueva por cada mención. Solo registrar/actuar cuando haya valor.

## Qué hacer con resultados útiles

### Backlink

- comprobar que la página existe y es de calidad;
- añadirla al inventario #394 si procede;
- no pedir anchor text artificial.

### Prensa/reseña

- guardar URL;
- incorporar a `/prensa/` solo si realmente es prensa/entrevista/coverage relevante;
- no copiar reseñas completas.

### Nueva ficha

- identificar plataforma;
- comparar metadata;
- abrir/actualizar la PR específica si existe;
- corregir upstream si el error viene de editorial/DILVE.

### Copia de contenido

- comprobar si es cita legítima, sindicación o copia;
- actuar solo si hay problema real.

## Revisión a 30 días

Registrar:

- nº total de alertas recibidas;
- nº de URLs únicas útiles;
- backlinks nuevos;
- fichas nuevas;
- menciones de prensa/reseñas;
- errores corregidos;
- consultas sin señal.

Después:

- mantener P0;
- pasar a semanal consultas de baja frecuencia;
- eliminar ruido.

## Relación con Search Console

Google Alerts no sustituye Search Console.

Search Console dice cómo Google ve/encuentra nuestro sitio; Alerts detecta **contenido nuevo de terceros** relacionado con nuestras entidades.

No confundir una alerta con una señal de indexación propia.

## Criterio de cierre

`ALERTS_CREATED · ACCOUNT_CONFIRMED · SETTINGS_TUNED · ISBN_ASIN_ALERTS_EVALUATED · FIRST_30_DAY_REVIEW_PLANNED · ACTION_CLASSIFICATION_DOCUMENTED · ZERO_COST`
