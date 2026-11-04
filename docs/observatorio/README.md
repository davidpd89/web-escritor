# Observatorio web — una ventana Edge y una orden a Claude

Sin app adicional: un catálogo de paneles y una rutina para que Claude revise toda la web, encuentre oportunidades y corrija problemas demostrados mediante las PR y pruebas habituales.

## Preparación en Windows (una sola vez)

**1. Abre Edge con el puerto fijo 9222.** Desde PowerShell en `C:\GIT\web-escritor`:

```powershell
.\scripts\abrir-observatorio.ps1
```

Se abren todas las webs de `fuentes.json`. Inicia sesión en cada una; Edge conserva el acceso en `%LOCALAPPDATA%\web-escritor\edge-observatorio`, mientras el proveedor lo permita. Es un perfil independiente del Edge normal. Para abrir menos páginas: `-Grupo seo`, `-Grupo comportamiento`, `-Grupo social`, `-Grupo ventas`, `-Grupo operaciones` o `-Grupo inicio`.

**2. Conecta Claude Code una vez al mismo puerto, solo en este proyecto** (en terminal, no dentro de Claude):

```powershell
claude mcp add --scope local observatorio-edge -- npx -y chrome-devtools-mcp@latest --browser-url=http://127.0.0.1:9222
```

Comprueba `claude mcp list` y `/mcp`. Si ya tienes configurado Chrome DevTools MCP para **este mismo puerto**, reutilízalo en lugar de duplicarlo.

**3. Uso habitual:** abre Claude Code en el repo y di `/observatorio-web` o «Revisa cómo va toda la web, analiza oportunidades y corrige los problemas reales». El puerto y las fuentes ya están en la skill. El Edge del observatorio debe seguir abierto durante la revisión.

## Alcance

- `fuentes.json` recoge los paneles ya usados/documentados (Search Console, Bing, Ahrefs, GoatCounter, Clarity, Amazon, Pinterest, Metricool, Brevo, Cloudflare, GitHub) y otras herramientas públicas de diagnóstico (PageSpeed, WebPageTest, GTmetrix, Rich Results, Schema.org, Google Trends).
- Claude recorre los paneles pertinentes **uno por uno y en profundidad**, cruzando datos con la web y CI. También puede investigar nuevas fuentes útiles y proponer incorporarlas al catálogo, sin instalar rastreadores o suscripciones inútiles.
- Si detecta un defecto verificable de la web, lo corrige en el repo, añade pruebas y utiliza PR/CI. Si es una oportunidad editorial o requiere tocar cuentas externas, documenta la evidencia y la acción recomendada.
- No todas las cuentas tienen API. Se usa la sesión de Edge cuando existe; los estados en el catálogo **no significan que estén logueadas ahora**.

## Precaución

`127.0.0.1:9222` da a cualquier proceso local acceso de control a ese perfil Edge **y sus sesiones**. Utiliza un ordenador de confianza y cierra la ventana del observatorio al acabar. Nunca expongas ese puerto en red ni introduzcas el perfil personal, cookies o claves en el repo. Los nuevos logins, CAPTCHA y expiraciones requieren al usuario.

Esta PR prepara archivos, **no verifica las sesiones ni instala MCP en tu ordenador**. Hay que hacer un smoke real en Windows antes de darla por probada. Documentación: https://learn.microsoft.com/en-us/microsoft-edge/web-platform/devtools-mcp-server · https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/advanced-usage.md · https://code.claude.com/docs/en/mcp.
