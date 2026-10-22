# Investigación GPT — Bluesky (22/10/2026)

**PR hija de #699.** Rama basada en research/gpt-social-dashboard-2026-10-22. Solo análisis y código de referencia, no instalado ni ejecutado; sin Actions ni merge.

## Diagnóstico
Perfil oficial ya enlazado en autor.html: https://bsky.app/profile/davidportoescritor.bsky.social. Bluesky AppView publica app.bsky.actor.getProfile mediante https://public.api.bsky.app sin login. Incluye followersCount, followsCount, postsCount; NO ofrece impresiones de cuenta. Datos independientes de Metricool útiles para comprobar cobertura y detectar desvíos.

## Implementación adaptada para script Python estándar (no ejecutada)
~~~python
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

actor = "davidportoescritor.bsky.social"
api = "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?"
url = api + urlencode({"actor": actor})
with urlopen(Request(url, headers={"Accept": "application/json",
                                  "User-Agent": "web-escritor-social-stats/1.0"}),
             timeout=10) as response:
    profile = json.load(response)
assert profile["handle"].casefold() == actor.casefold()
snapshot = {"network": "bluesky", "followers": profile.get("followersCount"),
            "posts": profile.get("postsCount"), "impressions_30d": None,
            "source": "bsky-public-appview"}
~~~
No añadir likes emitidos por nosotros como señal de engagement de la audiencia.

## Open source auditado
[MarshalX/atproto](https://github.com/MarshalX/atproto), [ejemplo del README](https://github.com/MarshalX/atproto/blob/main/README.md), licencia MIT [LICENSE](https://github.com/MarshalX/atproto/blob/main/LICENSE). Su ejemplo usa Client/login para operar como usuario; para este lector público es más ligero urllib. Se documenta la alternativa, no se copia un cliente autenticado innecesario.

## QA pendiente
GET 200 con handle correcto, campo int >=0, error 429/retry, timeout, alias DID/cambio de handle, rango nulo, cabeceras y caché; comparar seguidores contra Metricool con fecha alineada antes de usarlo como respaldo. Impresiones permanecen null.

## Entrega Claude
Releer fuente oficial y estado main, integrar una sola vez sobre el contrato padre, ejecutar pruebas offline/live autorizadas, documentar limitaciones reales antes de solicitar merge. Se mantiene aislamiento respecto de las demás hijas.
