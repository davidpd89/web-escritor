# E.8 · Auditoría de terceros

**Estado histórico final de PR #135:** `IMPLEMENT_NOW`  
**Estado de la capacidad dentro de la antigua rama #135:** `IMPLEMENTED_IN_PR`  
**Estado observado en `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`:** el registro/contrato entregado por #135 no está presente  
**Naturaleza de esta PR:** documentación y reconstrucción histórica; no carga, elimina ni configura terceros.

## 1. Qué se está recuperando

La hipótesis original de E.8 era auditar los scripts de terceros —en especial GoatCounter, Metricool y Brevo— para conocer su impacto real y cargar de forma `defer`/`async` o diferida aquello que pudiera retrasarse sin romper funcionalidad.

La investigación de #135 transformó esa idea genérica en algo más mantenible: un **inventario versionado de integraciones de terceros con contrato de regresión**, no una campaña indiscriminada de `async`/lazy-loading.

Hay una distinción decisiva que esta reconstrucción debe conservar:

- #135 **sí llegó a implementar** `data/third-party-integrations.json`, documentación asociada y un test en su propia rama;
- #135 fue cerrada y **nunca se fusionó**;
- por tanto, ese entregable histórico no equivale a `MERGED_MAIN` y no aparece hoy en `main`;
- una futura implementación no debe fingir que la capacidad está ya desplegada, pero tampoco debe rediseñarla desde cero ignorando el contrato que #135 dejó definido.

## 2. Hipótesis original

Fuente: `docs/IDEAS-MEJORA-WEB-2026-08-27.md` en el snapshot histórico `8e72321d047c0445c5ac411ebe242af8a0386929`.

> Confirmar el impacto real de GoatCounter/Metricool/Brevo en el hilo principal y cargarlos `defer`/`async` o tras interacción cuando sea posible.

La frase era una hipótesis, no una autorización para retrasar scripts a ciegas. La revisión posterior añadió necesidad, privacidad, CSP, ownership, duplicados y coste de red/CPU.

## 3. Evolución completa de la decisión

| Etapa | Estado / hallazgo | Qué añadió |
|---|---|---|
| Banco original | hipótesis abierta | Auditar GoatCounter/Metricool/Brevo y diferir carga cuando sea seguro. |
| Revisión 108/108 | `IMPLEMENT_NOW` | El bug previo de GoatCounter demostró valor. Se propone registro con dominio, loader, `async/defer`, privacidad, CSP y owner, más checker de duplicados y URLs protocol-relative. |
| Matriz operativa | `IMPLEMENTAR` | Amplía inventario a GoatCounter/Metricool/Brevo/Turnstile y exige bytes, CPU, network, necesidad y política de carga. No sumar Ahrefs Analytics/Clarity sin experimento. |
| Blueprints | trabajo neto ligado también a I.2/I.5 | E.8 debe compartir la autoridad `data/third-party-integrations.json`; no crear un segundo registro de privacidad/performance. |
| Implementación dentro de #135 | `IMPLEMENTED_IN_PR` | #135 añadió el registro, documentación y test de regresión. |
| Autoridad humana final | `IMPLEMENT_NOW` | Declara explícitamente que #135 ya entrega inventario + contrato; el trabajo posterior sería mantener bytes/CPU/network/necesidad. |
| JSON final | `IMPLEMENT_NOW` + `deliveredInPr135` | Machine-readable: el baseline registry + regression contract estaban implementados **en esa PR**. |
| Revalidación independiente | mantenido | No encuentra razón para cambiar E.8; solo E.7 cambia en el bloque E. |
| Revalidación actual de esta PR | capacidad histórica ausente de `main` | Como #135 no se mergeó, el entregable debe considerarse recuperable, no presente en producción/main. |

## 4. Contrato que #135 dejó diseñado

El registro de terceros debía ser una **fuente de verdad pequeña y comprobable**, no un catálogo decorativo. Para cada integración, como mínimo debía poder responder:

- qué proveedor/host interviene;
- cuál es su propósito;
- en qué superficies se carga;
- qué loader o código lo activa;
- si el recurso es síncrono, `async`, `defer`, dinámico o condicionado a una acción;
- qué hosts deben estar autorizados por CSP;
- si se han observado cookies o almacenamiento local;
- qué red/endpoints utiliza;
- qué owner mantiene la integración;
- qué fuente de privacidad/documentación la respalda;
- cuándo se verificó por última vez;
- y, para performance, qué bytes/requests/CPU añade en los journeys donde realmente se usa.

El blueprint posterior vinculó E.8 con I.2/I.5: **un único inventario puede servir a rendimiento y privacidad**, siempre que cada campo tenga semántica clara. E.8 es propietaria del coste/carga/necesidad; I.2/I.5 de la justificación de datos, retención y minimización.

## 5. Evidencia del repositorio y del historial

### Evidencia histórica

La propia PR #135 registró entre sus entregables reales:

- `data/third-party-integrations.json`;
- `docs/THIRD-PARTY-INTEGRATIONS.md`;
- test del contrato del registro.

`data/web-improvement-decisions-2026-08-28.json` contiene además una entrada `deliveredInPr135.E.8` que dice que el baseline y la regresión estaban implementados en esa PR.

### Evidencia del `main` actual

La reconstrucción se basa en `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`. La búsqueda actual no localiza `third-party-integrations` en el repositorio. Esto es coherente con la historia: #135 no fue mergeada.

