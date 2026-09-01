# C.3 · Contenido generado a partir de preguntas reales de lectores

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `IMPLEMENT_AFTER_CURRENT_DEBT`.

## Veredicto

#135 mantiene C.3 como trabajo válido: usar preguntas reales y repetidas como evidencia de demanda es preferible a idear páginas SEO especulativas. La implementación debe ser privacy-first: trabajar con señales agregadas, no almacenar conversaciones o PII «por si acaso».

## Hipótesis original

Recopilar preguntas del club de lectura, redes u otros canales y convertir las recurrentes en artículos/FAQ porque su demanda ya está validada.

## Evolución histórica

### Primera revisión → `IMPLEMENT_AFTER_CURRENT_DEBT`

Fuentes propuestas:

- Search Console;
- lectores;
- email;
- asistente.

La revisión fijó que la pregunta debe guardar su fuente de demanda y que la respuesta debe aportar contenido propio, no una pieza SEO sintética.

### Matriz intermedia → `IMPLEMENTAR`

La matriz la expresó como:

> capturar preguntas reales de lectores/redes/asistente y convertir las repetidas en contenido; registrar fuente agregada de demanda, sin PII.

### Autoridad final → `IMPLEMENT_AFTER_CURRENT_DEBT`

El cierre mantiene el valor pero respeta la cola de deuda existente:

> «Convertir preguntas reales repetidas de lectores/redes/asistente en contenido, agregadas y sin PII.»

### Revalidación independiente

C.3 se mantuvo. No apareció un motivo para rechazarla ni para elevarla por delante de deuda prioritaria.

## Por qué es diferente de keyword research genérico

La evidencia parte de una persona o superficie real:

```text
pregunta recurrente
→ intención normalizada
→ comprobar si ya existe respuesta canónica
→ decidir enriquecer URL existente o crear pieza nueva
→ responder con experiencia/fuentes reales
→ medir si resolvió la necesidad
```

No:

```text
lista de keywords
→ generar una URL por variante
→ rellenar artículos a escala
```

## Fuentes de demanda permitidas

### Search Console / Bing

Queries agregadas con impresiones/clics. No contienen identidad del usuario.

### Club/lectores/redes

Registrar la **pregunta normalizada**, frecuencia/contexto y canal, no nombres/handles salvo que exista necesidad editorial y permiso explícito.

### Email

No copiar mensajes privados completos al backlog. Extraer una intención agregada como «varios lectores preguntan por X».

### Asistente

La idea no autoriza almacenar conversaciones. Si se usa señal del asistente, debe seguir la gobernanza privacy-first de G.5: minimización, agregación, retención definida y sin PII.

## Modelo mínimo posible

Solo si hace falta una autoridad estructurada:

```json
{
  "intent": "qué es portal fantasy",
  "sourceClass": "search-console",
  "observations": 12,
  "window": "2026-08",
  "existingCanonical": "/cuaderno/que-es-el-portal-fantasy/",
  "decision": "ENRICH_EXISTING",
  "status": "reviewed"
}
```

No guardar la pregunta literal si contiene datos personales y no son necesarios.

## Jerarquía de decisiones

1. ¿Existe ya una URL que responde?
2. Si sí, enriquecer esa URL antes de crear otra.
3. Si no, ¿la pregunta se repite o tiene señal suficiente?
4. ¿David puede aportar una respuesta original/útil?
5. ¿La nueva URL tiene intención distinta y suficiente sustancia?
6. Solo entonces publicar.

## Relación con C.5

C.3 es una defensa contra C.5: no expandir por subgénero/edad/tono salvo que preguntas/queries demuestren una intención diferenciada.

## Relación con B.3/B.8

Una pregunta puede justificar una respuesta directa (B.3) o un TL;DR (B.8), pero esos son formatos de presentación. C.3 decide **qué necesidad merece contenido**.

## Relación con A.1

Si varias piezas reales forman una familia temática, A.1 puede agruparlas usando la arquitectura existente. No crear primero el cluster y luego fabricar preguntas que lo llenen.

## R.21 y R.31: investigación posterior que refuerza C.3

La sexta pasada localizó una señal propia concreta: «portal fantasy» tenía aproximadamente 91 impresiones / 1 clic en el snapshot operativo de Search Console. La acción correcta fue plantear un experimento sobre la URL ya expuesta, no crear más páginas.

La séptima pasada añadió Google Trends como **filtro de investigación**, recordando que 0–100 es interés relativo, no volumen absoluto, y que related/rising queries son inputs, nunca órdenes de crear URLs.

Ambos hallazgos refuerzan el principio de C.3: evidencia de demanda antes que ideación por volumen.

## Privacidad y gobernanza

- no PII en backlog editorial;
- no capturas de conversaciones privadas como dataset permanente;
- no inferir atributos sensibles;
- no enviar preguntas de usuarios a SaaS GEO por defecto;
- source class y conteo suelen bastar;
- borrar datos crudos cuando deja de existir necesidad.

## Definition of Done para una futura implementación

- fuente de demanda registrada;
- pregunta/intención normalizada;
- comprobación de URL existente;
- decisión ENRICH/NEW/NO_ACTION explícita;
- contenido original y revisado;
- ausencia de PII innecesaria;
- enlaces/canonicals correctos;
- no scaled content;
- métrica posterior ligada a la hipótesis, no a vanity scores.

## Qué NO hacer

- generar 100 FAQs sintéticas;
- almacenar todos los prompts del asistente;
- publicar una pregunta de una persona identificable sin necesidad/permiso;
- crear una URL por variación léxica;
- confundir Trends con volumen;
- reemplazar investigación editorial por un LLM que invente «preguntas frecuentes»;
- usar FAQPage como táctica SERP (A.7).

## Pasadas revisadas

Cuarta–quinta: sin cambio específico.  
Sexta: R.21 aporta caso real de demanda propia.  
Séptima: R.31 aporta Trends como filtro, no generador de URLs.  
Octava–decimoquinta: sin override que cambie C.3; mantienen evidencia-first/privacy-first.

## Trazabilidad

- hipótesis original;
- revisión 108/108;
- fuentes primarias people-first/spam;
- matriz final intermedia;
- R.21 Search Console;
- R.31 Google Trends;
- autoridad machine-readable;
- autoridad humana final;
- revalidación independiente.

## Recomendación para Clara/Claude

Implementar después de la deuda prioritaria como **workflow de demanda editorial**, preferiblemente manual-first. Automatizar solo cuando exista volumen que lo justifique, y siempre sobre datos agregados.