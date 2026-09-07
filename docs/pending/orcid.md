# ORCID — identidad pública y obras

Fecha de investigación: **2026-09-07**  
PR owner: **#408 · `tracking/orcid`**  
Estado: **RESEARCHED · RECORD_ID_CONFIRMED · READY_FOR_AUTHENTICATED_EXECUTION**

## Objetivo

Usar ORCID como una autoridad pública machine-readable adicional para **David Porto Díaz**, sin forzar un uso académico artificial.

El objetivo útil es que nombre, web, bio, keywords, enlaces y obras publicadas sean coherentes, públicos cuando interese y consumibles por sistemas externos.

ORCID actual:

- https://orcid.org/0009-0005-9089-3782

## Identidad canónica preparada

- Nombre: **David Porto Díaz**
- ORCID iD: `0009-0005-9089-3782`
- Web oficial: `https://davidportodiaz.com/`
- Wikidata: `https://www.wikidata.org/wiki/Q139678851`
- Amazon Author: `https://www.amazon.es/stores/author/B0GZFP1JV3`
- Goodreads: `https://www.goodreads.com/author/show/66843136.David_Porto_D_az`

La web oficial ya incluye ORCID en `Person.sameAs`; no hace falta tocar código antes de comprobar la cuenta real.

## Qué permite ORCID actualmente

ORCID permite añadir:

- nombre/publicado como;
- otras variantes de nombre;
- país/región;
- keywords;
- websites/social links;
- bio breve;
- obras;
- afiliaciones/professional activities cuando proceda;
- distintos niveles de visibilidad por ítem.

Fuentes oficiales:

- https://support.orcid.org/hc/en-us/articles/360006973673-Add-identifying-biographical-information-to-your-ORCID-record
- https://support.orcid.org/hc/en-us/articles/360006973833-Add-links-to-personal-websites-to-your-ORCID-record
- https://support.orcid.org/hc/en-us/articles/360006971533-Add-keywords-to-your-ORCID-record

## Visibilidad y utilidad machine-readable

ORCID ofrece tres niveles:

- Everyone;
- Trusted parties;
- Only me.

Los datos marcados **Everyone** pueden verse públicamente, consumirse mediante la API pública y formar parte del public data file anual.

Para nuestro objetivo de identidad pública interesa que estén en `Everyone`, salvo razón de privacidad:

- nombre;
- bio;
- web oficial;
- links públicos seleccionados;
- keywords relevantes;
- obras que queramos usar como autoridad pública.

Emails pueden mantenerse privados. No convertir ORCID en un directorio de datos personales.

Fuente:

- https://support.orcid.org/hc/en-us/articles/360006897614-Visibility-settings

## Bio preparada

Versión recomendada, breve y factual:

> David Porto Díaz es un escritor español nacido en Pontevedra y residente en Madrid. Es autor de *Samuel entre mundos* (Libros Indie, 2025), novela de fantasía juvenil ambientada en Noveris, y de *Las manecillas del recuerdo* (Monza Ediciones, 2026). En 2026 obtuvo el Primer Premio del XII Certamen de Microrrelatos «De amor» de Letras Como Espada y fue finalista del I Premio de Literatura Infantil Juan Andrés Teno. Su web oficial es davidportodiaz.com.

ORCID admite bio en texto plano y hasta 5.000 caracteres, pero no necesitamos usar el máximo.

Fuente:

- https://support.orcid.org/hc/en-us/articles/360006971513-Add-a-biography-to-your-ORCID-record

Antes de publicar, verificar formulación de premios con la autoridad actual del proyecto, igual que en Goodreads/Wikidata.

## Keywords recomendadas

No meter 30 términos SEO. Usar conceptos reales y coherentes:

- escritor
- ficción especulativa
- fantasía
- fantasía juvenil
- portal fantasy
- worldbuilding
- escritura creativa
- novela coral
- memoria

ORCID permite múltiples keywords y las usa también como campo de búsqueda del Registry.

Fuente:

