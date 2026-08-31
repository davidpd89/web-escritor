# Newsletter · reconciliación de consentimiento y wiring del shell

Fecha: 2026-08-31

Estado: contrato funcional previo a implementación. Esta rama parte del HEAD exacto de #291 (`e568aac1e500ca4cc4b29bbffef3e9e0ae7d10da`). Mantener Draft y sin merge hasta implementar, validar CI y revisar el flujo real.

## 1. Motivo

La auditoría final de la pila de diseño detectó un drift objetivo entre la política de privacidad, el cliente de newsletter y el shell global.

No es un cambio estético ni una conclusión jurídica. Es una incoherencia técnica/documental demostrable en el repositorio:

- `privacidad.html` afirma que el formulario de suscripción exige aceptar la política antes de enviarlo;
- el helper genérico `submitNewsletter(formId, emailId, gdprId, statusId, sourceLabel)` recibe `gdprId`, pero actualmente no resuelve ni valida ese control;
- los formularios genéricos auditados no contienen el checkbox que esos IDs describen;
- Lectores beta sí mantiene un consentimiento explícito real, no premarcado, con label y bloqueo de submit;
- el doble opt-in de Brevo/Worker continúa siendo un segundo paso posterior al envío y no debe confundirse con el consentimiento previo visible en la interfaz;
- el formulario global de `Explorar` se genera desde `scripts/build-site-shell.py`, pero páginas V1 como `privacidad.html` cargan `assets/v1-shell.js` y no `script.js`; `v1-shell.js` abre/cierra el diálogo, pero no enlaza el submit de `#newsletter-form-explore` con el flujo DOI.

## 2. Evidencia exacta en el HEAD de origen

### 2.1 Helper genérico

Owner actual: `script.js`.

Llamadas auditadas y sus IDs de consentimiento ya declarados en la firma/call site:

1. HOME estática
   - formulario: `newsletter-form-home`
   - email: `nl-email-home`
   - consentimiento esperado: `nl-gdpr-home`
   - source: `home`
2. Fragmento
   - formulario: `newsletter-form-fragmento`
   - consentimiento esperado: `nl-gdpr-fragmento`
   - source: `fragmento`
3. Las manecillas del recuerdo
   - formulario: `newsletter-form-manecillas`
   - consentimiento esperado: `nl-gdpr-manecillas`
   - source: `manecillas`
4. HOME · tarjeta dinámica de Manecillas
   - formulario: `newsletter-form-home-manecillas-card`
   - consentimiento esperado: `home-manecillas-card-gdpr`
   - source existente: preservar el que usa la llamada actual; no introducir una fuente nueva por esta PR
5. Cuaderno
   - formulario: `newsletter-form-cuaderno`
   - consentimiento esperado: `nl-gdpr-cuaderno`
   - source: `cuaderno`
6. Explorar global
   - formulario: `newsletter-form-explore`
   - consentimiento esperado: `nl-gdpr-explore`
   - source existente: preservar el que usa la llamada actual; no ampliar `SOURCE_MAP` por esta PR salvo que un test demuestre que ya está desalineado

El helper hoy valida email, timeout/offline/429 y estados de error, pero no usa `gdprId`. El POST general conserva el payload `{ email, source, website }`.

### 2.2 HTML/builders auditados

Sin checkbox correspondiente en el HEAD de origen:

- `index.html` → HOME estática;
- `fragmento/index.html`;
- `las-manecillas-del-recuerdo/index.html`;
- `cuaderno/index.html`;
- `assets/v1-home-editorial-v3.js` → tarjeta dinámica HOME;
- `scripts/build-site-shell.py` → formulario global de Explorar.

`Explorar` es generado: no se debe arreglar editando a mano las múltiples copias HTML. El owner es el builder y la paridad se valida con `python scripts/build-site-shell.py --check`.

### 2.3 Referencia positiva existente

`lectores-beta/index.html` contiene `#lectores-beta-gdpr` como checkbox `required`, no premarcado y asociado a un `<label>`.

`script.js` resuelve ese elemento y bloquea el submit si no está marcado. El browser QA de privacidad intercepta el Worker y demuestra:

