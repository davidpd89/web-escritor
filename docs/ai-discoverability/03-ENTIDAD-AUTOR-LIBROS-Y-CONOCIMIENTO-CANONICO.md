# 03 — Entidad, autor, libros y conocimiento canónico

## 1. Objetivo

Conseguir que un sistema que necesite responder sobre David Porto Díaz pueda resolver sin ambigüedad:

- quién es;
- qué ha publicado;
- qué obra pertenece a qué editorial;
- qué premio corresponde al autor y cuál no;
- qué es Noveris;
- qué fechas/ISBN/páginas son correctos;
- dónde está la fuente oficial;
- qué URLs externas representan exactamente la misma entidad.

Esto no garantiza una recomendación, pero reduce el coste de verificación y el riesgo de hallucination.

---

## 2. Grafo canónico mínimo

### Persona

`https://davidportodiaz.com/#author`

Debe conectar:

- nombre: David Porto Díaz;
- profesión pública: escritor;
- web oficial;
- imagen autorizada;
- lugar de nacimiento y residencia solo mientras sean datos públicos autorizados;
- obras;
- premios/reconocimientos con atribución precisa;
- perfiles `sameAs` exactos.

### Obra: Samuel

Nodo estable:

`https://davidportodiaz.com/#book-samuel`

y página canónica:

`https://davidportodiaz.com/libros/samuel-entre-mundos/`

Hechos canónicos actuales:

- David Porto Díaz;
- Libros Indie;
- 2025;
- ISBN `9791387659776`;
- ASIN `B0GB6LGQFH`;
- 422 páginas;
- tapa blanda;
- castellano;
- fantasía juvenil / fantasía de portales / ficción especulativa.

### Obra: Manecillas

Nodo estable:

`https://davidportodiaz.com/#book-manecillas`

y página:

`https://davidportodiaz.com/las-manecillas-del-recuerdo/`

Hechos actuales:

- David Porto Díaz;
- Monza Ediciones;
- publicación 03/09/2026;
- ISBN `979-8-90514-935-1`;
- 272 páginas;
- tapa blanda;
- PVP editorial 16 €;
- novela coral / ficción especulativa / narrativa familiar;
- sin retailer/Offer hasta disponer de URL verificada.

### Noveris

- lugar ficticio;
- parte del universo narrativo de Samuel;
- no empresa ni localización real;
- URL canónica `/universo/noveris/`;
- Wikidata Q139927664.

---

## 3. Single source of truth

### Regla

Un dato factual no debe escribirse manualmente en diez superficies independientes si puede derivarse de una autoridad interna controlada.

### Superficies derivadas o verificadas

- home JSON-LD;
- Autor;
- libros;
- ficha individual;
- `/ai/`;
- `llms.txt`;
- `llms-full.txt`;
- press-kit JSON;
- asistente local;
- sitemap/metadata cuando el hecho influya;
- tests.

### DoD

Modificar un hecho central debe provocar una comprobación de paridad en todas las superficies públicas relevantes.

---

## 4. `sameAs` no significa «habla de mí»

### Usar `sameAs` para

- perfil exacto de David;
- ficha exacta del mismo libro cuando la semántica lo permita;
- entidad Wikidata correspondiente.

### No usar `sameAs` para

- una reseña;
- un artículo sobre David;
- una entrevista;
- una noticia de evento;
- un comparable;
- una editorial si el nodo es David.

Para cobertura externa usar relaciones como `subjectOf` cuando semánticamente corresponda.

---

## 5. Identificadores fuertes

### Persona

- Wikidata;
- ORCID;
- Amazon Author Central;
- perfiles sociales oficiales;
- perfiles de lectura/autor exactos.

### Libros

- ISBN;
- ASIN cuando existe;
- ficha editorial;
- retailer exacto;
- Goodreads/Open Library/LibraryThing/etc. cuando la ficha sea inequívoca.

### Prioridad

Los identificadores reducen homonimia. No son puntos que haya que coleccionar sin criterio.

---

## 6. Desambiguación explícita

### David Porto Díaz

La página del autor debe indicar de forma natural:

- escritor gallego nacido en Pontevedra;
- residente en Madrid;
- autor de las dos obras conocidas del proyecto.

### Noveris

Mantener texto visible:

> Noveris es una ciudad ficticia del universo de Samuel entre mundos.

Esto resuelve colisiones con empresas o marcas reales.

### Premio Letras Como Espada

Debe quedar siempre claro:

- premio al autor;
- certamen de microrrelatos;
- no premio de Samuel;
- no premio de Manecillas.

### Juan Andrés Teno

- finalista Top 10 del autor;
- no atribuir obra si fuente oficial no la identifica.

---

## 7. Datos que NO debemos canonizar sin fuente

- edades de lectura «oficiales» no publicadas por editor;
- número dinámico de estrellas/reseñas como hecho permanente;
- ventas;
- rankings comerciales;
- stock;
- precio retailer;
- fechas de futuras ediciones no anunciadas;
- premios de obra inexistentes;
- retailers de Manecillas no verificados;
- supuesta continuación de Samuel;
- equivalencia con Harry Potter/Percy Jackson como hecho.

---

## 8. Schema.org: estrategia

