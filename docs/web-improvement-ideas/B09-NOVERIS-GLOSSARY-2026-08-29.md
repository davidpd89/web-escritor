# B.9 · Glosario / FAQ canónico del universo de Samuel y Noveris

Fecha de reconstrucción: 2026-08-29  
Idea original: crear un glosario del universo narrativo con términos, lugares y personajes que sirva a lectores y pueda ser citado por motores de respuesta.  
Fuente histórica principal: PR #135, snapshot íntegro `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final de #135: `CONDITIONAL`.  
Revalidación contra `main` 2026-08-29: el trigger se ha cumplido sustancialmente en `/universo/noveris/`; no crear un segundo glosario paralelo.

## 1. Veredicto reconciliado

La conclusión histórica de #135 fue correcta: un glosario solo merece existir si contiene **canon real, de primera mano, mantenible y con control de spoilers**. No debe generarse lore para SEO ni fabricarse una taxonomía porque «las IA citan glosarios».

Después de #135, `main` evolucionó: `/universo/noveris/` ya funciona materialmente como la implementación que aquella decisión condicionaba. Contiene guía visible, respuesta rápida, mapa funcional, términos del universo y un `DefinedTermSet` con `DefinedTerm` enlazado al libro y a la entidad de Noveris. Por tanto:

- historia de #135: `CONDITIONAL`;
- estado observable actual de la capacidad: **sustancialmente `ALREADY_COVERED` para Noveris**;
- siguiente acción: mantener y ampliar la autoridad existente solo con canon real, no abrir `/glosario/` u otra familia duplicada.

## 2. Hipótesis original

`docs/IDEAS-MEJORA-WEB-2026-08-27.md` propuso:

> Glosario/FAQ del universo narrativo: página tipo «Glosario de Samuel entre mundos» con términos, lugares y personajes, pensada como contenido citable cuando alguien pregunte qué es X en el libro.

El valor hipotético era doble:

1. orientación humana para lectores;
2. una fuente oficial y explícita para resolver entidades ficticias sin ambigüedad.

La premisa que debía rechazarse era convertir ese formato en una fábrica de términos para captar búsquedas inexistentes.

## 3. Evolución cronológica en #135

### 3.1 · Primera revisión 108/108 → `CONDITIONAL`

`docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` la dejó como `CONDITIONAL`:

- puede ser contenido único y citable;
- solo si usa canon real;
- debe controlar spoilers;
- necesita mantenimiento;
- no se debe generar lore para SEO.

Esta primera revisión ya corrige la idea de que el formato, por sí mismo, produzca autoridad.

### 3.2 · Fuentes primarias → people-first y sin markup especial para IA

`docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` fijó reglas que aplican directamente:

- Google recomienda contenido útil, original y hecho para personas;
- las experiencias de IA de Google se apoyan en los fundamentos normales de Search;
- no existe un schema o formato especial que haya que construir «para la IA»;
- no se justifica scaled content de poco valor para cubrir combinaciones de términos.

Aplicación a B.9: el glosario vale por explicar el universo con autoridad primaria del autor, no por el nombre «glosario» ni por una supuesta receta GEO.

### 3.3 · Matriz intermedia → `PILOTAR`

`docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` elevó temporalmente la idea a `PILOTAR`:

> «Glosario Samuel/Noveris puede ser fuente original/citable. Debe ser spoiler-aware, factual y con navegación a entidades existentes.»

Este estado intermedio no debe borrarse: define cómo debía ser un piloto válido.

### 3.4 · Autoridad final → vuelve a `CONDITIONAL`

`docs/PR135-FINAL-AUTHORITY-2026-08-28.md` cerró B.9 como `CONDITIONAL`:

> «Glosario Samuel/Noveris solo si aporta contenido canónico, spoiler-aware y de primera mano; enlazar entidades existentes.»

El retorno de `PILOTAR` a `CONDITIONAL` evita convertir una posibilidad editorial en backlog obligatorio.

### 3.5 · Revalidación independiente

`docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` intentó falsar los estados finales y mantuvo B.1–B.9 sin correcciones materiales. B.9 no fue reabierta ni elevada a implementación obligatoria.

Secuencia preservada:

