# B.8 · Revalidación de producción — TL;DR en piezas largas

Fecha: 2026-08-29  
Base: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #173  
Decisión: **CONDITIONAL · TRIGGER_NOT_MET · NO_CODE**

## Conclusión

El trigger de B.8 no está demostrado en el corpus actual. Las piezas largas inspeccionadas del Cuaderno están aproximadamente en el rango de 4–8 minutos de lectura, disponen de índice cuando lo necesitan y varias ya abren con una definición/respuesta directa natural.

Añadir ahora un TL;DR adicional sería, en esos casos, duplicar la capa B.3 y añadir una plantilla sin problema de lectura demostrado.

## Evidencia del repo

Ejemplos revisados:

- `cuaderno/que-es-el-portal-fantasy/`: 7 min, índice y definición directa inicial;
- `cuaderno/portal-fantasy-vs-fantasia-epica/`: 4 min, índice y respuesta inmediata a la diferencia principal;
- `cuaderno/fantasia-juvenil-espanola-portales-magia-coste/`: 8 min, índice y definición inicial;
- `cuaderno/worldbuilding-noveris-ciudad-magica/`: 7 min, índice y `article-note` inicial.

La búsqueda del repo no muestra un patrón existente de `TL;DR`, `En resumen` o `Resumen rápido` que deba normalizarse.

## Fuente primaria actual

La guía de Google para funciones generativas de Search mantiene que no hace falta reescribir ni fragmentar contenido en un formato especial para IA. La claridad y la utilidad para las personas siguen siendo el criterio principal.

Por tanto, un TL;DR solo se justifica si mejora escaneabilidad humana de una pieza concreta; no como táctica GEO/AEO obligatoria.

## Diferencia respecto a B.3

- B.3 responde inmediatamente una pregunta local o definicional.
- B.8 resume una pieza completa cuando la extensión/complejidad hace útil esa capa.

Las piezas inspeccionadas ya resuelven bien el primer problema. No hay evidencia de que necesiten además el segundo.

## Trigger real de reapertura

Aplicar B.8 cuando aparezca al menos una de estas condiciones:

- artículo sustancialmente más largo/complejo que el corpus actual;
- guía con muchas decisiones o pasos donde el lector necesite un mapa ejecutivo;
- datos de lectura/feedback que indiquen dificultad para localizar conclusiones;
- pieza de referencia cuya síntesis tenga utilidad editorial independiente.

En ese caso el resumen debe escribirse manualmente para esa pieza y medirse antes de convertirlo en componente recurrente.

## Qué no hacer

- añadir TL;DR a todos los artículos por builder;
- imponer una longitud arbitraria de 40–60 palabras;
- duplicar una definición inicial ya clara;
- insertar resúmenes en fragmentos literarios;
- medir éxito por “citable chunks”;
- afirmar que un TL;DR garantiza citas de IA.

## Definition of Done

- [x] corpus actual inspeccionado;
- [x] longitud/estructura de ejemplos contrastada;
- [x] relación con B.3 revalidada;
- [x] trigger no cumplido documentado;
- [x] no se introduce plantilla global;
- [ ] reabrir ante una pieza realmente larga/compleja o evidencia UX;
- [ ] revisión de Claude antes de merge.

**Estado final:** `CONDITIONAL · TRIGGER_NOT_MET · NO_CODE`.
