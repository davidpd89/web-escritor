# Implementation Truth Ledger — WEB DAVID PORTO

**Corte:** 27/08/2026  
**Autoridad machine-readable:** `data/implementation-truth-ledger.json`  
**Objetivo:** impedir que documentación, código parcial, configuración externa y comportamiento real vuelvan a mezclarse bajo la palabra «hecho».

## 1. El problema que resuelve

El proyecto ha crecido mediante muchas PR especializadas y varios sistemas externos. Eso ha producido una clase de error más peligrosa que un TODO visible: **la finalización aparente**.

Ejemplos ya observados:

- una lista Brevo fue creada, pero el Worker/binding/journey beta no quedó probado;
- Search Console recibió un plan maestro completo, pero eso no creó la propiedad, BigQuery ni auth API;
- una estrategia de IA puede estar mergeada sin que una integración externa esté activa;
- un smoke de producción puede dar verde contra una release antigua si no comprueba identidad exacta;
- un bump manual de cache puede resolver un teléfono y dejar intacta la causa estructural;
- una PR de diseño puede enumerar ficheros que en realidad no existen en su propia rama;
- una rama con 5.000+ líneas de investigación puede existir sin PR y quedar fuera del flujo normal;
- CI puede tener 30 workflows y aun así un push directo a `main` evitar muchos de ellos;
- `npm audit` puede decir «10 high» sin que eso explique qué es alcanzable, pero ignorar el contador tampoco es una respuesta.

La corrección es tratar el estado como datos y exigir vocabulario preciso.

## 2. Estados permitidos

### `DOCUMENTED`

Existe investigación, arquitectura, runbook o backlog. No existe todavía evidencia suficiente de implementación.

### `IMPLEMENTED_IN_PR`

Existe código/documentación ejecutable en una PR abierta. Aún no está en `main`.

### `MERGED_MAIN`

La pieza está en `main`. Esto solo habla del repositorio.

No implica automáticamente:

- cuenta configurada;
- secret/binding creado;
- servicio desplegado;
- contacto/email recibido;
- Google procesando datos;
- producción sirviendo el SHA esperado.

### `CONFIGURED_LIVE`

Existe configuración real en el proveedor externo correspondiente.

Ejemplo válido: una lista Brevo real con ID conocido.

Ejemplo inválido: un `wrangler.example.jsonc` que describe cómo crearla.

### `VERIFIED_E2E`

Se ha probado el resultado final relevante.

Ejemplos:

```text
submit beta
→ DOI/alta
→ contacto en lista correcta
→ no fuga a lista general
```

```text
merge SHA X
→ artifact X
→ deploy
→ davidportodiaz.com/_release/X.json
→ contenido exacto X
```

### `BLOCKED`

Existe una dependencia que impide afirmar progreso honesto: acceso, autorización, proveedor, fecha futura o evidencia externa.

### `NOT_APPLICABLE`

Se revisó y decidió expresamente no aplicar.

## 3. Regla para Claude

Antes de escribir «hecho», «implementado», «listo», «configurado», «funciona» o equivalente, Claude debe responder mentalmente:

```text
¿En qué capa tengo evidencia?
```

Si solo ha editado Markdown:

```text
DOCUMENTED
```

Si ha creado código en una PR abierta:

```text
IMPLEMENTED_IN_PR
```

Si lo ve en `main`:

```text
MERGED_MAIN
```

Si consulta la cuenta real y existe:

```text
CONFIGURED_LIVE
```

Si ejecuta el journey y observa el resultado final:

```text
VERIFIED_E2E
```

No se permite saltar niveles por inferencia.

## 4. Estado actual resumido

