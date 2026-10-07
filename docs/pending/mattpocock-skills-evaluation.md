# Pendiente futuro: evaluar mattpocock/skills

> Estado: **PENDIENTE · INVESTIGACIÓN FUTURA · NO IMPLEMENTAR NI MERGEAR AHORA**

## Recurso

Repositorio a revisar:

https://github.com/mattpocock/skills

Página explicativa / catálogo de skills:

https://www.aihero.dev/skills

## Objetivo

Investigar en el futuro si alguna de las skills, patrones, instrucciones o formas de trabajo de ese repositorio puede mejorar el desarrollo, mantenimiento, QA o automatización de `web-escritor`.

No se presupone que deba instalarse ni copiarse nada. Primero hay que entender qué contiene, cómo funciona y qué encaja de verdad con este proyecto.

## Investigación futura

Cuando se retome:

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

## Principio multiagente acordado

La integración no debe quedar atada a un único proveedor de IA:

- reglas duraderas del proyecto: fuente canónica y neutral;
- Codex/agentes compatibles: `AGENTS.md` y skills en `.agents/skills/`;
- Claude Code: `CLAUDE.md` y, cuando aporte descubrimiento nativo, adaptadores mínimos en `.claude/skills/`;
- los adaptadores no deben copiar la lógica de una skill: deben apuntar a la fuente canónica;
- no cargar todas las skills por defecto; solo la que encaja con la tarea;
- cualquier nueva integración debe entrar en una PR pequeña, reversible y con beneficio comprobable.

Esto permite que Codex, Claude u otro agente trabajen con el mismo contrato sin mantener instrucciones divergentes.

## Preguntas que debe responder la investigación

- ¿Aporta capacidades que hoy no tenemos?
- ¿Reduce errores o trabajo manual?
- ¿Mejora revisión de código, testing, documentación o consistencia?
- ¿Puede integrarse sin ensuciar el contexto ni hacer más frágil el flujo?
- ¿Conviene copiar/adaptar una skill, usarla como referencia o no hacer nada?
- ¿Hay alguna idea que merezca convertirse en test, instrucción del repo o automatización?

## Criterio de cierre futuro

Cerrar esta investigación con una de estas conclusiones:

- `ADOPT_SELECTED_SKILLS`
- `ADAPT_SELECTED_PATTERNS_ONLY`
- `NO_USEFUL_BENEFIT_FOUND`

Si se decide adoptar algo, hacerlo en una PR nueva y específica. Esta PR solo conserva la investigación pendiente.
