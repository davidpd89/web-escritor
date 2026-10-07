# Pendiente futuro: evaluar migración local a WordPress con Docker

> Estado: **PENDIENTE · INVESTIGACIÓN FUTURA · NO IMPLEMENTAR NI MERGEAR AHORA**

## Idea de partida

Para una futura revisión de arquitectura, valorar una prueba aislada de migración de la web actual a WordPress utilizando Docker Desktop y una instalación local/contenedorizada de WordPress.

La idea original a conservar es:

> "Para la próxima, si quieres probar a migrar a WordPress, instálate Docker Desktop, te instalas una imagen de WordPress (o del que quieras) y le dices a la IA que te haga una migración de lo que tienes, manteniendo el diseño y demás."

## Objetivo de la prueba

Comprobar, sin comprometer la web actual, si WordPress aporta alguna ventaja real frente a la arquitectura existente en:

- mantenimiento y edición de contenido;
- experiencia de publicación;
- SEO técnico;
- rendimiento/Core Web Vitals;
- accesibilidad;
- seguridad y actualizaciones;
- coste operativo;
- automatización con IA/Codex/Claude;
- facilidad para conservar el diseño actual;
- compatibilidad con las funcionalidades y tests existentes.

## Cómo probarlo en el futuro

1. Revisar primero el estado real de `main` y documentar la arquitectura actual.
2. Instalar Docker Desktop en el equipo de pruebas.
3. Levantar una instancia **local** de WordPress mediante contenedores, sin tocar producción.
4. Preparar una copia/migración experimental de la web actual.
5. Intentar conservar con fidelidad:
   - diseño visual;
   - tipografías;
   - estructura de navegación;
   - URLs y canónicos;
   - metadatos/structured data;
   - contenido;
   - responsive;
   - accesibilidad;
   - comportamiento de formularios y componentes.
6. Comparar la versión migrada contra la web actual con los mismos tests y auditorías.
7. Medir qué cosas se simplifican y cuáles empeoran.
8. Decidir con evidencia: **MIGRAR / NO MIGRAR / MIGRAR SOLO PARTE**.

## Condiciones

- No sustituir la web actual durante la investigación.
- No perder URLs, SEO, contenido ni diseño por una migración "aproximada".
- No asumir que WordPress es mejor por defecto.
- No asumir que la arquitectura actual es mejor por defecto.
- No convertir esta PR en una migración real sin una decisión explícita posterior.
- Si se prueba otro CMS además de WordPress, documentarlo por separado y comparar en igualdad de condiciones.

## Criterio de cierre futuro

Esta PR puede cerrarse cuando exista una prueba reproducible y una conclusión documentada:

- `WORDPRESS_MIGRATION_BENEFICIAL`
- `WORDPRESS_MIGRATION_NOT_BENEFICIAL`
- `PARTIAL_MIGRATION_WORTH_TESTING`

Hasta entonces debe permanecer como recordatorio de investigación.
