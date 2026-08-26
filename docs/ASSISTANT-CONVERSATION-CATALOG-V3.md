# Asistente editorial V3 — catálogo conversacional

Fecha: 2026-08-24  
Este documento es la fuente de trabajo para ampliar respuestas sin convertir `assistant-local-knowledge.mjs` en una lista caótica de keywords.

## 1. Principios de voz

El asistente habla como un índice editorial útil, no como una persona ficticia ni como un soporte técnico.

Sí:

- breve;
- concreto;
- explica por qué un enlace es útil;
- reconoce ambigüedad;
- ofrece 1–3 siguientes pasos;
- diferencia datos canónicos de navegación;
- si no sabe, orienta.

No:

- «¡Genial!» repetido;
- emojis;
- «No te he entendido»;
- «Como IA…»;
- «Estoy encantado de ayudarte»;
- párrafos largos sin fuente;
- inventar disponibilidad, fechas, premios o información editorial.

## 2. Copia base recomendada

### Hero

Título: `Consulta la web`

Lead: `Busca una obra, un fragmento, un artículo, una herramienta o información sobre David. Si no hay una respuesta exacta, te llevaré a la página más útil.`

Label: `Escribe qué buscas`

Placeholder: `Por ejemplo: ¿dónde puedo leer un fragmento?`

Panel aria-label: `Consulta del sitio`

Log aria-label: `Resultados de la consulta`

Bienvenida: `Escribe qué buscas. Puedo responder sobre el contenido publicado o llevarte directamente a la sección adecuada.`

Estado de búsqueda: `Buscando en la web…`

## 3. Modelo de intención

Cada turno se entiende como combinación de:

- `entity`: de qué habla;
- `action`: qué quiere hacer;
- `intent`: tarea final;
- `context`: qué se preguntó antes.

No hace falta que una frase contenga una keyword exacta si una entidad conocida se reconoce con suficiente confianza.

## 4. Entidades y alias

### `manecillas`

Alias fuertes:

- las manecillas del recuerdo
- manecillas
- el libro de las manecillas
- el libro del reloj
- reloj del recuerdo

Erratas tolerables solo para token largo/nombre propio:

- maneciyas
- manecilas
- manecilllas

No activar por `reloj` a secas si la pregunta no tiene contexto de obra, porque puede aparecer en otro contenido.

### `samuel`

Alias:

- Samuel entre mundos
- Samuel
- el libro de Samuel

### `noveris`

Alias:

- Noveris
- universo de Samuel
- mundo de Samuel

### `author`

Alias:

- David
- David Porto
- David Porto Díaz
- autor
- escritor

`David` a secas solo debe resolver como autor cuando existe una acción/contexto relevante (`quién es`, `biografía`, `contactar`, `premios`, etc.).

### `tools`

Alias conceptuales:

- herramientas
- recursos para escritores
- utilidades
- revisar texto
- revisar manuscrito
- analizar texto

Las herramientas concretas no necesitan intent manual si Pagefind puede localizar su página por título/contenido.

## 5. Acciones normalizadas

### `read`

leer, probar, ver un fragmento, muestra, capítulo, primeras páginas, leer gratis, echar un vistazo.

### `navigate`

dónde está, llévame, ir a, abrir, enlace, página, sección, dónde encuentro, cómo llego.

### `discover`

qué hay, qué puedo encontrar, por dónde empiezo, enséñame, orientarme, no sé qué buscar.

### `submit`

enviar manuscrito, mandar novela, presentar obra, buscar editorial.

### `contact`

contactar, correo, email, entrevista, prensa, medio, podcast.

### `attend`

evento, firma, feria, presentación, agenda.

## 6. Intents P0 y respuesta canónica

### `greeting`

Ejemplos:

- Hola
- Buenas tardes
- Hey, ¿qué tal?

Respuesta:

`Hola. Puedes preguntarme por los libros, fragmentos, artículos, herramientas, editoriales, convocatorias, eventos o información sobre David.`

Siguientes pasos: Obras · Leer un fragmento · Herramientas.

No mostrar fuentes documentales para un saludo.

### `capabilities`

Ejemplos:

- ¿Qué puedes hacer?
- ¿Para qué sirve esto?
- ¿En qué me ayudas?

Respuesta:

`Sirvo para encontrar contenido dentro de esta web. Puedo responder preguntas breves sobre lo publicado y, si no hay una respuesta exacta, llevarte a la página más útil.`

### `site-overview`

Ejemplos:

- ¿Qué hay en esta web?
- No sé por dónde empezar
- Enséñame las secciones
- ¿Qué enlaces tienes?
- ¿Hay un mapa de la web?

Respuesta:

`La web se organiza en cuatro rutas principales: Obras, Cuaderno, Herramientas y la zona de Autor/Prensa. Si me dices si vienes a leer, escribir o buscar información sobre David, puedo afinar el camino.`

