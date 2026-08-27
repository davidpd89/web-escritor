# Claude Toolbox 2026 — plugins, MCP, Skills, APIs y servicios para WEB DAVID PORTO

**Corte de investigación original:** 27 de agosto de 2026  
**Revalidación transversal:** 27 de agosto de 2026, después de PR #114–#119  
**Segundo refresco (esta rama):** 27 de agosto de 2026, rama actualizada contra `main` tras el merge de PR #114–#128 (83 commits de diferencia con la base original de esta PR). Ver correcciones puntuales más abajo -- no se ha reescrito el resto del corpus, que sigue fechado 27/08.  
**Ámbito:** `davidpd89/web-escritor`  
**Estado:** autoridad operativa y backlog; no instala nada por sí sola, no despliega y no contiene credenciales.

## Objetivo

Esta carpeta define qué capacidades externas merece la pena dar a Claude Code/VS Code para trabajar sobre davidportodiaz.com con más criterio, evidencia y capacidad de verificación.

No es una lista de plugins “interesantes”. Cada herramienta entra solo si puede responder una pregunta que hoy importa al proyecto y que el modelo por sí solo resuelve peor: ¿qué está ocurriendo realmente en el navegador?, ¿cómo se ve en un iPhone real?, ¿ha empeorado el layout?, ¿la API moderna que propone está realmente soportada?, ¿ha roto accesibilidad?, ¿el PR contradice el contrato de diseño?, ¿hay una vulnerabilidad?, ¿la documentación de una librería sigue vigente?, ¿el diseño se corresponde con Figma?, ¿el cambio ha afectado CWV reales?

## Principio rector

> Claude no gana criterio por tener 40 herramientas encendidas. Gana criterio cuando la herramienta correcta aporta evidencia independiente en el momento correcto.

Por tanto:

1. **No instalar todo.** El catálogo se clasifica `INSTALL_NOW`, `PILOT`, `ON_DEMAND`, `DEFER` o `REJECT`.
2. **Determinismo antes que opinión.** Browser, LSP, tests, validadores y datos reales tienen prioridad sobre un segundo agente que “opina”.
3. **Autoridad por dominio.** Chrome/Playwright verifican navegador; Figma estructura diseño; axe/WCAG accesibilidad; CrUX rendimiento real; GitHub estado de repo; ninguna herramienta sustituye a todas las demás.
4. **No duplicar capacidades existentes.** Este repo ya fija Playwright, Lighthouse CI, Pa11y y Lychee. Una integración nueva debe añadir algo distinto, no otro score parecido.
5. **OAuth antes que API key.** Si el proveedor ofrece OAuth remoto, se prefiere. Las API keys nunca se guardan en Git ni en un MCP compartido.
6. **Mínimo privilegio.** Lectura/diagnóstico antes de escritura. Las mutaciones de cuentas, DNS, secretos, billing o infraestructura externa siguen requiriendo autorización explícita. Esto no implica convertir cada merge de una PR verde en una aprobación manual: PR #116 está mergeada y, con autorización explícita del propietario, el ruleset `main-production-integrity` ya está activo en `main` (0 aprobaciones requeridas, 4 required checks, force-push/deletion bloqueados -- verificado via `GET /repos/.../rules/branches/main`, no solo documentado). `agente → PR → CI verde → merge → deploy automático de main` ya es el flujo real, no solo el objetivo.
7. **Herramientas de navegador = superficie hostil.** El contenido web puede contener prompt injection. Un agente que lee páginas externas no recibe simultáneamente permisos de deploy, secretos o mutaciones de cuenta sin una frontera clara.
8. **No “AI design by plugin”.** `frontend-design`, Figma y Canva generan hipótesis o artefactos; las decisiones se validan contra los contratos V1, navegador, usuarios, accesibilidad y rendimiento.
9. **Coste de contexto.** Plugins y MCP aportan tools/instrucciones al contexto. Se habilitan por tarea, especialmente los de gran superficie.
10. **Toda instalación tiene propietario, propósito, auth, prueba y criterio de retirada.**