### Mantener

- `Person`;
- `Book`;
- `WebSite`;
- `WebPage`;
- `Article`/`BlogPosting` para Cuaderno si corresponde;
- `Event` para eventos reales;
- `BreadcrumbList`;
- `ImageObject` donde aporte contexto.

### Añadir solo si el contenido existe

- `VideoObject` para vídeos originales indexables;
- `ProfilePage` si el patrón y soporte encajan;
- `Organization` para editoriales solo como entidad real relacionada;
- `Offer` solo con oferta real y verificable.

### No crear «AI schema»

Google confirma que no existe schema especial requerido para AI Search.

---

## 9. Texto visible > JSON-LD huérfano

Los sistemas de búsqueda esperan que datos estructurados representen contenido real de la página.

Por tanto, las páginas de libro deben mostrar humanamente:

- autor;
- editorial;
- fecha/año;
- ISBN;
- páginas;
- formato;
- género;
- sinopsis;
- disponibilidad verificada.

No esconder atributos recomendables solo dentro de schema.

---

## 10. Recommendation attributes

Crear una taxonomía factual para obras.

### Samuel

Campos potenciales:

- genre;
- subgenre;
- tropes;
- themes;
- protagonist age **solo si deriva del texto y se presenta como personaje, no rango lector**;
- romanceCentrality;
- magicSystem;
- settingType;
- tone;
- format;
- pageCount;
- verifiedAvailability.

### Manecillas

- novelStructure: coral;
- speculativeElement;
- themes: memoria/familia/valor/segunda oportunidad según material oficial;
- centralObject: reloj;
- format;
- pageCount;
- publisher;
- publicationDate;
- verifiedAvailability.

### Regla

Cada atributo debe poder señalar a una página del sitio donde se explica de forma humana.

---

## 11. Entity consistency audit trimestral

Comparar:

### David

- web;
- Wikidata;
- ORCID;
- Amazon Author Central;
- Goodreads;
- Babelio;
- StoryGraph;
- LinkedIn;
- redes oficiales.

### Samuel

- web;
- Libros Indie;
- Amazon;
- Casa del Libro;
- Goodreads;
- Open Library;
- LibraryThing;
- Qué Libro Leo;
- ISFDB.

### Manecillas

Añadir únicamente fuentes públicas reales a medida que aparezcan.

### Resultado

Crear issue por discrepancia factual externa relevante con:

- fuente;
- dato incorrecto;
- dato canónico;
- evidencia;
- vía de corrección;
- estado.

---

## 12. Datos versionados

Para cada hecho cambiante, registrar:

- valor;
- fuente;
- `verifiedAt`;
- si es publicable;
- superficies afectadas;
- si requiere recrawl.

Ejemplo conceptual:

```json
{
  "publicationDate": {
    "value": "2026-09-03",
    "source": "Monza / contrato editorial autorizado",
    "verifiedAt": "2026-08-27",
    "public": true,
    "recrawlCritical": true
  }
}
```

---

## 13. Factual mutation tests

Una futura prueba debería mutar temporalmente:

- ISBN;
- publisher;
- publicationDate;
- numberOfPages;

Y comprobar que el validador detecta divergencia en superficies públicas derivadas.

Esto evita que una IA encuentre dos verdades distintas dentro del mismo dominio.

---

## 14. Política de fechas

Distinguir:

- `datePublished` del contenido web;
- `dateModified` del contenido web;
- fecha de publicación de la obra;
- fecha del evento;
- fecha de verificación factual.

No mezclar estas cuatro fechas.

Para crawlers, `dateModified` debe cambiar cuando hay una modificación material, no cada build.

---

## 15. Correcciones

Proponer una ruta pública pequeña:

`/correcciones/`

o una sección dentro de Metodología editorial.

Debe explicar:

- cómo reportar un error;
- que los errores factuales se corrigen;
- cómo se marca una corrección material cuando corresponde;
- qué email usar.

No hace falta publicar un historial vacío ni teatralizar errores inexistentes.

---

## 16. Knowledge panel / entity claims

No prometer Knowledge Panel ni «entidad Google» como resultado automático.

Sí mantener:

- WebSite/Person coherentes;
- Wikidata correcto;
- perfiles externos;
- cobertura real;
- autoría clara;
- no duplicar identidades.

---

## 17. Política de external profiles

Antes de añadir un nuevo perfil al `sameAs`:

1. confirmar que es oficial;
2. confirmar que no es una búsqueda/listado ambiguo;
3. rellenar datos mínimos coherentes;
4. enlazar desde el sitio solo si aporta valor;
5. evitar crear cuentas vacías solo por SEO.

---

## 18. Definición de éxito

Una consulta como:

> «¿Cuándo se publicó Samuel entre mundos de David Porto Díaz?»

no debería encontrar 2025 en una fuente, 2026 en otra y una fecha diferente en una tercera.

Una consulta como:

> «¿Qué premio ganó Samuel entre mundos?»

no debería recibir el premio de microrrelatos atribuido a la novela.

Una consulta como:

> «¿Qué es Noveris?»

no debería confundir la ciudad ficticia con una empresa real.

La entidad está bien diseñada cuando esas respuestas son aburridamente consistentes.
