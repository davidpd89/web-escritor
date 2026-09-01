# A.8 · Página “¿En qué orden leer las obras de David Porto?”

Fecha de reconstrucción: 2026-08-29  
Idea original: crear una página específica de orden de lectura por ser un formato frecuente en búsquedas de sagas.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado de esta PR: decisión `REJECT`; no crea URL.

## Veredicto reconciliado

**REJECT en el estado actual.**

La primera versión individual decía `DEFER / REJECT NOW`, pero la autoridad final humana y machine-readable de #135 es inequívoca: **`REJECT`**. Samuel entre mundos y Las manecillas del recuerdo no forman una saga ni tienen un orden obligatorio documentado. Crear ahora una página de “orden de lectura” fabricaría una intención que el catálogo no tiene.

El hecho de que la matriz intermedia usase `DEFERIR` se conserva como historia de investigación, no como estado final.

A.8 puede reabrirse como una nueva evaluación futura si cambian los hechos —por ejemplo, aparece una saga/orden real o demanda recurrente—, pero eso no convierte el estado histórico actual en `DEFER`.

## 1. Regla de reconstrucción

Esta PR usa el corpus directo de #135. Conserva:

- hipótesis original y su argumento de demanda genérica en sagas;
- primera decisión `REJECT`;
- estado intermedio `DEFERIR`;
- cross-check del catálogo/registry;
- alternativa `/empieza-aqui/`;
- autoridad final `REJECT`;
- triggers que justificarían una nueva evaluación;
- revalidación independiente.

## 2. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` proponía una página tipo:

> “¿En qué orden leer las obras de David Porto?”

La justificación era que el formato tiene demanda para sagas y puede ser citable por motores de IA.

La hipótesis tenía que superar una pregunta básica: **¿existe realmente un orden de lectura en este catálogo?**

## 3. Evolución cronológica en #135

### 3.1 · Primera revisión → `REJECT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` concluyó:

> Samuel y Manecillas no son una saga con orden. Crear “orden de lectura” sería thin/artificial. Usar `/empieza-aqui/` para orientar por interés.

Este fue el primer veredicto material.

### 3.2 · Fuentes primarias

Google · Creating helpful, reliable, people-first content  
https://developers.google.com/search/docs/fundamentals/creating-helpful-content

Google Search spam policies  
https://developers.google.com/search/docs/essentials/spam-policies

Aplicación de #135:

- una página debe resolver una necesidad real de la audiencia;
- no crear superficies principalmente porque una keyword/formato funciona para otros sitios;
- evitar contenido thin/doorway/scaled que solo reformula páginas existentes.

No existe una regla de Google ni de IA que obligue a una web de autor a tener “reading order”.

### 3.3 · Repo cross-check → premisa artificial

`docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` incluye A.8 entre las ideas que no deben volver al backlog sin nueva evidencia:

- Samuel y Manecillas no forman saga/orden obligatorio;
- crear la URL sería intención artificial;
- alternativa: mejorar `/empieza-aqui/` por interés/tono.

### 3.4 · Overrides → alternativa conservada

`docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` mantiene A.8 rechazado y propone:

> mejorar `/empieza-aqui/` con rutas por interés/tono y enlaces a ambas obras.

La alternativa resuelve la pregunta legítima “¿por dónde empiezo?” sin afirmar una secuencia inexistente.

### 3.5 · Matriz intermedia → `DEFERIR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` introdujo una formulación menos tajante:

> `DEFERIR`: con dos libros no relacionados, “orden de lectura” tiene baja utilidad. Recuperar si aparece saga/orden real o demanda en queries.

Esta fue una oscilación intermedia. El argumento de reapertura futura sobrevivió; el estado `DEFERIR` no.

### 3.6 · Autoridad machine-readable final → `REJECT`

`data/web-improvement-decisions-2026-08-28.json` fija:

```json
{"id":"A.8","area":"seo","status":"REJECT"}
```

### 3.7 · Autoridad humana final → `REJECT`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md`:

> con dos libros no relacionados, una página “orden de lectura” sería artificial. Reabrir solo si existe saga/orden real o demanda demostrada.

La cláusula “reabrir” es un trigger futuro; no rebaja el estado actual.

### 3.8 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` volvió a revisar A.1–A.12 y mantuvo A.8. No apareció una necesidad nueva que justificase cambiar el rechazo.

Secuencia completa:

```text
hipótesis de reading-order por patrón de sagas
→ REJECT
→ repo confirma obras independientes
→ alternativa /empieza-aqui/
→ matriz intermedia DEFERIR
→ final JSON/humano REJECT
→ revalidación confirma
```

## 4. Evidencia del proyecto

- `work-samuel` y `work-manecillas` son entradas separadas del registry bajo el catálogo de obras;
- no están modeladas como volúmenes de una misma `BookSeries`;
- `/libros/` ya permite descubrir/comparar las obras;
- `/empieza-aqui/` ya resuelve orientación inicial;
- la auditoría de Search Console citada en #135 mostró consultas como “david porto”, “portal fantasy” y “noveris”, no evidencia material de “orden de lectura”.