| Iniciativa | Estado auditado | Dueño | Principal gap |
|---|---|---|---|
| Public artifact allowlist-first | `MERGED_MAIN` | #106/main | identidad exacta pertenece a #116 |
| Release integrity | `IMPLEMENTED_IN_PR` | #116 | reflow basal + ruleset live |
| Ruleset main | `DOCUMENTED` | #116 | no activo todavía |
| PWA freshness | `IMPLEMENTED_IN_PR` | #117 | revisar Global Discoverability + base reflow |
| Reflow compartido | `IMPLEMENTED_IN_PR` | #119 | validar corrección V7 |
| Design/UX tooling | `IMPLEMENTED_IN_PR` | #114 | faltan 14/15/catalog + governance |
| Repo hygiene | `IMPLEMENTED_IN_PR` | #115 | base reflow y segunda ronda |
| Claude Toolbox | `IMPLEMENTED_IN_PR` | #120 | validar catálogo/prerequisites |
| Brevo snapshot counts | `IMPLEMENTED_IN_PR` | #118 | regenerar contra API live después |
| Brevo lista beta | `CONFIGURED_LIVE` | Brevo | objeto existe; journey no |
| Brevo beta routing | `BLOCKED` | #118/Cloudflare | binding + deploy + smoke |
| Promesa capítulo Samuel | `BLOCKED` | #118/Brevo | E2E o retirar promesa |
| Search Console plan | `MERGED_MAIN` | #110 | plan ≠ cuenta/API/BQ |
| Search Console Domain property | `DOCUMENTED` | #110 | inspección/config cuenta real |
| Search Console BigQuery | `DOCUMENTED` | #110 | GCP/billing/roles/export |
| Search Console API | `DOCUMENTED` | #110 | scripts/auth real |
| AI visibility plan | `MERGED_MAIN` | #113 | separar activaciones externas |
| Manecillas launch transition | `MERGED_MAIN` | script | ejecutar 03/09; comercio separado |
| Node dependency risk | `DOCUMENTED` | nueva PR pendiente | advisory-by-advisory |

La tabla es solo una vista humana. El JSON contiene `falseCompletionTrap`, `nextAction`, evidencia y criterio de cierre para cada item.

## 5. Cómo se actualiza

La PR propietaria de una iniciativa debe actualizar la entrada cuando cambie materialmente de estado.

Ejemplos:

### Al mergear #117

```text
IMPLEMENTED_IN_PR
→ MERGED_MAIN
```

No pasar a `VERIFIED_E2E` solo porque mergeó.

### Al crear el binding beta

No cambiar el estado del objeto «lista beta» —ya existe—. Cambiar el item específico de routing:

```text
BLOCKED
→ CONFIGURED_LIVE
```

Después del smoke de aislamiento:

```text
CONFIGURED_LIVE
→ VERIFIED_E2E
```

### Al mergear documentación Search Console

El plan permanece `MERGED_MAIN`. Los items de propiedad/BigQuery/API continúan `DOCUMENTED` hasta ejecución real.

## 6. Qué NO debe hacer el ledger

No convertirse en:

- otro roadmap genérico;
- una copia de todos los TODO del repo;
- un sustituto de las PR propietarias;
- una excusa para no leer CI;
- una fuente de métricas externas inventadas;
- un log de cada commit menor.

Solo entran iniciativas en las que confundir estado puede producir una decisión incorrecta de producto, release, seguridad, SEO, CRM o infraestructura.

## 7. Criterio de evidencia

### Evidencia repo

Válida:

- fichero concreto;
- test;
- workflow;
- PR;
- commit;
- generated artifact contract.

### Evidencia externa

Válida:

- respuesta/estado leído de la cuenta real;
- objeto real identificado;
- workflow live observado;
- email/journey controlado;
- respuesta HTTP de producción;
- API/export real.

No válida:

- «debería»;
- «el código está preparado»;
- «la documentación dice que»;
- «la fecha ya llegó»;
- «el proveedor normalmente hace esto».

## 8. Relación con #116

El ledger y Production Integrity resuelven problemas distintos:

```text
#116
¿puede entrar un cambio sin pasar la puerta correcta?
```

```text
Truth Ledger
¿estamos describiendo correctamente hasta dónde llegó cada capability?
```

Ambos se necesitan.

El caso del reflow demuestra por qué: el gate detectó un fallo real basal en varias PR. El ledger evita que esas PR se declaren listas ignorando ese contexto.

## 9. Relación con documentación futura

Toda macro-PR nueva debería incluir en su cuerpo:

```text
Truth stage al abrir:
Truth stage al cerrar:
External config required: yes/no
E2E required: yes/no
Evidence:
```

Esto no necesita una plantilla burocrática enorme. Cinco líneas bastan para evitar ambigüedad.

## 10. Definition of Done de este sistema

- JSON válido y testeado;
- IDs únicos;
- stages válidos;
- `VERIFIED_E2E` imposible sin evidencia externa explícita;
- items incompletos deben tener `nextAction` y `closureCriterion`;
- evidencia de repo relativa, cuando es path, debe existir;
- el ledger queda privado: `data/` no entra en public artifact;
- la versión humana explica semántica y no contradice el JSON;
- Claude usa este ledger como índice de estado antes de retomar una iniciativa abierta.
