# A.2 · Página pilar por universo narrativo

Fecha de reconstrucción: 2026-08-29  
Idea original: crear una página central de referencia para Samuel y otra para Las manecillas del recuerdo que agregue y enlace todo el contenido disperso.  
Fuente histórica principal: PR #135, snapshot conservado en `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado de esta PR: documentación y decisión; no crea URLs ni modifica runtime.

## Veredicto reconciliado

**ALREADY_COVERED / MEJORAR LOS HUBS EXISTENTES, NO CREAR OTROS.**

La necesidad legítima —que cada obra/universo tenga un punto canónico desde el que el lector pueda entender la obra y seguir hacia fragmentos, universo, prensa y contenido relacionado— ya está implementada. Crear ahora nuevas páginas “pilar” paralelas duplicaría intención, enlaces y autoridad de URLs que ya funcionan como hubs.

Esta es también la decisión final histórica de #135. La investigación pasó por `PARTIAL_AUDIT` y por una formulación intermedia `YA_CUBIERTO/PILOTAR`, pero la inspección profunda del repositorio resolvió la duda: Samuel, Manecillas y Noveris ya tienen superficies canónicas que cumplen la función legítima de hub.

## 1. Regla de reconstrucción de #135

Esta PR no depende de la condensación posterior de #148 para reconstruir A.2. Usa directamente el snapshot histórico de #135 `8e72321...`.

Se conserva:

- cada hallazgo único relativo a A.2;
- todos los cambios de estado relevantes;
- contradicciones o formulaciones intermedias;
- fuentes primarias que afectaron la decisión;
- evidencia concreta del repo;
- decisión humana y machine-readable final;
- revalidación independiente;
- planes/tests útiles que sobreviven al descarte de nuevas páginas.

Las pasadas posteriores que no aportaron un cambio específico de A.2 se registran como revisadas, sin copiar contenido ajeno a esta idea.

## 2. Hipótesis original de #135

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` proponía:

> crear una página “pilar” central para Samuel entre mundos y otra para Las manecillas del recuerdo que agregase y enlazase el contenido disperso de Cuaderno, recomendaciones y club de lectura.

Era una hipótesis, no una tarea aprobada. El propio banco original advertía que cada idea debía contrastarse con el repo, coste, mantenimiento, dependencias y fuentes actuales.

La intuición válida era clara: evitar que el ecosistema de una obra quede repartido sin una ruta central útil. La parte pendiente de demostrar era si esa ruta central faltaba realmente.

## 3. Evolución cronológica de la decisión en #135

### 3.1 · Primera revisión 108/108 → `PARTIAL_AUDIT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` no autorizó nuevas páginas. Clasificó A.2 como `PARTIAL_AUDIT` porque ya veía fichas/hubs fuertes de Samuel, Noveris y Manecillas.

Acción propuesta entonces:

- hacer mapa de contenidos por obra;
- comprobar qué piezas estaban realmente dispersas;
- reforzar las URLs existentes antes de inventar otra “página pilar”.

Este fue el primer giro: el problema dejó de ser “construir dos hubs” y pasó a ser “comprobar si los hubs actuales ya resuelven la tarea”.

### 3.2 · Fuentes primarias → la arquitectura debe responder a una necesidad, no a una receta

`docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` fijó como referencias relevantes:

- Google · helpful/people-first content;
- Google · link best practices;
- Google · spam policies;
- Google · AI optimization guide, para no convertir una estructura editorial en supuesto hack GEO/AEO.

Lectura aplicable de #135:

- las páginas importantes deben ser descubribles mediante enlaces HTML rastreables;
- los enlaces y anchors ayudan a entender relaciones;
- no existe una obligación oficial de “pillar page por entidad”;
- no crear URLs redundantes para cubrir una fórmula SEO/IA.

### 3.3 · Cross-check del repositorio → `ALREADY_COVERED`

`docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` encontró las superficies canónicas que resolvían la hipótesis:

- `/libros/samuel-entre-mundos/`;
- `/las-manecillas-del-recuerdo/`;
- `/universo/noveris/`;
- colecciones del Cuaderno.

Conclusión histórica:

> `ALREADY_COVERED`. Enriquecer los hubs canónicos cuando haya contenido, no crear “páginas pilar” duplicadas.

### 3.4 · Override por inspección profunda → prevalece `ALREADY_COVERED`

`docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` formalizó el override porque la inspección del repo tenía más peso que la hipótesis inicial.

Evidencia específica de A.2:

- `/libros/samuel-entre-mundos/` ya es hub canónico de Samuel;
- `/las-manecillas-del-recuerdo/` ya es hub canónico de Manecillas;
- navegación, fragmentos y universo ya se relacionan con esas rutas;
- para Noveris la autoridad es `/universo/noveris/`;
- crear un “hub definitivo” nuevo duplicaría intención y autoridad.

Instrucción histórica para Claude:

> enriquecer los hubs existentes cuando haya material nuevo; no crear otra página pilar por etiqueta SEO.

### 3.5 · Matriz intermedia → `YA_CUBIERTO/PILOTAR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` dejó una formulación intermedia:

> `YA_CUBIERTO/PILOTAR`: ya existen hubs de obra/universo y arquitectura editorial. Auditar qué contenido disperso carece de ruta central antes de crear otra URL.

No contradice el hallazgo del repo en cuanto a construcción: no autorizaba nuevos hubs. El término `PILOTAR` se refería a auditar rutas/relaciones.

La autoridad final posterior simplificó correctamente el estado a `ALREADY_COVERED`.

### 3.6 · Blueprints netos → A.2 no entra como nueva construcción

`docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` contiene solo trabajo neto después de contrastar las ideas con el repo. A.2 no recibe un builder ni una nueva familia de URLs.

Eso confirma:

```text
hub canónico = existente
nueva página pilar = no autorizada
auditoría de relaciones = posible
corrección de gaps reales = posible
```

### 3.7 · Autoridad machine-readable final → `ALREADY_COVERED`

`data/web-improvement-decisions-2026-08-28.json` fija:

```json
{"id":"A.2","area":"seo","status":"ALREADY_COVERED"}
```

Y define la semántica decisiva:

> `ALREADY_COVERED` significa mejorar la autoridad existente, nunca duplicarla.

### 3.8 · Autoridad humana final → `ALREADY_COVERED`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` consolida A.2:

