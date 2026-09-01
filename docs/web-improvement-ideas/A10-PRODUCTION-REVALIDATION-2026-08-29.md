# A.10 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #159  
Decisión operativa: **ALREADY_COVERED COMPLETELY · NO_CODE · PRESERVE_HTTP_CONTRACT**

## Decisión cerrada

No se rediseña ni se reimplementa la 404 por A.10.

El estado actual cumple la necesidad humana y el contrato técnico importante:

- `404.html` es una página de error diseñada, comprensible y coherente con el sitio;
- ofrece rutas de recuperación útiles;
- declara `noindex,follow`;
- no canonicaliza el error a Home;
- no redirige automáticamente una URL inexistente a `/`;
- el QA de discoverability demuestra que una ruta inexistente responde **HTTP 404 real** y recibe el contenido de `404.html`;
- el comportamiento sigue probado con navegador, sin JavaScript y bajo reflow.

A.10 queda como contrato de preservación. No existe trabajo neto de runtime.

## Revalidación con la documentación oficial vigente

### Google · errores 404 / soft 404

https://developers.google.com/search/docs/crawling-indexing/http-network-errors

Google mantiene la distinción material:

- una URL inexistente debe responder un código 4xx adecuado, normalmente `404` o `410`;
- una página con apariencia de error que devuelve `200` puede ser tratada como **soft 404**;
- las respuestas 4xx no se consideran contenido indexable normal;
- `404` y `410` indican que el recurso no existe.

Por tanto, el status HTTP es la garantía esencial. `noindex` puede conservarse como defensa explícita/product decision, pero **no sustituye** un HTTP 404 correcto.

### Google · página 404 personalizada

https://developers.google.com/search/docs/crawling-indexing/soft-404-errors

La recomendación vigente sigue siendo ofrecer una página útil para la persona que llega a una URL rota:

- explicar que la página no se encuentra;
- mantener apariencia/navegación coherentes con el sitio;
- ofrecer enlaces a Home o contenido útil/popular;
- opcionalmente permitir reportar un enlace roto si existe un canal operativo razonable;
- asegurarse de que el servidor devuelve 404 real.

El estado actual satisface el núcleo de esta recomendación sin añadir complejidad.

## Evidencia del repo actual

### `404.html`

La página actual contiene:

- `<meta name="robots" content="noindex,follow">`;
- título `Página no encontrada · David Porto Díaz`;
- mensaje explícito de dirección inexistente;
- navegación/shell V1;
- CTA y enlaces de recuperación;
- destinos como Inicio, Obras, Cuaderno, Herramientas, Recomendaciones y mapa del sitio;
- ausencia de canonical ficticia a Home;
- ausencia de contenido/schema creado para intentar posicionar una URL de error.

No es una plantilla vacía ni una página legacy desconectada del diseño actual.

### QA de navegador real

`.github/workflows/global-discoverability-closure-qa.yml` se activa cuando cambia `404.html` o las superficies propietarias de discoverability y ejecuta `qa/global-discoverability-browser.mjs`.

Ese QA no se limita a abrir `/404.html` directamente. Levanta un servidor edge de prueba con el comportamiento esperado y navega a una ruta controladamente inexistente:

```text
/__global_discoverability_missing__/deep/path
```

Después comprueba:

```text
response.status() == 404
h1 comunica que la página no existe
enlaces de recuperación a /, /libros/, /cuaderno/, /herramientas/ y /mapa-del-sitio/
```

Además la suite incluye:

- 404 en viewports representativos;
- navegación esencial sin JavaScript;
- reflow general;
- evidencias de navegador como artefactos de CI.

Esto confirma que el contrato histórico de #135 sigue vivo y protegido.

## Por qué NO se añade otro test

El documento histórico sugería mantener un smoke HTTP si no existía equivalente.

Sí existe equivalente, y es mejor que un test estático dedicado:

