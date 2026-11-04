---
name: observatorio-web
description: Auditoría integral y autónoma de davidportodiaz.com en SEO, métricas, redes, afiliación y rendimiento usando Edge 127.0.0.1:9222; investiga, contrasta y corrige fallos reales mediante PR.
---

# Observatorio web: mirar, entender, corregir

Usar cuando el usuario diga «vamos a revisar cómo va todo», «audita toda la web», `/observatorio-web` o equivalente. No pedirle otra vez enlaces, puerto ni credenciales.

1. Leer `docs/observatorio/fuentes.json`; es el inventario de referencia, **no prueba de sesiones activas**. Usar el MCP `observatorio-edge` de Chrome DevTools con Edge en `http://127.0.0.1:9222` y su perfil ya autenticado. Si el MCP tiene otro nombre pero está conectado al mismo Edge, reutilizarlo. Si no conecta, indicar la instrucción única en `docs/observatorio/README.md`, sin inventar que se ha revisado nada. No copiar, extraer ni registrar cookies.
2. Revisar **uno por uno todos los paneles pertinentes**; entrar en secciones y reportes útiles, no limitarse a las portadas. Buscar datos SEO (Search Console, Bing, Ahrefs), tráfico (GoatCounter), comportamiento (Clarity), afiliación (Amazon), redes (Pinterest, Metricool), newsletter (Brevo), operaciones (Cloudflare, GitHub) y diagnóstico externo (PageSpeed y demás). Sin un tope artificial de fuentes, páginas o hallazgos, pero evitar repetir métricas idénticas.
3. Investigar libremente **otras herramientas de SEO, visibilidad en IA, indexación, rendimiento, seguridad, UX, enlaces y analítica** que aporten valor real. Si merecen la pena, incorporarlas al inventario con estado comprobado o pendiente, enlace y utilidad. No registrar cuentas nuevas, activar pagos o instalar trackers sin autorización.
4. Cruzar señales, fechas y periodos razonables (7/28 días cuando haya datos). Distinguir hecho, hipótesis y limitación del proveedor. Verificar cualquier incidencia contra la web pública, la rama `main`, las pruebas y las reglas reales de Google/Bing/etc. «Sin acceso» no significa «cero». Un clic saliente a Amazon no demuestra una venta.
5. **Si el usuario ha pedido revisar y mejorar, actuar:** resolver errores demostrados del sitio con corrección general, prueba de regresión, PR y CI, coordinando otras PR abiertas. No abrir decenas de PR por señales menores ni desactivar puertas de calidad. Si falta evidencia o es una oportunidad estratégica, informar y priorizar. Nunca cambiar datos, pagos, DNS, permisos, correos, campañas ni estados de una cuenta externa sin aprobación expresa.
6. Informe final conciso pero sustancial: qué fuentes y periodos se consultaron de verdad; estado actual; incidencias demostradas y PR creadas/fusionadas; oportunidades priorizadas por impacto; servicios inaccesibles o sin datos. No declarar cerrada una corrección sin verificar el despliegue cuando proceda.

Sin desarrollar una app nueva ni acumular contexto inútil. Guardar notas privadas solo en `.local/observatorio/` (ignorado por Git); no versionar datos sensibles ni informes de cuentas.
