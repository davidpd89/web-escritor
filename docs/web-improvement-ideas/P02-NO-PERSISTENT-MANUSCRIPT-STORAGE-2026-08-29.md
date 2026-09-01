# P.2 · Guardado local del progreso — reconstrucción completa desde PR #135

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: snapshot `8e72321d047c0445c5ac411ebe242af8a0386929` de PR #135.  
Estado final histórico: `REJECT`.

## 1. Hipótesis original

P.2 proponía guardar mediante `localStorage` el progreso de las herramientas para que una persona pudiera cerrar la pestaña y continuar más tarde, manteniendo el enfoque sin cuenta/backend.

La idea era atractiva por coste técnico, pero partía de una simplificación importante: «local» no significa «sin riesgo». Persistir un manuscrito o texto inédito en el navegador cambia el threat model y contradice una de las garantías diferenciales del ecosistema privado de herramientas.

## 2. Evolución dentro de #135

### Revisión exhaustiva 27/08

Decisión: `REJECT`.

Motivo explícito:

- no persistir manuscritos por defecto en `localStorage`;
- deja texto sensible persistente en el dispositivo;
- contradice la postura privacy-first;
- solo settings no sensibles u opt-in muy concreto podrían reconsiderarse.

### Matriz final intermedia 28/08

La matriz llegó a `PILOTAR SELECTIVO` y describió un posible alcance con:

- clear/reset;
- aviso de almacenamiento local;
- no persistir datos sensibles por defecto.

Esa formulación **no es la autoridad final**. Es útil como registro de la alternativa considerada, pero fue supersedida por una decisión más estricta.

### Autoridad final humana + machine-readable

Estado final: `REJECT`.

Regla:

> No persistir manuscritos/textos largos en `localStorage` por defecto. Reabrir solo para una herramienta no sensible, opt-in, con clear/reset y threat model.

## 3. Revalidación independiente

La revalidación independiente mantiene el rechazo y lo cita como ejemplo de trabajo eliminado correctamente por la criba: no introducir `localStorage` indiscriminado para herramientas privadas.

No aparece una pasada posterior con evidencia que justifique revertirlo.

## 4. Evidencia actual de `main`

`data/private-tools-privacy-manifest.json` establece un contrato inequívoco para herramientas que aceptan texto inédito/manuscritos:

- `analysisRunsInBrowser: true`;
- `manuscriptSentToServer: false`;
- `thirdPartyScripts: false`;
- `programmaticNetworkConnections: false`;
- **`persistentManuscriptStorage: false`**;
- `serviceWorkerOnToolPage: false`;
- `cloudAI: false`.

La decisión P.2 está por tanto alineada con una autoridad técnica viva del repositorio. Implementar autosave persistente de manuscritos sin cambiar deliberadamente ese contrato sería una regresión de privacidad, no una mejora de UX.

## 5. Riesgos concretos que justifican el rechazo

Persistencia local de texto sensible implica, entre otros:

- restos de manuscrito en equipos compartidos;
- recuperación inesperada después de que el usuario crea haber terminado;
- exposición ante cualquier script same-origin comprometido;
- mayor impacto de XSS;
- complejidad de expiración/migraciones/esquema;
- necesidad de UI de borrar/restablecer;
- riesgo de almacenar inadvertidamente contenido que el usuario no esperaba conservar.

No es correcto describir `localStorage` como equivalente a memoria efímera de la pestaña.

## 6. Qué sí queda permitido

El `REJECT` afecta al guardado persistente por defecto de contenido sensible, no a todo uso posible de estado local.

Una futura excepción necesita simultáneamente:

1. herramienta claramente no sensible;
2. datos de bajo riesgo;
3. opt-in explícito, nunca implícito;
4. copy claro «se guarda solo en este dispositivo/navegador»;
5. botón visible clear/reset;
6. expiración o política de retención definida;
7. threat model revisado;
8. tests de borrado y migración;
9. ninguna contradicción con `private-tools-privacy-manifest.json`.

Ejemplos potenciales a estudiar, no aprobados automáticamente:

- preferencia visual no sensible;
- parámetros simples de una calculadora;
- URLs/IDs públicos, no texto inédito.

## 7. Qué no debe confundirse con P.2

- D.4 «leer después» guarda URLs públicas, no manuscritos; tiene su propia decisión `CONDITIONAL`.
- P.1 exportar un resultado localmente no requiere persistirlo después de cerrar la página.
- IndexedDB no evita el problema: cambia la API, no la naturaleza persistente del dato.
- `sessionStorage` tiene otro ciclo de vida, pero tampoco debe introducirse como workaround universal sin necesidad.

## 8. Definition of Done

Para P.2, el DoD actual es **no implementar la idea original** y preservar las garantías existentes:

- herramientas privadas no persisten manuscritos;
- auditoría de privacidad continúa verificándolo;
- documentación pública no promete algo distinto al runtime;
- cualquier futura excepción llega en PR propia con justificación y cambio explícito del contrato aplicable.

## 9. Conclusión

P.2 es un rechazo deliberado, no una tarea pendiente. #135 consideró la comodidad del autosave pero concluyó que, para un ecosistema que procesa manuscritos privados, la ausencia de persistencia es una propiedad de producto valiosa. La autoridad viva de `main` confirma hoy esa decisión.