> ya hay hubs de obra/universo. Solo ampliar cuando una auditoría muestre contenido sin ruta central útil.

### 3.9 · Revalidación independiente → la decisión sobrevive al intento de falsación

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` revisó de nuevo A.1–A.12 contra repo y fuentes actuales. No modificó A.2. Las correcciones materiales de esa revalidación afectaron a otros IDs.

Por tanto el cierre histórico de A.2 siguió siendo `ALREADY_COVERED`.

## 4. Fuentes primarias que sostienen la decisión

1. Google Search Central · Creating helpful, reliable, people-first content  
   https://developers.google.com/search/docs/fundamentals/creating-helpful-content

2. Google Search Central · Link best practices  
   https://developers.google.com/search/docs/crawling-indexing/links-crawlable

3. Google Search spam policies  
   https://developers.google.com/search/docs/essentials/spam-policies

4. Google · AI optimization guide  
   https://developers.google.com/search/docs/fundamentals/ai-optimization-guide

Aplicación a A.2:

- propósito claro y utilidad humana antes que plantilla SEO;
- enlaces internos rastreables y contextuales;
- no existe un número mágico de hubs/satélites;
- evitar superficies duplicadas/thin creadas para capturar variaciones de intención;
- no hay una arquitectura especial obligatoria para citación IA.

## 5. Evidencia del repo conservada por esta PR

### Samuel

`/libros/samuel-entre-mundos/` ya es la URL canónica de la obra y contiene:

- canonical propio;
- `WebPage` + `Book` con `@id` estable;
- `BreadcrumbList` Inicio → Libros → Samuel;
- section-context con la propia obra y rutas relacionadas;
- enlaces a Noveris, fragmento, compra, editorial y recursos del ecosistema.

Crear `/universos/samuel/`, `/samuel/` o una segunda página pilar sería duplicar una entidad que ya tiene URL de referencia.

### Las manecillas del recuerdo

`/las-manecillas-del-recuerdo/` ya funciona como hub:

- canonical;
- `WebPage` + `Book` con `@id`;
- `BreadcrumbList` Inicio → Libros → Manecillas;
- section-context con La novela, Fragmentos y Ficha de prensa;
- metadatos editoriales y relación con su muestra.

### Noveris

`/universo/noveris/` es la superficie canónica del universo/ciudad ficticia de Samuel. #135 fue explícita: no crear otro “hub definitivo” que compita con Samuel + Noveris.

### Hub de obras

`/libros/` ya agrupa el catálogo. La navegación contextual y `data/content-registry.json` permiten relacionar las piezas.

## 6. Qué sí sobrevivió de la idea original

No una URL nueva, sino una auditoría de completitud de los hubs actuales.

Un hub debe poder responder, cuando el contenido exista realmente:

1. qué es la obra;
2. estado editorial verificable;
3. cómo leer una muestra;
4. dónde comprar cuando exista URL real;
5. qué contenido propio amplía obra/universo;
6. qué recursos de prensa/eventos existen;
7. cómo volver al catálogo.

No todos los hubs necesitan todas las secciones. La regla es resolver tareas reales, no completar una plantilla.

## 7. Plan correcto si aparece un gap

### Fase 1 · inventario derivado

Usar `data/content-registry.json` y relaciones ya existentes (`parentId`, `hubId` y relaciones canónicas disponibles). No crear otro inventario de “hubs”.

Salida orientativa, derivada y read-only:

```json
{
  "entity": "samuel",
  "canonicalHub": "/libros/samuel-entre-mundos/",
  "related": [
    "/fragmento/",
    "/universo/noveris/",
    "/clubes-de-lectura/samuel-entre-mundos/"
  ]
}
```

### Fase 2 · auditoría humana

Para cada relación:

- ¿el enlace ayuda al lector en ese contexto?;
- ¿el anchor explica el destino?;
- ¿hay una URL más canónica?;
- ¿la relación es factual/editorial o solo SEO?;
- ¿la pieza realmente necesita ruta de vuelta al hub?

### Fase 3 · corregir solo gaps demostrados

Ejemplos legítimos:

- pieza del Cuaderno sobre Samuel sin enlace de vuelta cuando sería útil;
- ficha sin enlace a un fragmento ya existente;
- recurso de prensa real escondido de navegación contextual.

## 8. Integración técnica si hubiera consumidor real

Preferir ampliar `scripts/check-internal-graph.py` antes que crear otro framework.

Interfaz orientativa:

```bash
python scripts/check-internal-graph.py --entity samuel --report
```

Salida posible:

```text
ENTITY samuel
hub: /libros/samuel-entre-mundos/
related registered: 7
related with path to hub: 7
hub outbound to related: 5
informational gaps: 2
```

Los gaps informativos no deben fallar CI salvo que el registry declare una relación contractual concreta.

## 9. Relación con A.1 y A.3

- A.1 trata colecciones temáticas/editoriales (`topic-collections`), no la URL canónica de una obra.
- A.2 trata el hub canónico de Samuel, Manecillas o Noveris.
- A.3 trata el grafo de enlaces/huérfanas y puede aportar evidencia a A.2.

No resolver A.2 creando otra colección de A.1 ni otro crawler de A.3.

## 10. Tests

- cada hub canónico declarado existe y es indexable;
- una entidad no recibe dos hubs canónicos incompatibles;
- IDs relacionados existen;
- cualquier relación marcada como obligatoria tiene enlace real;
- `check-internal-graph.py` sigue sin broken links/canonical collisions;
- `check-global-discoverability.py` y sitemap/registry siguen sincronizados;
- no aparece una nueva URL pilar sin trigger editorial explícito.

## 11. Qué NO hacer

- crear un segundo hub de Samuel porque una herramienta SEO sugiera “pillar page”;
- duplicar sinopsis para generar superficie indexable;
- crear “universo de Manecillas” sin una necesidad editorial real;
- convertir un hub en un índice de enlaces sin contenido propio;
- producir páginas por personaje/trope para completar un cluster;
- mantener manualmente un segundo mapa de relaciones;
- interpretar `ALREADY_COVERED` como permiso para rehacer el sistema.

## 12. Coste / beneficio

Auditar hubs existentes: beneficio medio/alto, coste bajo/medio.  
Crear dos páginas nuevas: beneficio negativo en el estado actual por duplicación/canibalización potencial.  
Extender un checker existente ante un consumidor real: coste bajo y riesgo controlado.

## 13. Definition of Done de A.2

### Ya demostrado por #135

- [x] hipótesis original recuperada;
- [x] primera revisión `PARTIAL_AUDIT` preservada;
- [x] repo cross-check localizó hubs reales;
- [x] override profundo cambió/afianzó `ALREADY_COVERED`;
- [x] matriz intermedia `YA_CUBIERTO/PILOTAR` preservada como historia;
- [x] ausencia de nueva construcción en blueprints netos registrada;
- [x] autoridad JSON final = `ALREADY_COVERED`;
- [x] autoridad humana final = `ALREADY_COVERED`;
- [x] revalidación independiente no reabrió la idea;
- [x] se conservan las URLs canónicas y el criterio de no duplicación.

### Solo si aparece nueva evidencia

- [ ] inventariar relaciones desde autoridades existentes;
- [ ] identificar gap concreto y tarea humana afectada;
- [ ] corregir solo enlaces/rutas que falten;
- [ ] mantener una sola URL canónica por entidad/obra;
- [ ] no crear nueva página pilar salvo necesidad editorial distinta y demostrada;
- [ ] suites de internal graph/discoverability verdes.

## 14. Trazabilidad del corpus histórico de #135 revisado para A.2

### Contienen evidencia o decisión específica

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `PARTIAL_AUDIT` inicial.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — metodología/fuentes.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — hubs encontrados; cambio a `ALREADY_COVERED`.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` — override profundo e instrucción de no duplicar.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — estado histórico `YA_CUBIERTO/PILOTAR`.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — A.2 queda fuera de nueva construcción neta.
- `data/web-improvement-decisions-2026-08-28.json` — autoridad machine-readable final.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana final.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — falsación independiente; decisión mantenida.

### Revisados sin cambio específico adicional para A.2

Se revisaron también cuarta y quinta pasada, sexta pasada y revisión crítica, séptima a decimoquinta pasada, casos/evidencia/límites, fuentes adicionales, repos evaluados y policy watch del snapshot de #135. Añadieron hallazgos para otros IDs pero no una modificación única de A.2; por eso se registran y no se copia contenido ajeno.

## 15. Recomendación de merge

**MERGE como reconstrucción completa + `ALREADY_COVERED`.**

A.2 queda cerrada así:

```text
NO crear nuevas páginas pilar para Samuel/Manecillas por fórmula SEO.
SÍ conservar Samuel, Manecillas y Noveris como hubs canónicos actuales.
SÍ auditar relaciones si aparece contenido sin ruta central útil.
NO crear una segunda fuente de verdad.
SÍ extender navegación/grafo existente solo ante un gap demostrado.
```