Fuentes: `works-hub`, `notebook-hub`, `tools-hub`, `press` (renderizar máximo 3–4 según UI).

Nota: hoy no existe una página pública específica de “mapa del sitio”; no se debe inventar esa URL. Esta respuesta hace de mapa conversacional usando rutas reales.

### `works`

Ejemplos:

- ¿Qué libros hay?
- Quiero ver sus novelas
- Llévame a las obras

Respuesta:

`Puedes empezar por Obras. Allí están «Las manecillas del recuerdo» y «Samuel entre mundos», con acceso a sus páginas y materiales de lectura.`

Fuentes: `works-hub`, `work-manecillas`, `work-samuel`.

### `manecillas`

Ejemplos:

- ¿De qué trata Manecillas?
- Háblame del libro del reloj
- ¿Qué es Las manecillas del recuerdo?

Respuesta actual canónica: mantener el resumen ya verificado por la web. No ampliar con datos no presentes en la fuente.

Fuente: `work-manecillas`.

### `manecillas-fragment`

Ejemplos:

- Quiero probar Manecillas
- ¿Hay fragmentos del libro del reloj?
- ¿Puedo leer algo antes?

Respuesta:

`Sí. Hay una página con fragmentos de «Las manecillas del recuerdo». Puedes leerlos aquí antes de ir a la ficha del libro.`

Fuente: `work-manecillas-fragments`.

### `samuel`

Ejemplos:

- ¿De qué trata Samuel?
- Háblame de Samuel entre mundos

Fuente: `work-samuel`.

### `samuel-fragment`

Ejemplos:

- ¿Puedo leer el primer capítulo de Samuel?
- Quiero probar Samuel

Respuesta:

`Sí. El primer capítulo completo de «Samuel entre mundos» está disponible para leer en la web.`

Fuente: `samuel-fragment`.

### `fragment-choice`

Ejemplos:

- Quiero leer un fragmento
- ¿Hay algo para probar?

Respuesta:

`Sí. ¿Quieres leer «Las manecillas del recuerdo» o el primer capítulo de «Samuel entre mundos»?`

Sugerencias: Las manecillas · Samuel.

`pending: fragment-choice`.

### `noveris`

Ejemplos:

- ¿Qué es Noveris?
- Llévame al mundo de Samuel
- Quiero ver el universo del libro

Respuesta:

`Noveris es el mundo fantástico de «Samuel entre mundos». Su guía reúne el universo, las facciones, el sistema mágico y el glosario.`

Fuente: `samuel-noveris`.

### `author`

Ejemplos:

- ¿Quién es David Porto?
- Quiero ver la biografía
- Háblame del autor

Respuesta:

`La página de Autor reúne la biografía, trayectoria y obra de David Porto Díaz.`

Fuente: `author`.

### `press/contact`

Ejemplos:

- ¿Cómo contacto con David?
- Soy periodista
- ¿Dónde está el kit de prensa?
- Quiero proponerle una entrevista

Respuesta:

`Para contacto profesional, entrevistas, reseñas o medios, la página de Prensa reúne los materiales y la vía de contacto adecuada.`

Fuente: `press`.

### `events`

Ejemplos:

- ¿Dónde firma?
- ¿Hay presentaciones?
- Próximos eventos

Respuesta:

`La página de Eventos y firmas reúne las fechas públicas disponibles y su contexto.`

Fuente: `events`.

No decir que existe un “próximo” evento concreto salvo que la fuente actual lo sostenga.

### `awards`

Ejemplos:

- ¿Qué premios tiene?
- ¿Qué ha ganado?
- Reconocimientos

Respuesta:

`Los premios y reconocimientos están reunidos en una página específica para poder comprobar cada mención con su contexto.`

Fuente: `awards`.

### `editorials`

Ejemplos:

- ¿Dónde envío mi manuscrito?
- Busco editorial
- ¿Quién acepta novelas?

Respuesta:

`Hay un directorio de editoriales que aceptan manuscritos. Úsalo para localizar opciones y comprobar sus condiciones antes de enviar una obra.`

Fuente: `editorials-hub`.

### `opportunities`

Ejemplos:

- concursos para escritores
- convocatorias
- premios literarios
- dónde presentar un relato

Respuesta:

`El directorio de convocatorias reúne concursos, premios y oportunidades para escritores en una sola página.`

Fuente: `opportunities`.

### `tools`

Ejemplos:

- herramientas para escritores
- quiero revisar un texto
- necesito analizar un manuscrito

Respuesta:

`La sección de Herramientas reúne utilidades gratuitas para revisar texto, estructura y personajes y preparar publicación o materiales editoriales.`

Fuente: `tools-hub`.

Para una herramienta específica desconocida, delegar en Pagefind en vez de añadir un `if` por cada herramienta.

### `recommendations`

Respuesta:

`La sección de Recomendaciones organiza lecturas por afinidades, temas y tipos de fantasía.`

Fuente: `recommendations-hub`.

### `notebook`

