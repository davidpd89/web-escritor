# G.2 · Borradores IA para guías del club de lectura

**Estado histórico final de PR #135:** `CONDITIONAL`  
**Uso permitido:** workflow editorial privado de borrador, con revisión humana sustantiva antes de publicar.  
**No es:** feature pública, generador de volumen ni sustituto del contenido de primera mano del autor.  
**Naturaleza de esta PR:** documentación; no genera ni publica contenido.

## 1. Hipótesis original

G.2 proponía usar IA para preparar resúmenes/guías de discusión del club de lectura, siempre con revisión humana antes de publicar.

La investigación mantuvo esa posibilidad, pero redujo mucho su prioridad y alcance: el cuello de botella del proyecto no era “falta de texto generado”, y la ventaja editorial de la web está precisamente en el canon y experiencia directa del autor.

## 2. Evolución y contradicción histórica

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Generar borrador de guía/resumen con revisión humana. |
| Revisión 108/108 | `CONDITIONAL` | Puede ayudar como workflow editorial privado; no es una feature pública. |
| Matriz operativa | `DEFERIR` | Las guías IA no son una escasez prioritaria; es preferible contenido de primera mano. |
| Autoridad final | `CONDITIONAL` | Recupera la posibilidad como ayuda interna, pero exige que el valor público sea revisión/experiencia humana y prohíbe generar volumen. |
| JSON final | `CONDITIONAL` | La autoridad machine-readable confirma el estado final. |
| Revalidación independiente | mantenido | Cambios IA grounded/human-reviewed y sin retención adicional innecesaria. |

Es importante no borrar la etapa `DEFERIR`: explica por qué `CONDITIONAL` **no significa “hacerlo ahora”**. El estado final permite el uso solo cuando existe una guía real que preparar y la IA reduce trabajo sin degradar autenticidad/canon.

## 3. Trigger correcto

G.2 solo se activa cuando concurren condiciones concretas:

- existe una sesión/guía/actividad real del club que necesita material;
- el autor/editor dispone de fuente canónica suficiente;
- el borrador acelera una tarea concreta, no crea contenido para rellenar calendario;
- habrá revisión humana completa antes de publicar;
- se verifican spoilers, nombres, hechos, cronología y preguntas;
- los derechos permiten reutilizar los fragmentos/contexto suministrados al proceso.

Si no existe una pieza editorial real que producir, no hay tarea G.2.

## 4. Qué puede hacer la IA

Como ayuda privada puede, por ejemplo:

- proponer una estructura inicial de guía;
- agrupar notas ya escritas por el autor;
- sugerir preguntas de discusión a partir de material canónico;
- detectar repetición en un borrador humano;
- convertir notas internas en una primera maqueta que después se reescribe/verifica;
- ayudar a generar variantes de preguntas por nivel de spoiler.

La salida no se considera contenido listo para producción.

## 5. Qué debe aportar la revisión humana

La revisión no puede limitarse a “leer por encima”. Debe comprobar:

- canon factual;
- spoilers y nivel de revelación;
- intención de personajes/temas cuando el texto la atribuya al autor;
- citas literales y derechos;
- tono/voz editorial;
- utilidad real de cada pregunta;
- ausencia de invenciones o interpretaciones presentadas como hechos;
- adecuación a la sesión concreta;
- enlaces/fuentes internos correctos.

La aportación humana es parte del producto final, no un gate administrativo.

## 6. Por qué no debe ser una feature pública

#135 separó explícitamente workflow editorial de producto. Un “generador de guías con IA” público implicaría:

- nuevo runtime/API/coste;
- privacidad y posible envío de texto de usuarios;
- control de abuso;
- factualidad/canon en tiempo real;
- accesibilidad y soporte;
- superficie de seguridad/CSP;
- incentivo a producir volumen genérico.

Nada de eso estaba justificado por la idea original. Si algún día se quisiera una herramienta pública, requeriría una nueva decisión de producto independiente de G.2.

## 7. Relación con contenido people-first

La matriz intermedia prefirió `DEFERIR` porque una guía automática no es escasa. Lo distintivo del sitio es lo que el autor puede aportar y un generador genérico no:

