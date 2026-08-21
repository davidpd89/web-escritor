# 41 — CLAUDE IMPLEMENTATION HANDOFF V1

`CLAUDE_IMPLEMENT_READY`: **YES_FOR_STAGING_IMPLEMENTATION**
`MERGE_READY`: **NO**
`PRODUCTION_READY`: **NO**

Repositorio: `davidpd89/web-escritor`
Única rama de trabajo autorizada para implementación: `implementacion-web-2026`
HEAD auditado por este paquete: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`
`main`: NO TOCAR.

**Sincronización 21/08/2026:** baseline reaudidado a `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`. El delta desde `755d4ef71de436f72dd5736d726a4b48523b2336` solo añade contratos de registry/navigation/retención UX y CI; no modifica las páginas/familias auditadas. `data/content-registry.json` y `data/navigation.json` del repo pasan a ser autoridad de findability durante la integración. Jaula está fuera de ambos en el HEAD actual. Al crear la ruta en staging entra primero solo en `content-registry.json` como `status:noindex`/`searchIndex:false`/`sitemap:false`; `navigation.json` continúa sin referenciarla hasta promoción pública aprobada.

## Qué significa «listo para Claude»

Claude puede materializar el sistema V1 en la rama de implementación/staging **sin inventar familias visuales, patrones, paleta, motion, rutas o fallbacks**. No significa publicar ni mezclar a `main`.

Antes de cualquier write Claude debe:

1. leer `IMPLEMENTATION-READINESS.md`, este fichero, `REFERENCIAS-HUMANAS.md`, `SIGNATURE-SYSTEM.md`, `ROUTE-INVENTORY.md` y los `*-preservation.json`;
2. comprobar el HEAD actual de `implementacion-web-2026`;
3. si difiere de `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`, comparar el delta y reauditar los contratos/rutas/builders/assets tocados; **no resetear ni sobrescribir trabajo nuevo**;
4. ejecutar antes de escribir `scripts/validate_extension.py` y `scripts/validate_lab.py`; los validadores de preservación se ejecutan **después de materializar cada candidato** y antes de aceptar el commit de esa familia;
5. trabajar en commits pequeños exclusivamente en `implementacion-web-2026`;
6. respetar builders: las páginas de herramientas generadas se cambian en `scripts/build-writer-tools.py`/fuente correspondiente y se regeneran, no se parchea solo el HTML generado;
7. no hacer merge, no tocar `main` y no desplegar producción.

## Orden exacto de implementación

0. Gate de drift + snapshot del HEAD.
1. Montar lab aislado/noindex.
2. Shell/tokens/base/Explorar.
3. Gate 0 sin assets.
4. Home A/B y seleccionar UNA por QA; nunca mezclar.
5. Libro/Manecillas.
6. Libro/Samuel con `book-samuel.html` + `samuel-preservation.json`.
7. Libro/Jaula en staging con `book-jaula.html` + `jaula-preservation.json`; mantener fuera de producción/sitemap hasta pasar gates.
   - tras crear el fichero de ruta, registrar `work-jaula` como `noindex` en `data/content-registry.json`; no añadir a `data/navigation.json` todavía; ejecutar `scripts/check-navigation-coverage.py`.
8. Libros index.
9. Cuaderno + artículo.
10. Autor.
11. Premios con `awards.html`; Prensa sigue como familia distinta.
12. Eventos + Ferias.
13. Herramientas hub + herramienta piloto; después propagar a las 17 usando los builders cuando corresponda.
14. Reference index/detail (Editoriales, Convocatorias, Recomendaciones, Metodología, Recursos).
15. Book companions/excerpts (Noveris, clubes, fragmentos).
16. Wayfinding/Empieza aquí/Mapa.
17. 404/Privacidad/Aviso legal/AI y secundarias.
18. Aplicar solo signatures aprobadas.
19. Ejecutar preservación contra los HTML candidatos + browser QA + Lighthouse/a11y/link/schema + benchmark 28.
20. Solo entonces evaluar `MERGE_READY`.

## Prohibiciones

- no Tailwind/component library para «resolver rápido»;
- no convertir bloques en tiles repetidos;
- no inventar paleta;
- no glass, glow, purple/blue AI, bento o pills;
- no dark mode como concepto rector;
- no custom cursor, magnetic buttons o scroll-jacking;
- no Three/WebGL/GSAP/Lenis global por comodidad;
- no mezclar Home A y B;
- no inventar assets, frases, sinopsis, premios, ratings, retailers o rutas;
- no borrar HTML/SEO/schema/anchors para limpiar una captura;
- no reescribir scripts funcionales sin paridad demostrada;
- Jaula está autorizada para staging: no enlazarla ni incluirla en sitemap/producción hasta que la ruta real responda 200 y pase `jaula-preservation.json`, SEO/schema y cobertura de navegación;
- no hand-edit de salida generada de Herramientas si existe builder autoritativo.

## Contratos especiales

### Samuel
Usar `book-samuel.html`, `css/samuel.css`, `data/samuel-preservation.json`.
No heredar la piel de Manecillas. Firma: **umbral / dos registros / ledger técnico / corriente de reseñas**. El asset 3D actual es fallback verificado, no la identidad. Preservar Book/WebPage/FAQ/reviews/quiz/retailers/anchors y todo el texto indexable.

### Jaula
Usar `book-jaula.html`, `JAULA-PUBLIC-SPEC.md` y `data/jaula-preservation.json`. Ejecutar `python scripts/check_preservation.py --jaula <ruta-candidata>` después de materializarla. Fuente canónica: manuscrito Drive `1bfo_20JoPw3W_oHK8k-G1rd3v-K1Jfvx`; publicar como `En desarrollo` con capítulo 1 íntegro. No inventar portada, fecha, editorial, ISBN, precio, retailers ni género comercial. El scaffold es noindex de lab; la ruta solo se promociona tras staging 200 + gate de navegación.

### Premios
Usar `awards.html`, `css/awards.css`, `data/awards-preservation.json`.
Firma: **archivo cronológico de evidencia**. Premios formales, selección editorial y trayectoria son capas semánticas distintas. Publicar un libro o recibir una reseña no se representa como premio.

### Herramientas
17 utilidades reales. Firma: **instrumentarium tipográfico**. La UX cambia; algoritmos, hooks, labels, help, privacidad, validaciones y builder contracts se preservan. No dashboard, no mosaico SaaS.

## Motion

La composición estática se aprueba antes que motion. View Transitions solo como progressive enhancement para pares semánticos. Scroll timelines detrás de `@supports`. La ruta viva no depende del SVG. Reduced-motion y no-JS son completos.

## Evidencia que Claude debe devolver tras staging

Tabla: `ruta/familia | preservación | responsive | teclado | no-JS | reduced-motion | schema | links | CWV | resultado`.

Si una fila no puede demostrarse: FAIL, no «parece correcto».

## Gates humanos posteriores

- elegir Home A o B tras capturas reales;
- aprobar identidad visual final y escenas fuertes;
- verificar retailers comerciales en el momento de salida;
- revisar Jaula en staging y autorizar su promoción/sitemap solo después de comprobar capítulo, SEO/schema, navegación y ausencia de metadata inventada;
- autorizar merge/main/producción.

El objetivo de Claude es **materializar un diseño decidido y demostrar paridad**, no rediseñarlo durante la implementación.
