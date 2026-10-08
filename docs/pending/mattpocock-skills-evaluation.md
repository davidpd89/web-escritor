# Evaluación de mattpocock/skills para web-escritor

> Estado: **INVESTIGACIÓN ACTIVA · ADOPCIÓN SELECTIVA · NO MERGEAR ESTA PR TODAVÍA**

## Recurso

Repositorio a revisar:

https://github.com/mattpocock/skills

Página explicativa / catálogo de skills:

https://www.aihero.dev/skills

## Objetivo

Determinar qué skills, patrones o instrucciones de ese repositorio mejoran de forma comprobable el desarrollo, mantenimiento, QA o automatización de `web-escritor`.

No se presupone que deba instalarse ni copiarse nada. Primero hay que entender qué contiene, cómo funciona y qué encaja de verdad con este proyecto.

## Proceso de evaluación

Durante la evaluación:

1. Revisar el estado y documentación actuales del repositorio externo.
2. Inventariar las skills disponibles y para qué sirven.
3. Separar:
   - skills directamente útiles para este repo;
   - ideas adaptables;
   - contenido redundante con lo que ya tenemos;
   - contenido incompatible o innecesario.
4. Compararlas con:
   - instrucciones actuales del proyecto;
   - flujos de Codex/Claude/ChatGPT;
   - tests y QA existentes;
   - documentación del repo;
   - automatizaciones ya implantadas.
5. Probar solo las candidatas con beneficio concreto y medible.
6. Evitar introducir dependencias, prompts o automatizaciones duplicadas sin necesidad.
7. Revisar licencia y condiciones antes de copiar o incorporar contenido.
8. Documentar cualquier adopción indicando qué problema resuelve.

## Criterio de adopción

- Usar primero la skill pública upstream, sin crear una variante local por defecto.
- No añadir infraestructura de agentes, wrappers, adaptadores o documentación paralela si la skill ya puede utilizarse directamente.
- Una skill se considera útil solo si descubre un problema real, reduce trabajo repetido o mejora de forma comprobable una implementación/revisión.
- Los hallazgos concretos sí pueden convertirse en PR pequeñas del repo (tests, QA, CI o código), una por problema.
- Si una skill no aporta nada sobre el proceso actual, no se integra.
- Evitar ciclos de review infinitos: un hallazgo debe verificarse contra el código antes de actuar.

## Resultado provisional de la primera prueba

### Útil ahora: `code-review`

Se ha usado directamente como método de revisión sobre PR pequeñas existentes.

Resultado comprobado:

- detectó que #574 acoplaba un test tipográfico al formato minificado del CSS;
- el hallazgo se convirtió en #579;
- una primera solución demasiado compleja se simplificó durante la propia review hasta un diff neto de 12 líneas añadidas / 4 eliminadas;
- al aplicarlo a #575 no apareció ningún defecto verificable, por lo que no se creó trabajo artificial.

Conclusión provisional: **usar upstream como herramienta de revisión, sin instalar/forkear una copia local por defecto**.

### Usar solo cuando exista el caso

- `diagnosing-bugs`: cuando haya un fallo reproducible o CI rojo cuya causa no esté clara.
- `tdd`: al corregir un bug o implementar comportamiento nuevo donde un test previo aporte una señal real.
- `improve-codebase-architecture`: no aplicar de forma general ahora; el scope es demasiado amplio para el objetivo de PR pequeñas y fácilmente revisables.
- `prototype`: reservar para una prueba visual concreta antes de tocar producción.

No convertir estas skills en infraestructura permanente hasta que un caso real demuestre que hace falta.

## Estado de adopción

