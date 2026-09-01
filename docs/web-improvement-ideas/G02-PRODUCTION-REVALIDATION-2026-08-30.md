# G.2 · Revalidación de producción — IA para borradores de clubes de lectura

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `CONDITIONAL · GENERIC_CLUB_NEED_ALREADY_SOLVED_DETERMINISTICALLY · AI_ONLY_FOR_SPECIFIC_PRIVATE_EDITORIAL_DRAFT · NO_RUNTIME`

## Estado real

La necesidad general que podía motivar G.2 ya tiene una solución mejor y más segura en `main`: `/clubes-de-lectura/preparar-sesion/` existe y se presenta expresamente como **«Herramienta gratuita · sin IA»**. La página usa `connect-src 'none'` y explica que los datos se procesan completamente en el navegador.

Por tanto no procede crear un generador público por IA, un endpoint nuevo ni un flujo de subida de textos.

## Autoridad editorial de Drive

`45_CONSTRUCTOR_SESION_CLUB_LECTURA_INVESTIGACION_E_IMPLEMENTACION_2026-08-18.md` adopta deliberadamente un preparador determinista y descarta para el producto general el enfoque de subir una obra y generar preguntas con un modelo. El owner aprobado:

- compone sesiones de 30/60/90 minutos;
- usa bancos editoriales propios y configuración reproducible;
- no usa `fetch`, XHR, storage, cookies propias ni APIs externas;
- no persiste título, autor o temas;
- no crea páginas SEO programáticas por libro;
- mantiene separadas las guías específicas de obra propia.

Drive también contiene un ejemplo específico para Manecillas, pero un ejemplo no constituye autorización de publicación ni activa por sí solo un workflow IA.

## Qué queda vivo de G.2

G.2 solo conserva utilidad como **tooling editorial privado y puntual** cuando exista una pieza específica aprobada y una persona responsable quiera acelerar un primer borrador.

Ese uso exige:

1. pieza editorial real y owner identificado;
2. fuentes/canon delimitados;
3. rights/privacy gate compatible con el proveedor;
4. no enviar manuscritos u obra protegida completa sin necesidad/autorización;
5. revisión humana sustantiva de canon, spoilers, preguntas y atribuciones;
6. output tratado como borrador, nunca como autoridad ni autopublicación;
7. publicación mediante el owner editorial normal.

## No implementar

- No IA en `/clubes-de-lectura/preparar-sesion/`.
- No vector DB/embeddings.
- No upload de PDF/EPUB/DOCX.
- No almacenamiento de inputs de lectores.
- No generación automática de guías indexables por títulos ajenos.
- No CI que genere o publique preguntas.
- No duplicar el motor determinista existente.

## Trigger de reapertura

Solo abrir trabajo adicional si existe una guía específica aprobada y el borrador asistido aporta ahorro medible frente a redactarla directamente. Incluso entonces, la vía preferida es workflow privado/manual, no feature pública.

## Cierre

La revalidación no rechaza IA editorial puntual. Rechaza convertirla en producto público cuando el problema general ya está resuelto de forma determinista, privada y más mantenible.