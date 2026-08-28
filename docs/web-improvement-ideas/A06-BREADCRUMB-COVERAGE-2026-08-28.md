# A.6 · Breadcrumbs visibles + `BreadcrumbList`

Fecha de revisión: 2026-08-28
Idea original: añadir breadcrumbs visibles y schema `BreadcrumbList` a rutas profundas si faltan.

## Veredicto

**PARTIAL_AUDIT / YA EXISTE EN SUPERFICIES IMPORTANTES. AUDITAR COBERTURA ANTES DE AÑADIR NADA.**

Google mantiene soporte oficial para `BreadcrumbList`: puede ayudar a mostrar la posición de una página dentro de la jerarquía del sitio y a que las personas entiendan/exploren esa jerarquía. Pero el repo ya usa breadcrumbs en páginas canónicas relevantes; la tarea correcta es detectar gaps/contradicciones, no inyectar breadcrumbs indiscriminadamente en todas las páginas.

## Fuente primaria

Google Search Central · Breadcrumb structured data
https://developers.google.com/search/docs/appearance/structured-data/breadcrumb

Puntos relevantes:

- Google usa breadcrumb markup para categorizar información en resultados.
- La cadena debe representar una ruta típica/útil hacia la página, no necesariamente reproducir literalmente la URL.
- `BreadcrumbList` requiere `ListItem` ordenados con `position`, `name` y, salvo el último elemento, normalmente `item`.
- El markup debe describir contenido visible/real y cumplir las políticas generales de structured data.

Schema.org:
https://schema.org/BreadcrumbList

## Evidencia actual del repo

Ya hay `BreadcrumbList` en superficies importantes:

### Samuel

`/libros/samuel-entre-mundos/` contiene:

```text
Inicio → Libros → Samuel entre mundos
```

integrado dentro del `WebPage` JSON-LD.

### Las manecillas del recuerdo

`/las-manecillas-del-recuerdo/` contiene:

```text
Inicio → Libros → Las manecillas del recuerdo
```

### Topic collections

La PR #35 preservó explícitamente `BreadcrumbList` en `/cuaderno/temas/` y `/cuaderno/temas/fantasia-de-portales/`.

Por tanto, la idea no puede tratarse como “breadcrumbs inexistentes”.

## La pregunta correcta

No es “¿toda URL profunda tiene BreadcrumbList?”, sino:

1. ¿qué familias se benefician de jerarquía explícita?
2. ¿hay páginas profundas donde el breadcrumb del JSON-LD contradice `parentId`/`hubId` del registry?
3. ¿hay breadcrumb visible y JSON-LD que difieren entre sí?
4. ¿algún builder genera páginas sin el contrato que su familia sí debería tener?

## Familias candidatas

### Debe auditarse

- libros/obras;
- Cuaderno y colecciones temáticas;
- recomendaciones;
- herramientas individuales;
- directorios/recursos profundos;
- clubes de lectura y guías hijas.

### No imponer por defecto

- Home;
- 404;
- legal/noindex;
- páginas utility/machine;
- páginas de un solo nivel donde el breadcrumb visual añadiría ruido sin ayudar al lector.

## Fuente de verdad propuesta

La jerarquía ya existe en `data/content-registry.json` mediante `parentId` y `hubId`. **No crear un segundo JSON de breadcrumbs.**

Ejemplo derivado:

```text
samuel-club-guide
parentId = samuel-club
samuel-club.parentId = work-samuel
work-samuel.parentId = works-hub
```

El checker debe poder derivar una ruta semántica y compararla con JSON-LD cuando la familia requiere breadcrumb.

## Implementación propuesta

`scripts/check-breadcrumb-coverage.py`

Entrada:
- `data/content-registry.json`;
- HTML de `sourceFile`.

Salida:

```text
PASS work-samuel: Inicio > Libros > Samuel entre mundos
PASS work-manecillas: Inicio > Libros > Las manecillas del recuerdo
WARN tool-x: family=tool expects BreadcrumbList but none found
ERROR article-y: BreadcrumbList item #2 points to unknown/noncanonical URL
```

Opciones:

```bash
python scripts/check-breadcrumb-coverage.py
python scripts/check-breadcrumb-coverage.py --json artifacts/breadcrumbs.json
```

## Reglas del checker

- validar JSON parseable;
- posiciones 1..N sin saltos/duplicados;
- URLs same-origin absolutas cuando haya `item`;
- URLs deben resolver a canonical/registry conocido;
- último item debe representar la página actual;
- no exigir breadcrumb a familias excluidas;
- si existe breadcrumb visible, comparar labels/destinos de forma razonable con JSON-LD;
- no asumir que la jerarquía de carpetas es la jerarquía editorial.

## Ejemplo de markup válido

```json
{
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Inicio",
      "item": "https://davidportodiaz.com/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Cuaderno",
      "item": "https://davidportodiaz.com/cuaderno/"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Qué es el portal fantasy"
    }
  ]
}
```

No copiar este ejemplo a todas las páginas; debe generarse/validarse desde la jerarquía real.

## Breadcrumb visible vs structured data

La presencia de schema no obliga a introducir una barra visual idéntica en cada familia.

Si UX decide breadcrumbs visibles:

- deben ser navegación real con `<nav aria-label="Migas de pan">`;
- anchors reales `<a href>`;
- último elemento puede ser texto/`aria-current="page"`;
- no duplicar `section-context` si ambos resuelven exactamente la misma tarea y generan ruido.

Esto es especialmente importante en esta web, donde ya existe navegación contextual de sección.

## Qué NO hacer

- generar breadcrumbs a partir de slugs/carpetas sin registry;
- añadirlos a Home/404 solo para “tener schema”;
- duplicar section-context con otra fila visual innecesaria;
- poner páginas noindex/gated en una cadena pública si no corresponde;
- usar nombres keyword-stuffed en lugar de labels humanos;
- crear enlaces a breadcrumbs inexistentes solo para ampliar el grafo.

## Tests

- fixtures con posiciones incorrectas;
- canonical final incorrecto;
- parentId inexistente/ciclo;
- family required sin breadcrumb;
- family exempt sin falso fallo;
- JSON-LD parseable y URLs absolutas;
- builder parity para cualquier familia generada que se modifique.

## Coste / beneficio

Auditar: bajo coste / valor medio.
Añadir markup donde realmente falta: bajo/medio.
Añadir barra visual sitewide sin diseño: coste UX y visual potencialmente superior al beneficio.

## Definition of Done

- [ ] definir matriz de familias `required / optional / exempt`;
- [ ] derivar jerarquía desde registry;
- [ ] ejecutar inventario real antes de modificar HTML;
- [ ] corregir únicamente gaps/contradicciones;
- [ ] si se toca un builder, añadir `--check`/parity;
- [ ] no duplicar navegación contextual sin motivo de UX;
- [ ] Rich Results/structured-data QA verde.

## Recomendación de merge

**MERGE como PARTIAL_AUDIT.** `BreadcrumbList` sigue siendo válido y útil, pero la mejora correcta es cobertura/paridad sobre el sistema actual, no un rollout ciego.