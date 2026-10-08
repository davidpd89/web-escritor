# QA integral incremental — documento padre vivo

> **PR COORDINADORA / DRAFT / NO MERGEAR.** Esta PR solo añade documentación de gobernanza. **No contiene ni debe acumular código, fixes, tests o cambios de producción.** Cada cambio técnico vive en una PR pequeña, independiente y revisable contra main. Relacionada con issue #585 (índice operativo anterior). Línea paralela y separada: skills #577.

## Mandato original y evolución

Auditar de forma continua y sistemática davidportodiaz.com y el repositorio completo: probar lo que aún no está probado, buscar inconsistencias entre páginas/familias/formatos, homogeneizar estilos y comportamiento donde corresponda, verificar responsive (anchos, zoom, reflow, orientaciones, foco, teclado, accesibilidad), CSS y tipografía, seguridad, privacidad, SEO, metadatos, navegación, datos y artefactos generados, flujos y compatibilidad. Comenzamos por tipografía V1 y sus fuentes (familias, tokens, stacks, métricas, assets locales), ampliamos al shell y a contratos públicos/CI. **La prioridad no es fabricar PR: es descubrir un fallo real o una laguna de cobertura demostrable.**

No asumir que la solución conocida sigue siendo óptima: antes de implementar investigar documentación oficial **actual en la fecha del trabajo**, código abierto mantenido, estándares y repositorios públicos, compatibilidad y licencias. Reutilizar lo sólido sin inventar frameworks paralelos, dependencias o scripts redundantes. Contrastar siempre con la arquitectura, cambios recientes, tests, workflows y PR abiertas del repositorio.

## Ciclo de cada PR hija

1. Auditar main, PR concurrentes, archivos afectados y contratos ya existentes. Formular riesgo/propiedad verificable y escenario positivo/negativo; descartar la idea si ya está cubierta.
2. Investigar referencias oficiales vigentes y soluciones públicas apropiadas. Documentar solo evidencia relevante.
3. Crear rama **desde main** y PR pequeña (una propiedad por PR; sin mezclar áreas); no basarse implícitamente en otra PR pendiente.
4. Corregir el fallo si existe; si el comportamiento es correcto, crear una prueba útil que impida la regresión. Evitar tests que pasan por casualidad, basados en snapshots frágiles o waits arbitrarios.
5. Ejecutar tests focalizados, revisar diff y su semántica; después revisar los **workflows realmente aplicables al HEAD final**. Si faltan checks, mantener en validación. Si falla un check, investigar la causa, corregir y volver a validar. No confundir “GitHub mergeable” con aprobación funcional.
6. Registrar en cada PR evidencia before/after, comandos/resultados, alcance, riesgo, limitaciones, CI y enlace **a esta PR padre**. Mantener esta coordinadora al día con enlaces y estados sin narración excesiva.
7. **NO MERGEAR, NO CERRAR, NO AUTO-MERGE, NO PUSH A MAIN.** Solo el propietario hace merge, **una PR cada vez**, revisando conflictos y revalidando respecto del nuevo main cuando cambie. La coordinadora nunca se utiliza como lote de cambios a fusionar.

## Protocolo de revisión externa (Codex y otros revisores)

- Antes de declarar lista cualquier PR hija, consultar **comentarios generales, revisiones e hilos inline** del HEAD vigente y comprobar si hay nuevas observaciones desde la última validación.
- Cada hallazgo se contrasta con los archivos reales, pruebas reproducibles y documentación oficial actual. No aplicar propuestas por autoridad sin verificar ni descartar defectos solo porque CI pasó.
- Si es correcto, corregir **dentro del mismo scope** y añadir una prueba de regresión cuando aporte valor. Si es falso positivo, fuera de alcance o redundante, justificar la decisión técnicamente en el hilo/PR; no silenciarla sin explicar.
- Cada nuevo commit invalida el estado «lista»: volver a revisar diff, dependencias y todos los checks aplicables del HEAD final; registrar respuesta y evidencia.
- No resolver hilos de revisión con hallazgos abiertos ni afirmar que «Codex aprobó» sin una aprobación observable.
- Las revisiones de skills #577/#593 pertenecen a la otra conversación y no deben duplicarse desde esta línea.

