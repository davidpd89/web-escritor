# I.2 · Inventario de analítica, terceros y consentimiento

**Estado histórico final de PR #135:** `IMPLEMENT_NOW`  
**Matriz:** `IMPLEMENTAR`  
**Entrega histórica:** #135 llegó a crear el baseline junto a E.8, pero PR #135 nunca se fusionó.  
**Estado efectivo en `main` al 29/08/2026:** la capacidad versionada `data/third-party-integrations.json` no está presente; no confundir `IMPLEMENTED_IN_PR` con `MERGED_MAIN`.  
**Naturaleza de esta PR:** documentación; no realiza asesoramiento jurídico ni cambia trackers/runtime.

## 1. Hipótesis original

I.2 proponía confirmar que Metricool y GoatCounter no estaban provocando consentimiento/cookies innecesarios y auditar el tratamiento real de los terceros ya integrados.

La investigación amplió correctamente el alcance: no basta preguntar “¿usa cookies?”. Cada integración debe registrar propósito, red, storage observado, carga, privacidad, retención/owner y consecuencia de consentimiento. Brevo y Turnstile también forman parte del mapa cuando se activan en sus respectivos flujos.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Evitar consentimiento innecesario/duplicado. |
| Revisión 108/108 | `IMPLEMENT_NOW` | GoatCounter no prueba el comportamiento de Metricool; audit vendor-by-vendor. |
| Matriz | `IMPLEMENTAR` | Inventario real de GoatCounter/Metricool/Brevo/Turnstile. |
| Blueprints W8 | implementación compartida con E.8/I.5 | Extender un único `data/third-party-integrations.json`. |
| Trabajo dentro de #135 | `IMPLEMENTED_IN_PR` | Baseline + contrato de regresión se llegaron a crear en esa rama. |
| Autoridad final/JSON | `IMPLEMENT_NOW` | Mantener inventario; no sumar analytics redundante. |
| Revalidación independiente | mantenido | Clarity behavioral tracking no se instala por defecto; AI Citations podía verificarse sin tracker mediante GSC/BWT. |
| Estado actual | no mergeado | #135 cerró sin merge; el registro no está en `main`. |

## 3. Regla arquitectónica: I.2 y E.8 son una sola autoridad técnica

No deben existir:

- `third-party-integrations.json` para rendimiento;
- otro `privacy-vendors.json` para privacidad;
- otra hoja manual para consentimiento.

El mismo registro debe contener las dimensiones necesarias para E.8 e I.2, con vistas/checkers distintos si hace falta.

Campos mínimos por integración:

```json
{
  "id": "goatcounter",
  "purpose": "analytics",
  "loadedOn": ["public-site"],
  "loader": "async|defer|dynamic|server-side",
  "networkHosts": [],
  "cookiesObserved": false,
  "localStorageObserved": false,
  "sessionStorageObserved": false,
  "privacySource": "https://...",
  "retention": "verify/document",
  "owner": "site",
  "lastVerified": "YYYY-MM-DD",
  "consentDecision": "documented decision, not legal conclusion"
}
```

Los valores reales deben salir de inspección/runtime/fuentes actuales; el ejemplo no autoriza copiar valores sin probarlos.

## 4. Revalidación de `main` · runtime actual

### GoatCounter

`script.js`:

- evita doble carga si ya existe `script[data-goatcounter]`;
- crea `https://gc.zgo.at/count.js` dinámicamente;
- marca `async=true`;
- usa `davidportodiaz.goatcounter.com/count`;
- puentea algunos `dp:analytics` a eventos agregados.

La política vigente lo describe como analítica sin cookies/identificadores personales. Esa afirmación debe seguir verificándose periódicamente contra runtime y fuente del proveedor, no darse por eterna.

### Metricool

`script.js` carga `https://tracker.metricool.com/resources/be.js` y ejecuta `beTracker.t(...)`.

La política vigente afirma que la versión inspeccionada no usa `document.cookie`, `localStorage`, `sessionStorage` ni IndexedDB y que envía una petición con datos agregados de página. I.2 debe convertir esa afirmación en evidencia versionada con `lastVerified`, no dejarla solo como prosa legal.

### Brevo / Worker propio

El navegador envía a `https://subscribe.davidpd89.workers.dev` un contrato mínimo: email + `source` + campos acotados. El Worker valida el `source`, compone atributos/list IDs server-side y llama al endpoint DOI de Brevo.

Esto procesa datos personales cuando el usuario se suscribe; no debe mezclarse conceptualmente con analytics cookieless.

### Turnstile / Workers AI

La CSP permite `challenges.cloudflare.com`; la política explica que Turnstile/Workers AI/AI Search corresponden al modo remoto opcional del asistente, actualmente desactivado en producción según `assets/assistant-config.js` (`remote: false`).

Una integración permitida por CSP no equivale a una integración activa en cada visita.

### Clarity

El propio `script.js` indica Clarity intencionadamente desactivado. No añadirlo para completar el inventario ni para AI Citations: la revalidación de #135 encontró una vía de verificación mediante GSC/BWT sin behavioral tracking.

## 5. Incongruencia actual detectada en este lote

