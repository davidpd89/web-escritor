# Handoff final — individualización completa de las 108 ideas de PR #135

**Fecha de auditoría:** 2026-08-29  
**Snapshot histórico de arqueología:** `8e72321d047c0445c5ac411ebe242af8a0386929`  
**`main` auditado:** `291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**PR coordinadora:** #148  
**Resultado:** `108/108` ideas originales individualizadas, sin IDs ausentes ni duplicados.

## 1. Qué se ha cerrado

Las ideas originales A.1–Q.4 de la antigua PR #135 tienen una PR DRAFT individual y docs-only. Cada PR conserva, cuando existe material específico para esa idea:

- hipótesis original;
- investigación y fuentes;
- evolución de estados;
- contradicciones y overrides;
- inspección del repositorio;
- blueprints/alternativas;
- decisión humana y machine-readable de #135;
- revalidación independiente;
- aportaciones únicas de pasadas posteriores;
- riesgos, anti-patrones, pruebas y Definition of Done;
- revalidación contra `main` cuando el estado práctico pudo cambiar.

La intención de estas PR no es afirmar que las 108 capacidades estén implementadas. Son unidades revisables de **conocimiento + decisión + contrato de ejecución**.

## 2. Cobertura exacta y huecos explicados

Las PR individuales ocupan el intervalo #150–#263, excluyendo exactamente seis PR ajenas al banco de ideas:

| PR | Motivo de exclusión |
|---:|---|
| #160 | fix de diseño HOME, ya mergeado |
| #161 | fix de diseño HOME, ya mergeado |
| #162 | fix de diseño HOME, ya mergeado |
| #163 | cadena de diseño abierta: HOME |
| #174 | cadena de diseño abierta: Libros |
| #205 | cadena de diseño abierta: Manecillas |

El intervalo contiene 114 números. `114 - 6 = 108`, y el manifiesto máquina-legible prueba la correspondencia uno-a-uno entre A.1–Q.4 y las 108 PR restantes.

Mapa por bloques:

- #150–#159 → A.1–A.10
- #164–#173 → A.11–A.12 + B.1–B.8
- #175–#184 → B.9 + C.1–C.9
- #185–#194 → C.10 + D.1–D.9
- #195–#204 → D.10–D.12 + E.1–E.7
- #206–#215 → E.8 + F.1–F.6 + G.1–G.3
- #216–#225 → G.4–G.5 + H.1–H.6 + I.1–I.2
- #226–#235 → I.3–I.5 + J.1–J.6 + K.1
- #236–#245 → K.2–K.5 + L.1–L.4 + M.1–M.2
- #246–#255 → M.3–M.5 + N.1–N.3 + O.1–O.4
- #256–#263 → P.1–P.4 + Q.1–Q.4

## 3. Regla de precedencia

No tratar todos los documentos como autoridades equivalentes.

1. **Snapshot histórico #135 (`8e72321...`)**  
   Es la fuente de arqueología: conserva investigación, pasadas, contradicciones y blueprints históricos.

2. **PR individual de la idea (#150–#263, excluyendo las seis ajenas)**  
   Es la autoridad detallada para revisar esa idea concreta. Reconcilia la arqueología de #135 con la evidencia del repositorio disponible durante la recuperación.

3. **PR #148**  
   Es la coordinadora/autoridad condensada global de las 108 decisiones. Sirve para mapa, fuentes, plan y guardrails, pero no sustituye la arqueología detallada de cada PR individual.

4. **Evidencia posterior de `main`, producción o una fuente primaria del proveedor**  
   Puede invalidar un hecho factual antiguo. Cuando eso ocurra debe actualizarse la decisión práctica sin borrar la historia que explica cómo se llegó a ella.

Una fuente secundaria o una pasada antigua no puede promocionar por sí sola una idea contra una autoridad posterior.

## 4. Estados: no confundir documentación con realidad

La regla transversal es:

`DOCUMENTED ≠ IMPLEMENTED_IN_PR ≠ MERGED_MAIN ≠ CONFIGURED_LIVE ≠ VERIFIED_E2E`

Interpretación operativa:

- `REJECT`: conservar la decisión; no desarrollar la feature salvo evidencia nueva que justifique reabrirla.
- `DEFER`: conservar para futuro; no convertirla ahora en backlog activo.
- `CONDITIONAL`: no implementar hasta aportar evidencia explícita del trigger definido en su PR.
- `PARTIAL_AUDIT`: medir o inventariar antes de escribir código.
- `ALREADY_COVERED`: mantener/extender la autoridad existente; no construir un sistema paralelo.
- `IMPLEMENT_AFTER_CURRENT_DEBT`: sí merece desarrollo, pero en una PR de implementación separada cuando la deuda prioritaria esté cerrada.
- `IMPLEMENT_NOW`: decisión favorable; aun así la PR documental no equivale a implementación runtime.
- `EXTERNAL_OPERATION`: Git solo puede documentar/runbook; cuenta, configuración y resultado requieren evidencia externa real.

## 5. Excepciones y reconciliaciones críticas

### E.7 — compresión

La autoridad histórica final llegó a `NOT_APPLICABLE` por Cloudflare DNS-only. La revalidación independiente y #148 corrigieron la inferencia a **`PARTIAL_AUDIT` efectivo**: DNS-only demuestra que Cloudflare no está haciendo proxy/compresión edge, pero no qué `Content-Encoding` entrega el origen.

No activar proxy naranja solo para “tener Brotli”. Primero observar respuestas live.

### E.8 + I.2 — registro de terceros/privacidad

#135 sí llegó a materializar el registro/baseline, pero #135 no se fusionó.

- `IMPLEMENTED_IN_PR(#135) = true`
- `MERGED_MAIN = false`

Cuando se implemente debe recuperarse **una sola autoridad compartida** para performance/terceros/privacidad, no crear registros paralelos.

### Q.3 — registro de experimentos

`data/experiments.json` existe en `8e72321...` y no existe en el `main` auditado.

Debe recuperarse el contrato histórico, no reinventarse. La existencia en una rama cerrada no autoriza marcarlo como ya desplegado.

### B.9 — glosario de Noveris

El trigger está sustancialmente cumplido en la página actual de Noveris mediante contenido visible y `DefinedTermSet`. No crear `/glosario/` paralelo. Cualquier `FAQPage` residual se revisa bajo A.7, no dentro de B.9.

### C.7 — mapa/línea temporal

Noveris ya dispone de mapa funcional con explicación textual. No duplicar el mapa. Otras visualizaciones siguen condicionadas a necesidad, canon, spoilers y accesibilidad.

### J.3 — calendario

El pipeline `.ics` ya existe (`scripts/build-event-calendars.py`). Una sesión de club real se declara en la autoridad general de eventos y reutiliza ese pipeline; no crear Google Calendar API/OAuth u otro builder.

### J.6 — lectores beta

La infraestructura existe, pero eso no prueba lista/workflows/configuración live ni E2E. Mantener la separación:

`CODE_PRESENT ≠ CONFIGURED_LIVE ≠ VERIFIED_E2E`

### Q.4 — plantilla de lanzamiento

A fecha 2026-08-29, el lanzamiento de Manecillas del 2026-09-03 todavía es futuro. Los runbooks ya cubren el lanzamiento. La plantilla reusable se extrae **después** del evento mediante postmortem real, no antes.

## 6. Hallazgos finales fuera de las 108 ideas

#135 investigó controles adicionales para confirmar que no quedaba una categoría técnica grave fuera del banco. No requieren nuevas PR individuales:

- **Navigation Preload:** absorbido en E.6 como `PARTIAL_AUDIT`; solo tras trace de cold navigation y uso correcto de `preloadResponse`.
- **bfcache:** `NO_ACTION`; no se localizaron `unload`/`beforeunload`. Verificar durante auditoría de navegación, sin feature nueva.
- **WCAG 2.2 adicional:** Focus Not Obscured absorbido en F.4; Consistent Help se beneficia del shell; otros criterios se reabren solo si aparecen flujos aplicables.
- **Google Site Reputation Abuse, actualización 2026-08-28:** policy watch; no genera feature nueva.
- **PWA shortcuts/Badging:** absorbidos respectivamente en L.3 y L.4.

Las demás oportunidades R.* con aportación material fueron incorporadas a las PR relacionadas o permanecen en el corpus histórico/#148 de integraciones. No abrir una “pasada 16” por volumen; reabrir solo ante evidencia nueva.

## 7. Protocolo recomendado para Claude

1. Revisar #148 para entender mapa global, estados y reglas.
2. Antes de decidir sobre una idea, abrir su PR individual y leer el documento completo; no decidir únicamente por el título o la tabla de #148.
3. Para `REJECT`/`DEFER`, se puede mergear documentación si se quiere conservar autoridad en `main`, pero **no** abrir implementación salvo nueva evidencia.
4. Para `CONDITIONAL`, exigir el trigger factual definido antes de desarrollar.
5. Para `PARTIAL_AUDIT`, ejecutar primero la medición/inventario descrito; la auditoría puede concluir `NO_ACTION`.
6. Para `ALREADY_COVERED`, inspeccionar y extender el sistema existente; no crear una segunda autoridad.
7. Para `IMPLEMENT_NOW`/`IMPLEMENT_AFTER_CURRENT_DEBT`, desarrollar en una PR de implementación separada. Mantener la PR arqueológica como documento de decisión; no mezclar un cambio runtime grande dentro de ella.
8. Para `EXTERNAL_OPERATION`, pedir acceso/autorización explícita y adjuntar evidencia live; Git no certifica por sí solo que la operación externa exista.
9. Tras implementar, actualizar ledger/autoridad de estado sin borrar el razonamiento histórico.
10. Antes de cada merge, refrescar contra el `main` vigente y revisar CI. `mergeable:true` no equivale a CI verde ni a E2E.
11. La cadena de diseño #163 → #174 → #205 es independiente de las 108 PR documentales y mantiene su propio orden de stacking/revisión.

## 8. Resultado de esta auditoría de cierre

Comprobado:

- 108 IDs esperados A.1–Q.4;
- 108 PR únicas;
- cero IDs ausentes;
- cero PR de idea duplicadas;
- seis números ajenos explicados;
- PR finales consultadas como OPEN/DRAFT/no merge y mergeables;
- aislamiento docs-only verificado durante la creación por lotes y de nuevo en el bloque final;
- diferencias `IMPLEMENTED_IN_PR` vs `MERGED_MAIN` preservadas;
- hallazgos fuera de 108 absorbidos o declarados `NO_ACTION`;
- dos erratas de descripción detectadas y corregidas:
  - #225: `inventaría` → `identifica`;
  - #253: `inventaría` → `detecta`.

No se ha encontrado en esta auditoría un error de decisión que obligue a rehacer una de las 108 PR.

### Nota sobre A.1–A.10

A.1–A.10 nacieron sobre un `main` anterior (`0eae248f...`), mientras los lotes posteriores se crearon sobre `291c8c...`. Siguen siendo docs-only y GitHub las considera mergeables. Los cambios de `main` entre ambas bases fueron principalmente fixes de diseño; la revalidación de cierre no ha encontrado una decisión factual A.1–A.10 invalidada por ellos. Claude debe, como con cualquier PR, refrescar el HEAD contra el `main` vigente antes del merge si la política de integración lo exige.

## 9. Límite del visto bueno

Este cierre certifica la **integridad de recuperación, trazabilidad y preparación para revisión**. No significa:

- que las 108 features estén desarrolladas;
- que todas deban desarrollarse;
- que operaciones externas estén configuradas;
- que producción esté verificada E2E;
- que todos los workflows de todas las PR sigan verdes en el instante del merge.

Claude debe revisar/desarrollar/mergear según el estado y el protocolo anterior, con `main` fresco y CI del HEAD que vaya a fusionar.