- email inválido → 0 POST;
- consentimiento sin marcar → 0 POST;
- consentimiento marcado + email válido → exactamente 1 POST;
- respuesta `pending_confirmation` → estado DOI, no suscripción confirmada localmente;
- no se añade un campo `consent` al payload actual del Worker.

Ese patrón demuestra comportamiento técnico existente, pero el copy beta es específico de una lista separada y NO debe copiarse literalmente a los formularios generales.

## 3. Ownership y arquitectura requerida

### 3.1 Un solo contrato funcional

La solución debe evitar dos implementaciones divergentes del newsletter general.

Preferencia arquitectónica:

- extraer/centralizar la lógica común de transporte + validación de newsletter en un owner reutilizable por `script.js` y `v1-shell.js`, o
- si se decide conservar dos puntos de entrada por compatibilidad, compartir al menos una función/contrato común y añadir una protección explícita contra doble binding.

No es aceptable copiar una segunda versión independiente de `postNewsletter()` en `v1-shell.js` sin QA de paridad.

### 3.2 `script.js`

`gdprId` deja de ser parámetro muerto. Debe:

- resolver el checkbox;
- fallar de forma accesible si el control falta en una superficie que declara `gdprId`;
- bloquear el POST si no está marcado;
- conservar la validación actual de email, timeout, offline, 429, errores recuperables, honeypot y estado DOI;
- no almacenar email ni consentimiento en `localStorage`/`sessionStorage`.

### 3.3 `assets/v1-shell.js` / Explorar

El formulario global de Explorar debe funcionar también en páginas V1 que cargan shell pero no `script.js`, incluida `privacidad.html`.

Requisitos:

- el diálogo continúa funcionando con teclado/Escape/focus trap;
- el submit de newsletter queda conectado al mismo contrato DOI;
- no se producen dos POST si una página carga ambos runtimes;
- no se introduce una dependencia que rompa páginas no-JS: sin JS el formulario puede quedar inactivo, pero su estructura/label/consentimiento debe seguir siendo legible y no inducir una falsa confirmación;
- CSP y scoping existentes se preservan.

### 3.4 Fuentes generadas

Modificar `scripts/build-site-shell.py` para que el HTML canónico de Explorar incluya el consentimiento general y regenerar mediante el mecanismo existente del repositorio.

No editar manualmente decenas de shells generados.

### 3.5 HOME dinámica

Modificar el owner `assets/v1-home-editorial-v3.js` para que la tarjeta dinámica cree también el control de consentimiento antes del botón/estado, con markup accesible equivalente al resto del sitio.

## 4. Copy general de consentimiento

Debe ser breve, claro y enlazar a `/privacidad.html`.

Restricciones:

- no usar wording específico de Lectores beta;
- no afirmar que el checkbox sustituye al doble opt-in;
- no premarcar;
- no esconder el enlace en texto secundario ilegible;
- no introducir una base jurídica nueva ni reinterpretar la política en esta PR.

Si durante implementación se concluye que el texto legal de `privacidad.html` debe cambiar, ese cambio debe describirse de forma explícita y factual en la PR. No convertir una corrección de wiring en asesoramiento jurídico.

## 5. Backend / Worker: límites de esta PR

El contrato actual del Worker general recibe `{ email, source, website }` y dispara DOI.

Por defecto, esta PR NO debe:

- añadir `consent` al payload;
- crear nuevas columnas/listas/atributos Brevo;
- guardar timestamps o pruebas de consentimiento;
- cambiar listas beta/general;
- cambiar `SOURCE_MAP` sin necesidad demostrada;
- alterar el endpoint de producción.

Consecuencia documentada: un checkbox validado solo en frontend prueba que la interfaz exigió asentimiento antes de enviar, pero no crea por sí mismo un registro persistente server-side de ese asentimiento. Si se necesita evidencia persistente, es una decisión separada de arquitectura/legal/backend y debe abrirse con su propio contrato.

## 6. QA obligatoria

### 6.1 Extender `tests/test-newsletter-client-contract.mjs`

El test actual protege endpoint, timeout, fuentes y no persistencia del email, pero no el consentimiento.

Añadir como mínimo aserciones que detecten regresión si:

- `gdprId` vuelve a quedar sin uso;
- el helper genérico no resuelve/valida checkbox;
- el flujo puede llegar a `postNewsletter()` con consentimiento sin marcar;
- se añade persistencia local de email/consentimiento sin contrato;
- desaparecen los IDs esperados del inventario de formularios.

Evitar regex frágil cuando sea viable; si se usa análisis estático, combinarlo con browser QA funcional.

### 6.2 Browser QA general

Añadir cobertura real con Worker interceptado para al menos:

- HOME estática;
- Fragmento;
- Manecillas;
- Cuaderno;
- tarjeta dinámica HOME;
- Explorar en una página que cargue `script.js` si existe;
- Explorar en `privacidad.html` o equivalente V1 que cargue `v1-shell.js` sin `script.js`.

Por cada arquetipo relevante:

1. checkbox presente, no premarcado y con label explícito;
2. email inválido → 0 POST;
3. email válido + checkbox sin marcar → 0 POST + mensaje accesible;
4. email válido + checkbox marcado → 1 POST;
5. doble submit durante request pendiente → 1 POST;
6. 201 `pending_confirmation` → copy de confirmación por email, no estado `subscribed` local;
7. 429 / 500 / timeout / offline → formulario recuperable y mensaje visible;
8. sentinel de email no aparece en URL, consola, storage ni requests ajenas al endpoint interceptado;
9. en páginas con ambos runtimes → 1 binding efectivo / 1 POST.

### 6.3 Legal browser QA

`qa/privacy-contract-browser.mjs` no debe seguir usando Lectores beta como sustituto de la prueba del formulario general cuando `privacidad.html` contiene `#newsletter-form-explore`.

Mantener el QA beta existente y añadir, separadamente, el contrato de Explore general en la propia página Legal.

### 6.4 Explore QA

`qa/explore-territories-browser.mjs` debe conservar sus pruebas de territorios/foco. Añadir una comprobación de que el bloque de suscripción del diálogo no rompe:

- focus trap;
- Escape;
- 320 px;
- 200% zoom/text sizing;
- ausencia de overflow;
- label/checkbox accesibles.

No mezclar esta prueba de UI con assertions de navegación irrelevantes.

### 6.5 Build/paridad

Obligatorio:

- `python scripts/build-site-shell.py --check`;
- QA de navegación/territorios existente;
- cualquier test que proteja generación determinista del shell.

## 7. CSS / accesibilidad

Usar el sistema visual existente; no crear un tercer estilo de consentimiento.

El control debe soportar:

- foco visible;
- click/tap sobre label;
- wrapping en 320 px;
- 200% zoom;
- text spacing;
- dark/system modes solo si ya forman parte del contrato de esa superficie;
- `prefers-reduced-motion` sin dependencia funcional de animaciones.

No reducir tipografía/contraste para “hacer caber” el texto.

## 8. Fuera de alcance

- rediseño de #287 Legal;
- rediseño de HOME/#163;
- cambios visuales subjetivos en cards/diálogo;
- nueva estrategia de email marketing;
- cambios en contenidos de campañas Brevo;
- consentimiento de cookies/analytics: el proyecto actual no tiene un consent manager y esta PR no debe inventarlo;
- resolver la revisión física Safari/iPhone pendiente de #163;
- merge automático de ninguna PR de la pila.

## 9. Criterios de cierre

Esta PR solo puede declararse resuelta cuando:

- todos los formularios generales auditados muestran y validan consentimiento explícito;
- `gdprId` no es parámetro muerto;
- Explore funciona en páginas shell-only;
- no existe doble binding;
- DOI y estados de error siguen intactos;
- Lectores beta permanece aislado en su lista/contrato;
- el Worker no cambia salvo justificación explícita y revisada;
- generación del shell queda en paridad;
- QA estática + browser reproduce el defecto previo y prueba la corrección;
- CI del HEAD exacto queda verde;
- la PR permanece Draft hasta revisión humana.

## 10. Relación con la pila de diseño

Esta PR es funcional y se apila después de #291. #287 no debe absorber esta corrección silenciosamente: su alcance sigue siendo visual/legal-documental y debe referenciar este owner funcional.

Tras implementar y validar esta PR, #291 podrá sustituir el finding abierto de newsletter por una referencia concreta al HEAD certificado de este owner, sin afirmar más de lo que prueben sus tests.