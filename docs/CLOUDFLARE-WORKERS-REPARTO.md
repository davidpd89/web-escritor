# Reparto del sitio en Cloudflare Workers Static Assets

GitHub Pages admite como máximo 1 GB por sitio. El catálogo de lecturas crece, así que `deploy-pages.yml`
publica además el mismo artefacto repartido entre varios Workers que solo sirven assets. Las URL son
idénticas, el coste es cero (un Worker que solo sirve assets no consume invocaciones) y todo se despliega
desde Actions.

## Cómo funciona

- El plan está en `config/workers-reparto.json`: host, zona, Worker núcleo, prefijo de los fragmentos y
  umbrales de ficheros. Workers Free admite 20.000 ficheros por versión; el máximo del plan es 19.500.
- `python scripts/reparto_workers.py planificar --dist dist --escribir` vuelve a calcular los fragmentos
  cuando el núcleo supera `objetivo_ficheros`. Divide la carpeta que tiene más hijos directos en lotes
  consecutivos.
- `repartir` genera un proyecto wrangler por Worker en `$RUNNER_TEMP/workers`. Cada fichero va a todos los
  Workers que sirven alguna de sus URL. El núcleo lleva el dominio personalizado (`plan.host`); cada
  fragmento recibe rutas de zona `host/prefijo*`, y la ruta más específica gana a la del dominio
  personalizado.
- `desplegar` sube primero los fragmentos y después el núcleo. Luego sincroniza las rutas por API con un
  `PUT` que cambia de dueño sin dejar hueco, y por último borra los fragmentos huérfanos: scripts con el
  prefijo que no están en el plan y no tienen ruta.
- Los nombres de los fragmentos salen de un hash de sus prefijos. Cuando se vuelve a planificar se crean
  Workers nuevos, y los viejos siguen sirviendo hasta que se mueven las rutas.
- Si faltan `CLOUDFLARE_API_TOKEN` o `CLOUDFLARE_ACCOUNT_ID`, los pasos se saltan y terminan con código 0.
  Mientras `bloqueante` sea `false`, los errores salen como `::error::` y no tumban el despliegue de Pages.

## Token de CI

Es un token de usuario llamado «web-escritor CI: Workers reparto (deploy-pages)» y está guardado en el
secreto del repositorio `CLOUDFLARE_API_TOKEN`. El ID de cuenta está en `CLOUDFLARE_ACCOUNT_ID`.

| Ámbito | Permisos |
| --- | --- |
| Cuenta | Workers Scripts: Edit; Account Settings: Read |
| Zona davidportodiaz.com | Workers Routes: Edit; Zone: Read; DNS: Edit |
| Usuario | Memberships: Read; User Details: Read |

Para rotarlo, crea uno nuevo con los mismos permisos (dash → My Profile → API Tokens), ejecuta
`gh secret set CLOUDFLARE_API_TOKEN` y borra el anterior.

## Estado actual (27/11/2026): espejo en staging

- `piloto.davidportodiaz.com` tiene `noindex` y `bloqueante: false`. El humo del repo
  (`tests/test-staging-smoke.mjs`) pasa con la release exacta, y 55 muestras aleatorias son idénticas byte
  a byte a producción.
- Hay 4 Workers (núcleo y 3 fragmentos) con 50 rutas.

## Corte del apex (cuando Pages se acerque al límite)

1. En `config/workers-reparto.json` pon `host: "davidportodiaz.com"`, `noindex: false` y `bloqueante: true`.
   Fusiona y espera a que el despliegue deje el núcleo y las rutas creados.
2. En DNS, borra los registros A/AAAA del apex que apuntan a GitHub. El dominio personalizado del Worker
   núcleo crea su propio registro.
3. Cambia `www`: quita el CNAME a `davidpd89.github.io`, crea un registro proxied (por ejemplo,
   `AAAA 100::`) y añade una Redirect Rule `www` → apex 301 que conserve la ruta y la query.
4. En `deploy-pages.yml`, quita `continue-on-error` del paso «Deploy split artifact» y del humo de Workers.
   Para que Workers no dependa de Pages, quita el corte de >900 MB del paso de presupuesto y añade
   `continue-on-error` a los pasos que suben y despliegan Pages, que pasarán de 1 GB. Sube el freno de espacio
   de la carga.
5. Comprueba el humo con `SITE_BASE_URL=https://davidportodiaz.com`, mira las cabeceras sin `noindex` y
   revisa Search Console.

## Vuelta atrás

- Para quitar el espejo, deja el host en el piloto, o borra los secretos y los pasos se saltan solos.
- Tras el corte: repón los registros A del apex a GitHub Pages (185.199.108-111.153) y el CNAME de `www`,
  quita el dominio personalizado del Worker núcleo y **borra las rutas `davidportodiaz.com/*` de los
  fragmentos** (dash → Workers Routes); si el apex queda proxied, esos prefijos seguirían sirviéndose desde
  los Workers. Devuelve el host del plan al piloto. Con el apex otra vez en Pages vuelve a aplicar el límite de
  1 GB.
