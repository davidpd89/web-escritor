# ISNI — David Porto Díaz

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · FREE_BNE_ROUTE_CONFIRMED · READY_FOR_DIRECT_AUDIT`

## Objetivo

Comprobar si David Porto Díaz ya dispone de ISNI y, si no existe, tramitarlo por una vía institucional gratuita que mejore la desambiguación del autor entre catálogos, bibliotecas y grafos de identidad.

## Vía gratuita confirmada

La Biblioteca Nacional de España confirma que tramita solicitudes ISNI escribiendo a `isni@bne.es` para:
- autores o entidades españolas o que trabajan en España;
- autores o entidades presentes en el catálogo de la BNE.

Fuente oficial:
- https://www.bne.es/es/preguntas-frecuentes/como-puedo-conseguir-isni

La BNE indica que la identificación de una identidad pública utiliza, entre otros datos, nombre, fecha/lugar cuando proceda, categoría y función, una obra de referencia y una URI pública.

No necesitamos contratar una agencia comercial si la BNE admite la solicitud.

## Paquete de identidad preparado

- Nombre: David Porto Díaz
- Función: escritor / autor
- Nacido en Pontevedra; residente en Madrid
- Web oficial: https://davidportodiaz.com/
- ORCID: 0009-0005-9089-3782
- Wikidata: Q139678851
- Amazon Author: B0GZFP1JV3
- Goodreads Author: 66843136

Obras de referencia:
- `Samuel entre mundos` — ISBN 9791387659776 — Libros Indie — 2025
- `Las manecillas del recuerdo` — papel ISBN 9798905149351 — Monza Ediciones — 2026
- `Las manecillas del recuerdo` — ebook ISBN 9798906781925 — Monza Ediciones — 2026

## Procedimiento

1. Buscar primero en ISNI por nombre y variantes.
2. Desambiguar cada candidato mediante obras, país, función y URLs asociadas.
3. Revisar posibles registros duplicados.
4. Si existe un ISNI inequívoco, guardar ID/URL y revisar sus datos públicos.
5. Si no existe, coordinar con #422 BNE y enviar la solicitud a la BNE con el paquete de identidad anterior y las fuentes públicas que solicite.
6. No incluir datos privados innecesarios en Git ni en comentarios públicos de la PR.
7. Una vez confirmado el ISNI, añadirlo a Wikidata y a `Person.sameAs` de la web si procede.
8. Comprobar posteriormente VIAF/BNE/WorldCat para detectar propagación/enlaces.

## Qué NO hacer

- No pagar por un ISNI mientras exista la vía BNE aplicable.
- No aceptar un ISNI solo por coincidencia de nombre.
- No inventar fecha de nacimiento completa u otros datos no publicados.
- No crear otro identificador si ya existe uno correcto.

## Criterio de cierre

`ISNI_SEARCHED · DUPLICATES_REVIEWED · ISNI_CONFIRMED_OR_BNE_REQUEST_SUBMITTED · PUBLIC_ID_VERIFIED · WIKIDATA_SITE_UPDATED_IF_APPLICABLE · NO_PAID_REGISTRATION`

## Nota de intento (2026-09-08)

Se intentó el paso 1 (búsqueda directa en isni.org) esta noche: el buscador
público de isni.org está protegido por un challenge de Cloudflare
("Verifique que es un ser humano"), que un navegador automatizado no debe
completar — es exactamente el tipo de verificación anti-bot que no hay que
sortear. La búsqueda directa en isni.org requiere, por tanto, hacerse
manualmente desde un navegador humano.

No cambia el resto del análisis: la vía BNE (`isni@bne.es`) sigue siendo el
camino recomendado si no aparece un ISNI ya existente, y sigue siendo un
correo que el propio autor debería enviar o autorizar explícitamente, no
algo para automatizar.