Respuesta:

`El Cuaderno reúne los artículos y piezas editoriales de la web. Puedes entrar por el índice y seguir por tema.`

Fuente: `notebook-hub`.

## 7. Preguntas que deben ir a Pagefind, no al router

Ejemplos:

- ¿Hay una herramienta para medir el diálogo?
- ¿Tienes algo sobre legibilidad?
- ¿Escribiste sobre portal fantasy?
- ¿Hay un artículo sobre worldbuilding?
- ¿Qué pone en el artículo de la Feria del Libro?

Motivo: son consultas de contenido concreto. Mantenerlas en el router obligaría a duplicar el índice editorial. Pagefind ya conoce las páginas y sus encabezados.

## 8. Render de resultado Pagefind

### 1 resultado fuerte

`He encontrado una página que encaja con lo que buscas.`

Luego:

**Título de la página**  
Excerpt limpio de 1–2 líneas.  
`Abrir →`

### 2–3 resultados

`Estas son las páginas más relacionadas. Empezaría por la primera:`

Presentar máximo tres filas, cada una con título y excerpt breve.

No numerar visualmente como citas académicas si no estamos respondiendo un hecho; son rutas de navegación.

## 9. Fallback sin resultados

Texto definitivo recomendado:

`No encuentro una página que responda exactamente a eso. Si buscabas algo dentro de esta web, puedo llevarte a Obras, Cuaderno, Herramientas o Prensa.`

Acciones:

- `Ver obras`
- `Ir al Cuaderno`
- `Abrir herramientas`

Si el query parece de contacto, priorizar Prensa.

## 10. Off-domain

Ejemplo: `¿Qué tiempo hace en Madrid?`

No intentar contestar. Respuesta:

`Este asistente solo consulta el contenido de esta web. Si buscabas algo sobre David, sus libros o recursos para escritores, dime qué necesitas y te llevo a la sección adecuada.`

Acciones: Obras · Herramientas · Autor.

## 11. Erratas

La tolerancia a errores debe ser conservadora.

Regla recomendada:

- solo comparar tokens >=5 caracteres;
- distancia máxima 1 para 5–7 caracteres;
- distancia máxima 2 para >=8;
- aplicar fuzzy principalmente a alias de entidades y títulos, no a palabras comunes como `libro`, `leer`, `autor`;
- una coincidencia fuzzy nunca debe sobreponerse a una coincidencia exacta de otra intención.

Ejemplos que deberían funcionar:

- maneciyas → manecillas
- smauel → samuel (solo si el resto de la consulta apunta a un libro)
- editorlaes → editoriales

Ejemplos que no deben adivinarse:

- `reloj` → no activar Manecillas automáticamente si no hay más contexto;
- `david` → no asumir “biografía” si la pregunta es ambigua.

## 12. Contexto de conversación

Contexto mínimo, no memoria larga:

```js
{
  pending: null | "fragment-choice",
  lastIntent: null | "..."
}
```

No guardar la conversación en servidor. No hace falta para este caso.

P2 posible:

- `pending: choose-work`
- `pending: choose-tool`
- `lastEntity: manecillas|samuel|...`

Solo si aparece un caso real donde reduzca fricción.

## 13. Tests mínimos obligatorios

### Exactos

- Hola → greeting
- ¿Qué puedes hacer? → capabilities
- ¿Qué libros hay? → works
- ¿De qué trata Manecillas? → manecillas
- ¿Puedo leer Samuel? → samuel-fragment
- ¿Dónde mando un manuscrito? → editorials

### Naturales

- Llévame a los libros → works
- No sé por dónde empezar → site-overview
- Quiero probar el libro del reloj → manecillas-fragment
- Busco dónde mandar mi novela → editorials
- Soy periodista y quiero contactar → press

### Erratas

- maneciyas → manecillas
- maneciyas + fragmento → manecillas-fragment

### Ambigüedad

- Quiero leer un fragmento → fragment-choice
- respuesta `Samuel` con pending → samuel-fragment

### No secuestro

- Hola, ¿de qué trata Manecillas? → manecillas, no greeting
- ¿Qué tiempo hace en Bilbao? → null/router; después fallback off-domain/local directory

### Seguridad

- ninguna respuesta local introduce una URL arbitraria;
- todos los `sourceIds` existen en registry;
- el remoto sigue OFF por defecto;
- una respuesta remota sin fuentes/citas falla cerrada.

## 14. Regla de mantenimiento

Antes de añadir una nueva keyword manual, preguntar:

1. ¿Es una intención de alto valor o solo contenido concreto?
2. Si es contenido concreto, ¿Pagefind ya lo encuentra?
3. ¿Puede resolverse añadiendo un alias a una entidad existente?
4. ¿La respuesta contiene un hecho que puede cambiar? Si sí, preferir navegación a una fuente viva en lugar de hardcodearlo.

Esta regla evita que el asistente vuelva a crecer como una lista interminable de `if`.