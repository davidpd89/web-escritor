# A.7 · `FAQPage` en páginas de libro

Fecha de reconstrucción: 2026-08-29  
Idea original: añadir preguntas frecuentes reales a las páginas de cada obra y marcarlas con `FAQPage` para mejorar rich snippets.  
Fuente histórica principal: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado de esta PR: decisión `REJECT` para la táctica SEO; no elimina FAQs humanas útiles.

## Veredicto reconciliado

**REJECT como táctica SEO/Google rich results. CONSERVAR FAQs visibles solo cuando ayudan al lector.**

La idea original quedó obsoleta durante la propia investigación de #135. Primero Google ya restringía fuertemente FAQ rich results a sitios gubernamentales/sanitarios reconocidos; después, desde el **7 de mayo de 2026**, retiró los FAQ rich results generales de Search. Por tanto, añadir `FAQPage` a Samuel o Manecillas esperando ganar espacio en SERP no tiene el beneficio que motivaba A.7.

## 1. Regla de reconstrucción

Esta PR reconstruye A.7 desde el corpus histórico directo de #135. Conserva:

- preguntas/uso original previsto;
- primera razón de rechazo;
- cambio oficial de Google de mayo de 2026;
- evidencia del repo sobre `FAQPage` legacy;
- alternativa de FAQ visible;
- estados de la matriz y autoridad final;
- guardrail propuesto;
- revalidación independiente.

## 2. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` proponía añadir `FAQPage` JSON-LD a páginas de libro con preguntas como:

- ¿es apta para X edad?;
- ¿hay versión audiolibro?;
- ¿en qué orden leer la saga?;

La intención era mejorar rich snippets y responder dudas de lectores.

#135 corrigió dos problemas:

1. el rich result ya no era una oportunidad válida para este sitio;
2. varias preguntas sugeridas no pueden responderse/inventarse si edad, audiolibro, saga, retailer o disponibilidad no son hechos canónicos confirmados.

## 3. Evolución cronológica en #135

### 3.1 · Primera revisión → `REJECT`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` ya rechazó A.7 como táctica SERP porque, en la documentación entonces vigente, Google limitaba la elegibilidad de FAQ rich results a sitios gubernamentales y sanitarios conocidos/autorizados.

La revisión preservó una distinción esencial:

> FAQs humanas sí; schema para “ganar espacio” no.

### 3.2 · Fuente primaria inicial

`docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` citaba:

Google · FAQPage structured data  
https://developers.google.com/search/docs/appearance/structured-data/faqpage

En ese punto histórico la guía ya hacía inviable el beneficio general esperado para una web de autor.

### 3.3 · Cambio oficial 2026 → retirada completa del rich result

La investigación posterior de #135 incorporó el changelog oficial:

Google Search Central · Documentation updates  
https://developers.google.com/search/updates

Cronología registrada:

- desde **7 mayo 2026** los FAQ rich results dejan de aparecer en Search;
- 8 mayo: Google comunica/documenta la retirada;
- posteriormente retira la documentación específica de la feature porque ya no se muestra.

Referencia histórica previa:

https://developers.google.com/search/blog/2023/08/howto-faq-changes

En 2023 ya se había reducido drásticamente la exposición de FAQ rich results. El cambio de 2026 cerró el caso para A.7 como táctica de Google Search.

### 3.4 · Repo cross-check → premisa falsa que no debe volver al backlog

`docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` clasifica A.7 entre las premisas falsas/ideas que no deben volver al backlog:

> Google retiró FAQ rich results de Search a partir del 7 de mayo de 2026 para este uso general. Preguntas humanas pueden seguir siendo útiles; `FAQPage` como hack SERP no.

### 3.5 · Overrides → alternativa concreta

`docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` conserva la alternativa:

> mantener preguntas/respuestas humanas cuando ayudan al lector, sin `FAQPage` como hack; usar headings claros y contenido verificable.

No convertir el rechazo de schema en rechazo de una buena sección editorial de preguntas.

### 3.6 · Matriz intermedia → `DESCARTAR como SEO rich-result`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` mantuvo:

> FAQ visible puede ser útil para lectores, pero Google retiró FAQ rich results generales el 07/05/2026. No añadir schema esperando SERP expandida.

### 3.7 · Autoridad machine-readable final → `REJECT`

`data/web-improvement-decisions-2026-08-28.json`:

```json
{"id":"A.7","area":"seo","status":"REJECT"}
```

### 3.8 · Autoridad humana final → `REJECT`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md`:

> no añadir `FAQPage` esperando rich results: Google retiró el FAQ rich result general el 07/05/2026. FAQ visible solo si ayuda al lector.

### 3.9 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` volvió a contrastar A.1–A.12 y confirmó expresamente que A.7 estaba correctamente rechazada por políticas/cambios de Google.

Secuencia histórica:

```text
hipótesis: FAQPage para rich snippets
→ REJECT por elegibilidad restringida
→ Google retira FAQ rich results generales 07/05/2026
→ cross-check: no devolver al backlog
→ matriz: DESCARTAR como táctica SERP
→ final JSON/humano = REJECT
→ revalidación confirma
```

## 4. Estado/historial del proyecto

La decisión no es solo teórica. El historial ya había tratado `FAQPage` legacy:

- PR #66: identificó `FAQPage` legacy en recomendaciones y pidió retirar el schema preservando el FAQ visible;
- PR #75 y #76 reutilizaron esa decisión en auditorías posteriores.

Esto refuerza la necesidad de un guardrail anti-regresión: no reintroducir por una recomendación SEO antigua algo que el proyecto ya retiró deliberadamente.

## 5. FAQ visible ≠ FAQ schema

Una sección visible puede tener alto valor si responde preguntas reales y verificadas:

