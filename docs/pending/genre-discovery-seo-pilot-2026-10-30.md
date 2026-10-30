# Encargo de producto/SEO: piloto de descubrimiento temático con valor propio

Estado: **BORRADOR, PROPUESTA SIN IMPLEMENTAR**. P2 de arquitectura de contenido.
Base: `f4a2ea43f` (30/10/2026). No es un fallo de indexación general.

## Evidencia y oportunidad

El catálogo ofrece 88 libros y usa enlaces de género como
`/recomendaciones/#genero=misterio-y-thriller`. Los fragmentos expresan estado
cliente de una misma página, no páginas HTML independientes con contenido
temático propio. No afirmar que Google no puede descubrir los libros: las fichas
y sus enlaces/sitemap ya existen.

Recuento sobre `data/reading-catalogue.json`: unir `libro_categorias.libro_id`
con libros en estado publicado, contar IDs distintos por categoría activa:

| Género | Libros |
|---|---:|
| Fantasía | 10 |
| Romance | 7 |
| Misterio y thriller | 10 |
| Narrativa | 8 |
| Aventuras | 9 |
| Biografías y memorias | 12 |
| Desarrollo personal | 10 |
| Cocina | 12 |
| Nutrición y bienestar | 7 |
| Cómic y novela gráfica | 6 |
| Infantil | 13 |

Existen guías propias `/recomendaciones/portal-fantasy-espanol/` y
`/recomendaciones/magia-con-coste/`: inventariarlas junto con Cuaderno antes de
proponer rutas nuevas y evitar competir con ellas por la misma intención.

## Encargo a la IA implementadora

1. Preparar mapa de intención/ruta y elegir solo 2–3 temas para un piloto según
   utilidad, calidad del catálogo y Search Console si está accesible. No inventar
   volumen de búsqueda ni prometer posiciones.
2. Diseñar páginas que ayuden a decidir: alcance y criterio de inclusión, para
   quién encaja cada selección, subgrupos útiles y diferencias verificables.
3. Distinguir catálogo bibliográfico de recomendación personal. No fingir lectura,
   «mejores», rankings ni experiencia del autor; respetar la política editorial.
4. Contenido propio y datos contrastados, no copiar sinopsis extensas ni añadir
   biografías de relleno para alcanzar una cifra de palabras.
5. Resultado útil sin JS: listado enlazado, H1/title/description distintivos,
   canonical propio, breadcrumbs y marcado coherente con contenido visible.
6. Integrar acceso desde catálogo/fichas/guías cuando corresponda y conservar los
   filtros como herramienta, no como sustituto del contenido editorial.
7. Usar constructores y registro público existentes: sitemap, Pagefind, navegación,
   límites de publicación, fechas y detección de rutas huérfanas.

## Aceptación y medición

- [ ] Inventario previo y plan de 2–3 páginas sin duplicar guías existentes.
- [ ] Propuesta de contenido/diseño revisable antes de producción masiva.
- [ ] Cada página resuelve una necesidad distinta y tiene evidencia de sus datos.
- [ ] Navegación móvil, filtros contextuales y fichas accesibles sin callejones sin salida.
- [ ] Sin contenido programático vacío, canonicals contradictorios ni hechos inventados.
- [ ] HTML sin JS, enlaces, sitemap, Pagefind, semántica y rendimiento comprobados.
- [ ] Si hay datos: baseline de consultas/entradas, seguimiento posterior del piloto;
      sin acceso a Search Console, registrar que el impacto SEO sigue sin medirse.
- [ ] CI y SHA publicado verificados por la IA implementadora.

No generar automáticamente once landing pages solo por tener cinco libros.
Esta PR es una propuesta de mejora, no evidencia de penalización ni de caída.
Otra IA continúa aquí con investigación editorial, diseño, implementación y entrega.
No fusionar el documento como trabajo terminado. Coordinar con #1004: ese encargo
mejora filtros móviles; este añade descubrimiento temático y contenido indexable.