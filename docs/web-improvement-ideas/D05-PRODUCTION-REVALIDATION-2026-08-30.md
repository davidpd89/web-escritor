# D.5 · Revalidación de producción — Pagefind / búsqueda local

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **ALREADY_COVERED · PAGEFIND_IS_LIVE_AUTHORITY · CORPUS_GATES_WORKING · NO_SECOND_ENGINE · NO_CODE**.

## 1. Resultado

D.5 no es deuda de implementación. Pagefind está materializado, publicado y consumido por el runtime del asistente. El trabajo correcto futuro es reparar o afinar esa integración únicamente ante un fallo reproducible; no abrir Fuse.js, embeddings, vector DB ni otro buscador paralelo.

## 2. Evidencia directa de `main`

### Builder

`scripts/build-pagefind-index.py`:

- toma todos los HTML git-tracked;
- excluye entradas de `data/content-registry.json` cuyo `status` no sea `public`;
- excluye `searchIndex: false`;
- excluye páginas con `meta robots` que contenga `noindex`;
- excluye HTML internos de `data/`, `tests/` y `scripts/`;
- elimina del corpus el chrome repetido `header.site-header`, `dialog.explore-dialog` y `footer.site-footer`;
- genera temporalmente `.pagefind-src`;
- ejecuta Pagefind;
- escribe `pagefind/eligible-manifest.json`;
- dispone de `--check` para fallar cuando el corpus comprometido queda obsoleto.

No existe una lista manual de URLs de búsqueda que compita con las autoridades editoriales del sitio.

### Runtime

`assets/assistant.js` contiene `pagefindFallback(query)` y carga:

```js
await import('/pagefind/pagefind.js')
```

Busca con Pagefind, normaliza los primeros resultados y, si el import/search falla, cae en `rankLocalSources()` sobre el registro local del asistente. Por tanto:

```text
Pagefind operativo
→ fallback local si falla
→ sin backend obligatorio para navegación/búsqueda
```

Pagefind no es un artefacto muerto ni un piloto pendiente.

## 3. Manifest actual y falso positivo descartado

`pagefind/eligible-manifest.json` declara actualmente **55 páginas** elegibles.

Durante la revalidación se detectó que:

```text
/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/
```

no aparece en el manifest pese a existir físicamente. La inspección directa de su HTML confirma:

```html
<meta name="robots" content="noindex, follow, ...">
```

Su exclusión es, por tanto, **correcta y deliberada** según el contrato del builder. No es una pérdida de cobertura de Pagefind.

Esta comprobación es importante porque evita convertir una diferencia de corpus válida en un bug inexistente.

## 4. Drive

El owner actual de asistente/búsqueda es `40 — ASISTENTE DE LA WEB — CHATBOT · BÚSQUEDA HÍBRIDA · IA GRATUITA · CITAS · PRIVACIDAD · IMPLEMENTACIÓN`.

Su principio útil coincide con la implementación actual: la búsqueda/navegación debe seguir funcionando aunque la capa de IA no esté disponible.

También existe material histórico anterior que describía Pagefind como ausente/no incorporado. Ese estado está superado por la evidencia directa del repo y no debe reabrir una deuda ya resuelta.

## 5. Qué sí justificaría cambios

Solo reabrir D.5 ante evidencia reproducible como:

- página pública/indexable que debería ser recuperable y no entra en el corpus;
- página gated/noindex que sí entra;
- manifest stale;
- mala relevancia demostrada con un corpus de queries real;
- no-result rate significativo;
- latencia/bytes excesivos;
- rotura de CSP/import;
- fallback roto;
- journey de teclado/lector de pantalla defectuoso.

En esos casos se modifica **Pagefind y sus tests actuales**.

## 6. Qué no hacer

- no crear un segundo motor visual;
- no añadir Fuse.js solo para mantener vivo el antiguo piloto comparativo;
- no añadir embeddings/vector DB por llamar «semántica» a la idea inicial;
- no enviar búsquedas a terceros por defecto;
- no mantener otro inventario de URLs;
- no indexar deliberadamente contenido `noindex` para «mejorar resultados»;
- no reescribir el builder sin un defecto medido.

## 7. Definition of Done

- [x] Pagefind verificado directamente en `main`;
- [x] consumo real desde `assets/assistant.js` verificado;
- [x] fallback local verificado;
- [x] manifest actual inspeccionado;
- [x] ausencia aparente de una URL investigada y explicada por `noindex`;
- [x] Drive reconciliado con la implementación actual;
- [x] sin motor paralelo ni código innecesario.

## Estado para Claude

Tratar D.5 como **capacidad ya cubierta**. Si aparece un problema, repararlo en la autoridad existente (`build-pagefind-index.py` + Pagefind + assistant fallback), no abrir una nueva arquitectura de búsqueda.