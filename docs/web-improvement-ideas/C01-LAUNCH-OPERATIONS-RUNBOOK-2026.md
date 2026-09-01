# C.1 · Runbook operativo de lanzamiento · Las manecillas del recuerdo

Fecha de corte: 2026-08-29  
Ventana: 2026-08-20 → 2026-09-17  
Propietario factual: `editorial-facts.json`  
Contrato de paridad: `docs/CONTENT-PARITY-MANECILLAS-V1.md`  
Landing canónica: `https://davidportodiaz.com/las-manecillas-del-recuerdo/`

> Este documento coordina la campaña. **No es una segunda fuente de verdad sobre el libro.** Título, editorial, fecha, ISBN, páginas, precio, formato, estado comercial y cualquier URL de compra se leen de `editorial-facts.json`. Si hay discrepancia, gana esa autoridad y este runbook debe corregirse.

## 1. Objetivo y límites

El lanzamiento debe convertir la atención alrededor de *Las manecillas del recuerdo* en acciones medibles sin sacrificar canon, control de spoilers ni estabilidad de las superficies evergreen.

Hasta que `books.lasManecillasDelRecuerdo.purchaseUrl` tenga una URL real y verificada:

- la conversión web primaria es `newsletter-manecillas`;
- la muestra se mide con `leer-fragmento-manecillas`, `sample-start-manecillas` y `sample-complete-manecillas`;
- no se publica `Offer`, disponibilidad de retailer ni CTA de compra inventado;
- no se crea un evento de compra de Manecillas hasta que exista un destino comercial real y el nuevo nombre se registre primero en `data/analytics-events.json`.

Este runbook tampoco convierte publicaciones sociales, newsletters, reseñas, preventas o retailer listings en hechos por el mero paso del tiempo. La ejecución externa exige evidencia.

## 2. Estados permitidos

| Estado | Significado |
| --- | --- |
| `VERIFIED_REPO` | El repo demuestra que la superficie/artefacto existe y cumple el contrato. |
| `VERIFIED_EXTERNAL` | Existe evidencia externa reproducible de que la acción se ejecutó. Debe conservarse referencia. |
| `UNVERIFIED_EXTERNAL` | La fecha/acción estaba prevista, pero este repo no prueba su ejecución. |
| `PLANNED` | Acción futura todavía no ejecutable o no observada. |
| `BLOCKED` | Existe un gate explícito que impide ejecutar/publicar. |
| `NOT_APPLICABLE` | Se decide no ejecutar y se registra el motivo. |

No usar `DONE`, `PUBLICADO`, `ENVIADO` o equivalentes sin evidencia.

## 3. Autoridades que se reutilizan

- `editorial-facts.json`: verdad factual del libro y gate comercial.
- `docs/CONTENT-PARITY-MANECILLAS-V1.md`: qué puede afirmar cada superficie y qué material está gated.
- `data/analytics-events.json`: taxonomía única de eventos medibles.
- `/las-manecillas-del-recuerdo/`: landing canónica.
- `/las-manecillas-del-recuerdo/fragmentos/`: muestra pública aprobada.
- `/prensa.html#ficha-manecillas`: ficha de prensa existente.
- newsletter source `manecillas`: conversión web vigente mientras no haya compra verificable.

No crear landing paralela, micrositio de campaña, segundo fichero de facts, segundo sistema de analytics ni “URL para IA”.

## 4. Gates globales

### G1 · Paridad factual

Antes de cada pieza externa o cambio web, contrastar el copy con `editorial-facts.json`. No copiar hechos desde este calendario a otra superficie como si fueran autoridad.

### G2 · Spoilers

La campaña puede usar premisa, objeto-reloj, memoria, herencia, tiempo, voces/vidas conectadas y fragmentos ya aprobados. Cualquier revelación fuera de esos materiales requiere revisión editorial específica.

### G3 · Comercio

`purchaseUrl:null` = **sin CTA comercial**, aunque la fecha de publicación esté confirmada y la web use el framing editorial autorizado de “publicada el 3 de septiembre de 2026”. Fecha editorial y disponibilidad comercial son gates distintos.

### G4 · Cubierta / high-res

`editorial-facts.json` conserva una incidencia editorial `must-not-propagate` sobre el handle impreso de la cubierta. El press kit/high-res y derivados que puedan amplificar ese error permanecen bloqueados hasta resolución y clearance. La portada web ya aprobada no se invalida por este gate.

### G5 · Evidencia

Una acción externa solo pasa a `VERIFIED_EXTERNAL` cuando queda una referencia reproducible: URL pública, message/campaign id, captura archivada, export o equivalente. Las métricas se registran por ventana y fuente; no se reconstruyen de memoria.

## 5. Calendario operativo revalidado

### Ola 1 · Descubrimiento / identidad de la obra

| Fecha | Acción | Objetivo | Métrica/gate | Estado al 29/08 | Evidencia |
| --- | --- | --- | --- | --- | --- |
| 20/08 | Portada / identidad visual | Fijar reconocimiento de obra | G1 + G4 | `UNVERIFIED_EXTERNAL` | El repo prueba la portada web; no prueba una publicación social concreta. |
| 24–26/08 | Teaser de premisa/reloj | Llevar tráfico cualificado a la landing | sesiones landing + `newsletter-manecillas` | `UNVERIFIED_EXTERNAL` | Sin evidencia de ejecución externa en el repo. |
| 27/08 | Activación editorial de fragmentos | Pasar de curiosidad a lectura | `leer-fragmento-manecillas`, `sample-start-manecillas`, `sample-complete-manecillas` | `VERIFIED_REPO` para la superficie; `UNVERIFIED_EXTERNAL` para promoción | La muestra pública y su instrumentación existen; la campaña externa no se infiere. |

