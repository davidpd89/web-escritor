# 18 — Revalidación transversal del Claude Toolbox · 27/08/2026

## 0. Por qué existe

La documentación `01–17` fue investigada el 27/08/2026, pero quedó primero en una rama huérfana y el repositorio siguió avanzando durante el mismo día. Esta revisión no vuelve a hacer una lista de herramientas: identifica qué afirmaciones de disponibilidad, autenticación, seguridad o gobernanza han sido contrastadas otra vez contra **fuentes primarias actuales** y contra el estado real del repo.

Regla de precedencia:

> Si un documento `01–17` contradice este fichero sobre estado del repo, modalidad de conexión, autenticación, privilegios o flujo de merge/deploy, prevalece este fichero hasta que el original sea actualizado.

No significa que una herramienta aquí verificada esté instalada. Se mantienen separados:

```text
DOCUMENTED
→ AVAILABLE/VERIFIED-BY-SOURCE
→ INSTALLED-LOCAL
→ CONFIGURED-PROJECT
→ ACTIVE
→ VERIFIED-IN-WORKFLOW
```

## 1. Claude Code plugins — mecanismo real vigente

### Fuente primaria

- https://code.claude.com/docs/en/discover-plugins
- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/plugin-marketplaces

### Confirmado

Claude Code soporta plugins que empaquetan:

- Skills;
- agentes/subagents;
- hooks;
- servidores MCP;
- servidores LSP;
- configuración asociada.

El marketplace oficial es `claude-plugins-official` y está disponible por defecto en Claude Code. La sintaxis documentada es:

```text
/plugin install <plugin>@claude-plugins-official
```

La documentación oficial también distingue scopes `user`, `project`, `local` y `managed`.

### Corrección de seguridad importante

Que un plugin aparezca en un marketplace **no autoriza a tratar todas sus capacidades como inocuas**. Anthropic indica expresamente que debe confiarse en un plugin antes de instalarlo y que un plugin puede incluir MCP, ficheros u otro software con capacidades propias.

Por tanto:

- revisar composición del plugin;
- identificar MCP/commands/hooks que introduce;
- preferir marketplace oficial cuando exista alternativa equivalente;
- no instalar una colección de plugins solo para “dar más inteligencia” a Claude;
- plugin con write/deploy/account access = integración privilegiada aunque el comando de instalación sea sencillo.

## 2. Plugin propio del proyecto

La documentación oficial diferencia:

```text
.claude/ standalone
```

para personalizaciones locales/proyecto rápidas, frente a:

```text
plugin + .claude-plugin/plugin.json
```

para componentes reutilizables/versionados/distribuibles.

Esto valida el enfoque del documento 11, pero introduce una condición adicional:

> No crear el plugin propio `web-david-porto` hasta que existan al menos 2–3 skills/procedimientos que ya hayan demostrado utilidad de forma standalone.

Primero estabilizar el procedimiento; después empaquetarlo. No construir infraestructura de marketplace antes de tener workflows probados.

## 3. Chrome DevTools MCP — revalidado a 25/08/2026

### Fuente primaria

- https://developer.chrome.com/blog/new-in-devtools-152
- repositorio/documentación oficial ChromeDevTools/chrome-devtools-mcp

### Estado actual

Chrome 152, publicado en la documentación de DevTools el **25/08/2026**, referencia Chrome DevTools MCP **v1.7.0** y nuevas capacidades de debugging para agentes.

Por tanto la recomendación sigue vigente y gana valor para este proyecto por:

- inspección DOM/CSS real;
- performance traces;
- network;
- heap/memory cuando corresponda;
- evidencia reproducible antes de tocar CSS;
- diagnóstico de casos como el overflow basal detectado por PR #119.

### Límite crítico

El navegador y el contenido web deben tratarse como input no confiable. Una sesión usada para inspeccionar Internet no debe compartir alegremente capacidad de leer secretos o mutar infraestructura.

Aplicación al proyecto:

```text
browser observation
≠
permission to deploy / change DNS / use secrets
```

## 4. Playwright MCP/CLI — revalidado

### Fuente primaria

- documentación oficial Microsoft Playwright MCP
- paquete oficial `@playwright/mcp`

### Decisión

Mantener el doble papel ya documentado:

- MCP para observación/exploración interactiva;
- Playwright del repo para regresiones deterministas y CI.

No convertir todo descubrimiento interactivo en test. Sí convertir en test los bugs reproducibles con riesgo de volver a aparecer.

Caso real del propio repo:

`Sitewide Reflow QA` detectó cinco overflows que habían entrado en `main`. PR #119 mejora ahora el diagnóstico para identificar los elementos ofensores. Es exactamente el patrón correcto:

```text
observación → causa → fixture/gate durable
```

## 5. Figma MCP — remoto recomendado y escritura real disponible

### Fuentes primarias

- https://developers.figma.com/docs/figma-mcp-server/
- https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/
- https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/

### Confirmado

Figma recomienda actualmente el **Remote MCP server** como opción general y con mayor conjunto de funciones.

Endpoint:

```text
https://mcp.figma.com/mcp
```

Para Claude Code, Figma documenta como vía preferida:

```text
claude plugin install figma@claude-plugins-official
```

porque incluye configuración MCP + Agent Skills.

La configuración manual continúa disponible:

```text
claude mcp add --transport http figma https://mcp.figma.com/mcp
```

con OAuth posterior.

### Cambio de capacidad que Claude debe conocer

Figma MCP ya no debe describirse como una integración de solo lectura/contexto. La documentación actual incluye **write to canvas** y herramientas para crear/modificar contenido nativo, con algunas herramientas solo en remote/clientes concretos.

Por tanto:

- conexión técnica no equivale a permiso para modificar el fichero final;
- usar fichero/laboratorio de diseño autorizado;
- limitar escritura a una tarea explícita;
- conservar navegador como autoridad de comportamiento web;
- Code Connect solo si aparece una arquitectura de componentes real que lo justifique.

## 6. BrowserStack MCP — remoto OAuth es la opción preferida

### Fuentes primarias

- https://www.browserstack.com/docs/browserstack-mcp-server/get-started
- https://www.browserstack.com/docs/browserstack-mcp-server/get-started/remote-mcp-server
- https://www.browserstack.com/docs/browserstack-mcp-server/faqs

### Confirmado

BrowserStack mantiene dos modalidades:

**Remote MCP**

```text
https://mcp.browserstack.com/mcp
```

con OAuth, sin necesidad de copiar username/access key al cliente.

**Local MCP**

usa Username + Access Key y la documentación actual pide Node.js 22+.

### Decisión del proyecto

Preferir remote/OAuth si la cuenta y el cliente utilizados lo soportan. Solo usar credenciales locales cuando exista una razón técnica concreta.

No contratar ni activar plan por adelantado. Primero definir una matriz mínima de dispositivo real que cubra el gap que Chrome emulado no puede cubrir:

- Safari iOS;
- Chrome Android;
- portrait/landscape;
- browser chrome dinámico;
- teclado virtual;
- touch/focus/dialogs.

## 7. Canva MCP — capacidad real amplia, pero rol web limitado por decisión nuestra

### Fuente primaria

- https://www.canva.dev/docs/mcp/

### Confirmado

Endpoint remoto:

```text
https://mcp.canva.com/mcp
```

La documentación actual describe capacidades de:

- crear/editar diseños;
- buscar diseños;
- assets y brand management;
- exportar;
- comentar/colaborar.

La disponibilidad de la conexión no cambia la frontera conceptual del proyecto:

- Canva puede gobernar campaña/media/moodboard/export;
- **no** debe convertirse en fuente de verdad del HTML/CSS responsive;
- Figma/navegador/repo gobiernan composición web, semántica y comportamiento.

## 8. Integraciones con escritura: clasificación obligatoria

A partir de esta revisión, el catálogo debe distinguir:

```text
READ_ONLY
WRITE_SANDBOX
WRITE_PROJECT
ACCOUNT_MUTATION
PRODUCTION_MUTATION
```

Ejemplos:

- Chrome DevTools sobre preview: `READ_ONLY` salvo acciones explícitas de navegador.
- Figma en fichero de laboratorio: `WRITE_SANDBOX`.
- Canva en diseño promocional autorizado: `WRITE_PROJECT`.
- Cloudflare config/secret: `PRODUCTION_MUTATION`.
- Brevo list/template/automation: `ACCOUNT_MUTATION`.

La existencia de OAuth no reduce la categoría de impacto. OAuth mejora gestión de credenciales, no convierte una herramienta de escritura en lectura.

## 9. Gobernanza GitHub actualizada por PR #116

Los documentos originales se redactaron antes de cerrar el modelo operativo de Production Integrity.

Modelo objetivo vigente:

```text
Claude / ChatGPT
→ rama
→ PR
→ CI
→ corrección
→ PR verde
→ merge por agente autorizado
→ main
→ deploy automático
→ verificación exacta de producción
```

Por tanto:

### No requiere clic rutinario del propietario

- crear rama;
- crear/actualizar PR;
- corregir CI;
- mergear PR verde si la integración/agente está autorizado;
- observar el deploy automático derivado de main.

### Sigue requiriendo autorización explícita cuando corresponda

