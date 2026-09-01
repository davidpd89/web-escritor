# B.3 · Revalidación de producción · 2026-08-29

## Veredicto

**ALREADY_PILOTED · CONDITIONAL · HOLD_EXPANSION · NO_CODE**

La idea histórica no necesita un piloto nuevo: el `main` vivo ya utiliza el patrón de respuesta inmediata en las piezas definicionales donde es editorialmente natural. La acción correcta ahora es **no extenderlo mecánicamente** sin evidencia de que aporte valor adicional.

## Base inspeccionada

- `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`;
- `data/content-registry.json`;
- `/cuaderno/que-es-el-portal-fantasy/`;
- `/cuaderno/portal-fantasy-vs-fantasia-epica/`;
- `/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/`;
- guía oficial vigente de Google Search Central sobre funciones generativas y contenido people-first.

## Piloto real ya existente

### Qué es el portal fantasy

La pieza abre su cuerpo editorial con un bloque visible:

```html
<div class="article-note" role="note" aria-label="Definición">
  <p><strong>El portal fantasy</strong> es un subgénero ...</p>
</div>
```

La respuesta define el término en un párrafo autocontenido y después el artículo desarrolla historia, estructura, ejemplos, mercado y contexto propio.

### Portal fantasy vs. fantasía épica

La pieza abre con otra definición directa que responde exactamente a la pregunta del título: diferencia ambos géneros por el origen del protagonista y la existencia o no del cruce entre mundos.

Después desarrolla comparación, ejemplos y matices.

### Fantasía juvenil española con portales y magia con coste

La guía abre con un `article-note` definicional que resume el encaje de portales + magia con coste y después desarrolla las consecuencias narrativas, protagonistas, worldbuilding y contexto español.

## Qué demuestra este estado

B.3 ya está **pilotada** en las superficies adecuadas:

- preguntas definicionales;
- comparaciones directas;
- guías conceptuales.

No se ha convertido en un componente obligatorio para todos los artículos ni en una secuencia repetitiva por cada H2. Ese equilibrio coincide con la decisión de #135.

## Revalidación Google 2026

Google Search Central mantiene que:

- las prácticas SEO fundamentales y el contenido útil/people-first siguen siendo la base;
- no es necesario dividir el contenido en fragmentos pequeños para que los sistemas generativos lo entiendan;
- no es necesario reescribir específicamente para IA;
- no existe una longitud ideal universal de página;
- la estructura debe responder primero a la audiencia y a la cuestión tratada.

Fuentes:

- `https://developers.google.com/search/docs/fundamentals/ai-optimization-guide`;
- `https://developers.google.com/search/docs/fundamentals/creating-helpful-content`.

Por tanto, el beneficio de los bloques actuales debe evaluarse como **claridad editorial/UX**, no como requisito de AI Overviews, AI Mode o GEO.

## Decisión operativa

No modificar artículos por B.3 en esta PR.

No existe evidencia disponible en esta revisión —Search Console, testing de lectores o problema UX reproducible— que justifique expandir el patrón a más piezas.

La ausencia de datos no se convierte en una recomendación automática de más bloques.

## Dónde sí podría extenderse en el futuro

Solo cuando una pieza nueva o existente tenga una pregunta principal cuya mejor apertura humana sea una respuesta inmediata. Ejemplos:

- una definición;
- una comparación;
- una guía práctica con decisión inmediata;
- requisitos de una convocatoria;
- explicación breve del propósito de una herramienta.

El primer párrafo puede cumplir la función sin necesidad de label `Respuesta breve` ni componente especial.

## Dónde no debe extenderse

- fragmentos literarios;
- ensayos cuya progresión sea parte del valor;
- entrevistas;
- páginas de obra que ya resuelven la orientación con otra jerarquía;
- todos los H2 por defecto;
- contenido reescrito solo para aparentar estructura AEO/GEO.

## Relación con B.8

El piloto actual confirma la diferencia:

- B.3 = respuesta inmediata a una pregunta/definición local;
- B.8 = resumen global/TL;DR de una pieza completa.

No debe duplicarse un `article-note` de apertura y un TL;DR cuando ambos solo repitan lo mismo.

## Triggers de reapertura

1. una pregunta real de lectores/Search Console no queda resuelta con rapidez;
2. un artículo práctico nuevo necesita una definición previa para ser usable;
3. pruebas de UX muestran dificultad para encontrar la respuesta principal;
4. se quiere medir de forma controlada el patrón en otra familia editorial.

## Qué no hacer

- componente global obligatorio;
- inserción automática por builder/regex;
- límite de palabras diseñado para “citación IA”;
- score AEO;
- repetir la misma respuesta en deck, note, FAQ y TL;DR;
- cambiar simultáneamente múltiples variables y atribuir luego el resultado al bloque.

## Definition of Done

- [x] estado histórico `CONDITIONAL` preservado;
- [x] corpus actual de Cuaderno inspeccionado;
- [x] piloto real localizado en tres piezas definicionales;
- [x] Google 2026 revalidado;
- [x] no se identifica deuda de implementación;
- [x] expansión retenida hasta evidencia real;
- [ ] CI del HEAD final completamente verde;
- [ ] revisión de Claude antes de merge.

## Cierre

B.3 no necesita código ni un nuevo rollout. El sitio ya demuestra el patrón correcto en artículos donde la respuesta directa mejora la comprensión. La mejora futura consiste en mantener criterio editorial, no en incrementar el número de answer blocks.