## Criterio para nuevos gates y presupuesto de CI (revisión Codex, 2026-10-08)

**No convertir todos los workflows auxiliares en checks universales por inercia.** Antes de añadir un gate exigir: riesgo reproducible no cubierto por el ruleset actual, chequeo existente sin ejecución obligatoria, inputs/artefactos adecuados, coste razonable y tests que capturen fallos reales. Si el riesgo es local, mantener un workflow especializado y no duplicar su ejecución. Comprobar siempre la matriz de checks requeridos real.

- **`scripts/release-readiness.py`:** checks deterministas, cortos y solo de lectura que inspeccionan el árbol fuente (o artefactos fuente existentes), tienen las dependencias ya instaladas en el gate y se benefician de figurar en la evidencia consolidada. Su registro se integra de forma secuencial; evitar incorporar checks que escriban archivos versionados o dependan de la red.
- **Paso explícito de `required-merge-gate.yml`:** cuando importa el orden respecto a los builders, se requiere inspeccionar el **dist final después de construirlo**, hace falta un entorno especial, o se desea una comprobación/diagnóstico separado por un motivo concreto. No añadir otro paso si el mismo contrato ya corre en el preflight.
- **Tests pequeños en `tests/test-*.py`:** invariantes/mutaciones de una implementación, con entradas positivas y negativas. No confundir que pasen los fixtures con que un checker audite todas las páginas reales.
- **Integración:** las hijas que tocan `release-readiness.py` o el mismo workflow tienen dependencia de merge *operativa*, aunque nazcan de `main` y sean PR independientes. Tras cada merge del propietario, revisar el diff de cada otra hija y preservar las líneas de las ya integradas; actualizar la rama y repetir CI.
- **Presupuesto de tiempo:** `Required merge gate` tiene `timeout-minutes: 20`. Referencias observadas en GitHub Actions del 8-oct-2026 (HEADs específicos): #619, job completo **69 s** (17 s tests Python; 7 s preflight), #615 **108 s** (24 s tests; 13 s preflight), #610 **87 s** (19 s tests; 10 s preflight). Son muestras **anteriores a la integración secuencial** de todas las hijas y no predicen el tiempo acumulado final. Revisar este indicador y el tiempo del preflight después de cada merge; si se acerca al timeout, optimizar/eliminar duplicidades antes de sumar otro gate. No subir timeout automáticamente para ocultar regresiones.

## Estados inequívocos

- **CANDIDATA:** hueco aún por demostrar.
- **EN INVESTIGACIÓN:** evidencia/duplicidades/alternativas.
- **EN IMPLEMENTACIÓN:** modificación limitada en rama independiente.
- **EN VALIDACIÓN:** CI incompleto/rojo, revisión técnica o interacción por resolver.
- **LISTA PARA REVISIÓN Y MERGE DEL AUTOR:** diff final, tests pertinentes y todos los checks aplicables verdes. Sigue ABIERTA.
- **MERGEADA POR EL AUTOR:** solo tras comprobar el estado real de GitHub.
- **DESCARTADA / SUSTITUIDA / DUPLICADA:** nunca equivalen a “lista”; documentar por qué y cuál es la alternativa.

## Índice inicial de PR hijas y relacionadas (consultar siempre estado real)

**Tipografía / V1 y consistencia:** #574, #575, #586, #592, #598, #599, #604, #605.  
**Infraestructura de pruebas, comportamiento y QA relacionado:** #584, #589, #590, #591; fix acotado #600.  
**Contratos públicos y CI:** #606, #607, #608, #609, #610, #611, #612.

**Deduplicación resuelta:** #611 es la implementación canónica de la cuarentena Noveris; #612 es duplicada y queda abierta para trazabilidad, pero NO MERGEAR. #610 y #611 pasan a `release-readiness.py`/Required merge gate, en lugar de depender únicamente del workflow auxiliar `Check content indexes`. Algunas PR (por ejemplo #608 y #609) evolucionaron de workflow opcional a Required merge gate después de su primera revisión: leer sus HEAD/diffs actuales, no descripciones antiguas.

