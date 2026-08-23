# Brevo Worker: despliegue pendiente tras PR55

Esta PR deja preparado el flujo DOI real, pero el despliegue en Cloudflare y la configuración de Brevo siguen siendo manuales y quedan fuera del repositorio.

## Variables y bindings requeridos

- `BREVO_API_KEY` (secret): clave API de Brevo.
- `BREVO_LIST_ID` (variable): ID numérico de la lista canónica. No se inventa ni se fija uno nuevo en esta PR.
- `BREVO_DOI_TEMPLATE_ID` (variable): ID numérico de un template de Brevo válido para double opt-in (`doiTemplate: true`). Debe elegirse/configurarse en la cuenta real.
- `BREVO_DOI_REDIRECT_URL` (variable): `https://davidportodiaz.com/gracias-suscripcion/`.
- `RATE_LIMITER` (binding nativo de **Cloudflare Workers Rate Limiting**): configurar en Cloudflare, por ejemplo 5 solicitudes por 60 segundos. `namespace_id` debe ser un entero positivo único elegido en la cuenta real; no se guarda un ID inventado en el repo.

El Worker usa `POST https://api.brevo.com/v3/contacts/doubleOptinConfirmation`. El navegador nunca envía `listIds`, `templateId`, `redirectionUrl` ni atributos arbitrarios: lista, template y redirect son configuración server-side.

## Rate limiting y modo degradado

El binding `RATE_LIMITER` es la protección de rate limit. Si falta, no expone `.limit()` o lanza una excepción, el Worker **lo registra como error de configuración y continúa sin rate limit**. Ese fail-open es deliberado para no bloquear lectores legítimos por un error de despliegue, pero significa que la protección está desactivada: antes de publicar hay que verificar el binding real. No se debe considerar el Worker protegido solo porque el código contenga la llamada.

La clave enviada al limiter es un SHA-256 del email normalizado, no el email en claro y no una IP compartida.

## Gates externos antes de desplegar

1. Crear/elegir un template DOI real en Brevo y verificar que sea DOI-compatible (`doiTemplate: true`).
2. Configurar `BREVO_DOI_TEMPLATE_ID`, `BREVO_LIST_ID`, `BREVO_DOI_REDIRECT_URL` y el secret `BREVO_API_KEY` en Cloudflare.
3. Crear/configurar el binding `RATE_LIMITER` con un `namespace_id` real del account y el límite acordado.
4. Desplegar manualmente el Worker solo después de que el frontend compatible esté en producción.
5. Hacer un smoke test real con un email de prueba: envío → email DOI → clic de confirmación → `/gracias-suscripcion/`.

Los tests del repositorio usan mocks y no envían emails ni contienen credenciales reales.
