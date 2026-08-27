# 12 — Seguridad, credenciales, costes y privacidad

## 1. Objetivo

El stack de diseño propuesto incluye servicios externos, OAuth, posibles API keys y herramientas que pueden observar la web o datos de usuarios.

La regla es simple:

> **Esta PR documenta qué configurar; no crea ni activa ninguna credencial, integración, tracking o servicio real.**

Cada activación futura necesita autorización explícita y mínimo privilegio.

## 2. Clasificación de acceso

### Clase A — sin secreto

- Chrome DevTools local;
- Playwright local;
- scripts propios de captura/auditoría;
- WCAG/MDN/web.dev;
- referencias web públicas.

Configurar primero.

### Clase B — OAuth

Preferido cuando el proveedor lo soporta:

- Figma MCP;
- Canva MCP;
- Stark MCP;
- BrowserStack remoto si la modalidad disponible ofrece OAuth.

Ventaja: no copiar tokens manualmente al repo.

### Clase C — API key/token

- BrowserStack local;
- Percy;
- Chromatic;
- axe según modalidad;
- CrUX/PSI;
- otras APIs aprobadas.

Guardar en secret store, nunca en Git.

### Clase D — tracking/observación de usuarios

- Clarity;
- cualquier session replay/heatmap/analytics adicional.

Requiere privacy gate independiente.

## 3. Matriz de secretos

| Servicio | Credencial | Repo | GitHub Secret | Local env | Comentario |
|---|---|---:|---:|---:|---|
| Figma | OAuth | NO | normalmente no | gestionado por cliente | preferido |
| Chrome DevTools | ninguna | — | — | — | local |
| Playwright | ninguna local | — | — | — | browsers locales |
| BrowserStack | username + access key si local | NO | SÍ si CI autorizado | SÍ | remoto OAuth preferible |
| Percy | `PERCY_TOKEN` | NO | SÍ | SÍ | solo si se elige Percy |
| Chromatic | project token | NO | SÍ | SÍ | solo si se elige Chromatic |
| Stark | OAuth | NO | normalmente no | gestionado | revisar plan |
| axe | OAuth/API key según setup | NO | si CI | si local | mínimo privilegio |
| CrUX | API key restringida | NO | si automatiza | SÍ | limitar API |
| PSI | API key restringida | NO | si automatiza | SÍ | puede compartir proyecto, no necesariamente key |
| Canva | OAuth | NO | normalmente no | gestionado | media, no layout web |
| Clarity | project/config | no secretos sensibles por diseño, pero no hardcodear decisiones sin gate | según integración | — | privacidad antes de activar |

## 4. GitHub Secrets

Solo crear secrets cuando exista:

1. integración aprobada;
2. workflow real que los necesita;
3. nombre documentado;
4. owner;
5. rotación/revocación;
6. criterio de retirada.

No crear una doc PR con placeholders que luego alguien sustituye por valores reales en Markdown.

## 5. `.env.example`

Si una implementación futura necesita variables locales, `.env.example` solo contiene **nombres**, nunca valores reales:

```dotenv
BROWSERSTACK_USERNAME=
BROWSERSTACK_ACCESS_KEY=
PERCY_TOKEN=
CRUX_API_KEY=
```

Añadir únicamente las variables de servicios realmente aprobados.

No llenar el ejemplo con 20 herramientas «por si algún día».

## 6. Principio de mínimo privilegio

### Figma

Empezar por lectura/contexto y canvas de laboratorio. No dar capacidad operativa más amplia de la necesaria.

### BrowserStack/Percy

Proyecto dedicado al sitio cuando compense, no token global reutilizado entre proyectos sin necesidad.

### Google API key

- restringir APIs;
- restringir origen/IP cuando sea compatible con el uso;
- no utilizar una key sin restricciones para CrUX/PSI.

### axe/Stark

Elegir scope mínimo para auditoría/proyecto piloto.

## 7. Identidades separadas

Cuando un proveedor permita nombrar tokens/clients, usar nombres funcionales:

```text
claude-web-design-audit
web-escritor-visual-ci
web-escritor-crux-read
```

Evitar `token2`, `test`, `claude` sin contexto.

## 8. Rotación

Para keys persistentes:

- owner;
- createdAt;
- lastRotatedAt;
- scope;
- whereUsed;
- revoke procedure.

No guardar esos datos sensibles en documentación pública si revelan información operativa innecesaria. Puede mantenerse un inventario privado.

## 9. Logs

Los scripts/workflows nunca deben imprimir:

- access keys;
- bearer tokens;
- OAuth refresh tokens;
- full request headers;
- URLs con secrets query string.

Sanitizar errores de terceros.

## 10. Pull requests desde forks

Si alguna vez se habilita CI visual en PRs externos/forks, recordar que los secrets no deben exponerse automáticamente.

Diseñar workflows que:

- fallen de forma informativa;
- salten la integración externa;
- o utilicen entornos aprobados;

sin imprimir secretos.

## 11. Costes: principio

No contratar herramientas por catálogo de features.

Cada servicio pasa un **pilot gate**.

### Preguntas

- ¿qué problema resuelve?;
- ¿ya lo resuelve una herramienta actual?;
- ¿cuántas veces al mes se usa?;
- ¿cuánto tiempo ahorra?;
- ¿detectó bugs que no veíamos?;
- ¿mejora review/decisión?;
- ¿podemos retirarlo fácilmente?

