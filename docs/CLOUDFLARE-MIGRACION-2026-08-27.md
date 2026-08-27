# Cloudflare — migración de zona completada, 2026-08-27

Registro de auditoría de la mutación real hecha hoy en producción, según lo
que exige `docs/claude-toolbox/08-CLOUDFLARE-Y-PRODUCCION.md` §13.

## Qué cambió

1. **Zona de Cloudflare creada** en la cuenta `davidpd89@gmail.com`
   (account id `77a008227d663ec8661f1e4422289c1b`), plan Free.
2. **13 registros DNS** cargados, todos en modo **DNS only** (sin proxy):
   4× A (GitHub Pages), CNAME `www`→`davidpd89.github.io`, CNAME
   `brevo1._domainkey`/`brevo2._domainkey` (DKIM), TXT `_dmarc` (DMARC de
   Brevo), TXT `@` ×2 (verificación de Google Search Console y de Brevo),
   TXT `_github-pages-challenge-davidpd89` (verificación de dominio de
   GitHub Pages — no la había importado el escaneo automático, la añadí a
   mano comparando contra el snapshot inactivo de Spaceship), y 2× TXT
   `_acme-challenge` que ya estaban en vivo (no vinculadas a ningún
   registro conocido nuestro; se dejaron tal cual, sin tocar).
3. **Nameservers cambiados en Spaceship**: de `henrik.ns.cloudflare.com` /
   `nora.ns.cloudflare.com` a `lamar.ns.cloudflare.com` /
   `sonia.ns.cloudflare.com` (los asignados a la zona nueva).

## Por qué (el hallazgo que lo motivó)

`henrik`/`nora` ya estaban activos como nameservers desde el 27 de mayo de
2026 (cambio hecho por el propio usuario, luego abandonado a medias), y
respondían con un SOA real y válido — es decir, había una zona de
Cloudflare activa y sirviendo el dominio, pero **no en ninguna cuenta a la
que tuviéramos acceso** (ni `davidpd89`, confirmado por auditoría de la
cuenta sin ningún evento de zona/DNS en 500+ entradas; ni ninguna otra
cuenta encontrada). Nadie supo identificar qué cuenta era. Con la
autorización expresa del usuario, se optó por crear una zona nueva y
propia en `davidpd89` y cortar el traspaso ahí, en vez de seguir
persiguiendo la zona huérfana.

## Verificado antes de tocar Spaceship

- **DNSSEC**: sin registro DS publicado (consulta DoH directa a
  `cloudflare-dns.com/dns-query`), por tanto no aplicaba el procedimiento
  de retirar DS y esperar TTL que describe
  `docs/CLOUDFLARE-ZONE-CDN-SECURITY-RUNBOOK.md`.
- **Sin registros MX**: el dominio no recibe correo directamente, solo usa
  DKIM/DMARC de Brevo para envío autenticado — reduce mucho el riesgo real
  de la migración.
- Los 13 registros se compararon uno a uno contra el snapshot real
  guardado en Spaceship (pestaña "Registros inactivos") antes de dar por
  buena la importación automática de Cloudflare.

## Estado en el momento de escribir esto

Cambio de nameservers confirmado en Spaceship (mensaje "Nameservers
actualizados"). Propagación en curso — Spaceship avisa hasta 48h. Todos
los registros siguen en modo DNS only, así que el comportamiento en
producción no cambia hasta que se decida activar el proxy (nube naranja)
explícitamente en algún registro. `curl -I https://davidportodiaz.com/`
seguía sirviendo GitHub Pages con normalidad justo después del cambio.

## Rollback

Si algo se rompe durante la propagación: en Spaceship → DNS avanzado →
Cambiar nameservers → volver a poner `henrik.ns.cloudflare.com` /
`nora.ns.cloudflare.com`. No se ha tocado nada del lado de GitHub Pages ni
de los Workers existentes.

## Pendiente / siguiente paso

- Confirmar en unas horas/días que `dig NS davidportodiaz.com` ya
  devuelve `lamar`/`sonia` y que el sitio sigue accesible.
- Decidir, ya con la zona propia estable, si activar el proxy (nube
  naranja) en los registros A/CNAME del apex — hoy deliberadamente en DNS
  only para no cambiar comportamiento de golpe.