### Ola 2 · Prelanzamiento inmediato

Ventana actual al corte de este runbook: **29/08–02/09**.

| Fecha | Acción | Objetivo | Métrica/gate | Estado al 29/08 |
| --- | --- | --- | --- | --- |
| 29–30/08 | Pieza “qué tipo de novela es / por qué este libro” | Dar contexto sin spoilers y reforzar posicionamiento | CTR a landing + newsletter; G1/G2 | `PLANNED` |
| 31/08 | Recordatorio de fecha + muestra | Convertir interés acumulado en lectura/alerta | sample start/completion + newsletter | `PLANNED` |
| 01/09 | Pieza de proceso humano | Construir confianza/autoridad, no hype vacío | interacción cualitativa + landing visits; G2 | `PLANNED` |
| 02/09 | Víspera | Concentrar atención en la fecha canónica | landing + newsletter; G1/G3 | `PLANNED` |

Regla: si una pieza no añade información/valor distinto, se cancela en vez de publicar por cumplir calendario.

### Ola 3 · Día de publicación

**03/09/2026**

Checklist, en este orden:

1. releer `editorial-facts.json`;
2. comprobar landing, canonical, JSON-LD, OG/Twitter, fragmentos y ficha de prensa;
3. comprobar `purchaseUrl`:
   - si sigue `null`, mantener conversión newsletter/muestra y **no inventar compra**;
   - si existe una URL verificada, actualizar primero la autoridad y luego las superficies derivadas de forma atómica;
4. si se habilita compra, registrar antes la taxonomía analytics específica de Manecillas;
5. publicar la pieza externa de lanzamiento solo con hechos ya autorizados;
6. guardar evidencia de ejecución externa;
7. registrar baseline de la ventana del día, sin confundir tráfico con ventas si no existe dato de venta.

Estado al 29/08: `PLANNED`.

### Ola 4 · Seguimiento

| Ventana | Acción | Objetivo | Decisión basada en evidencia | Estado |
| --- | --- | --- | --- | --- |
| 04–06/09 | Primer seguimiento | Resolver dudas reales y reutilizar señales de lectores | Priorizar preguntas/objeciones observadas; no inventar recepción | `PLANNED` |
| 07–10/09 | Profundización | Llevar lectores de muestra a obra/autor | Comparar sample start → complete y newsletter | `PLANNED` |
| 11–17/09 | Cola editorial | Transformar campaña temporal en contenido evergreen útil | Conservar solo piezas con valor duradero; evitar duplicar landing | `PLANNED` |

## 6. Scorecard mínimo

No existe “score de lanzamiento” compuesto. Se registran dimensiones por separado:

| Dimensión | Fuente | Lectura correcta |
| --- | --- | --- |
| Tráfico a landing | analítica web existente | interés/descubrimiento, no venta |
| `newsletter-manecillas` | GoatCounter + backend newsletter | alta aceptada; no equivale por sí sola a DOI confirmado |
| `leer-fragmento-manecillas` | GoatCounter | intención de leer la muestra |
| `sample-start-manecillas` | GoatCounter | apertura real de la muestra |
| `sample-complete-manecillas` | GoatCounter | llegada al CTA final / consumo significativo |
| Compra | solo cuando haya destino/evidencia comercial | no inferir desde clicks ni desde publicationDate |
| Señales cualitativas | respuestas/preguntas/reseñas con evidencia | insumo editorial; no convertirlas en rating agregado propio |

Ventanas recomendadas: baseline 29/08–02/09, lanzamiento 03/09, +72 h 04–06/09 y cola 07–17/09. Comparar periodos equivalentes cuando sea posible; no atribuir causalidad a una pieza sin experimento.

## 7. Kill-switches

Detener o retirar una pieza si ocurre cualquiera de estos casos:

- contradice `editorial-facts.json`;
- revela un spoiler no autorizado;
- apunta a retailer/compra no verificado;
- usa un asset bloqueado por la incidencia de cubierta/rights;
- repite una pieza previa sin valor editorial nuevo;
- presenta una métrica de plataforma como ventas, ranking, autoridad o causalidad;
- requiere borrar/modificar contenido evergreen para acomodar una promoción efímera.

## 8. Registro de ejecución

Para cada acción que realmente se ejecute, añadir una fila aquí o en el artefacto externo autorizado con:

`date_time · channel · action_id · status · evidence_ref · landing_variant · metric_window · notes`

No almacenar secretos, tokens, emails de suscriptores ni datos personales en el repo.

### Ejecuciones verificadas al corte 29/08/2026

Ninguna acción externa se marca como verificada desde esta PR. El repo sí demuestra las superficies web e instrumentación indicadas como `VERIFIED_REPO`.

## 9. Definition of Done de C.1

- [x] calendario histórico recuperado;
- [x] factual authority actual identificada y reutilizada;
- [x] editorial/publisher historical drift corregido en la revalidación, sin reescribir la historia;
- [x] runbook operativo único, no sistema paralelo;
- [x] estados que impiden fingir ejecución externa;
- [x] métricas mapeadas a la taxonomía real;
- [x] purchase gate respeta `purchaseUrl:null`;
- [x] spoiler/high-res gates preservados;
- [x] ventana 29/08–17/09 convertida en tareas ejecutables;
- [ ] CI del HEAD final verde;
- [ ] revisión de Claude antes de merge.
