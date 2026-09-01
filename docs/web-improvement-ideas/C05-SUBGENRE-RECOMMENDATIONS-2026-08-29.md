# C.5 · Ampliar recomendaciones evergreen por subgénero/edad/tono

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `REJECT` para expansión mecánica.

## Veredicto

#135 acabó rechazando la propuesta tal como estaba formulada: crear más páginas de recomendaciones por combinaciones de subgénero, edad o tono sin demanda demostrada introduce riesgo de scaled content y canibalización.

Esto **no prohíbe para siempre una URL nueva**. El gate final es mucho más estricto: intención diferenciada + demanda medida + análisis original. Mientras tanto, optimizar activos que ya reciben impresiones.

## Hipótesis original

La lista inicial proponía más páginas tipo «portal fantasy en español» segmentadas por edad/tono, aprovechando la arquitectura de recomendaciones ya existente.

La suposición implícita era que más cobertura long-tail podía ampliar tráfico.

## Evolución histórica

### Primera revisión → `REJECT`

La revisión 108/108 fue clara:

- no expansión mecánica por keyword/subgénero;
- riesgo de scaled content;
- riesgo de canibalización;
- nueva URL solo con intención distinta, análisis original y demanda medida.

### Matriz intermedia → `DEFERIR salvo demanda`

La matriz suavizó temporalmente el rechazo:

> no abrir más recomendaciones por edad/tono sin queries, impresiones, backlinks o valor editorial; primero explotar `portal fantasy` existente.

No es una aprobación; conserva un trigger factual para reevaluar.

### Autoridad final → `REJECT`

El cierre vuelve al estado más estricto:

> «No producir recomendaciones long-tail por edad/tono sin demanda; priorizar URLs ya posicionadas (`portal fantasy`).»

### Revalidación independiente

C.5 y C.6 fueron citadas expresamente como decisiones correctamente rechazadas por riesgo de scaled/spam/link-swap.

## R.21 — evidencia propia posterior: «portal fantasy»

La sexta pasada encontró una señal real en Search Console comunicada el 27/08/2026:

```text
query: portal fantasy
impresiones: ~91
clics: 1
```

La conclusión no fue «crear cinco páginas más». Fue diseñar un **experimento CTR sobre la URL que ya recibe impresiones**:

1. recuperar URL exacta;
2. posición media, país, dispositivo y periodo;
3. observar title/snippet real;
4. formular H0/H1;
5. cambiar una sola capa (título O primer párrafo O meta description);
6. esperar muestra comparable;
7. medir.

Esto es una pieza central de C.5 porque demuestra con datos propios por qué optimizar una oportunidad existente gana a fabricar long-tail.

## R.31 — Google Trends como filtro, no fábrica de URLs

La séptima pasada añadió Google Trends:

- escala 0–100 = interés relativo normalizado, no volumen absoluto;
- 0 no implica necesariamente cero búsquedas;
- related/rising queries son input de investigación;
- Search Console refleja demanda que ya toca el dominio;
- Trends aporta contexto externo/estacionalidad.

Antes de crear contenido por una query rising, hay que comprobar intención, solapamiento y capacidad de aportar algo original.

## Arquitectura existente que refuerza el rechazo

A.1 ya documentó `data/topic-collections.json` y `build-topic-collections.py`: el sitio puede agrupar piezas reales cuando existe una familia sustancial. No hace falta crear páginas para «completar un cluster».

Las recomendaciones y Cuaderno ya contienen activos sobre portal fantasy/worldbuilding. C.5 no debe competir consigo misma.

## Gate de reevaluación

Solo reabrir una URL nueva si se cumplen simultáneamente:

```text
measured demand
AND distinct search/user intent
AND existing URLs cannot satisfy it cleanly
AND substantial original analysis
AND editorial maintenance capacity
AND no scaled-template pattern
```

Señales aceptables de demanda:

- queries/impressions GSC/Bing;
- preguntas reales repetidas (C.3);
- Trends como contexto;
- enlaces/referrals hacia un tema;
- necesidad editorial explícita de lectores.

## Cómo decidir ENRICH vs NEW

### `ENRICH_EXISTING`

Cuando la intención cabe en una página ya posicionada y añadir sección mejora al lector.

### `NEW`

Solo cuando la nueva necesidad tiene suficiente autonomía: responde otra pregunta, requiere estructura propia y no deja dos URLs compitiendo por lo mismo.

### `NO_ACTION`

Cuando la demanda es mínima, la intención no está clara o el contenido resultante sería genérico.

## Qué significa «análisis original»

No basta listar libros encontrados en retailers. Debe existir criterio/editorial real, por ejemplo:

- comparación de elementos narrativos;
- taxonomía explicada;
- experiencia de lectura;
- selección razonada;
- distinciones que ayuden a decidir;
- fuentes verificables donde correspondan.

## Riesgos

- canibalización entre recomendaciones;
- thin content;
- scaled content abuse;
- títulos distintos con cuerpo casi idéntico;
- páginas obsoletas que exigen mantenimiento;
- recommendations sin experiencia/criterio;
- crear páginas por cada filtro de UI;
- convertir Trends o keyword tools en órdenes editoriales.

## Alternativa documentada en overrides

En vez de páginas por subgénero:

> usar Search Console/Bing para detectar intención diferenciada y enriquecer una URL existente; crear una nueva solo con demanda + análisis original.

## Relación con C.3

C.3 es una fuente válida de demanda. Preguntas repetidas pueden demostrar que una segmentación resuelve un problema real.

## Relación con A.1

Agrupar contenido real mediante topic collections no obliga a producir nuevos satélites. La colección sigue a las piezas; no al revés.

## Relación con B.3/B.8

Un answer block o TL;DR no convierte una página duplicada en útil. Formato no sustituye intención.

## Qué NO hacer

- «mejores libros X para adolescentes», «para adultos», «oscuros», «románticos» como patrón automático;
- generar listas con IA;
- copiar sinopsis de retailers;
- crear páginas para cada filtro;
- usar número mínimo de palabras como criterio;
- medir éxito solo por páginas indexadas;
- cambiar varias variables a la vez en el experimento de portal fantasy.

## Pasadas posteriores revisadas

- cuarta/quinta: sin override específico;
- sexta: R.21 aporta experimento CTR real;
- séptima: R.31 aporta Trends como filtro de demanda;
- octava–decimoquinta: no cambian el estado final;
- revalidación independiente reafirma expresamente el rechazo.

## Trazabilidad

- hipótesis original;
- revisión `REJECT`;
- matriz `DEFERIR salvo demanda`;
- override/alternativa de enriquecer existente;
- R.21 Search Console;
- R.31 Google Trends;
- autoridad machine-readable;
- autoridad final `REJECT`;
- revalidación independiente.

## Recomendación para Clara/Claude

**No implementar expansión long-tail.** Primero trabajar la URL real de portal fantasy y otras superficies con demanda observada. Solo abrir una nueva pieza si supera el gate de intención/demanda/originalidad.