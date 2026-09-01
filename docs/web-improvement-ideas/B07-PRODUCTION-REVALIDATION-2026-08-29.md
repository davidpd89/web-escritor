# B.7 · Revalidación de producción — IndexNow

Fecha: 2026-08-29  
Base: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #172  
Decisión: **IMPLEMENTED_IN_PR · POST_DEPLOY_NOTIFY · LIVE_SUBMISSION_AFTER_MERGE**

## Hallazgo

`main` no contiene una implementación de IndexNow. A diferencia de varias ideas de #135 que ya estaban cubiertas, aquí sí existía un hueco técnico reproducible.

El pipeline de producción ya ofrecía, sin embargo, el owner correcto para implementarlo: `.github/workflows/deploy-pages.yml` construye el artefacto público, despliega GitHub Pages y después verifica en `davidportodiaz.com` el SHA exacto de la release. IndexNow se integra en esa secuencia; no se crea un pipeline paralelo.

## Contrato oficial revalidado

IndexNow está diseñado para notificar URLs añadidas, actualizadas o eliminadas.

La documentación actual establece, entre otros límites:

- key de 8–128 caracteres válidos;
- fichero de ownership público, con la opción raíz recomendada;
- envío por POST de hasta 10.000 URLs;
- `200` = solicitud recibida;
- `202` = recibida con validación de key pendiente;
- `403` = key inválida;
- `422` = URLs/key no pertenecen al host declarado;
- `429` = exceso de solicitudes.

Un `200`/`202` **no significa indexado, rankeado ni citado**. Esta implementación registra únicamente recepción/validación pendiente.

## Reutilización de una autoridad pública existente

El repo ya publica en raíz:

`59347d39b5684876a7ccc84382f31758.txt`

Su contenido es exactamente:

`59347d39b5684876a7ccc84382f31758`

El fichero ya está permitido explícitamente por `scripts/build-public-dist.py` y clasificado como `verification`. Cumple el contrato de key pública de IndexNow, por lo que no se añade otra key ni se toca la allowlist.

## Implementación

### `scripts/indexnow.py`

Añade dos fases deliberadamente separadas:

1. `derive`: compara dos artefactos públicos ya construidos y sus registries;
2. `submit`: envía el conjunto resultante después de verificar producción.

`derive`:

- toma únicamente rutas públicas con `searchIndex=true`;
- excluye estados `noindex`, `internal`, `gated` y `deprecated`;
- excluye fragmentos;
- compara el contenido real servido mediante hash del source publicado;
- detecta altas, modificaciones y bajas;
- emite URLs absolutas HTTPS del host canónico;
- limita a 10.000 URLs.

`submit`:

- valida host/HTTPS/fragmentos;
- valida key y filename;
- construye `host`, `key`, `keyLocation`, `urlList`;
- reintenta de forma acotada 429/5xx/fallos de red;
- trata 200/202 como recepción, no indexación;
- falla ante respuestas permanentes inválidas;
- tiene `--dry-run`.

### Pipeline de deploy

`deploy-pages.yml` pasa a:

```text
build current artifact
→ build previous public artifact
→ derive changed indexable URLs
→ upload ephemeral change-set
→ stamp exact release identity
→ deploy
→ verify exact SHA in production
→ verify public IndexNow key
→ submit changed URLs
```

El job de notificación depende de `verify-production`; no puede avisar de una release que todavía no está confirmada en producción.

`workflow_dispatch` no inventa un “diff anterior” y genera un change-set vacío.

## Tests

`tests/test-indexnow.py` cubre:

- alta;
- modificación;
- baja;
- exclusión de `noindex`;
- exclusión de fragmentos;
- URL HTTPS/host;
- key real publicada por el repo;
- `keyLocation`;
- filename incorrecto;
- key demasiado corta.

El test se integra en los gates existentes que ejecutan `tests/test-*.py`; no se crea otro workflow de CI específico.

## Limitaciones deliberadas

- La PR no puede demostrar una recepción live de IndexNow antes de estar en `main`, porque el workflow de deploy solo se ejecuta tras push a `main`.
- No se envían todas las URLs en cada release.
- No se notifican assets CSS/JS/imágenes: la unidad es URL pública indexable.
- No se dice que IndexNow sustituya sitemap/crawling normal.
- No se almacena ninguna key secreta: la key es un proof público por diseño.

## Definition of Done

- [x] gap real demostrado;
- [x] owner de deploy existente reutilizado;
- [x] diff sobre artefacto público, no `git diff` bruto;
- [x] altas/modificaciones/bajas soportadas;
- [x] noindex/gated excluidos;
- [x] key pública existente reutilizada;
- [x] notificación posterior a verificación exacta de producción;
- [x] semántica 200/202 correcta;
- [x] test unitario añadido;
- [ ] CI del HEAD final completamente verde;
- [ ] primera ejecución live tras merge/push a `main`;
- [ ] revisar Bing Webmaster Tools IndexNow tras recibir tráfico real;
- [ ] revisión de Claude antes de merge.

**Estado final:** `IMPLEMENTED_IN_PR · POST_DEPLOY_NOTIFY · LIVE_SUBMISSION_AFTER_MERGE`.
