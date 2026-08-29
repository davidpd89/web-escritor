# G.3 · Alt text asistido por IA como tooling

**Estado histórico final de PR #135:** `CONDITIONAL`  
**Uso permitido:** sugerencia/borrador interno cuando el volumen o la tarea lo justifiquen.  
**Regla innegociable:** el `alt` final depende del propósito y contexto de la imagen y requiere revisión humana antes de commit/publicación.  
**Naturaleza de esta PR:** documentación; no genera ni cambia atributos `alt`.

## 1. Hipótesis original

G.3 proponía usar IA para sugerir textos alternativos en el volumen de imágenes de portadas/recomendaciones, con validación manual obligatoria y sin automatización ciega en CI.

La revisión mantuvo la idea únicamente como **tooling opcional**. La razón principal es semántica: describir visualmente una imagen no equivale a escribir un buen `alt`. El texto alternativo depende de **para qué está esa imagen en esa página**.

## 2. Evolución completa

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | IA propone alt, humano valida antes de commit. |
| Revisión 108/108 | `CONDITIONAL` | El propósito/contexto manda; skill/borrador, nunca CI automático. |
| Matriz operativa | `PILOTAR COMO TOOLING` | Puede ahorrar trabajo, pero la revisión contextual es parte obligatoria del proceso. |
| Autoridad final | `CONDITIONAL` | Reafirma que la IA solo asiste; no publica. |
| JSON final | `CONDITIONAL` | Estado machine-readable alineado. |
| Revalidación independiente | mantenido | Cambios IA deben ser human-reviewed y no abrir automatización/retención innecesaria. |

`PILOTAR COMO TOOLING` es una etapa intermedia compatible con el estado final: solo se prueba cuando existe un trigger real; no es una implementación global pendiente.

## 3. Por qué el contexto manda

La misma imagen puede requerir resultados distintos:

- **Portada dentro de una ficha cuyo título ya está al lado:** repetir literalmente todo el texto de la cubierta puede ser redundante.
- **Portada enlazada en un listado:** puede necesitar identificar la obra/función del enlace.
- **Imagen decorativa de ambiente:** puede requerir `alt=""` en vez de una descripción poética generada.
- **Infografía/mapa/timeline:** una frase visual breve puede no proporcionar equivalente suficiente; quizá necesita texto adyacente más completo.
- **Foto de autor:** el nivel de detalle útil depende del contexto editorial.
- **Captura que demuestra un estado/UI:** el alt debe transmitir la información relevante, no enumerar píxeles.

Un modelo que solo ve el asset no conoce necesariamente ese propósito.

## 4. Trigger correcto

G.3 solo compensa si:

- existe un lote/volumen real que hace costosa la redacción inicial;
- hay suficiente contexto disponible para la persona revisora;
- la herramienta no introduce más fricción que escribir el alt directamente;
- el contenido no exige una interpretación que el modelo no puede verificar;
- el resultado nunca entra en producción sin revisión.

Con pocas imágenes o contenido muy contextual, redactar manualmente sigue siendo la ruta preferida.

## 5. Workflow recomendado

1. Identificar imagen, página y propósito.
2. Determinar primero si necesita alt no vacío.
3. Proporcionar a la herramienta solo el contexto mínimo necesario y permitido.
4. Obtener una o varias sugerencias breves.
5. Revisar contra el asset y el contenido de la página.
6. Eliminar redundancias con caption/título/texto vecino.
7. Comprobar que no inventa nombres, edades, raza, emociones, relaciones o hechos no verificables.
8. Ajustar longitud/especificidad al uso real.
9. Commit solo después de aprobación humana.
10. Pasar los checkers/auditorías de imágenes/HTML existentes.

## 6. Política para imágenes decorativas

Un riesgo específico del “alt con IA” es llenar de descripciones assets que deberían quedar fuera del árbol accesible.

Antes de generar hay que responder: **¿esta imagen aporta información o función que no está ya expresada?**

Si la respuesta es no y la imagen es decorativa, la solución correcta puede ser `alt=""`/tratamiento equivalente, no un texto generado.

Por tanto un buen tooling debería permitir como salida válida:

- `DECORATIVE / alt=""`;
- `FUNCTIONAL / describir destino o función`;
- `INFORMATIVE / proponer alt contextual`;
- `COMPLEX / requiere equivalente textual más amplio`.