No fijar aquí precios: cambian y dependen de plan/región. Claude debe verificar la página oficial el día de contratación.

## 12. Orden de coste recomendado

### Cero/bajo coste primero

- Chrome DevTools;
- Playwright;
- scripts propios;
- Figma con acceso disponible;
- WCAG;
- tests manuales.

### Después

- BrowserStack si el gap real-device existe;
- un visual regression service;
- un a11y expert tool;
- Maze cuando haya pregunta UX.

### Último

- servicios de recording persistente;
- enterprise design governance;
- herramientas duplicadas.

## 13. Duplicidad

No pagar simultáneamente por:

- Percy + Chromatic sin caso distinto;
- Stark + axe de forma permanente antes del piloto;
- varias granjas de devices;
- múltiples session replay tools;
- varios page builders/prototypers que creen fuentes de verdad paralelas.

## 14. Clarity y privacidad

El estado actual no incluye session recording.

Activarlo cambia materialmente el modelo de privacidad.

Antes:

### Producto

- definir pregunta;
- periodo;
- páginas;
- necesidad.

### Legal/privacy

- requisitos EEA vigentes;
- consentimiento válido cuando corresponda;
- política de privacidad;
- retención;
- masking;
- tratamiento de formularios;
- audiencia.

### Técnica

- CSP;
- performance;
- loading;
- opt-in/consent mechanism;
- QA staging/prod.

### Cierre

- fecha de evaluación;
- decidir keep/remove;
- retirar si no aporta.

## 15. Maze y participantes

No guardar PII de participantes en GitHub.

Los informes deben usar:

- IDs anónimos;
- segmento;
- resultado agregado/cualitativo;
- citas solo con consentimiento y minimizadas.

## 16. Screenshots y datos

Los evidence packs pueden mostrar:

- emails introducidos en forms;
- nombres;
- query params;
- dashboards.

Usar datos de prueba.

Nunca capturar el panel de un servicio con tokens/PII y subirlo a una PR pública.

## 17. Producción vs preview

Herramientas de observación deben preferir preview/staging para cambios.

Si se testea producción:

- read-only;
- no submit real de newsletter repetido;
- no crear contactos/test data;
- no activar compras;
- no cambiar paneles.

## 18. Figma/Canva assets

No asumir que un asset encontrado en una cuenta tiene permiso para publicación web.

Registrar provenance/rights independientemente del acceso técnico.

OAuth da permiso para acceder, no derechos de autor.

## 19. MCP supply-chain

Preferir:

1. MCP oficial del proveedor;
2. plugin oficial;
3. repositorio oficial verificado;
4. tercero solo tras revisión.

Antes de instalar un MCP de terceros:

- maintainer;
- package/repo;
- permissions;
- transport;
- secrets;
- network access;
- update policy;
- open issues/security.

No instalar un MCP aleatorio porque su nombre sea `ux-expert`.

## 20. `npx ...@latest`

Es cómodo para setup exploratorio, pero para automatización estable considerar versión fijada/revisada para evitar cambios inesperados.

Proceso:

- probar latest;
- registrar versión que pasó el pilot;
- revisar updates conscientemente.

## 21. MCP remoto vs local

### Remoto/OAuth

Preferible cuando:

- es oficial;
- scopes claros;
- evita secrets locales;
- proveedor mantiene endpoint.

### Local

Útil para:

- browser tooling;
- Playwright;
- servicios que requieren entorno local;
- mayor control.

No exponer un servidor MCP local a red pública.

## 22. Herramientas con write access

Figma/Canva y otros MCP pueden escribir.

Regla:

- laboratorio dedicado;
- no modificar assets/ficheros finales sin tarea explícita;
- no borrar;
- no publicar;
- no exportar masivamente;
- review antes de sustituir un diseño aprobado.

## 23. Approval matrix

| Acción | Puede Claude hacerla directamente en futuro | Requiere usuario |
|---|---:|---:|
| instalar Chrome/Playwright local | si se autoriza entorno | — |
| leer web/repo | sí | — |
| crear docs/scripts en rama | sí | — |
| conectar OAuth Figma | no | SÍ |
| crear BrowserStack key | no | SÍ |
| crear Percy/Chromatic token | no | SÍ |
| activar Clarity | no | SÍ explícito |
| modificar privacidad/CSP por tracking | rama sí; activación no | SÍ para activación |
| crear Google API key | no | SÍ |
| contratar plan | no | SÍ |
| actualizar baseline visual | propuesta sí | review/criterio del PR |
| merge/deploy | no por esta documentación | SÍ/flujo autorizado |

## 24. Inventario de integraciones

Proponer un fichero privado/operativo futuro con:

```yaml
service:
status: proposed|pilot|active|retired
owner:
purpose:
auth:
secretNames:
scopes:
createdAt:
reviewAt:
removeProcedure:
```

No incluir valores.

## 25. Gate final

Una herramienta de diseño no se activa si no sabemos:

- qué pregunta responde;
- qué datos ve;
- qué puede escribir;
- qué credenciales requiere;
- cuánto cuesta;
- cómo se revoca;
- cómo se prueba;
- quién aprueba.

El objetivo es mejorar diseño sin convertir el proyecto en una colección opaca de integraciones.