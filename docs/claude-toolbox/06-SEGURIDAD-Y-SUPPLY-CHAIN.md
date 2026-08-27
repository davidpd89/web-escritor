# 06 — Seguridad y supply chain de plugins/MCP

## 1. Modelo de amenaza

Dar una tool a Claude no equivale a instalar una extensión pasiva. Un plugin puede incluir:

- hooks que se ejecutan al editar/usar Bash;
- servidores MCP locales con ejecución de procesos;
- MCP remotos que reciben contexto/datos;
- comandos y subagents;
- LSP servers;
- acceso a repo, navegador, cuentas y servicios externos.

El riesgo no se limita a “que la extensión sea maliciosa”. También existe:

- plugin legítimo comprometido;
- update que amplía capacidades;
- prompt injection de una web que alcanza un agent con tools potentes;
- secreto escrito en config;
- OAuth con scopes innecesarios;
- cadena NPM/npmx sin pin/review;
- cinco scanners dando una falsa sensación de seguridad.

## 2. Orden de confianza

1. Anthropic Verified / marketplace oficial.
2. Plugin de vendor reconocido dentro de marketplace oficial.
3. Marketplace/repo oficial del vendor.
4. Community marketplace de Anthropic después de revisar source.
5. Repo de tercero con reputación/evidencia y revisión manual.
6. Marketplace desconocido: bloqueado.

El marketplace oficial tampoco elimina la necesidad de revisar permisos y finalidad.

## 3. Security Guidance — siempre activo

```bash
claude plugin install security-guidance@claude-plugins-official
```

Hook Anthropic Verified para advertir antes de introducir patrones peligrosos. Especialmente relevante:

- XSS via `innerHTML`;
- `eval`/`new Function`;
- shell/child process injection;
- GitHub Actions injection;
- Python command/deserialization hazards.

### Limitación

Es prevención contextual, no scanner exhaustivo. Un warning que no salta no certifica seguridad.

## 4. Hookify — seguridad del workflow

```bash
claude plugin install hookify@claude-plugins-official
```

Reglas propias propuestas:

### Branch

Bloquear/warn:

```text
git checkout main && write
git push origin main
git commit while current branch == main
```

La implementación exacta debe respetar la sintaxis del plugin actual; no copiar regex conceptual como producción sin validar.

### Secrets

Warn/block si un edit añade patrones:

- `BREVO_API_KEY=` con valor real;
- `BROWSERSTACK_ACCESS_KEY=`;
- `AXE_API_KEY=`;
- `CONTEXT7_API_KEY=`;
- `FIGMA_TOKEN=` si alguna integración futura usa PAT;
- `CLOUDFLARE_API_TOKEN=`;
- bearer tokens/JWT/private keys.

Permitir nombres/placeholders en `.env.example` sin valor real.

### Deploy

Advertir/bloquear por defecto:

- `wrangler deploy`;
- Pages/Workers production mutation;
- DNS changes;
- secret put;
- GitHub merge command.

Solo una autorización explícita de la tarea debe permitirlo.

## 5. Claude Security — gate de alto riesgo

```bash
claude plugin install claude-security@claude-plugins-official
```

Clasificación: ON_DEMAND.

Ejecutar ante:

- cambios de Worker/API;
- input sanitization;
- CSP/auth/Turnstile/rate limits;
- nuevos webhooks;
- nueva third-party script;
- cambios de secrets/config;
- preparación de lanzamiento.

No ejecutar la suite completa por un cambio de `font-size`.

## 6. Elegir un scanner determinista adicional, no tres

### Semgrep — candidato preferente a pilot

Ventajas:

- reglas deterministas;
- feedback sobre code patterns;
- utilidad en JS/Python/YAML;
- encaja como segunda capa junto a hooks.

Pilot:

1. snapshot de findings actuales;
2. eliminar falsos positivos obvios/configurar scope;
3. ejecutar sobre 5 PRs sensibles;
4. medir findings reales que no detectan tests/Security Guidance;
5. decidir si merece CI permanente.

### SonarQube — defer

Es una plataforma más amplia de quality/security. No montar un servicio/quality gate solo para obtener un dashboard adicional. Reabrir si:

- el repo/organización crece;
- se adopta Sonar Cloud por otra razón;
- necesitamos gobernanza/quality profiles centralizados.

### Aikido — defer

SAST/secrets/IaC potente, pero mismo solapamiento. Elegirlo solo si una prueba demuestra mejor ajuste/operación que Semgrep.

