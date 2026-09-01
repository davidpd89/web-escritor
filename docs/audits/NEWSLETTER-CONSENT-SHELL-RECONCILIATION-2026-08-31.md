# Newsletter · reconciliación de consentimiento y wiring del shell

Fecha: 2026-08-31

Estado: contrato funcional previo a implementación. Esta rama parte de #291 (`e568aac1e500ca4cc4b29bbffef3e9e0ae7d10da`). Mantener Draft y sin merge hasta implementar, validar CI del HEAD exacto y revisar el flujo real.

## 1. Motivo

La auditoría final de la pila de diseño detectó un drift objetivo entre la política de privacidad, el cliente de newsletter y el shell global.

No es un cambio estético ni una conclusión jurídica. Es una incoherencia técnica/documental demostrable en el repositorio:

- `privacidad.html` afirma que el formulario de suscripción exige aceptar la política antes de enviarlo;
- el helper genérico `submitNewsletter(formId, emailId, gdprId, statusId, sourceLabel)` recibe `gdprId`, pero actualmente no resuelve ni valida ese control;
- varios formularios generales realmente renderizados no contienen checkbox de consentimiento;
- `assets/newsletter-popup.js` genera otro formulario general real, envía `source: "popup"` y tampoco contiene checkbox;
- Lectores beta sí mantiene consentimiento explícito real, no premarcado, con label y bloqueo de submit;
- el doble opt-in de Brevo/Worker es un segundo paso posterior al envío y no debe confundirse con el consentimiento previo visible en interfaz;
- `#newsletter-form-explore` se genera desde `scripts/build-site-shell.py`, pero páginas V1 como `privacidad.html` cargan `assets/v1-shell.js` y no `script.js`; `v1-shell.js` abre/cierra el diálogo, pero no enlaza ese submit con el flujo DOI.

## 2. Inventario real del HEAD de origen

La implementación NO debe asumir que todo ID histórico de `script.js` corresponde a una superficie visible actual. Se distingue entre superficies activas, fallback, código muerto/latente y contratos separados.

### 2.1 Superficies generales activas con `script.js`

Owner de transporte actual: `script.js`.

1. Fragmento de Samuel
   - formulario: `newsletter-form-fragmento`
   - email: `nl-email-fragmento`
   - consentimiento esperado por la llamada actual: `nl-gdpr-fragmento`
   - status: `nl-status-fragmento`
   - source: `fragmento`

2. Las manecillas del recuerdo
   - formulario: `newsletter-form-manecillas`
   - email: `nl-email-manecillas`
   - consentimiento esperado: `nl-gdpr-manecillas`
   - status: `nl-status-manecillas`
   - source: `manecillas`

3. Cuaderno
   - formulario: `newsletter-form-cuaderno`
   - email: `nl-email-cuaderno`
   - consentimiento esperado: `nl-gdpr-cuaderno`
   - status: `nl-status-cuaderno`
   - source: `cuaderno`

4. Explorar global en páginas que sí cargan `script.js`
   - formulario: `newsletter-form-explore`
   - email: `nl-email-explore`
   - consentimiento esperado: `nl-gdpr-explore`
   - status: `nl-status-explore`
   - source: `explore`

El helper valida hoy email, timeout/offline/429, honeypot y estados DOI/error, pero `gdprId` es un parámetro muerto. El POST general conserva `{ email, source, website }`.

### 2.2 HOME estática / fallback

`index.html` contiene `newsletter-form-home` y la llamada genérica espera `nl-gdpr-home`.

Pero la HOME mejorada por `assets/v1-home-editorial-v3.js` ejecuta `buildFlow()`, inserta el flujo Yale y después elimina el bloque estático `#newsletter` junto con el resto del fallback antiguo. Por tanto:

- el formulario estático debe seguir siendo semánticamente correcto para fallback/no-JS y para cualquier estado en el que el enhancement no llegue a montarse;
- NO debe usarse como prueba de que la HOME mejorada visible mantiene un newsletter inline;
- esta PR no debe reintroducir ni rediseñar por sí sola una franja de newsletter en la HOME mejorada.

### 2.3 HOME dinámica: código latente que NO está renderizado actualmente

Hay dos piezas históricas que no deben confundirse con UI activa:

1. `script.js` llama a `newsletter-form-home-manecillas-card` y vuelve a intentarlo tras `dp:home-editorial-ready`.
2. `assets/v1-home-editorial-v3.js` conserva infraestructura genérica `createActionCard(config)` capaz de generar formularios y define `createYaleSignupStrip()` con `newsletter-form-home-yale`.