- https://support.orcid.org/hc/en-us/articles/360006971533-Add-keywords-to-your-ORCID-record

## Websites / social links

ORCID permite enlaces ilimitados, cada uno con su propia visibilidad.

Orden recomendado:

1. Web oficial — `https://davidportodiaz.com/`
2. Wikidata — `https://www.wikidata.org/wiki/Q139678851`
3. Amazon Author — `https://www.amazon.es/stores/author/B0GZFP1JV3`
4. Goodreads — perfil canónico
5. LinkedIn — si el perfil actual es el oficial

No hace falta replicar absolutamente cada red social de la web. Priorizar autoridades/identidad, no volumen.

Fuente:

- https://support.orcid.org/hc/en-us/articles/360006973833-Add-links-to-personal-websites-to-your-ORCID-record

## Regla importante: `Other identifiers`

No intentar escribir manualmente Goodreads ID, Amazon Author ID o Wikidata QID dentro de `Other identifiers` como si fueran identificadores ORCID verificados.

ORCID documenta que los **person identifiers** de esa sección solo pueden ser añadidos por trusted organizations/import tools.

Por tanto:

- Goodreads/Amazon/Wikidata → website links públicos si interesa;
- ISNI/Scopus/etc. → solo si una integración/trusted organization los añade por el canal correcto.

Fuente:

- https://support.orcid.org/hc/en-us/articles/360006894854-Add-person-identifiers-other-identifiers-to-your-ORCID-record

## Obras: ORCID sí soporta libros

ORCID soporta actualmente el work type **Book**. No hay que registrar las novelas como `Other` ni como artículo.

Fuente:

- https://info.orcid.org/ufaqs/what-work-types-does-orcid-support/

### Samuel entre mundos

Datos preparados:

- Work type: `Book`
- Title: `Samuel entre mundos`
- Publisher: `Libros Indie`
- Publication date: `2025` (usar fecha más precisa solo si la edición/owner la confirma)
- External identifier type: `ISBN`
- External identifier value: `9791387659776`
- Relationship: `Self`
- Work URL: `https://davidportodiaz.com/libros/samuel-entre-mundos/`
- Language: Spanish/es
- Visibility: Everyone

No copiar a ORCID fecha contradictoria de un retailer sin resolver antes la autoridad bibliográfica.

### Las manecillas del recuerdo — papel

- Work type: `Book`
- Title: `Las manecillas del recuerdo`
- Publisher: `Monza Ediciones`
- Publication date: `2026-09-03`
- External identifier: ISBN `9798905149351`
- Relationship: `Self`
- Work URL: `https://davidportodiaz.com/las-manecillas-del-recuerdo/`
- Language: Spanish/es
- Visibility: Everyone

Número de páginas: 272 es el dato canónico actual del proyecto, pero ORCID no necesita páginas para que el registro sea útil. No forzarlo si la UI no lo pide.

### Las manecillas del recuerdo — Kindle

Datos:

- ISBN `9798906781925`
- ASIN `B0HHM71F46`
- publicación: `2026-08-12`
- publisher: `Monza Ediciones`

La sesión debe comprobar cómo representa ORCID las distintas versiones/ediciones de un mismo libro en la UI actual.

ORCID agrupa works cuando comparten identificadores; aquí papel y Kindle tienen ISBN distintos. No crear una duplicación confusa solo por rellenar ambos formatos.

Opciones aceptables:

1. una entrada principal de la obra/edición papel con su ISBN, si es la representación más clara;
2. dos entradas si la UI permite distinguirlas de forma inequívoca y resulta útil;
3. usar `Version of` solo si el modelo de identificadores de ORCID encaja realmente con esa relación, no por intuición.

No usar ASIN como sustituto de ISBN si ORCID no lo ofrece como identifier type válido.

Fuentes:

- https://support.orcid.org/hc/en-us/articles/360006971353-Metadata-in-the-Works-section
- https://support.orcid.org/hc/en-us/articles/360006894774-Group-multiple-versions-of-the-same-work-together

