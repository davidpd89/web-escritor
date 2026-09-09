# Google Knowledge Panel + Search Profile — David Porto Díaz

Fecha de revisión: 2026-09-07

Estado: `RESOLVED · CLAIMED_BY_AUTHOR · CLOSED`

## Cierre (2026-09-09)

David confirmó directamente que ya completó el paso de verificación de identidad de Google (el que pide documento de identidad) y reclamó el panel/entidad por su cuenta — ese paso, por su naturaleza, solo lo puede hacer él, nunca esta sesión.

Verificado en vivo que existe una entidad real en el Knowledge Graph de Google para "David Porto Díaz escritor" (aparece una tarjeta de "Información" con fecha de nacimiento junto a los resultados). Nota aparte, no bloqueante para este cierre: esa fecha de nacimiento visible en Google coincide con el mismo dato sin referencias ya señalado en Wikidata (`docs/tracking/wikidata.md` / #398) — sigue siendo una decisión de privacidad del autor, no algo para tocar aquí.

Sin más acción pendiente en esta rama.

## Objetivo

Comprobar si Google reconoce a David Porto Díaz como entidad con Knowledge Panel y/o Search Profile, reclamar gratuitamente cualquier superficie elegible y corregir identidad, obras y enlaces mediante las vías oficiales.

## Knowledge Panel

Google confirma que los paneles de conocimiento:
- se generan automáticamente a partir del Knowledge Graph y múltiples fuentes web;
- no se crean manualmente bajo demanda;
- pueden reclamarse por la persona/entidad representada cuando Google ofrece la opción;
- permiten sugerir correcciones tras verificar identidad.

Fuentes:
- https://support.google.com/knowledgepanel/answer/9163198?hl=es
- https://support.google.com/knowledgepanel/answer/7534902?hl=es
- https://support.google.com/knowledgepanel/answer/9787176?hl=es

Google documenta actualmente como posibles vías de verificación propiedades/perfiles oficiales como Search Console, YouTube, X/Twitter o Facebook.

## Search Profile — hallazgo relevante de 2026

Google documenta ahora un `Search profile` para determinados creadores, publishers o brands con Knowledge Panel generado automáticamente. Puede agregar contenido de plataformas como YouTube, Instagram, TikTok y X.

Si está disponible y se reclama, permite:
- fijar hasta 8 publicaciones;
- añadir hasta 8 enlaces;
- sugerir cambios de nombre y bio;
- compartir contenido;
- consultar insights de rendimiento en Search y Discover.

Fuente oficial:
- https://support.google.com/websearch/answer/16905608

Para David esta superficie puede tener valor directo si existe: permite priorizar web oficial, libros y contenido relevante sin depender solo de lo que Google seleccione automáticamente.

## Datos canónicos para verificar

- Nombre: David Porto Díaz
- Web: https://davidportodiaz.com/
- Wikidata: Q139678851
- ORCID: 0009-0005-9089-3782
- Amazon Author: B0GZFP1JV3
- Goodreads Author: 66843136
- Samuel entre mundos
- Las manecillas del recuerdo

No usar premios, fechas personales u otros datos para completar el panel si no están respaldados por fuentes públicas adecuadas.

## Procedimiento Claude

### A. Descubrimiento
1. Buscar `David Porto Díaz` en Google con sesión autenticada.
2. Repetir en incógnito y en móvil/escritorio.
3. Distinguir Knowledge Panel real de simples módulos de resultados/perfiles sociales.
4. Comprobar homónimos.

### B. Knowledge Panel
1. Si existe, guardar captura/estado inicial.
2. Comprobar si aparece `Registrarse como responsable de este panel de información` / `Claim this knowledge panel`.
3. Reclamar mediante la cuenta/propiedad oficial más fuerte, preferentemente Search Console cuando Google la ofrezca.
4. Revisar nombre, foto, descripción, ocupación, web, perfiles y obras.
5. Enviar correcciones solo con fuentes públicas verificables.

### C. Search Profile
1. Comprobar si existe `View Search Profile` / equivalente junto al panel.
2. Si existe, reclamarlo.
3. Revisar bio y nombre.
4. Añadir enlaces de alto valor, priorizando web oficial y páginas canónicas de los libros cuando la UI lo permita.
5. Elegir publicaciones destacadas solo si ayudan a lectores: lanzamiento de Manecillas, ficha del libro, fragmento, Samuel, etc.; no llenar ocho slots por llenar.
6. Registrar insights iniciales para comparar después.

## Coordinación de entidad

Contrastar cualquier dato con:
- #398 Wikidata
- #396 Amazon Author Central
- #397 Goodreads
- #408 ORCID
- #420 VIAF
- #421 ISNI
- #405 Google Books

No crear perfiles externos artificiales solo para aumentar `sameAs`.

## Posibles cambios en la web

No hace falta tocar código por adelantado. Solo si la auditoría revela una URL/identificador oficial nuevo o una inconsistencia real:
- actualizar `Person.sameAs`/owner factual;
- corregir datos estructurados;
- ejecutar CI/QA.

## Criterio de cierre

`KNOWLEDGE_PANEL_STATE_RECORDED · CLAIMED_IF_AVAILABLE · SEARCH_PROFILE_STATE_RECORDED · SEARCH_PROFILE_CLAIMED_IF_AVAILABLE · IDENTITY_DATA_REVIEWED · CORRECTIONS_SUBMITTED_IF_NEEDED · NO_ARTIFICIAL_CREATION`
