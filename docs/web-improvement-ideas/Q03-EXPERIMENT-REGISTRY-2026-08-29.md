# Q.3 · Registro versionado de experimentos — reconstrucción completa desde PR #135

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: snapshot `8e72321d047c0445c5ac411ebe242af8a0386929` de PR #135.  
Estado final histórico: `IMPLEMENT_NOW`.

## 1. Hipótesis original

Q.3 proponía conservar un registro breve de «qué probamos y qué pasó» para cambios significativos de SEO/UX: hipótesis, cambio, resultado y aprendizaje. El objetivo era evitar repetir experimentos ya fallidos, confundir correlación con causalidad o perder el contexto de una decisión meses después.

La idea no era crear una plataforma de experimentación ni otro dashboard. Era introducir memoria operativa versionada y auditable dentro del mismo repositorio.

## 2. Evolución dentro de #135

### Revisión exhaustiva 27/08

Decisión: `IMPLEMENT_NOW`.

Se definió un registro versionado con, como mínimo:

- hipótesis;
- baseline;
- SHA/cambio aplicado;
- métrica principal;
- ventana de observación;
- anomalías/confounders;
- resultado;
- decisión;
- rollback o siguiente paso.

La revisión insistió en dos límites:

1. un experimento no autoriza por sí solo el cambio;
2. no registrar resultados ficticios ni atribuir causalidad sin ventana/baseline suficientes.

### Matriz final 28/08

Decisión: `YA_CUBIERTO`.

No significaba que la capacidad existiera previamente en `main`. Significaba que, durante el trabajo de PR #135, ya se había materializado `data/experiments.json` y su contrato. Por eso la matriz dejó de tratar Q.3 como algo por diseñar.

### Autoridad final humana + machine-readable

Estado final: `IMPLEMENT_NOW`.

`data/web-improvement-decisions-2026-08-28.json` lo declara además en `deliveredInPr135`:

> Versioned experiment registry + schema/contract are implemented in this PR. Future work is to populate it when experiments actually run.

Esta distinción es esencial: la autoridad final conserva `IMPLEMENT_NOW` como decisión, mientras el entregable ya estaba construido **dentro de #135**.

## 3. Artefacto histórico entregado por #135

En el snapshot histórico existe `data/experiments.json` con este baseline:

```json
{
  "schemaVersion": 1,
  "description": "Registro de experimentos medibles de SEO/UX/performance. Un experimento no autoriza cambios por sí solo.",
  "allowedDecisions": ["KEEP", "REVERT", "ITERATE", "INCONCLUSIVE"],
  "experiments": []
}
```

El array vacío era correcto: el registro no debía rellenarse retrospectivamente con experimentos inventados para aparentar historial.

## 4. Revalidación contra `main` actual

Comprobación directa el 29/08/2026:

- `data/experiments.json` existe en `8e72321...`;
- `data/experiments.json` devuelve **404 en `main`**.

Por tanto el estado de verdad es:

```text
DOCUMENTED = true
IMPLEMENTED_IN_PR(#135) = true
MERGED_MAIN = false
CONFIGURED_LIVE = not applicable
VERIFIED_E2E = false
```

No es correcto decir hoy `ALREADY_COVERED` en `main` solo porque la matriz intermedia de #135 usara `YA_CUBIERTO`: aquella etiqueta describía el estado de la rama de #135, no el resultado de un merge que nunca ocurrió.

La decisión práctica para una futura implementación es recuperar el contrato ya diseñado, no volver a inventar otro registry.

## 5. Contrato funcional que debe recuperarse

Un experimento real debería poder expresar, según aplique:

- `id` estable;
- `title`/descripción breve;
- área: SEO, UX, performance, contenido, conversión…;
- `hypothesis`;
- `baseline` y fuente de baseline;
- cambio/variable independiente;
- SHA, PR o versión desplegada;
- métrica primaria y guardrails;
- fecha de inicio;
- fecha/ventana prevista de evaluación;
- contexto/anomalías/confounders;
- resultado observado;
- decisión final: `KEEP`, `REVERT`, `ITERATE`, `INCONCLUSIVE`;
- evidencia o fuente de datos;
- rollback/follow-up si corresponde.

No todos los campos tienen que publicarse en la web. Es una autoridad interna de decisión.

