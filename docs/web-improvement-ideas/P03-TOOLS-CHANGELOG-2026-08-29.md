# P.3 · Changelog público de herramientas — reconstrucción completa desde PR #135

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: snapshot `8e72321d047c0445c5ac411ebe242af8a0386929` de PR #135.  
Estado final histórico: `DEFER`.

## 1. Hipótesis original

P.3 proponía una página pública «Novedades de herramientas» que recogiese de forma breve qué se añade o mejora en el ecosistema de `/herramientas/`, con la expectativa de crear contenido recurrente de bajo esfuerzo para usuarios habituales.

La idea solo funciona si ya existe una cadencia suficientemente real de releases y una audiencia que vuelve para seguirlas. Sin eso, una página de changelog se convierte en otra superficie editorial que hay que alimentar artificialmente.

## 2. Evolución dentro de #135

### Revisión exhaustiva 27/08

Decisión: `DEFER`.

La revisión concluyó que un changelog solo compensa con:

- releases reales y suficientemente frecuentes;
- usuarios recurrentes;
- información que merezca ser comunicada fuera del historial técnico de Git.

No se debía crear una página para rellenarla con cambios menores.

### Matriz final 28/08

Decisión: `DEFERIR`.

La matriz mantuvo la misma razón: «changelog solo cuando exista frecuencia real de releases; no crear página para rellenarla».

### Autoridad final humana + machine-readable

Estado final: `DEFER`.

No existe cambio posterior de estado.

## 3. Pasadas posteriores / revalidación independiente

La revalidación independiente mantiene P.3. No aparece evidencia nueva que demuestre una necesidad de producto ni una audiencia recurrente para un changelog público.

Las pasadas posteriores aportaron oportunidades para distribución, herramientas y medición, pero no una razón nueva para convertir el historial técnico del repositorio en contenido editorial público.

## 4. Evidencia actual de `main`

`main` contiene un ecosistema amplio de herramientas y autoridades estructuradas (`data/tools-hub.json`, rutas bajo `/herramientas/`, builders y QA). La existencia de muchas herramientas no equivale a tener una cadencia pública de releases que justifique otra URL.

Git ya conserva de forma más exacta:

- commits;
- PRs;
- fechas;
- diffs;
- racional técnico.

Ese historial técnico es hoy suficiente para mantenimiento interno. No debe duplicarse manualmente en una página pública sin propósito para el lector.

## 5. Trigger de reapertura

Reabrir P.3 únicamente si se cumple una combinación clara de señales como:

1. varias mejoras públicas de herramientas durante un periodo sostenido;
2. usuarios recurrentes o feedback que pregunte qué ha cambiado;
3. cambios con valor real para uso, no refactors invisibles;
4. capacidad de mantener el changelog desde una autoridad estructurada, sin edición duplicada;
5. una ruta de distribución real —RSS, newsletter o hub— que justifique la pieza.

No usar un número arbitrario de releases como regla universal: debe existir utilidad humana observada.

## 6. Diseño recomendado si algún día se activa

Preferir un registro estructurado con entradas del tipo:

- fecha;
- herramienta afectada;
- tipo: nueva / mejora / corrección / retirada;
- resumen visible para usuario;
- URL de herramienta;
- breaking change si aplica;
- fuente técnica/PR opcional.

La página pública se generaría desde ese registro. No mantener dos cronologías manuales independientes.

## 7. Qué no publicar

- refactors internos sin efecto perceptible;
- upgrades de dependencias como contenido editorial;
- cambios de CI;
- correcciones de seguridad con detalles explotables;
- texto promocional para aparentar actividad;
- fechas de «actualización» sin cambio real.

## 8. QA / Definition of Done si se reabre

- toda entrada corresponde a una modificación pública real;
- enlace a herramienta vigente;
- orden cronológico determinista;
- noindex/indexing decidido según valor real;
- no se duplica una autoridad técnica existente;
- feed/newsletter solo si hay cadencia que lo justifique;
- no se generan páginas individuales por release sin demanda.

## 9. Relación con otras ideas

- **P.4:** el discovery contextual herramienta↔contenido tiene mayor valor inmediato y prioridad más alta.
- **Q.3:** un registro de experimentos no es un changelog; mide hipótesis/resultados.
- **Q.4:** runbooks de lanzamiento tampoco son changelog de producto.
- **O.4:** Metricool puede distribuir novedades reales si algún día existe esa cadencia, pero no crea la necesidad.

## 10. Conclusión

P.3 queda `DEFER`. El repositorio ya contiene el historial técnico suficiente y #135 no encontró evidencia de que los lectores necesiten una página pública de releases. Solo debe recuperarse cuando exista una cadencia real y recurrente que haga útil esa superficie.