# A.5 · Enlaces salientes a fuentes de autoridad

Fecha de reconstrucción: 2026-08-29  
Idea original: añadir citas/enlaces salientes a fuentes externas prestigiosas donde sea natural, presentándolo como mejora E-E-A-T/SEO.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado de esta PR: documentación/criterio condicional; no ordena un rollout sitewide.

## Veredicto reconciliado

**CONDITIONAL.**

Enlazar una fuente primaria puede mejorar verificabilidad, contexto y confianza **cuando una afirmación concreta lo necesita**. #135 rechazó convertir esa práctica en una táctica mecánica de SEO/E-E-A-T o en una política de “añadir enlaces de autoridad” a todas las páginas.

La versión anterior de esta PR decía `IMPLEMENTAR COMO POLÍTICA`. Eso era más fuerte que la autoridad histórica final. La decisión correcta es:

```text
hay hecho/afirmación externa que necesita evidencia → citar la mejor fuente
no existe esa necesidad → no añadir un enlace por cumplir A.5
```

## 1. Regla de reconstrucción

Esta PR usa directamente el corpus de #135 en `8e72321...`. Conserva hipótesis, fuentes, estados intermedios, decisión final, relación con A.4, anti-patrones y cualquier diseño técnico que sobreviva al gate condicional.

## 2. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` planteaba:

> añadir citas/enlaces a fuentes externas de prestigio —editoriales, prensa literaria, otros autores— porque el “outbound linking” a fuentes fiables seguiría siendo señal de calidad E-E-A-T.

La parte problemática era presentar el outbound linking como una palanca directa de ranking/autoridad. La parte válida era la verificabilidad.

## 3. Evolución cronológica en #135

### 3.1 · Primera revisión → `CONDITIONAL`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` corrigió la premisa:

> enlazar fuentes útiles mejora verificabilidad/contexto, pero no afirmar “outbound link = señal E-E-A-T/ranking”. Añadir solo donde ayuda al lector o sustenta una afirmación.

Desde esta primera revisión A.5 ya era condicional, no una tarea sitewide.

### 3.2 · Fuentes primarias

`docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` fijó:

Google Search Central · Link best practices  
https://developers.google.com/search/docs/crawling-indexing/links-crawlable

Google · Creating helpful, reliable, people-first content  
https://developers.google.com/search/docs/fundamentals/creating-helpful-content

Google Search spam policies · Link spam  
https://developers.google.com/search/docs/essentials/spam-policies#link-spam

Lectura de #135:

- enlaces externos pueden aportar contexto/verificabilidad;
- E-E-A-T no es un score único que se optimice añadiendo dominios “fuertes”;
- no hay cuota de outbound links;
- enlaces pagados/afiliados deben calificarse correctamente;
- esquemas/intercambios orientados a ranking son un riesgo.

### 3.3 · Matriz intermedia → `PILOTAR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` usó `PILOTAR`:

> enlazar fuentes primarias cuando mejoren la pieza; no tratar outbound links como factor directo de ranking/E-E-A-T.

Ese lenguaje no significaba implantar enlaces en masa. Era compatible con probar el criterio donde hubiera una afirmación que necesitase evidencia.

### 3.4 · Repo cross-check → se mantiene `CONDITIONAL`

`docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` incluye A.5 entre los condicionales:

> enlaces salientes: solo donde una fuente mejora verificabilidad/lectura; no por “E-E-A-T boost”.

No apareció un gap transversal que justificase una nueva infraestructura global.

### 3.5 · Autoridad machine-readable final → `CONDITIONAL`

`data/web-improvement-decisions-2026-08-28.json` fija:

```json
{"id":"A.5","area":"seo","status":"CONDITIONAL"}
```

Y exige que todo `CONDITIONAL` tenga un trigger explícito antes de código.

### 3.6 · Autoridad humana final → trigger por afirmación

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` consolida:

> enlazar fuentes primarias cuando ayuden al lector o acrediten una afirmación; no vender outbound links como factor directo E-E-A-T/ranking.

### 3.7 · Revalidación independiente → decisión mantenida

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` mantuvo A.1–A.12. No reabrió A.5 como implementación obligatoria.

Secuencia histórica:

```text
hipótesis: authority outbound links / E-E-A-T
→ CONDITIONAL
→ PILOTAR donde aporta evidencia
→ repo cross-check mantiene CONDITIONAL
→ final JSON/humano = CONDITIONAL
→ revalidación independiente mantiene
```

## 4. Trigger exacto

A.5 se activa cuando una página realiza una afirmación externa cuya verificabilidad mejora con una fuente.

Ejemplos:

### Hechos propios

Libro, autor, fragmento, proceso creativo: normalmente la autoridad primaria es el propio proyecto, editorial o documentación contractual/factual correspondiente. No hace falta añadir una bibliografía externa por estética.

### Hechos externos cambiantes

- editorial acepta/no acepta manuscritos;
- convocatoria y sus bases;
- fecha/condición de un evento externo;
- comportamiento de Google/Brevo/otra plataforma;
- política o estándar técnico.

Aquí citar la fuente responsable suele ser útil.

### Recomendaciones/opinión

La opinión no necesita fingir objetividad mediante referencias. Los hechos bibliográficos, disponibilidad, edición, premio o editorial sí pueden necesitar fuente.

## 5. Jerarquía de evidencia que sobrevive a #135

Cuando el trigger se cumple:

1. fuente oficial/primaria;
2. organismo/entidad responsable;
3. documentación técnica oficial;
4. fuente secundaria reputada cuando la primaria no existe o para contexto;
5. evitar blogs SEO/agregadores para justificar decisiones que tienen documentación oficial.

Ejemplos:

