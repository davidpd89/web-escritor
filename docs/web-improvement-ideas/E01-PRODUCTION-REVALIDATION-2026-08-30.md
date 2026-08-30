# E.1 · Revalidación de producción — escalera AVIF → WebP

Fecha: 2026-08-30  
Base verificada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.  
Decisión: **ALREADY_HAS_GATED_LADDER · FOUR_COVER_VARIANTS_MANAGED · EXPAND_ONLY_WITH_MEASURED_CANDIDATE · NO_MASS_CONVERSION · NO_CODE**.

## 1. Resultado

La idea original amplia de convertir imágenes a AVIF ya no describe el estado real del sitio. `main` dispone de una autoridad reproducible y con QA para una escalera AVIF → WebP selectiva.

E.1 no debe convertirse en una migración masiva. El trabajo futuro consiste en evaluar candidatos concretos por bytes, uso, LCP y calidad visual e incorporarlos a **la misma autoridad** solo cuando el beneficio sea material.

## 2. Builder canónico

`scripts/build-image-format-ladder.py` declara explícitamente:

- solo procesa parejas listadas en `data/image-format-ladder.json`;
- WebP es la fuente/fallback;
- AVIF es la derivada;
- la procedencia se fija mediante SHA-256 de ambos archivos;
- encoder, calidad y versión de Pillow están fijados;
- `--check` valida frescura sin usar mtime ni solo dimensiones;
- cambio del WebP obliga a regenerar/registrar la derivada;
- derivada ausente, corrupta o con hash/dimensiones incorrectas falla.

Eso ya resuelve el problema de reproducibilidad que una conversión ad hoc no cubriría.

## 3. Manifest actual

`data/image-format-ladder.json` usa `schema_version: 2` y contiene actualmente **4 fuentes elegibles**:

- `portada-las-manecillas-del-recuerdo-320.webp`;
- `...-512.webp`;
- `...-768.webp`;
- `...-1024.webp`.

Cada una tiene un hermano `.avif` y hashes de fuente/derivada.

El propio manifest advierte que no es una lista de assets a convertir masivamente.

## 4. QA existente

`.github/workflows/image-format-ladder-qa.yml` ejecuta:

1. tests de mutación/unidad;
2. `build-image-format-ladder.py --check`;
3. `check-image-format-ladder.py --check` para el contrato HTML;
4. browser QA con Chromium.

Además el workflow se dispara ante cambios en el manifest, scripts, requisitos, tests, assets de portada y superficies consumidoras principales.

No se necesita un segundo pipeline de optimización de formatos.

## 5. Qué falta demostrar antes de ampliar

Esta revalidación no establece que los demás WebP/JPEG/PNG deban recibir AVIF.

Un nuevo candidato debe tener evidencia de:

- consumo público real;
- bytes relevantes en el journey;
- frecuencia/criticidad suficiente;
- ahorro AVIF material frente al fallback;
- calidad visual aceptable;
- compatibilidad con el patrón HTML existente;
- beneficio no neutralizado por complejidad/cache/preload.

LCP merece prioridad, pero tampoco se convierte automáticamente todo LCP sin comparar bytes y calidad.

## 6. Contrato de incorporación futura

Para cada candidato aprobado:

```text
medir source
→ generar AVIF con builder canónico
→ registrar pareja/hashes
→ integrar picture/srcset según autoridad vigente
→ validar HTML
→ browser QA
→ medir de nuevo
```

No producir derivados fuera del manifest y «registrarlos después» como práctica habitual.

## 7. Qué no hacer

- no convertir `assets/**` masivamente;
- no borrar WebP fallback;
- no introducir otro encoder/pipeline sin migración explícita;
- no usar mtime como frescura;
- no añadir AVIF porque el formato sea moderno;
- no degradar arte/portadas por perseguir bytes;
- no tocar preloads/LCP sin medición;
- no mantener `<picture>` y manifest manualmente divergentes.

## 8. Estado final

```text
format ladder authority = PRESENT
reproducibility = PRESENT
provenance hashes = PRESENT
browser/CI guard = PRESENT
current eligible set = 4 Manecillas cover variants
mass conversion trigger = ABSENT
future expansion = ASSET_BY_ASSET
```

## 9. Definition of Done

- [x] builder inspeccionado directamente;
- [x] manifest y encoder inspeccionados;
- [x] cuatro parejas actuales verificadas;
- [x] QA/workflow inspeccionado;
- [x] conversión masiva descartada;
- [x] criterio de candidato futuro definido;
- [x] sin segundo pipeline ni código innecesario.

## Estado para Claude

Tratar E.1 como una capacidad ya implementada con alcance selectivo. Antes de ampliar, aportar un candidato concreto y medición de bytes/LCP/calidad; si compensa, incorporarlo al ladder existente, nunca mediante conversión global paralela.