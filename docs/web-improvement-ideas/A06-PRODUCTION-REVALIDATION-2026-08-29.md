# A.6 · Revalidación e implementación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #155  
Decisión operativa: **IMPLEMENTED_IN_PR · AUDIT_GUARDRAIL · NO_SITEWIDE_ROLLOUT**

> Autoridad operativa: este documento y el código del HEAD actual describen la implementación final. `A06-BREADCRUMB-COVERAGE-2026-08-28.md` conserva la arqueología de #135 y su blueprint W4 histórico.

## Problema real confirmado

#135 acertó al no ordenar “añadir breadcrumbs a toda la web”. El repo actual tiene cuatro estados legítimos:

1. páginas con breadcrumb visible + `BreadcrumbList`, como colecciones de Cuaderno y Recomendaciones;
2. páginas con `BreadcrumbList` pero sin una segunda barra visual, como la ficha de Samuel;
3. páginas con breadcrumb humano pero sin `BreadcrumbList`, especialmente herramientas y algunas superficies utilitarias;
4. páginas donde no existe ningún contrato de breadcrumb.

La primera ejecución del nuevo auditor contra el sitio real fue útil precisamente porque falsó una interpretación demasiado agresiva: encontró 28 “errores”, de los cuales 26 eran páginas con breadcrumb visible pero sin structured data y 2 eran rutas visible/structured distintas pero compatibles. La documentación oficial actual no convierte ninguno de esos casos, por sí solo, en error.

Por tanto, el gap real de A.6 es **QA de validez e integridad de los breadcrumbs que sí existen**, más inventario de cobertura. No es imponer `BreadcrumbList` o una barra visual a toda página profunda.

## Revalidación con la documentación oficial vigente

Fuente primaria:

https://developers.google.com/search/docs/appearance/structured-data/breadcrumb

La documentación vigente confirma:

- `BreadcrumbList` sigue siendo una feature soportada;
- el breadcrumb debe representar una ruta típica y útil para el usuario, no copiar mecánicamente la URL;
- una página puede declarar múltiples breadcrumb trails;
- **no es obligatorio incluir el host/top level**;
- **no es obligatorio incluir la página actual**;
- si se usa `BreadcrumbList`, Google exige **al menos dos `ListItem`**;
- `position` es obligatorio y define el orden;
- `item` es obligatorio en cada `ListItem` salvo el último, que puede heredar la URL de la página contenedora.

Esto invalida dos simplificaciones del blueprint histórico:

1. “último item = canonical siempre” no puede ser un error universal, porque el current item puede omitirse;
2. “visible ↔ JSON-LD deben ser exactamente iguales” tampoco puede ser universal, porque Google admite múltiples rutas y niveles omitidos.

La guía general de structured data mantiene la exigencia de marcado válido y representativo:

https://developers.google.com/search/docs/appearance/structured-data/sd-policies

## Evidencia del repo actual

### Colección del Cuaderno

`/cuaderno/temas/fantasia-de-portales/` publica visible + `BreadcrumbList` con una ruta coherente.

### Recomendaciones

`/recomendaciones/portal-fantasy-espanol/` publica visible + `BreadcrumbList`.

### Samuel

`/libros/samuel-entre-mundos/` publica `BreadcrumbList` pero no una segunda fila visual. Ese modelo es válido y no se toca.

### Herramientas y otras superficies

La primera ejecución real detectó numerosas páginas con breadcrumb visible y sin `BreadcrumbList`, entre ellas herramientas. Eso se conserva como inventario `INFO`, no como fallo: structured data es una mejora opcional, no una condición de validez de la navegación humana.

### Fragmento de Samuel y guía imprimible

El audit inicial marcó ambos como `order-drift` porque sus rutas visible y structured no eran idénticas:

- el fragmento visible incluye `Libros`, mientras su `BreadcrumbList` usa una ruta más corta a través de Samuel;
- la guía imprimible omite `Inicio` visualmente y usa una formulación ligeramente distinta para “Club de lectura”.

Ambas cadenas son rutas coherentes hacia la página. La documentación vigente permite trails alternativos y no obliga a replicar todos los niveles. El checker final solo bloquea **contradicciones de orden entre destinos compartidos**, no diferencias legítimas de longitud o copy.

## Implementación final

### `scripts/check-breadcrumb-parity.py`

Usa `data/content-registry.json` como autoridad de rutas públicas; **no crea `data/breadcrumbs.json`**.

Audita rutas públicas/indexables con `sourceFile` HTML y:

