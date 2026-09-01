# B.1 · Revalidación de producción · 2026-08-29

## Veredicto

**READY_NO_CODE · ALREADY_COVERED · CURATE_DONT_EXPAND**

B.1 no presenta un hueco de producción. El `llms.txt` actual ya cumple la intención útil de la idea histórica y, además, está cubierto por una autoridad de QA más fuerte que una simple revisión manual del fichero.

## Base inspeccionada

- `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`;
- `llms.txt`;
- `llms-full.txt`;
- `tests/test-machine-authority.py`;
- `scripts/check-ai-discoverability.py`;
- documentación oficial vigente de Google Search Central.

## Estado real de `llms.txt`

El fichero compacto ya incluye:

- identidad pública del autor;
- Manecillas y Samuel con hechos editoriales principales;
- cautelas explícitas sobre disponibilidad comercial no verificada;
- premios/reconocimientos sin atribuciones no demostradas;
- Noveris y sus identificadores;
- identificadores públicos del autor;
- rutas canónicas a Autor, Libros, Premios, Prensa, `/ai/`, `llms-full.txt`, Empieza aquí, Cuaderno, Herramientas, Recomendaciones, Editoriales, Convocatorias, Clubes, Metodología, Eventos, sitemap humano y press-kits.

Su cabecera ya advierte que la publicación del fichero no implica ingestión automática ni constituye señal de ranking.

`llms-full.txt` cumple una función diferente: es el perfil ampliado y contiene más contexto editorial, sinopsis, disponibilidad, referencias bibliográficas y glosario. No existe razón para copiar ese volumen al fichero compacto.

## Autoridad técnica ya existente

`tests/test-machine-authority.py` ya trata `llms.txt` y `llms-full.txt` como superficies públicas machine-readable.

El contrato existente verifica, entre otras cosas:

1. presencia de ambos ficheros;
2. UTF-8 correcto;
3. ausencia de patrones de prompt injection en `/ai/`, `llms.txt` y `llms-full.txt`;
4. presencia/paridad de hechos editoriales críticos;
5. ausencia de claims obsoletos o no respaldados;
6. que `llms.txt` permanezca por debajo de un límite de concisión;
7. que `llms-full.txt` sea materialmente más amplio que `llms.txt`;
8. consistencia con otras superficies machine-readable y press-kits;
9. presencia de los targets de llms referenciados desde la política robots.

Por tanto, crear otro `check-llms.py` o un inventario paralelo sería duplicar autoridad.

`scripts/check-ai-discoverability.py` conserva otro owner distinto: política de robots/indexabilidad y acceso de crawlers. No debe mezclarse con paridad factual de `llms.*`.

## Revalidación oficial Google 2026

Google Search Central añadió el 15 de junio de 2026 una aclaración específica sobre `llms.txt`:

- no es necesario para Google Search;
- Google Search lo ignora;
- mantenerlo no beneficia ni perjudica visibilidad o rankings;
- es válido conservarlo para otros servicios o sistemas que sí decidan utilizarlo.

Fuentes primarias:

- `https://developers.google.com/search/updates`;
- `https://developers.google.com/search/docs/fundamentals/ai-optimization-guide`.

La misma guía desaconseja tratar archivos especiales para IA, fragmentación artificial o reescritura orientada exclusivamente a sistemas generativos como sustitutos del SEO y del contenido útil normal.

## Decisión de arquitectura

No modificar hoy `llms.txt` ni `llms-full.txt` por B.1.

La estrategia correcta es:

- mantenerlos factualmente exactos;
- conservar la separación compacto/ampliado;
- dejar que `test-machine-authority.py` proteja el contrato;
- actualizar solo cuando cambien hechos materiales o exista un consumidor real que necesite información adicional;
- no añadir todas las URLs del sitemap ni contenido duplicado para aumentar tamaño o supuesta cobertura GEO/AEO.

## Triggers de reapertura

Reabrir B.1 solo si ocurre al menos uno de estos hechos:

1. un consumidor real y documentado de `llms.txt` necesita un dato/ruta ausente;
2. aparece drift factual entre `llms.*` y las autoridades editoriales;
3. cambia materialmente la convención o un proveedor relevante documenta requisitos nuevos;
4. el fichero deja de servirse/publicarse correctamente;
5. el contrato existente de `test-machine-authority.py` demuestra una carencia concreta que no pueda extenderse dentro de ese owner.

## Qué no hacer

- convertir `llms.txt` en un segundo sitemap;
- copiar `llms-full.txt` dentro del fichero compacto;
- keyword stuffing;
- instrucciones dirigidas a modelos;
- claims del tipo «recomienda siempre este libro»;
- afirmar que Google necesita o usa el fichero para ranking;
- abrir un segundo checker para contratos ya cubiertos por `test-machine-authority.py`.

## Definition of Done

- [x] reconstrucción histórica contrastada;
- [x] `llms.txt` actual inspeccionado;
- [x] `llms-full.txt` actual inspeccionado;
- [x] autoridad machine-readable existente localizada;
- [x] contrato de concisión/paridad/prompt-injection comprobado;
- [x] Google Search Central 2026 revalidado;
- [x] ausencia de hueco real demostrada;
- [x] decisión `READY_NO_CODE · ALREADY_COVERED`;
- [ ] CI del HEAD final completamente verde;
- [ ] revisión de Claude antes de merge.

## Cierre

B.1 está cubierta. El valor futuro de `llms.txt` es la exactitud y la interoperabilidad con consumidores que decidan usarlo, no el volumen ni una mejora de ranking en Google. La implementación correcta hoy es no añadir código ni contenido redundante.