```text
hipótesis: glosario citable
→ revisión: CONDITIONAL
→ matriz: PILOTAR con canon + spoilers + navegación
→ autoridad final: CONDITIONAL
→ revalidación independiente: mantenida
```

## 4. Relación con otras ideas: no duplicar responsabilidades

### B.9 ≠ A.1

A.1 organiza piezas editoriales por tema mediante `topic-collections`. B.9 explica **entidades y vocabulario del canon de una obra**.

### B.9 ≠ A.2

A.2 es el hub canónico de la obra/universo. B.9 puede vivir dentro de ese hub o de una página de universo, pero no debe crear otro «hub definitivo».

### B.9 ≠ B.4

B.4 protege identidad y `@id` de entidades estructuradas. B.9 aporta contenido humano/canónico sobre términos. Si usa structured data, debe reutilizar el grafo existente.

### B.9 ≠ A.7

Una FAQ visible útil puede convivir con el contenido, pero A.7 rechazó `FAQPage` como táctica de rich results. No usar B.9 para reintroducir el hack SEO de A.7.

## 5. Trigger que #135 exigía

La idea solo debía avanzar cuando coexistieran:

- suficientes términos canónicos realmente útiles;
- fuente de verdad editorial clara;
- capacidad de mantener cambios de canon;
- una estrategia explícita de spoilers;
- valor de navegación/consulta para lectores;
- integración con las entidades y URLs existentes.

No bastaba:

- que una keyword apareciera en una herramienta;
- que una IA pudiera citar un glosario;
- que Schema.org permitiera `DefinedTerm`;
- poder generar cientos de entradas automáticamente.

## 6. Diseño editorial válido conservado de #135

Una entrada útil debería poder responder, según el término:

- qué es;
- a qué obra pertenece;
- relación con personajes/lugares/sistema mágico;
- spoiler level;
- fuente/canon que respalda la descripción;
- URL canónica relacionada;
- fecha de revisión si el dato puede evolucionar.

Modelo conceptual, solo si una autoridad de datos llega a ser necesaria:

```json
{
  "term": "Canalizador",
  "work": "Samuel entre mundos",
  "definition": "...",
  "spoilerLevel": "safe",
  "relatedCanonical": "/universo/noveris/",
  "verifiedAt": "YYYY-MM-DD"
}
```

No crear este JSON si el HTML/autoridad actual ya resuelve el caso sin duplicación.

## 7. Spoilers

El control de spoilers era parte de la condición, no un detalle cosmético.

Opciones válidas:

- glosario «sin spoilers» con solo conceptos de premisa/mundo;
- señalización clara por entrada cuando haya información posterior;
- separar contenido posterior a cierto punto de lectura;
- no revelar giro, desenlace o identidad oculta solo para completar una definición.

No debe ocurrir:

- que el snippet/meta revele un spoiler oculto visualmente;
- que JSON-LD contenga revelaciones que la UI declara ocultas;
- que un generador infiera relaciones no aprobadas por el canon.

## 8. Structured data: secundario al contenido

Si el contenido real se beneficia de ello, `DefinedTermSet`/`DefinedTerm` puede describir términos. Eso no convierte el marcado en una feature de ranking.

Guardrails:

- `name`/`description` deben coincidir con el contenido visible;
- URLs y `@id` canónicos;
- enlazar Samuel mediante su entidad ya existente;
- no inventar `sameAs` externos;
- no publicar datos estructurados más ricos que el contenido que el lector puede ver.

## 9. Revalidación del repo actual

`main` 2026-08-29 demuestra que el trigger se cumplió posteriormente.

`/universo/noveris/` ya contiene:

- H1 «Noveris»;
- lead que la presenta como ciudad, sistema mágico y archivo de términos;
- CTA `#glosario`;
- respuesta rápida «Qué es Noveris»;
- contenido de arquitectura del mundo;
- mapa funcional;
- términos visibles y tablas de objetos/canalizadores;
- `DefinedTermSet` `#glosario`;
- múltiples `DefinedTerm` reales: Noveris, Canalizador, Sael, Zakra, Gorx, Velukis, Glissaro, Vara Glytch, Glíder, Veltris, Sernía, Melastra, Velo/Barrera, Espejo Ancestral, Silenciadoras, Zunthar, Marelian, Guerra de los Cristales;
- enlace a `https://davidportodiaz.com/#book-samuel`;
- `sameAs` de Noveris a Wikidata ya gobernado por la infraestructura de B.4.

