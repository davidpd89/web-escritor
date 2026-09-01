# B.9 · Revalidación de producción — glosario de Noveris

Fecha: 2026-08-29  
Base: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #175  
Decisión: **ALREADY_COVERED · PRESERVE_CANONICAL_GLOSSARY · NO_PARALLEL_GLOSSARY**

## Conclusión

El trigger histórico de B.9 ya está materializado en `/universo/noveris/`. La página no contiene solo menciones dispersas: ofrece un glosario humano visible y un `DefinedTermSet` coherente con ese contenido.

Crear otra URL, otro JSON o un segundo “diccionario para IA” fragmentaría el canon y aumentaría el riesgo de drift.

## Estado real de Noveris

La página actual incluye:

- hero que presenta la URL como ciudad, sistema mágico y archivo de términos;
- respuesta rápida sobre qué es Noveris;
- explicación del sistema, historia, mapa y canalizadores;
- `<section id="glosario">` visible;
- tarjetas de términos como Canalizador, Sael, Zakra, Gorx, Velukis, Glissaro, Vara Glytch, Glíder, Veltris, Sernía, Melastra, Velo/Barrera, Espejo Ancestral y Silenciadoras;
- `DefinedTermSet` JSON-LD `https://davidportodiaz.com/universo/noveris/#glosario`;
- `hasDefinedTerm` para el conjunto canónico;
- `DefinedTerm` de Noveris enlazado a su Wikidata verificado.

La implementación supera el “piloto de glosario” planteado en #135: ya es una superficie editorial real.

## Semántica de Schema.org

Schema.org define `DefinedTermSet` como un conjunto de términos definidos, por ejemplo una clasificación, glosario, diccionario o enumeración. `hasDefinedTerm` relaciona ese conjunto con objetos `DefinedTerm`.

Eso encaja semánticamente con la superficie actual de Noveris.

No se interpreta como una rich-result feature de Google ni como garantía de citas/ranking. La razón para conservarlo es consistencia semántica con un glosario humano real, no una promesa SEO.

## Relación con B.4

El `sameAs` de Noveris apunta al QID verificado y queda cubierto por `scripts/check-wikidata-sameas.py`. No se añaden QIDs por intuición ni un knowledge graph paralelo.

## Relación con A.7

Durante esta revalidación se confirmó que `main` también contenía un nodo `FAQPage` en Noveris. Esa regresión **no pertenece a B.9**.

Se corrige en #156/A.7, que retira el `FAQPage` y preserva simultáneamente:

- la FAQ humana visible;
- `WebPage`;
- `DefinedTermSet`;
- el glosario visible.

B.9 no mezcla ese fix y no debe volver a añadir FAQ schema como parte del glosario.

## Arquitectura canónica

La autoridad debe seguir siendo `/universo/noveris/`.

Si se añade un término nuevo:

1. validar que es canon público y no spoiler no autorizado;
2. añadirlo al contenido visible cuando aporte valor;
3. mantener paridad razonable con `DefinedTermSet` si forma parte del glosario formal;
4. actualizar `llms-full.txt` solo si el término merece formar parte del perfil machine-readable ampliado;
5. no duplicar el término en una segunda fuente de verdad.

No todos los nombres del manuscrito necesitan ser públicos ni estar en structured data.

## Qué no hacer

- crear `/glosario-noveris/` paralelo sin intención distinta;
- crear un JSON “para LLMs” con otro canon;
- publicar spoilers o lore provisional;
- llenar `sameAs` con entidades aproximadas;
- añadir términos solo por cantidad;
- presentar `DefinedTermSet` como rich result soportado por Google;
- reintroducir `FAQPage` para términos que ya tienen definición visible.

## Definition of Done

- [x] página real inspeccionada;
- [x] glosario humano visible confirmado;
- [x] `DefinedTermSet`/`hasDefinedTerm` confirmado;
- [x] semántica Schema.org revalidada;
- [x] autoridad `/universo/noveris/` preservada;
- [x] relación con B.4 documentada;
- [x] `FAQPage` derivado a su owner A.7 y no mezclado en esta PR;
- [x] no se crea glosario paralelo;
- [ ] revisión de Claude antes de merge.

**Estado final:** `ALREADY_COVERED · PRESERVE_CANONICAL_GLOSSARY · NO_PARALLEL_GLOSSARY`.
