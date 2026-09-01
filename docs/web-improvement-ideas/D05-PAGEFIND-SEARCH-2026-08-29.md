# D.5 · Buscador interno mejorado / Pagefind

Fecha de reconstrucción: 2026-08-29  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `ALREADY_COVERED`.  
Revalidación actual: Pagefind sigue materializado en `main`; no abrir otro motor de búsqueda.

## 1. Hipótesis original

La lista inicial planteaba mejorar el buscador si solo hacía coincidencia literal, evaluando búsqueda difusa/semántica client-side y sin servicio de pago para consultas del tipo «quiero algo como X».

La hipótesis no exigía embeddings: buscaba mejor recall/relevancia sin backend.

## 2. Evolución completa en #135

### Primera revisión → `IMPLEMENT_AFTER_CURRENT_DEBT`

La revisión propone un piloto de Pagefind:

- adecuado para HTML estático;
- índice post-build;
- sin backend;
- comparar contra Fuse.js y buscador/asistente existente;
- evaluar recall, bytes, latencia y accesibilidad.

### Matriz → `PILOTAR ALTO`

La matriz eleva Pagefind como candidato claro:

> «Pagefind sobre `.preview-dist`: gratis, estático, sin backend/token. Comparar relevancia/UX con buscador actual.»

### Repo cross-check → `ALREADY_COVERED`

La inspección profunda cambia la decisión porque encuentra que el piloto ya había sido implementado.

Evidencia histórica:

- `scripts/build-pagefind-index.py`;
- filtro por `content-registry`/`searchIndex`/`noindex`;
- exclusión de HTML interno/chrome;
- modo `--check`;
- `tests/test-build-pagefind-index.py`;
- `/pagefind/` versionado/publicado;
- `assets/assistant.js` consume `/pagefind/pagefind.js` con fallback local.

### Override profundo

`IDEAS-MEJORA-WEB-OVERRIDES-REPO-2026-08-28.md` ordena explícitamente:

> no abrir una PR para «integrar búsqueda semántica» ni añadir embeddings/vector DB; reabrir solo si una eval real demuestra un fallo.

### Autoridad final → `ALREADY_COVERED`

> «Pagefind ya está integrado (`build-pagefind-index.py`, Pagefind 1.5.x). Afinar relevancia/UX, no abrir otro piloto.»

### Revalidación independiente

La falsación final mantiene D.1–D.12 y señala expresamente que Pagefind ya cubre búsqueda.

## 3. Genealogía de implementación

La historia de commits confirma que no es documentación latente.

### `28fd66c8c1ab5baa7c9beea2e486f1b4f8f86aeb`

Mensaje:

> `AF: materializar busqueda local Pagefind desde content-registry + noindex, sin cambios en assistant.js`

Ese commit materializa el índice local a partir de la autoridad del sitio.

### `5812c998a4651a70abf0605b79b7ab7a00c1ebe0`

Posteriormente se corrige/sincroniza el corpus, excluyendo fixtures/templates internos y regenerando índice/cifras.

Esta genealogía explica por qué el estado final no puede volver a `IMPLEMENT_AFTER_CURRENT_DEBT` sin evidencia nueva.

## 4. Arquitectura actual

`scripts/build-pagefind-index.py` sigue en `main` y declara como corpus:

- HTML git-tracked;
- exclusión si registry `status != public`;
- exclusión si `searchIndex: false`;
- exclusión por `<meta name=robots ... noindex>`;
- exclusión de `data/`, `tests/`, `scripts/`;
- default-include para el resto.

También elimina chrome repetido:

```text
header.site-header
dialog.explore-dialog
footer.site-footer
```

El builder:

- genera `.pagefind-src` temporal;
- ejecuta Pagefind;
- escribe `eligible-manifest.json`;
- tiene `--check` para detectar corpus stale.

## 5. Pagefind ≠ búsqueda vectorial

La idea original usó el término «semántica/difusa», pero la investigación neta no recomienda añadir una arquitectura vectorial.

Regla final:

```text
Pagefind actual
→ medir queries problemáticas
→ mejorar contenido/metadatos/ranking/configuración si procede
→ solo considerar otra tecnología si existe fallo reproducible que Pagefind no puede resolver
```

