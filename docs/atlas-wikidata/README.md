# P5b · Wikidata por lotes seguros y compatibles con cambio de motor (21/10/2026)

**Responsabilidad ÚNICA de esta PR:** construir consultas P840/P915/P551 validadas desde IDs Q seleccionados del atlas. No conecta a ningún servicio, no ejecuta SPARQL, no descarga registros, no interpreta resultados como hechos confirmados.

## Un cambio de plataforma verificado que afectará a nuestro diseño

Wikimedia está migrando el backend del [Wikidata Query Service](https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/WDQS_backend_update/Migrate) desde Blazegraph a QLever. La documentación vigente **21/10/2026** advierte que los endpoints `query-next.wikidata.org` pueden responder **Unauthorized User-Agent** hasta el lanzamiento público; v1 y v2 coexistirán al menos hasta **febrero de 2027**. **No sustituir ahora a ciegas `query.wikidata.org` por `query-next.wikidata.org`.** Hay [alternativas](https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/Alternative_endpoints) como `qlever.dev/wikidata`, que pueden diferir en versión de datos, semántica, acceso y límites; no garantizan servicio indefinido.

La [política actual de WDQS](https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual) exige identificarse con un User-Agent descriptivo, limita el tiempo a 60 segundos por consulta, CPU 60 s/min por usuario+IP, hasta 5 consultas paralelas y devuelve 429 con Retry-After. **Nunca hacer una consulta por cada usuario o ficha** ni lanzar escaneos globales sin control de límites y permiso.

## Código ya preparado

- [scripts/atlas_wikidata_batch_queries.py](../../scripts/atlas_wikidata_batch_queries.py): librería Python **stdlib**, recibe QIDs verificados y emite consultas SPARQL `.rq` con `VALUES` y manifiestos de lote sha256. Tres tipos diferenciados:
  - `narrative` → `wdt:P840` — **location of narrative** de una **obra**, nunca prueba de una escena callejera.
  - `filming` → `wdt:P915` — **filming location** de una **adaptación** audiovisual, no conexión directa con texto novelístico.
  - `author_residence` → `wdt:P551` — **residence** de autor histórico, no `P19` birth place ni escenario del libro; considerar viviendas privadas y restricciones de publicación.
- 20 QIDs por lote por defecto, máximo 50; validación `^Q[1-9][0-9]*$` evita inyección de SPARQL, deduplicación, hash y salidas que nunca se sobrescriben.
- [tests/test_atlas_wikidata_batch_queries.py](../../tests/test_atlas_wikidata_batch_queries.py): siete pruebas sintéticas **ESCRITAS, NO EJECUTADAS**.
- Query estándar `VALUES`, `wdt:`, `OPTIONAL`, `P625`: no usa `SERVICE wikibase:label`, función específica Blazegraph que puede no comportarse igual en QLever. Etiquetas multilingües se resolverán en otra etapa desde metadatos de entidades/autoridades.

## Muestra de consulta generable, solo ejemplo

```sparql
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT DISTINCT ?subject ?place ?coordinate WHERE {
  VALUES ?subject { wd:Q123 wd:Q456 }
  ?subject wdt:P840 ?place .
  OPTIONAL { ?place wdt:P625 ?coordinate . }
}
LIMIT 10000
```

```bash
# NO se ejecutó en esta PR.
python scripts/atlas_wikidata_batch_queries.py \
  --kind narrative --qids Q123 Q456 \
  --out-dir /datos/atlas/wikidata-candidate-queries
```

Los IDs Q123/Q456 son demostrativos, **no obras verificadas**. QIDs se seleccionan previamente por `works.wikidata_qid`, `adaptations.wikidata_qid` o `authors.wikidata_qid` del contrato #669 con consentimiento de publicación adecuado.

## Estado de la futura implementación del executor (NO construida en esta PR)

1. Cargar cola de lotes seleccionados y guardar `query_sha256`, `provider_release`, URL endpoint y `fetched_at`; enviar **solo** por solicitud explícita/worker offline con User-Agent, rate limit bajo y Retry-After para 429.
2. Versionar raw resultados externos fuera de Git, comparar QIDs y `?place` con GeoNames/Overture/OSM/Pleiades. El punto P625 se interpreta como **coordenada de la entidad del lugar**, no como lugar exacto de una escena.
3. Si se alcanza `LIMIT 10000`, marcar `potentially_truncated` y subdividir lotes o usar dump; nunca publicar un subconjunto como cobertura exhaustiva.
4. Enriquecer referencias de **statement** cuando existan (las tripletas `wdt:` no incluyen la fuente de cada afirmación). Guardar `source_ids`, `evidence_note` y *editorial review*; no promover vínculos P840/P915/P551 automáticamente.
5. Separar compatibilidad por proveedor v1/v2 con tests de 10 QIDs y misma semántica. Cuando cambie el servicio, actualizar endpoint en configuración, no reescribir toda la ingesta.
6. Nunca incluir vida privada actual de autores ni direcciones de residencias privadas; publicar museos/casas públicas comprobadas.

**Dependencias:** [#667 fuentes mundiales](https://github.com/davidpd89/web-escritor/pull/667), [#669 contrato](https://github.com/davidpd89/web-escritor/pull/669), [#670 integración](https://github.com/davidpd89/web-escritor/pull/670). **Estado draft**; sin HTTP, tests, Actions, merge ni despliegue.
