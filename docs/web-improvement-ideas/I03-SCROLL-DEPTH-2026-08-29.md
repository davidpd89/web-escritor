# I.3 · Scroll depth agregado en artículos

**Estado histórico final de PR #135:** `DEFER`  
**Naturaleza:** analítica opcional; no deuda técnica actual.  
**Regla:** no instrumentar scroll por curiosidad. Solo reabrir si una decisión editorial concreta depende de saber hasta dónde leen las personas.

## 1. Hipótesis original

I.3 proponía añadir eventos custom de GoatCounter para registrar profundidad de scroll agregada en artículos largos del Cuaderno, con la intención de decidir dónde cortar, resumir o ampliar contenido.

La idea partía de una intuición razonable —la profundidad puede aportar una señal de consumo—, pero #135 terminó corrigiendo el orden causal: **primero hay que saber qué decisión cambiaríamos con ese dato; después decidir si merece instrumentación**.

## 2. Evolución completa de la decisión

| Etapa | Estado / hallazgo | Consecuencia |
|---|---|---|
| Banco original | hipótesis | Eventos custom de GoatCounter para profundidad de lectura agregada. |
| Revisión 108/108 | `DEFER` | Sin una decisión asociada, scroll depth solo añade ruido. |
| Matriz operativa | `PILOTAR` | Puede probarse en una pregunta concreta y alcance pequeño; no necesita un nuevo SaaS. |
| Overrides | `DEFER` reafirmado | “No instrumentar por curiosidad”; reabrir solo si una decisión editorial depende del dato. |
| Autoridad final | `DEFER` | No compensa ahora frente a la falta de una pregunta decisional concreta. |
| Revalidación independiente | mantenido | I.1–I.5 se mantienen; no aparece evidencia que obligue a instrumentar más comportamiento. |

La aparente contradicción `PILOTAR` → `DEFER` no debe borrarse: la matriz demostró que técnicamente el piloto sería barato; la autoridad final decide que **el coste principal no es técnico sino analítico/operativo**: recopilar una métrica sin pregunta produce trabajo y falsas conclusiones.

## 3. Estado real de `main` revalidado el 29/08/2026

`main@291c8c677aaa7df635142687d1a6848e80ffcaa2` ya tiene:

- GoatCounter cargado como analítica ligera;
- `_gcEvent(...)` para eventos custom concretos;
- un bridge `dp:analytics` para módulos opt-in;
- un listener de scroll para la barra visual de progreso en páginas que optan por `data-reading-progress`.

Eso **no significa que I.3 esté implementada**.

La barra de progreso:

- modifica UI local;
- calcula `scrollY / altura del documento`;
- no es un evento de analítica;
- no prueba que se estén enviando hitos 25/50/75/100;
- no autoriza a reutilizar automáticamente su listener para tracking.

No se ha localizado en la inspección actual una instrumentación específica de `scroll depth` hacia GoatCounter.

## 4. Por qué `DEFER` sigue siendo correcto

Una cifra como “70 % de lectores llega al 50 %” no dice por sí sola:

- si el artículo es demasiado largo;
- si el lector obtuvo la respuesta y abandonó satisfecho;
- si el contenido posterior es irrelevante;
- si existe navegación hacia otra página;
- si el usuario volvió después;
- si el tráfico proviene de una intención distinta;
- si un cambio editorial mejoraría el resultado.

Sin una hipótesis previa, la métrica invita a optimizar por movimiento en pantalla en lugar de por utilidad.

## 5. Trigger exacto para reabrir I.3

Solo reabrir si existe una pregunta del tipo:

> “En esta familia concreta de artículos, creemos que una sección importante situada después de X no se alcanza; si la mayoría abandona antes, moveremos/resumiremos esa sección. Si no, no cambiaremos el contenido.”

El ticket/experimento debe declarar antes de instrumentar:

- URLs/familia afectada;
- pregunta;
- cambio que se haría en cada resultado plausible;
- ventana de medición;
- muestra mínima razonable;
- segmentos que sí/no se compararán;
- cuándo se retirará la instrumentación.

Si no puede escribirse esa decisión por adelantado, I.3 permanece `DEFER`.

## 6. Forma mínima de un futuro piloto

Si se cumple el trigger:

1. reutilizar GoatCounter existente;
2. no instalar Clarity/GA/Brevo Tracker solo para scroll;
3. instrumentar únicamente páginas del experimento;
4. enviar hitos discretos, no un evento continuo;
5. disparar cada hito una sola vez por carga/sesión cuando sea técnicamente razonable;
6. no enviar email, texto seleccionado, query completa ni identificadores de contacto;
7. documentar el payload exacto en I.2/E.8;
8. retirar o mantener únicamente si el experimento demuestra utilidad continuada.

