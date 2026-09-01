# K.3 · Revalidación de producción — afiliación

Fecha: 2026-08-30  
Base auditada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
Tree de la base: `68d02e1fe8ac2cfa239f4a716929e992abb672fd`

## Veredicto

Estado 2026-08-30: `PARTIAL_IMPLEMENTATION · AMAZON_AFFILIATION_PUBLICLY_DECLARED · LINK_LEVEL_DISCLOSURE_GAP · SITEWIDE_DISCLOSURE_GAP · EXPANSION_BLOCKED`

Estado 2026-09-01 (tras #304 + esta PR): `SITEWIDE_DISCLOSURE_GAP` y `LINK_LEVEL_DISCLOSURE_GAP` cerrados — ver "Gap concreto" abajo. `EXPANSION_BLOCKED` se mantiene como política permanente (no una condición temporal): cualquier nuevo retailer/superficie afiliada debe repetir el contrato completo, no reutilizar este cierre como excepción.

K.3 no debe cerrarse como una implementación correcta hasta verificar in situ (visualmente, en varios tamaños/dispositivos) que el disclosure del header es legible y no degrada el diseño — ver capturas y verificación de reflow/pa11y en la PR.

## Evidencia directa de `main`

### 1. La relación se declara públicamente

`/recomendaciones/politica-de-recomendaciones/` contiene:

> «Cuando una lista incluye enlaces de compra con el tag `davidporto-21`, son enlaces afiliados: una compra puede generar una pequeña comisión sin coste adicional para quien compra.»

Por tanto, para la realidad editorial del sitio no procede tratar `davidporto-21` como un tag misterioso o meramente legacy: la propia web afirma que identifica afiliación.

El repo/Drive no permiten, por sí solos, inspeccionar el estado privado del panel de Amazon. Si el programa se hubiese cancelado, esa declaración y los tags tendrían que retirarse. Mientras el sitio publique que son afiliados, la implementación debe cumplir el contrato correspondiente.

### 2. Samuel contiene enlaces etiquetados

`editorial-facts.json` incluye para Samuel:

- editorial;
- Amazon con `?tag=davidporto-21`;
- Casa del Libro.

Solo Amazon aparece identificado como afiliado. No debe propagarse afiliación a retailers que son únicamente destinos factuales.

### 3. El tag está centralizado en el shell

`scripts/build-site-shell.py` define:

```python
AMAZON_SAMUEL_URL = "https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21"
```

y lo usa en el CTA global `Comprar` con:

```html
rel="sponsored nofollow noopener noreferrer"
```

Ese header se genera para una parte amplia del sitio V1; solo se desactiva explícitamente en determinadas rutas, entre ellas Manecillas. Por tanto, el owner de un arreglo sitewide **no es** `libros/samuel-entre-mundos/index.html`: es el shell/generador y su contrato de QA.

### 4. `rel="sponsored"` no es disclosure para el lector

Es una señal técnica correcta para buscadores, pero no comunica visualmente al usuario que el enlace puede generar comisión.

## Requisito externo vigente — Amazon España

La ayuda oficial del Programa de Afiliados de Amazon España, consultada el 2026-08-30, exige dos capas simultáneas:

1. una declaración clara y visible **cerca de cada enlace de afiliado**; Amazon ofrece ejemplos como «(enlace pagado)», `#publicidad`, `#publi` o `#ColaboraciónPagada`;
2. una declaración clara y visible a nivel de sitio con el texto requerido por el Acuerdo Operativo:
   «En calidad de Afiliado de Amazon, obtengo ingresos por las compras adscritas que cumplen los requisitos aplicables».

Fuentes oficiales:

- https://afiliados.amazon.es/help/node/topic/GHQNZAU6669EZS98
- https://afiliados.amazon.es/help/operating/agreement

La política actual de Recomendaciones explica la comisión, lo cual es positivo, pero no sustituye el requisito de disclosure próximo a los enlaces globales y tampoco reproduce actualmente la declaración de sitio exigida por Amazon. Además, esa política está en una ruta `noindex`, por lo que no debe usarse como única capa de transparencia para un CTA presente en el header.

## Gap concreto

Estado en la revalidación original (2026-08-30):

```text
tag affiliate                 = yes
rel=sponsored                 = yes
explicación editorial         = yes, en política de Recomendaciones
link-level visible disclosure = no demostrado en header global
required site statement       = no localizado
```

Estado tras `docs/audits/K03-...` follow-up + esta PR (2026-09-01):

```text
tag affiliate                 = yes
rel=sponsored                 = yes (scoped a host real amazon.es, no a un patrón que también acepta lookalikes)
explicación editorial         = yes, en política de Recomendaciones
required site statement       = yes, aviso-legal.html («En calidad de Afiliado de Amazon, obtengo ingresos...»), añadido en #304
link-level visible disclosure = yes, header-buy global (scripts/build-site-shell.py): badge "Afiliado" visible bajo "Comprar" + aria-label
                                 accesible; test-header-buy-disclosure.py cubre las 65 páginas V1 con el CTA
```

Consecuencia: gap cerrado para el CTA global del header. No ampliar afiliación a ningún retailer ni nueva superficie sin repetir este mismo contrato (tag real + `rel=sponsored` + disclosure próximo + declaración sitewide).

## Arreglo correcto cuando se edite código

### Owner

Reutilizar `scripts/build-site-shell.py` y el QA del shell. No parchear manualmente decenas de HTML generados ni crear un componente paralelo.

### Contrato mínimo

1. El CTA afiliado debe llevar una indicación visible y próxima conforme al requisito vigente.
2. Debe existir en una superficie global y visible la declaración de Afiliado de Amazon requerida por el acuerdo.
3. `rel="sponsored"` debe mantenerse.
4. La política de Recomendaciones puede conservar la explicación editorial sobre independencia de criterio.
5. Los enlaces no afiliados de editorial/Casa del Libro deben seguir sin tag ni disclosure de comisión falso.
6. Si la afiliación deja de estar activa, retirar tanto el tag como las declaraciones asociadas; no mantener una relación comercial ficticia.

## Diseño recomendado — no degradar UX

No convertir el header en una frase legal larga. Separar los dos niveles:

- junto al CTA: etiqueta breve visible, por ejemplo «enlace afiliado»/formulación compatible con el requisito aplicable;
- declaración completa: ubicación global clara y accesible, idealmente una sección legal/transparencia compartida y enlazable.

La elección final de copy debe respetar el texto exigido por Amazon y la normativa publicitaria aplicable; el documento no autoriza abreviarlo de forma que deje de ser claro.

## QA que debe acompañar el arreglo

No crear un checker paralelo. Añadir la regla al owner existente del shell o a su suite de tests:

- todo `amazon.es` con `tag=davidporto-21` debe conservar `rel~="sponsored"`;
- todo enlace afiliado generado por el shell debe tener disclosure visible próximo;
- debe existir exactamente una declaración sitewide autorizada, accesible desde las superficies públicas;
- links de Amazon sin relación afiliada no deben recibir tags por heurística;
- Casa del Libro/editorial no deben convertirse en afiliados;
- no hardcodear precio/stock de Amazon;
- si se cambia el tag en la autoridad, el shell y `editorial-facts.json` no deben divergir.

## Mejora de arquitectura recomendada

El `tag` está actualmente duplicado entre hechos editoriales y el shell. Antes de ampliar programas, modelar la relación comercial como dato explícito en la autoridad canónica, por ejemplo:

```text
retailer
book
public_url
affiliate = true|false
affiliate_program
affiliate_tag
relationship_status
relationship_verified_at
disclosure_policy
rel_policy
```

No introducir este schema hasta decidir su owner y migrar sin duplicar fuentes. El objetivo es eliminar hardcodes, no sumar otra tabla inconexa.

## Expansión futura: gate retailer por retailer

Una nueva afiliación solo entra si existen simultáneamente:

1. programa real y activo;
2. cuenta/relación verificada;
3. URL/código suministrado por ese programa;
4. destino correcto para el producto;
5. disclosure visible requerido;
6. `rel=sponsored` cuando corresponda;
7. términos compatibles con la superficie;
8. criterio editorial independiente de la comisión;
9. sin tracker adicional si el programa ya aporta atribución suficiente.

No inferir afiliación de que una tienda venda el libro.

## Books2Read

Sigue siendo una oportunidad condicional, no un requisito. Reabrir solo cuando haya una necesidad real de resolver múltiples retailers/ebook y exista una URL operativa compatible. Primero medir utilidad en una superficie limitada; no sustituir destinos canónicos por sistema.

## Qué NO hacer

- describir K.3 como «ya implementada correctamente» mientras falta disclosure cercano/sitewide;
- confiar en `rel=sponsored` como aviso humano;
- esconder toda transparencia en una política secundaria;
- añadir tags inventados a Casa del Libro/editorial;
- monetizar automáticamente todas las recomendaciones;
- instalar trackers adicionales para atribución afiliada;
- crear thin affiliate pages;
- afirmar precio/stock externo no verificado;
- parchear cada HTML generado a mano.

## Estado de CI antes de esta ampliación

HEAD auditado: `45a399837ca3fd14c0ea4215545ad808823c1ef3`.

Runs observados en `success`:

- Check content indexes — `33313186669`;
- Required merge gate — `33313186655`;
- Public artifact contract — `33313186710`;
- Analytics taxonomy QA — `33313186682`;
- Runtime scoping QA — `33313186697`;
- CSP public shell QA — `33313186698`;
- Accessibility baseline (Pa11y) — `33313186714`;
- Sitewide Reflow QA — `33313186705`.

La modificación de esta revalidación debe disparar/revalidar nuevamente los checks de rama.

## Por qué esta PR no parchea el shell todavía

El shell genera una cantidad amplia de HTML. Con la interfaz actual de edición no existe un hunk editor seguro ni ejecución local del generador para regenerar y revisar todos los artefactos derivados sin riesgo de reconstrucciones masivas. El contrato del proyecto prohíbe precisamente sustituir ficheros HTML largos a mano.

Por eso este DRAFT no debe confundirse con cierre técnico: documenta un **gap de producción accionable** y el owner exacto del futuro parche. El cambio de código debe hacerse cuando pueda ejecutarse el generador y verificarse su diff/QA completo.

## Cierre

K.3 pasa de «parcialmente implementada de forma correcta» a una conclusión más precisa: la afiliación Amazon existe y está declarada, pero **falta cerrar el disclosure exigido en las superficies donde se muestra el enlace**. La prioridad no es añadir más programas sino corregir el contrato de transparencia existente y después centralizar la relación comercial.

Estado final: `PARTIAL_IMPLEMENTATION · COMPLIANCE_GAP`; mantener DRAFT.