## Estado real del repositorio que condiciona esta estrategia

- Sitio estático HTML/CSS/JS; Node existe principalmente para QA/build tooling, no como framework de aplicación.
- `package.json` ya fija Playwright, Lighthouse CI, Pa11y y Pagefind; antes de añadir equivalentes hay que demostrar un gap.
- Existen workflows de browser QA, CSP, broken links, accesibilidad, contenido, runtime y otros contratos.
- `.claude/settings.local.json` ya no está versionado en `main` (PR #115, mergeada) y `.gitignore` ya cubre el caso. **MERGED_MAIN**, no ya "implemented-in-PR". #115 introdujo por su cuenta una regresión real (borró `/herramientas/auditor-web/` y `/publicar-web/`, que un contrato existente exige preservar como noindex) que pasó desapercibida porque esas rutas no estaban en el filtro de paths del workflow correspondiente; PR #123 restauró los ficheros y amplió el filtro para que el mismo patrón no pueda repetirse en silencio.
- La regresión basal de reflow de Samuel/Noveris que varias PR arrastraban quedó cerrada por PR #119 (mergeada); el residual que quedó específicamente en `/mapa-del-sitio/` se cerró después en PR #125. El toolbox sigue sin necesitar un segundo scanner de reflow.
- GoatCounter se cargaba con un `src` relativo al protocolo (`//gc.zgo.at/count.js`), que resuelve a `https://` en producción real pero a `http://` en cualquier build estático auditado por Lighthouse CI sobre `localhost` -- disparando `is-on-https` (best-practices atascado en 0.82) en **todas** las páginas de **todas** las PR recientes, sin ser un problema real de producción. PR #124 lo cerró hardcodeando el esquema; no instalar ninguna herramienta nueva para "arreglar" Lighthouse antes de comprobar si la causa es esta.
- La auditoría de `npm audit` (13 vulnerabilidades, 10 high) se resolvió con una clasificación de reachability real: todas viven en las dependencias transitivas de `@lhci/cli`/`pa11y-ci` (herramientas de CI, nunca en producción), ambos paquetes ya están en su última versión publicada y no existe upgrade seguro hoy (`npm audit fix --force` solo forzaría un downgrade a versiones de hace años). Ver el hallazgo relacionado: 3 workflows instalaban Playwright 1.55.0 de forma ad-hoc en vez del 1.62.1 pinneado en `package.json` -- unificado en PR #127.
- Cloudflare forma parte del runtime; cualquier plugin Cloudflare se considera de alto privilegio.
- El sistema de diseño V1 y sus contratos existen; el problema no es pedir a una IA una estética nueva, sino aumentar capacidad de observar, contrastar, experimentar y verificar.

## Estado de esta documentación

Esta carpeta fue recuperada de la rama huérfana `docs/claude-plugins-mcp-toolbox-2026`, que había quedado 7 commits por detrás de `main` y sin PR. Solo se han trasladado los 19 artefactos `docs/claude-toolbox/*` sobre una rama fresca de `main`; no se han arrastrado cambios de runtime de la rama antigua.

Esta misma rama (PR #120) quedó después otros 83 commits por detrás mientras seguía en draft. Se ha vuelto a actualizar contra `main` el 27/08/2026 (tras el merge de PR #114-#128) y se han corregido las afirmaciones que describían #115/#116/#119/#124 como pendientes -- ver los cambios puntuales en este README y en `18-REVALIDACION-2026-08-27.md`. Sigue sin mergearse: falta revalidar el resto de `tools-catalog.json` (los `INSTALL_NOW` no tocados en este refresco) contra fuentes oficiales actuales antes de darla por cerrada.

La vigencia de las integraciones con mayor riesgo de caducidad se vuelve a contrastar en `18-REVALIDACION-2026-08-27.md`. Si un documento anterior contradice ese fichero en una cuestión de disponibilidad, autenticación, alcance o gobernanza, prevalece la revalidación hasta actualizar el documento original.

## Lectura recomendada

1. `01-INVENTARIO-Y-DECISIONES.md` — qué entra y qué no.
2. `02-CLAUDE-CODE-VSCODE-PLUGIN-MANAGEMENT.md` — instalación, scopes, updates y confianza.
3. `03-STACK-P0-QUE-CLAUDE-DEBE-INSTALAR.md` — mínimo conjunto de alto retorno.
4. `04-DISENO-UX-BROWSER-Y-DEVICE.md` — navegador, Figma, Canva, BrowserStack, accesibilidad visual.
5. `05-CODIGO-PR-LSP-SKILLS-Y-MEMORIA.md` — navegación de código, PR, skills y memoria del proyecto.
6. `06-SEGURIDAD-Y-SUPPLY-CHAIN.md` — hooks, scanners y límites.
7. `07-RESEARCH-SEO-CONTENIDO-Y-ANALITICA.md` — documentación, investigación y analítica opcional.
8. `08-CLOUDFLARE-Y-PRODUCCION.md` — herramientas con capacidad de afectar producción.
9. `09-MCP-API-KEYS-OAUTH-Y-SECRETOS.md` — modelo de credenciales.
10. `10-APIS-CLIS-Y-WEBS-EXTERNAS.md` — capacidades útiles aunque no sean plugins.
11. `11-PLUGIN-PROPIO-DAVID-PORTO.md` — propuesta de plugin/skills propios.
12. `12-RUNBOOK-INSTALACION-CLAUDE.md` — orden exacto, una capacidad cada vez.
13. `13-BACKLOG-CLAUDE-TOOLBOX.md` — backlog CTB.
14. `14-FUENTES-Y-CORTE-2026-08-27.md` — fuentes primarias y estado original.
15. `15-NO-INSTALAR-Y-ANTI-PATRONES.md` — ruido que no queremos.
16. `16-VSCODE-EXTENSIONS-Y-MCP-EN-EL-IDE.md` — IDE y MCP.
17. `17-SEGUNDA-PASADA-MARKETPLACE-Y-CANDIDATOS.md` — segunda ronda de candidatos/rechazos.
18. `18-REVALIDACION-2026-08-27.md` — correcciones de vigencia y precedencia tras la auditoría transversal.
19. `tools-catalog.json` — versión legible por máquina; una entrada de catálogo no equivale a instalación ni a activación live.

## Relación con otras autoridades

- Search Console gobierna Search Console; una PR documental mergeada no significa cuenta/API/BigQuery configurados.
- Brevo gobierna Reader CRM/email; lista creada no equivale a journey live ni a automatización verificada.
- AI discoverability gobierna recomendación/citación en IA; estrategia mergeada no equivale a servicio externo activado.
- Diseño/UX tooling (#114) gobierna el método de dirección de arte y QA visual.
- Production Integrity (#116) gobierna la promoción PR → main → deploy → producción verificada.
- **Esta carpeta gobierna la adquisición y operación de capacidades de Claude.**

## Definition of Done

La estrategia se considera aplicada cuando:

- Claude tiene un stack mínimo estable, no una colección indiscriminada;
- cada integración puede identificarse por origen, auth y scope;
- no hay secretos en repo;
- `.claude` separa política compartida de estado local;
- los plugins de alto privilegio están desactivados salvo uso explícito;
- existe una skill propia para observar/revisar esta web, con evals;
- un cambio de UI puede recorrer `observe → hypothesize → implement → browser → accessibility → visual diff → device`;
- un PR puede revisarse con GitHub + LSP + tests + seguridad sin duplicar cinco scanners;
- todas las recomendaciones futuras de plugins se contrastan contra `tools-catalog.json`, la revalidación y la documentación oficial vigente antes de instalarse;
- ninguna herramienta aparece como `ACTIVE` o `VERIFIED` solo porque esté documentada.