## Añadir works: método preferido

ORCID recomienda importar desde servicios conectados cuando sea posible porque reduce errores y aporta una fuente externa validada.

Pero para estas novelas, si no hay un import tool adecuado, es legítimo añadirlas manualmente con ISBN.

Fuente:

- https://support.orcid.org/hc/en-us/articles/360006896874-Add-works-manually

No gastar tiempo intentando conseguir una “validated work” si no existe una editorial/servicio ORCID conectado que pueda añadirla. Una entrada self-asserted correcta sigue siendo útil y transparente.

## Contributor role

Si la UI ofrece roles CRedIT para una obra manual, no forzar una taxonomía académica que no encaje. El autor ya queda representado por ownership de la entrada y el work; añadir `Writing – Original Draft` solo si la interfaz lo exige o aporta claridad.

## Duplicados

Antes de añadir cada obra:

1. buscar por título;
2. buscar por ISBN;
3. revisar works ya existentes en la cuenta;
4. si existe la misma obra con el mismo ISBN, actualizar/agrupar en vez de duplicar.

No añadir Samuel o Manecillas dos veces porque una entrada venga de un trusted organization y otra sea manual: ORCID puede agrupar versiones con identificadores comunes.

## Professional activities / affiliations

No inventar afiliación institucional. David es escritor y la web pública no requiere simular una universidad/empresa para “dar autoridad”.

Usar estas secciones solo si existe una relación real y pública que tenga sentido.

## Secuencia exacta para Claude

### Fase 1 · acceso

1. Entrar en ORCID.
2. Confirmar que la cuenta es `0009-0005-9089-3782`.
3. Confirmar nombre público.
4. No exponer email/login en la PR.

### Fase 2 · visibilidad

1. revisar defaults;
2. revisar bio;
3. revisar websites;
4. revisar keywords;
5. revisar works;
6. poner `Everyone` solo en los campos que queramos realmente públicos.

### Fase 3 · identidad

1. nombre `David Porto Díaz`;
2. bio actual;
3. web oficial primera;
4. enlaces externos seleccionados;
5. no añadir person identifiers manuales falsos.

### Fase 4 · works

1. buscar Samuel por ISBN;
2. añadir/verificar;
3. buscar Manecillas papel por ISBN;
4. añadir/verificar;
5. decidir Kindle viendo UI real;
6. comprobar duplicados;
7. revisar visibilidad `Everyone`.

### Fase 5 · QA público

Abrir ORCID en sesión limpia y confirmar:

- nombre correcto;
- web oficial visible;
- bio legible;
- keywords no spam;
- works visibles;
- ISBN correctos;
- links resuelven;
- no aparece información privada accidental.

## Repo

La web actual ya contiene:

`https://orcid.org/0009-0005-9089-3782`

en `Person.sameAs`.

No hay cambio previo de código necesario.

Si durante la sesión:

- ORCID real cambia → actualizar fuente canónica y `sameAs`;
- se obtiene legítimamente un ISNI u otro person identifier estable → coordinar con #421/#398 antes de añadir nuevos `sameAs`;
- se crea/corrige una obra externa con URL estable relevante → valorar `Book.sameAs` solo si representa realmente la misma entidad/edición.

## Evidencia mínima de cierre

- ORCID iD confirmado;
- nombre;
- bio: UPDATED/NO_ACTION;
- websites finales;
- keywords finales;
- visibilidad de campos públicos;
- works finales con ISBN;
- duplicados: NONE/RESOLVED;
- fecha QA público.

## Criterio de cierre

`ORCID_ACCESS_CONFIRMED · NAME_CURRENT · WEBSITE_PUBLIC · BIO_CURRENT · KEYWORDS_CURATED · PUBLIC_VISIBILITY_INTENTIONAL · SAMUEL_ADDED_OR_VERIFIED · MANECILLAS_ADDED_OR_VERIFIED · LINKS_CURATED · DUPLICATES_REVIEWED · NO_FAKE_PERSON_IDENTIFIERS`