| Skill | Estado | Motivo |
| --- | --- | --- |
| [`pr`](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/pr) | **PILOTO EN REVISIÓN** → #593 | Un cuerpo homogéneo puede ahorrar revisión; las copias actuales en Codex y Claude deben justificar instalación/mantenimiento frente a los plugins oficiales y superar paridad + activación real. No dar por terminada la adopción mientras #593 siga bloqueada por review. |
| [`code-review`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/code-review/SKILL.md) | **USAR UPSTREAM, NO VENDORIZAR** | Ha encontrado problemas reales en #574/#579, #586/#595 y #592/#594. No se copia por problemas reportados de recursión ([upstream #573](https://github.com/mattpocock/skills/issues/573)); se usa como revisión independiente. |
| [`retro`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/retro/SKILL.md) | **USAR PUNTUALMENTE, NO INSTALAR** | La prueba sobre esta sesión fue útil para confirmar qué NO convertir en infraestructura. No produjo una mejora permanente adicional. |
| [`diagnosing-bugs`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/diagnosing-bugs/SKILL.md) | **USAR UPSTREAM MANUALMENTE, NO VENDORIZAR** | Ya demostró valor sobre #597: artifact real → causa de CLS → fix mínimo #600. No instalar con auto-invocación: hay informe upstream de sobre-activación en preguntas simples ([#578](https://github.com/mattpocock/skills/issues/578)); no convertir un caso concreto en afirmación universal del modelo. |
| [`tdd`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/tdd/SKILL.md) | **ESPERAR IMPLEMENTACIÓN ADECUADA** | Útil para comportamiento nuevo con interfaz pública acordada; [su propio SKILL.md](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/tdd/SKILL.md) obliga a confirmar antes el punto de prueba y remite a `codebase-design` si la interfaz está en duda, no como dependencia de instalación. |
| [`implement`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/implement/SKILL.md) | **NO ADOPTAR AHORA** | Upstream revisa antes del commit aunque `code-review` puede no ver cambios sin commit, hace commit directo en la rama actual y puede consumir mucho contexto por ticket. Choca con nuestro flujo PR-first/revisión fresca. |
| [`to-spec`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/to-spec/SKILL.md) | **NO ADOPTAR AHORA** | #585 ya cubre el caso actual con menos ceremonia. Requiere tracker/labels y hay un problema reportado de etiquetado del padre como `ready-for-agent` ([#606](https://github.com/mattpocock/skills/issues/606)), con riesgo de asignación excesiva en agentes AFK. Reevaluar solo para trabajo realmente multi-sesión. |
| [`triage`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/triage/SKILL.md) | **NO ADOPTAR AHORA** | Upstream la limita a issues/PR entrantes de terceros; nuestro hardening actual nace de planificación propia (#585). Requiere setup de tracker/labels y el setup actual **sí instruye crear etiquetas faltantes** ([skill en el ref auditado](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/setup-matt-pocock-skills/SKILL.md)); las razones vigentes para no adoptar son necesidad de configuración y ausencia de incidencias entrantes de terceros. Añadiría proceso sin mejorar el flujo actual. |
| [`research`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/research/SKILL.md) | **NO ADOPTAR AHORA** | Existe incidencia sobre subagentes anidados ([#530](https://github.com/mattpocock/skills/issues/530)); los documentos de investigación pueden resultar efímeros. No hay beneficio probado de instalarla. Usar solo puntualmente para una pregunta externa muy estrecha. |
| [`prototype`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/prototype/SKILL.md) | **PENDIENTE DE CASO VISUAL REAL** | No hay ahora una decisión UI/UX abierta que justifique probarla. Reservar para una comparación visual concreta y desechable. |
| [`wizard`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/wizard/SKILL.md) | **USAR PUNTUALMENTE, NO INSTALAR** | Puede servir para un futuro flujo de dashboard/credenciales, pero no encaja con la mayor parte de #555 (QA multidispositivo/manual). |
| [`handoff`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/handoff/SKILL.md) | **NO ADOPTAR TODAVÍA; COMPATIBILIDAD CODEX PENDIENTE** | [Issue upstream #622](https://github.com/mattpocock/skills/issues/622) abierta (verificada 2026-10-08): en Codex un handoff escrito en `/tmp` puede desaparecer entre sesiones. La skill actual sigue escribiendo en el temporal del SO; instalarla upstream sin cambiar el destino NO demuestra un handoff Codex ↔ Claude duradero. Esperar una solución comprobada o, si surge un caso real, probar un destino duradero explícito fuera de artefactos públicos. Mantener #593 independiente, sin instalar esto por arrastre. |
| [`wayfinder`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/wayfinder/SKILL.md) | **NO ADOPTAR AHORA** | Es el flujo más pesado del upstream y está pensado para trabajo multi-sesión cuyo camino aún no está claro. #585 ya tiene destino/frontier explícitos con mucha menos ceremonia; añadir mapas, child issues, labels y blocking edges sería duplicar planificación. |
| [`improve-codebase-architecture`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/improve-codebase-architecture/SKILL.md) | **NO AHORA** | El scope global es mayor que el objetivo actual de cambios pequeños y fáciles de revisar. |
| `resolving-merge-conflicts` | **NO ADOPTAR / RETIRADA UPSTREAM** | El upstream estable la eliminó en v1.3 porque la resolución de conflictos se considera responsabilidad del harness/agente. No conservar una skill archivada sin necesidad. |

## Preguntas que debe responder la investigación

- ¿Aporta capacidades que hoy no tenemos?
- ¿Reduce errores o trabajo manual?
- ¿Mejora revisión de código, testing, documentación o consistencia?
- ¿Puede integrarse sin ensuciar el contexto ni hacer más frágil el flujo?
- ¿Conviene copiar/adaptar una skill, usarla como referencia o no hacer nada?
- ¿Hay alguna idea que merezca convertirse en test, instrucción del repo o automatización?

## Criterio de cierre

Cerrar esta investigación con una de estas conclusiones:

- `ADOPT_SELECTED_SKILLS`
- `ADAPT_SELECTED_PATTERNS_ONLY`
- `NO_USEFUL_BENEFIT_FOUND`

Si se decide adoptar algo, hacerlo en una PR nueva y específica. Esta PR solo conserva la investigación pendiente.

## Auditoría del catálogo completo (8 de octubre de 2026)

Fuente verificada: [mattpocock/skills](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills), commit upstream `b0618bc436ad893b3c5e84e55fba86586d34a404` (2026-10-08). **38 directorios de skills**: 20 `engineering`, 7 `productivity`, 4 `misc` y 7 `in-progress`. `deprecated` solo contiene README. Licencia MIT comprobada. El upstream considera `in-progress` beta, sin garantía de estabilidad. Las 14 skills activas ya recogidas en la matriz anterior mantienen su decisión; `resolving-merge-conflicts` está retirada y no cuenta entre las 38.

### Resto del catálogo: decisión explícita por skill

| Skill | Decisión para web-escritor | Por qué / cuándo reabrir |
| --- | --- | --- |
| [engineering/ask-matt](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/ask-matt) | NO INSTALAR | Router de skills; esta investigación y su matriz ya resuelven qué invocar. |
| [engineering/codebase-design](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/codebase-design) | USO PUNTUAL | Aplicar vocabulario de interfaces y seams solo ante un refactor real de JS/QA, no reestructurar por disciplina abstracta. |
| [engineering/domain-modeling](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/domain-modeling) | USO PUNTUAL | Crear `GLOSSARY.md`/ADR solo ante ambigüedad de dominio o decisión difícil de revertir demostrada; no hay caso documentado ahora. |
| [engineering/grill-with-docs](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/grill-with-docs) | NO INSTALAR AHORA | Entrevista interactiva y documentación de dominio para decisiones abiertas; el flujo actual ya tiene alcance y criterios cerrados. |
| [engineering/implement-spec](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/implement-spec) | NO ADOPTAR | Branch de integración, subagentes y merges internos; sobrecoste y colisión con PR pequeñas independientes y control de merges del autor. |
| [engineering/setup-matt-pocock-skills](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/setup-matt-pocock-skills) | NO INSTALAR | Configura tracker, labels, glosarios y steering para el ecosistema completo; aquí no se adopta el ecosistema entero. |
| [engineering/to-tickets](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/to-tickets) | NO ADOPTAR AHORA | Descomposición con bloqueos/issue tracker; #577 y #585 ya coordinan PR pequeñas sin crear otra capa de tickets. |
| [productivity/grill-me](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/grill-me) | USO PUNTUAL | Router de entrevista: solo cuando haya decisiones no resueltas que requieran al autor. |
| [productivity/grilling](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/grilling) | USO PUNTUAL | Preguntas para un diseño realmente ambiguo, no en trabajos con requisitos ya verificados. |
| [productivity/teach](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/teach) | DESCARTAR PARA REPO | Genera un espacio didáctico y lecciones, no mejora el código ni la revisión actual. |
| [productivity/to-questionnaire](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/to-questionnaire) | USO PUNTUAL | Solo si una decisión necesita respuestas de terceros; no añadir plantillas de cuestionario sin destinatario real. |
| [productivity/wait-what](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/wait-what) | NO INSTALAR | Reformula explicaciones confusas; no justifica archivos permanentes en el proyecto. |
| [productivity/writing-for-agents](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/writing-for-agents) | USO PUNTUAL | Evaluado en comentario de #577 del 2026-10-08: `AGENTS.md`/`CLAUDE.md` no existen en `main`; evitar recrear #587 sin un problema concreto. |
| [misc/git-guardrails-claude-code](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/misc/git-guardrails-claude-code) | NO ADOPTAR TAL CUAL; PILOTO LIMITADO #617 | El upstream declara `misc/` **congelado/sin mantenimiento** en [su política explícita](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/.out-of-scope/frozen-misc-skills.md); los fallos concretos están en [#898](https://github.com/mattpocock/skills/issues/898) y [#1077](https://github.com/mattpocock/skills/issues/1077); el hook original puede fallar abierto. #617 es una adaptación local Python probada contra comandos habituales, **no una barrera de autorización** (solo Bash de Claude; wrappers/API/otros agentes fuera de garantía). No declarar lista hasta QA y análisis coste/mantenimiento. |
| [misc/migrate-to-shoehorn](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/misc/migrate-to-shoehorn) | NO APLICA | Migra assertions de tests TypeScript; el repo publica HTML/CSS/JS estático y `package.json` solo fija utilidades CI, sin TypeScript de app. |
| [misc/scaffold-exercises](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/misc/scaffold-exercises) | NO APLICA | Crea cursos/ejercicios con lint específico de AI Hero; no existe ese producto ni estructura. |
| [misc/setup-pre-commit](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/misc/setup-pre-commit) | NO ADOPTAR TAL CUAL | Instala Husky/Prettier, formatea staged files y presupone scripts `test`/`typecheck`; el `package.json` real no tiene esos scripts y el repo ya tiene Required merge gate. Evitar churn editorial/HTML. |
| [in-progress/chief-of-staff](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/chief-of-staff) | NO ADOPTAR (BETA) | Orquestación de subagentes y tareas de larga duración, innecesaria y no probada para este flujo. |
| [in-progress/claude-handoff](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/claude-handoff) | NO ADOPTAR (BETA) | Lanza `claude --bg`; además, el `handoff` estable no garantiza persistencia Codex ([#622](https://github.com/mattpocock/skills/issues/622)). No adoptar beta ni depender de #593 para resolver eso. |
| [in-progress/loop-me](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/loop-me) | NO APLICA (BETA) | Diseña workflows de rutinas personales, no resuelve un defecto de desarrollo actual. |
| [in-progress/setup-ts-deep-modules](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/setup-ts-deep-modules) | NO APLICA (BETA) | Exige arquitectura de paquetes TypeScript/dependency-cruiser ausente. |
| [in-progress/writing-beats](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/writing-beats) | USO PUNTUAL EDITORIAL (BETA) | Puede probarse sin instalar al planificar un artículo del Cuaderno, si hay material y decisión editorial concreta. No afecta al desarrollo/CI. |
| [in-progress/writing-fragments](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/writing-fragments) | USO PUNTUAL EDITORIAL (BETA) | Recoge material de artículos; no crear procesos nuevos hasta un caso de escritura real. |
| [in-progress/writing-shape](https://github.com/mattpocock/skills/tree/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/writing-shape) | USO PUNTUAL EDITORIAL (BETA) | Estructura artículos desde material previo; probar fuera de `main` solo si existe una petición de contenido. |

### Instalación y procedencia: resolución de la revisión #577/#593

La [guía upstream a este mismo commit](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/README.md#installation-30-second-setup) distingue **plugins autoactualizables** (Claude Code y Codex) de **copias editables con skills.sh y actualizaciones manuales**. Los plugins son adecuados para un usuario que quiere todo el paquete al día, pero no dan un snapshot **selectivo y versionado con este repositorio**: #593 pretende distribuir **solo** `pr` a ambos agentes con el mismo comportamiento por revisión de código. Esa ventaja tiene coste real: dos copias físicas requieren un contrato de paridad y actualización explícita. No dar por probado que un `skills-lock.json` lógico haya generado y mantenga ambos árboles. Las incidencias abiertas [skills.sh #781](https://github.com/vercel-labs/skills/issues/781) (saltos CRLF/LF) y [#806](https://github.com/vercel-labs/skills/issues/806) (hash sin verificación reproducible del instalado) impiden tratar `computedHash` como prueba de integridad.

Política evaluada: **copias de proyecto fijadas al upstream `b0618bc436ad893b3c5e84e55fba86586d34a404`, cambios solo mediante PR explícita, comparación de bytes/formatos y contrato determinista de paridad**. No instalar además el plugin global homónimo en la misma sesión, pues el [README upstream](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/README.md#installation-30-second-setup) avisa de duplicación. En #593 deben quedar documentadas y probadas por separado: 1) contenido de ambas copias; 2) comando/manual de sincronización; 3) activación real en sesión limpia Codex y Claude, que **no queda acreditada por CI web**. Hasta entonces **#593 no lista para merge**.

### Trazabilidad de la matriz

La fuente principal de cada decisión es el `SKILL.md` del enlace exacto en su fila, fijado a `b0618bc436ad893b3c5e84e55fba86586d34a404`; riesgos específicos se asocian a incidencias upstream enlazadas directamente. Las decisiones sin defecto reportado se basan en el propósito declarado de la skill y en la comparación con la estructura del proyecto (HTML/CSS/JS estático, `package.json` de QA y [Required merge gate](https://github.com/davidpd89/web-escritor/blob/main/.github/workflows/required-merge-gate.yml)), **no** en afirmar que se haya ejecutado una prueba por cada descarte. `38/38` significa **38 rutas inspeccionadas y clasificadas, no 38 ejecuciones end-to-end**.

### Veredicto de cobertura y siguiente paso

**Catálogo upstream revisado al 100 % en esta fecha (38/38 rutas actuales, incluidas beta).** Esto **no equivale** a declarar la investigación principal terminada: queda pendiente resolver/validar el handoff duradero en Codex (upstream #622), y cualquier comprobación específica que surja de cambios upstream posteriores. Solo se crea una PR hija cuando exista beneficio probado en el repositorio. Todas las PR siguen bajo control de merge del autor; no tocar la línea QA #585.



## Evidencia de lectura directa de las 38 skills (8 de octubre de 2026)

Fuente común: `mattpocock/skills@b0618bc436ad893b3c5e84e55fba86586d34a404`. Se han abierto los **38 archivos `SKILL.md`** asociados a la matriz anterior y cotejado el contenido introductorio, propósito e instrucciones de cada uno. Esta evidencia amplia la revisión documental: **no** acredita activación de 38 skills en agentes reales ni pruebas end-to-end. Los SHA de blob permiten detectar cambios independientes del nombre de la ruta.

| Ruta exacta de `SKILL.md` | SHA de blob Git |
| --- | --- |
| [`skills/engineering/pr/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/pr/SKILL.md) | `84dd4fb2f068e9f6282690235d20dd505b418119` |
| [`skills/engineering/code-review/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/code-review/SKILL.md) | `373a4f26e6cfa3617778397945bb069d9cb184bc` |
| [`skills/engineering/retro/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/retro/SKILL.md) | `12149acf2dd23b4514dec57b04a6293eaa1352fa` |
| [`skills/engineering/diagnosing-bugs/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/diagnosing-bugs/SKILL.md) | `d039541ddd1c46e6ddbd662fe99d49b686fc5e12` |
| [`skills/engineering/tdd/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/tdd/SKILL.md) | `01eadaa34e7c9a63a67d6dc3cce1cc81b0e49985` |
| [`skills/engineering/implement/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/implement/SKILL.md) | `bd49e472984c7b99aac40286fdae749bb955a842` |
| [`skills/engineering/to-spec/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/to-spec/SKILL.md) | `3f52599ae2a4347aee5a07432c2707518e691a7f` |
| [`skills/engineering/triage/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/triage/SKILL.md) | `3fd5617e906cf9b71a6b17424791adb905fc248b` |
| [`skills/engineering/setup-matt-pocock-skills/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/setup-matt-pocock-skills/SKILL.md) | `293c25b75590119794af03b037ba4288054a32b3` |
| [`skills/engineering/research/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/research/SKILL.md) | `fecee97e9457ba039678d2fcf1b1bc9fca78307d` |
| [`skills/engineering/prototype/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/prototype/SKILL.md) | `a0044501fe0d385b4d8575b610188ede9b236ccf` |
| [`skills/engineering/wizard/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/wizard/SKILL.md) | `c4294ad8298b9b95fc727496b1b802b1f7363fba` |
| [`skills/engineering/wayfinder/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/wayfinder/SKILL.md) | `e28cf3018906d6d60fc5b25390b4eeea035dd290` |
| [`skills/engineering/improve-codebase-architecture/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/improve-codebase-architecture/SKILL.md) | `44cc7d3136c44534d68ac523fa6cd37e759d2846` |
| [`skills/engineering/ask-matt/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/ask-matt/SKILL.md) | `4bfeeb61dae548b8b7754c4fba7bd40ab3926099` |
| [`skills/engineering/codebase-design/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/codebase-design/SKILL.md) | `3f63c8146dd2604b419c929e9876b90c30d410e9` |
| [`skills/engineering/domain-modeling/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/domain-modeling/SKILL.md) | `a4438c6879c517d1a08e2b5fbca049b632688dfe` |
| [`skills/engineering/grill-with-docs/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/grill-with-docs/SKILL.md) | `62b9efb6f991d1b229adee7506962f13ced0c499` |
| [`skills/engineering/implement-spec/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/implement-spec/SKILL.md) | `183923797ab58f1b3ef09e03bc1f1f203c309f37` |
| [`skills/engineering/to-tickets/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/to-tickets/SKILL.md) | `9b77a01db9460c99c22d03c910c349f890f12c0e` |
| [`skills/productivity/handoff/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/handoff/SKILL.md) | `a224edc643a20ddb989f9bca1547440169159810` |
| [`skills/productivity/grill-me/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/grill-me/SKILL.md) | `3947ff9c4ad980d14fc07fccbf659d47c114e81d` |
| [`skills/productivity/grilling/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/grilling/SKILL.md) | `df69d9936880cd3314c28858c6c52f48db23b856` |
| [`skills/productivity/teach/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/teach/SKILL.md) | `493fa3bae0dada971c4dfb965790e56920b1dced` |
| [`skills/productivity/to-questionnaire/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/to-questionnaire/SKILL.md) | `dadd0c00d6a350acaa15bb9ca1b96b20ead684ca` |
| [`skills/productivity/wait-what/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/wait-what/SKILL.md) | `9b15cd1a7dda0854ca093e29e3e0de57e241b2ac` |
| [`skills/productivity/writing-for-agents/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/productivity/writing-for-agents/SKILL.md) | `a37608daf6e835e767deecfb498facecaaba82ba` |
| [`skills/misc/git-guardrails-claude-code/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/misc/git-guardrails-claude-code/SKILL.md) | `58bcdd875b164093b95f436fa32a65c6cb5eb572` |
| [`skills/misc/migrate-to-shoehorn/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/misc/migrate-to-shoehorn/SKILL.md) | `ae4f965e204fc93cedbc4e2c306e92829d93f800` |
| [`skills/misc/scaffold-exercises/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/misc/scaffold-exercises/SKILL.md) | `d87df28e7d8abb4e57ecc6e47d71c274d16054c7` |
| [`skills/misc/setup-pre-commit/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/misc/setup-pre-commit/SKILL.md) | `1b9708168263067adb4684d06ebb8f4ccfe9682c` |
| [`skills/in-progress/chief-of-staff/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/chief-of-staff/SKILL.md) | `97da622d09acaaacebbb4482663c907e241f4594` |
| [`skills/in-progress/claude-handoff/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/claude-handoff/SKILL.md) | `77f82fc59c89c3a83ed5a92521dc2869f0533724` |
| [`skills/in-progress/loop-me/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/loop-me/SKILL.md) | `e58a474ca80feffdeb28842bc3bdee37da6510e7` |
| [`skills/in-progress/setup-ts-deep-modules/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/setup-ts-deep-modules/SKILL.md) | `7e30047eaeda175de5d93886596a37baf365bb90` |
| [`skills/in-progress/writing-beats/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/writing-beats/SKILL.md) | `3d3b25b605491adc5c62ae5423127717a94b9632` |
| [`skills/in-progress/writing-fragments/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/writing-fragments/SKILL.md) | `c7c889b880cf9c8d289119dea5ff240641b615ca` |
| [`skills/in-progress/writing-shape/SKILL.md`](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/in-progress/writing-shape/SKILL.md) | `02f2866d13e72504e010f2ad3458eb9b36b876db` |

### Decisión de implementación para web-escritor

- **PR ya existentes:** `pr` → #593 y adaptación local de `git-guardrails-claude-code` → #617. Son pilotos; no fusionar hasta evidencia funcional de runtime y CI del HEAD definitivo. La versión nueva de #617 se publicó usando `[skip ci]`, por lo que el CI anterior no valida sus últimos commits.
- **Uso sin instalar:** `code-review`, `diagnosing-bugs`, `tdd`, `codebase-design` y `writing-for-agents` se pueden aplicar puntualmente con el material upstream, cuando exista un caso concreto. **No** crear PR para una simple metodología de revisión.
- **Sin caso de integración ahora:** procesos de tracker/triage, arquitectura global, orquestación multisesión, cursos, andamiaje TS y skills beta editoriales. No se ha demostrado mejora suficiente para añadir dependencias o automatización.
- **Estimación de PR adicionales:** **0 obligatorias** para completar la revisión documental de este snapshot; **0–3 opcionales** condicionadas a encontrar en una prueba real un defecto o mejora que aún no cubran main/otras PR. Cada PR debe tener un único objetivo y evidencia before/after, no una obligación de instalar una skill.
- **Pendientes no sustituibles por lectura:** smoke real de la skill `pr` en Codex y Claude Code (#593); smoke real del hook Bash/Claude Code (#617); CI definitivo de #617; conclusión de las hijas y cierre de la auditoría #577.
- **Control de consumo:** mientras se priorice otro repositorio, los commits preparatorios usarán `[skip ci]`. GitHub indica que los checks requeridos saltados pueden permanecer pendientes: antes de integrar se necesitará un commit final **sin** ese marcador y el CI completo. No activar `workflow_dispatch` ni hacer merges.