### 42Crunch — N/A ahora

Excelente para OpenAPI/API Security, pero `web-escritor` no gira alrededor de una especificación OpenAPI. No instalar una suite API porque exista.

## 7. Secrets scanner

Antes de añadir otro producto, verificar qué cubre ya GitHub/CI y usar herramientas nativas cuando existan. Si se incorpora un secrets scanner, debe bloquear **nuevos** secretos sin convertir ejemplos/documentación en ruido permanente.

Nunca guardar una credencial “temporal” pensando rotarla después.

## 8. NPM/npx

Varios MCP locales se lanzan con `npx`.

Reglas:

- vendor package exacto;
- documentar package name;
- preferir `@latest` solo en setup exploratorio si el proveedor lo recomienda; para CI/infra reproducible considerar pinning/version policy;
- revisar changelog antes de upgrades sensibles;
- Node LTS compatible;
- no instalar globalmente si no hace falta;
- no ejecutar package desconocido copiado de un post/blog.

## 9. Remote MCP y exfiltración

Antes de conectar un MCP remoto:

1. qué datos recibe;
2. qué tools expone;
3. dónde se procesan/retienen;
4. OAuth scopes;
5. si el proveedor puede acceder a source/private content;
6. si la cuenta contiene información no relacionada;
7. política para desactivar/revocar.

Un endpoint HTTPS no garantiza que el proveedor sea correcto: verificar siempre con documentación oficial.

## 10. Prompt injection

Particularmente crítico en:

- Chrome/Claude in Chrome;
- Firecrawl/Exa;
- Playwright sobre sitios externos;
- BrowserStack navegando terceros;
- GitHub issues/PRs de usuarios externos;
- documentos de terceros.

### Separación recomendada

**Sesión de research externa**:
- read-only repo;
- browser/search tools;
- sin Cloudflare deploy;
- sin secret mutation;
- sin email/CRM write.

**Sesión de implementación**:
- repo write;
- localhost/staging;
- fuentes ya seleccionadas;
- no navegar sitios aleatorios con permisos de producción cargados.

Anthropic recomienda además perfiles de navegador separados y evitar páginas sensibles al usar Claude en Chrome.

## 11. Auto-update

Política por clase:

- LSP/documentation skills: update normal, revisar si rompe.
- browser MCP: revisar release material cuando cambian capabilities.
- repo write/deploy/account plugins: revisar fuente/changelog y scopes.
- vendor marketplace third-party: auto-update controlado.

Registrar en `tools-catalog.json` `last_verified` y `source`.

## 12. OAuth revocation y key rotation

Para cada integración autenticada debe existir una respuesta a:

- ¿dónde revoco OAuth?
- ¿dónde roto la key?
- ¿qué variable la contiene?
- ¿qué acciones deja de funcionar al revocar?

No usar la misma key de producción para CI, portátil y un MCP si el servicio permite separar identidades.

## 13. No convertir `.mcp.json` en un vault

Puede versionarse configuración pública, por ejemplo un endpoint remoto sin credencial. No puede contener:

```json
{
  "env": {
    "BROWSERSTACK_ACCESS_KEY": "real-secret"
  }
}
```

Preferir OAuth o env local/keychain.

## 14. Seguridad del plugin propio

Si creamos `david-porto-web`:

- sin red por defecto;
- sin secretos;
- Skills declarativas antes que hooks ejecutables;
- hooks pequeños y auditables;
- no incluir shell general-purpose;
- no auto-deploy;
- tests/evals;
- manifest mínimo;
- versionado/changelog;
- revisión de plugin-dev antes de publicar/compartir.

## 15. Incident response

Si un plugin/MCP parece comprometido o hace algo inesperado:

1. deshabilitar;
2. cerrar sesión/revocar OAuth;
3. rotar keys potencialmente expuestas;
4. revisar git/worktree y comandos ejecutados;
5. inspeccionar logs de proveedor cuando existan;
6. revisar cambios en cuentas externas;
7. eliminar config/cache si el vendor lo recomienda;
8. documentar incidente y criterio de reinstalación;
9. no “arreglarlo” simplemente actualizando a ciegas.

## 16. Gate de incorporación

Un plugin de escritura o cuenta externa no pasa a `INSTALL_NOW` sin:

- vendor/source verificado;
- finalidad única;
- test sandbox;
- auth documentada;
- revocation documentada;
- privacidad evaluada;
- solapamiento revisado;
- riesgo de prompt injection considerado;
- al menos un caso de uso real del proyecto.