# Yale Review clean-room translation lab

Este laboratorio demuestra cómo trasladar principios editoriales observados en The Yale Review al sistema V1/V6 de `davidportodiaz.com` sin copiar código, fuentes, DOM, assets ni branding de terceros.

## Archivos

- `prototype.html`: composición de prueba usando contenido/rutas de David Porto.
- `prototype.css`: CSS original limitado al laboratorio.
- `test-contract.mjs`: comprobaciones automáticas mínimas del contrato clean-room/responsive.

## Cómo probarlo en un checkout local

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
- sin JavaScript.

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

## Qué NO demuestra este laboratorio

- No afirma reproducir el CSS exacto de Yale Review.
- No contiene measurements obtenidos con DevTools del sitio de terceros.
- No propone reemplazar el shell actual.
- No cambia banners V5.
- No modifica runtime público.
- No es una aprobación automática para sustituir Home.

## Uso por CODEX

Antes de implementar en runtime, leer en este orden:

1. `../YALE-REVIEW-FROM-THE-ARCHIVES-AUDITORIA.md`
2. `../YALE-REVIEW-DEEP-DIVE-ADDENDUM.md`
3. `../YALE-REVIEW-CODEX-IMPLEMENTATION-HANDOFF.md`
4. este README;
5. `prototype.html` + `prototype.css`.

Después comparar el prototipo con:

- `assets/v1-tokens.css`
- `assets/v1-site-cohesion-v6.css`
- `assets/v1-editorial.css`
- `assets/v1-home-editorial-v3.css`
- `assets/v1-families.css`
- `assets/v1-shell-lrb-v2.css`

No aplicar una refactorización global sin baseline de screenshots y gates verdes.