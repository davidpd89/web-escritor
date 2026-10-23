# Código libre adicional archivado para mapas de muchos lugares (21/10/2026)

**Hija [#668](https://github.com/davidpd89/web-escritor/pull/668), dependiente lógicamente de [ADR-000](https://github.com/davidpd89/web-escritor/pull/666)**. Son copias **literalmente iguales al upstream**; no están importadas en el runtime ni ejecutadas. Licencia completa de cada repositorio preservada al lado de los archivos.

## 1. Simplify.js — simplificar líneas de rutas sin cargar kilómetros de geometría

- Upstream: [mourner/simplify-js](https://github.com/mourner/simplify-js).
- Código `research/vendor/simplify-js/simplify.js` — blob SHA **`339c84f53d0dd81348774d4f8f691e36c7ca86b6`** (original `simplify.js`).
- Licencia `research/vendor/simplify-js/LICENSE.upstream` — blob **`bda6bcc2dc1f5ac029c03750c72c07b5ba8b4f82`**. Licencia **BSD-2-Clause**, copyright (c) 2017 Vladimir Agafonkin; conservar aviso y condiciones.
- Uso: simplificar una línea **ya correctamente trazada** para representar rutas más ligeras (número menor de vértices, menor GeoJSON). No **calcula recorridos ni tiempos** ni da derecho a teselas; tampoco elegir tolerancia sin comprobar distorsiones y accesibilidad. Es opcional para la fase tardía de rutas P9.

## 2. Supercluster — agrupación de puntos cuando el usuario abre mapa

- Upstream: [mapbox/supercluster](https://github.com/mapbox/supercluster), paquete v9.1.0 según `package.json` inspeccionado.
- Código `research/vendor/supercluster/index.js` — SHA **`460e2a7568f7156e69ca3f7283dd158bc43c1e3f`**.
- Tipos `research/vendor/supercluster/index.d.ts` — SHA **`20aca35eb7fec2e7028093fc93038fb36836ded5`**.
- Licencia `research/vendor/supercluster/LICENSE.upstream` — SHA **`21b48915f91320709a294274dfa418a1491455e7`**, **ISC**, copyright (c) 2024 Mapbox. Permite copia y modificación conservando copyright/permiso.
- **DEPENDENCIA YA VENDORIZADA, pero NO cableada**: `kdbush@4.1.0` ISC aparece literalmente en `research/vendor/kdbush/index.js` con licencia en `LICENSE.upstream` (ver su README). Para usar `Supercluster` queda resolver su import ESM `from 'kdbush'` mediante paquete fijado/lockfile o adaptación en copia separada, más types GeoJSON para TypeScript. El `index.js` de Supercluster **aún no funciona por sí solo** dentro de nuestra web. Para implementar mapa interactivo, **preferir paquete instalado a versión fija** (lockfile y auditoría) y cargarlo **solo al entrar en vista de mapa**, no en la home ni listados. `Supercluster` no geocodifica, no prueba novelas ni añade mapas base; solo agrupa GeoJSON Point.

## 3. Decisión de dependencia y rendimiento

**Página de destino y libro**: HTML estático + filtros ligeros [#672](https://github.com/davidpd89/web-escritor/pull/672). **Mapa interactivo**: cargar Leaflet/MapLibre + clustering en solicitud posterior; por defecto mapa externo o WebP estático con derechos de uso comprobados. El software no paga ancho de banda ni resuelve licencias del mapa. Para rutas, no mostrar línea sugerida a pie sin proveedor o trazado real comprobado.

**Por qué código y licencia por separado:** licencia de **software** ≠ licencia de datos Overture/OSM ≠ fotos/títulos/cubiertas. No copiar material sin LICENSE como si código público equivaliese a dominio público.

## 4. Comparación con StoryMapJS: licencia inconsistente en origen

- [NUKnightLab/StoryMapJS/LICENSE](https://github.com/NUKnightLab/StoryMapJS/blob/master/LICENSE): **Mozilla Public License 2.0** según archivo completo inspeccionado en GitHub.
- [NUKnightLab/StoryMapJS/package.json](https://github.com/NUKnightLab/StoryMapJS/blob/master/package.json): campo **`license: ISC`**, igual que su `pyproject.toml`. Son afirmaciones incompatibles sobre los términos del código. **No lo hemos copiado** ni dependido de él hasta aclaración de mantenedores; sí sirve como inspiración de navegación narrativa y rutas sobre mapa.
- Además el `package.json` menciona `leaflet@^0.7.2`, una dependencia antigua; no incluir la aplicación completa en la web estática por encima del diseño existente.

## QA pendiente

- [x] Código/avisos archivados sin modificar.
- [ ] Verificar copia byte a byte frente a upstream y registrar revisión; el almacenamiento con mismo blob SHA permite comparación.
- [ ] Instalar dependencias solo en PR de implementación posterior y ejecutar tests autorizados.
- [ ] Comparar tamaño gzipped de mapa con/sin puntos, consumo móvil, CLS/INP/JS y CDN de teselas; no declarar mejora medida sin hacerlo.

## 21/10/2026 — revisión adicional de dependencias y alternativas

- [KDBush 4.1.0](https://github.com/mourner/kdbush): se añadió [código fuente ISC literal](kdbush/index.js) y [LICENCIA completa](kdbush/LICENSE.upstream), SHA originales verificados (ver [README](kdbush/README.md)). **Se resuelve el hueco documental** de la dependencia runtime directa de Supercluster, no se ejecuta ni conecta el módulo.
- Nuevas referencias encontradas: [Akhand](https://github.com/CodeRustyPro/akhand) ofrece 9.057 registros de lugares narrativos en su release depurada, con API de país/ciudad/autor/género/año y GeoJSON; [Literary Atlas](https://github.com/rostam/literary-atlas) representa ficción con ubicación y época, distingue sitios ficticios y relata por qué algunos libros quedan SIN pin. Ambos repositorios inspeccionados **sin LICENSE en la raíz**; **NO copiar su código ni sus corpus** sin autorización explícita y verificación de permisos. Ideas de UX sí se pueden analizar en #670.
