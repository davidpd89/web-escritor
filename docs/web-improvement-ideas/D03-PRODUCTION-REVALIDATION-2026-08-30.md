# D.3 · Revalidación de producción — progreso de lectura

Fecha: 2026-08-30  
Base comprobada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.

## Veredicto

**IMPLEMENTED_IN_PR · EXISTING_OPT_IN_PRESERVED · SHORT_RETIRED_STUB_FIXED · REGRESSION_GUARD_ADDED**

La capacidad ya existía y estaba correctamente diseñada como opt-in. La auditoría sí encontró una anomalía concreta: la página retirada `cuaderno/sistema-de-magia-noveris/` seguía montando progreso pese a declarar `1 min de lectura` y contener únicamente una nota de retirada, un párrafo de orientación y enlaces relacionados.

La PR corrige exclusivamente ese scoping; no rehace el componente.

## 1. Runtime existente preservado

`script.js` sigue gobernando la feature con:

```js
if (!document.body.hasAttribute("data-reading-progress")) return;
```

El componente:

- se crea solo en páginas que optan explícitamente;
- usa listener de scroll pasivo;
- difiere trabajo mediante `scheduleTask`;
- no introduce dependencia;
- usa `aria-hidden="true"` para no anunciar porcentajes continuamente a tecnologías de asistencia.

No se ha cambiado este runtime.

## 2. Auditoría directa de superficies

La inspección directa confirma `data-reading-progress` en long-form real:

- `/fragmento/`;
- `/las-manecillas-del-recuerdo/fragmentos/`;
- Feria del Libro de Madrid 2026;
- `que-es-el-portal-fantasy`;
- `portal-fantasy-vs-fantasia-epica`;
- `fantasia-juvenil-espanola-portales-magia-coste`;
- `libros-fantasia-juvenil-espanola-2025-2026`;
- `worldbuilding-noveris-ciudad-magica`.

Ese montaje selectivo se conserva.

## 3. Anomalía corregida

`/cuaderno/sistema-de-magia-noveris/` está actualmente en estado editorial retirado:

- `noindex`;
- H1 `Contenido temporalmente retirado`;
- `1 min de lectura`;
- una nota que explica la retirada;
- un párrafo que redirige a superficies canónicas publicadas.

Aun así tenía:

```html
<body data-reading-progress data-back-to-top>
```

Eso contradecía el propio contrato de D.3: una señal continua de progreso no aporta valor en una superficie corta que ni siquiera ofrece el artículo original.

Se cambia únicamente a:

```html
<body data-back-to-top>
```

No se toca el contenido, metadata, estado `noindex`, enlaces, newsletter, layout ni `data-back-to-top` porque quedan fuera del alcance de D.3.

## 4. Guardia de regresión

Se añade `tests/test-reading-progress-scoping.py`.

El Required merge gate ejecuta automáticamente `tests/test-*.py`, por lo que el contrato pasa a ser obligatorio en cada PR:

- `script.js` debe mantener el opt-in;
- las ocho superficies long-form conocidas deben conservar `data-reading-progress`;
- el stub retirado no debe recuperarlo por regeneración accidental.

La prueba no convierte la lista en una política universal para toda futura página: nuevas superficies se incorporan cuando exista una decisión editorial concreta.

## 5. Falso negativo de code search

Durante esta revalidación GitHub code search devolvió `total_count: 0` para `data-reading-progress`, incluso cuando la inspección directa de `script.js` y de los HTML demostraba lo contrario.

Esto vuelve a confirmar la regla del proyecto: **no usar code search como prueba suficiente de ausencia**. Los veredictos de D.3 se basan en archivos directos.

## 6. Qué no se ha hecho

- segunda barra;
- cambio visual del componente;
- nueva animación;
- tracking de scroll;
- `aria-live` porcentual;
- expansión a páginas cortas;
- modificación del texto literario/editorial.

## Decisión final

D.3 deja de ser una auditoría abstracta: la capacidad existente queda preservada y el único desajuste reproducible encontrado queda corregido y protegido por test.

**Estado final: `IMPLEMENTED_IN_PR · EXISTING_OPT_IN_PRESERVED · SHORT_RETIRED_STUB_FIXED · REGRESSION_GUARD_ADDED`.**
