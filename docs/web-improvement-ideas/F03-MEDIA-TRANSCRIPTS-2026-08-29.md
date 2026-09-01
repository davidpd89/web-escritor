# F.3 · Alternativas, transcripciones y captions para media informativa

**Estado histórico final de PR #135:** `CONDITIONAL`  
**Trigger:** existe audio/vídeo que comunica habla o información necesaria para comprender el contenido.  
**No aplica automáticamente:** media puramente decorativa sin información equivalente que transmitir.  
**Naturaleza de esta PR:** documentación; no genera transcripciones ni edita media.

## 1. Idea original

La hipótesis inicial decía que cualquier contenido futuro en vídeo/audio —booktrailers, extractos sonoros, etc.— debía tener transcripción textual desde el primer día.

#135 mantuvo el principio de accesibilidad, pero corrigió la formulación absoluta: **la obligación depende de qué comunica la pieza**, no de que exista un `<video>` o `<audio>`.

## 2. Evolución de la decisión

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | regla amplia | Transcripción textual para cualquier nuevo vídeo/audio. |
| Revisión 108/108 | `CONDITIONAL` | Transcripción/captions cuando la media comunica habla/información; no exigir una transcripción artificial a vídeo decorativo. |
| Matriz | `CONDICIONAL` | Todo medio informativo nuevo debe nacer con alternativa adecuada desde origen. |
| Autoridad final | `CONDITIONAL` | Mantiene la distinción informativo/decorativo y evita una migración blanket. |
| Revalidación independiente | mantenido | No aparece razón para endurecerlo como implementación universal. |

## 3. Interpretación correcta

F.3 es una **política de publicación y QA**, no necesariamente una feature técnica.

Antes de publicar una pieza multimedia debe clasificarse:

1. **Audio/vídeo con habla o narración relevante:** necesita alternativa textual adecuada; en vídeo, captions/subtítulos cuando corresponda y transcripción si aporta acceso equivalente/útil.
2. **Vídeo con información visual necesaria además del audio:** la solución debe cubrir también esa información visual; una transcripción del diálogo por sí sola puede ser insuficiente.
3. **Audio sin equivalente textual:** necesita alternativa equivalente.
4. **Media decorativa/ambiental:** no se debe fabricar una “transcripción” vacía; debe marcarse/implementarse de forma que no cree ruido accesible.
5. **Media de tercero embebida:** el hecho de que un proveedor ofrezca captions no exime de verificar que la experiencia real sea suficiente.

La implementación exacta debe contrastarse con WCAG vigente en el momento de publicar la media; esta PR recupera la decisión de #135, no sustituye una auditoría normativa de cada pieza futura.

## 4. Por qué quedó `CONDITIONAL`

En el corte histórico no había justificación para abrir un proyecto global de transcripción. El valor aparece **cuando existe una pieza informativa real**. Convertir F.3 en `IMPLEMENT_NOW` habría producido trabajo hipotético y riesgo de mantener archivos/transcripciones sin media que los necesitara.

Por eso el trigger debe residir cerca del flujo editorial/media:

- nueva pieza informativa → comprobar alternativa accesible antes de publicar;
- media ya existente → inventariar solo si una auditoría detecta contenido informativo sin alternativa;
- media decorativa → documentar clasificación y no forzar texto inútil.

## 5. Evidencia y relación con el sitio

E.6 trataba específicamente el coste de la intro/vídeo de Home. Esa pieza no debe confundirse automáticamente con F.3: rendimiento y accesibilidad hacen preguntas distintas.

Si la intro es puramente decorativa y no contiene información necesaria, F.3 no exige una transcripción solo porque haya un archivo de vídeo. Si en cambio un futuro booktrailer, entrevista, lectura o extracto de audio comunica contenido editorial, el trigger sí se cumple.

## 6. Flujo editorial recomendado

Para cada media nueva:

- `purpose`: decorativa / informativa / mixta;
- `speech`: sí/no;
- `visualInformation`: sí/no;
- `transcriptRequired`: sí/no + motivo;
- `captionsRequired`: sí/no + motivo;
- `audioDescriptionOrEquivalent`: si corresponde;
- idioma;
- URL/fichero canónico de la alternativa;
- owner;
- fecha de verificación.

No es obligatorio crear un registro técnico global si el volumen no lo justifica. Puede bastar un checklist de lanzamiento/media mientras haya pocas piezas.

## 7. Qué no hacer

- No transcribir vídeos decorativos por checklist.
- No publicar media informativa y prometer “la transcripción llegará después” como flujo normal.
- No asumir que subtítulos automáticos sin revisar son equivalentes.
- No generar con IA una transcripción/caption y publicarla sin revisión.
- No insertar texto oculto lleno de keywords llamándolo transcripción.
- No duplicar una transcripción en varias URLs indexables sin necesidad.
- No convertir F.3 en un argumento para añadir más audio/vídeo.

## 8. Definition of Done cuando el trigger exista

- [ ] la pieza se ha clasificado por propósito;
- [ ] el contenido hablado/informativo tiene alternativa adecuada desde publicación;
- [ ] captions/transcripción reflejan fielmente el contenido y están revisados;
- [ ] información visual necesaria también es accesible por una alternativa adecuada;
- [ ] la alternativa está enlazada/descubrible sin depender de JS frágil;
- [ ] mobile/keyboard/screen reader pueden acceder a controles y alternativa;
- [ ] no se publica contenido automatizado sin revisión humana;
- [ ] si es media de tercero, se comprueba la experiencia integrada real;
- [ ] la decisión decorativa está documentada cuando evita una transcripción innecesaria.

## 9. Relación con otras ideas

- **E.6:** optimización/lazy-load del vídeo; no determina si necesita transcripción.
- **G.2/G.3:** cualquier ayuda IA es borrador y necesita revisión humana; mismo principio aplica a captions/transcripciones asistidas.
- **C.4:** extractos descargables pueden servir de equivalente solo si realmente transmiten el mismo contenido y los derechos lo permiten.
- **Accesibilidad general:** controles del player siguen sujetos a F.1/F.4 y text resilience F.2.

## 10. Trazabilidad #135

Revisados:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — formulación original absoluta.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — corrección a `CONDITIONAL` según propósito.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — corpus de accesibilidad.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — estado de media real.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` y repo overrides — revisados; sin cambio material específico de F.3.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `CONDICIONAL`.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — no crea un workstream neto independiente para F.3.
- `data/web-improvement-decisions-2026-08-28.json` — `CONDITIONAL` final.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — alternativa/transcripción/captions según contenido.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — decisión mantenida.
- pasadas posteriores — revisadas; no aportan una contradicción que cambie el trigger.

## 11. Cierre

F.3 se conserva como una regla de calidad: **si una pieza multimedia comunica información, su alternativa accesible forma parte de la pieza desde el primer día**. La misma regla evita producir transcripciones inútiles para media verdaderamente decorativa.