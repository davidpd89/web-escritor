# A.8 · Página “¿En qué orden leer las obras de David Porto?”

Fecha de revisión: 2026-08-28
Idea original: crear una página específica de orden de lectura por ser un formato frecuente en búsquedas de sagas.

## Veredicto

**DEFER / REJECT NOW.**

Actualmente no existe un problema real de orden de lectura que resolver. Samuel entre mundos y Las manecillas del recuerdo son obras diferenciadas; el repo no documenta una relación de saga/continuidad que exija leer una antes que otra. Crear una página de “orden de lectura” ahora fabricaría una intención que el catálogo no tiene.

La web ya dispone de dos superficies más honestas para la tarea real de descubrimiento:

- `/libros/` → catálogo de obras;
- `/empieza-aqui/` → orientación para lectores nuevos.

## Fuentes primarias

1. Google Search Central · Creating helpful, reliable, people-first content
   https://developers.google.com/search/docs/fundamentals/creating-helpful-content
   - El contenido debe ser útil para la audiencia incluso si llegara directamente al sitio.
   - Google desaconseja producir contenido principalmente para atraer visitas de buscadores.

2. Google Search spam policies
   https://developers.google.com/search/docs/essentials/spam-policies
   - Doorway abuse y scaled content abuse cubren páginas creadas principalmente para capturar consultas similares sin valor independiente suficiente.

No existe una guía de Google que diga que toda web de autor deba tener una página “reading order”.

## Evidencia del proyecto

- `work-samuel` y `work-manecillas` son entradas separadas del registry bajo `works-hub`.
- No están modeladas como episodios/volúmenes de una misma `BookSeries`.
- `/libros/` ya permite comparar/descubrir obras.
- `/empieza-aqui/` ya es el punto de orientación humana.
- La información de Search Console aportada en la auditoría reciente mostró consultas como “david porto”, “portal fantasy” y “noveris”; no se aportó evidencia de demanda “orden de lectura”.
- Una búsqueda web exploratoria de “David Porto Díaz orden de lectura” / “Samuel entre mundos orden de lectura” no encontró una necesidad clara asociada al autor. Esto **no sustituye GSC**, pero tampoco aporta una señal para construir la URL.

## Cuándo sí tendría sentido

Reabrir A.8 solo si aparece uno de estos triggers:

1. se publica una secuela/precuela de Samuel con orden recomendado;
2. existe una `BookSeries` real con 2+ volúmenes y orden factual;
3. Search Console registra consultas significativas/recurrentes preguntando por orden;
4. lectores reales preguntan repetidamente por dónde empezar y `/empieza-aqui/` no resuelve bien la tarea;
5. el catálogo crece lo suficiente para que haya itinerarios genuinos (no inventados).

## Qué haría entonces

No crear una página por fórmula SEO. Primero decidir si basta con mejorar `/libros/` o `/empieza-aqui/`.

Si una URL propia está justificada:

```text
/orden-de-lectura/
```

Contenido mínimo legítimo:

- respuesta directa al orden real;
- explicación de independencia/dependencia entre libros;
- enlaces canónicos a cada obra;
- estado de publicación real;
- sinopsis diferencial breve;
- aclaración cuando el orden sea opcional.

Structured data:

- `ItemList` si aporta claridad;
- `Book` referenciando entidades existentes;
- `BookSeries` solo si la serie existe realmente;
- nunca inventar `position` narrativa si los libros son independientes.

## Alternativa mejor hoy

Mejorar `/empieza-aqui/` con decisiones reales de descubrimiento, por ejemplo:

```text
Si buscas fantasía juvenil y portal fantasy → Samuel entre mundos
Si buscas una novela coral sobre memoria/tiempo → Las manecillas del recuerdo
```

Solo si esos posicionamientos están respaldados por la información canónica del libro. Esto resuelve “¿por dónde empiezo?” sin fingir que existe un orden cronológico.

## Tests si se activa en el futuro

- la URL solo entra en registry/sitemap cuando existe trigger documentado;
- todos los libros enlazados existen/canonicalizan correctamente;
- `BookSeries` solo se usa con una serie factual;
- ItemList y orden visible coinciden;
- no duplicar contenido de `/libros/`;
- internal graph sin canibalización/huérfanas;
- query intent y propósito editorial registrados en el PR.

## Qué NO hacer

- crear “orden de lectura” porque es una keyword habitual para otros autores;
- afirmar que Samuel debe leerse antes que Manecillas;
- llamar saga a obras independientes;
- generar páginas tipo “por dónde empezar”, “orden de libros”, “orden de novelas” con contenido casi idéntico;
- añadir schema de serie ficticia;
- llenar la página con sinopsis duplicadas para alcanzar longitud.

## Coste / beneficio

Ahora:
- beneficio: bajo/no demostrado;
- riesgo de thin/duplicative content: medio;
- coste de mantenimiento/otra URL: innecesario.

Con saga real/demanda demostrada:
- beneficio potencial: alto y legítimo.

## Definition of Done

- [x] confirmar que las obras actuales no requieren orden documentado;
- [x] comprobar que ya existen `/libros/` y `/empieza-aqui/`;
- [ ] no crear URL ahora;
- [ ] registrar trigger futuro si aparece serie/demanda;
- [ ] si el problema es “por dónde empiezo”, evaluar primero mejorar `empieza-aqui`.

## Recomendación de merge

**MERGE como `DEFER`.** Evita crear contenido artificial hoy y deja criterios objetivos para reabrir la idea cuando el catálogo realmente lo necesite.