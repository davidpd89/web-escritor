# KDBush v4.1.0: dependencia real de Supercluster cubierta (21/10/2026)

**P2 / [#668](https://github.com/davidpd89/web-escritor/pull/668)**. Se archivaron **sin cambios**:
- [`mourner/kdbush/index.js`](https://github.com/mourner/kdbush/blob/main/index.js) → [`research/vendor/kdbush/index.js`](index.js), blob Git `d2aac2bbb04a8dbd8fc20e341ca02591eedd8cca`.
- [LICENCIA ISC completa](https://github.com/mourner/kdbush/blob/main/LICENSE) → [`LICENSE.upstream`](LICENSE.upstream), blob Git `bf7a73179b91ee750383176b236c1e15cdc31bb1`. Copyright © 2026 Vladimir Agafonkin.
- Versión vista en [package.json upstream](https://github.com/mourner/kdbush/blob/main/package.json): **4.1.0**, export ESM, sin dependencias de runtime. Exactitud de copia y SHA **verificadas contra GitHub en esta ronda**.

**Por qué:** [Supercluster v9.1.0](https://github.com/mapbox/supercluster) (ya copiado literalmente en #668, ISC) importa `kdbush` para indexar puntos y agrupar pins. Hasta ahora su código archivado **no incluía esta dependencia**, impedía incluso plantear una integración offline completamente local sin instalarla.

**Forma de integración preferida:** en una PR posterior, instalar versiones exactas `supercluster@9.1.0`, `kdbush@4.1.0` con lockfile existente cuando sea imprescindible un mapa interactivo, o adaptar **solo la ruta de importación** en una copia aparte de `supercluster/index.js` a `kdbush/index.js`. **Nunca editar los originales vendorizados.** No copiar dependencias de desarrollo, no instalar MapLibre/Leaflet en la portada ni cargar mapas por defecto.

**No se ha lanzado JS ni test ni Actions**. El motor no tiene datos ni teselas y no se usa en la web. No confundir la licencia ISC de los algoritmos con la licencia/cartografía de sus teselas.