- por qué se tomó una decisión narrativa;
- documentación real usada para escribir;
- matices de personajes/temas;
- preguntas nacidas de lectores reales;
- material de proceso auténtico.

G.2 puede reducir trabajo mecánico alrededor de ese material. No debe reemplazarlo.

## 8. Privacidad, derechos y retención

Esta idea no autoriza:

- subir manuscritos completos a cualquier servicio sin revisar condiciones;
- guardar prompts/outputs con contenido sensible indefinidamente;
- usar material de lectores sin base/consentimiento;
- publicar extractos extensos generados/reproducidos sin rights gate;
- entrenar un sistema con conversaciones del club.

La herramienta concreta y su tratamiento de datos deben evaluarse en el momento de uso. La documentación histórica no valida ningún proveedor específico.

## 9. Flujo recomendado cuando se active

1. Definir la pieza real, objetivo, audiencia y spoiler level.
2. Preparar solo las fuentes canónicas necesarias.
3. Pedir un borrador estructural, no una “guía final”.
4. Revisar contra las fuentes y el manuscrito/canon autorizado.
5. Reescribir tono/preguntas desde criterio humano.
6. Verificar citas/derechos y enlaces.
7. Pasar QA editorial/accesibilidad normal.
8. Publicar como contenido del autor/sitio, no como “respuesta automática”.
9. Si el proceso se repite, documentar una plantilla interna; no crear automáticamente un SaaS/feature.

## 10. Qué no hacer

- No generar una guía por capítulo solo porque J.2 exista como otra idea.
- No publicar salida cruda de IA.
- No añadir disclaimers como sustituto de revisar hechos.
- No usar IA para inventar preguntas sobre escenas que no están en el canon.
- No convertir el Cuaderno/club en contenido escalado.
- No presentar opiniones generadas como comentarios del autor.
- No retener texto sensible “por si sirve más adelante”.
- No crear backend público bajo el paraguas de G.2.

## 11. Definition of Done cuando el trigger exista

- [ ] hay una pieza editorial real y owner humano;
- [ ] están delimitadas las fuentes canónicas y derechos;
- [ ] la IA solo produce un borrador interno;
- [ ] canon/spoilers/citas/preguntas se revisan manualmente;
- [ ] el resultado contiene criterio/experiencia humana material;
- [ ] no se presenta contenido no verificado como factual;
- [ ] no se introduce retención/PII innecesaria;
- [ ] el resultado pasa los mismos QA editoriales/a11y/SEO que cualquier contenido humano;
- [ ] no se automatiza publicación;
- [ ] si no aporta ahorro/calidad frente al flujo humano, se abandona sin coste hundido.

## 12. Relación con otras ideas

- **C.2:** el contenido de proceso real tiene mayor valor diferencial; G.2 puede ayudar a estructurarlo, no fabricarlo.
- **C.3:** preguntas reales de lectores son mejor fuente que preguntas sintéticas genéricas.
- **J.2:** una guía por capítulo solo se justifica por una necesidad real del club; G.2 no activa J.2 automáticamente.
- **G.3:** comparte el principio de IA como tooling con revisión contextual humana.
- **G.5:** no recoger conversaciones/preguntas reales para este uso sin política de privacidad específica.

## 13. Trazabilidad #135

Revisados:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original de guías/resúmenes IA revisados.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `CONDITIONAL`, workflow privado.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — people-first/spam/IA.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — club/contenido existente.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` y repo overrides — revisados; no autorizan feature pública.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — estado intermedio `DEFERIR` y razón: no es escasez prioritaria.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — no existe workstream runtime de G.2.
- `data/web-improvement-decisions-2026-08-28.json` — final `CONDITIONAL`.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — borradores internos permitidos solo con valor humano público.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — decisión mantenida y human review.
- pasadas posteriores — revisadas; no añaden un trigger que convierta la idea en `IMPLEMENT_NOW`.

## 14. Cierre

G.2 sobrevive a la criba únicamente como herramienta editorial privada y opcional. La historia `CONDITIONAL → DEFERIR → CONDITIONAL` no es incoherencia: expresa que puede ser útil en una tarea concreta, pero no constituye una prioridad ni una feature que el proyecto deba construir.