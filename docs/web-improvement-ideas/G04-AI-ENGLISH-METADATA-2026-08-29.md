# G.4 · Metadatos ingleses asistidos por IA sin contenido inglés

**Estado histórico final de PR #135:** `REJECT`  
**Etapa intermedia:** `DEFERIR`  
**Decisión:** no publicar meta descriptions/JSON-LD/OG en inglés mientras no existan páginas equivalentes reales en inglés.  
**Naturaleza de esta PR:** documentación; no añade i18n ni metadatos.

## 1. Hipótesis original

G.4 proponía generar con IA y revisión humana metadescripciones y JSON-LD en inglés para una futura capa internacional, separándolo expresamente de traducir la obra literaria.

La investigación terminó corrigiendo la premisa: traducir solo metadatos no crea una versión inglesa del sitio. Puede sugerir a buscadores, redes y personas que existe un contenido equivalente que en realidad sigue estando únicamente en español.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Traducir metadata, no literatura, con IA + revisión. |
| Revisión 108/108 | `REJECT` | Metadatos ingleses sin páginas inglesas equivalentes generan incoherencia. |
| Matriz operativa | `DEFERIR` | Esperar a una internacionalización real. |
| Autoridad final | `REJECT` | No crear expectativa falsa; traducir cuando exista versión real. |
| JSON final | `REJECT` | Estado machine-readable definitivo. |
| Revalidación independiente | mantenido | N.1–N.3 también siguen diferidos hasta existir contenido equivalente. |

La diferencia `DEFERIR → REJECT` importa: no hay una tarea técnica pendiente que simplemente esté esperando turno. La propuesta, tal como estaba formulada —metadata inglesa sobre páginas españolas—, se descarta. Solo un producto distinto y real (páginas inglesas) puede abrir un trabajo nuevo.

## 3. Estado actual de `main` revalidado el 29/08/2026

La Home vigente declara:

- `<html lang="es">`;
- `og:locale="es_ES"`;
- `inLanguage: "es"` en `WebSite`, `WebPage` y entidades;
- título, descripción y contenido editorial en español.

No se ha encontrado una versión equivalente inglesa que justifique `hreflang`, `og:locale:alternate` ni metadata inglesa paralela.

Esto es coherente con las autoridades relacionadas:

- **C.9:** traducción/adaptación `DEFER` hasta existir proyecto/licencia real;
- **N.1:** `hreflang` solo con URLs equivalentes reales;
- **N.2:** locale alternativo sin URLs localizadas no aporta;
- **N.3:** glosario de traducción interno solo cuando exista workflow real.

## 4. Por qué la IA no cambia la decisión

Que un modelo pueda traducir rápido y barato no resuelve:

- inexistencia de una URL inglesa canónica;
- equivalencia editorial entre versiones;
- revisión factual de nombres, premios, editoriales y disponibilidad;
- mantenimiento de paridad cuando cambie el original;
- navegación y experiencia en el idioma;
- derechos/licencias si se traduce contenido protegido;
- expectativa del usuario que llega desde un snippet en inglés.

La facilidad de generación es irrelevante si falta el producto al que los metadatos deberían describir.

## 5. Trigger de reevaluación

Solo reabrir si existe simultáneamente:

1. una decisión real de publicar contenido en otro idioma;
2. URLs equivalentes y mantenibles;
3. alcance editorial definido (qué se traduce y qué no);
4. derechos/licencia cuando proceda;
5. responsable de revisión humana;
6. estrategia canónica/hreflang coherente;
7. mecanismo de mantener paridad factual.

En ese escenario, la IA podría ser tooling de borrador, nunca autoridad automática.

## 6. Implementación correcta si algún día se activa

La secuencia debería ser:

`contenido equivalente real → URL/canonical → idioma de documento → hreflang/paridad → metadata/OG/JSON-LD localizados → QA`

No al revés.

Cada traducción generada debe revisar como mínimo:

- nombres propios y grafías canónicas;
- títulos oficiales de obras;
- fechas;
- ISBN/editorial;
- premios y matices de atribución;
- URLs de compra/disponibilidad;
- claims no presentes en el original;
- `inLanguage`, `og:locale`, canonical y alternates.

## 7. Qué no hacer

- No añadir una meta description inglesa a una URL cuyo contenido es español.
- No poner `inLanguage: en` en entidades/páginas españolas.
- No añadir `og:locale:alternate` como señal ornamental.
- No crear `hreflang` sin equivalente real.
- No traducir solo JSON-LD esperando descubrimiento internacional.
- No inventar una landing inglesa vacía/thin para justificar metadata.
- No asumir que revisión humana significa que la arquitectura deja de ser incoherente.

## 8. Definition of Done de esta idea

G.4 queda correctamente cerrada mientras:

- [x] la web española mantiene metadata española coherente;
- [x] no se publican alternates ingleses ficticios;
- [x] no se presenta la generación IA como sustituto de i18n;
- [x] la reevaluación queda ligada a contenido equivalente real.

Si aparece i18n real, debe abrirse una nueva implementación basada en ese estado futuro, no “activar G.4” literalmente.

## 9. Trazabilidad #135

Revisados:

- `IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — rechazo por incoherencia.
- `IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `DEFERIR`.
- `data/web-improvement-decisions-2026-08-28.json` — final `REJECT`.
- `PR135-FINAL-AUTHORITY-2026-08-28.md` — metadata inglesa sin páginas inglesas crea expectativa falsa.
- `PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — G e internacionalización mantenidas.
- C.9/N.1/N.2/N.3 — autoridades relacionadas revisadas.
- pasadas/overrides posteriores — sin evidencia que justifique metadata inglesa aislada.

## 10. Cierre

La decisión no es “IA mala para traducción”. Es más concreta: **los metadatos deben describir contenido que realmente existe**. Hasta que haya una versión inglesa real, generar su envoltorio semántico sería crear una promesa que la página no cumple.