No:

```text
"semántica" en el backlog
→ embeddings
→ vector DB
→ API/Worker
```

## 6. Qué se debe medir si se reabre

Eval con corpus fijo de consultas reales:

- marca/autor;
- títulos de libros;
- Noveris/canalizadores;
- herramientas;
- editoriales/concursos;
- temas de Cuaderno;
- sinónimos razonables;
- queries internas sin resultado.

Métricas:

```text
relevant@1
relevant@3
no-result rate
latency
index bytes
JS bytes
keyboard journey
screen-reader labels/status
```

No hace falta un «semantic search score» inventado.

## 7. Fallback

La arquitectura histórica mantiene fallback local si Pagefind no carga. Esa resiliencia forma parte de la implementación existente.

Cualquier cambio debe preservar:

- ausencia de backend obligatorio;
- CSP;
- no exponer contenido gated/noindex;
- comportamiento razonable si el índice falla.

## 8. Autoridad de corpus

D.5 no debe crear una lista manual paralela de rutas. La elegibilidad deriva de las autoridades ya usadas por el sitio.

Esto evita:

- indexar páginas privadas/gated;
- olvidar nuevas rutas públicas;
- drift entre Search, sitemap y registry.

## 9. Relación con C.8/C.3

- C.8 puede usar búsquedas/no-results como evidencia para mejorar «Empieza aquí».
- C.3 puede usar queries agregadas como señal editorial.
- D.5 sigue siendo mecanismo de recuperación, no generador automático de contenido.

## 10. Relación con el asistente

El asistente puede consumir/usar Pagefind como fallback/fuente local, pero eso no convierte D.5 en un proyecto de IA.

No duplicar índices para «buscador» y «asistente» sin necesidad.

## 11. Seguridad/privacidad

Ventajas del diseño actual:

- índice estático;
- no requiere queries en servidor propio;
- no añade SaaS;
- no necesita tokens;
- corpus público deliberado.

No degradar esto enviando búsquedas a terceros por defecto.

## 12. Qué NO hacer

- nueva integración Pagefind;
- Fuse.js paralelo «por comparar» después de que el estado final ya cerró el piloto;
- embeddings/vector DB sin eval;
- indexar `noindex`;
- índice manual de URLs;
- enviar queries a proveedor externo;
- crear otro buscador visual separado del asistente/search actual;
- reescribir builder solo por estilo.

## 13. Trigger real de reapertura

Uno de:

- mala relevancia reproducible;
- cobertura incorrecta;
- páginas públicas ausentes;
- páginas privadas indexadas;
- índice stale;
- bytes/latencia excesivos;
- CSP/runtime roto;
- accesibilidad defectuosa.

Entonces corregir **la integración existente**.

## 14. Blueprints

`IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` excluye expresamente las capacidades ya existentes como Pagefind del backlog neto. No hay blueprint de nueva implementación porque esa deuda desapareció tras el cross-check.

## 15. Pasadas posteriores revisadas

Cuarta–decimoquinta no añaden un motor superior ni cambian D.5. La política free-first es coherente con Pagefind, pero no justifica reabrirlo. R.57 Coverage puede medir CSS/JS, no es una razón para sustituir Search.

## 16. Trazabilidad

- idea original;
- revisión `IMPLEMENT_AFTER_CURRENT_DEBT`;
- matriz `PILOTAR ALTO`;
- repo cross-check `ALREADY_COVERED`;
- override profundo;
- commits `28fd66c8...` y `5812c998...`;
- autoridad machine-readable;
- autoridad final;
- revalidación independiente;
- `scripts/build-pagefind-index.py` actual.

## 17. Definition of Done de esta reconstrucción

- [x] hipótesis original preservada;
- [x] estados previos y override preservados;
- [x] genealogía encontrada;
- [x] arquitectura actual descrita;
- [x] trigger de reapertura limitado a fallos medidos;
- [x] no se crea un segundo motor.

## Recomendación para Clara/Claude

**No implementar D.5.** Pagefind ya es la autoridad. Si una eval real descubre un defecto, reparar/extender Pagefind y sus tests; no crear búsqueda paralela.