- Google Search → `developers.google.com/search`;
- Brevo → Help/Developers de Brevo;
- WCAG → W3C/WAI;
- convocatoria → organizador/bases;
- editorial/edición → editorial/catálogo responsable según el hecho.

## 6. Integración técnica: solo donde ya haya una autoridad de datos

No crear un sistema global de citas porque A.5 existe.

En datasets que ya modelan hechos verificados, puede ser apropiado reutilizar o introducir campos equivalentes a:

```json
{
  "sourceUrl": "https://...",
  "sourceType": "official",
  "verifiedAt": "2026-08-28",
  "supports": ["submission-status"]
}
```

Pero antes de añadir campos hay que inspeccionar si la autoridad concreta ya tiene `source`, `sourceUrl`, `verifiedAt` u otro equivalente.

Esto se cruza con A.4: `verifiedAt` y revisión factual deben compartir semántica, no crear dos calendarios de verificación.

## 7. Enlaces visibles

Cuando una fuente merece mostrarse:

```html
<a href="https://developers.google.com/search/docs/...">
  documentación oficial de Google sobre …
</a>
```

Preferir anchors que expliquen el destino frente a “clic aquí”, salvo contexto donde una etiqueta corta sea más natural.

## 8. Calificación de enlaces

No usar `nofollow` por defecto en todos los enlaces externos.

- relación pagada/afiliada → `rel="sponsored"` es la calificación preferida por Google; `nofollow` puede acompañar según el contrato/política;
- fuente que no se desea respaldar → `nofollow` cuando corresponda;
- enlace editorial normal y confiable → no necesita `nofollow` automático.

La calificación debe reflejar la relación real, no una teoría de PageRank interno.

## 9. QA condicional

Reutilizar el checker externo existente (Lychee/QA de enlaces). No crear otro crawler solo para A.5.

Si un dataset concreto declara registros “verified”, un checker semántico puede validar su contrato:

```python
for item in externally_verified_records:
    assert item.get("sourceUrl")
    assert item.get("verifiedAt")
```

Solo si esa autoridad realmente adopta esos campos.

No programar un algoritmo que decida por DA/DR si un dominio es “autoridad”.

## 10. Auditoría correcta

No contar links por página. Preguntar dónde hay afirmaciones que necesitan evidencia:

- directorios/convocatorias → normalmente sí;
- artículos técnicos → afirmaciones materiales;
- prensa/premios → fuente real cuando se presenta reconocimiento externo;
- recomendaciones → datos verificables, no la opinión;
- obra → hechos comerciales/editoriales externos cuando corresponda.

## 11. Qué NO hacer

- insertar Wikipedia/universidades/prensa solo para “pasar autoridad”;
- cuota 3–5 links por artículo;
- intercambiar links con autores para ranking;
- elegir dominios por DA/DR;
- `nofollow` en todos los enlaces externos;
- bibliografías falsas en literatura/opinión;
- citar blogs SEO cuando existe documentación oficial;
- crear un nuevo registry global de fuentes sin necesidad;
- marcar A.5 como implementada porque algunas páginas ya enlazan fuera.

## 12. Beneficio / coste

Verificabilidad: alto cuando hay hechos externos.  
Confianza editorial: alto en directorios/guías.  
SEO directo atribuible a “poner enlaces salientes”: no demostrado.  
Coste: bajo por caso; alto e inútil si se convierte en auditoría sitewide sin trigger.

## 13. Tests si se implementa en una autoridad concreta

- registro `verified` exige evidencia conforme al schema elegido;
- `verifiedAt` mantiene semántica compatible con A.4;
- afiliados/comerciales conservan `sponsored` cuando aplique;
- links siguen verdes en QA externo;
- una fuente externa nunca se convierte accidentalmente en canonical del contenido propio;
- builder/UI preservan fuente visible solo cuando el contrato la requiere.

## 14. Definition of Done de A.5

### Historia ya recuperada

- [x] hipótesis de “authority outbound links” preservada;
- [x] corrección del supuesto boost E-E-A-T preservada;
- [x] estado inicial `CONDITIONAL` preservado;
- [x] `PILOTAR` de matriz intermedia documentado como formulación histórica;
- [x] cross-check mantuvo trigger estricto;
- [x] autoridad JSON final = `CONDITIONAL`;
- [x] autoridad humana final = `CONDITIONAL`;
- [x] revalidación independiente no cambió A.5;
- [x] relación con A.4 y fuentes primarias conservada.

### Para cada activación futura

- [ ] identificar la afirmación exacta que necesita evidencia;
- [ ] elegir fuente primaria si existe;
- [ ] reutilizar schema/campos actuales;
- [ ] calificar relación comercial cuando proceda;
- [ ] no fijar KPI de número de enlaces;
- [ ] ejecutar QA correspondiente.

## 15. Trazabilidad del corpus histórico de #135 revisado para A.5

### Evidencia/decisión específica

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `CONDITIONAL` y corrección del boost.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — links/people-first/spam.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `PILOTAR` histórico.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — condición estricta por utilidad/verificabilidad.
- `data/web-improvement-decisions-2026-08-28.json` — estado final machine-readable.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana final.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — revalidación independiente.

### Revisados sin cambio específico adicional

Overrides de repo, blueprints netos, cuarta a decimoquinta pasada, casos/evidencia/límites, fuentes adicionales, repos evaluados y policy watch se revisaron. No añaden una decisión A.5 que sustituya el trigger final `CONDITIONAL`.

## 16. Recomendación de merge

**MERGE como reconstrucción completa de una decisión `CONDITIONAL`.**

No significa “implementar enlaces externos”. Significa que Clara/Claude dispone del criterio exacto de cuándo y cómo hacerlo sin repetir la investigación ni convertirlo en una receta SEO.