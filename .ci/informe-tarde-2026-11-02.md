# Informe de la tarde del 02/11/2026: catálogo de lecturas

Sigue a `.ci/informe-noche-2026-11-02.md`.

## Cambios (PR)
- Fusionadas: #1060 (títulos SEO con autor), #1061 (GEO), #1063 (textos de orientación en 181 fichas), #1064 (informe de la noche) y #1052 (caja de formatos y barrido de precios robusto).
- #1065: la ingesta ya no publica fichas que no admiten al menos dos bloques de orientación (`reading-texts.payload`, `MIN_BLOCKS`, con `para_quien` obligatorio). Esos libros quedan en `pendiente_datos` con el motivo «Datos insuficientes para orientar al lector» y se reintentan a los 3 días. Lleva un test nuevo, que falla sin el arreglo.

## Verificaciones
- `unittest discover -p 'test_reading*.py'` en la rama de la #1065: 292 tests OK.
- Test nuevo comprobado en los dos sentidos: falla sin el arreglo y pasa con él.

## Fallos
- Run 41430716548 de `reading-catalogue-sync` (lanzado a mano tras la #1063):
  - la ingesta aceptó 60 libros y los precios se actualizaron (62 libros, 123 peticiones, 63 formatos);
  - la puerta de tests falló en `test_every_published_book_gets_at_least_two_modules` con isbn-9791388042669, que solo admitía `para_quien`, y no se publicó nada;
  - la causa estructural la corrige la #1065.

## Pendientes
- Relanzar `reading-catalogue-sync` tras la #1065 y revisar los libros nuevos, `sin_oferta` y `formatos_compra`.
- Textos de orientación para los libros nuevos (`scripts/reading-texts.py`, en local con GPT).
- IndexNow para las fichas con textos nuevos, si el sync no lo hace solo.
- Prioridades de GPT que requieren a David: ver el informe de la noche.
- Mejora posible: `descripcion_breve` es generada e infla la longitud de `source_text`, que decide la familia y `encaje_documentado`. Valorar contar solo la sinopsis editorial.