- género/tono de la obra;
- dónde leer un fragmento;
- independencia o continuidad **solo si está confirmada**;
- edición/formato real;
- dónde comprar solo con destino real verificado;
- recursos de club de lectura;
- cuestiones reales repetidas por lectores.

No hace falta `FAQPage` para presentar esa información de forma útil.

## 6. Aplicación por superficie

### Samuel

Preguntas reales pueden vivir como HTML normal o enlazar a recursos existentes. No añadir `FAQPage` por Google.

### Las manecillas del recuerdo

Mismo criterio. Especial cuidado con disponibilidad/retailer/formatos antes de que existan hechos comerciales confirmados.

### Noveris / club

Un formato pregunta-respuesta editorial no implica `FAQPage`.

`QAPage` tampoco es sustituto automático: corresponde a páginas de una pregunta con respuestas de usuarios según su contrato, no a FAQ redactada por el autor.

### Cuaderno (nota de reconciliación, 2026-09-01)

Este veredicto rechaza `FAQPage` como táctica SEO en páginas de libro y en
`/recomendaciones/` (gate vigente: `scripts/check-recomendaciones-no-faqpage.py`).
No cubre los artículos de `/cuaderno/` que ya incluyen una sección de FAQ
visible genuina para el lector: ahí rige un contrato distinto y posterior,
`qa/cuaderno-browser.mjs`, que exige paridad 1:1 entre el FAQ visible
(`.article-faq details`) y su `FAQPage` — si un artículo muestra FAQ al
lector, el schema debe reflejarlo exactamente; no se permite FAQ visible sin
`FAQPage` ni desincronizado. Esta paridad es una decisión editorial posterior
y más específica para esa superficie, no una regresión de A.7: no retirar el
`FAQPage` de los artículos de Cuaderno que ya tienen FAQ visible sin retirar
también el FAQ visible, y sin romper `qa/cuaderno-browser.mjs`.

## 7. Structured data que sí merece prioridad

En páginas de obra la exactitud de estos tipos/relaciones tiene más valor que sumar schema por cantidad:

- `Book`;
- `WebPage`;
- `Person`/author mediante `@id`;
- publisher real;
- ISBN, páginas, fecha, formatos reales;
- `BreadcrumbList` donde corresponda;
- `ImageObject`;
- relaciones factuales con fragmentos/partes.

## 8. Guardrail anti-regresión

Si no existe ya un test equivalente, #135 deja justificación para uno pequeño.

Ejemplo:

```python
for html in public_indexable_html():
    graphs = parse_jsonld(html)
    assert not contains_type(graphs, "FAQPage"), (
        f"{html}: FAQPage rich results were retired by Google in 2026; "
        "visible FAQ is allowed, schema requires a documented non-Google consumer"
    )
```

### Excepción futura

No convertir esto en una prohibición metafísica del vocabulario Schema.org. Si un consumidor real/no-Google exige `FAQPage`, documentar:

- consumidor;
- beneficio;
- páginas;
- fecha de verificación;
- mantenimiento;
- por qué compensa.

“Quizá ayuda a las IA” no es evidencia suficiente.

## 9. Qué NO hacer

- generar 8–12 preguntas genéricas por libro;
- copiar People Also Ask automáticamente;
- convertir sinopsis en preguntas repetidas;
- añadir schema esperando snippets grandes;
- confundir `QAPage` con FAQ editorial;
- marcar contenido no visible;
- inventar edad, audiolibro, saga, retailer, formatos o disponibilidad;
- conservar schema obsoleto porque “Schema.org aún define el tipo”;
- usar A.7 para aumentar volumen de structured data sin consumidor.

## 10. Impacto

Idea original como táctica SEO: valor nulo/obsoleto + mantenimiento.  
FAQ visible útil: valor UX/editorial potencialmente alto.  
Guardrail: bajo coste y valor preventivo razonable dado el historial legacy.

## 11. Tests / Definition of Done

### Historia ya recuperada

- [x] preguntas/hipótesis original preservadas;
- [x] primera razón de `REJECT` preservada;
- [x] retirada oficial del 07/05/2026 preservada;
- [x] repo cross-check y alternativa visibles preservados;
- [x] `DESCARTAR` de matriz intermedia preservado;
- [x] autoridad JSON final = `REJECT`;
- [x] autoridad humana final = `REJECT`;
- [x] revalidación independiente confirmó la decisión;
- [x] historial #66/#75/#76 registrado.

### Futuro mantenimiento

- [ ] escanear el `main` que vaya a revisar Clara/Claude por `FAQPage`;
- [ ] retirar solo schema sin consumidor vigente;
- [ ] preservar preguntas visibles útiles;
- [ ] añadir guardrail si no existe equivalente;
- [ ] documentar cualquier excepción no-Google real.

## 12. Trazabilidad del corpus histórico de #135 revisado para A.7

### Evidencia/decisión específica

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis/preguntas originales.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `REJECT` inicial por elegibilidad.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — FAQPage oficial histórica.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — retirada 2026 y premisa falsa.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` — alternativa visible sin schema.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `DESCARTAR` como rich-result.
- `data/web-improvement-decisions-2026-08-28.json` — `REJECT` final.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — autoridad humana.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — confirmación independiente.

### Revisados sin cambio específico adicional

Blueprints netos, overrides de repo no aplicables, cuarta a decimoquinta pasada, casos/evidencia/límites, fuentes adicionales, repos evaluados y policy watch fueron revisados; no añaden un cambio de decisión para A.7.

## 13. Recomendación de merge

**MERGE como reconstrucción completa de un `REJECT` documentado.**

La PR deja a Clara/Claude la alternativa válida —FAQ humana útil— y evita reintroducir una táctica de Google retirada.