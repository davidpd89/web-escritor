# D.9 · Revalidación de producción — tiempo estimado de lectura

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **ALREADY_PILOTED_MANUALLY · CUADERNO_METADATA_OWNER_EXISTS · BUILD_DERIVATION_NOT_OWNED · NO_AUTOMATION_WITHOUT_DRIFT · NO_CODE**.

## 1. Corrección respecto a la reconstrucción histórica

La reconstrucción del 29/08 decía que no se había localizado una implementación equivalente en `main`. La inspección directa de producción invalida esa frase.

El tiempo de lectura ya aparece como metadata HTML visible en múltiples piezas del Cuaderno. D.9 no parte de cero.

## 2. Inventario directo de superficies comprobadas

En `main` se verificó:

| Ruta | Metadata visible |
| --- | --- |
| `/cuaderno/que-es-el-portal-fantasy/` | `7 min de lectura` |
| `/cuaderno/portal-fantasy-vs-fantasia-epica/` | `4 min de lectura` |
| `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/` | `8 min de lectura` |
| `/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/` | `5 min de lectura` |
| `/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/` | `4 min de lectura` |
| `/cuaderno/worldbuilding-noveris-ciudad-magica/` | `7 min de lectura` |
| `/cuaderno/sistema-de-magia-noveris/` | `1 min de lectura` |

La última URL es un stub `noindex` con contenido retirado; su minuto de lectura es una señal de que la metadata existe incluso fuera de long-form útil, no una razón automática para tocar ahora otro HTML largo.

## 3. Owner editorial actual en Drive

`21 — CUADERNO + ARTÍCULO MASTER SPEC V1 — ÍNDICE EDITORIAL · LECTURA · SERIES · SEO · RESPONSIVE` gobierna esta familia.

El master establece expresamente:

- en el índice, `tiempo de lectura solo si ya se calcula y aporta, no por moda`;
- en la apertura del artículo, `tiempo lectura solo si útil`;
- metadata textual y sobria, sin convertirla en chips decorativos.

Por tanto la decisión de producto actual no es «añadir tiempo de lectura a todo», sino conservarlo donde aporta orientación.

## 4. No se ha localizado un cálculo build-time propietario

`scripts/build-article-tools.py` fue inspeccionado directamente. Su función es pre-renderizar herramientas/TOC, generar IDs y coordinar el control de progreso; no calcula ni sincroniza minutos de lectura.

Los valores actuales son, por la evidencia disponible, metadata editorial estática/manual.

Eso no constituye por sí mismo un bug. La preferencia histórica por build-time buscaba determinismo y evitar JS, pero automatizar ahora solo tiene sentido si se demuestra deriva real.

## 5. Por qué no crear un builder ahora

No se ha demostrado todavía:

- que alguno de los minutos publicados sea incorrecto;
- que los valores queden desactualizados tras editar artículos;
- que nuevas piezas omitan sistemáticamente la metadata cuando debería aparecer;
- que exista una regla WPM canónica previamente acordada;
- que otra autoridad del contenido ya almacene un word count reutilizable.

Crear un generador sin esos contratos obligaría a inventar una fórmula y podría sobrescribir decisiones editoriales existentes.

## 6. Trigger correcto para automatizar

Automatizar solo si aparece al menos uno:

```text
manual reading-time drift reproducible
OR repeated omissions in eligible long-form
OR canonical word-count authority becomes available
OR editorial workflow explicitly adopts a documented WPM rule
```

Entonces el cambio correcto sería:

1. definir qué nodo/cuerpo editorial se cuenta;
2. definir WPM/redondeo una sola vez;
3. excluir shell, related, newsletter y utilidades;
4. derivar valor en build;
5. añadir `--check`/test de stale output;
6. limitarlo a las familias/rutas elegibles;
7. no tocar fichas de libro por consistencia artificial.

## 7. Crossfinding: stub retirado

`/cuaderno/sistema-de-magia-noveris/` declara `1 min de lectura` pese a ser una URL retirada/noindex y de orientación mínima.

Según el master, este dato probablemente aporta poco. Se registra como **LOW_VALUE_METADATA_CROSSFINDING**.

No se modifica aquí porque:

- D.3 ya corrigió en su PR independiente otro problema de scoping de esa misma página;
- el conector de GitHub disponible reemplaza archivos HTML largos completos, por lo que una limpieza cosmética de una línea no justifica aumentar el riesgo de corrupción;
- no afecta indexación, canonical ni contenido factual.

Puede eliminarse en un cambio local/hunk seguro cuando se agrupe mantenimiento de esa página.

## 8. SEO y rendimiento

El tiempo de lectura existente es texto HTML y no requiere runtime. No se trata como factor de ranking ni se añade schema específico inventado.

La implementación actual tampoco justifica unir D.9 a D.3: expectativa de duración y progreso de scroll siguen siendo funciones distintas.

## 9. Qué no hacer

- no añadir un segundo componente de reading time;
- no calcularlo en JavaScript en cada carga;
- no inventar una constante WPM sin owner;
- no recalcular automáticamente todas las páginas solo porque existe la idea histórica;
- no añadirlo a fichas de libro/Home/herramientas por consistencia;
- no presentarlo como SEO;
- no convertir cada metadata en badge/chip;
- no usar el valor manual actual como evidencia de que la fórmula histórica propuesta ya existe.

## 10. Definition of Done

- [x] falsa ausencia histórica corregida;
- [x] siete superficies con reading time verificadas directamente;
- [x] owner de diseño/editorial en Drive recuperado;
- [x] builder de article tools inspeccionado y descartado como calculadora de minutos;
- [x] automatización condicionada a deriva/owner real;
- [x] stub retirado registrado como crossfinding sin cambio inseguro;
- [x] sin runtime ni builder nuevo innecesario.

## Estado para Claude

Tratar D.9 como **piloto ya materializado manualmente**. No implementar desde cero. Si se detecta deriva real, convertir entonces la metadata a derivación build-time con una regla documentada y tests; hasta entonces preservar la solución existente y su criterio `solo si útil`.