El HTML público sí demuestra que siguen existiendo terceros que justifican el inventario. Por ejemplo, el CSP actual de `/asistente/` referencia dominios de GoatCounter, Metricool, Cloudflare Turnstile y el Worker de Brevo. Eso prueba **existencia/configuración en código**, no por sí solo coste, cookies, retención o comportamiento E2E.

## 6. Veredicto reconciliado

La decisión histórica `IMPLEMENT_NOW` se mantiene, pero debe expresarse con la taxonomía correcta:

1. **En la antigua #135:** el baseline llegó a `IMPLEMENTED_IN_PR`.
2. **Nunca alcanzó `MERGED_MAIN`:** cerrar/resetear la PR no conserva el artefacto en la rama principal.
3. **En el `main` actual:** la capacidad de registro no está localizada y no debe afirmarse como implementada.
4. **Esta PR individual:** solo recupera el contrato y la decisión; no recrea todavía runtime/data/tests para no convertir una PR arqueológica en una implementación silenciosa.

Si más adelante se desarrolla E.8, debe **recrear/recuperar el registro histórico como autoridad única**, actualizado contra los terceros que realmente existan entonces, y no diseñar otro sistema paralelo.

## 7. Plan de implementación derivado de #135

Una PR de desarrollo posterior debería, como mínimo:

1. recuperar `data/third-party-integrations.json` con schema explícito;
2. inventariar GoatCounter, Metricool, Brevo/Worker, Turnstile y cualquier tercero vigente;
3. mapear cada entrada a los ficheros/loaders reales;
4. registrar CSP/network hosts sin copiar secretos;
5. medir bytes/requests y, cuando sea material, CPU/long tasks en journeys representativos;
6. clasificar si la integración es global, condicional o activada tras interacción;
7. comprobar duplicados, hosts protocol-relative/no HTTPS y referencias no inventariadas;
8. añadir test de regresión que falle cuando el código introduce un tercero nuevo sin declararlo;
9. cambiar estrategia de carga **solo** si la medición y semántica del script demuestran que es seguro y útil;
10. mantener una única autoridad compartida con I.2/I.5.

## 8. Qué no autoriza E.8

- No convertir todos los terceros a `async` o “tras interacción” sin entender dependencias.
- No eliminar GoatCounter/Metricool/Brevo solo por ser terceros.
- No instalar Clarity, Ahrefs Analytics u otro tracker para “completar” el inventario.
- No duplicar el inventario con un fichero separado para privacidad.
- No introducir un tag manager nuevo.
- No afirmar `cookiesObserved=false` o “cookieless” sin observación/documentación suficiente.
- No afirmar `CONFIGURED_LIVE` por encontrar un dominio en HTML/CSP.
- No tratar bytes de terceros como único criterio: necesidad, privacidad, resiliencia y accesibilidad también importan.

## 9. Tests y Definition of Done de una futura implementación

- [ ] existe una sola autoridad versionada para terceros;
- [ ] cada host externo cargado por las superficies auditadas está inventariado o explícitamente excluido con motivo;
- [ ] no hay duplicados ni URLs protocol-relative inesperadas;
- [ ] el checker detecta una integración nueva no declarada;
- [ ] CSP y registro permanecen en paridad;
- [ ] loaders/estrategia `async/defer/dynamic` reflejan el código real;
- [ ] existe baseline de bytes/requests para terceros importantes;
- [ ] cualquier cambio de carga tiene before/after y no rompe analytics, formularios, Turnstile ni feedback;
- [ ] privacidad/retención se enlaza con I.2/I.5 en vez de duplicarse;
- [ ] ningún estado externo se eleva a `CONFIGURED_LIVE`/`VERIFIED_E2E` sin evidencia externa.

## 10. Relación con otras ideas

- **I.2:** cookies/storage/network/purpose y consentimiento de GoatCounter/Metricool/Brevo/Turnstile.
- **I.5:** revisión periódica de minimización/retención/eliminación.
- **E.2/E.5:** si un tercero aparece como contributor real de INP o rompe un budget, se actúa desde evidencia.
- **M.1:** CSP/headers delimitan hosts permitidos, pero no sustituyen el inventario.
- **Q.3:** cualquier experimento de añadir/quitar/cambiar una integración debe registrar hipótesis y resultado.

## 11. Trazabilidad del corpus histórico de #135

Revisados como fuentes relevantes o controles de consistencia:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `IMPLEMENT_NOW`, forma inicial del registro/checker.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — fuentes base de rendimiento/privacidad.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — contraste con integraciones existentes.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` — correcciones de criterio posteriores.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` — regla general de no duplicar autoridades.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — inventario ampliado a Turnstile y coste/necesidad.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — autoridad compartida con I.2/I.5.
- `data/web-improvement-decisions-2026-08-28.json` — `IMPLEMENT_NOW` + `deliveredInPr135`.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana final.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — decisión mantenida.
- pasadas posteriores de investigación — revisadas para detectar cambios de status o nuevas obligaciones; no sustituyen la autoridad final cuando solo amplían herramientas adyacentes.

## 12. Cierre

E.8 no es “poner `async` a tres scripts”. Es mantener un contrato explícito sobre **qué terceros existen, por qué existen, cuánto cuestan y cómo se cargan**. #135 llegó a construir ese contrato, pero no lo llevó a `main`. La reconstrucción correcta conserva tanto el trabajo histórico como esa ausencia actual, sin confundir `IMPLEMENTED_IN_PR` con `MERGED_MAIN`.