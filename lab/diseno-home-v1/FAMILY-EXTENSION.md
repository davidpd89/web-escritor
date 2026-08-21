# V1 — EXTENSIÓN DE FAMILIAS + HANDOFF CLAUDE

Este directorio completa el paquete `37 — LAB HOME V1 — CÓDIGO LISTO PARA INTEGRAR` con las familias que no deben resolverse improvisando componentes genéricos.

Estado tras validación: consultar `CLAUDE-HANDOFF.md`.
Rama objetivo: `implementacion-web-2026`.
Baseline auditado: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.
`main`: no tocar.

## Qué contiene

- scaffolds noindex de las familias V1;
- Samuel con composición propia de umbral;
- Premios como archivo cronológico, separado de Prensa;
- catálogo de 17 herramientas como instrumentarium tipográfico;
- familias de Autor, Eventos/Ferias, Libros, Cuaderno, referencias, companions, fragmentos, wayfinding y secundarias;
- firmas editoriales reutilizables;
- inventario de 55 rutas del sitemap + 3 operativas fuera de sitemap + Jaula autorizada para staging aún fuera de sitemap;
- contratos de preservación para Samuel y Premios;
- referencias humanas y APIs nativas que justifican decisiones;
- validador estático de cobertura y anti-patrones genéricos.

## Regla de implementación

Estos HTML no sustituyen el contenido de producción. Son **scaffolds de composición**. Claude debe transplantar desde cada ruta real todo lo que el contrato marque como preservado: head, schema, anchors, texto indexable, enlaces, formularios, hooks y comportamiento.

La capa V1 se monta namespaced y convive inicialmente con legacy. No se sustituye `styles.css` ni `script.js` de forma global hasta demostrar paridad.

## Definición de «listo para Claude»

1. ninguna ruta pública del sitemap queda sin familia/scaffold;
2. Samuel y Premios tienen composición propia;
3. Jaula dispone de scaffold/contrato real, pero no genera enlace público falso hasta que la ruta exista y pase el gate;
4. las 17 herramientas conservan builder/hooks/algoritmos y cambian solo su sistema de presentación;
5. no hay `card`, `badge`, `pill`, bento, glass, blur, gradientes decorativos o librerías de motion globales en la extensión;
6. no hay dependencia de JS/motion/media para entender o navegar;
7. el HEAD está anclado y existe política explícita de drift;
8. el QA visual real sigue pendiente de staging.

## No confundir estados

`CLAUDE_IMPLEMENT_READY` permite implementar en staging.
`MERGE_READY` exige QA real de navegador, responsive, teclado, no-JS, reduced-motion, schema, enlaces, CWV y benchmark visual.
`PRODUCTION_READY` además exige autorización explícita.
