# A.6 · Revalidación e implementación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #155  
Decisión operativa: **IMPLEMENTED_IN_PR · AUDIT_GUARDRAIL · NO_SITEWIDE_VISUAL_ROLLOUT**

> Autoridad operativa: este documento y el código del HEAD actual describen la implementación final. `A06-BREADCRUMB-COVERAGE-2026-08-28.md` conserva la arqueología de #135 y su blueprint W4 histórico.

## Problema real confirmado

#135 acertó al no ordenar “añadir breadcrumbs a toda la web”. El repo actual tiene tres estados legítimos:

1. páginas con breadcrumb visible + `BreadcrumbList`, como colecciones de Cuaderno y Recomendaciones;
2. páginas con `BreadcrumbList` pero sin una segunda barra visual, como la ficha de Samuel, que ya dispone de navegación contextual;
3. páginas donde no existe un contrato de breadcrumb y añadirlo no mejora necesariamente la UX.

Lo que faltaba en `main` no era otra barra de navegación, sino **un gate reproducible que impidiera que las páginas que sí publican breadcrumbs visibles/estructurados diverjan entre sí o apunten a rutas incorrectas**.

No existía `scripts/check-breadcrumb-parity.py` ni una comprobación equivalente en `content-index-check.yml`.

## Revalidación con la documentación oficial vigente

Fuente primaria:

https://developers.google.com/search/docs/appearance/structured-data/breadcrumb

La documentación actual de Google mantiene `BreadcrumbList` como feature soportada y aclara varios puntos que obligan a ajustar el blueprint histórico de #135:

- el breadcrumb debe representar una ruta típica y útil para el usuario, no copiar mecánicamente la estructura de URL;
- se permiten varias rutas breadcrumb para una misma página;
- **no es obligatorio incluir la página de nivel superior/host como primer elemento**;
- **no es obligatorio incluir la página actual como último `ListItem`**;
- los `ListItem` estructurados deben respetar el orden mediante `position`.

Por tanto, la frase histórica “el último item debe ser siempre el canonical actual” no puede convertirse en un error universal de CI. El contrato correcto es más preciso: si la URL canónica actual aparece en la cadena, no puede aparecer antes del final; si se omite, esa omisión es válida.

La guía general de structured data sigue exigiendo que el marcado represente contenido real y sea técnicamente válido:

https://developers.google.com/search/docs/appearance/structured-data/sd-policies

## Evidencia del repo actual

### Colección del Cuaderno

`/cuaderno/temas/fantasia-de-portales/` publica:

- breadcrumb visible `Inicio → Cuaderno → Temas → Fantasía de portales`;
- `BreadcrumbList` equivalente.

Es una familia donde la paridad visible ↔ structured data es un contrato real.

### Recomendaciones

`/recomendaciones/portal-fantasy-espanol/` publica:

- breadcrumb visible `Inicio → Recomendaciones → Portal fantasy en español`;
- `BreadcrumbList` equivalente.

También debe mantenerse sincronizado.

### Samuel

`/libros/samuel-entre-mundos/` publica `BreadcrumbList` (`Inicio → Libros → Samuel entre mundos`) pero no añade una segunda fila visual de migas. La página ya dispone de shell/contexto de navegación y una barra visual adicional no está justificada por A.6.

Ese estado se conserva como **JSON-LD-only válido**, no como defecto que obligue a modificar la UI.

## Implementación final

### `scripts/check-breadcrumb-parity.py`

El checker usa `data/content-registry.json` como autoridad de rutas públicas y aliases; **no crea `data/breadcrumbs.json`**.

Audita rutas públicas e indexables con `sourceFile` HTML y:

- detecta breadcrumbs visibles por clase/`aria-label` semánticos;
- extrae todos los `BreadcrumbList` existentes, incluidos múltiples trails;
- valida JSON-LD breadcrumb parseable;
- exige posiciones consecutivas en cada `BreadcrumbList`;
- valida URLs same-origin y rutas conocidas/canónicas;
- evita exponer rutas no públicas dentro de un breadcrumb;
- rechaza URLs relativas ambiguas en vez de adivinarlas;
- rechaza URLs repetidas o la página actual antes del final;
- comprueba `aria-current="page"` cuando existe en la navegación visible;
- compara la secuencia intermedia visible ↔ structured data;
- usa `label`, `shortLabel` y `aliases` del registry para evitar falsos positivos semánticos (`Obras` / `Libros`, por ejemplo);
- soporta varias rutas estructuradas y acepta que una de ellas coincida con la visible;
- permite omitir Home y/o la página actual del `BreadcrumbList`, conforme a la documentación vigente.

### Severidad

```text
ERROR
  breadcrumb visible sin BreadcrumbList
  JSON-LD breadcrumb malformado
  posiciones incoherentes
  URL externa/no canónica/no pública
  current page en posición intermedia
  drift real de rutas/nombres intermedios visible ↔ structured

INFO
  BreadcrumbList sin breadcrumb visual dedicado

PASS
  visible + structured en paridad
  JSON-LD-only válido
  ruta sin contrato de breadcrumb
```

`missing-visible` es deliberadamente informativo. Convertirlo en error impondría un patrón visual sitewide que Google no exige y que puede duplicar `section-context`.

### Informe opcional

```bash
python scripts/check-breadcrumb-parity.py
python scripts/check-breadcrumb-parity.py --json artifacts/breadcrumbs.json
```

El JSON es un artefacto de auditoría, no una segunda fuente de verdad.

## Regresión

`tests/test-breadcrumb-parity.py` cubre 13 contratos:

1. visible + JSON-LD coincidente;
2. JSON-LD-only válido;
3. visible-only bloqueado por `missing-jsonld`;
4. omisión válida de Home/current en structured data;
5. aliases del registry para nombres equivalentes;
6. drift de secuencia intermedia;
7. URL externa;
8. canonical actual antes del final;
9. posiciones no consecutivas;
10. múltiples `BreadcrumbList` cuando uno coincide;
11. breadcrumb JSON-LD malformado;
12. ruta sin contrato de breadcrumb;
13. URL relativa ambigua.

## CI

`.github/workflows/content-index-check.yml` ejecuta explícitamente:

```bash
python scripts/check-breadcrumb-parity.py
python tests/test-breadcrumb-parity.py
```

Además `Required merge gate` ejecuta `tests/test-*.py`, de modo que la semántica queda protegida también por el gate universal.

## Lo que A.6 NO hace

- no añade breadcrumb visual a todas las páginas;
- no obliga a Home a tener breadcrumb;
- no exige que el current page aparezca en JSON-LD;
- no infiere jerarquía desde carpetas/slugs;
- no crea un segundo registry;
- no duplica `section-context`;
- no mezcla esta responsabilidad con Person/Book IDs;
- no convierte la presencia de `BreadcrumbList` en excusa para alterar UX estable;
- no crea un “breadcrumb score” SEO.

## Trigger para tocar HTML

Solo se modifica una página/familia cuando el checker demuestra un defecto objetivo:

- breadcrumb visible sin structured parity;
- destino no canónico/no público;
- orden incoherente;
- builder que genera drift entre páginas hermanas;
- o una decisión UX independiente concluye que una familia concreta necesita navegación breadcrumb visible.

La última condición requiere evidencia de navegación/UX; no se deriva automáticamente de SEO.

## Definition of Done

- [x] historia y blueprint W4 de #135 preservados;
- [x] `main@291c8c6…` inspeccionado;
- [x] documentación Google vigente revalidada;
- [x] regla histórica “current obligatorio” corregida según fuente actual;
- [x] modelos reales visible+JSON-LD y JSON-LD-only contrastados;
- [x] checker implementado sin segunda autoridad;
- [x] múltiples breadcrumb trails soportados;
- [x] paridad semántica protegida;
- [x] 13 contratos de regresión añadidos;
- [x] CI integrado;
- [x] no se fuerza rollout visual sitewide.

**Conclusión:** A.6 deja de ser una auditoría documental pendiente y pasa a una capacidad de QA mantenible. El cambio útil es impedir drift donde existe un contrato breadcrumb, no llenar todas las páginas de otra fila de navegación.