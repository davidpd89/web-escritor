# Brevo Worker: despliegue pendiente tras PR55

Esta PR deja preparado el flujo, pero el despliegue real en Cloudflare requiere configuración manual fuera del repo.

## Variables y bindings requeridos

- `BREVO_API_KEY` (secret): clave API de Brevo
- `BREVO_LIST_ID` (variable): ID numérico de la lista canónica
- `BREVO_DOI_REDIRECT_URL` (variable): `https://davidportodiaz.com/gracias-suscripcion/`
- `RATE_LIMIT_KV` (KV binding): namespace KV real para rate limiting

## Nota operativa

- Sin un namespace enlazado en `RATE_LIMIT_KV`, el Worker mantiene comportamiento fail-open (no bloquea por rate limit).
- La URL de retorno DOI debe coincidir con la configurada en Brevo para evitar redirecciones rotas tras la confirmación por email.