`privacidad.html` afirma sobre la suscripción general:

- que el formulario exige aceptar la política antes de enviarlo;
- y que esa aceptación no se almacena como campo separado.

Sin embargo, en el runtime actual:

- `submitNewsletter(formId, emailId, gdprId, ...)` recibe `gdprId` pero no lo usa;
- la Home inspeccionada no contiene `nl-gdpr-home`;
- el flujo beta sí comprueba explícitamente su checkbox propio.

Esto es **evidencia de drift entre política y runtime** que debe resolverse en una PR de implementación/legal técnica separada antes de afirmar paridad. I.2 debe registrarlo como gap, no emitir una conclusión jurídica improvisada.

## 6. Qué debe medir el futuro auditor

Por vendor/ruta representativa:

- requests y hosts;
- momento de carga;
- bytes/CPU si aplica (E.8);
- cookies before/after;
- localStorage/sessionStorage/IndexedDB;
- query/body de red solo hasta el nivel seguro necesario, sin volcar PII;
- propósito declarado;
- fuente oficial de privacidad;
- retención declarada/observable;
- datos que entran/salen;
- si existe opt-in explícito o el flujo se activa por acción;
- CSP necesaria;
- propietario interno y fecha de última revisión.

No registrar emails reales, tokens, API keys ni cuerpos sensibles en artifacts de CI.

## 7. Separar hechos técnicos de decisión legal

El inventario puede afirmar:

- “no observamos cookies en este test”;
- “el script hace requests a X”;
- “el proveedor declara Y”;
- “la función solo se activa tras submit”.

No debe convertir automáticamente esos hechos en:

- “no requiere consentimiento en toda jurisdicción”;
- “cumple RGPD”;
- “es anónimo” si el proveedor no lo sustenta;
- “nunca cambia”.

Cuando haga falta una conclusión legal, se valida aparte.

## 8. Contrato de regresión propuesto

El checker compartido E.8/I.2 debería fallar o alertar cuando:

- aparece un host tercero no registrado;
- se duplica un vendor/loader;
- entra una URL protocol-relative/insegura;
- cambia CSP sin actualizar inventario;
- aparece storage/cookie donde el contrato decía que no;
- se incorpora tracking/recording sin decisión previa;
- falta `lastVerified`/source en integraciones críticas.

Los cambios de comportamiento que solo pueden observarse live deben producir `PARTIAL_AUDIT/NEEDS_LIVE_VERIFY`, no una falsa certeza en CI estático.

## 9. Definition of Done de implementación

- [ ] un único registro compartido con E.8;
- [ ] GoatCounter, Metricool, Brevo/Worker y Turnstile/AI modelados según uso real;
- [ ] Clarity marcado ausente/desactivado, no añadido;
- [ ] tests de hosts/duplicados/CSP;
- [ ] auditor browser seguro de storage/network en rutas representativas;
- [ ] `lastVerified` y fuentes oficiales;
- [ ] drift privacidad↔runtime de newsletter corregido o explícitamente bloqueante;
- [ ] política actualizada solo tras comprobar hechos;
- [ ] ninguna PII/secreto en artifacts;
- [ ] revisión periódica enlazada con I.5;
- [ ] estado `VERIFIED_E2E` solo tras inspección live cuando corresponda.

## 10. Qué no hacer

- No instalar CMP/cookie banner por checklist sin determinar tratamiento real.
- No quitar consentimiento por asumir que “cookieless = siempre exento”.
- No instalar Clarity/Ahrefs Analytics u otro tracker para obtener más datos sin hipótesis.
- No crear un segundo inventario paralelo al de E.8.
- No copiar el baseline de #135 y marcarlo como mergeado.
- No guardar PII de requests en reportes.
- No arreglar texto legal sin verificar comportamiento runtime.

## 11. Relación con otras ideas

- **E.8:** misma autoridad técnica, dimensión performance/network/third-party.
- **I.5:** revisión periódica de minimización/retención/deletion.
- **H.1/H.2:** consentimiento y journeys Brevo deben ser factualmente coherentes.
- **G.5:** cualquier nueva analítica del asistente ampliaría este inventario y requeriría un trigger específico.
- **M.1:** CSP/headers ayudan a comprobar qué terceros están autorizados, no cuáles efectivamente cargan.

## 12. Trazabilidad #135

Revisados:

- banco original I.2;
- revisión 108/108 (`IMPLEMENT_NOW`);
- matriz (`IMPLEMENTAR`);
- blueprints W8;
- implementación histórica del registry/checker dentro de #135;
- `data/web-improvement-decisions...`;
- autoridad final;
- revalidación independiente y decisión Clarity;
- E.8 y autoridades Brevo/privacidad relacionadas.

La falta de merge de #135 cambia el estado de entrega efectivo, no la validez del diseño investigado.

## 13. Cierre

I.2 es una de las pocas ideas del lote que sí representa trabajo técnico neto. Pero el trabajo correcto no es “poner o quitar un banner”: es mantener una **fuente versionada y comprobable de qué terceros existen, qué hacen realmente y cuándo se verificó**, compartida con E.8 y reconciliada con la política pública.