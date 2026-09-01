# G.4 · Revalidación de producción — metadata inglesa sin contenido inglés

**Fecha:** 2026-08-30  
**Base:** `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
**Decisión:** `REJECT · SPANISH_CANONICAL_COHERENT · NO_EQUIVALENT_ENGLISH_URLS · AI_TRANSLATION_IRRELEVANT · NO_CODE`

## Estado real

La web canónica continúa siendo española: Home y superficies editoriales usan `lang="es"`, `og:locale="es_ES"` e `inLanguage: "es"`. No se ha verificado una familia equivalente de URLs inglesas ni una capa `hreflang` que represente contenido realmente localizado.

Esto coincide con C.9: no existe todavía un proyecto de traducción/internacionalización con derechos, alcance, owner y mantenimiento de paridad suficientemente verificados.

## Revalidación frente a Google

La documentación vigente de Google para versiones localizadas parte de una condición básica: existen **múltiples versiones de una página para idiomas o regiones diferentes**. `hreflang` sirve para relacionar esas variaciones reales.

Google también aclara que una página cuyo contenido principal sigue en el mismo idioma no se convierte en una versión lingüística distinta porque se traduzcan únicamente elementos secundarios. Por extensión, traducir solo title/meta/OG/JSON-LD no crea el producto inglés que esos metadatos prometerían.

## Por qué IA no cambia la decisión

Un modelo puede traducir texto, pero no resuelve:

- inexistencia de URL inglesa canónica;
- falta de contenido equivalente real;
- derechos/licencias;
- navegación y experiencia en inglés;
- paridad factual futura;
- revisión de ISBN, fechas, editorial, disponibilidad y claims;
- relación canonical/hreflang entre versiones.

La velocidad de traducción no justifica una arquitectura incoherente.

## Secuencia correcta si algún día se activa i18n

`proyecto editorial real → contenido equivalente → URL localizada → lang/canonical → hreflang recíproco → metadata/OG/JSON-LD localizados → QA/paridad`

No debe empezarse por la metadata.

## No implementar

- No meta description inglesa sobre URL española.
- No `inLanguage: en` en páginas españolas.
- No `og:locale:alternate` ornamental.
- No `hreflang` sin equivalente real.
- No landing inglesa thin para justificar metadata.
- No JSON-LD traducido aislado.
- No generación IA masiva de envoltorio semántico.

## Trigger de un trabajo futuro distinto

Solo cuando existan simultáneamente URLs inglesas reales, alcance editorial, derechos, responsable de revisión y mantenimiento de paridad. En ese escenario la IA podría ser tooling de borrador, no autoridad automática.

## Cierre

G.4 permanece `REJECT` tal como fue formulada. No hay una tarea técnica pendiente: el trabajo futuro nacerá de una internacionalización real, no de traducir metadatos sobre contenido español.