# Investigación GPT — Mastodon (22/10/2026)

**PR hija de #699.** Rama basada en research/gpt-social-dashboard-2026-10-22. Solo análisis y código de referencia, no instalado ni ejecutado; sin Actions ni merge.

## Diagnóstico
Cuenta enlazada: https://mastodon.social/@davidportodiaz. El endpoint GET /api/v1/accounts/:id es PUBLIC una vez conocido el ID local y devuelve followers_count/statuses_count; la ruta GET /api/v1/accounts/lookup?acct=... exige **token de usuario con read:accounts** según docs: NO automatizar lookup anónimo por error. Resolver ID una vez con el flujo permitido, conservarlo en configuración NO secreta y consultar GET por ID. Las cuentas remotas tienen IDs locales distintos. Ningún endpoint público ofrece «impresiones totales».

## Adaptación ligera de lectura (no ejecutada)
~~~python
import json
import os
from urllib.request import Request, urlopen

account_id = os.environ["MASTODON_ACCOUNT_ID"]  # ID LOCAL resuelto con autorización
assert account_id.isdecimal()
url = "https://mastodon.social/api/v1/accounts/" + account_id
with urlopen(Request(url, headers={"Accept": "application/json",
                                  "User-Agent": "web-escritor/1.0"}),
             timeout=10) as response:
    account = json.load(response)
assert account["acct"] == "davidportodiaz"
snapshot = {"network": "mastodon", "followers": account["followers_count"],
            "posts": account["statuses_count"], "impressions_30d": None}
~~~
No confundir followers_count con «personas únicas de redes».

## Código abierto verificable
[halcy/Mastodon.py](https://github.com/halcy/Mastodon.py) MIT ([licencia](https://github.com/halcy/Mastodon.py/blob/master/LICENSE)), [README con inicialización de cliente](https://github.com/halcy/Mastodon.py/blob/master/README.rst): utiliza from mastodon import Mastodon y Mastodon(...). Si se adopta, preservar el texto de licencia y fijar versión; la petición pública anterior evita dependencia adicional.

## QA pendiente
Resolver ID con permiso, 200 público para GET /:id; 404/410 suspensión; instancias y campos locales; timeout/429/503; no meter app token en la página. No se afirma haber resuelto el ID ni ejecutado llamadas de red.

## Entrega Claude
Releer fuente oficial y estado main, integrar una sola vez sobre el contrato padre, ejecutar pruebas offline/live autorizadas, documentar limitaciones reales antes de solicitar merge. Se mantiene aislamiento respecto de las demás hijas.
