# Escalera de formatos AVIF → WebP (L.1, 2026-08-23)

## Alcance frente a otras piezas relacionadas

- **#61 H.3** (`scripts/check-responsive-images.py`) sigue siendo la autoridad de **geometría responsive**: `width`/`height`, `srcset`/`sizes`, coherencia de `loading`/`fetchpriority`. Este contrato no duplica esos checks.
- **#67 L.1** se limita a la **escalera de formatos y procedencia**: qué imágenes deben ofrecer AVIF además de WebP, cómo se genera la derivada y cómo se prueba que no ha quedado silenciosamente obsoleta respecto a su fallback.

## Política de elegibilidad

Solo las fuentes WebP declaradas explícitamente en `data/image-format-ladder.json` reciben una derivada AVIF hermana. **No** se convierte `/assets/` de forma indiscriminada. Quedan excluidos por diseño:

- imágenes OG/redes sociales que necesitan una URL estable en un formato de amplio soporte;
- materiales de trabajo e imágenes no publicadas;
- variantes sin consumidor real;
- PNG/JPEG que deban conservarse por transparencia, fidelidad o compatibilidad y donde convertir no compense.

La lista actual cubre únicamente la cubierta de *Las manecillas del recuerdo* en cuatro tamaños ya consumidos por Home y las superficies principales de Manecillas: 320, 512, 768 y 1024 px. El retrato de Home que ya tenía AVIF antes de esta PR queda fuera de esta autoridad porque no fue generado por este pipeline.

## Dependencia Python reproducible

Pillow es la única dependencia Python no estándar que necesita este pipeline. Su autoridad es `scripts/requirements.txt`, actualmente fijada a `Pillow==12.3.0` para Python 3.12.

Tanto la batería global `Tool engine tests` como `Image format ladder QA` instalan ese mismo fichero. No hay un `pip install pillow` flotante ni versiones distintas por workflow. El manifest declara además `encoder.pillow_version`; builder y checker fallan si el entorno no coincide con la versión fijada.

## Contrato de procedencia y frescura

`data/image-format-ladder.json` usa `schema_version: 2`. Cada entrada declara:

- `source`: WebP fuente/fallback;
- `derivative`: AVIF hermano esperado;
- `source_sha256`: SHA-256 de los bytes del WebP;
- `derivative_sha256`: SHA-256 de los bytes del AVIF.

El manifest también fija el contrato del encoder (`format: AVIF`, `quality: 60`, `pillow_version: 12.3.0`). La frescura **no** depende de dimensiones, `mtime` ni fecha de ejecución.

Esto cierra dos clases de obsolescencia silenciosa:

1. Si cambia el contenido del WebP aunque conserve exactamente la misma anchura y altura, `source_sha256` deja de coincidir y CI falla hasta regenerar la derivada.
2. Si el AVIF se sustituye/corrompe por otro fichero —incluso con las mismas dimensiones—, `derivative_sha256` deja de coincidir y CI falla.

Las dimensiones siguen comprobándose como una condición secundaria de equivalencia de formato, no como señal de frescura ni como sustituto de #61.

## Builder

`scripts/build-image-format-ladder.py` es la única vía canónica de regeneración:

- `--check` es de solo lectura y valida manifest, versión de Pillow, hashes, existencia y dimensiones;
- sin `--check`, regenera **solo** las parejas que estén ausentes u obsoletas;
- tras regenerar, actualiza los SHA-256 de fuente y derivada en el manifest;
- no recorre ni convierte el repositorio completo;
- la derivada debe ser el `.avif` hermano con el mismo nombre base del WebP.

Ejemplo:

```bash
python -m pip install --requirement scripts/requirements.txt
python scripts/build-image-format-ladder.py
python scripts/build-image-format-ladder.py --check
```

## Checker HTML/formato

`scripts/check-image-format-ladder.py --check` verifica, para cada entrada elegible:

1. que existan tanto el WebP como el AVIF;
2. que ambos SHA-256 coincidan con la autoridad del manifest;
3. que sus dimensiones sean iguales;
4. que `derivative` sea exactamente el AVIF hermano de la fuente;
5. que una referencia HTML al WebP dentro de la escalera tenga inmediatamente antes un `<source type="image/avif">` con el mismo `media`;
6. que ese `<source>` apunte al **AVIF correspondiente**, no simplemente a cualquier fichero AVIF con la misma condición de `media`;
7. que el `<img>` siga siendo el fallback de amplio soporte; AVIF se añade como formato preferente, no sustituye al fallback.

## Mutation tests obligatorios

`tests/test-check-image-format-ladder.py` demuestra el contrato con fixtures aislados:

- **A — sincronizado:** WebP + AVIF + hashes correctos → PASS;
- **B — fuente obsoleta:** cambia el contenido del WebP manteniendo **exactamente** las mismas dimensiones → checker y builder `--check` FALLAN por SHA-256;
- **C — regeneración:** el builder regenera únicamente la derivada afectada, actualiza el manifest y el checker vuelve a PASS;
- **D1 — falta fallback:** diagnóstico explícito de WebP ausente;
- **D2 — falta AVIF:** diagnóstico explícito de derivada ausente;
- **mutación adicional:** AVIF reemplazado por contenido distinto con el mismo tamaño → FAIL por `derivative_sha256`;
- **mutación adicional:** un AVIF de otra variante colocado inmediatamente antes del WebP → FAIL por correspondencia de hermano;
- se mantienen las pruebas de `media` distinto y dimensiones distintas.

## Verificación en navegador

`qa/image-format-ladder-browser.mjs` comprueba en Chromium que la Home solicita realmente el `.avif` de la cubierta cuando el navegador lo soporta y que la geometría renderizada no se degrada. La geometría HTML contractual continúa siendo responsabilidad de #61.

No se modifican URLs de `og:image`, `twitter:image` ni JSON-LD para forzar AVIF: esas superficies mantienen formatos compatibles con consumidores externos.

## Cómo añadir una nueva superficie elegible

1. Confirmar que ya existe un WebP público con consumidor real; no crear variantes especulativas.
2. Añadir la pareja `source`/`derivative` al manifest.
3. Ejecutar el builder canónico para generar solo esa derivada y registrar sus SHA-256.
4. Añadir el `<source type="image/avif">` correspondiente inmediatamente antes de su WebP, con el mismo `media` cuando aplique.
5. Ejecutar mutation/unit tests, builder `--check`, checker `--check` y browser QA.
6. Si cambia posteriormente el WebP fuente, ejecutar de nuevo el builder; no actualizar hashes manualmente para silenciar el gate.
