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

- **Listas y abiertas:** #574, #575, #586, #592, #598, #599, #604, #605, #606, #607, #608 y #609. #608 (11 workflows verdes) y #609 (10 workflows verdes) comprobadas sobre su HEAD final.
- **En validación sobre HEAD final:** #610 (Wikidata), #611 (cuarentena Noveris canónica), #614 (breadcrumbs), #615 (fechas visibles/JSON-LD) y #616 (seguridad HTML). Los checks existentes deben completarse antes de marcar lista cada una.
- **Duplicada, NO MERGEAR:** #612 solapa exactamente con #611; conservar ABIERTA por trazabilidad, nunca integrar ambas.
- **Otras QA relacionadas:** #584, #589, #590, #591 y #600; evaluar individualmente antes de confirmar estado.
- **Integración individual:** #608/#610/#611/#615 afectan al preflight `scripts/release-readiness.py`; #607/#609/#614/#616 afectan a `.github/workflows/required-merge-gate.yml`. Tras cada merge del propietario, reconciliar cambios y revalidar HEAD y CI antes del siguiente; no fusionar en lote.
- **Criterio actualizado:** la presencia de una comprobación en `Check content indexes` no equivale a check obligatorio según el ruleset de main; la #616 repara esa diferencia para seguridad HTML. No duplicar checkers, conectar los existentes al gate correcto.

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
