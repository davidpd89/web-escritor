# A.5 · Enlaces salientes a fuentes de autoridad

Fecha de revisión: 2026-08-28
Idea original: añadir enlaces/citas a fuentes externas prestigiosas donde sea natural, presentándolo como mejora E-E-A-T/SEO.

## Veredicto

**IMPLEMENTAR COMO POLÍTICA DE CITACIÓN Y CONFIANZA; RECHAZAR LA IDEA DE “OUTBOUND LINKS = BOOST”.**

Enlazar fuentes primarias mejora verificabilidad, utilidad y confianza cuando un texto hace afirmaciones externas. Google recomienda enlazar recursos externos cuando aportan contexto y dice que citar fuentes puede ayudar a demostrar trustworthiness. Eso no equivale a un factor de ranking mecánico ni a que cuantos más enlaces a “dominios de autoridad” pongamos, mejor posicionemos.

## Fuentes primarias

1. Google Search Central · Link best practices
   https://developers.google.com/search/docs/crawling-indexing/links-crawlable
   - Google indica que los enlaces externos pueden ayudar a establecer confiabilidad al citar fuentes.
   - Recomienda enlazar cuando tiene sentido para dar contexto.
   - Si no confías en una fuente, `nofollow`; si existe relación pagada, `sponsored`.

2. Google Search Central · Creating helpful, reliable, people-first content
   https://developers.google.com/search/docs/fundamentals/creating-helpful-content
   - La confianza es central en el marco E-E-A-T.
   - E-E-A-T no es un ranking factor único que pueda “optimizarse” añadiendo links.

3. Google Search spam policies · Link spam
   https://developers.google.com/search/docs/essentials/spam-policies#link-spam
   - Intercambios excesivos, enlaces pagados que pasan crédito de ranking y esquemas artificiales violan políticas.
   - Los enlaces publicitarios/pagados deben calificarse con `nofollow` o `sponsored`.

## Qué problema resuelve realmente

En este proyecto hay páginas de distinta naturaleza:

### Hechos propios

Libro, autor, fragmento, proceso creativo. La fuente primaria puede ser el propio sitio, editorial o documento oficial.

### Hechos externos cambiantes

Editoriales que aceptan manuscritos, convocatorias, políticas de Google/Brevo, fechas de eventos, características de plataformas. Aquí una fuente externa primaria es especialmente valiosa.

### Recomendaciones/opinión

No hace falta convertir cada opinión en una bibliografía. Sí debe quedar claro cuándo un dato (ISBN, edición, disponibilidad, premio, editorial) proviene de una fuente verificable.

## Prioridad de fuentes

Cuando se haga una afirmación factual externa, preferir:

1. fuente oficial/primaria;
2. organismo/entidad responsable;
3. documentación técnica oficial;
4. fuente secundaria reputada solo cuando no existe primaria o para contexto;
5. evitar agregadores SEO para justificar decisiones técnicas si existe documentación del proveedor.

Ejemplos:

- Google Search → developers.google.com/search;
- Brevo → help.brevo.com / developers.brevo.com;
- ISBN/editorial → editorial/retailer/catálogo oficial según el hecho;
- convocatoria → bases del organizador;
- WCAG → W3C/WAI.

## Plan de integración

### A. Política editorial

Añadir una sección a la autoridad de metodología editorial existente en lugar de crear una página SEO nueva:

```text
Hecho externo verificable → fuente primaria visible o registrada.
Opinión/recomendación → no fingir objetividad ni autoridad externa.
Enlace comercial/afiliado → rel="sponsored nofollow" cuando corresponda.
Fuente no confiable pero necesaria → rel="nofollow".
```

### B. Source records machine-readable solo donde ya exista un dataset

No añadir un sistema global de citas a todos los HTML. Para directorios/datos generados, un registro como:

```json
{
  "sourceUrl": "https://...",
  "sourceType": "official",
  "verifiedAt": "2026-08-28",
  "supports": ["submission-status"]
}
```

es preferible porque builder/UI pueden derivar de una misma evidencia.

### C. Links visibles en contenido

Usar anchors descriptivos:

```html
<a href="https://developers.google.com/search/docs/...">documentación oficial de Google sobre ...</a>
```

No “fuente”, “más info”, “click aquí” si se puede explicar el destino.

## Auditoría propuesta

No contar links. Clasificar afirmaciones que realmente requieren fuente:

- directorios/convocatorias: obligatorio;
- artículos técnicos: recomendable por afirmación relevante;
- prensa/premios: obligatorio cuando se presenta como reconocimiento externo;
- recomendaciones: fuente para datos bibliográficos/verificación, no para la opinión personal;
- páginas de obra: fuentes comerciales/editoriales solo para hechos que el sitio no controla.

## Código / QA

Aprovechar el checker de enlaces externo existente (Lychee/check external links). No construir otro crawler.

Posible checker semántico específico para datasets:

`scripts/check-source-evidence.py`

```python
for item in externally_verified_records:
    assert item.get("sourceUrl")
    assert item.get("verifiedAt")
    assert item.get("sourceType") in {"official", "primary", "secondary"}
```

Debe validar presencia/formato/paridad; **no** decidir automáticamente que un dominio es “autoritativo”.

## Qué NO hacer

- insertar enlaces a Wikipedia, periódicos o universidades solo para “pasar autoridad”;
- fijar una cuota de 3–5 outbound links por artículo;
- intercambiar enlaces con autores para ranking;
- añadir enlaces irrelevantes a dominios con DR/DA alto;
- usar `nofollow` en todos los enlaces externos por miedo;
- confundir `rel=sponsored` con una penalización: es la calificación correcta para relaciones pagadas/afiliadas;
- citar blogs SEO como fuente primaria si existe documentación oficial;
- añadir bibliografías falsas a contenido literario/opinión.

## Beneficio esperado

- verificabilidad: alto en directorios/guías técnicas;
- confianza editorial: alto;
- SEO directo cuantificable por “link saliente”: **no demostrado**;
- mantenimiento: mejora si fuente + `verifiedAt` se integran con la política A.4.

## Tests

- datasets que afirman `verified` requieren `sourceUrl` + `verifiedAt`;
- enlaces `sponsored`/afiliados conservan el `rel` requerido;
- Lychee/external-link QA sigue verde;
- no introducir fuente externa como canonical del contenido propio;
- builders preservan fuente/evidencia visible cuando el contrato lo exige.

## Definition of Done

- [ ] identificar datasets/páginas con hechos externos verificables;
- [ ] reutilizar campos de fuentes ya existentes antes de inventar otros;
- [ ] documentar jerarquía de fuentes;
- [ ] auditar afiliados/comerciales para `sponsored`;
- [ ] integrar con A.4 cuando haya `verifiedAt`/review cadence;
- [ ] no fijar cuotas de enlaces ni KPI de “authority links”.

## Recomendación de merge

**MERGE como política editorial/técnica.** Mejora calidad y trazabilidad. No debe venderse como una receta de ranking basada en enlazar dominios “fuertes”.