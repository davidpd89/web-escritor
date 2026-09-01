# M.2 · Revalidación de producción · HSTS preload

Fecha: 2026-08-30  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
Evidencia live upstream: PR #244 / M.1, run `33325462091`

## Veredicto

`DEFER · HSTS_HOST_ONLY_ALREADY_LIVE · SUBDOMAIN_INVENTORY_INCOMPLETE · NO_CODE`

M.1 ya ha resuelto la incógnita principal: producción envía HSTS en todas las rutas HTTPS muestreadas:

```text
Strict-Transport-Security: max-age=31556952
```

No se observaron las directivas:

```text
includeSubDomains
preload
```

Por tanto M.2 no consiste en «añadir HSTS». El host principal ya conserva HSTS durante aproximadamente un año. La única decisión pendiente es si algún día compensa extender esa obligación a todo el namespace y entrar en preload.

## Evidencia live

M.1 observó:

- `http://davidportodiaz.com/` → `301` a `https://davidportodiaz.com/`;
- siete familias HTTPS → `200`;
- `server: GitHub.com`;
- HSTS host-only uniforme: `max-age=31556952`.

Esto satisface el gate histórico «M.1 live audit finalizado» para el host principal, pero no el inventario de subdominios.

## Requisitos actuales

La documentación MDN vigente mantiene que:

- `includeSubDomains` aplica HSTS a todos los subdominios;
- la inclusión en preload requiere `includeSubDomains`;
- preload exige `max-age` de al menos `31536000` segundos;
- MDN recomienda probar con cuidado `includeSubDomains` porque puede inutilizar hosts que no soporten HTTPS correctamente;
- la política HSTS queda cacheada en clientes durante `max-age`, por lo que el rollback no es inmediato.

El valor live actual ya supera el mínimo temporal de un año, pero **eso no hace elegible ni prudente el preload por sí solo**: falta `includeSubDomains` y, sobre todo, falta demostrar que el namespace completo puede soportarlo.

## Inventario pendiente

El repo demuestra el dominio principal y servicios externos, pero no constituye un inventario DNS completo. Antes de reabrir M.2 debe existir evidencia para todos los hosts bajo `*.davidportodiaz.com`, incluidos hosts históricos o gestionados fuera de este repositorio.

El inventario mínimo debe registrar:

```text
hostname
purpose
DNS record/provider
HTTP behavior
HTTPS behavior
certificate validity
owner
can survive inherited HSTS
retirement plan
```

Búsquedas de código o motores de búsqueda no sustituyen una fuente DNS/operativa autoritativa.

## Decisión

Mantener HSTS host-only tal como lo entrega actualmente GitHub Pages. No añadir `includeSubDomains` ni `preload` desde esta PR.

Reabrir únicamente cuando:

1. el namespace esté inventariado de forma completa;
2. todos los hosts necesarios tengan HTTPS válido y estable;
3. hosts legacy se hayan retirado o migrado;
4. el owner acepte que futuros subdominios deberán nacer HTTPS-ready;
5. se revisen otra vez los requisitos vigentes de preload justo antes de actuar.

## Qué NO hacer

- confundir `max-age≈1 año` con preload ya preparado;
- cambiar la cabecera por score;
- activar `includeSubDomains` a partir de un inventario parcial;
- intentar configurar HSTS desde `<meta>`;
- crear una capa proxy únicamente para conseguir esta directiva;
- tratar el rollback como instantáneo.

## Estado final

M.1 reduce incertidumbre, pero no cambia la decisión de M.2: **DEFER** hasta disponer de inventario completo y compromiso operativo explícito.
