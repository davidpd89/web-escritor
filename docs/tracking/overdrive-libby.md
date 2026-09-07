# OverDrive / Libby — bibliotecas digitales

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · PUBLISHER_DISTRIBUTION_MODEL_CONFIRMED · MANECILLAS_PUBLISHER_DEPENDENCY · READY_FOR_CATALOG_AUDIT`

## Objetivo

Comprobar si `Las manecillas del recuerdo` y, cuando exista una edición digital legítima, `Samuel entre mundos` están disponibles para adquisición por bibliotecas mediante OverDrive/Libby, y determinar si Monza/Libros Indie pueden habilitar esa distribución sin coste para David.

No abrir una distribución paralela ni aceptar un agregador de pago solo por aparecer en Libby.

## Qué es útil aquí

OverDrive declara actualmente:

- más de **30.000 publishers/content partners**;
- una red de alrededor de **92.000 bibliotecas, escuelas, universidades y organizaciones**;
- alcance en **115 países** y más de 100 idiomas;
- Libby como app de lectura para bibliotecas públicas/académicas/corporativas;
- Sora para centros educativos;
- merchandising/promoción sin coste dentro de su ecosistema para partners y títulos disponibles.

Fuentes oficiales:

- https://company.overdrive.com/publishers/
- https://company.overdrive.com/publisher-inquiry/
- https://company.overdrive.com/contact/partner-support/

Esto sí puede aumentar descubrimiento y lectura institucional, pero el canal de entrada es editorial/distribución, no un perfil social de autor.

## Modelo de distribución actual

OverDrive trabaja mediante:

1. acuerdo de distribución con publisher/content provider;
2. onboarding de contenidos y metadata;
3. catálogo en OverDrive Marketplace;
4. adquisición por bibliotecas/centros;
5. lectura mediante Libby/Sora.

La propia OverDrive presenta el contacto como `Publisher Inquiry` y `Partner support`.

### Consecuencia para David

No intentar abrir una segunda cadena de distribución personal si Monza o Libros Indie controlan los derechos digitales correspondientes.

Primero identificar el **owner real** de la edición digital y su distribuidor.

## Estado por obra

### Las manecillas del recuerdo

Existe ebook legítimo publicado por Monza:

- ISBN `9798906781925`
- ASIN `B0HHM71F46`
- publicación 2026-08-12
- idioma español

Esta es la prioridad de la PR.

Claude debe preguntar/confirmar en #428:

- si Monza distribuye a OverDrive;
- si su agregador actual ofrece canal bibliotecas;
- si el ISBN digital ya aparece en OverDrive Marketplace/Libby;
- si puede habilitarse sin coste para David y sin conflicto contractual.

### Samuel entre mundos

El proyecto no tiene actualmente una edición ebook autorizada/documentada equivalente.

Por tanto:

- no inventar un ebook;
- no convertir el PDF/EPUB promocional, si existiera, en una edición comercial;
- solo revisar OverDrive si Libros Indie confirma una edición digital real o un derecho de distribución aplicable.

## Auditoría de catálogo

Buscar por:

- `9798906781925`;
- `Las manecillas del recuerdo`;
- `David Porto Díaz`.

Si el catálogo público visible depende de biblioteca/territorio:

- usar una biblioteca real disponible para consulta;
- no concluir `ABSENT` solo porque una biblioteca concreta no lo haya comprado;
- distinguir `TITLE_IN_OVERDRIVE_MARKETPLACE` de `OWNED_BY_THIS_LIBRARY`.

Estados útiles:

- `TITLE_AVAILABLE_TO_LIBRARIES`
- `TITLE_NOT_OBSERVED`
- `LIBRARY_HAS_LICENSE`
- `LIBRARY_DOES_NOT_OWN_TITLE`
- `PUBLISHER_DISTRIBUTION_NOT_ENABLED`
- `PUBLISHER_DEPENDENCY`

## Metadata a revisar si aparece

- título;
- autor/contributor;
- ISBN;
- publisher;
- idioma;
- portada;
- descripción;
- subjects/categories;
- fecha;
- formato EPUB/ebook;
- territorios/licensing model si se expone.

No congelar precio/licencia institucional en nuestra web: puede variar por modelo y biblioteca.

## Oportunidad de bibliotecas

Una vez confirmado que Manecillas **está disponible para compra institucional** en OverDrive:

- documentar la ficha/ID;
- valorar solicitudes de adquisición a bibliotecas concretas únicamente mediante sus canales normales;
- priorizar bibliotecas relacionadas con Madrid/Pontevedra y clubes de lectura si existe encaje;
- no enviar solicitudes masivas ni pedir a lectores que saturen bibliotecas.

La adquisición por una biblioteca no garantiza ventas directas, pero puede ampliar lectura, descubrimiento y futuras recomendaciones.

## Lo que NO haremos

- pagar un agregador solo por entrar en OverDrive;
- abrir Draft2Digital/Kobo u otra distribución si choca con Monza;
- subir un archivo del libro sin autorización;
- crear una edición digital de Samuel que no exista;
- afirmar que el libro está en `Libby` porque OverDrive acepte publishers;
- confundir Marketplace con disponibilidad concreta en cada biblioteca.

## Secuencia para Claude

1. Buscar Manecillas por ISBN/título.
2. Confirmar con Monza owner/distribuidor digital.
3. Preguntar si OverDrive está habilitado o disponible en el contrato/feed actual.
4. Si ya está: auditar metadata y registrar ficha/ID.
5. Si no está pero Monza puede habilitarlo sin coste para David: solicitarlo mediante publisher/distributor.
6. Si requiere gasto o conflicto contractual: `NO_GO` y documentar.
7. Para Samuel, solo continuar si Libros Indie confirma ebook/distribución legítimos.
8. Tras activación, comprobar disponibilidad en una muestra razonable de bibliotecas y guardar evidencia.

## Posible cambio en la web

No añadir un CTA `Leer en Libby` hasta que exista una URL/availability real y estable.

Si la edición queda disponible institucionalmente, valorar una mención secundaria en la ficha del libro o página de bibliotecas/clubes, sin desplazar compra/fragmento.

## Prioridad

`P1/P2` para Manecillas si Monza ya dispone del canal; `NO_GO por ahora` para Samuel si no existe ebook autorizado.

## Criterio de cierre

`MANECILLAS_OVERDRIVE_STATE_VERIFIED · PUBLISHER_DISTRIBUTION_OWNER_IDENTIFIED · METADATA_AUDITED_IF_PRESENT · ZERO_OUT_OF_POCKET_COST_CONFIRMED_OR_NO_GO · SAMUEL_DIGITAL_STATUS_DOCUMENTED · LIBRARY_AVAILABILITY_NOT_CONFUSED_WITH_MARKETPLACE · WEB_LINK_ADDED_ONLY_IF_REAL`