## 6. Reglas de gobernanza

### Antes del experimento

- definir hipótesis antes de mirar el resultado;
- elegir una variable principal cuando sea posible;
- definir qué resultado cambiaría la decisión;
- registrar baseline y fuente;
- no usar una ventana arbitrariamente corta solo para obtener una conclusión.

### Durante

- no cambiar simultáneamente varias variables sin documentarlo;
- registrar incidentes, campañas, estacionalidad o cambios externos que puedan sesgar la lectura;
- no mover el criterio de éxito después de ver los datos.

### Después

- `INCONCLUSIVE` es resultado válido;
- no forzar KEEP/REVERT si la muestra no permite concluir;
- distinguir observación de causalidad;
- conservar el resultado aunque se revierta;
- registrar la decisión humana, no solo la métrica.

## 7. Primer caso claro preservado por #135

La investigación detectó una oportunidad concreta en Search Console: la query `portal fantasy` tenía aproximadamente 91 impresiones y 1 clic en el snapshot operativo de agosto de 2026.

La recomendación no era crear más páginas, sino:

1. identificar URL, posición, dispositivo/país y snippet reales;
2. modificar una variable razonable —por ejemplo title/snippet si la evidencia lo justifica—;
3. registrar baseline;
4. esperar una ventana suficiente;
5. comparar CTR/posición sin atribución falsa;
6. decidir `KEEP/REVERT/ITERATE/INCONCLUSIVE`.

Q.3 es la autoridad natural para registrar ese tipo de prueba.

## 8. Qué no debe convertirse en «experimento»

- corregir un bug reproducible;
- arreglar una violación de accesibilidad conocida;
- actualizar un hecho editorial falso/desactualizado;
- implementar una obligación legal/seguridad necesaria;
- comparar vanity metrics sin hipótesis;
- cambiar varias cosas y luego escoger la métrica que mejoró.

Esos trabajos pueden medirse, pero no deben maquillarse como A/B tests.

## 9. No crear infraestructura paralela

Cuando se recupere Q.3:

- restaurar/evolucionar `data/experiments.json`;
- no crear `experiments-v2.json`, una Sheet paralela o una base SaaS sin necesidad;
- si el schema necesita cambiar, versionarlo deliberadamente y migrar;
- cualquier UI futura debe leer del registry, no convertirse en otra autoridad.

No hace falta añadir tracking nuevo para tener un registro de experimentos. Las fuentes pueden ser GSC, Bing, CrUX, Lighthouse, analytics agregada, tests de usuario o QA existente.

## 10. Definition of Done de la recuperación

- existe un único registry versionado;
- schema/documentación describe campos obligatorios/opcionales;
- decisiones permitidas conservan `KEEP/REVERT/ITERATE/INCONCLUSIVE` salvo migración justificada;
- array inicial puede seguir vacío: cero resultados inventados;
- test/validador detecta IDs duplicados, estados inválidos y registros incompletos;
- todo experimento nuevo referencia una hipótesis y baseline previos;
- puede enlazar SHA/PR y evidencia;
- ninguna entrada contiene PII innecesaria;
- el registry no autoriza deploy/merge automáticamente;
- historial no se reescribe para borrar experimentos fallidos.

## 11. Relaciones con otras ideas

- **C.3:** preguntas/demanda real pueden generar hipótesis, no contenido automático.
- **C.5/R.21:** el experimento CTR de `portal fantasy` es caso natural.
- **E.2/E.3/E.4/E.5:** cambios de performance medidos pueden registrarse cuando sean experimentales.
- **Q.1:** CrUX puede aportar métrica de campo cuando exista muestra.
- **Q.2:** GSC+Bing aportan observaciones que pueden generar experimentos.
- **Q.4:** launch checklist es runbook, no registro de experimentos.

## 12. Conclusión

Q.3 es uno de los casos donde la taxonomía de verdad evita un error serio. #135 **sí lo implementó en su rama**, pero esa rama no se fusionó. Por tanto no hay que rediseñarlo y tampoco hay que afirmar que `main` ya lo contiene. La futura PR de implementación debe recuperar el registry diseñado en #135, mantenerlo vacío hasta que existan pruebas reales y usarlo como memoria auditable de decisiones, no como generador de métricas.