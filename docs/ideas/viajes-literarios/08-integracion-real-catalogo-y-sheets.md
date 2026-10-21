# 08 · Reutilizar importación de Sheets y publicador real, sin crear otro (21/10/2026)

Inspección directa de **main** tras la fusión de [#661](https://github.com/davidpd89/web-escritor/pull/661), **sin ejecutar scripts ni flujos**.

## 1. Qué está funcionando en el catálogo de libros (según código, no prueba en vivo)

- [scripts/import-reading-sheet.py](https://github.com/davidpd89/web-escritor/blob/main/scripts/import-reading-sheet.py) contiene **importación de 5 pestañas** llamadas `01_LIBROS`, `02_CATEGORIAS`, `03_PORTADAS`, `04_ENLACES`, `05_FUENTES`.
- Usa `values:batchGet` de Google Sheets y solo conecta la hoja en modo `--live` con `GOOGLE_SHEETS_ACCESS_TOKEN`; también lee un snapshot JSON versionado. `--check` permite comparar lo calculado contra el catálogo actual. El proceso no publica directamente los cambios que se limiten a un candidato.
- El importador separa los datos recibidos de su **review** en `data/reading-import-review.json`, preserva ISBN publicados por la ingesta y evita suplantar registros existentes. Este patrón es importante para evitar que el atlas borre libros.
- [docs/catalogo-lecturas-automatizacion.md](https://github.com/davidpd89/web-escritor/blob/main/docs/catalogo-lecturas-automatizacion.md) documenta que la ingesta puede ejecutarse a las **06:30 UTC** bajo controles y que el pipeline principal **no usa LLM**; leer estado de Actions/configuración real en fase de desarrollo antes de asumir que una ejecución concreta ha ocurrido.
- [data/reading-intake-config.json](https://github.com/davidpd89/web-escritor/blob/main/data/reading-intake-config.json) tiene `enabled=true`, `autopublish=true`, `max_new_books=5`, `max_requests=80`, `request_delay_seconds=1.5`; **no tocar configuración en esta PR**. Importar un lugar no debería consumir el presupuesto de llamadas de libros.

## 2. Lo que NO se puede hacer simplemente

- [scripts/refresh-reading-catalogue.py](https://github.com/davidpd89/web-escritor/blob/main/scripts/refresh-reading-catalogue.py) es un **writer de catálogo de lectura**, no un publicador genérico de cualquier archivo. Al construir añade a git una lista concreta de carpetas y ejecuta validaciones específicas de libros.
- [scripts/publish-reading-refresh.py](https://github.com/davidpd89/web-escritor/blob/main/scripts/publish-reading-refresh.py) comprueba `allowed_path(path)` y **rechaza por diseño cualquier ruta diferente** de `data/reading-...`, `recomendaciones/...`, `editoriales/...`, ciertas portadas/audio y `pagefind/...`.
- No podemos añadir `atlas-literario/...`, `data/atlas-...` o `assets/atlas-...` al lote existente sin **cambiar de forma explícita esta política**, el QA, sus pruebas de seguridad y los pasos que preparan build/sitemap/indexación. Si se metieran en la rama de artefactos, la publicación fallaría por diseño.
- Tampoco se puede enlazar una fila `obra` con `reading_book_id` basándose únicamente en coincidencia textual de título. Resolver IDs y ediciones correctamente; el nuevo atlas lee referencias al catálogo, **no edita precios ni portadas del catálogo**.

## 3. Opciones de integración técnica futura

**A — Recomendación: un único proceso de publicación con dos módulos independientes de ingestión.**
1. Ingesta libros se mantiene sin modificaciones funcionales, con sus límites.
2. Nuevo `atlas-discover`/ `atlas-review-export` alimenta **solo candidatos y snapshots aprobados**.
3. Coordinación en un solo worker o mecanismo serial/lock: concatena artefactos de ambos **solo tras validación por separado**. Ampliar `allowed_path` explícitamente para rutas atlas y pruebas contra path traversal, borrados, HTML inyectado y acceso a privados. Asegurar que `--check` del Atlas tiene la misma disciplina que el catálogo.
4. Escritura de PR controlada, gates por SHA, no dos merges solapados. Cambios a generador web en PR de implementación aparte.
5. No tocar `autopublish` existente como parte de un experimento de contenido.

**B — Alternativa de riesgo menor en primera publicación:** Atlas recibe snapshots aprobados por **PR manual**, sin cron ni permisos del writer de lectura. Permite probar 3–5 fichas y accesibilidad; cuando haya volumen y métricas, unir la orquestación a la ingesta diaria. **Más segura para el primer lanzamiento** aunque menos automática.

**Decisión recomendada por etapas:** B para pruebas iniciales; A para crecimiento de verdad después de comprobar que el esquema, el mapa y QA son estables. Ninguna se implementa ahora.

## 4. Sheets: adaptar patrón, no clonar su esquema

- Reutilizar enfoque `batchGet`, snapshot local, revisión separada, `--check`, conservación de registros ajenos, errores de cabecera duplicada y bloqueos al faltar referencias.
- Crear hoja de cálculo **propia del Atlas** o grupo de pestañas claramente aislado, acordado con usuario. No meter `01_DESTINOS` dentro del contrato de libros sin versión y responsable de datos.
- Campos base que deben existir por entidad: `id`, `estado`, `fuente_id`, `fecha_verificacion`, `ultima_revision`, `aprobado_por`, `licencia_dato`, `notas_internas` (nunca exportarlas a público).
- **Lista mínima de seis pestañas** para el MVP de captación: `DESTINOS`, `LUGARES`, `OBRAS_REFERENCIAS`, `RELACIONES`, `FUENTES`, `IMAGENES`. `RUTAS`, `RUTA_PARADAS`, `AUTORES` y revisiones se suman progresivamente. Mantener cabeceras exactas de [01-modelo-datos-drive.md](01-modelo-datos-drive.md) al fijar contrato final.
- `LUGARES` y `RELACIONES` deben poder ser muchos-a-muchos entre destinos, libros, autores y adaptaciones (una ciudad puede tener muchos puntos y un sitio aparecer en varios libros).
- En la exportación: **no** pasar fórmula de Sheets, contenido HTML, URL de imagen arbitraria, tokens o comentario interno directamente al HTML. Sanitizar desde datos de terceros hasta el frontend.

## 5. QA adicional al fusionar arquitecturas (futuro)

- Comprobar que el writer de libros aún rechaza `data/secrets.json`, `../`, renombres, archivos HTML inesperados y cualquier ruta nueva no registrada.
- Tests de simultaneidad: una publicación automática de libros en curso no puede solaparse con otra publicación del Atlas, ni crear dos cambios concurrentes de `sitemap.xml`, `data/content-registry.json` y `pagefind/`.
- Regresiones de `/recomendaciones/` con todos los filtros, portadas y enlaces Amazon; el Atlas no debe modificar estados de lectura.
- Una fila de lugar aprobada sin relación revisada produce ficha de sitio cultural **solo** si tiene categoría intrínseca válida; nunca se inventa una relación libro-lugar.
- Ingesta de un dataset público caído: continúa el último snapshot bueno y **no despublica** sitios por no recibir datos ese día.
- Fichas nuevas deben existir en salida antes de que el índice las enlace; resolver antiguo problema del generador Atlas.
- `dry-run` obligatorio en primera tanda, sin Actions reales hasta orden del propietario.

**Esta PR documenta la integración; no realiza escrituras en Google Sheets, main o pipelines de despliegue.**
