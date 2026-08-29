# M.2 · HSTS preload / `includeSubDomains`

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `DEFER`.

## Veredicto

#135 dejó HSTS preload estrictamente diferido. No se debe activar `includeSubDomains`/`preload` para mejorar un score de seguridad ni como extensión automática de M.1: primero hay que inventariar **todos** los subdominios, comprobar HTTPS estable y aceptar conscientemente el compromiso operativo de forzar HTTPS incluso antes del primer contacto con el servidor.

## Hipótesis original

Evaluar HSTS preload una vez confirmado que todos los subdominios sirven HTTPS de forma estable, reconociendo desde el principio que es una decisión de alto compromiso.

## Evolución histórica

### Revisión 108/108 → `DEFER`

- valor potencial medio;
- coste técnico bajo, pero riesgo operativo alto;
- no activar hasta inventario de subdominios;
- decisión explícita, no checklist.

### Matriz → `DEFERIR ESTRICTO`

> «HSTS preload solo con inventario completo de subdominios y compromiso HTTPS permanente. No por score.»

### Autoridad final → `DEFER`

> «HSTS preload solo tras inventario completo de subdominios y compromiso HTTPS permanente; no por conseguir A+.»

La revalidación independiente mantuvo M.2 diferida.

## Revalidación oficial actual

MDN documenta que:

- `Strict-Transport-Security` se entrega como **cabecera HTTP sobre HTTPS**;
- `includeSubDomains` aplica la política a todos los subdominios;
- para `preload`, `max-age` debe ser al menos `31536000` (1 año) y `includeSubDomains` debe estar presente;
- HSTS hace que errores TLS no puedan saltarse normalmente;
- un subdominio sin HTTPS compatible puede quedar inaccesible bajo una política heredada.

Fuentes:

- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security
- https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/TLS

## Relación con M.1

M.1 debe observar primero el header HSTS **real** de producción.

Resultados posibles:

```text
NO_HSTS
HSTS_HOST_ONLY
HSTS_INCLUDE_SUBDOMAINS
HSTS_PRELOAD_DIRECTIVE
PRELOADED_EXTERNALLY
UNKNOWN
```

Ninguno de ellos autoriza automáticamente cambiar M.2.

Si ya existe HSTS host-only, puede ser correcto mantenerlo mientras se inventarían subdominios. Si ya hubiera `includeSubDomains` o `preload`, habría que auditar el riesgo real antes de tocarlo.

## Por qué `includeSubDomains` cambia el riesgo

La política del dominio padre alcanza subdominios presentes y futuros. Antes de activarla hay que conocer, como mínimo:

- `www`;
- endpoints Worker/API;
- hosts de preview/staging si pertenecen al mismo dominio;
- correo/webmail u otros servicios si existieran bajo el dominio;
- subdominios antiguos aún resolviendo DNS;
- redirects y certificados de cada host;
- proveedores externos con CNAME.

No asumir que «la web principal funciona con HTTPS» significa que todo el namespace está preparado.

## Inventario previo obligatorio

Documento/artefacto recomendado:

```text
hostname
purpose
owner/provider
DNS record
HTTP reachable
HTTPS reachable
certificate valid
redirect HTTP→HTTPS
HSTS own header
can survive inherited includeSubDomains
retirement plan
notes
```

La fuente debe combinar DNS real y documentación operativa; el repo por sí solo no basta.

## Gate de decisión

Solo considerar `includeSubDomains`/preload cuando:

```text
all known subdomains inventoried
AND all required hosts support valid HTTPS
AND legacy/insecure hosts retired or migrated
AND owner accepts future-subdomain constraint
AND rollback implications understood
AND M.1 live audit is clean/stable
```

## Rollback y compromiso

HSTS se cachea en clientes durante `max-age`. Reducir o eliminar la cabecera no borra instantáneamente políticas ya almacenadas.

Preload añade otra capa: navegadores distribuyen una lista incorporada. La retirada no es equivalente a desactivar un feature flag y puede tardar en propagarse.

Por eso #135 lo trata como decisión de alto compromiso.

## Secuencia segura si algún día se decide avanzar

No saltar directamente a preload. Una progresión prudente sería:

1. M.1: observar comportamiento HTTP/HTTPS actual;
2. inventario de subdominios;
3. corregir hosts inseguros;
4. HSTS host-only con `max-age` prudente si faltara y se controla la capa;
5. observar durante ventana suficiente;
6. valorar `includeSubDomains`;
7. observar nuevamente;
8. solo entonces evaluar preload y requisitos vigentes.

Los valores concretos deben decidirse con la infraestructura real del momento, no copiarse de este documento.

## GitHub Pages / Cloudflare

El sitio puede tener capas externas que no están representadas en HTML. M.2 debe implementarse donde realmente se controlen las cabeceras HTTP.

No activar Cloudflare proxy únicamente para conseguir preload/HSTS si el cambio de proxy no está justificado por una decisión de infraestructura independiente.

## No confundir seguridad con SEO

HSTS es una medida de seguridad/transporte. No vender `preload` como factor de ranking ni perseguirlo para obtener una puntuación A+ en una herramienta externa.

## Subdominios futuros

Con `includeSubDomains`, cualquier nuevo subdominio debe nacer HTTPS-ready. Esto cambia la gobernanza de DNS y despliegue futura.

Antes de aprobar M.2 debe existir una norma operativa equivalente a:

> Ningún nuevo host bajo el dominio se publica si no dispone de HTTPS válido desde el primer momento.

## Qué NO hacer

- añadir `preload` porque MDN lo muestra en un ejemplo;
- copiar `max-age=63072000; includeSubDomains; preload` sin inventario;
- activar `includeSubDomains` antes de probar cada host;
- interpretar un A+ de Observatory como aprobación;
- aplicar HSTS desde `<meta>`;
- enviar HSTS por HTTP y asumir que el navegador lo aplica;
- activar proxy/CDN solo para esta casilla;
- olvidar CNAMEs/proveedores externos;
- asumir rollback instantáneo.

## Definition of Done para salir de `DEFER`

- M.1 live audit finalizado;
- listado completo de subdominios/servicios;
- HTTPS/certificados/redirects verificados;
- responsables y dependencias externas identificados;
- riesgo de `includeSubDomains` documentado;
- decisión explícita de aceptar compromiso futuro;
- plan de rollout gradual;
- comprobación de requisitos actuales de preload inmediatamente antes de actuar.

## Trazabilidad preservada

- hipótesis original cautelosa;
- revisión `DEFER`;
- matriz `DEFERIR ESTRICTO`;
- autoridad final `DEFER`;
- revalidación independiente;
- relación obligatoria con M.1;
- fuentes MDN actuales y requisitos de preload.

## Recomendación para Clara/Claude

**No activar HSTS preload ni `includeSubDomains` ahora.** Completar primero M.1 y un inventario DNS/HTTPS de todo el namespace. Reabrir solo como decisión explícita de infraestructura, no como mejora de score.