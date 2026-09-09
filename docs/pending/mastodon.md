# Mastodon — identidad verificada + atribución Fediverse

Fecha de revisión: 2026-09-07

Estado: `RESEARCHED · FREE_WEB_VERIFICATION_CONFIRMED · FEDIVERSE_ATTRIBUTION_CONFIRMED · INSTANCE_RECOMMENDED · ACCOUNT_CREATION_NEEDS_AUTHOR`

## Recomendación de instancia y handle (2026-09-09)

David preguntó qué significan "instancia" y "handle" y pidió usar el mismo nombre de usuario que en sus otras redes.

- **Handle** = el nombre de usuario dentro de Mastodon, exactamente como `@nombre` en Instagram/TikTok/etc. Ya usa `davidportodiaz` en Instagram/Facebook/LinkedIn/Threads y `davidportoescritor` en TikTok/Bluesky — para consistencia se recomienda **`davidportodiaz`**.
- **Instancia** = el servidor concreto de Mastodon donde vive la cuenta (Mastodon es una red descentralizada, no hay un único "mastodon.com"). El handle completo se escribe `@usuario@instancia`, p. ej. `@davidportodiaz@mastodon.social`.

**Recomendación**: `mastodon.social`, la instancia insignia operada por Mastodon GmbH (verificado en vivo en el pie de `mastodon.social/about`: "software libre... y marca comercial de Mastodon GmbH" — la organización perdió su estatus de entidad sin ánimo de lucro alemana (gGmbH) en algún momento entre 2021 y ahora, según la propia página "About" del proyecto, y está en proceso de mover su estructura a una nueva fundación con una entidad estadounidense (Mastodon, Inc.) de por medio) — sigue siendo estable a largo plazo, moderación seria, sin política de nicho de una comunidad temática, y la más ampliamente federada, lo que maximiza que perfiles en otras instancias puedan encontrarlo y seguirlo sin fricción. Handle resultante: **`@davidportodiaz@mastodon.social`**.

**Importante — esto no lo puedo crear yo**: crear una cuenta nueva (Mastodon incluida) es una acción que las normas de esta sesión reservan siempre para el titular, nunca para Claude, con independencia de lo urgente o simple que parezca. David tiene que registrar `davidportodiaz` en `mastodon.social` él mismo (email + contraseña, sin datos sensibles adicionales). En cuanto exista la cuenta, Claude puede completar el resto de este documento sin más intervención suya: verificación `rel="me"`, `fediverse:creator`, y añadir el perfil a `Person.sameAs`.

## Objetivo

Crear o revisar una presencia oficial gratuita de David Porto Díaz en Mastodon y conectarla técnicamente con `davidportodiaz.com` mediante estándares abiertos que refuercen identidad y atribución de autor.

No se trata simplemente de “abrir otra red social”: la utilidad concreta es que la propia web oficial pueda verificar el perfil y que los artículos compartidos en Mastodon puedan atribuirse correctamente a David.

## Verificación gratuita confirmada

Mastodon documenta oficialmente que cualquier persona con web propia puede verificar su identidad sin pagar ni enviar documentación.

El mecanismo es:

1. incluir en la web un enlace al perfil Mastodon con `rel="me"`;
2. poner la URL de la web en uno de los campos del perfil Mastodon;
3. guardar el perfil;
4. Mastodon comprueba el enlace recíproco y marca el campo como verificado.

Fuente oficial:
- https://joinmastodon.org/es/verification

## Situación del repo

Búsqueda actual en `main`:

- no hay enlace Mastodon;
- no hay `rel="me"`;
- no hay `fediverse:creator`.

Por tanto no toca generar código todavía: primero necesitamos el handle/URL canónico real del perfil.

## Perfil

Si no existe cuenta, elegir una instancia estable y razonable; no migrar/crear múltiples cuentas por acumular URLs.

Configurar:

- display name: David Porto Díaz;
- foto coherente con otros perfiles;
- bio breve factual;
- web oficial;
- libros solo de forma natural, sin convertir la bio en anuncio;
- descubrimiento/indexación activados si la instancia/versión lo permite y la intención es ser encontrable.

Mastodon 4.6 incluye controles `discoverable` e `indexable` en el perfil. Claude debe revisar la UI real de la instancia y dejar ambos coherentes con el objetivo de descubrimiento público.

Fuentes:
- https://docs.joinmastodon.org/methods/profile/
- https://blog.joinmastodon.org/2026/06/mastodon-4-6/

## Cambio web requerido tras conocer el handle

Una vez exista URL estable, añadir en la fuente owner del shell/perfil social un enlace real:

```html
<a rel="me" href="https://INSTANCIA/@HANDLE">Mastodon</a>
```

No hardcodear en decenas de HTML si el repo tiene owner/generador central.

Después:

- regenerar outputs;
- comprobar `rel="me"` en producción;
- comprobar que Mastodon verifica `davidportodiaz.com`;
- añadir URL a `Person.sameAs` si el perfil es oficial, público y estable.

## fediverse:creator

Mastodon mantiene la atribución de previews mediante `fediverse:creator`. En Mastodon 4.6 el perfil incluye además `attribution_domains`, que permite autorizar dominios desde los que el usuario quiere recibir atribución.

Fuente actual:
- https://blog.joinmastodon.org/2026/06/mastodon-4-6-for-devs/

Si la instancia soporta esta función:

1. añadir `davidportodiaz.com` como attribution domain en el perfil;
2. añadir en las páginas editoriales/artículos del sitio la metadata `fediverse:creator` con el handle exacto;
3. probar una URL real compartida en Mastodon;
4. confirmar que la preview atribuye el artículo a David y no marca `missing_attribution`.

No añadir esta metadata hasta tener handle definitivo y soporte confirmado en la instancia.

## Qué páginas deberían llevar atribución

Si funciona correctamente, priorizar:

- artículos de `/cuaderno/`;
- páginas editoriales firmadas por David;
- quizá fichas de libros si conceptualmente tiene sentido.

No meterla en páginas técnicas, privacidad, formularios, tools sin autoría editorial o contenidos generados por terceros.

## Discoverability / Collections

Mastodon 4.6 incorpora Collections y experiencias de descubrimiento que dependen de preferencias del perfil.

Si queremos visibilidad:

- activar `Feature me in discovery experiences`/equivalente si la UI lo ofrece;
- mantener cuenta pública;
- evitar bloquear indexación si el objetivo es descubrimiento orgánico.

No sacrificar privacidad personal fuera del perfil público del autor.

## Estrategia de contenido

No duplicar automáticamente todo Instagram/LinkedIn.

Uso mínimo razonable:

- lanzamientos reales;
- artículos del Cuaderno;
- eventos/firmas;
- fragmentos breves permitidos;
- conversación genuina con lectores/escritores.

Si después de 60–90 días no aporta interacción/referrals ni utilidad de identidad, mantener solo el perfil verificado con actividad mínima.

## Métricas

Registrar:

- referrals desde Mastodon;
- clicks hacia libros/artículos;
- seguidores/interacciones solo como contexto;
- preview attribution funcionando;
- tiempo de mantenimiento.

No justificar trabajo futuro solo por número de seguidores.

## Guardrails

- cero pago;
- una sola cuenta oficial estable;
- no bots de autopost masivo inicialmente;
- no comprar seguidores;
- no crear contenido duplicado sin valor;
- no añadir `sameAs` hasta verificar perfil real;
- no inventar handle antes de que exista.

## Criterio de cierre

`PROFILE_READY · PROFILE_PUBLIC_DISCOVERABILITY_CONFIGURED · WEBSITE_REL_ME_ADDED · WEBSITE_VERIFIED · PERSON_SAMEAS_UPDATED · ATTRIBUTION_DOMAIN_CONFIGURED_IF_SUPPORTED · FEDIVERSE_CREATOR_TESTED · REFERRALS_MEASURABLE`