## 7. Qué revisar manualmente

- propósito de la imagen en esa URL;
- nombres propios/canon;
- texto visible que ya la acompaña;
- función si la imagen está dentro de un enlace/control;
- nivel de detalle útil;
- información sensible o inferida;
- idioma/voz consistente;
- duplicación con captions;
- si la imagen necesita en realidad una descripción larga/recurso alternativo.

No basta con confirmar que “la imagen se parece a lo que dice el alt”.

## 8. Automatización que #135 rechazó implícitamente

No debe existir un CI que:

1. detecta `alt` vacío/faltante;
2. llama automáticamente a un modelo;
3. escribe el resultado;
4. commitea/publica.

Ese flujo elimina precisamente la decisión contextual que hace accesible el contenido y puede convertir errores de visión/identificación en texto factual del sitio.

Sí puede existir un checker que detecte `alt` ausente/contratos HTML y obligue a que un humano decida. Eso es distinto de autogenerarlo.

## 9. Privacidad, derechos y coste

El uso de un proveedor concreto debe evaluarse en el momento del piloto:

- ¿se envía el asset fuera del repositorio?
- ¿contiene una imagen privada/no publicada?
- ¿el proveedor retiene inputs/outputs?
- ¿hay coste/cuota?
- ¿se está enviando material con derechos de terceros?

G.3 no autoriza automáticamente subir todas las imágenes del repositorio a un servicio externo.

## 10. Qué no hacer

- No generar alt para imágenes decorativas solo para evitar `alt=""`.
- No repetir “imagen de / foto de” innecesariamente.
- No copiar OCR de una portada como alt por defecto.
- No inferir atributos sensibles o intenciones emocionales.
- No inventar contenido no visible/canónico.
- No publicar sin revisión contextual.
- No autocorregir en CI.
- No convertir alt en keywords SEO.
- No añadir un SaaS permanente si un prompt/manual ocasional resuelve el volumen real.

## 11. Definition of Done cuando se pilote

- [ ] el trigger de volumen/ahorro está documentado;
- [ ] cada imagen se clasifica por función antes de generar;
- [ ] `alt=""` sigue siendo una decisión válida para decorativas;
- [ ] la sugerencia se revisa viendo la imagen y su página;
- [ ] no hay invenciones/inferencias sensibles;
- [ ] no se duplica innecesariamente caption/título;
- [ ] assets complejos reciben alternativa apropiada, no un alt insuficiente;
- [ ] ningún output se commitea automáticamente;
- [ ] se revisan privacidad/derechos del proveedor si se usa uno externo;
- [ ] el piloto se abandona si no mejora tiempo/calidad frente a redacción manual.

## 12. Relación con otras ideas

- **F.3:** media informativa compleja puede necesitar alternativas más extensas; un alt corto no sustituye transcript/captions.
- **C.7:** mapas/timelines visuales requieren versión textual accesible; G.3 no resuelve por sí solo una pieza compleja.
- **O.2:** social cards no necesariamente necesitan el mismo alt/uso que la imagen editorial en página.
- **G.2:** comparte el patrón “IA como borrador interno + revisión humana”.
- **E.1:** formatos AVIF/WebP cambian bytes, no la semántica alt; no duplicar alt entre derivados como autoridades separadas.

## 13. Trazabilidad #135

Revisados:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original.
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `CONDITIONAL`, contexto/purpose.
- `docs/IDEAS-MEJORA-WEB-FUENTES-PRIMARIAS-2026-08-27.md` — accesibilidad/IA.
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — volumen/pipelines de imágenes existentes.
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` y `...OVERRIDES-REPO...` — revisados, sin cambio a automatización.
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `PILOTAR COMO TOOLING`.
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — no abre un workstream de autogeneración/CI.
- `data/web-improvement-decisions-2026-08-28.json` — final `CONDITIONAL`.
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — alt IA solo tooling con revisión contextual.
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — decisión mantenida/human-reviewed.
- pasadas posteriores — revisadas; no aparece evidencia que justifique generación automática.

## 14. Cierre

G.3 no busca que la IA “escriba los alt”. Busca, como mucho, reducir el trabajo de borrador cuando exista volumen real, manteniendo la decisión accesible donde debe estar: en una persona que conoce la imagen, su función y el contenido que la rodea.