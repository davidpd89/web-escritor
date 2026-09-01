# B.4 · Revalidación de producción · 2026-08-29

## Veredicto

**READY_NO_CODE · ALREADY_COVERED_STRONGLY · EXTEND_EXISTING_AUTHORITY**

B.4 no presenta un hueco actual. El repo tiene ya una autoridad técnica explícita para IDs canónicos y otra para `sameAs`/Wikidata, ambas creadas a partir de errores reales y más fuertes que un nuevo inventario documental.

## Base inspeccionada

- `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`;
- `scripts/check-canonical-entity-ids.py`;
- `scripts/check-wikidata-sameas.py`;
- contrato machine-readable existente;
- fichas de obras inspeccionadas durante A.7/A.12;
- documentación oficial vigente de Google Search Central.

## Owner 1 · IDs canónicos

`scripts/check-canonical-entity-ids.py` recorre JSON-LD público y vigila entidades `Book`, `Person` y `Organization`.

Tiene dos niveles de protección:

1. **consistencia por nombre**: falla si una misma entidad nominal aparece con varios `@id`;
2. **anclaje explícito**: fija los IDs esperados para que un cambio masivo coherente pero erróneo no pueda pasar.

IDs anclados actualmente:

```text
David Porto Díaz
→ https://davidportodiaz.com/#author

Las manecillas del recuerdo
→ https://davidportodiaz.com/#book-manecillas

Samuel entre mundos
→ https://davidportodiaz.com/#book-samuel
```

El segundo nivel es especialmente importante: evita que una sustitución global cambie todos los usos al mismo ID equivocado y pase una mera prueba de igualdad.

## Owner 2 · Wikidata / sameAs

`scripts/check-wikidata-sameas.py` nació de incidentes reales en los que QIDs correctos sintácticamente representaban entidades completamente equivocadas.

El checker mantiene:

- `KNOWN_GOOD` verificado;
- `KNOWN_BAD` para impedir reintroducciones;
- fallo ante QIDs nuevos no revisados;
- modo `--live` para contrastar labels/descripciones con Wikidata;
- trazabilidad a archivo/línea.

Esto evita tratar `sameAs` como una colección estética de URLs.

## Estado actual

No se detecta una nueva entidad propia que requiera:

- nuevo ID global;
- nuevo QID;
- nuevo checker;
- inventario de knowledge graph paralelo.

Las modificaciones de A.7/A.12 sobre Samuel preservan el mismo `Book @id`; retiraron únicamente markup no relacionado (`FAQPage` / reviews de terceros) en sus ramas propietarias.

## Revalidación Google 2026

Google mantiene dos principios relevantes:

1. structured data debe representar fielmente el contenido visible y cumplir las políticas del tipo correspondiente;
2. para las funciones generativas de Search no existe un schema especial y no es necesario sobrecargar structured data para “IA”.

Fuentes:

- `https://developers.google.com/search/docs/appearance/structured-data/sd-policies`;
- `https://developers.google.com/search/docs/fundamentals/ai-optimization-guide`;
- `https://developers.google.com/search/docs/appearance/ai-features`.

Por tanto, la calidad del grafo se mide por **identidad correcta, estabilidad y paridad**, no por número de propiedades o enlaces.

## Decisión de arquitectura

No crear un segundo grafo machine-readable.

Si aparece una entidad propia nueva:

1. definirla en su superficie/autoridad natural;
2. asignar un `@id` estable solo si necesita identidad compartida;
3. extender `EXPECTED_IDS` cuando proceda;
4. verificar cualquier `sameAs` externo antes de incluirlo;
5. extender el checker/fixtures existentes;
6. mantener paridad con contenido humano y press-kit.

## Guardrails

No:

- inventar VIAF/ISNI;
- usar artículos de prensa como `sameAs`;
- cambiar IDs por estética/ruta de la página;
- crear IDs distintos para una misma obra según superficie;
- añadir Organizations sintéticas;
- medir “completitud” por cantidad de schema;
- afirmar que más propiedades aumentan ranking/citas IA.

## Triggers de reapertura

1. nueva obra/entidad propia con uso cross-page;
2. divergencia real de `@id` detectada por CI;
3. nuevo identificador externo verificado;
4. cambio de press-kit/autoridad que deje el grafo desalineado;
5. carencia concreta del checker actual.

## Definition of Done

- [x] historial de B.4 preservado;
- [x] checker de IDs inspeccionado;
- [x] IDs anclados confirmados;
- [x] checker Wikidata inspeccionado;
- [x] allowlist/denylist verificadas como owner existente;
- [x] Google 2026 revalidado;
- [x] no se detecta entidad nueva ni drift;
- [x] decisión `ALREADY_COVERED_STRONGLY`;
- [ ] CI del HEAD final completamente verde;
- [ ] revisión de Claude antes de merge.

## Cierre

B.4 está cubierta de forma fuerte. Cualquier mejora futura debe ampliar los checkers y autoridades actuales ante una entidad o regresión real, no construir un segundo knowledge graph.