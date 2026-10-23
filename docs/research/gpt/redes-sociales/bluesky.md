# Bluesky — PR #706: implementación preparada, no desplegada

Actualizado 22/10/2026. PR hija de [#699](https://github.com/davidpd89/web-escritor/pull/699). **Scope: solo lectura de seguidores y publicaciones Bluesky.** No modificar UI, navegación, cron ni otras redes en esta PR.

## Problema y opción seleccionada

El perfil enlazado en `autor.html` y `scripts/build-site-shell.py` es https://bsky.app/profile/davidportoescritor.bsky.social. Necesitamos seguidores verificables, sin contraseña ni scraper.

**A (elegida):** `GET https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=davidportoescritor.bsky.social`. Las [instrucciones oficiales de AppView](https://bsky.network/docs/api-directory/) y el [lexicon getProfile](https://github.com/bluesky-social/atproto/blob/main/lexicons/app/bsky/actor/getProfile.json) indican que es público sin sesión. El [lexicon profileViewDetailed](https://github.com/bluesky-social/atproto/blob/main/lexicons/app/bsky/actor/defs.json) declara `did` y `handle` obligatorios; `followersCount` y `postsCount` opcionales. NO contiene impresiones, alcance ni visualizaciones.

**B (no elegida):** [MarshalX/atproto](https://github.com/MarshalX/atproto), SDK Python [MIT](https://github.com/MarshalX/atproto/blob/main/LICENSE). El método [Client.get_profile](https://github.com/MarshalX/atproto/blob/main/packages/atproto_client/client/client.py) llama a esta misma operación, pero introduce dependencias y gestión de cliente innecesarias para una petición pública. Su llamada central, extraída y adaptada de ese fichero, es:

~~~python
return self.app.bsky.actor.get_profile(
    models.AppBskyActorGetProfile.Params(actor=actor)
)
~~~

No se incorpora el SDK ni ese fragmento a la ejecución. La solución seleccionada es código propio con `urllib` estándar; si se decide copiar el SDK después, hay que conservar el aviso de licencia MIT.

## Código REAL añadido en esta PR

- [scripts/research/gpt_social_bluesky.py](../../../../scripts/research/gpt_social_bluesky.py): petición pública única, timeout 10 s, límite 256 KB, validación estricta de perfil, DID y contadores, ISO UTC, JSON por red; escritura atómica solo con parámetro explícito.
- [tests/test_gpt_social_bluesky.py](../../../../tests/test_gpt_social_bluesky.py): 13 pruebas offline de contrato.
- [tests/fixtures/social/bluesky_profile.fixture.json](../../../../tests/fixtures/social/bluesky_profile.fixture.json): fixture **sintética**, no seguidores reales.

El adaptador no incluye login, tokens, scraping, schedulers, modificaciones de la web ni dependencias instalables.

### Comandos reproducibles

~~~bash
# Contrato sin red
python -m unittest discover -s tests -p 'test_gpt_social_bluesky.py' -v
python scripts/research/gpt_social_bluesky.py --fixture tests/fixtures/social/bluesky_profile.fixture.json

# Comprobación de la cuenta real (solo imprime por stdout)
python scripts/research/gpt_social_bluesky.py

# Solo tras verificar DID auténtico por una segunda fuente del titular:
python scripts/research/gpt_social_bluesky.py --expected-did 'DID_REAL' --output /tmp/bluesky-profile.json
~~~

El modo `--output` **exige** `--expected-did`; el DID de la fixture no sirve. Si falla red, JSON, identidad, contador de seguidores o escritura, termina con error y no reemplaza la última instantánea válida. Una respuesta que omite `followersCount` se representa como `null` y `status=partial` por stdout; nunca se publica como cero.

**Pruebas ejecutadas:** 13/13 OK localmente en una copia aislada del adaptador. Incluyen 0 frente a null, bool/negativos/float/texto, handle o DID distinto, respuesta no objeto, tamaño excesivo, única URL, fixture sin escritura, guardia DID, preservación de fichero anterior ante error y escritura válida con respuesta simulada. **No se ejecutó CI, Actions ni la suite del repositorio.**

**Bloqueantes actuales:** la prueba live de este perfil no pudo ejecutarse por un fallo de resolución DNS desde el entorno de trabajo; el DID auténtico está `[[pendiente]]`. Sin esos dos datos no puede afirmarse que funcione contra la cuenta real.

## Conexión exacta con la futura web

El script produce **un registro Bluesky**, con `id,profile_url,handle,did,followers,posts,views_30d=null,impressions_30d=null,interactions_30d=null,observed_at,source,status`. No produce el agregado completo con `schema_version` y `networks[]`. **No** dirigir `--output` a `data/social-metrics.generated.json`: hace falta el compositor de #699/#705 y el frontend de #704. El diseño incorporará el CTA «Seguir en Bluesky» que abre el perfil externo. Un botón de seguimiento interno exigiría permisos de cada visitante y no está contemplado.

## Siguiente prueba estricta, antes de fusionar

1. Ejecutar el GET real; registrar estado HTTP, handle, DID y tipos de los dos contadores, no la cifra de la fixture.
2. Verificar DID desde la cuenta propia; repetir con `--expected-did`; contrastar fecha, perfil y salida en fichero temporal.
3. Probar 404/429/5xx y timeout con respuesta simulada, en especial que no se sobrescribe último dato; validar Windows y Linux.
4. Solo entonces conectar el registro al agregador y definir caducidad (p. ej. 24h), fallback y QA de la UI en PR separada. Correr la suite completa cuando se autorice Actions.

**Estado real:** API y campos contrastados en documentación vigente; fuente de código abierto contrastada con licencia; adaptador y tests escritos; solo test offline realizado. **Integración end-to-end no demostrada.**
