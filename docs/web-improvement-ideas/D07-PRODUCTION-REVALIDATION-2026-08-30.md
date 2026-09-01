# D.7 · Revalidación de producción — hover previews

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **REJECT · EXPLORE_PREVIEW_IS_ACCESSIBLE_AUXILIARY · NO_HOVER_LISTING_LAYER · NO_CODE**.

## 1. Resultado

El patrón rechazado en D.7 —mostrar información esencial o una ficha enriquecida únicamente al pasar el cursor por listados— no debe incorporarse.

El preview existente dentro de `Explorar` no contradice ese rechazo: es auxiliar, vive dentro de un diálogo explícito y mantiene la navegación principal como enlaces reales.

## 2. Inspección directa de `assets/v1-shell.js`

El diálogo `Explorar` mantiene filas enlazables con `href` real. El preview lateral se actualiza mediante:

```js
link.addEventListener('mouseenter', ...)
link.addEventListener('focus', ...)
```

Es decir, la información auxiliar tiene equivalencia de mouse/foco y no sustituye el destino del enlace.

Además el diálogo gestiona:

- apertura/cierre explícitos;
- `aria-expanded`;
- foco inicial;
- ciclo de Tab dentro del diálogo;
- Escape/cancel;
- restauración de foco al opener;
- navegación mediante enlaces normales.

## 3. Por qué esto no rehabilita D.7

D.7 proponía previews añadidos a libros/recomendaciones/listados para evitar navegar.

El patrón real de `Explorar` es distinto:

```text
navegación explícita
+ preview auxiliar no esencial
+ enlace directo siempre disponible
```

No:

```text
hover sobre card/listado
→ contenido necesario oculto
→ segunda interacción para touch/keyboard
```

No hay motivo para extender el preview de `Explorar` a otras familias solo por consistencia visual.

## 4. Touch/móvil

En touch, el usuario puede activar directamente el enlace. No se exige un primer tap para abrir una preview y un segundo tap para navegar.

Eso preserva la regla más importante de D.7: la acción principal no debe depender del hover ni complicarse para dispositivos sin hover persistente.

## 5. Gate extraordinario

Solo reabrir un preview enriquecido en listados si aparece un problema comparativo real:

- listado mucho más denso;
- usuarios necesitan comparar sin perder contexto;
- la información no cabe de forma visible razonable;
- solución equivalente en mouse, teclado y touch;
- no carga media pesada innecesariamente;
- testing demuestra menos fricción.

## 6. Qué no hacer

- no añadir hover cards globales;
- no duplicar fichas enteras en DOM oculto;
- no cargar portadas high-res al hover;
- no convertir tap en dos pasos;
- no introducir overlays/tooltips con sinopsis largas;
- no copiar el panel de `Explorar` a cada listado;
- no usar el patrón como adorno para parecer más «premium».

## 7. Definition of Done

- [x] runtime real de `Explorar` inspeccionado;
- [x] equivalencia `mouseenter` + `focus` verificada;
- [x] enlaces reales preservados como acción primaria;
- [x] preview existente diferenciado del patrón rechazado;
- [x] sin nueva capa hover ni código.

## Estado para Claude

Mantener D.7 rechazada para listados. El preview de `Explorar` es una excepción deliberada y accesible como señal auxiliar; no convertirlo en patrón sitewide.