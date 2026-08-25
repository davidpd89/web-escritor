# Yale Review clean-room translation lab

Este laboratorio demuestra cómo trasladar principios editoriales observados en The Yale Review al sistema V1/V6 de `davidportodiaz.com` sin copiar código, fuentes, DOM, assets ni branding de terceros.

## Archivos

- `prototype.html`: composición de prueba usando contenido/rutas de David Porto.
- `prototype.css`: CSS original limitado al laboratorio.
- `integration-candidate.css`: capa opt-in que prueba el lenguaje Yale sobre selectores REALES del V1/V6 sin modificar producción.
- `integration-map.json`: mapa máquina familia → selectores → cambio permitido → pruebas requeridas.
- `test-contract.mjs`: comprobaciones automáticas mínimas del contrato clean-room/responsive y del candidato de integración.

## Cómo probar el prototipo aislado

Desde la raíz del repo:

```bash
python -m http.server 8080
```

Abrir:

```text
http://localhost:8080/docs/referencias-editoriales/yale-review-lab/prototype.html
```

Ejecutar el contrato:

```bash
node docs/referencias-editoriales/yale-review-lab/test-contract.mjs
```

## Cómo probarlo sobre una página REAL sin tocar producción

`integration-candidate.css` está deliberadamente inerte. Nada del sitio lo carga.

En un checkout local, para una página de prueba:

1. añadir temporalmente `data-yale-reference-preview="true"` al elemento `<html class="v1">`;
2. añadir después de las hojas de producción:

```html
<link rel="stylesheet" href="/docs/referencias-editoriales/yale-review-lab/integration-candidate.css">
```

3. servir el repo localmente;
4. capturar antes/después en 390, 768 y 1440 como mínimo;
5. comprobar teclado, zoom 200% y reduced motion;
6. retirar atributo y `<link>` al terminar.

La capa está scopeada al atributo de preview precisamente para que un enlace accidental al CSS no altere la web normal.

## Páginas reales recomendadas para la comparación

Primera tanda, porque cubre todas las gramáticas sin probar 59 URLs a mano:

- `/` — Home: banners + clusters;
- `/cuaderno/` — benchmark interno más cercano a Yale;
- un artículo real de `/cuaderno/` — prosa larga y cola editorial;
- `/libros/` — catálogo/Obras;
- `/las-manecillas-del-recuerdo/` — familia Libro;
- `/herramientas/` — hub funcional;
- `/autor.html` — identidad/documental;
- `/prensa.html` — ledger de prensa;
- `/eventos.html` — cronología;
- `/mapa-del-sitio/` — findability/auxiliar;
- `/404.html` — recuperación y gutter móvil.

Si esas familias quedan coherentes, ejecutar después la matriz global de QA ya existente sobre todo el inventario.

## Viewports obligatorios

- 320 × 800
- 390 × 844
- 768 × 1024
- 1024 × 768
- 1440 × 1000
- 1728 × 1117

Además:

- landscape móvil con altura <=430px;
- `prefers-reduced-motion: reduce`;
- keyboard-only;
- zoom 200%;
- sin JavaScript cuando la página tenga fallback no-JS definido.

## Qué evaluar visualmente

1. El H1 domina sin sentirse como un billboard.
2. Los bloques se separan con reglas, no con cards elevadas.
3. Las piezas de distinta importancia tienen distinta escala pero comparten superficie.
4. La metadata se reconoce siempre por posición/tamaño.
5. Los títulos interactivos se subrayan; no saltan ni hacen zoom.
6. Los filtros siguen pareciendo parte de la publicación, no un widget externo.
7. El ledger inferior puede recorrerse rápidamente.
8. En móvil el orden sigue siendo lógico y no hay dos columnas comprimidas.
9. Ninguna línea toca accidentalmente el borde del viewport: todo respeta `--page-gutter`.
10. La composición sigue pareciendo David Porto porque usa Instrument Serif, Newsreader, Manrope y los tokens propios.
11. Home conserva los banners y la dirección de arte aprobada.
12. Libro/Herramientas siguen siendo utilizables: la limpieza no puede eliminar affordance funcional.

## Qué NO demuestra este laboratorio

- No afirma reproducir el CSS exacto de Yale Review.
- No contiene measurements fingidos como `computed CSS` de Yale.
- No propone reemplazar el shell actual.
- No cambia banners V5.
- No modifica runtime público.
- No es una aprobación automática para sustituir Home.
- No autoriza a instalar GT Cinetype ni fuentes Yale.

## Uso por CODEX

Leer en este orden:

1. `../YALE-REVIEW-FROM-THE-ARCHIVES-AUDITORIA.md`
2. `../YALE-REVIEW-DEEP-DIVE-ADDENDUM.md`
3. `../YALE-REVIEW-CODEX-IMPLEMENTATION-HANDOFF.md`
4. `integration-map.json`
5. este README;
6. `prototype.html` + `prototype.css`;
7. `integration-candidate.css`.

Después comparar con:

- `assets/v1-tokens.css`
- `assets/v1-site-cohesion-v6.css`
- `assets/v1-editorial.css`
- `assets/v1-home-editorial-v3.css`
- `assets/v1-families.css`
- `assets/v1-shell-lrb-v2.css`

## Orden rápido para CODEX

```text
baseline screenshots
→ ejecutar test-contract.mjs
→ preview opt-in en Cuaderno
→ preview opt-in en Home
→ preview opt-in en Herramientas/Autor/Prensa
→ decidir qué reglas merecen subir a V1/V6
→ implementar por familia, no con overrides infinitos
→ ejecutar QA global
→ visual diff final
```

No aplicar una refactorización global sin baseline de screenshots y gates verdes. Si un cambio solo “parece más Yale” pero empeora orientación, lectura, acceso a herramientas, conversión o responsive, se descarta.