**Línea que NO pertenece aquí:** investigación/adopción de skills de GitHub #577, su PR hija #593 y otros desarrollos explícitamente adscritos a skills; coordinar cruces, no duplicar.

## Estado operativo (8 de octubre de 2026)

- **Listas y abiertas:** #574, #575, #586, #592, #598, #599, #604, #605, #606, #607, #608, #609, #610 y #611. #610 y #611 tienen 11/11 workflows verdes en HEAD final. #608 (11 workflows verdes) y #609 (10 workflows verdes) comprobadas sobre su HEAD final.
- **Listas tras CI final:** #614 (breadcrumbs) y #616 (seguridad HTML), cada una 10/10 workflows en verde, abiertas.
- **Lista tras CI final:** #615 (semántica temporal HTML/JSON-LD), 11/11 workflows verdes sobre HEAD final, +1 línea en preflight. Los checks existentes deben completarse antes de marcar lista cada una.
- **Lista con CI completo:** #619, `check-article-dates.py --check` en Required merge gate: Cuaderno/JSON-LD/revisión editorial. Un archivo, +1 línea, HEAD final 11/11 workflows verdes; ABIERTA sin mergear.
- **EN VALIDACIÓN tras revisión Codex:** #618 amplía checker y mutaciones para `srcset`/`imagesrcset` (15 casos negativos, 9 positivos), atributos sin comillas y entidades. El 11/11 verde anterior no valida el HEAD nuevo, no mergear hasta CI y revisión.
- **EN VALIDACIÓN:** #620, corrección de límites WHATWG para `time datetime` (horas, fechas sin año, semana ISO, fracciones, offset) con 38 casos de regresión en script+test. CI pendiente.
- **LISTA:** #621, checker integrado de indexabilidad/sitemap/robots/canónicas/navegación en Required merge gate, +1 línea, HEAD final 11/11 workflows verdes; abierta sin mergear.
- **LISTA:** #622, comprobación AVIF/WebP (procedencia, dimensiones, correspondencia de `<source>` y fallback) en Required merge gate; +1 línea, HEAD final 11/11 workflows verdes; ABIERTA sin mergear.
- **LISTA:** #623 integra `check-professional-resources.py` al Required merge gate para editoriales/convocatorias/ICS; +1 línea, HEAD 7e695ef9, 11/11 checks verdes, mergeable, abierta sin mergear.
- **EN VALIDACIÓN:** #624, corrección aislada de duraciones HTML exactas en segundos (`P`, `PT`, meses/años inválidos) y soporte humano, con 13 válidos, 18 inválidos y 5 de compatibilidad JSON-LD; comparte archivo con #620 y requiere reconciliación secuencial. CI pendiente.
- **Duplicada, NO MERGEAR:** #612 solapa exactamente con #611; conservar ABIERTA por trazabilidad, nunca integrar ambas.
- **QA adicionales verificadas:** #584, #589, #590 y #591 listas, todas las comprobaciones del HEAD final verdes, ABIERTAS y sin merge.
- **#600 pendiente:** CI de cambios Identity green excepto timeout de una URL externa en `Check external links` (sin relación con el diff); el rerun del único job rojo falló otra vez por el mismo timeout externo; no declararla lista ni repetir ciegamente.
- **Integración individual:** #608/#610/#611/#615/#619/#621/#622/#623 afectan al preflight `scripts/release-readiness.py`; #607/#609/#614/#616 afectan a `.github/workflows/required-merge-gate.yml`. Tras cada merge del propietario, reconciliar cambios y revalidar HEAD y CI antes del siguiente; no fusionar en lote.
- **Criterio actualizado:** la presencia de una comprobación en `Check content indexes` no equivale a check obligatorio según el ruleset de main; la #616 repara esa diferencia para seguridad HTML. No duplicar checkers, conectar los existentes al gate correcto.