- crear/rotar credenciales;
- activar un servicio de pago;
- cambiar DNS;
- modificar account-level Cloudflare/Brevo/Search Console u otro servicio si no estaba ya autorizado;
- ejecutar una operación externa irreversible o materialmente sensible.

### Estado real hoy

PR #116 todavía está abierta. `main` sigue sin protección. Por tanto esta gobernanza es **IMPLEMENTED-IN-PR / TARGET**, no `CONFIGURED-LIVE`.

Ningún documento debe decir que `main` ya está protegido hasta que el ruleset se active y se haga la prueba conductual.

## 10. Corrección sobre `.claude/settings.local.json`

La rama original observó correctamente que `.claude/settings.local.json` estaba versionado con permisos/rutas locales.

La PR #115 ya implementa:

- eliminación del fichero versionado;
- exclusión en `.gitignore`.

Pero #115 sigue abierta.

Estado correcto:

```text
DOCUMENTED: yes
IMPLEMENTED-IN-PR: yes (#115)
MERGED-MAIN: no
```

No duplicar la corrección en esta PR.

## 11. Dependencias: nuevo gap que el toolbox original no podía conocer

Un run reciente de `npm ci` en GitHub Actions informó:

```text
402 packages audited
13 vulnerabilities
2 low
1 moderate
10 high
```

También aparecen dependencias deprecadas en el árbol de instalación.

Eso **no demuestra** que davidportodiaz.com tenga diez vulnerabilidades high explotables. Este sitio no envía `node_modules` al navegador y muchas dependencias son QA/build tooling.

Pero sí demuestra que falta una autoridad de supply-chain que responda, advisory por advisory:

1. paquete afectado;
2. versión;
3. directo/transitivo;
4. quién lo introduce;
5. producción/browser vs build/CI/dev-only;
6. código vulnerable alcanzable o no en nuestro uso;
7. versión corregida;
8. upgrade mínimo;
9. riesgo de breaking change;
10. acción y deadline.

Regla:

> No ejecutar `npm audit fix --force` como respuesta automática a un contador.

Se debe abrir una auditoría separada de dependencias con evidencia.

## 12. Herramientas de diseño vs problemas actuales

No instalar herramientas para evitar reparar bugs que ya tenemos diagnosticados.

Ejemplos:

- overflow Samuel/Noveris → arreglar PR #119; BrowserStack puede validar después, no sustituir la corrección;
- cache PWA stale → PR #117; no añadir Workbox solo porque existe;
- integridad de deploy → #116; no añadir un segundo servicio de monitoring antes de cerrar el gate;
- Brevo → #118 + verificación live; no añadir CRM alternativo.

## 13. Estado que debe usar Claude al leer `tools-catalog.json`

`tools-catalog.json` representa una **decisión de catálogo**, no realidad instalada.

Interpretación obligatoria:

```text
INSTALL_NOW = recomendado para instalación/piloto cuando corresponda
PILOT       = probar antes de adoptar
ON_DEMAND   = conectar solo ante un caso concreto
DEFER       = no activar todavía
REJECT      = no usar salvo que cambie materialmente el contexto
```

Nunca inferir:

```text
INSTALL_NOW == instalado
PILOT == cuenta creada
ON_DEMAND == credencial disponible
```

## 14. Fuentes de vigencia prioritaria

Para datos susceptibles de cambiar, Claude debe consultar en este orden:

1. documentación oficial actual del proveedor;
2. catálogo/marketplace oficial del proveedor;
3. repositorio oficial/release actual;
4. documentación de esta carpeta como decisión del proyecto;
5. terceros solo para experiencia comparativa, no para afirmar soporte.

Para seguridad, costes y disponibilidad de planes, revalidar el mismo día de la activación.

## 15. Definition of Done de esta recuperación

Esta rama/PR no se considera lista porque se hayan copiado los ficheros antiguos.

Debe comprobarse:

- [x] los 19 artefactos de la rama huérfana están recuperados sobre `main` fresco;
- [x] README deja de afirmar como realidad futura decisiones ya cambiadas por #115/#116/#119;
- [x] Figma remote/write, BrowserStack remote OAuth, Canva MCP y Claude plugin marketplace se contrastan con fuente primaria vigente;
- [x] se registra el nuevo gap de supply-chain sin exagerar el riesgo;
- [ ] revisar `tools-catalog.json` contra estas correcciones y actualizar entradas conflictivas;
- [ ] comprobar que ningún comando `INSTALL_NOW` apunta a paquete/repo inexistente o tercero no confiable;
- [ ] CI transversal verde salvo fallos basales ya poseídos por otra PR y documentados con evidencia;
- [ ] PR real abierta; la rama huérfana anterior deja de ser la autoridad operativa.
