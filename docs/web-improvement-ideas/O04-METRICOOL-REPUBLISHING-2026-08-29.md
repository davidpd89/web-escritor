# O.4 · Republicación evergreen mediante Metricool

Fecha de reconstrucción: 2026-08-29  
Fuente histórica: PR #135, snapshot `8e72321d047c0445c5ac411ebe242af8a0386929`.  
Estado histórico final: `EXTERNAL_OPERATION`.

## Veredicto

#135 concluyó que reutilizar contenido evergreen con Metricool puede ser razonable, pero **no es una feature de la web**. Es una operación editorial externa que debe ejecutarse en la cuenta/herramienta real, con límites de frecuencia, UTM y revisión humana.

Git solo puede documentar el workflow; no puede demostrar que publicaciones estén programadas o que la cuenta esté correctamente conectada.

## Hipótesis original

Programar republicación estacional de contenido evergreen del Cuaderno con Metricool, ya presente en el stack, en vez de asumir que solo el contenido nuevo merece promoción.

## Evolución

### Revisión

La revisión consideró razonable reutilizar evergreen siempre que no se convierta en spam ni requiera nueva infraestructura del sitio.

### Matriz → `IMPLEMENTAR OPERATIVO`

La matriz formuló:

> Metricool ya está en stack. Conectar MCP vía OAuth cuando se autorice y reutilizar evergreen según analytics.

### Autoridad final → `EXTERNAL_OPERATION`

El cierre separó correctamente repositorio y operación:

> Metricool ya está en stack; MCP por OAuth cuando se autorice. Lectura/analytics por defecto; publicar/editar solo con instrucción explícita.

### Revalidación independiente

O.1–O.4 se mantuvieron.

## Revalidación actual de `main`

El runtime actual incluye `tracker.metricool.com` en CSP y documentación del shell, lo que demuestra que Metricool forma parte de la capa analítica del sitio.

Eso **no** demuestra:

- que una cuenta social concreta esté conectada;
- que exista calendario de republicación;
- que MCP/OAuth esté autorizado;
- que haya posts programados;
- que la atribución UTM esté funcionando.

Por tanto el estado sigue siendo `EXTERNAL_OPERATION`.

## Qué contenido es candidato

Solo piezas evergreen con valor vigente, por ejemplo:

- guías del Cuaderno;
- artículos de proceso que sigan siendo actuales;
- recursos/herramientas estables;
- piezas de universo cuando no dependan de campaña temporal.

No republicar automáticamente:

- anuncios caducados;
- fechas/eventos pasados;
- “ya disponible” fuera de contexto;
- precios/retailers sin revalidación;
- convocatorias cerradas;
- posts que dependan de una noticia temporal.

## Workflow editorial recomendado

```text
canonical URL
content type
last reviewed
social candidates
platform
copy
asset
UTM
frequency cap
status
publishedAt
result/notes
```

La fuente de verdad sigue siendo el contenido canónico del sitio; Metricool distribuye derivados.

## Frecuencia

No convertir “evergreen” en “repetir indefinidamente”. Debe existir:

- ventana mínima entre repeticiones;
- variedad de piezas;
- revisión previa si ha pasado suficiente tiempo;
- cancelación si el contenido dejó de ser factual/útil.

## UTM y medición

Si se usa UTM, mantener taxonomía consistente:

```text
utm_source=<red>
utm_medium=social
utm_campaign=<campaña/evergreen>
utm_content=<pieza/variante>
```

No crear parámetros diferentes por operador sin una autoridad común.

Métricas útiles:

- referral sessions/clicks;
- signups atribuibles si la arquitectura existente lo soporta;
- interacciones sociales;
- visitas a obra/herramienta;
- comparación de piezas, no vanity score aislado.

## MCP / automatización

Si se usa integración MCP/plugin:

- OAuth/autorización explícita;
- lectura/analytics por defecto;
- publicación, edición o borrado solo con instrucción explícita;
- no programar posts autónomamente desde un workflow de código;
- preservar revisión humana del copy.

## Relación con O.3

O.3 rechazó bloques públicos de social copy. O.4 es la alternativa correcta: preparar el copy en la capa editorial externa, no contaminar el artículo público.

## Relación con C.1

La republicación evergreen no debe pisar campañas de lanzamiento. C.1 gobierna secuencias temporales de Manecillas; O.4 reutiliza piezas estables bajo otra cadencia.

## Relación con I.4

La medición de contenido → acción puede aprovechar UTMs/exports ya existentes. O.4 no autoriza otro tracker.

## Qué NO hacer

- añadir código de scheduling a la web;
- publicar automáticamente porque una URL tenga etiqueta evergreen;
- usar el tracker Metricool como prueba de que publishing está configurado;
- repetir el mismo post con alta frecuencia;
- republicar datos caducados;
- generar copy social sin revisión;
- confundir `DOCUMENTED` con `CONFIGURED_LIVE`.

## Evidencia necesaria para `CONFIGURED_LIVE`

Fuera de Git:

- cuenta/red conectada;
- permisos correctos;
- publicación de prueba o calendario visible;
- URL/UTM comprobada;
- ownership de la cuenta;
- procedimiento de pausa/cancelación.

## Trazabilidad

- backlog original O.4;
- revisión 108/108;
- matriz `IMPLEMENTAR OPERATIVO`;
- autoridad final `EXTERNAL_OPERATION`;
- revalidación independiente;
- evidencia actual del runtime Metricool.

## Recomendación

Mantener O.4 como operación editorial externa. No requiere cambios runtime. Cuando se ejecute, usar Metricool con revisión humana, UTMs consistentes y límites de frecuencia; cualquier acción de publicación necesita autorización explícita.