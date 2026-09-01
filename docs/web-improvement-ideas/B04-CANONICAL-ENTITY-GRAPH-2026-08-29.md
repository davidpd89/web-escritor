# B.4 · Entidad `Person`/`Author` completa y enlazada por `@id`

Fecha de reconstrucción: 2026-08-29  
Idea original: verificar que Article/Book/Person/Organization comparten entidades canónicas y `sameAs` reales.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado final: `ALREADY_COVERED`.

## Veredicto reconciliado

**ALREADY_COVERED. MANTENER LA AUTORIDAD EXISTENTE; NO CREAR UN SEGUNDO «GRAFO DE ENTIDADES».**

#135 empezó planteando una auditoría de `Person @id`, `author @id`, `sameAs` y vínculos de Book/Article. La inspección profunda encontró que el repo ya tiene checkers explícitos que fijan los IDs canónicos de David, Samuel y Manecillas y detectan divergencias. La idea dejó de ser una implementación nueva.

## 1. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` proponía comprobar un grafo tipo:

```text
Article → author @id → Person → sameAs
Book → author @id → Person
Person/Book → Organization cuando corresponda
```

Objetivo: evitar ambigüedad y mejorar resolución de entidad para buscadores/consumidores, sin inventar identificadores.

## 2. Evolución en #135

### Revisión exhaustiva → `PARTIAL_AUDIT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` consideró B.4 de alto valor: auditar `Person @id`, `sameAs`, `author @id` y paridad con press-kit. También dejó claro que no existe schema especial para IA.

### Matriz final → `IMPLEMENTAR/VERIFICAR`

La matriz intermedia mantuvo la auditoría, con una salvaguarda clave: **no inventar ISNI/VIAF** ni añadir identificadores por parecer «más completos».

### Repo cross-check profundo → `ALREADY_COVERED`

`docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` encontró:

- `scripts/check-canonical-entity-ids.py`;
- `scripts/check-jsonld-absolute-urls.py`;
- `scripts/check-wikidata-sameas.py`;
- IDs anclados para David/Manecillas/Samuel;
- press-kits y metadata factual existentes.

Decisión: no crear un grafo paralelo; extender el checker existente solo si aparece una nueva entidad propia o un fallo reproducible.

### Autoridad final → `ALREADY_COVERED`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` fijó:

> `check-canonical-entity-ids.py`, `check-wikidata-sameas.py`, press-kit y grafo existente cubren la base. Mantener paridad factual.

### Revalidación independiente

La falsación final mantuvo B.4 sin correcciones.

Secuencia:

```text
hipótesis: completar/conectar grafo
→ revisión: auditar, no schema especial IA
→ matriz: verificar IDs/sameAs, no inventar identificadores
→ inspección profunda: checkers ya existen
→ autoridad final: ALREADY_COVERED
→ revalidación: mantiene
```

## 3. Estado real de `main`

`scripts/check-canonical-entity-ids.py` documenta exactamente el problema que B.4 intentaba prevenir: si una misma obra usa dos `@id` absolutos distintos, un consumidor RDF las interpreta como entidades distintas y las señales dejan de acumularse correctamente.

El checker:

- recorre JSON-LD de HTML público;
- vigila `Book`, `Person`, `Organization`;
- agrupa por `name`;
- falla si un mismo nombre usa varios `@id`;
- ancla IDs canónicos esperados para evitar que un cambio masivo coherente pero erróneo pase desapercibido.

IDs fijados actualmente:

```text
David Porto Díaz → https://davidportodiaz.com/#author
Las manecillas del recuerdo → https://davidportodiaz.com/#book-manecillas
Samuel entre mundos → https://davidportodiaz.com/#book-samuel
```

Esto es más fuerte que una revisión visual ocasional.

## 4. Fuentes primarias y principio 2026

Google Search Central:

- Structured data general guidelines: https://developers.google.com/search/docs/appearance/structured-data/sd-policies
- AI features / website: https://developers.google.com/search/docs/appearance/ai-features
- AI optimization guide 2026: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

Google mantiene que structured data debe coincidir con el contenido visible y seguir las reglas de cada feature. Para las funciones generativas **no existe un schema especial adicional** ni hay que sobreoptimizar marcado para IA.

Schema.org sigue siendo vocabulario descriptivo; tener más propiedades no implica ranking.

## 5. Contrato de identidad canónica

### Autor

- un `@id` estable;
- nombre público coherente;
- `sameAs` solo a perfiles/identificadores reales y controlados/verificados;
- no inventar VIAF/ISNI;
- press-kit y `/ai/` deben contar los mismos hechos P0.

### Libros

- cada obra propia mantiene un `@id` único;
- Book en Home/listados/ficha debe referirse al mismo ID;
- ISBN/editorial/fecha no deben divergir entre JSON-LD y contenido visible;
- reseñas/premios no se deben reasignar a otra obra.

### Organization

Solo cuando exista una entidad real que corresponda; no crear organizaciones sintéticas para completar relaciones.

## 6. Relación con `sameAs`

`sameAs` no es una lista de «sitios donde aparece el nombre». Debe representar perfiles/entidades equivalentes y fiables.

#135 ya conserva identificadores reales como Wikidata/ORCID y perfiles bibliográficos/sociales seleccionados. Cada alta nueva debe verificar:

- URL real;
- identidad correcta;
- no colisión con homónimo;
- vigencia;
- pertinencia como equivalencia, no mera mención.

## 7. Qué hacer si aparece una nueva entidad

No crear otro archivo de autoridad. Extender:

1. la página/registry/press-kit correspondiente;
2. `EXPECTED_IDS` solo si la entidad propia necesita un ID anclado global;
3. fixtures/tests del checker;
4. `sameAs` checker si hay identificadores externos;
5. paridad con JSON-LD visible.

## 8. Qué NO hacer

- cambiar `@id` por estética;
- usar la URL de cada página como ID diferente para la misma persona/obra;
- inventar `sameAs`;
- enlazar menciones de prensa como `sameAs`;
- crear un «knowledge graph» JSON paralelo a registry/press-kit;
- añadir schema no visible;
- decir que structured data garantiza citas IA;
- optimizar cantidad de propiedades como KPI;
- duplicar `check-canonical-entity-ids.py`.

## 9. Tests/QA

Mantener:

- `check-canonical-entity-ids.py`;
- `check-jsonld-absolute-urls.py`;
- `check-wikidata-sameas.py`;
- validación JSON-LD;
- tests específicos cuando cambian IDs.

Un cambio de entidad propia debe fallar si introduce un nuevo ID divergente.

## 10. Definition of Done

- [x] hipótesis original preservada;
- [x] `PARTIAL_AUDIT` inicial preservado;
- [x] matriz `IMPLEMENTAR/VERIFICAR` preservada;
- [x] override profundo `ALREADY_COVERED` preservado;
- [x] checker real inspeccionado;
- [x] autoridad final preservada;
- [x] revalidación independiente preservada;
- [x] guardrail «no schema especial IA» preservado.

## 11. Trazabilidad #135

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md`;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md`;
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md`;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md`;
- `data/web-improvement-decisions-2026-08-28.json`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md`;
- `docs/ai-discoverability/03-ENTIDAD-AUTOR-LIBROS-Y-CONOCIMIENTO-CANONICO.md`.

Las restantes pasadas/fuentes fueron revisadas sin cambio posterior de estado.

## 12. Recomendación

**MERGE como reconstrucción completa + `ALREADY_COVERED`.** La mejora futura es extender el checker/autoridad existente ante entidades nuevas o regresiones, no construir otro grafo.