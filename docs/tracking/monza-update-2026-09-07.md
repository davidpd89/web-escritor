# Monza Ediciones — delta operativo 2026-09-07

Este suplemento prevalece sobre valores antiguos del runbook `docs/tracking/monza-ediciones.md` cuando haya discrepancia.

## Datos vigentes de Manecillas

### Papel
- título: `Las manecillas del recuerdo`
- autor: David Porto Díaz
- editorial: Monza Ediciones
- ISBN: 9798905149351
- ASIN: B0HHY9MYLM
- publicación: 2026-09-03
- PVP vigente usado por producción/Amazon: **15,99 €**
- páginas actuales de la autoridad del proyecto: **272**

### Kindle
- ISBN: 9798906781925
- ASIN: B0HHM71F46
- publicación: 2026-08-12
- precio vigente/canónico actual: **2,99 €**

## Discrepancias a resolver con Monza

1. Páginas físico: 272 en web/proyecto frente a 266 en alguna ficha comercial.
2. PVP físico: 15,99 € vigente frente a snapshots de 16,00 € en retailers.
3. Identificar registrant real de ambos ISBN 979-8.
4. Identificar owner de DILVE/ONIX/feeds de papel y ebook.
5. Confirmar portada, sinopsis, dimensiones, formato, idioma, Thema/BISAC y distribución que se están enviando.

No corregir downstream por intuición. Orden de autoridad:
`ejemplar final / metadata Monza → owner DILVE/ONIX → retailers/bibliotecas → web propia si nuestra autoridad estaba equivocada`.

## Oportunidad externa útil

Si Monza dispone de ficha pública de libro/autor, solicitar cuando sea editorialmente razonable:
- nombre canónico `David Porto Díaz`;
- bio/foto actualizadas;
- ficha completa de Manecillas;
- enlace a `https://davidportodiaz.com/las-manecillas-del-recuerdo/` o a la web oficial del autor;
- press kit cuando aporte utilidad.

## Entregable para Monza

Preparar una sola matriz:
`campo | valor publicado | valor correcto | evidencia | owner técnico | destinos afectados`

Evitar correos separados a Amazon/Casa/Agapea/TSL si todos heredan el mismo error upstream.

## Dependencias
- #404 DILVE
- #406 ISBN
- #407 TodosTusLibros
- #410 retailers
- #396 Amazon Author Central
- #469 LibraryThing Early Reviewers, si Monza autoriza review copy completa