- **Candidata concretada como #624:** el checker admitía `P`/`PT` sin duración, meses/años en duraciones HTML. Contrato WHATWG y JSON-LD separados, pruebas de 36 casos, HEAD todavía en CI. Evitar merge conjunto con #620 sin reconciliar.

## Secuencia segura de integración propuesta (sin automatizar merges)

*Estado observado el 8-oct-2026; **NO** es autorización para merge automático.*

1. **Grupo de gates en YAML:** comprobar primero que #607, #609, #614 y #616 sigan verdes sobre sus HEAD finales. Integrar **una sola** PR por decisión del autor. Tras cada merge a main, refrescar el resto de ramas que tocan `.github/workflows/required-merge-gate.yml` y repetir CI si cambió su HEAD o base efectiva.
2. **Grupo de preflight en Python:** #608, #610, #611, #615, #619, #621, #622 están documentadas como listas con CI de sus HEAD individuales; **no equivalen a una integración combinada probada**. #623 ya está lista. Fusionar secuencialmente **solo cuando la base actual y todos los checks estén verificados**, sincronizar las demás ramas para **conservar las líneas de las ya integradas**, y comprobar que no se pierde ninguna entrada del listado `CHECKS`. No aprobar una PR basándose en CI de un HEAD anterior al sync.
3. **Seguridad HTML:** #616 introduce el checker en Required gate. #618 amplía la cobertura real de `srcset/imagesrcset` y sus pruebas, pero **sigue pendiente de CI de su HEAD nuevo**; no fusionarla por su antiguo 11/11 ni considerar que #616 sustituye sus mutaciones.
4. **Parser temporal compartido:** #620 (fecha/hora local/global, año extendido) y #624 (duraciones) **modifican el mismo script**. Ambas siguen en validación. Una vez que #620 pase revisión y sea mergeada por el autor, reconciliar #624 sobre el parser resultante conservando ambos contratos y ejecutar conjuntamente `tests/test-public-time-microsyntax.py`, `tests/test-public-time-duration-microsyntax.py` y `scripts/check-public-time-semantics.py` más CI total. Si se invierte el orden de merge, invertir también la reconciliación.
5. **Bloqueos no resueltos:** #600 tiene un timeout externo reproducido en su workflow; **NO LISTA**. #612 duplica la #611: **NO MERGEAR**. #613 permanece coordinadora draft hasta cerrar el conjunto; el usuario decide todos los merges.

**Control por paso:** tras cada merge manual comprobar SHA de `main`, diff de cada hija contra el nuevo `main`, mergeability real, hilos de Codex y todos los checks exigidos. Medir duración de Required gate y preflight tras cada integración; ante regresión, detener la secuencia y corregir antes de continuar.

## Registro y mantenimiento

- Esta PR es la **fuente de verdad de objetivos, criterios de aceptación, alcance y parentesco**. El documento versionado que añade es su respaldo y punto de reanudación entre conversaciones.
- La issue #585 queda como índice histórico/redirección a esta coordinadora, no como una tercera línea paralela.
- Cada nueva PR hija debe enlazar a esta coordinadora y explicar una unidad verificable. Actualizar la tabla de seguimiento en el cuerpo de la coordinadora, *no* añadiendo código de las hijas.
- No escribir “Closes #padre” ni comandos automáticos que puedan cerrar accidentalmente la coordinadora.
- Nunca prometer que los tests pueden sustituir QA real de dispositivos/servicios: separar lo automatizable de lo manual.
- La coordinación es dinámica: revisar periódicamente prioridades a la luz de main y resultados, conservando decisión y trazabilidad.

## Checklist antes de considerar una hija terminada

- [ ] Sin duplicidad con main/otras PR
- [ ] Referencias/documentación actual verificadas cuando sean materiales
- [ ] Diff pequeño, scope único, pruebas relevantes
- [ ] Pruebas negativas/mutaciones cuando agreguen cobertura real
- [ ] CI completo del HEAD final verde
- [ ] Sin conflictos ni dependencias ocultas con otras PR pendientes
- [ ] PR hija enlazada aquí; estado y riesgos actualizados
- [ ] Abierta y **sin mergear**
