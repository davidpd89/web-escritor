# Investigación de GPT — autores, identidad y biografías

**P1 · DRAFT · NO MERGEAR.** Coordinación: [#691](https://github.com/davidpd89/web-escritor/pull/691). Relacionada: [#687](https://github.com/davidpd89/web-escritor/pull/687), [#680](https://github.com/davidpd89/web-escritor/pull/680), [#683](https://github.com/davidpd89/web-escritor/pull/683).

## Gap exacto (22/10/2026)

`main` publica 31 autores, 30 biografías con URL fuente; `scripts/reading_intake_pipeline.py` crea perfiles al importar libros y refresca extractos breves de fichas de autor Penguin, con comprobación de homónimos. La #687, **no fusionada**, propone 55 autores y 41 biografías. **No falta el generador de perfiles**: faltan fuentes independientes, datos atribuibles, resolución de identidades en editoriales distintas y mejoras que aporten valor incluso si el autor no tiene biografía pública.

## Objetivos y límites

- Entidad de autor estable: identificador local, nombre visible, variantes, fuentes, ISNI/VIAF/Wikidata/Open Library si verificadas; homónimos no se unen por nombre o ISBN sin evidencia.
- Ficha editorial homogénea: presentación atribuida, todos **los libros que figuran en nuestro catálogo**, sellos verificados, géneros/temas de esos libros, cronología y obra relacionada; no afirmar «bibliografía completa» del autor.
- Biografía breve de elaboración propia a partir de **hechos comprobados** o fragmento autorizado según licencias. Distinguir nombre, país, fechas y premios de datos inciertos; no inventar fechas ni reproducir biografías enteras. Si no hay biografía, mostrar contexto útil, no texto SEO artificial.
- Evitar trabajos duplicados: el mismo cambio autor/libro/sello actualiza páginas y sitemap por el único builder existente. No sumar un CMS o LLM diario.
- Fijar cobertura y caducidad para campos cambiantes (web y redes oficiales) y política de erratas/fuentes retiradas.

## Fuentes candidatas comprobadas

- [Open Library](https://openlibrary.org/developers/api): API de autores y obras; **uso de bajo volumen**, prohíbe utilizarla de backend masivo; para escala utilizar dumps y verificar licencia/atribución. Su entidad *work* no es una edición ISBN: no fusionar traducciones/títulos automáticamente.
- [Wikidata](https://www.wikidata.org/wiki/Help:Data_access): candidatos QID, aliases e identificadores; `sameAs` únicamente con identidad verificada y con prueba, no por similitud. Consultas SPARQL acotadas.
- Fichas de autor **editoriales oficiales** (Penguin ya conectada, Planeta en estudio #680), derechos de reutilización y robots por proveedor; no copiar textos completos.
- [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) MIT puede ayudar a crear **cola de posibles duplicados**; la decisión requiere otra evidencia independiente.

## Experimentos ordenados

- **A1:** comparar 31 perfiles `main` y 55 candidatos #687: sin biografía, fuentes rotas/antiguas, autor de varias editoriales, alias y homónimos.
- **A2:** 10 autores reales con y sin ficha editorial: probar correspondencia manual de identificadores oficiales, coste/política API y cobertura; registrar aciertos y falsos positivos.
- **A3:** adaptador offline optativo `scripts/research/gpt_author_identity_candidates.py` + test de ambigüedad; solo emite **propuestas**, nunca publica `sameAs` ni modifica páginas.
- **A4:** prototipo de una plantilla mejorada con 3 casos (1 libro, coautoría, autor con libros en 2 editoriales), SEO `Person`/breadcrumbs y accesibilidad; benchmark HTML y `Pagefind`.
- **A5:** contrato de mantenimiento, revalidación temporal y transición a #687 cuando esté fusionada.

**Criterio de salida:** ninguna biografía ni relación inventada; identidad fiable, cobertura medible, cambios reversibles, datos aportados por cada fuente y plan claro para integrar con el builder. **Sin tests ejecutados ni despliegues.**