- prueba una **ruta inexistente**, no solo el fichero `404.html`;
- inspecciona el status de la respuesta;
- valida el contenido de rescate;
- vive en el workflow propietario de discoverability;
- se dispara cuando cambia la 404 o infraestructura relacionada.

Añadir `tests/test-404.py`, otro Playwright o un checker SEO paralelo duplicaría la misma garantía sin cubrir una clase nueva de fallo.

## Lo que debe preservarse

1. URL inexistente → HTTP 404 real.
2. Body útil de `404.html`.
3. `noindex,follow` puede mantenerse como señal explícita de producto.
4. Sin canonical a `/`.
5. Sin redirect automático a Home.
6. Navegación y shell coherentes.
7. Recuperación a destinos canónicos y estables.
8. Uso básico sin JavaScript.
9. Accesibilidad/reflow bajo gates globales.
10. La 404 no entra en sitemap ni se trata como contenido editorial indexable.

## Mejoras posibles que NO son deuda de A.10

### Búsqueda dentro de la 404

No se añade Pagefind/buscador solo porque exista. Puede evaluarse si analítica o testing demuestra que usuarios aterrizan con frecuencia en URLs rotas y no encuentran salida mediante los enlaces actuales.

### Reportar enlace roto

Podría existir si hay un canal de mantenimiento útil. Sin ese flujo, añadir un formulario o servicio genera más superficie de spam/privacidad que valor.

### Tracking especial de recuperación

No es requisito para que la 404 sea correcta. Solo se instrumenta si responde una pregunta de producto concreta y encaja con la taxonomía/privacidad existente.

### Redirects inteligentes

Un redirect 301/308 sí es correcto cuando una URL retirada tiene un reemplazo claro. Eso pertenece a la política de migración concreta de esa URL, no a convertir **todas** las 404 en redirects automáticos.

## Alternativas descartadas

1. **Rediseñar por checklist** — no resuelve defecto actual.
2. **Redirigir todo a Home** — oculta errores y puede generar soft-404/confusión.
3. **Responder 200 con la plantilla 404** — rompe el contrato HTTP.
4. **Canonical a Home** — señal contradictoria para una URL inexistente.
5. **Añadir keywords/schema a la 404** — intenta convertir error en contenido SEO.
6. **Segundo test de status 404** — duplicaría `global-discoverability-browser.mjs`.
7. **Buscador pesado obligatorio** — coste sin evidencia de necesidad.
8. **Una 404 distinta por territorio** — multiplica mantenimiento sin resolver un problema demostrado.

## Trigger de reapertura

A.10 solo vuelve a desarrollo ante un hecho reproducible, por ejemplo:

- una URL inexistente responde 200/3xx inesperado;
- infraestructura/deploy deja de servir `404.html` con status 404;
- desaparecen rutas de recuperación esenciales;
- un cambio de shell rompe la página sin JS/reflow/accesibilidad;
- datos de usuarios demuestran que la recuperación actual falla de forma significativa;
- una migración concreta necesita redirects de URLs retiradas hacia reemplazos verdaderos.

La corrección debe extender el QA/infraestructura propietaria, no crear otro subsistema genérico de 404.

## Definition of Done

- [x] historia de #135 preservada;
- [x] `main@291c8c6…` revalidado;
- [x] `404.html` actual inspeccionado;
- [x] `noindex,follow` confirmado;
- [x] ausencia de canonical a Home confirmada;
- [x] recuperación útil confirmada;
- [x] workflow propietario localizado;
- [x] smoke de ruta inexistente + HTTP 404 real confirmado en código;
- [x] no-JS/reflow/browser evidence confirmados;
- [x] documentación Google vigente contrastada;
- [x] soft-404 200 explícitamente descartado;
- [x] test duplicado falsado como innecesario;
- [x] no existe gap de runtime actual.

**Conclusión:** A.10 está completamente cubierta. La acción correcta es preservar el contrato HTTP y el QA existente; rediseñar o añadir infraestructura adicional sin un fallo real empeoraría mantenibilidad sin mejorar recuperación.