- detecta breadcrumb visible por clase/`aria-label` semánticos;
- extrae todos los `BreadcrumbList`, incluidos múltiples trails;
- detecta JSON-LD breadcrumb malformado;
- exige al menos dos `ListItem` por `BreadcrumbList`;
- exige posiciones consecutivas `1..N`;
- exige `name`;
- exige `item` en todos los elementos estructurados salvo el último;
- valida URLs same-origin, conocidas y públicas;
- rechaza URLs relativas ambiguas en vez de resolverlas heurísticamente;
- rechaza destinos repetidos;
- si la URL canónica actual aparece, no puede aparecer antes del final;
- valida `aria-current="page"` en breadcrumbs visibles cuando existe;
- permite múltiples trails;
- permite omitir host/current;
- permite longitudes y labels distintos entre visible/structured;
- solo reporta `order-drift` entre ambos cuando al menos dos destinos compartidos aparecen en un orden contradictorio.

### Severidad definitiva

```text
ERROR
  BreadcrumbList malformado
  menos de 2 ListItem
  position no consecutivo
  name ausente
  item ausente en un ListItem estructurado no final
  URL externa/ambigua/no canónica/no pública
  destino repetido
  current canonical antes del final
  aria-current visible múltiple/no final
  orden contradictorio de destinos compartidos

INFO
  breadcrumb visible sin BreadcrumbList
  BreadcrumbList sin breadcrumb visual dedicado

PASS
  cualquier combinación válida de los dos contratos
  ruta sin breadcrumb
```

Esto separa **integridad** de **cobertura opcional**. CI bloquea datos incorrectos, no una oportunidad SEO no implementada.

### Informe opcional

```bash
python scripts/check-breadcrumb-parity.py
python scripts/check-breadcrumb-parity.py --json artifacts/breadcrumbs.json
```

El JSON es evidencia de auditoría, no una segunda fuente de verdad.

## Regresión

`tests/test-breadcrumb-parity.py` cubre 15 contratos:

1. visible + JSON-LD válido;
2. JSON-LD-only válido e inventariado;
3. visible-only válido e inventariado;
4. omisión válida de host/current manteniendo dos items;
5. labels distintos con destino válido;
6. orden contradictorio de destinos compartidos;
7. URL externa;
8. current canonical antes del final;
9. posiciones no consecutivas;
10. múltiples `BreadcrumbList`;
11. breadcrumb JSON-LD malformado;
12. ruta sin contrato breadcrumb;
13. URL relativa ambigua;
14. `BreadcrumbList` de un solo item;
15. `item` ausente en elemento no final.

## CI

`.github/workflows/content-index-check.yml` ejecuta explícitamente:

```bash
python scripts/check-breadcrumb-parity.py
python tests/test-breadcrumb-parity.py
```

`Required merge gate` vuelve a ejecutar todos los `tests/test-*.py`.

## Lo que A.6 NO hace

- no añade una barra breadcrumb sitewide;
- no obliga a convertir cada breadcrumb visible en structured data;
- no obliga a convertir cada `BreadcrumbList` en UI visible;
- no exige Home/current en structured data;
- no exige que visible y structured tengan exactamente la misma longitud o copy;
- no infiere jerarquía por carpetas/slugs;
- no crea un segundo registry;
- no duplica `section-context`;
- no mezcla Person/Book IDs;
- no crea un score SEO.

## Trigger para tocar HTML

Solo se corrige una página cuando aparezca un defecto objetivo del marcado existente o cuando una decisión editorial/UX independiente justifique ampliar cobertura structured/visible en esa familia.

Que el audit reporte `missing-jsonld` o `missing-visible` como `INFO` no es por sí solo autorización para modificar decenas de páginas.

## Definition of Done

- [x] historia y blueprint W4 de #135 preservados;
- [x] `main@291c8c6…` inspeccionado;
- [x] documentación Google vigente revalidada;
- [x] current/host opcionales reflejados;
- [x] mínimo de dos `ListItem` reflejado;
- [x] `item` no-final obligatorio reflejado;
- [x] primera ejecución real usada para falsar severidades incorrectas;
- [x] cuatro modelos de cobertura del repo reconocidos;
- [x] checker implementado sin segunda autoridad;
- [x] múltiples trails soportados;
- [x] 15 contratos de regresión;
- [x] CI integrado;
- [x] no rollout visual/structured indiscriminado.

**Conclusión:** A.6 queda convertida en un guardrail útil y conservador: protege la calidad del breadcrumb que publicamos y hace visible la cobertura, sin confundir una feature opcional de Search con un requisito universal del sitio.