Sin embargo, el `buildFlow()` vigente solo añade:

- `createYaleHero()`;
- `createYaleWorksGrid()`;
- `createYaleSamuelFeature()`;
- `createYaleToolsFeature()`;
- `createEvents()`;
- `createInstallBlock()`.

No llama a `createCluster()`, no llega a `createActionCard(config)` y no llama a `createYaleSignupStrip()`.

Consecuencia contractual:

- `newsletter-form-home-manecillas-card` NO es una superficie visible que haya que crear para “cumplir” esta PR;
- `newsletter-form-home-yale` tampoco debe activarse accidentalmente;
- los tests de inventario deben diferenciar bindings muertos/latentes de formularios realmente renderizados;
- si se decide recuperar una franja de newsletter inline en la HOME, eso requiere una decisión de producto/diseño separada o una instrucción explícita, no puede colarse como efecto secundario de este fix;
- durante la implementación se puede retirar o documentar el binding muerto de `newsletter-form-home-manecillas-card` si la ausencia se demuestra de forma determinista, pero no es obligatorio para corregir el consentimiento de las superficies activas.

### 2.4 Popup de newsletter: superficie activa omitida por el primer contrato

Owner: `assets/newsletter-popup.js`.

El popup se carga en familias concretas de Cuaderno, Recomendaciones, Noveris y Clubes de lectura. Genera dinámicamente:

- `#nl-popup-form`;
- `#nl-popup-email`;
- `#nl-popup-submit`;
- `#nl-popup-status`;
- honeypot `website`.

Su submit llama a `postNewsletter()` con:

```js
{
  email,
  source: "popup",
  website
}
```

No existe checkbox ni validación de consentimiento previa. Es newsletter general y, mientras `privacidad.html` mantenga el contrato actual, debe entrar en el mismo cierre funcional.

El popup ya depende de helpers globales de `script.js`; no crear una tercera implementación de transporte.

### 2.5 Explorar en páginas shell-only

`scripts/build-site-shell.py` genera `#newsletter-form-explore` sin checkbox.

`privacidad.html` demuestra el caso crítico:

- contiene el formulario generado de Explorar;
- carga `/assets/v1-shell.js`;
- no carga `script.js`;
- `v1-shell.js` gestiona el diálogo/foco, pero no el submit de newsletter.

Así, el formulario está visible pero no tiene el wiring DOI general en ese arquetipo.

El fix debe operar en el builder y en un owner runtime compartible; no editar a mano las múltiples copias generadas del diálogo.

### 2.6 Lectores beta: contrato separado y referencia positiva

`lectores-beta/index.html` contiene `#lectores-beta-gdpr` como checkbox `required`, no premarcado y asociado a `<label>`.

`script.js` lo resuelve y bloquea el submit si no está marcado. El browser QA de privacidad demuestra:

- email inválido → 0 POST;
- consentimiento sin marcar → 0 POST;
- consentimiento marcado + email válido → exactamente 1 POST;
- `pending_confirmation` → estado DOI, no suscripción confirmada localmente;
- no se añade campo `consent` al payload actual del Worker.

El copy beta es específico de una lista separada y NO debe copiarse literalmente a los formularios generales.

### 2.7 `quiz`: source legado, no superficie de newsletter vigente

`cloudflare-worker-subscribe.js` conserva `quiz` en `SOURCE_MAP`, pero el quiz vigente de Samuel (`assets/samuel-quiz.js`) no captura email ni llama al Worker. El antiguo `quiz-noveris-app` fue retirado y `script.js` lo documenta como código eliminado.

No añadir consentimiento ni newsletter al quiz actual por esta PR. La presencia de `quiz` en el Worker no demuestra una superficie activa.

## 3. Ownership y arquitectura requerida

### 3.1 Un solo contrato funcional

La solución debe evitar implementaciones divergentes del newsletter general.

Preferencia arquitectónica:

- extraer/centralizar transporte + validación de newsletter en un owner reutilizable por `script.js`, `v1-shell.js` y el popup; o
- si se conservan varios puntos de entrada por compatibilidad, compartir una función/contrato común y añadir protección explícita contra doble binding.

No es aceptable copiar una segunda versión independiente de `postNewsletter()` en `v1-shell.js` ni una tercera en `newsletter-popup.js`.

### 3.2 Helper general de consentimiento

