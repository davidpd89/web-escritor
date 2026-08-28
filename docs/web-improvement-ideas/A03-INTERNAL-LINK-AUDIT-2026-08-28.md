# A.3 · Auditoría automatizada de enlazado interno

Fecha de reconstrucción: 2026-08-29  
Idea original: crear un script que detecte artículos del Cuaderno sin enlaces entrantes para evitar contenido aislado.  
Fuente histórica principal: PR #135, snapshot conservado en `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado de esta PR: documentación y decisión; no crea un crawler nuevo ni modifica runtime.

## Veredicto reconciliado

**ALREADY_COVERED STRONGLY. NO construir otro auditor.**

La investigación de #135 empezó considerando A.3 una implementación nueva y llegó a clasificarla como `IMPLEMENT_AFTER_CURRENT_DEBT` / `IMPLEMENTAR`. La inspección profunda del repositorio descubrió después que la capacidad central ya existía en `scripts/check-internal-graph.py`. Esa evidencia prevaleció y el estado final histórico pasó a `ALREADY_COVERED`.

La mejora futura, si existe un consumidor real, debe extender ese checker. No se autoriza otro crawler, otra fuente de verdad del grafo ni cuotas arbitrarias de enlaces.

## 1. Regla de reconstrucción de #135

Esta PR reconstruye A.3 desde el snapshot histórico `8e72321...`, no desde la condensación de #148.

Se preservan todos los hallazgos únicos de A.3, incluidos los estados intermedios que quedaron superados, porque explican por qué una tarea inicialmente aprobada dejó de ser una implementación nueva.

## 2. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` proponía crear un script que detectara artículos de `cuaderno/` sin enlaces entrantes para no dejar contenido aislado del grafo interno.

La necesidad era legítima: páginas importantes deben poder descubrirse mediante enlaces internos rastreables. La incógnita era si el proyecto ya tenía esa capacidad.

## 3. Evolución cronológica de la decisión en #135

### 3.1 · Primera revisión → `IMPLEMENT_AFTER_CURRENT_DEBT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` aprobó inicialmente la idea como trabajo futuro de alto valor:

> crear un checker del grafo interno; cada URL indexable/importante debe recibir enlaces HTML rastreables. Fuente de verdad: registry + sitemap + HTML.

En ese momento la revisión todavía no había localizado la implementación existente.

### 3.2 · Fuente primaria → la razón para detectar huérfanas sí es válida

Google Search Central · Link best practices  
https://developers.google.com/search/docs/crawling-indexing/links-crawlable

Lectura de #135:

- las páginas importantes deben tener enlaces desde otras páginas;
- anchors descriptivos ayudan a usuarios y buscadores;
- no existe un número ideal/mágico de enlaces por página.

Por tanto:

```text
detectar 0 inbound = problema objetivo
imponer 3/5/N inbounds = no sustentado
```

### 3.3 · Matriz intermedia → `IMPLEMENTAR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` todavía la trató como construcción:

> auditor de enlaces entrantes/huérfanos desde artefacto público + registry; reportar profundidad, inlinks y páginas sin ruta editorial; gate solo para huérfanos no intencionales.

Este estado quedó históricamente superado por el cross-check del repo.

### 3.4 · Repo cross-check → se descubre `check-internal-graph.py`

`docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` encontró que `scripts/check-internal-graph.py` ya:

- detecta targets internos ausentes;
- detecta páginas indexables huérfanas;
- valida canonicals y colisiones;
- genera reporte de inbound links;
- ignora correctamente feeds/assets/noindex.

**Decisión:** `ALREADY_COVERED`.

### 3.5 · Override por inspección profunda → la construcción nueva queda prohibida

`docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` formalizó el hallazgo y fijó la instrucción para Claude:

> no crear un segundo crawler de enlaces.

También dejó dos extensiones futuras concretas, solo si aportan valor:

1. distinguir `global-nav` vs `contextual`;
2. convertir ciertos warnings de rutas `discoverabilityRequired` en error, con fixture/test.

Estas extensiones son parte de la investigación de #135 y deben conservarse; son más específicas que una propuesta genérica de “otro auditor”.

### 3.6 · Blueprints netos → A.3 desaparece de la cola de construcción

`docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` declara que las capacidades ya existentes —incluido el grafo interno— no aparecen como trabajo que haya que construir.

La ausencia de A.3 del backlog neto es evidencia deliberada, no un olvido.

### 3.7 · Autoridad machine-readable final → `ALREADY_COVERED`

`data/web-improvement-decisions-2026-08-28.json` fija:

```json
{"id":"A.3","area":"seo","status":"ALREADY_COVERED"}
```

Y la policy define:

> `ALREADY_COVERED` significa mejorar la autoridad existente, nunca duplicarla.

### 3.8 · Autoridad humana final → mantener/extender el contrato existente

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` consolida:

> `scripts/check-internal-graph.py` ya cubre grafo/huérfanos. Mantener y extender ese contrato, no crear otro auditor.

### 3.9 · Revalidación independiente → decisión mantenida

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` intentó falsar las 108 decisiones. A.3 no cambió.

Por tanto, la secuencia histórica completa es:

```text
hipótesis de script nuevo
→ IMPLEMENT_AFTER_CURRENT_DEBT
→ IMPLEMENTAR en matriz intermedia
→ repo descubre checker existente
→ ALREADY_COVERED final
```

## 4. Estado real de la capacidad encontrada por #135

`scripts/check-internal-graph.py` ya cubre:

- broken internal page links;
- orphan indexable pages;
- missing canonicals;
- canonical collisions;
- exclusiones de assets, feeds, legal/utilities y noindex;
- `--report` con `INBOUND COUNTS (indexable)`.

