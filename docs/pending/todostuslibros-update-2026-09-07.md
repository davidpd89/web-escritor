# TodosTusLibros — actualización operativa 2026-09-07

Complementa `todostuslibros.md` con los datos vigentes tras los últimos cambios de producción.

## Datos actuales

### Samuel entre mundos

- ISBN `9791387659776`
- Libros Indie
- 422 páginas según autoridad actual del proyecto
- TodosTusLibros ya muestra un registro público asociado a Libros Indie

Discrepancia pendiente: algunos retailers muestran 412 páginas. Resolver en #429/#404 antes de alterar la web.

### Las manecillas del recuerdo · papel

- ISBN `9798905149351`
- Monza Ediciones
- publicación `2026-09-03`
- 272 páginas según autoridad actual del proyecto
- **PVP actual: 15,99 €**

Los snapshots externos de 16,00 € se clasifican como datos históricos/downstream hasta verificar qué PVP transmite el owner editorial.

### Kindle

- ISBN `9798906781925`
- ASIN `B0HHM71F46`
- publicación `2026-08-12`
- precio actual 2,99 €

## Qué debe hacer Claude en la sesión real

1. Buscar exactamente los tres ISBN en TodosTusLibros.
2. Capturar URL estable de cada resultado real.
3. Verificar título, autor, editorial, formato, páginas, fecha y portada.
4. Tratar precio/stock como snapshot, no como metadata fija.
5. Si falta Manecillas, comprobar antes #404 DILVE / #428 Monza.
6. Si aparece después de propagación, comprobar que la ficha no sea duplicada.
7. Comparar nombre de autor con el feed upstream: `DAVID, PORTO DÍAZ` puede ser serialización bibliográfica y no un bug visual.

## Oportunidad para la web

Si la ficha de Manecillas papel aparece con URL estable, correcta y útil para localizar librerías españolas, valorar añadirla como destino secundario tipo **“Buscar en librerías”** en la ficha del libro o zona de compra.

Condiciones:

- no sustituye el CTA principal de Amazon físico `https://amzn.to/4zW6Yeu`;
- no se presenta como stock garantizado;
- no se añade hasta verificar la URL definitiva;
- si se incorpora a `Book.sameAs`, comprobar que la URL represente inequívocamente la misma edición/ISBN.

Esto puede mejorar utilidad para lectores que prefieran librería física y reforzar la coherencia de entidad/bibliografía sin sacrificar el funnel principal.

## Regla de corrección

`publisher/distribuidor → DILVE/ISBN → TodosTusLibros → retailer`

No al revés.

## Cierre actualizado

- `SAMUEL_RECORD_VERIFIED`
- `MANECILLAS_PAPER_RECORD_VERIFIED_OR_UPSTREAM_PENDING`
- `MANECILLAS_EBOOK_STATE_RECORDED`
- `PAGE_COUNT_RECONCILED_OR_EXTERNAL_DEPENDENCY_RECORDED`
- `PVP_DISCREPANCY_RECONCILED`
- `DUPLICATES_REVIEWED`
- `OPTIONAL_SITE_LINK_DECIDED`