Una exploración web histórica tampoco encontró una necesidad clara asociada al autor. #135 fue cuidadosa: eso no sustituye Search Console, pero tampoco aporta trigger para una URL nueva.

## 5. Tarea real que sí existe hoy

No “orden”, sino **orientación**.

La web puede ayudar a elegir entre obras independientes mediante `/empieza-aqui/` o `/libros/`, usando hechos editoriales canónicos:

```text
si buscas fantasía juvenil / portal fantasy → Samuel entre mundos
si buscas la propuesta editorial/temática propia de Manecillas → Las manecillas del recuerdo
```

El copy exacto debe derivarse de la información factual del libro; no inventar posicionamientos para rellenar la ruta.

## 6. Triggers para reabrir una evaluación futura

Una nueva PR puede volver a evaluar A.8 si ocurre al menos uno:

1. secuela/precuela con orden recomendado;
2. `BookSeries` real con dos o más volúmenes;
3. queries significativas/recurrentes de Search Console sobre orden;
4. preguntas repetidas de lectores que `/empieza-aqui/` no resuelve;
5. catálogo suficientemente amplio para itinerarios genuinos.

El trigger debe estar documentado con evidencia. No basta “estas páginas funcionan en SEO para otros autores”.

## 7. Si algún día se reactiva

Primero comprobar si basta con ampliar `/libros/` o `/empieza-aqui/`.

Solo con necesidad independiente podría considerarse una URL como:

```text
/orden-de-lectura/
```

Contenido mínimo legítimo:

- respuesta directa al orden real;
- explicación de dependencia/independencia;
- links canónicos;
- estado de publicación real;
- diferencias útiles entre libros;
- aclaración si el orden es opcional.

Structured data solo factual:

- `ItemList` si aporta claridad;
- referencias a entidades `Book` existentes;
- `BookSeries` únicamente si la serie existe;
- nunca `position` narrativa inventada para libros independientes.

## 8. Qué NO hacer

- crear la URL porque “reading order” es keyword común en autores con sagas;
- afirmar que Samuel debe ir antes que Manecillas;
- llamar saga a obras independientes;
- generar variantes “por dónde empezar”, “orden de libros”, “orden de novelas” casi idénticas;
- `BookSeries` ficticia;
- llenar con sinopsis duplicadas;
- usar “citable por IA” como razón independiente para fabricar una página;
- tratar `DEFERIR` de la matriz como estado final ignorando las autoridades posteriores.

## 9. Tests si una futura reevaluación la aprobara

- trigger documentado antes de crear URL;
- registry/sitemap solo se modifican tras aprobación;
- libros/canonicals correctos;
- `BookSeries` factual;
- `ItemList` y orden visible coinciden;
- no duplicación significativa de `/libros/`;
- internal graph correcto;
- query intent/propósito editorial explícitos en la PR.

## 10. Coste / beneficio

Ahora:

- beneficio: bajo/no demostrado;
- riesgo thin/duplicative: medio;
- mantenimiento: innecesario.

Con saga/demanda real:

- beneficio potencial: alto;
- evaluación futura legítima.

## 11. Definition of Done

### Historia ya recuperada

- [x] hipótesis original preservada;
- [x] `REJECT` inicial preservado;
- [x] repo cross-check sobre independencia de obras preservado;
- [x] alternativa `/empieza-aqui/` preservada;
- [x] `DEFERIR` intermedio registrado sin confundirlo con final;
- [x] autoridad JSON final = `REJECT`;
- [x] autoridad humana final = `REJECT`;
- [x] triggers futuros preservados;
- [x] revalidación independiente confirmó.

### Ahora

- [ ] no crear URL de orden de lectura;
- [ ] usar `/libros/`/`/empieza-aqui/` si hay necesidad de orientación;
- [ ] reabrir solo con evidencia nueva.

## 12. Trazabilidad del corpus histórico de #135 revisado para A.8

### Evidencia/decisión específica

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `REJECT` inicial.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — people-first/spam policy.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — premisa artificial + alternativa.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` — alternativa `/empieza-aqui/`.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `DEFERIR` histórico.
- `data/web-improvement-decisions-2026-08-28.json` — `REJECT` final.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana final/triggers.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — falsación independiente.

### Revisados sin cambio específico adicional

Blueprints netos, overrides de repo no aplicables, cuarta a decimoquinta pasada, casos/evidencia/límites, fuentes adicionales, repos evaluados y policy watch fueron revisados; no contienen una decisión posterior que sustituya `REJECT`.

## 13. Recomendación de merge

**MERGE como reconstrucción completa de `REJECT`.**

La PR deja documentado qué tendría que cambiar en el mundo real para volver a evaluar la idea, sin fingir que hoy queda “pendiente” de implementación.