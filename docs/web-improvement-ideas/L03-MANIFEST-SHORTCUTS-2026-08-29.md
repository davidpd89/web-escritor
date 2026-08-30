# L.3 · Atajos PWA en `manifest.json`

Fecha de reconstrucción: 2026-08-29  
Revalidación: 2026-08-30  
Fuente histórica primaria: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `ALREADY_COVERED`.

## Veredicto

**`IMPLEMENTED_IN_PR · CANONICAL_SHORTCUT_CONTRACT · EXISTING_PWA_QA_OWNER · ENFORCEMENT_ACTIVE_IN_PR`.**

La funcionalidad L.3 ya estaba materialmente implementada en `main`: `manifest.json` publica cuatro shortcuts reales. La revalidación detectó, sin embargo, un hueco de regresión pequeño y concreto: el QA existente validaba los shortcuts presentes, pero no obligaba a que el conjunto canónico siguiera existiendo. Eliminar accidentalmente `shortcuts` podía dejar pasar esa parte del contrato.

La PR no crea otro manifest ni otro sistema de quick actions. Endurece el owner PWA ya existente con un contrato determinista del conjunto canónico.

## Hipótesis original

Añadir shortcuts desde el icono instalado hacia destinos frecuentes como Cuaderno, Novedades o Club de lectura.

## Evolución histórica

### Revisión inicial → `ALREADY_COVERED`

La revisión ya localizó shortcuts en el manifest y recomendó mantenerlos.

### Matriz intermedia → `PILOTAR BAJO COSTE`

La matriz formuló temporalmente la idea como un posible piloto de shortcuts hacia Obras/Cuaderno/Herramientas si el soporte y la UX lo justificaban.

### Inspección profunda / autoridad final → `ALREADY_COVERED`

El cross-check del repositorio confirmó que el manifest ya publica shortcuts reales. La autoridad final cerró:

> «`manifest.json` ya contiene shortcuts. Mantener; soporte no universal.»

## Estado actual de `main`

Revalidado sobre `main@291c8c677aaa7df635142687d1a6848e80ffcaa2` (tree `68d02e1fe8ac2cfa239f4a716929e992abb672fd`).

`manifest.json` declara cuatro shortcuts:

1. **Las manecillas del recuerdo** → `/las-manecillas-del-recuerdo/`
2. **Todos los libros** → `/libros/`
3. **Cuaderno** → `/cuaderno/`
4. **Kit de prensa** → `/prensa.html`

Cada entrada incluye `name`, `short_name`, `url` y `description`.

La funcionalidad estaba cubierta, pero la permanencia del conjunto no estaba cerrada por un gate explícito.

## Owner QA existente

El repositorio ya dispone de un owner PWA específico:

- `.github/workflows/pwa-offline-qa.yml`
- `qa/pwa-offline.mjs`
- `qa/pwa-cache-freshness-contract.mjs`

`qa/pwa-offline.mjs` comprueba installability y que los shortcuts presentes tengan destinos válidos. Ese comportamiento debe conservarse; no se crea un harness paralelo.

## Gap de regresión localizado

La validación iteraba `manifest.shortcuts`, pero no fijaba el conjunto esperado. Si un cambio eliminaba toda la propiedad `shortcuts`, no quedaba una aserción dedicada que expresase que los cuatro accesos actuales forman parte del contrato PWA.

Ese es el único cambio de implementación de L.3.

## Implementación en esta PR

Se añade `qa/pwa-shortcuts-contract.mjs` y se integra en `.github/workflows/pwa-offline-qa.yml`.

El contrato exige:

- `manifest.shortcuts` como array;
- exactamente cuatro shortcuts canónicos;
- URLs únicas;
- destinos exactos actuales;
- `name`, `short_name`, `url` y `description` no vacíos;
- URLs internas/root-relative;
- inexistencia de URLs protocol-relative;
- existencia física de cada destino en el repositorio.

La prueba se ejecuta dentro del workflow PWA existente, antes del QA de navegador.

## Evidencia de CI

En el HEAD `6ce88674026abdb75edb7c5fe05971f9d925b0fb`, el run de **PWA offline QA** terminó en `success`, incluyendo el nuevo contrato de shortcuts. Required merge gate, Pa11y, content indexes, CSP public shell, runtime scoping, analytics y artefactos públicos también han completado correctamente. Sitewide Reflow seguía ejecutándose en la última comprobación y debe revalidarse antes de cerrar el bloque.

## Qué significa ahora el contrato

- no crear otro manifest;
- no duplicar shortcuts con JS;
- no abrir un sistema propio de «quick actions»;
- mantener el conjunto canónico mientras siga siendo decisión de producto;
- cambiar el contrato y el manifest juntos si una prioridad estable cambia;
- no hacer que los shortcuts sean navegación esencial.

## Soporte y arquitectura

Los shortcuts del Web App Manifest dependen del navegador/SO. Por eso:

- nunca deben ser la única forma de llegar a una sección;
- la navegación HTML principal sigue siendo autoridad;
- no deben esconder funcionalidades esenciales;
- el sitio debe funcionar exactamente igual sin instalación PWA.

## Cuándo revisar la selección

Reevaluar solo cuando cambie una prioridad editorial real, por ejemplo:

- una obra principal sustituye a otra;
- una URL deja de ser canónica;
- aparece una función recurrente claramente más útil;
- testing de PWA demuestra que un shortcut actual no aporta.

No rotarlos por campañas de pocos días si eso degrada estabilidad.

## Criterios de un buen shortcut

- destino estable;
- tarea frecuente;
- etiqueta corta comprensible;
- URL pública/canónica;
- no requiere sesión/estado;
- aporta incluso sin contexto previo.

## Relación con L.1/L.2/L.4

Los shortcuts no implican Push, Badging ni offline-first. Son una capacidad independiente cuya funcionalidad ya existía y cuya regresión queda ahora explicitada en QA.

## Qué NO hacer

- añadir shortcut por cada sección;
- usar enlaces externos como shortcut principal sin razón;
- depender de ellos para tareas esenciales;
- crear iconos nuevos solo por completar checklist;
- cambiar el manifest en cada campaña;
- confundir shortcuts con enlaces del header/footer;
- crear un segundo workflow PWA para comprobar lo mismo.

## Trazabilidad preservada

- hipótesis original;
- revisión que localiza implementación;
- matriz `PILOTAR BAJO COSTE`;
- override profundo de repo;
- autoridad final `ALREADY_COVERED`;
- manifest actual con cuatro shortcuts;
- gap de regresión localizado;
- contrato determinista añadido al owner QA existente.

## Recomendación para Clara/Claude

**No añadir nuevos shortcuts por L.3.** Mantener los cuatro destinos actuales mientras sigan siendo canónicos y conservar `qa/pwa-shortcuts-contract.mjs` como guardrail. Si la selección cambia por una decisión editorial estable, actualizar manifest y contrato en el mismo cambio.
