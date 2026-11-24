Antes de responder, busca en internet actual (Wikipedia en español e inglés, web oficial del autor, editoriales, prensa cultural, bibliotecas como BNE o VIAF, Goodreads) y basa la respuesta en esas fuentes. Usa tu memoria solo para lo que confirmes en ellas.

Escribes la ficha de un autor para davidportodiaz.com, una web española de libros recomendados. La ficha debe responder lo que busca en Google o en una IA quien escribe el nombre del autor: quién es, por dónde empezar a leerle, qué libros tiene y en qué orden, si tiene sagas y qué autores se le parecen. Escribe en español de España, en tono informativo, sin opiniones ni adjetivos de promoción («imprescindible», «magistral», «fascinante»…), sin muletillas de IA y sin hablar de las fuentes dentro del texto.

Datos del autor en nuestra web (los libros son ediciones a la venta en España; puede haber varias ediciones de una misma obra):

{{AUTOR}}

Responde con un único bloque ```json con este objeto, sin texto fuera del bloque:

```json
{
  "slug": "el mismo slug de arriba",
  "identificado": true,
  "intro": "50-90 palabras: quién es (nacionalidad, oficio), qué escribe y por qué se le conoce. Empieza por su nombre.",
  "por_donde_empezar": [{"titulo": "título en España", "motivo": "una o dos frases: por qué es buena entrada (la más conocida, la primera de una saga, la más breve, la premiada…)"}],
  "obras": [{"titulo": "título en España (o el original si no se ha traducido)", "titulo_original": "solo si es distinto", "anio": 1974, "saga": "nombre de la saga o null"}],
  "sagas": [{"nombre": "nombre de la saga", "libros": ["título 1", "título 2"]}],
  "biografia": "120-250 palabras en dos o tres párrafos separados por \n\n: origen, formación, trayectoria, obras clave, premios y adaptaciones verificados.",
  "parecidos": [{"nombre": "uno de los candidatos", "motivo": "una frase con lo que comparten (tema, tono, público, época)"}],
  "faq": [{"pregunta": "¿…?", "respuesta": "1-3 frases con datos concretos"}],
  "fuentes": [{"titulo": "nombre de la página", "url": "https://..."}]
}
```

Reglas:
- `identificado`: false si no encuentras con seguridad a esta persona (homónimos, autor sin rastro en internet). En ese caso deja el resto vacío: es mejor no publicar que inventar.
- `por_donde_empezar`: 2 o 3 obras. Prioriza las que están en nuestra lista de libros si son buena entrada; usa el título exacto de nuestra lista cuando coincida.
- `obras`: sus libros principales (hasta 30) con el año de la PRIMERA publicación original, no el de la edición española. Sin antologías de otros ni prólogos.
- `sagas`: solo si existen, con los libros en orden de lectura. Si no tiene, lista vacía.
- `parecidos`: de 2 a 4, elegidos SOLO entre los candidatos dados, con el nombre escrito igual. Si ninguno se parece de verdad, lista vacía.
- `faq`: de 3 a 5 preguntas que la gente busca de este autor en concreto (orden de lectura de una saga, su libro más famoso, adaptaciones, si sigue escribiendo, su nacionalidad…). Nada de preguntas sobre dónde comprar ni genéricas que valgan para cualquier autor.
- `fuentes`: de 2 a 6 páginas que hayas consultado de verdad, con URL https completa.
- No pongas enlaces, Markdown ni comillas tipográficas dentro de los textos. Cifras, premios y fechas solo si están en las fuentes.
