# A.3 · Auditoría automatizada de enlazado interno

Fecha de revisión: 2026-08-28
Idea original: crear un script que detecte artículos del Cuaderno sin enlaces entrantes para evitar contenido aislado.

## Veredicto

**ALREADY_COVERED STRONGLY. NO construir otro auditor.**

La capacidad central de la idea ya existe en `scripts/check-internal-graph.py`: analiza HTML indexable, construye el grafo interno y reporta enlaces rotos, páginas huérfanas, canonicals ausentes y colisiones canónicas. Además dispone de `--report` para mostrar conteos inbound.

La mejora razonable es, como máximo, hacer su salida más consumible por máquinas/Claude o añadir vistas por familia; no crear otro script que calcule lo mismo con reglas diferentes.

## Fuente primaria

Google Search Central · Link best practices
https://developers.google.com/search/docs/crawling-indexing/links-crawlable

Google recomienda que toda página importante tenga al menos un enlace desde otra página del sitio y que el anchor text sea descriptivo. También aclara que no existe un número ideal de enlaces por página. Eso justifica detectar huérfanas; no justifica imponer cuotas arbitrarias de enlaces.

## Estado real del repo

`scripts/check-internal-graph.py` declara literalmente que:

- reporta broken internal page links;
- detecta orphan indexable pages;
- detecta missing canonicals;
- detecta canonical collisions;
- excluye assets, feeds, legal/utilities y noindex de los errores de grafo;
- con `--report` imprime `INBOUND COUNTS (indexable)`.

La implementación actual recorre los HTML, extrae `<a href>`, resuelve relativos/canónicos y construye `incoming[target]`.

La release audit histórica #1 registró 59 páginas indexables con 0 enlaces internos rotos, 0 huérfanas y 0 colisiones canónicas en ese HEAD.

## Qué sí puede mejorarse

### 1. Salida JSON opcional

Hoy `--report` está orientado a consola. Para Claude/CI sería útil:

```bash
python scripts/check-internal-graph.py --report --json artifacts/internal-graph.json
```

Ejemplo:

```json
{
  "summary": {
    "indexablePages": 61,
    "broken": 0,
    "orphans": 0,
    "canonicalCollisions": 0
  },
  "pages": [
    {
      "url": "/cuaderno/que-es-el-portal-fantasy/",
      "inboundCount": 6,
      "outboundCount": 9,
      "inboundFrom": ["/cuaderno/", "/cuaderno/temas/fantasia-de-portales/"]
    }
  ]
}
```

### 2. Vista por familia

Sin cambiar el criterio de error, permitir filtros:

```bash
python scripts/check-internal-graph.py --family cuaderno --report
```

La familia debe derivarse de `content-registry.json`, no de heurísticas duplicadas.

### 3. Distinguir “huérfana” de “débilmente enlazada”

Solo “0 inbound” debe ser un problema objetivo. Un inbound count bajo puede aparecer en un informe, pero **no debe convertirse en error CI genérico**: una página muy específica puede necesitar pocos enlaces y una página hub muchos.

## Código propuesto

Extensión mínima:

```python
ap.add_argument("--json", help="write machine-readable graph report")

# después de construir pages/incoming
payload = {
    "summary": {...},
    "pages": [
        {
            "path": short(meta["path"], root),
            "canonical": meta["canonical"],
            "inboundCount": len(incoming.get(key, [])),
            "outboundCount": len(meta["links"]),
        }
        for key, meta in pages.items()
    ],
}
```

No modificar la lógica de resolución de enlaces salvo bug demostrado.

## Tests

- fixture con una página indexable sin inbound → warning `orphan`;
- fixture con enlace roto → error;
- fixture con canonical duplicado → error;
- noindex/legal/feeds no generan falso orphan;
- JSON y salida humana proceden del mismo grafo;
- el modo JSON no cambia exit code ni semántica existente;
- Required merge gate sigue ejecutando el contrato.

## Qué NO hacer

- nuevo crawler JS separado para volver a descubrir lo mismo;
- imponer “mínimo 3/5 enlaces internos por página”;
- auto-insertar enlaces por keyword;
- crear links ocultos para elevar inbound count;
- usar un score de Ahrefs/Semrush como fuente de verdad del grafo interno;
- modificar anchors solo para keywords si empeora lectura.

## Valor

Capacidad base: **ya implementada y de alto valor**.
Mejora JSON: **bajo coste / valor medio** para agentes y dashboards.
Otro auditor paralelo: **valor negativo**, introduce drift.

## Definition of Done

- [x] existe auditor de huérfanas/enlaces/canonicals;
- [x] existe informe inbound humano;
- [ ] opcional: JSON machine-readable si hay consumidor real;
- [ ] si se añade JSON, test de paridad humano/JSON;
- [ ] ninguna nueva fuente de verdad sobre URLs/familias;
- [ ] baseline actual ejecutado antes de cualquier cambio.

## Recomendación de merge

**MERGE como `ALREADY_COVERED`.** Si Claude necesita machine-readable output, abrir después una PR pequeña sobre el checker actual.