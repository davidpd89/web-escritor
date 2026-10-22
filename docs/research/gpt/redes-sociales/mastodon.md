# Mastodon — resolución pública, código y pruebas (22/10/2026)

PR hija de [#699](https://github.com/davidpd89/web-escritor/pull/699). Scope único: obtener seguidores/publicaciones del perfil Mastodon de forma segura. **No se ha tocado la web ni creado un workflow**.

## Problema localizado y solución

La investigación anterior decía que hacía falta resolver el ID de la cuenta mediante `/api/v1/accounts/lookup` con token (`read:accounts`). Ese endpoint **sí** exige token, pero hay una alternativa mejor que faltaba:

**GET público documentado:** `https://mastodon.social/api/v2/search?q=davidportodiaz&type=accounts&limit=5`. La [documentación oficial de búsqueda](https://docs.joinmastodon.org/methods/search/) confirma acceso público **sin parámetros `resolve` ni `offset`**. La respuesta trae `accounts[]` con entidades Account, incluido `id`, `followers_count` y `statuses_count`. [Entidad Account](https://docs.joinmastodon.org/entities/Account/). No hace falta OAuth para este caso si el servidor permite efectivamente la consulta anónima.

**No elegir por orden de resultados**: el script filtra los elementos hasta encontrar exactamente UNA cuenta cuyo `username`, `acct` y URL `https://mastodon.social/@davidportodiaz` coinciden. Si no coincide o hay duplicados, falla. No confundir cuentas remotas con un mismo nombre ni una URL manipulada. El ID es cadena según documentación oficial y se compara contra un ID previamente verificado al escribir.

### Repositorio público REAL que hace esto

[Mastodon.py](https://github.com/halcy/Mastodon.py) implementa `search_v2` en [mastodon/search.py](https://github.com/halcy/Mastodon.py/blob/c21b954db370b122a26dff127efbca9aa74e386a/mastodon/search.py). [Sus tests públicos usan search_v2](https://github.com/halcy/Mastodon.py/blob/c21b954db370b122a26dff127efbca9aa74e386a/tests/test_search.py). Es software bajo [MIT](https://github.com/halcy/Mastodon.py/blob/master/LICENSE). Estas líneas proceden de su implementación, conservando su propósito: desactivar resolución autenticada y usar el endpoint `v2/search`.

~~~python
if not resolve:
    del params["resolve"]
# ...
return self.__api_request(
    'GET', '/api/v2/search', params,
    offset_pagination=result_type is not None,
    offset_pagination_field=result_type
)
~~~

Extracto atribuido a Mastodon.py, licencia MIT. El adaptador de esta PR **no depende de Mastodon.py**: reproduce el comportamiento con Python estándar, evitando instalar dependencias para una lectura diaria. El test `test_one_get_no_auth_no_resolve` comprueba que la petición no incluye token ni `resolve`.

## Archivos reales añadidos

- [scripts/research/gpt_social_mastodon.py](../../../../scripts/research/gpt_social_mastodon.py): GET con timeout de 10 s y máximo 256 KB, filtro de cuenta exacta, números enteros válidos o nulos, fecha UTC, salida JSON; escritura atómica a fichero explícito solo tras comprobar `--expected-id`.
- [tests/test_gpt_social_mastodon.py](../../../../tests/test_gpt_social_mastodon.py): 18 tests de contrato (simulaciones, sin red).
- [tests/fixtures/social/mastodon_search.fixture.json](../../../../tests/fixtures/social/mastodon_search.fixture.json): respuesta **completamente sintética** para ejecutar el extractor sin Internet.

### Ejecutar y revisar

~~~bash
# Offline: 18 pruebas, sin servidor ni secretos
python -m unittest discover -s tests -p 'test_gpt_social_mastodon.py' -v
python scripts/research/gpt_social_mastodon.py --fixture tests/fixtures/social/mastodon_search.fixture.json

# Paso 1: petición real SOLO para inspección; imprime el id y contadores actuales
python scripts/research/gpt_social_mastodon.py

# Paso 2: después de comprobar id y URL con el propio perfil y GET /api/v1/accounts/:id
python scripts/research/gpt_social_mastodon.py --expected-id 'ID_LOCAL_VERIFICADO' --output /tmp/mastodon.json
~~~

**Prueba local efectivamente ejecutada:** 18/18 tests pasan (Python unittest, entorno aislado, código en disposición de carpetas del repositorio). Cubren cuenta falsa/parecida, cuenta repetida, ausencia de cuenta, ID distinto, URL alterada, tipos inválidos y nulos, ausencia de followers frente a cero, respuesta excesiva, solicitud sin autorización ni `resolve` y conservación del fichero anterior en errores. Faltan pruebas **reales** de respuesta HTTP, 404/429/503 y timeout, que deben ejecutarse con conexión autorizada.

## Qué se integra y dónde

El resultado es un objeto `{"id":"mastodon", "account_id":"...", "profile_url":"...", "followers":N, "posts":N, "views_30d":null, "impressions_30d":null, "interactions_30d":null, "observed_at":"...", "source":"mastodon-public-search", "status":"ok"}`. **Es un registro, no el JSON social global.** El agregador futuro de la PR #699 compondrá las redes en `data/social-metrics.generated.json`; no usar ese nombre como ruta de salida directa. En #704 se decidirá HTML, estilos y el enlace externo «Seguir en Mastodon». No se publica una cifra sin fecha/identidad verificada.

## Lo que no puede declararse validado todavía

Desde el entorno de trabajo, una llamada real a `mastodon.social` produjo error DNS; por eso **ni el ID real ni los seguidores actuales han sido confirmados por este adaptador**. La documentación avala la API, pero la aceptación de una petición anónima concreta en el servidor hay que comprobarla. Hasta superar ese paso, la PR **no está lista para merge ni para activación**. No hubo Actions, integración con el shell, cron, ni cambios en main.

### Puerta de aceptación concreta para Claude

1. GET real `/api/v2/search`: 200, cuenta exacta y campos esperados. Si el servidor no ofrece cuenta en búsqueda pública, registrar fallo y pasar a GET por ID verificado. No forzar solución con scraping.
2. Confirmar `id` con `GET /api/v1/accounts/:id` y URL del perfil. Guardarlo solo donde corresponda, sin token.
3. Probar explícitamente 429/503/timeout, conservar último dato válido y controlar su caducidad en el agregador.
4. Integrar una sola vez en el pipeline común tras validar esos tres pasos. Luego suite completa/CI cuando se autorice.

**Decisión**: preferir API oficial + lector mínimo y verificable a una colección de enlaces o dependencias redundantes.
