# D.7 · Vista previa enriquecida al pasar el cursor

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `REJECT`.

## 1. Hipótesis original

Mostrar portada + sinopsis al hacer hover sobre libros/recomendaciones en desktop para permitir exploración más rápida sin navegar.

## 2. Evolución en #135

### Revisión → `REJECT`

La primera revisión concluye que el patrón:

- es desktop-only;
- aumenta complejidad;
- introduce desigualdad touch/hover;
- no responde a una necesidad UX prioritaria.

### Matriz → `DEFERIR`

La matriz mantiene la crítica:

> «Hover preview desktop aporta poco frente al coste responsive/a11y y no ayuda móvil.»

### Autoridad final → `REJECT`

> «Hover preview desktop-only no compensa coste responsive/a11y y no ayuda móvil.»

### Revalidación independiente

La falsación final menciona expresamente Reader Mode/hover/share-selection como ideas que no compensan.

## 3. Problema principal: equivalencia entre modalidades

Una interacción esencial que solo aparece con hover crea dos experiencias:

```text
mouse desktop → preview
keyboard/touch/mobile → no preview o comportamiento distinto
```

Para hacerla equivalente habría que añadir:

- focus preview;
- tap/close state;
- gestión de overlays;
- Escape;
- posicionamiento responsive;
- prevención de clipping;
- lectura por AT;
- manejo de pointer coarse/fine.

Ese coste supera el beneficio actual.

## 4. No confundir con previews deliberadas existentes

El shell actual de «Explorar» contiene un panel de preview dentro de un diálogo controlado. Eso no rehabilita D.7:

- es una interfaz explícita de navegación;
- no depende únicamente de hover;
- tiene trigger/diálogo propio;
- no convierte listados de libros/recomendaciones en superficies hover.

D.7 trata un patrón adicional de preview al pasar el cursor sobre listados.

## 5. Alternativas más robustas

Antes de preview:

- título claro;
- subtítulo/descriptor breve;
- portada relevante;
- metadata suficiente;
- CTA/descripción visible;
- destino canónico rápido;
- tarjetas/listas que funcionen igual con mouse, touch y teclado.

Si una sinopsis es necesaria para decidir, puede estar visible sin interacción oculta.

## 6. Accesibilidad

Riesgos típicos del hover content:

- contenido que aparece/desaparece inesperadamente;
- imposibilidad de mantener hover al mover puntero;
- foco no sincronizado;
- overlay que tapa contenido;
- teclado sin equivalente;
- magnificación/zoom con clipping;
- lector de pantalla que encuentra contenido duplicado u oculto.

No añadir una interacción compleja sin una necesidad que lo justifique.

## 7. Móvil

D.7 falla especialmente en móvil porque no existe hover persistente. Un sustituto por tap convierte una acción simple de navegar en un flujo de dos toques y requiere estado adicional.

La regla del proyecto debe ser:

```text
acción principal funciona con tap directo
> preview auxiliar que interfiere con navegación
```

## 8. Performance

Previews con imágenes/sinopsis pueden:

- precargar assets que el usuario no necesita;
- aumentar DOM;
- añadir listeners;
- provocar layout work;
- perjudicar móvil aunque el feature se «oculte» visualmente.

No cargar datos/assets de hover solo para desktop sin evidencia de retorno.

## 9. Qué NO hacer

- hover cards globales;
- tooltip con sinopsis larga;
- duplicar toda la ficha del libro en DOM oculto;
- cargar imágenes high-res al hover;
- requerir segundo tap en móvil;
- crear comportamiento distinto para teclado;
- usar hover preview como argumento de «sitio premiable» sin utilidad.

## 10. Gate excepcional de reapertura

Aunque el estado es `REJECT`, podría reevaluarse si:

- hay un listado mucho más denso;
- usuarios necesitan comparar sin perder contexto;
- diseño funciona igualmente con mouse/teclado/touch;
- preview aporta información que no cabe visible;
- performance y a11y se prueban;
- testing demuestra reducción real de fricción.

No reabrir por tendencia visual.

## 11. Relación con C.8/D.6

- C.8 orienta mediante rutas explícitas.
- D.6 rechaza un quiz general artificial.
- D.7 tampoco debe añadir una capa de interacción si la arquitectura visible ya permite decidir.

## 12. Pasadas posteriores revisadas

Cuarta–decimoquinta: ninguna cambia D.7. La revalidación independiente reafirma explícitamente que hover preview no compensa.

## 13. Trazabilidad

- idea original;
- revisión `REJECT`;
- matriz `DEFERIR`;
- autoridad final `REJECT`;
- revalidación independiente;
- shell actual revisado para evitar confundir su panel «Explorar» con la idea.

## 14. Definition of Done de esta reconstrucción

- [x] motivo del rechazo preservado;
- [x] desktop/touch/keyboard analizados;
- [x] preview actual del shell diferenciado;
- [x] alternativas visibles documentadas;
- [x] sin implementación.

## Recomendación para Clara/Claude

No implementar D.7. Mantener información suficiente visible y navegación directa; reevaluar solo si un catálogo/listado futuro demuestra una necesidad comparativa real.