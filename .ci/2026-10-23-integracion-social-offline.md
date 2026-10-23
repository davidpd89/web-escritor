# Integración offline del panel de redes sociales (2026-10-23)

Rama: `int/social-pipeline-2026-10-23` (worktree `C:\GIT\web-escritor-int-social`), base `origin/main` c8624491 + merges limpios de #699, #704, #705, #706, #707 (solo ramas locales; nada empujado).

## Hecho
- Merge sin conflictos de las 5 ramas (reutilizadas sin cambios: compose, reader.mjs, metricool_followers/threads, bluesky, mastodon).
- Nuevo `scripts/research/gpt_social_snapshot.py`: adaptadores -> compositor -> JSON público, un solo comando.
- Nuevo fixture `tests/fixtures/social/metricool_followers.fixture.json` y `tests/test_gpt_social_snapshot.py` (9 pruebas).

## Defectos demostrados
1. No había orquestador: tres CLI manuales sin traspaso entre ellos.
2. Salida no idempotente: `generated_at` cambia en cada ejecución -> el fichero se reescribía siempre.
3. Los adaptadores sellaban `observed_at` con el reloj real; con `--now` reproducible el compositor lo rechazaba como futuro (ahora se pasa el mismo instante).
4. Una fuente caída dejaba su red en pendiente aunque el último valor siguiera vigente (<48 h); ahora se conserva revalidado y nunca se resucita uno caducado.

## Verificación
- unittest `test_gpt_*.py`: ver resumen en el chat.
- node --test reader + python->js: 22/22.
- No verificado: llamadas reales a APIs, datos reales de Metricool, CI.

## Ejecución
```
cd scripts/research
python gpt_social_snapshot.py --output <ruta>/social-metrics.json \
  --bluesky-fixture ../../tests/fixtures/social/bluesky_profile.fixture.json \
  --mastodon-fixture ../../tests/fixtures/social/mastodon_search.fixture.json \
  --metricool-export ../../tests/fixtures/social/metricool_followers.fixture.json --now 2026-10-22T08:00:00Z
```
Sin `--*-fixture`, Bluesky y Mastodon se leen en vivo (pasar `--expected-did` / `--expected-mastodon-id`). Metricool es siempre un export local privado.

## Pendiente antes de publicar
Fijar DID/ID reales; export real de Metricool; decidir ubicación del JSON y UI (script.js, autor.html fuera de alcance aquí); consolidar PRs tras merge de #703/#724 por el otro agente.

## Validación adicional (2026-10-23, tarde)
- Merge de `origin/main` limpio. Python `test_gpt_*.py`: 226 OK (225 + 1 nueva). Node reader + python->js: 22/22.
- Real: Bluesky `davidportoescritor.bsky.social` DID `did:plc:i5nwasa74ucmiymxjmh57t7x` (cotejado con resolveHandle); Mastodon `@davidportodiaz@mastodon.social` id `117238993380408996` (cotejado con accounts/lookup). Seguidores y posts leídos en vivo; impresiones/interacciones/vistas son `null` (la API pública no las da).
- Identidad errónea: ambas fuentes rechazadas; con todas caídas sale rc=1, conserva el fichero y el lector lo oculta a las 48 h.
- Defecto corregido: con valores iguales `observed_at` cambiaba y el fichero se reescribía en cada ejecución; ahora solo se reescribe si cambia el contenido o pasan 6 h (para renovar la caducidad). 2 pruebas.
- Metricool: sin export real ni conector accesible desde esta sesión -> **verificación real pendiente**; solo fixture sintético.
