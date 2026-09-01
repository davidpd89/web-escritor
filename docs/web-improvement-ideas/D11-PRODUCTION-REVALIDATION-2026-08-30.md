# D.11 · Revalidación de producción — estados vacíos / no-results / unavailable

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **PARTIAL_AUDIT · KEY_RECOVERY_STATES_ALREADY_STRONG · INVENTORY_NOT_PROVEN_COMPLETE · NO_GLOBAL_COMPONENT · NO_CODE**.

## 1. Resultado

La reconstrucción histórica clasificaba D.11 como trabajo neto transversal. La inspección de producción muestra que varios de los journeys más importantes ya tienen estados explícitos, accionables y accesibles.

No hay evidencia suficiente para declarar la auditoría sitewide cerrada, pero tampoco para crear un componente universal o reescribir los estados actuales.

D.11 pasa a ser una **auditoría residual por evidencia**, no una feature pendiente genérica.

## 2. Asistente / búsqueda

`assets/assistant.js` cubre directamente varios estados críticos.

### No results

Si Pagefind y el ranking local no encuentran coincidencias claras, el usuario recibe:

> «No encuentro una coincidencia clara en el contenido de la web. Puedes orientarte desde estas rutas o abrir el mapa del sitio.»

Además se adjuntan hasta tres rutas estables del registry.

No es una pantalla muerta ni un CTA comercial.

### Fallo de capa remota

Si Turnstile no está disponible, no se puede obtener sesión, la configuración remota está desactivada o la respuesta remota falla/queda inválida, el flujo cae a la búsqueda local.

En `429` diferencia explícitamente el límite de respuestas ampliadas y sigue ofreciendo páginas.

### Timeout

Ante aborto por timeout comunica:

> «He tardado demasiado en responder. Prueba de nuevo o abre una de estas páginas relacionadas.»

### Input inválido

- pregunta demasiado larga → explica el máximo y devuelve foco al input;
- pregunta demasiado corta → pide una consulta más concreta y devuelve foco.

Eso ya cumple buena parte del contrato D.11 en una superficie compleja.

## 3. Agenda sin próximos eventos

`eventos.html` contiene un estado vacío explícito cuando no existe una próxima fecha confirmada:

> «Ahora mismo no hay una próxima fecha publicada.»

Explica que la agenda solo se actualiza cuando existe una firma/presentación/encuentro confirmado y ofrece dos siguientes acciones reales:

- solicitar presentación;
- ver el archivo reciente.

No inventa un evento ni convierte la ausencia en falsa urgencia.

## 4. Newsletter y estados de red

El runtime global ya distingue, entre otros:

- email inválido;
- staging deshabilitado;
- offline;
- timeout;
- rate limit;
- fallo de red/servidor;
- confirmación DOI pendiente.

D.1 ya revalidó este microfeedback. D.11 no debe duplicarlo con otro sistema de mensajes.

## 5. Contenido retirado

`/cuaderno/sistema-de-magia-noveris/` es otro ejemplo de `unavailable` explícito:

- indica que el contenido está temporalmente retirado;
- explica por qué la URL continúa existiendo;
- informa de `noindex`/fuera de sitemap;
- dirige a ficha y fragmento oficiales de Samuel.

La retirada no se disfraza como error genérico ni deja al visitante sin salida.

## 6. Qué sigue sin estar demostrado

Esta revalidación no ha navegado exhaustivamente cada combinación de estado de todas las herramientas, filtros, recursos y futuras funciones.

Por tanto no se afirma:

```text
ALL_EMPTY_STATES_VERIFIED
```

ni se crea una tabla paralela que pretenda ser la autoridad de todos los componentes.

El trabajo restante es detectar **casos concretos** donde se incumpla el patrón ya visible en las superficies maduras.

## 7. Nuevo criterio operativo

Antes de abrir código por D.11 debe existir un caso reproducible con al menos uno de estos defectos:

- no explica qué ocurrió;
- confunde vacío legítimo con error;
- deja bloqueada la acción principal;
- no ofrece recuperación aunque existe una evidente;
- mueve/retiene foco de forma incorrecta;
- no comunica estado dinámico importante;
- introduce dark pattern;
- contradice la autoridad factual de la función.

Entonces se corrige **en el owner del componente**, no en una librería genérica de EmptyState.

## 8. Qué no hacer

- no crear `EmptyState` global por abstracción prematura;
- no añadir newsletter a todos los vacíos;
- no inventar actividad futura;
- no añadir `aria-live` a todo;
- no convertir mensajes textuales correctos en cards ornamentales;
- no duplicar mensajes del asistente/newsletter;
- no instrumentar analytics de cada vacío sin pregunta de producto.

## 9. Estado final de la idea

```text
critical journeys inspected = GOOD/PARTIALLY_COVERED
sitewide inventory = NOT_PROVEN_COMPLETE
new generic runtime = NOT_JUSTIFIED
future changes = CASE_BY_CASE
```

Esto es más preciso que mantener `IMPLEMENT_AFTER_CURRENT_DEBT` como si no existiera trabajo de producción previo.

## 10. Definition of Done

- [x] asistente/no-results inspeccionado directamente;
- [x] fallos remotos/fallback/timeout inspeccionados;
- [x] estado de agenda vacía inspeccionado;
- [x] newsletter reconciliada con D.1;
- [x] contenido retirado reconocido como unavailable state válido;
- [x] ausencia de auditoría exhaustiva declarada;
- [x] criterio de reapertura por defecto reproducible definido;
- [x] sin componente global ni código nuevo.

## Estado para Claude

No tratar D.11 como una campaña pendiente de microcopy. Las superficies críticas comprobadas ya tienen recuperación fuerte. Mantener una auditoría residual y corregir únicamente estados concretos defectuosos dentro de su owner.