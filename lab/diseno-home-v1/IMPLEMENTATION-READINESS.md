# IMPLEMENTATION READINESS — V1

Estado: **LISTO PARA IMPLEMENTACIÓN EN STAGING POR CLAUDE; NO LISTO PARA MERGE/PRODUCCIÓN**.

Baseline auditado: `implementacion-web-2026@5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

Este estado significa que las familias publicables ya no dependen de que el implementador invente composición. Sigue faltando la evidencia que solo existe tras montar staging: capturas reales, elección Home A/B, responsive real, teclado, no-JS, reduced-motion, schema/links y rendimiento.

## Semáforo actual

| Área | Estado de diseño/código | Puede Claude materializarla sin diseñar | Gate posterior |
|---|---|---:|---|
| Tokens / base / shell / Explorar | IMPLEMENT_READY | Sí | navegador + accesibilidad |
| Home V1-A / V1-B | IMPLEMENT_READY_AB | Sí | elegir UNA variante tras QA; nunca mezclar |
| Libro / Manecillas | IMPLEMENT_READY | Sí | visual + retailers + schema/paridad |
| Libro / Samuel | IMPLEMENT_READY | Sí | `samuel-preservation.json` + quiz/reviews/retailers |
| Libros / índice | IMPLEMENT_READY | Sí | browser gate |
| Cuaderno / índice | IMPLEMENT_READY | Sí | CollectionPage/RSS/rutas |
| Artículo / lectura | IMPLEMENT_READY | Sí | cuerpo completo + FAQ visible/schema |
| Autor | IMPLEMENT_READY | Sí | browser gate + contenido completo |
| Prensa | IMPLEMENT_READY | Sí | archivos/copias/links reales |
| Premios | IMPLEMENT_READY | Sí | separación premio/selección/trayectoria |
| Eventos / Ferias | IMPLEMENT_READY | Sí | vacío/abundante + fechas |
| Herramientas / hub | IMPLEMENT_READY | Sí | 17 utilidades + builder contract |
| Herramienta piloto/propagación | IMPLEMENT_READY | Sí | algoritmos/hooks/privacidad/paridad |
| Reference index/detail | IMPLEMENT_READY | Sí | contenido/rutas reales |
| Companions / fragmentos / Noveris | IMPLEMENT_READY | Sí | preservar funciones y texto |
| Wayfinding / Empieza aquí / Mapa | IMPLEMENT_READY | Sí | navegación y móvil |
| 404 / Privacidad / Aviso legal / AI | IMPLEMENT_READY | Sí | robots/semántica legal |
| Jaula | IMPLEMENT_READY / AUTHORIZED_FOR_STAGING | Sí | crear ruta + capítulo fuente + SEO/schema + navegación; producción sigue bloqueada |
| Motion transversal | ENHANCEMENT_READY | Sí, solo tras estático | reduced-motion/no-JS |
| View Transition semántica | ENHANCEMENT_READY | Sí | Home ganadora + navegador real |
| Capturas / benchmark premio | BLOCKED_BY_STAGING | No | revisión humana |

## Cobertura

- 55/55 rutas de `sitemap.xml` tienen familia y scaffold.
- `/404.html`, `/privacidad.html` y `/aviso-legal.html` están cubiertas fuera de sitemap.
- `/donde-empieza-la-jaula/` tiene `book-jaula.html` + `jaula-preservation.json`; todavía no existe en la rama pública y permanece fuera de sitemap hasta pasar staging.
- Samuel y Premios tienen familias propias; no reutilizan Manecillas/Prensa por comodidad.
- Herramientas conserva las 17 utilidades actuales y el contrato de generación: si una salida depende de `scripts/build-writer-tools.py` o de otro builder, el cambio se hace en la fuente autoritativa y se regenera.

## Qué puede hacer Claude ahora

1. comprobar drift contra el HEAD auditado;
2. montar el lab V1 en `implementacion-web-2026`/staging;
3. implementar familia por familia siguiendo los scaffolds y contratos de preservación;
4. ejecutar los validadores estáticos y los checks propios del repo;
5. producir evidencia visual/técnica por ruta;
6. devolver FAIL cuando no exista evidencia suficiente.

## Qué NO puede decidir Claude

- no elegir o mezclar Home A/B sin capturas y evaluación;
- no cambiar la dirección «Cartografía editorial viva»;
- no convertir bloques en tiles/cards por conveniencia;
- no inventar paleta, lore, textos, premios, reviews, retailers o assets;
- no introducir glass/gradientes/glow/dark-mode como identidad;
- no añadir GSAP/Lenis/Three/WebGL global para «hacerla premium»;
- no publicar ni enlazar Jaula en producción hasta que la nueva ruta pase staging, SEO/schema y cobertura de navegación; sí puede materializarse ya en staging desde el scaffold autorizado;
- no borrar SEO/schema/anchors o funcionalidad legacy sin equivalente probado;
- no tocar `main`, mergear ni desplegar producción.

## Gates que impiden `MERGE_READY`

1. Home: ganador A/B decidido con capturas reales.
2. 320/390/768/1024/1440/1728 + landscape real.
3. teclado/focus/dialog/formularios.
4. 200% zoom + text spacing.
5. no-JS y reduced-motion completos.
6. contenido largo, extremo, escaso, sin media y font fallback.
7. schema/canonical/OG/links/paridad funcional.
8. builders/CI del repo sin drift.
9. Lighthouse/CWV y a11y del staging.
10. benchmark 28: ≥88/100 y áreas críticas ≥8/10; ≥92 para candidatura interna.

## Definition of implementation-ready global

Cumplida para **iniciar la implementación en staging** cuando `scripts/validate_lab.py` y `scripts/validate_extension.py` pasan sobre el paquete ensamblado. Los validadores de preservación no pueden pasar por anticipado: se ejecutan contra los HTML candidatos una vez materializados y son obligatorios antes de aceptar esa familia. Esto no equivale a `MERGE_READY`.

La siguiente fase no es «seguir inspirando a Claude». Es **hacer que Claude materialice exactamente este sistema y medirlo en navegador** cuando se autorice la escritura en la rama.