La implementación recorre HTML, extrae `<a href>`, resuelve URLs relativas/canónicas y construye el conjunto de enlaces entrantes.

Una release audit histórica registró, en aquel HEAD, 59 páginas indexables con:

- 0 enlaces internos rotos;
- 0 huérfanas;
- 0 colisiones canónicas.

Ese resultado histórico prueba la capacidad del checker en aquel corte; no debe presentarse como garantía eterna del `main` futuro.

## 5. Mejoras que #135 deja abiertas sin convertirlas en obligación

### 5.1 · `global-nav` vs `contextual`

Un enlace desde navegación global no expresa la misma relación editorial que un enlace contextual. Si existe una pregunta real sobre calidad del grafo, el checker actual podría clasificar la procedencia.

No convertir esa distinción en error CI sin una regla contractual concreta.

### 5.2 · `discoverabilityRequired`

Si el registry ya declara que una ruta debe ser descubrible desde una familia/hub específico, un warning podría convertirse en error con fixture/test.

El requisito debe proceder de una autoridad existente, no inventarse dentro del checker.

### 5.3 · Salida JSON opcional

Para Claude/CI puede ser útil una salida machine-readable si existe consumidor:

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

Debe salir del mismo grafo interno, no de un segundo cálculo.

### 5.4 · Vista por familia

Si un consumidor la necesita:

```bash
python scripts/check-internal-graph.py --family cuaderno --report
```

La familia debe derivarse de `content-registry.json` o autoridad equivalente, no de heurísticas nuevas.

### 5.5 · Huérfana vs débilmente enlazada

- 0 inbound puede ser error objetivo para una URL pública/importante.
- inbound bajo puede reportarse, pero no debe ser un error genérico.

Una página específica puede necesitar pocos enlaces; un hub, muchos. No crear un score SEO casero.

## 6. Código orientativo preservado

Extensión mínima posible:

```python
ap.add_argument("--json", help="write machine-readable graph report")

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

## 7. Tests

Capacidad base:

- fixture con página indexable sin inbound → orphan;
- enlace roto → error;
- canonical duplicado → error;
- noindex/legal/feeds no generan falso orphan;
- Required merge gate conserva el contrato.

Si se añade JSON:

- salida humana y JSON proceden del mismo grafo;
- mismo exit code/semántica;
- schema estable si existe consumidor.

Si se añade `global-nav/contextual` o `discoverabilityRequired`:

- fixtures positivos/negativos explícitos;
- no convertir navegación global en fallo por intuición;
- no introducir una segunda fuente de verdad de relaciones.

## 8. Qué NO hacer

- nuevo crawler JS separado;
- nuevo `data/internal-links.json` editable a mano;
- imponer mínimo 3/5/N enlaces internos por página;
- auto-insertar enlaces por keyword;
- links ocultos para elevar inbound count;
- usar Ahrefs/Semrush/DA como autoridad del grafo interno;
- alterar anchors útiles solo por keywords;
- reimplementar canonicals dentro de otro checker.

## 9. Coste / beneficio

Capacidad base: ya implementada y de alto valor.  
Salida JSON: bajo coste / valor medio si existe consumidor.  
Clasificación contextual: valor potencial, pero solo ante pregunta editorial real.  
Segundo auditor paralelo: valor negativo por drift y contradicciones.

## 10. Definition of Done de A.3

### Ya demostrado por #135

- [x] hipótesis original recuperada;
- [x] `IMPLEMENT_AFTER_CURRENT_DEBT` inicial preservado;
- [x] `IMPLEMENTAR` de la matriz preservado como estado superseded;
- [x] `check-internal-graph.py` localizado;
- [x] capacidades concretas del checker documentadas;
- [x] override profundo `ALREADY_COVERED` preservado;
- [x] extensiones `global-nav/contextual` y `discoverabilityRequired` conservadas;
- [x] ausencia de A.3 en blueprints netos explicada;
- [x] autoridad JSON final = `ALREADY_COVERED`;
- [x] autoridad humana final = `ALREADY_COVERED`;
- [x] revalidación independiente mantuvo la decisión.

### Solo si aparece un consumidor/gap

- [ ] ejecutar baseline del checker actual;
- [ ] describir la pregunta que el output actual no responde;
- [ ] extender el checker existente, no crear otro;
- [ ] añadir fixture/test del nuevo contrato;
- [ ] no convertir inlinks bajos en score/ranking proxy;
- [ ] no crear nueva fuente de verdad.

## 11. Trazabilidad del corpus histórico de #135 revisado para A.3

### Contienen evidencia o decisión específica

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `IMPLEMENT_AFTER_CURRENT_DEBT` inicial.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — enlaces rastreables y ausencia de cuota mágica.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `IMPLEMENTAR` histórico.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — descubrimiento del checker existente.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` — override y extensiones concretas.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — grafo interno excluido expresamente del backlog de nueva construcción.
- `data/web-improvement-decisions-2026-08-28.json` — autoridad machine-readable final.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana final.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — falsación independiente, sin cambio de A.3.

### Revisados sin cambio específico adicional

Se revisaron también cuarta y quinta pasada, sexta y revisión crítica, séptima a decimoquinta pasada, casos/evidencia/límites, fuentes adicionales, repos evaluados y policy watch. No añadieron un hallazgo único que alterase A.3.

## 12. Recomendación de merge

**MERGE como reconstrucción completa + `ALREADY_COVERED`.**

```text
NO construir otro auditor.
SÍ mantener scripts/check-internal-graph.py como autoridad.
SÍ extenderlo si aparece un gap reproducible o consumidor real.
NO imponer cuotas de enlaces ni scores SEO caseros.
SÍ conservar fixtures, canonicals, huérfanas y discoverability como contratos medibles.
```