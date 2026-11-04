# Observatorio de la web — punto de entrada para revisión integral

**Estado (04-11-2026):** acceso y procedimiento preparados; **las cuentas autenticadas no están verificadas desde esta PR**. No existe todavía un almacén agregado de datos ni un sistema que extraiga métricas por API de todos los proveedores.

## Qué es (y qué no)

Un inventario versionado y una rutina **de solo lectura** para Claude Code: revisar SEO, tráfico, UX, afiliación, redes y salud técnica en sus fuentes originales, producir un diagnóstico con evidencias y recomendar tareas con impacto. Reutiliza `docs/search-console/`, `docs/pending/ahrefs-free.md`, la analítica de GoatCounter/Clarity/Metricool y GitHub Actions. No instala otro tracker ni crea un panel público con métricas privadas.

- Inventario legible por máquinas: [fuentes.json](./fuentes.json). **Estado documentado ≠ sesión activa.** Claude actualizará los estados solo con una verificación real y fechada, nunca con suposiciones.
- Entrada de Claude: skill **`/observatorio-web`** en `.claude/skills/observatorio-web/SKILL.md`, disponible al abrir el proyecto en Claude Code.
- Atajo para abrir los paneles en Edge: desde PowerShell, en la raíz, `./scripts/abrir-observatorio.ps1`; `-Grupo seo`, `-Grupo social`, `-Grupo ventas`, `-Grupo comportamiento`, `-Grupo operaciones` o `-Grupo todo`. Por defecto abre solo seis paneles prioritarios. No hace falta servidor local ni puerto.

## Primer uso (una sola vez por equipo/perfil)

1. En **Microsoft Edge**, instala y autoriza la extensión **Claude in Chrome** en el perfil que usarás para los paneles; accede a los servicios con sus métodos oficiales. Las sesiones las conserva Edge, nunca el repositorio. Cualquier nueva autenticación, CAPTCHA o expiración de sesión requiere intervención humana.
2. Abre Claude Code desde la raíz del repo con `claude --chrome`. Usa `/chrome` para comprobar conexión, elegir **Edge** y conceder los permisos por sitio. La primera instalación requiere autorización. **No se puede activar esa conexión desde una configuración Git versionada.**
3. Pídele `/observatorio-web` o «revisa cómo va la web con el observatorio». Leerá el catálogo, visitará los paneles accesibles con sus herramientas de navegador y redactará un único informe; distinguirá «sin acceso» de «cero».
4. Si quieres evitar cargar las herramientas del navegador en sesiones de programación normales, mantenlo desactivado por defecto y usa `--chrome` solo para la revisión. No necesita `--remote-debugging-port` ni cookies exportadas.

Documentación oficial de la integración de Claude Code con Edge: https://code.claude.com/docs/en/chrome

## Qué medir y decidir

Comparar periodos **7 contra 7 días** y **28 contra 28 días** donde el proveedor los ofrezca, anotando fecha de actualización del dato. El objetivo no es copiar 40 cifras, sino descubrir problemas y oportunidades:

- **SEO y visibilidad:** consultas con impresiones y CTR bajo, páginas con caída sostenida, URLs excluidas, errores de sitemap, enlazado interno, backlinks útiles, presencia en Bing e IA (cuando haya informe).
- **Tráfico y comportamiento:** visitas reales, fuentes, rutas de salida, interacciones y fricciones confirmadas. Separar clic a Amazon de venta atribuida; filtrar bots cuando el servicio lo permita.
- **Conversión y comunidad:** Amazon Afiliados, altas efectivamente confirmadas en Brevo, actividad social y clics de Pinterest; medir resultados, no solo impresiones.
- **Calidad operativa:** despliegue publicado, PR abiertas, fallos de CI repetidos, Core Web Vitals de campo si están disponibles, Clarity con consentimiento.
- **Prioridad:** P0 incidencia real de seguridad, indisponibilidad o pérdida crítica; P1 caída contrastada o conversión rota; P2 oportunidad editorial/comercial medida. Toda propuesta debe incluir página/consulta afectada, dato, fecha, impacto estimado y prueba siguiente.

Formato de entrega: `Fecha/fuentes realmente consultadas`, `Resumen de 3 hallazgos`, `P0/P1/P2 con evidencia y decisión`, `Datos inaccesibles o anticuados`, `Siguientes PR sugeridas (sin crearlas salvo petición)`. Se puede guardar **un informe local** en `.local/observatorio/` (ignorado por Git); no subir capturas de cuentas, datos de clientes, tokens ni ingresos individualizados.

## Límites técnicos y próximos pasos opcionales

La extensión de Claude requiere instalación, login y permisos del usuario; el script de PowerShell **solo abre pestañas** y no comprueba que Claude pueda controlarlas. Ningún PR puede iniciar sesión por ti ni garantizar las sesiones futuras.

Cuando la revisión manual justifique una fuente recurrente, priorizar **conector/API de lectura oficial** y almacenamiento privado de métricas agregadas. Añadirlos **uno a uno**, con autorización y costes contrastados: antes de eso, este observatorio ofrece un único procedimiento y evita automatizaciones duplicadas. No generar PR por cada fluctuación de datos.

Referencias internas: `docs/search-console/README.md`, `docs/claude-toolbox/07-RESEARCH-SEO-CONTENIDO-Y-ANALITICA.md`, `docs/claude-toolbox/09-MCP-API-KEYS-OAUTH-Y-SECRETOS.md`, `docs/pending/ahrefs-free.md`, `data/analytics-events.json`.
