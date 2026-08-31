# /ai/ — contrato visual y de integridad factual

Fecha: 2026-08-31
Estado: contrato preparado; implementación pendiente
Cadena: continúa después de `DISEÑO - Accesibilidad` (#288)

## Superficie

- `/ai/`

La ruta es pública, indexable y se presenta explícitamente como documento oficial de autoridad editorial y datos machine-readable. Por tanto, exactitud factual y estabilidad pesan más que decoración.

## Baseline verificado

La página actual:

- usa `assets/v1-ai-authority.css` como owner propio;
- es text-first y no depende de runtime decorativo;
- utiliza tokens semánticos y no presenta una fuga cromática legacy relevante;
- tiene header reducido propio en vez del shell interactivo completo;
- enlaza `/llms.txt`, `/llms-full.txt`, JSON de press-kit y páginas humanas de verificación;
- publica WebPage JSON-LD;
- contiene ledgers de hechos sobre autor, obras, identificadores y fuentes.

La hoja `v1-ai-authority.css` ya parte de una arquitectura razonable. Esta PR debe ser de **continuidad y precisión**, no un rediseño vistoso.

## Bloqueo factual pre-lanzamiento detectado

A fecha de este contrato, **31 de agosto de 2026**, el HTML afirma sobre `Las manecillas del recuerdo`:

- `Estado editorial: Publicada el 3 de septiembre de 2026`;
- fecha `3 de septiembre de 2026`.

El 3 de septiembre todavía es futuro. En una superficie que se define como fuente verificable, el tiempo verbal/estado no puede presentar como ocurrido un hecho futuro.

### Propagación verificada

La inconsistencia no está aislada en `/ai/`. También se ha comprobado en:

- `/llms.txt`: `Estado editorial autorizado: publicada el 3 de septiembre de 2026`;
- `/llms-full.txt`: repite ese estado y añade un “contrato temporal” que reconoce expresamente que la redacción `publicada` se mantiene incluso en material preparado antes de la fecha;
- `/press-kit/las-manecillas-del-recuerdo.json`: `publicationDate: 2026-09-03`, `status: published` y sinopsis atómica que dice `publicada el 3 de septiembre de 2026`.

Por tanto, no basta con corregir una frase visible: hay que definir una única fuente de verdad temporal y evitar divergencias entre HTML, llms y press-kit.

Antes de cerrar esta PR hay que reconciliar ese estado con una fuente editorial válida y con la fecha real del despliegue:

- antes de la publicación, usar formulación factual de estado futuro/programado solo si está documentalmente respaldada;
- desde el día efectivo de publicación, actualizar a estado publicado únicamente tras verificar que el lanzamiento ocurrió;
- sincronizar las superficies machine-readable afectadas mediante el flujo factual correspondiente;
- revisar si otras páginas/schema repiten el mismo estado antes de declarar el problema cerrado.

No inventar un nuevo estado ni asumir que una fecha prevista equivale a publicación efectiva.

## Dirección visual

**Documento de autoridad / registro verificable.**

Prioridades:

1. hechos fáciles de escanear y copiar;
2. clara jerarquía entre fuente primaria, resumen y recursos machine-readable;
3. URLs/códigos legibles;
4. ledgers densos pero cómodos;
5. impresión útil;
6. mínima dependencia de JS y movimiento;
7. continuidad azul/dorado muy contenida.

No convertirlo en landing de IA, dashboard, cards comerciales ni página promocional de libros.

## Preservar estrictamente

- canonical, robots y WebPage JSON-LD;
- identidad y enlaces verificadores;
- jerarquía de fuentes;
- identificadores (Wikidata, ORCID, ISBN, etc.) salvo corrección factual verificada;
- rutas machine-readable;
- cautelas sobre ingestión/indexación/ranking;
- lectura completa sin JS;
- ausencia de motion decorativo;
- print.

## Implementación esperada

Mantener `v1-ai-authority.css` como owner. No cargar componentes innecesarios del shell si comprometen estabilidad o legibilidad.

Revisar:

- header reducido y coherencia con identidad actual;
- hero y sello de revisión;
- cards/`authority-file` para que sigan pareciendo archivos, no marketing;
- ledgers y records;
- code/URLs largas;
- notas de fuente;
- estados de enlace/focus;
- footer;
- impresión.

## QA requerido

- desktop 1440/1280;
- tablet 1024/768;
- 390/360/320;
- zoom 200 %;
- text spacing;
- teclado/focus;
- no-JS;
- print;
- cero overflow;
- URLs e identificadores largos;
- validación JSON-LD;
- comprobación de que los links machine-readable responden en el entorno QA cuando sea viable;
- assertions de hechos atómicos contra una fuente/fixture controlada para evitar divergencia accidental.

### QA temporal

El contrato debe impedir estados imposibles del tipo `publicada`/`published` con una fecha futura respecto a la fecha efectiva de build/deploy, salvo que el término aparezca dentro de una cita o contexto inequívocamente futuro. La prueba no debe falsificar la fecha actual ni hardcodear un PASS que dejará de tener sentido tras el lanzamiento.

La cobertura debe incluir al menos `/ai/`, `llms.txt`, `llms-full.txt` y `press-kit/las-manecillas-del-recuerdo.json`, y ampliarse a cualquier otra superficie que la auditoría encuentre con el mismo hecho.

## Aislamiento

No alterar Autor, Manecillas, Samuel ni otras fuentes factuales de manera incidental. Si el bloqueo factual exige sincronización transversal, documentar exactamente qué superficies se actualizan y por qué.

## Cierre

Mantener Draft y sin merge. Esta PR no puede considerarse cerrada mientras la incoherencia temporal pre-lanzamiento siga presente o las superficies canónicas discrepen entre sí. Revisión física final bajo `REAL-DEVICE-REVIEW-CONTRACT-2026-08-29.md`.