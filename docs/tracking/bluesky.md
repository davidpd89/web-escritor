# Bluesky — identidad oficial y verificación por dominio

Fecha de revisión: **2026-09-07**  
PR owner: **#451 · `tracking/bluesky`**  
Estado: **RESEARCHED · EXISTING_ACCOUNT_IN_REPO · DOMAIN_HANDLE_AVAILABLE · RECOMMENDATION_DEFER_LOW_ROI**

## Recomendación (2026-09-09)

David preguntó para qué sirve esto y dijo que actualmente no tiene apenas seguidores en Bluesky. Mi recomendación: **aplazarlo por ahora**, no hacerlo esta noche.

El TXT de dominio (`_atproto.davidportodiaz.com`) es viable técnicamente y sin coste, pero:

- es un cambio de DNS en vivo sobre el dominio real — categoría de acción que esta sesión trata siempre como "requiere tu confirmación explícita", no algo que decida por mi cuenta aunque sea técnicamente reversible;
- con audiencia mínima en Bluesky ahora mismo, el beneficio inmediato es bajo: el handle de dominio ayuda sobre todo a que otros verifiquen que la cuenta es realmente tuya, algo más valioso cuando ya hay gente mirando el perfil;
- no perjudica nada dejarlo para cuando el uso de Bluesky crezca — no hay ventana de oportunidad que se cierre por esperar.

Si en el futuro decides invertir en Bluesky (más actividad, más seguidores), este documento ya tiene toda la investigación lista para ejecutarlo entonces sin repetir el trabajo.

## Objetivo

Consolidar la presencia de **David Porto Díaz** en Bluesky como identidad oficial vinculada a `davidportodiaz.com`, sin abrir cuentas duplicadas ni confundir el handle por dominio con el badge azul de verificación de Bluesky.

El objetivo no es publicar por publicar: es que una cuenta ya enlazada desde la web tenga identidad coherente, enlace canónico y, si se decide mantener Bluesky, use el dominio propio como señal verificable y portable.

## Estado actual del proyecto

La web del proyecto ya ha utilizado como perfil Bluesky:

- `https://bsky.app/profile/davidportoescritor.bsky.social`
- handle conocido: `@davidportoescritor.bsky.social`

Por tanto, la primera acción **NO** es crear otra cuenta.

Claude debe entrar en esa cuenta y comprobar:

- que sigue siendo la cuenta controlada por David;
- DID de la cuenta;
- nombre visible;
- avatar;
- bio;
- enlace web;
- posts/actividad;
- si ya tiene custom domain handle o algún badge de verificación.

Si la cuenta no es accesible o no pertenece realmente a David, documentar el estado antes de crear una nueva identidad.

## Verificación por dominio — estado oficial actual

Bluesky mantiene el sistema de **custom domain handle** como una capa de verificación/identidad.

Fuente oficial:

- https://bsky.social/about/blog/4-28-2023-domain-handle-tutorial
- https://bsky.social/about/blog/3-6-2023-domain-names-as-handles-in-bluesky

Flujo oficial:

1. `Settings` → `Account` → `Handle`.
2. Elegir `I have my own domain`.
3. Bluesky muestra el DID público de la cuenta.
4. Añadir en DNS:
   - host/name: `_atproto`
   - type: `TXT`
   - value: `did=did:plc:...` con el DID exacto mostrado por Bluesky.
5. Esperar propagación DNS.
6. Pulsar `Verify DNS Record`.
7. El handle puede pasar a ser `@davidportodiaz.com`.

El DID **no es un secreto** según la propia guía; es un identificador público.

### Guardrail DNS

No inventar ni copiar un DID de ejemplo.

Claude debe obtener el DID directamente de la cuenta autenticada y añadir **solo** el TXT que Bluesky indique.

No tocar otros registros DNS (MX, SPF, DKIM, DMARC, CNAME, GitHub Pages, etc.).

## Custom domain handle ≠ badge azul

Desde abril de 2025 Bluesky mantiene además un sistema visual de verificación mediante badges y Trusted Verifiers.

Fuente oficial:

- https://bsky.social/about/blog/04-21-2025-verification

La propia Bluesky distingue ambas capas:

- **domain handle** → identidad vinculada al dominio controlado por el usuario;
- **verification badge** → verificación visual adicional concedida por Bluesky o Trusted Verifier.

No escribir `VERIFIED_BADGE=true` simplemente porque el handle sea `@davidportodiaz.com`.

Estado correcto tras el TXT, si no existe badge:

`DOMAIN_HANDLE_VERIFIED · BLUE_BADGE_NOT_CLAIMED/NOT_OBSERVED`

## Ventaja concreta de usar `@davidportodiaz.com`

La documentación oficial de Bluesky explica que el dominio como handle aporta:

- asociación inmediata entre web oficial y cuenta social;
- identidad portable dentro del AT Protocol;
- menor riesgo de confusión con cuentas homónimas;
- una señal de autenticidad basada en control del dominio.

Bluesky anunció en 2025 que más de 270.000 cuentas ya habían vinculado su username a un sitio mediante domain handle.

No presentar esto como beneficio SEO directo ni garantía de Knowledge Panel/ranking.

## Perfil recomendado

### Display name

`David Porto Díaz`

No usar variantes como `David Porto` si el objetivo es coherencia de entidad.

### Handle preferido

Si se decide mantener Bluesky y DNS lo permite:

`@davidportodiaz.com`

### Bio preparada

Versión corta:

> Escritor. Autor de Las manecillas del recuerdo y Samuel entre mundos. Pontevedra → Madrid. Libros, escritura y lo que ocurre entre una historia y la siguiente.

No añadir premios si el límite de caracteres degrada la claridad. Si se añaden, no atribuirlos a una obra concreta sin fuente.

### Web

`https://davidportodiaz.com/`

### Foto

Usar la misma fotografía oficial/canónica que se haya validado para la web/press kit. Coordinar con #444 si finalmente se libera una imagen en Commons, pero Commons no es requisito para Bluesky.

## Estrategia mínima de actividad

No mantener una cuenta simplemente como backlink vacío.

Si se conserva, un nivel razonable sería:

- novedades de obras cuando existan;
- fragmentos/artículos propios con contexto real;
- eventos/firma/prensa;
- alguna interacción auténtica sobre escritura/lectura;
- reutilización selectiva de contenido de otras redes, no réplica automática de todo.

No comprar seguidores, engagement ni automatizar respuestas.

## Cambio necesario en la web si cambia el handle

Tras verificar `@davidportodiaz.com`:

1. comprobar la URL pública canónica de Bluesky;
2. actualizar el enlace social del shell/footer desde `davidportoescritor.bsky.social` al perfil canónico nuevo si procede;
3. actualizar cualquier `sameAs`/dataset machine-readable que todavía apunte al handle anterior;
4. regenerar shell si el enlace social vive en `scripts/build-site-shell.py`;
5. ejecutar `build-site-shell.py --check` + CI relevante.

No editar docenas de HTML manualmente si el shell es el owner.

La guía oficial indica que el `.bsky.social` más reciente queda reservado y que menciones/tags del handle anterior siguen apuntando a la cuenta después del cambio, pero aun así nuestra web debe enlazar la identidad canónica actual.

## QA después del cambio

- abrir `https://bsky.app/profile/davidportodiaz.com` o URL canónica que Bluesky exponga;
- confirmar display name;
- confirmar handle;
- confirmar avatar/bio/web;
- abrir enlace desde footer de davidportodiaz.com;
- móvil + escritorio;
- revisar que el DNS TXT `_atproto` resuelva;
- confirmar que la web sigue resolviendo normalmente;
- comprobar que no se rompió correo ni GitHub Pages;
- comprobar que la cuenta antigua no se convirtió accidentalmente en duplicado.

## Coordinación con otras PR

- #398 Wikidata → identidad de autor y external IDs.
- #444 Wikimedia Commons → foto libre solo si se decide licenciarla.
- #437 Instagram/Threads, #439 LinkedIn, #435 YouTube → mismo nombre/web/foto.
- #460/#459 → monitorización de menciones.

## No hacer

- no crear segunda cuenta sin auditar la existente;
- no llamar “badge azul” al domain handle;
- no publicar el DID como si fuera credencial secreta ni, al contrario, ocultarlo como si lo fuera;
- no modificar DNS fuera del TXT requerido;
- no convertir el perfil en feed automático de promociones;
- no añadir `sameAs` a una cuenta que no esté controlada/verificada.

## Criterio de cierre

Si se mantiene Bluesky:

`EXISTING_ACCOUNT_CLAIMED · PROFILE_COHERENT · DOMAIN_HANDLE_VERIFIED · CANONICAL_PROFILE_URL_RECORDED · WEBSITE_SOCIAL_LINK_UPDATED · MACHINE_SAMEAS_UPDATED_IF_APPLICABLE · DNS_QA_DONE · MOBILE_DESKTOP_QA_DONE`

Si se decide no mantener actividad:

`NO_GO_LOW_VALUE · EXISTING_LINK_REMOVAL_REVIEWED · NO_DUPLICATE_ACCOUNT_CREATED`

## Fuentes consultadas 2026-09-07

- Bluesky — domain handle tutorial: https://bsky.social/about/blog/4-28-2023-domain-handle-tutorial
- Bluesky — domain names as handles: https://bsky.social/about/blog/3-6-2023-domain-names-as-handles-in-bluesky
- Bluesky — verification badges / Trusted Verifiers: https://bsky.social/about/blog/04-21-2025-verification
- Bluesky User FAQ: https://bsky.social/about/blog/5-19-2023-user-faq