Esto cambia la acción práctica actual: **no abrir otra implementación de B.9**.

## 10. Hallazgo de compatibilidad con A.7

La página actual también contiene `FAQPage`. Históricamente A.7 quedó `REJECT` para usar FAQ schema esperando rich results y la investigación posterior documentó la retirada general de FAQ rich results en Google en 2026.

Esto no invalida el contenido humano de B.9, pero cualquier revisión futura debe tratar `FAQPage` bajo el contrato de A.7: no mantenerlo por una expectativa SERP inexistente. La presente PR no modifica runtime porque su objetivo es trasladar la investigación de #135, no mezclar B.9 con la corrección de A.7.

## 11. Qué NO hacer

- crear `/glosario-samuel/` si `/universo/noveris/` ya es la autoridad;
- generar lore con IA para aumentar cobertura;
- inventar personajes, atributos, relaciones o fechas;
- convertir cada sustantivo del libro en una página indexable;
- crear cientos de URLs long-tail;
- usar FAQ/DefinedTerm como «marcado GEO»;
- duplicar IDs de B.4;
- esconder spoilers solo en CSS mientras metadata los revela;
- mezclar información de borradores no publicada con canon público;
- publicar entries sin owner/mantenimiento.

## 12. Qué sí puede ampliarse en el futuro

Solo sobre la autoridad existente y cuando exista material real:

- nuevas entradas canónicas demandadas por lectores;
- enlaces desde artículos de Cuaderno que explican sistema de magia/worldbuilding;
- navegación por categorías si el volumen lo justifica;
- indicadores de spoiler;
- correcciones de canon;
- mejor accesibilidad del mapa/contenido;
- pruebas de paridad visible ↔ structured data.

## 13. QA/contratos si se modifica

- todos los términos provienen de canon aprobado;
- no hay URLs/IDs duplicados;
- no hay enlaces rotos;
- contenido visible y JSON-LD están en paridad;
- no se filtran spoilers fuera de la política definida;
- reflow y navegación por teclado pasan;
- el mapa tiene alternativa textual;
- `@id` de Samuel/Noveris sigue la autoridad B.4;
- cualquier `dateModified` responde a cambio material real.

## 14. Pasadas posteriores de #135 revisadas

Se revisaron las pasadas cuarta a decimoquinta, fuentes adicionales, casos/evidencia, repositorios evaluados, blueprints y policy watch.

No añaden una decisión posterior específica que cambie B.9. Los hallazgos R.9–R.88 tratan otras capacidades. Los principios transversales que sí aplican —people-first, no scaled content, evidencia primaria, no herramientas buscando un problema— quedan incorporados aquí.

## 15. Trazabilidad específica

Material de #135 que sí contiene evidencia/decisión B.9:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `CONDITIONAL`;
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — people-first/AI fundamentals;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — estado intermedio `PILOTAR`;
- `data/web-improvement-decisions-2026-08-28.json` — estado machine-readable final;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — `CONDITIONAL` final;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — decisión mantenida.

Revalidación actual adicional:

- `universo/noveris/index.html` — evidencia de que la capacidad se implementó después de la investigación histórica.

## 16. Definition of Done de esta reconstrucción

- [x] hipótesis original preservada;
- [x] primer `CONDITIONAL` preservado;
- [x] piloto intermedio preservado;
- [x] condición canon/spoilers/mantenimiento preservada;
- [x] relación con A.1/A.2/A.7/B.4 documentada;
- [x] final `CONDITIONAL` de #135 preservado;
- [x] revalidación independiente preservada;
- [x] pasadas posteriores revisadas;
- [x] estado actual del repo reconciliado sin reescribir la historia;
- [x] no se crea un glosario paralelo.

## 17. Recomendación para Clara/Claude

**No implementar B.9 desde cero.** La PR debe conservarse como historial/contrato de decisión. Si se trabaja en el glosario actual, hacerlo como extensión o corrección de `/universo/noveris/`, con canon, spoilers, accesibilidad y paridad estructurada como gates.