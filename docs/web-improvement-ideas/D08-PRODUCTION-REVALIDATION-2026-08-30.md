# D.8 · Revalidación de producción — modo oscuro manual

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **DEFER · SINGLE_VISUAL_SYSTEM_INTENTIONAL · NO_MANUAL_THEME_OWNER · NO_CODE**.

## 1. Resultado

D.8 sigue siendo una mejora aplazada, no una deuda. El sistema visual actual tiene tokens semánticos y territorios oscuros localizados, pero no un segundo tema global ni un owner de preferencia manual persistente.

Añadir un toggle ahora obligaría a mantener otro estado visual completo sin evidencia de necesidad.

## 2. Evidencia directa del sistema de tokens

`assets/v1-tokens.css` define una autoridad única de superficies, texto, bordes, acentos, foco y tipografía.

El propio fichero documenta que V1-B puede usar un territorio `Ink` oscuro en secciones concretas, pero especifica expresamente:

> `This is NOT a global dark-mode switch`

La oscuridad localizada de un hero/territorio forma parte de la composición de marca; no es un tema de usuario.

## 3. Base accesible actual

`assets/v1-base.css` ya contiene reglas de foco, reflow/rotura de texto y `prefers-reduced-motion` para la experiencia base.

No se ha localizado en la autoridad inspeccionada un selector manual `system/light/dark`, un almacenamiento persistente de tema o una segunda matriz completa de tokens/componentes.

Eso no implica que falte una feature necesaria. Es coherente con la decisión histórica de mantener un único sistema visual mientras se estabiliza la identidad.

## 4. Dark mode no sustituye otras preferencias

No usar un tema oscuro como argumento genérico de accesibilidad. Contraste, forced-colors, zoom, foco y reduced motion son problemas distintos y deben resolverse en sus respectivos contratos.

D.8 solo se refiere a una **preferencia de apariencia** adicional que el usuario podría forzar.

## 5. Coste real de reapertura

Un modo manual exigiría probar al menos:

- todos los tokens semánticos;
- texto, fondos y bordes;
- focus/hover/disabled/error;
- formularios;
- Explorar y asistente;
- portadas, fotos e ilustraciones;
- logos/iconos;
- tablas y herramientas;
- impresión;
- móvil/desktop;
- contraste en ambos temas;
- arranque sin flash de tema incorrecto;
- sincronización `SYSTEM/LIGHT/DARK`;
- persistencia y varias pestañas.

No es razonable introducir esa matriz solo por tendencia de diseño.

## 6. Gate de reapertura

```text
repeated user demand
AND visual system/tokens stable
AND semantic token coverage sufficient
AND QA capacity for both themes
AND no brand/readability regressions
```

Si se reabre, el modelo preferible es de tres estados:

```text
SYSTEM
LIGHT
DARK
```

no un booleano que impida volver a la preferencia del sistema.

## 7. Qué no hacer

- no duplicar hojas CSS enteras;
- no usar `filter: invert()` global;
- no introducir `localStorage` sin owner de preferencia;
- no añadir JS inline que complique CSP;
- no confundir territorio visual oscuro con modo oscuro;
- no vender dark mode como solución universal de accesibilidad;
- no empaquetarlo con Reader Mode o controles de texto.

## 8. Definition of Done

- [x] tokens actuales inspeccionados;
- [x] territorio oscuro localizado distinguido de un tema global;
- [x] ausencia de owner manual confirmada en la arquitectura inspeccionada;
- [x] coste de estados preservado;
- [x] gate futuro definido;
- [x] sin implementación prematura.

## Estado para Claude

Mantener D.8 en `DEFER`. El sistema visual único es deliberado. Reabrir un selector `system/light/dark` solo con demanda real y cuando la cobertura de tokens/QA haga sostenible mantener dos apariencias completas.