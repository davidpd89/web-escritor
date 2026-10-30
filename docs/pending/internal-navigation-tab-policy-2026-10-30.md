# Propuesta UX: política coherente de pestañas para navegación interna

Estado: **BORRADOR, PROPUESTA SIN IMPLEMENTAR**. P2 de recorrido del catálogo.
Base: `f4a2ea43f` (30/10/2026).

## Evidencia y alcance

Inspección de producción con Chromium y service workers bloqueados, sobre
`main a[href]`, clasificando mismo origen y atributo target:

| Ruta | Enlaces internos | Con target=_blank |
|---|---:|---:|
| `/recomendaciones/` | 665 | 358 |
| `/recomendaciones/autores/neil-gaiman/` | 15 | 1 |
| `/herramientas/` | 47 | 0 |

El recuento incluye elementos ocultos por paginación/filtros: NO son 358 enlaces
simultáneamente visibles. Enlaces típicos afectados: portada, título y Ver ficha
de una tarjeta, perfil del autor y libros relacionados. Se abre otra pestaña
para continuar explorando contenido del mismo sitio; en Herramientas no ocurre.

`scripts/build-reading-catalogue.py`, `newtab()`, documenta explícitamente esta
política y transforma enlaces internos del contenido. `author_links()`,
`related_books()` y listados de autor/editorial también emiten target=_blank.
Por tanto, **no es un bug accidental** ni un incumplimiento WCAG automático.
La propuesta revisa una decisión de diseño existente: conservar el catálogo
puede ser útil, pero forzar pestañas en cada salto también fragmenta el recorrido.

## Encargo a la IA implementadora

1. Verificar el motivo/requisito de producto de la política antes de revertirla.
   Si el titular confirma que quiere conservarla, documentar decisión y mejorar
   coherencia/avisos en lugar de cambiar el comportamiento unilateralmente.
2. Evaluar dos recorridos móviles: catálogo filtrado -> ficha -> autor -> otra ficha,
   y retorno a resultados. Medir pestañas y preservación de filtros/posición.
3. Proponer misma pestaña como comportamiento previsible de exploración interna,
   con retorno al catálogo que conserve contexto; o justificar alternativa explícita.
4. No mezclar compra externa, descargas y enlaces internos: cada uno tiene
   requisitos distintos. Mantener rel de seguridad y afiliación donde corresponde.
5. Si se cambia, corregir constructores y expectativas de tests, no HTML a mano;
   coordinar con #1001 (URL) y #1004 (experiencia móvil), sin duplicar sus alcances.

## Aceptación y pruebas

- [ ] Decisión de producto explícita con motivo de la política actual y propuesta.
- [ ] Evidencia antes/después del recorrido completo en móvil/escritorio.
- [ ] No acumular pestañas involuntarias para exploración interna habitual.
- [ ] Ctrl/Cmd-click, teclado y apertura voluntaria en otra pestaña siguen disponibles.
- [ ] Volver conserva filtros y ubicación de resultados o ofrece mecanismo claro.
- [ ] Enlaces que sí abren fuera lo comunican coherentemente, sin iconos engañosos.
- [ ] Sin regresiones de compras, descargas, rel, sitemap y funcionamiento sin JS.
- [ ] Pruebas de navegación real, generadores, versiones/artefactos y CI.
- [ ] Publicación y SHA comprobados si se aprueba e implementa el cambio.

No hay medición de abandono o conversiones: no atribuir pérdidas comerciales ni
mejoras SEO al target por sí solo. Es una propuesta de consistencia y navegación.
Otra IA continúa aquí con evaluación, diseño y eventual implementación. No
fusionar el documento como si cambiara la experiencia ni ejecutar cambios sin
resolver el requisito explícito de producto existente.