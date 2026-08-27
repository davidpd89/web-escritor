# URGENTE — davidportodiaz.com en producción real es GitHub Pages, no Cloudflare Workers, y expone archivos internos

Fecha: 2026-08-27, ~01:50 UTC. Escrito por Claude tras un hallazgo inesperado durante esta sesión. **No he tocado la configuración de hosting/DNS/Pages — solo he investigado en modo lectura.** Necesita tu decisión con la cabeza despejada, no una corrección mía a ciegas de madrugada.

## El hallazgo

Todo el trabajo de esta sesión (y de la PR #106 "allowlist-first", y los tests `test-public-artifact-contract.py`/`test-staging-publication-gate.py`) asume que lo que gobierna qué es público en `davidportodiaz.com` es `scripts/build-public-dist.py` + `.assetsignore`, pensado para el despliegue de **Cloudflare Workers** (`.preview-dist`, `wrangler deploy --assets`).

Pero comprobando el dominio real esta noche:

```
curl -sI https://davidportodiaz.com/
Server: GitHub.com
X-GitHub-Request-Id: ...
```

`gh api repos/davidpd89/web-escritor/pages`:

```json
{"cname":"davidportodiaz.com","build_type":"legacy","source":{"branch":"main","path":"/"}}
```

**El origen real que sirve `davidportodiaz.com` ahora mismo es GitHub Pages, modo "legacy" (Jekyll), sirviendo la rama `main` completa desde la raíz — sin pasar por `build-public-dist.py`, sin `.assetsignore`, sin ninguna de las exclusiones que tanto trabajo os ha costado.**

Comprobado directamente, estos ficheros están accesibles en producción ahora mismo:

- `https://davidportodiaz.com/editorial-facts.json` → 200 (incluye `knownEditorialIncident`, la nota interna sobre el handle @davidpuede)
- `https://davidportodiaz.com/scripts/check-secrets.py` → 200 (y presumiblemente el resto de `scripts/`)
- `https://davidportodiaz.com/docs/CLAUDE-HANDOFF-PR106-AUDITORIA-PROFUNDA-III.md` → 200 (y presumiblemente el resto de `docs/`, incluido este mismo fichero una vez se suba)
- `https://davidportodiaz.com/cloudflare-worker-subscribe.js` → 200 (código fuente del Worker; no contiene la API key en sí, pero sí toda la lógica)
- `https://davidportodiaz.com/donde-empieza-la-jaula/` → 200 (la ruta que el registry marca como `gated`)

`.env` sí devuelve 404 — nunca ha estado trackeado por git, así que las claves reales (Brevo, OpenAI, Cloudflare) no están expuestas por esta vía.

## Por qué no lo he arreglado yo esta noche

El build de Pages lleva un rato en estado `errored` (`gh api repos/davidpd89/web-escritor/pages` → `"status":"errored"`), lo que significa que ahora mismo sirve una copia **desactualizada** de `main` (de antes de que empezaran a fallar los builds), no la versión más reciente — no he conseguido determinar la causa exacta del fallo sin acceso al log completo de Jekyll. No hay fichero `.nojekyll`, así que Pages intenta procesar todo el repo (800+ ficheros, incluido Python) con Jekyll, lo cual nunca ha sido la intención.

La corrección correcta y duradera es casi seguro migrar el despliegue de Pages de modo "legacy" (rama+ruta cruda) a modo **Actions-based**: un workflow que ejecute `python scripts/build-public-dist.py`, suba `.preview-dist` como artefacto de Pages (`actions/upload-pages-artifact`) y lo despliegue (`actions/deploy-pages`) — reutilizando exactamente el mismo builder allowlist-first ya probado toda la noche. Pero:

1. Cambiar el `build_type` de Pages es una acción sobre infraestructura de producción, difícil de verificar sin poder abrir la web y comprobar visualmente que nada se ha roto.
2. No sé con certeza si Cloudflare está detrás como proxy real o solo como DNS (`Server: GitHub.com` sugiere que Cloudflare está en modo "solo DNS", sin proxy, para este registro — coherente con lo que se dijo en el cutover DNS de esta misma sesión: "los 10 registros DNS... en modo DNS only"). Si me equivoco sobre qué sirve realmente el dominio, un cambio a ciegas podría dejar la web caída sin que nadie lo note hasta que despiertes.

Dado que el sitio en sí sigue funcionando visualmente para un visitante normal (solo hay ficheros internos accesibles *además* del sitio, no un sitio caído), prefiero documentarlo con precisión y que decidas con la web delante en vez de arriesgarme a un cambio de hosting irreversible de madrugada.

## Qué recomendaría (a falta de tu confirmación)

1. Verificar en el dashboard de Cloudflare si hay ya un Worker/Route sirviendo `davidportodiaz.com` directamente (si es así, probablemente lo más seguro sea simplemente **desactivar GitHub Pages** en Settings → Pages, ya que Cloudflare pasaría a ser el único origen).
2. Si Cloudflare Workers NO está aún sirviendo el dominio real (solo el subdominio `*.workers.dev` de preview), la ruta segura es migrar Pages a modo Actions con `build-public-dist.py`, no apagarlo sin más.
3. Añadir `.nojekyll` en cualquier caso — no debería estar procesando este repo con Jekyll pase lo que pase.
4. Una vez resuelto, rotar/revisar si algo de lo expuesto (sobre todo el detalle del incidente @davidpuede en `editorial-facts.json`) necesita alguna acción adicional más allá de dejar de exponerlo.

## Estado de lo demás

Nada de esto invalida el trabajo de esta sesión: todos los tests (`test-public-artifact-contract.py`, `test-staging-publication-gate.py`, `build-public-dist.py --check-assetsignore`, etc.) siguen verdes porque validan correctamente el contrato de `.preview-dist`/Cloudflare — el problema es que ese contrato, hasta donde he podido comprobar esta noche, no es el que gobierna el dominio real todavía.
