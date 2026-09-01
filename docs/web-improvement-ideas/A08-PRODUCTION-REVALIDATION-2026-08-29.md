# A.8 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #157  
Decisión operativa: **REJECT · NO_CODE · NO_FAKE_SERIES_INTENT**

## Decisión cerrada

No se crea una página “orden de lectura” para David Porto Díaz, Samuel entre mundos y Las manecillas del recuerdo.

Hoy no existe una serie/saga que requiera ordenar esos libros. Crear la URL para capturar una keyword potencial sería publicar una respuesta a una pregunta que el propio catálogo no plantea.

## Evidencia del repo actual

### Catálogo

`/libros/` presenta dos obras en un `ItemList`:

1. `Las manecillas del recuerdo`;
2. `Samuel entre mundos`.

Cada entrada es un `Book` independiente con su propia ficha, ISBN/editorial/fecha y URL. No existe una relación `BookSeries`, volumen, posición de saga ni dependencia de lectura entre ambas.

### Búsqueda estructural

En `main`:

```text
BookSeries        → 0 resultados
"orden de lectura" → 0 resultados
"saga"             → 0 resultados
```

No hay, por tanto, dato canónico que una página de orden de lectura pudiera proyectar.

### Discovery humano ya existente

`/empieza-aqui/` responde la necesidad real de orientación del sitio:

- obra actual;
- fantasía;
- autor;
- lecturas;
- herramientas;
- prensa.

Su mensaje explícito es “¿Por dónde empiezas?” y permite elegir según intención, no según una secuencia narrativa inexistente.

`/libros/` ya funciona como hub canónico de Obras y enlaza directamente las fichas publicadas.

## Por qué no se crea una URL preventiva

Una página “orden de lectura” tendría actualmente una de estas formas, todas peores que el estado actual:

- “puedes leer cualquiera primero” → contenido demasiado fino y redundante con `/libros/`;
- poner Manecillas antes que Samuel por ser obra actual → confundir prioridad editorial con continuidad narrativa;
- poner Samuel antes que Manecillas por fecha de publicación → confundir cronología bibliográfica con orden de saga;
- inventar una conexión temática suficiente para hablar de “universo” → dato falso;
- usar la página como keyword landing → intención artificial sin contenido sustancial.

No se crea arquitectura por anticipación a un catálogo futuro.

## Relación con A.2

A.2 ya cerró la regla de hubs canónicos:

- `/libros/` representa Obras;
- cada libro tiene su ficha canónica;
- se evita crear una segunda URL equivalente sin intención propia.

A.8 sigue exactamente esa arquitectura. Una página de orden solo se justifica cuando el orden sea una entidad/intención distinta y real.

## Structured data

No se introduce `BookSeries` mientras no exista una serie real y verificable.

La ausencia de `BookSeries` no es un “schema gap”; es una representación correcta del catálogo actual.

## Alternativas descartadas

1. **Página “orden de lectura” con dos libros independientes** — thin/redundante.
2. **Orden por fecha de publicación** — no equivale a orden narrativo.
3. **Orden por prioridad comercial** — no equivale a saga.
4. **`BookSeries` preventivo** — afirmaría una relación editorial inexistente.
5. **Página por keyword antes de demanda real** — arquitectura sin necesidad humana demostrada.
6. **Duplicar `/empieza-aqui/`** — ya existe una superficie de orientación más útil.

## Trigger de reapertura

A.8 solo vuelve a desarrollo cuando exista al menos una de estas condiciones:

- una saga/serie real con dos o más entregas y orden de lectura confirmado;
- un `BookSeries` editorial verdadero que merezca página propia;
- precuelas, relatos o spin-offs cuya secuencia pueda confundir legítimamente;
- consultas reales/repetidas de lectores o Search Console preguntando por orden;
- un catálogo suficientemente amplio donde “qué leer primero” sea una decisión distinta de “qué libros existen”.

En ese momento la página debe responder primero a la necesidad humana y derivar sus relaciones desde datos canónicos; no se crea para cumplir una receta SEO.

## Definition of Done

- [x] historia de #135 preservada;
- [x] `main@291c8c6…` revalidado;
- [x] catálogo actual inspeccionado;
- [x] `BookSeries` ausente y correctamente ausente;
- [x] “orden de lectura” ausente;
- [x] “saga” ausente;
- [x] `/libros/` confirmado como hub de Obras;
- [x] `/empieza-aqui/` confirmado como orientación humana;
- [x] thin page/keyword landing descartadas;
- [x] triggers futuros definidos;
- [x] no existe cambio de runtime neto.

**Conclusión:** A.8 sigue siendo `REJECT`. La web no necesita una página que explique el orden de dos libros que no forman una serie. Si el catálogo cambia, se reabre con hechos nuevos; hoy crearla degradaría claridad y arquitectura.