Para las superficies que declaren un ID de consentimiento, el runtime debe:

- resolver el checkbox;
- fallar de forma accesible si el control esperado falta;
- bloquear el POST si no está marcado;
- no premarcarlo;
- conservar email validation, timeout, offline, 429, errores recuperables, honeypot y DOI;
- no guardar email ni consentimiento en `localStorage`/`sessionStorage`.

### 3.3 `assets/v1-shell.js` / Explorar

Explorar debe funcionar también en páginas V1 shell-only.

Requisitos:

- mantener teclado, Escape, focus trap y retorno de foco;
- conectar el submit al mismo contrato DOI;
- evitar dos POST si una página carga shell + `script.js`;
- mantener estructura/label/consentimiento legibles sin JS, sin falsa confirmación;
- preservar CSP y scoping existentes.

### 3.4 `scripts/build-site-shell.py`

Modificar el HTML canónico de Explorar para incluir el consentimiento general y regenerar mediante el mecanismo existente.

No editar manualmente decenas de shells generados.

### 3.5 `assets/newsletter-popup.js`

Añadir al popup el mismo consentimiento general:

- checkbox no premarcado;
- label explícito con enlace a `/privacidad.html`;
- bloqueo antes de `postNewsletter()`;
- foco y Tab correctos dentro del `<dialog>`;
- wrapping a 320 px / zoom 200 %;
- conservar cooldown, dismiss, triggers, DOI y estados de error.

### 3.6 HOME

- Corregir `newsletter-form-home` del fallback estático si se mantiene el texto legal vigente.
- NO activar `newsletter-form-home-yale` ni fabricar `newsletter-form-home-manecillas-card` solo porque existan helpers históricos.
- Si se elimina un binding muerto, proteger que la HOME visual vigente no cambia por esa limpieza.

## 4. Copy general de consentimiento

Debe ser breve, claro y enlazar a `/privacidad.html`.

Restricciones:

- no usar wording específico de Lectores beta;
- no afirmar que el checkbox sustituye al doble opt-in;
- no premarcar;
- no esconder el enlace en texto secundario ilegible;
- no introducir una base jurídica nueva ni reinterpretar la política en esta PR.

Si durante implementación se concluye que el texto factual de `privacidad.html` debe cambiar, explicarlo expresamente. No convertir un fix de wiring en asesoramiento jurídico.

## 5. Backend / Worker: límites

El Worker general recibe `{ email, source, website }` y dispara DOI.

`SOURCE_MAP` vigente incluye `home`, `fragmento`, `manecillas`, `cuaderno`, `popup`, `explore`, además de fuentes con otros contratos como `lectores-beta` y el legado `quiz`.

Por defecto, esta PR NO debe:

- añadir `consent` al payload;
- crear columnas/listas/atributos Brevo;
- guardar timestamps o pruebas de consentimiento;
- cambiar listas beta/general;
- eliminar o añadir fuentes de `SOURCE_MAP` sin una razón demostrada independiente;
- alterar el endpoint de producción.

Un checkbox validado solo en frontend prueba el requisito de interfaz previo al envío, pero no crea por sí mismo un registro persistente server-side del asentimiento. Si se necesita evidencia persistente, es una decisión separada de arquitectura/legal/backend.

## 6. QA obligatoria

### 6.1 Contrato estático de cliente

Extender `tests/test-newsletter-client-contract.mjs` para detectar regresión si:

- `gdprId` vuelve a quedar muerto en superficies que lo usan;
- un formulario activo llega a `postNewsletter()` con consentimiento sin marcar;
- el popup queda fuera del inventario;
- se trata `newsletter-form-home-manecillas-card` como formulario visible sin prueba de render;
- se activa `newsletter-form-home-yale` de forma accidental;
- se añade persistencia local de email/consentimiento sin contrato;
- se cambia el payload o `SOURCE_MAP` sin justificación.

Evitar regex frágil cuando sea viable y combinar análisis estático con browser QA funcional.

### 6.2 Browser QA general con Worker interceptado

Cubrir como mínimo:

- HOME fallback/estática cuando ese arquetipo sea accesible en test;
- Fragmento;
- Manecillas;
- Cuaderno;
- popup en una ruta representativa que realmente lo cargue;
- Explorar en una página que cargue `script.js`;
- Explorar en `privacidad.html` o equivalente shell-only;
- HOME mejorada para demostrar que el fix no crea una franja/card de newsletter nueva por accidente.

Por arquetipo relevante:

1. checkbox presente cuando la superficie de suscripción está activa, no premarcado y con label explícito;
2. email inválido → 0 POST;
3. email válido + checkbox sin marcar → 0 POST + mensaje accesible;
4. email válido + checkbox marcado → 1 POST;
5. doble submit durante request pendiente → 1 POST;
6. 201 `pending_confirmation` → copy de confirmación por email, no `subscribed` local;
7. 429 / 500 / timeout / offline → formulario recuperable;
8. sentinel de email no aparece en URL, consola, storage ni requests ajenas al endpoint interceptado;
9. en páginas con más de un runtime → 1 binding efectivo / 1 POST.

### 6.3 Popup QA

Además del transporte:

- el nuevo checkbox entra en el trap de foco en orden lógico;
- clicar su label cambia el control;
- Escape/cierre/dismiss siguen funcionando;
- cooldown no se altera;
- el popup no se apila sobre otro `<dialog>`;
- 320 px, 200 % zoom y text spacing sin overflow.

### 6.4 Legal browser QA

`qa/privacy-contract-browser.mjs` no debe usar Lectores beta como sustituto del formulario general cuando `privacidad.html` contiene `#newsletter-form-explore`.

Mantener el QA beta y añadir separadamente el contrato de Explore general en Legal.

### 6.5 Explore QA

`qa/explore-territories-browser.mjs` debe conservar territorios/foco y añadir que el bloque de suscripción no rompe:

- focus trap;
- Escape;
- 320 px;
- 200 % zoom/text sizing;
- ausencia de overflow;
- label/checkbox accesibles.

### 6.6 Build/paridad

Obligatorio:

- `python scripts/build-site-shell.py --check`;
- QA de navegación/territorios existente;
- test de generación determinista del shell;
- si se toca HOME estática, mantener la paridad/contratos de Home existentes.

## 7. CSS / accesibilidad

Usar el sistema visual existente; no crear un tercer estilo de consentimiento.

El control debe soportar:

- foco visible;
- click/tap sobre label;
- wrapping en 320 px;
- 200 % zoom;
- text spacing;
- `prefers-reduced-motion` sin dependencia funcional de animaciones.

No reducir tipografía o contraste para hacerlo caber.

## 8. Fuera de alcance

- rediseño de #287 Legal;
- rediseño de HOME/#163;
- activar una franja Yale de newsletter hoy no renderizada;
- activar la antigua tarjeta dinámica de Manecillas;
- añadir newsletter al quiz vigente;
- nueva estrategia de email marketing;
- cambios en campañas Brevo;
- consentimiento de cookies/analytics;
- resolver la revisión física Safari/iPhone pendiente de #163;
- merge automático de ninguna PR.

## 9. Criterios de cierre

Esta PR solo puede declararse resuelta cuando:

- todos los formularios generales **realmente activos** auditados muestran y validan consentimiento explícito cuando así lo exige el contrato vigente;
- el popup está incluido;
- `gdprId` deja de ser parámetro muerto para las superficies correspondientes;
- Explore funciona en páginas shell-only;
- no existe doble binding;
- DOI y estados de error siguen intactos;
- Lectores beta permanece aislado;
- el quiz vigente no recibe newsletter por accidente;
- HOME mejorada no gana una nueva superficie de suscripción por efecto secundario;
- el Worker no cambia salvo justificación explícita;
- generación del shell queda en paridad;
- QA estática + browser reproduce los defectos previos y prueba la corrección;
- CI del HEAD exacto queda verde;
- la PR permanece Draft hasta revisión humana.

## 10. Relación con la pila de diseño

Esta PR es funcional y se apila después de #291. #287 no debe absorber esta corrección silenciosamente: su alcance sigue siendo visual/legal-documental y debe referenciar este owner funcional.

Tras implementar y validar esta PR, #291 podrá sustituir el finding abierto de newsletter por una referencia concreta al HEAD certificado de este owner, sin afirmar más de lo que prueben sus tests.

## 11. Taxonomía actual de verdad

Mientras esta rama solo contenga este contrato:

```text
DOCUMENTED = true
FUNCTIONAL_OWNER_ASSIGNED = true
IMPLEMENTED_IN_PR = false
BUG_FIXED = false
MERGED_MAIN = false
CONFIGURED_LIVE = false / no probado
VERIFIED_E2E = false
```

Los workflows heredados verdes prueban únicamente que el cambio documental no rompe el baseline; no prueban el fix funcional.