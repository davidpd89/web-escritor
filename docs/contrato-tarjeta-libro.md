# Contrato de la tarjeta y la ficha de libro

Todas las tarjetas del catálogo (`/recomendaciones/`) y todas las fichas (`/recomendaciones/libros/<slug>/`) se generan con la misma plantilla a partir de los datos de Amazon y del catálogo. No hay ajustes a mano por libro: si un libro no encaja, se corrige el dato o la regla, nunca la página.

Los límites están en un único sitio, `scripts/build-reading-catalogue.py`, junto a `tags()`:

| Constante | Valor | Qué fija |
|---|---|---|
| `CARD_TAGS` | 2 | Etiquetas en la tarjeta (las más informativas: género, temporada, temática, época, contenido; sin edad) |
| `DETAIL_TAGS` | 8 | Etiquetas en la ficha, con el mismo orden de prioridad |
| `CARD_TITLE_CHARS` | 44 | Título de tarjeta: cabe en 2 líneas; si no, variante corta o corte por palabra con «…» |
| `CARD_SYNOPSIS` | 200 | Descripción de tarjeta sin distintivo |
| `CARD_SYNOPSIS_BADGE` | 150 | Descripción de tarjeta con distintivo, para que todas las tarjetas midan lo mismo |
| `NOVELTY_DAYS` | 30 | Ventana de «Novedad» |

## Distintivo

- **Próximamente**: la fecha de publicación es posterior a hoy.
- **Novedad**: se publicó entre hoy y 30 días atrás.
- **Nada**: se publicó hace más de 30 días.

«Hoy», en la generación, es la última `fecha_actualizacion` del catálogo (`data_anchor`), no el reloj. Así, dos generaciones con los mismos datos dan las mismas páginas. En el navegador, `assets/reading-catalogue.js` recalcula el distintivo cada día con la misma ventana de 30 días, de modo que una página antigua no muestra «Novedad» de más.

## Contenido fijo de la tarjeta

Cada tarjeta lleva siempre, en este orden:

1. Portada.
2. Distintivo, si lo hay.
3. Título en 2 líneas como máximo; el título completo va en `aria-label`.
4. Autoría y editorial enlazadas.
5. Páginas.
6. Dos etiquetas como máximo.
7. Descripción.
8. Cuatro casillas de formato: tapa dura, tapa blanda, Kindle y audiolibro, con precio, «Ver precio» o ✕.
9. Botones «Comprar» y «Ver ficha».

Comprar y la casilla del formato principal usan el mismo enlace de Amazon (`amazon_destination`).

## Comprobación y cuarentena

`tests/test_reading_card_contract.py` comprueba dos cosas:

- las reglas, sobre casos límite;
- todas las tarjetas publicadas: título, dos etiquetas como máximo, cuatro casillas de formato y «Ver ficha».

Si un libro incumple el contrato, la prueba falla y nombra el libro, y hay que corregir su dato. (Pendiente: apartar ese libro automáticamente en cuarentena para que el resto del lote se publique igualmente.) Las fichas usan las mismas reglas, con `DETAIL_TAGS` en lugar de `CARD_TAGS`.

Las páginas de autor y de editorial también llaman a `tags()`, pero sin tope: ahí se listan todos los temas del autor o de la editorial.
