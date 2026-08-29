# A.7 · Revalidación de producción final

Fecha: 2026-08-29  
Base revalidada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`  
PR: #156  
Decisión operativa: **REJECT · NO_CODE · PRESERVE_HUMAN_FAQ**

## Decisión cerrada

No se añade `FAQPage` a las páginas de Samuel, Las manecillas del recuerdo ni a ninguna otra superficie con el objetivo de obtener rich results o “más presencia SEO”.

Una sección de preguntas y respuestas **visible, útil y factual** sigue siendo válida como contenido editorial/UX. Lo rechazado es convertirla en `FAQPage` por una ventaja de Google Search que ya no existe.

## Revalidación con la documentación oficial vigente

Fuente primaria:

https://developers.google.com/search/updates

Google documenta dos hitos definitivos:

- **7 de mayo de 2026:** los FAQ rich results dejan de aparecer en Google Search;
- **15 de junio de 2026:** Google elimina la documentación de la feature FAQ rich result porque ya no se muestra.

La antigua URL de documentación específica:

https://developers.google.com/search/docs/appearance/structured-data/faqpage

redirige actualmente al changelog general de Search Central, no a una guía de feature soportada.

Esto no es una interpretación de terceros: la superficie oficial de Google ya no ofrece FAQ rich results como feature de Search.

## Estado real del repo

Búsqueda sobre el `main` actual por `FAQPage`:

```text
0 resultados
```

Por tanto:

- no existe schema legacy que retirar;
- no hay migración pendiente;
- no hay builder reintroduciéndolo;
- no existe un bug de producción que justifique tocar HTML/JSON-LD.

La premisa histórica “escanear main antes de cerrar” queda cumplida.

## Por qué NO se añade un guardrail global anti-`FAQPage`

#135 dejó abierta la posibilidad de un test anti-regresión si no existía equivalente. Tras revalidarlo, **no se implementa hoy** por una razón de arquitectura:

Google haya retirado una presentación concreta no significa que el vocabulario Schema.org deba quedar prohibido para cualquier consumidor futuro.

Un test global del tipo:

```python
assert "FAQPage" not in all_public_html
```

convertiría una decisión de Search 2026 en una prohibición tecnológica indefinida. Eso sería más fuerte que la evidencia disponible y obligaría a desmontar el test si apareciera un consumidor real no-Google.

La protección suficiente hoy es:

1. decisión `REJECT` explícita en la autoridad documental;
2. ausencia comprobada en producción;
3. trigger objetivo para cualquier reintroducción.

Si vuelve a aparecer `FAQPage` sin consumidor documentado, entonces sí existe una regresión concreta que debe retirarse o cubrirse con un gate específico.

## FAQ humana que sí es válida

Puede mantenerse o añadirse HTML normal cuando responda preguntas reales, por ejemplo:

- género/tono;
- si una obra es independiente o parte de una serie, solo cuando sea un hecho real;
- dónde leer un fragmento;
- formatos/ediciones confirmados;
- recursos para clubes de lectura;
- preguntas repetidas de lectores.

No se inventan preguntas para completar una plantilla ni hechos sobre edad, audiolibro, saga, retailer o disponibilidad.

## `QAPage` no es sustituto

No se cambia `FAQPage` por `QAPage` para conservar la táctica. `QAPage` representa otra clase de superficie y no convierte una FAQ editorial redactada por el sitio en una página de preguntas/respuestas de usuarios.

## Alternativas descartadas definitivamente

1. **Añadir `FAQPage` a cada libro** — beneficio Google retirado.
2. **Generar preguntas genéricas por volumen** — contenido redundante y riesgo factual.
3. **Cambiar a `QAPage`** — semántica incorrecta si no existe esa experiencia real.
4. **Mantener schema porque “Schema.org lo define”** — existencia del vocabulario no demuestra consumidor/beneficio.
5. **Prohibición global permanente por test** — demasiado fuerte mientras no exista una regresión real.
6. **“Quizá ayuda a IA”** — no constituye un consumidor verificable ni justifica markup adicional.

## Trigger de reapertura

A.7 solo se reabre si ocurre uno de estos hechos:

- Google u otro buscador vuelve a documentar una feature relevante basada en `FAQPage`;
- un consumidor no-Google real y medible requiere el tipo;
- `FAQPage` reaparece en producción sin una justificación documentada;
- una necesidad editorial humana exige mejorar el FAQ visible, en cuyo caso se trabaja el contenido/UX sin asumir schema.

Cualquier reapertura debe documentar consumidor, páginas afectadas, beneficio y coste de mantenimiento.

## Definition of Done

- [x] historia de #135 preservada;
- [x] retirada del 07/05/2026 revalidada;
- [x] eliminación de documentación del 15/06/2026 revalidada;
- [x] antigua URL FAQPage comprobada;
- [x] `main@291c8c6…` escaneado por `FAQPage`;
- [x] cero usos actuales confirmados;
- [x] FAQ visible diferenciada de FAQ schema;
- [x] `QAPage` descartado como sustituto automático;
- [x] guardrail global permanente falsado como exceso actual;
- [x] triggers objetivos de reapertura definidos;
- [x] no existe cambio de runtime neto.

**Conclusión:** A.7 está terminada como `REJECT`. No hay nada que “implementar para SEO”; la mejora correcta es no reintroducir una feature retirada y seguir respondiendo preguntas humanas cuando el contenido lo justifique.