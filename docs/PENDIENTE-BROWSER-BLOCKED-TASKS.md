# Tareas bloqueadas para el asistente — requieren acción manual del autor

Fecha: 2026-08-26

## Por qué existe este documento

El autor ha reportado que, varias veces esta sesión, controlar el navegador del asistente sobre un panel de terceros que exige inicio de sesión (Groq, Spaceship) coincidió con el bloqueo/cierre de la aplicación, obligando a reinstalar. No hay forma de diagnosticar la causa raíz desde el lado del asistente (es un fallo de la aplicación anfitriona, no del código de este repo), así que la medida prudente es **evitar que el asistente conduzca el navegador sobre paneles de terceros que requieran login**, y dejar esas tareas documentadas aquí para que el autor las haga directamente.

El asistente sigue pudiendo usar el navegador con normalidad sobre: el servidor de desarrollo local (`localhost`) y la web pública ya desplegada (`davidportodiaz.com`, sin login) — ninguna de esas dos coincidió con ningún bloqueo.

## Pendiente 1 — Cloudflare AI Search: crear el token de API

`wrangler ai-search create` exige un token de API específico para AI Search que solo se genera desde el dashboard:

1. Entra en https://dash.cloudflare.com/77a008227d663ec8661f1e4422289c1b/ai/ai-search/tokens
2. Crea un token (botón "Create token" o similar).
3. Pásame el valor del token (o dímelo y lo guardo yo como secret de Wrangler sin que quede en texto plano en el chat — mejor pégalo directamente cuando te lo pida por separado).

Con ese token puedo terminar de crear la instancia (`david-porto-site-search`, tipo `web-crawler`, indexando `https://davidportodiaz.com/sitemap.xml`) sin más pasos manuales.

## Pendiente 2 — Brevo: revisión de campañas, listas y automatizaciones

Necesito trabajar en el dashboard de Brevo (`app.brevo.com`) para revisar campañas existentes, crear la campaña de lanzamiento de *Las manecillas del recuerdo*, listas/segmentos y recordatorios — pero:

- La API de Brevo (`BREVO_API_KEY` en `.env`) está bloqueada para este entorno: Brevo exige autorizar la IP de origen (`Security > Authorised IPs` en su dashboard), y esa IP es propia de este entorno de ejecución, no una IP fija tuya — autorizarla no sería una solución duradera.
- El dashboard en sí requiere sesión iniciada, justo el tipo de interacción que coincidió con los bloqueos anteriores.

**Recomendación**: hazlo tú directamente en `app.brevo.com`. Lo que ya existe en el código, para que sepas desde dónde partir:
- Worker de suscripción ya desplegado y funcionando (`subscribe.davidpd89.workers.dev`), con dos listas separadas: `BREVO_LIST_ID` (newsletter general) y `BREVO_BETA_LIST_ID` (lectores beta) — nunca se mezclan.
- Flujo de doble opt-in (DOI) ya implementado en el frontend (`assets/newsletter-popup.js`, formularios en todo el sitio).
- Lo que falta es trabajo de contenido/dashboard: plantilla de campaña de lanzamiento de Manecillas, secuencia de recordatorios, y decidir si se crea una lista/segmento específico para "avisar cuando salga Manecillas" o se reutiliza la general.

Si prefieres que lo intente yo asumiendo el riesgo de bloqueo, dímelo explícitamente y lo hago con cuidado (guardando el progreso a menudo).

## Pendiente 3 — Google Search Console

No tengo evidencia de haber llegado a usarlo esta sesión (no encontré ninguna acción completada ahí). Igual que Brevo, es un dashboard con sesión iniciada de terceros. Necesito que confirmes:
- Si la propiedad de `davidportodiaz.com` ya está verificada en Search Console.
- Si quieres que lo intente yo (mismo riesgo de bloqueo que arriba) o prefieres revisarlo/enviarme capturas o exports tú.

Lo que normalmente haría ahí una vez tenga acceso seguro: comprobar cobertura de indexación, enviar el sitemap (`https://davidportodiaz.com/sitemap.xml`), revisar errores de rastreo y Core Web Vitals reportados.
