# 09 — MCP, OAuth, API keys y secretos

## Objetivo

Claude debe poder conectar servicios sin convertir el repositorio en un inventario de credenciales. Este documento define dónde vive cada clase de configuración.

## 1. Jerarquía de autenticación

Preferencia general:

1. **OAuth remoto** con proveedor oficial;
2. OAuth/local keychain;
3. API token dedicado y de mínimo scope en entorno local/secret manager;
4. API key genérica solo si el servicio no ofrece mejor mecanismo;
5. credencial escrita en config versionada: prohibido.

## 2. Matriz de integraciones previstas

| Integración | Auth preferida | Variable si aplica | ¿Secreto en repo? | Estado |
|---|---|---|---:|---|
| Figma MCP remoto | OAuth | ninguna key necesaria | No | PILOT |
| BrowserStack remoto | OAuth | ninguna | No | PILOT |
| BrowserStack local | Access key | `BROWSERSTACK_USERNAME`, `BROWSERSTACK_ACCESS_KEY` | No | fallback |
| Context7 | anónimo primero | `CONTEXT7_API_KEY` si se necesita | No | P0 sin key |
| axe MCP | OAuth preferido | `AXE_API_KEY` fallback | No | PILOT |
| Cloudflare | login/OAuth/token mínimo | `CLOUDFLARE_API_TOKEN` si aplica | No | ON_DEMAND |
| Firecrawl | API key | `FIRECRAWL_API_KEY` | No | PILOT |
| Exa | API key/OAuth según integración actual | `EXA_API_KEY` si aplica | No | PILOT |
| CrUX API | Google Cloud API key | nombre dedicado, p.ej. `CRUX_API_KEY` | No | ON_DEMAND |
| WebPageTest | API key si automatizado | `WEBPAGETEST_API_KEY` | No | PILOT |
| GitHub MCP | auth oficial/OAuth/token del cliente | no duplicar PAT si no hace falta | No | P0 |
| Canva | OAuth/MCP oficial | no PAT manual si no es necesario | No | PILOT |
| Semgrep SaaS | token si se adopta servicio | env/CI secret | No | PILOT |

Los nombres pueden cambiar según la documentación del proveedor en la fecha de instalación. Claude debe comprobar la fuente primaria antes de crear cualquier variable.

## 3. Figma

Preferencia:

```bash
claude plugin install figma@claude-plugins-official
```

El plugin configura MCP/Skills y permite autenticar mediante flujo oficial.

Manual remoto:

```bash
claude mcp add --scope user --transport http figma https://mcp.figma.com/mcp
```

Luego `/mcp` → Authenticate.

No usar un personal access token si OAuth remoto resuelve el caso.

## 4. BrowserStack

### Remoto

Endpoint:

```text
https://mcp.browserstack.com/mcp
```

OAuth hereda permisos de la cuenta y evita pasar key.

### Local

```text
BROWSERSTACK_USERNAME
BROWSERSTACK_ACCESS_KEY
```

En shell/secret manager del usuario. No pegar estos valores en `.vscode/mcp.json`, `.mcp.json` ni `.claude/settings.json` versionados.

## 5. axe

Deque documenta OAuth 2.0 o API key.

OAuth:

```bash
npx -y @deque/axe-auth login
```

Requiere actualmente Node 22 LTS+ para ese flujo. Los tokens se gestionan en keychain según su documentación.

Fallback:

```text
AXE_API_KEY
```

No establecer simultáneamente credenciales incompatibles si el setup del plugin indica lo contrario.

## 6. Context7

Comenzar sin key. Solo crear `CONTEXT7_API_KEY` si:

- chocamos con límites;
- existe uso recurrente;
- la mejora de cuota justifica otra credencial.

Esto evita el anti-patrón “crear key para todo lo que podría necesitarla”.

## 7. CrUX / Google APIs

Si se habilita CrUX History/API:

- proyecto Google Cloud específico o apropiado;
- habilitar solo API necesaria;
- key restringida por API y, cuando sea posible, por entorno;
- cuota/usage alerts;
- GitHub Secret si un workflow necesita acceso;
- local env si solo usa Claude/local scripts.

No usar una key genérica que también tenga otras APIs sensibles.

## 8. Secret stores

Orden preferido:

- OAuth/keychain del proveedor;
- secret manager del sistema;
- entorno del usuario;
- GitHub Actions Secrets para CI;
- Cloudflare secret bindings para Workers;
- `.env` local gitignored cuando sea estrictamente necesario.

Nunca:

- `.env.example` con valor;
- markdown;
- PR body/comments;
- screenshot;
- `tools-catalog.json`;
- `.mcp.json` compartido;
- `.claude/settings.json` compartido;
- código source.

## 9. `.env.example`

Puede documentar **nombre y propósito**, nunca valor real:

```text
# Example only; no real value
CRUX_API_KEY=
```

Antes de añadir variables nuevas, comprobar si realmente habrá script/CI que las lea. No coleccionar placeholders innecesarios.

## 10. `.mcp.json`

Puede contener:

```json
{
  "mcpServers": {
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

solo si la sintaxis corresponde a la versión de Claude Code y se decide que project scope es mejor que user scope.

No puede contener secretos.

## 11. `.claude/settings.local.json`

Debe ser local y gitignored. El estado actual del repo contradice ese objetivo, porque está trackeado. Resolver como P0 de hardening.

## 12. GitHub Actions

Si una herramienta necesita CI:

1. secret con nombre específico;
2. environment/repository scope mínimo;
3. workflow permissions mínimos;
4. no exponer secret en logs;
5. no ejecutar sobre forks no confiables con secrets;
6. pin de Actions/dependencies razonable;
7. fallo claro si falta el secret cuando la tarea es obligatoria; skip explícito si es opcional.

## 13. Rotación

Registrar sin valor:

- nombre de credencial;
- proveedor;
- propietario;
- scope;
- dónde se revoca;
- fecha de creación/última revisión;
- consumidores;
- procedimiento de rotación.

No registrar el secret.

## 14. Scopes

### Read-only first

Figma: fichero/lab específico cuando pueda limitarse.  
GitHub: repo específico.  
BrowserStack: usar permisos de cuenta mínimos.  
Cloudflare: read/diagnosis si existe token separado.  
Analytics: read-only.

### Write escalation

Una tool pasa a write solo si una tarea actual necesita una mutación que no se puede hacer por PR/code. La capacidad puede revocarse después.

## 15. API keys compartidas entre herramientas

No reutilizar una key simplemente porque dos tools llaman al mismo vendor. Identidades separadas facilitan:

- revocación;
- auditoría;
- cuotas;
- detectar abuso;
- diferenciar local/CI.

## 16. Test seguro de una credencial

Tras configurar una integración:

1. leer un recurso inocuo;
2. verificar identidad/scope;
3. confirmar que no puede acceder a recursos no necesarios cuando el proveedor permite limitar;
4. evitar mutación en el primer test;
5. revocar y repetir si el scope resultó excesivo.

## 17. Claude nunca pide al usuario pegar la key en chat si existe alternativa

El runbook debe instruir al usuario a configurar la credencial en el UI/CLI/secret store del proveedor. Claude puede indicar el nombre de variable o el comando seguro, pero no necesita ver el valor.

## 18. Inventario de credenciales

`tools-catalog.json` marca `auth`, pero jamás contiene valores. Si en el futuro se necesita inventario operativo, crear un documento solo de nombres/scopes/owners, no de secretos.