Ejemplo conceptual de hitos:

- `article_scroll_25`
- `article_scroll_50`
- `article_scroll_75`
- `article_scroll_100`

Los nombres son ilustrativos, no una autorización para añadirlos ahora.

## 7. Métricas que NO deben confundirse

### Scroll visual

La barra `data-reading-progress` es feedback de interfaz.

### Scroll depth analítico

Es un evento enviado a un sistema de medición.

### Lectura real

Ninguno de los dos demuestra comprensión o lectura. Tiempo, scroll, viewport y eventos son proxies.

### Conversión

Una persona puede leer poco y realizar la acción correcta; o leer todo y no encontrar valor. No usar profundidad como KPI universal.

## 8. Privacidad y minimización

Aunque un porcentaje de scroll parezca inocuo, I.3 está subordinada a I.2/I.5:

- inventariar host/payload;
- documentar finalidad;
- confirmar almacenamiento/cookies reales del proveedor;
- evitar combinar el evento con una identidad de newsletter;
- no construir un perfil lector individual;
- revisar retención si cambia el contrato actual.

El objetivo histórico era **agregado sin PII**. No convertir el piloto en analítica individual.

## 9. Relación con otras ideas

- **D.3:** barra visual de progreso; puede existir sin tracking.
- **I.2:** cualquier nuevo evento/vendor debe aparecer en el inventario de terceros/consentimiento.
- **I.4:** correlación de resultados debe ser manual-first y agregada, no identity graph.
- **I.5:** la revisión periódica puede retirar eventos que dejaron de responder una pregunta.
- **Q.3:** si se abre I.3, registrar hipótesis/baseline/resultado como experimento.

## 10. Qué no hacer

- No añadir eventos 25/50/75/100 sitewide “porque son estándar”.
- No instalar un SDK de behavioral analytics para resolver esta idea.
- No inferir calidad editorial directamente de scroll.
- No mezclar email/contact ID con navegación.
- No medir páginas breves donde la métrica carece de sentido.
- No dejar el tracking permanente después de un piloto sin una finalidad vigente.
- No reutilizar el listener de `data-reading-progress` como tracking implícito.

## 11. Definition of Done si se reabre

- [ ] existe una pregunta editorial concreta;
- [ ] está escrito qué decisión cambiará según el resultado;
- [ ] alcance de URLs limitado;
- [ ] reutiliza GoatCounter existente, salvo evidencia contraria;
- [ ] payload agregado/minimizado y sin PII;
- [ ] I.2/E.8 actualizados;
- [ ] experimento registrado en Q.3;
- [ ] no se confunde scroll con lectura/comprensión;
- [ ] hay criterio de retirada;
- [ ] el resultado produce una decisión documentada, incluido `NO_CHANGE`.

## 12. Trazabilidad #135

Revisados para esta reconstrucción:

- `docs/IDEAS-MEJORA-WEB-2026-08-27.md` — hipótesis original I.3;
- `docs/IDEAS-MEJORA-WEB-REVISION-2026-08-27.md` — `DEFER` y regla de decisión previa;
- `docs/IDEAS-MEJORA-WEB-MATRIZ-FINAL-2026-08-28.md` — `PILOTAR` con GoatCounter custom event;
- `docs/IDEAS-MEJORA-WEB-OVERRIDES-2026-08-28.md` — reafirma `DEFER` por curiosidad analítica;
- `docs/IDEAS-MEJORA-WEB-REPO-CROSSCHECK-2026-08-27.md` — contexto de capacidades existentes;
- `docs/IDEAS-MEJORA-WEB-CODE-BLUEPRINTS-2026-08-28.md` — no abre blueprint propio para I.3;
- `data/web-improvement-decisions-2026-08-28.json` — autoridad machine-readable final;
- `docs/PR135-FINAL-AUTHORITY-2026-08-28.md` — `DEFER`;
- `docs/PR135-INDEPENDENT-REVALIDATION-2026-08-28.md` — estado mantenido.

## 13. Cierre

I.3 no está rechazada porque medir scroll sea imposible o caro. Está diferida porque el proyecto ya tiene suficiente analítica para formular preguntas antes de añadir más eventos. La secuencia correcta es **decisión → experimento → instrumentación mínima**, no al revés.