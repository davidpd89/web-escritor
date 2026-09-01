# P.4 · Enlace cruzado herramienta ↔ contenido — reconstrucción completa desde PR #135

Fecha de reconstrucción: 2026-08-29  
Fuente histórica primaria: snapshot `8e72321d047c0445c5ac411ebe242af8a0386929` de PR #135.  
Estado final histórico: `IMPLEMENT_AFTER_CURRENT_DEBT`.

## 1. Hipótesis original

P.4 proponía conectar herramientas con artículos, recomendaciones o recursos relacionados: por ejemplo, una herramienta de worldbuilding con una guía del Cuaderno sobre worldbuilding y el artículo de vuelta con la herramienta.

El objetivo no era fabricar enlaces internos por SEO, sino mejorar el siguiente paso del usuario entre una necesidad práctica y contenido editorial relevante.

## 2. Evolución dentro de #135

### Revisión exhaustiva 27/08

Estado: `IMPLEMENT_AFTER_CURRENT_DEBT`.

Valor estimado alto. La revisión propuso:

- modelar `relatedContent/relatedTools` en autoridades;
- generar enlaces contextuales;
- checker de URLs;
- límites de densidad;
- evitar enlaces manuales dispersos que se rompan.

### Matriz final 28/08

Decisión: `IMPLEMENTAR ALTO`.

La matriz confirmó que era una de las mejoras con mejor relación valor/coste del ecosistema de herramientas. Se insistió en derivar la relación de un registry para no mantener vínculos manuales huérfanos.

### Autoridad final humana + machine-readable

Estado: `IMPLEMENT_AFTER_CURRENT_DEBT`.

No fue rechazado ni degradado: se pospone únicamente para no competir con deuda prioritaria.

## 3. Pasadas posteriores / revalidación independiente

La revalidación independiente mantiene P.4 y lo coloca en la primera ola de mejoras gratuitas con valor verificable.

No aparece una corrección posterior que cambie su naturaleza. Las pasadas de internal linking y arquitectura refuerzan la regla general: extender autoridades existentes y validarlas, no crear un segundo grafo.

## 4. Evidencia actual de `main`

`data/content-registry.json` ya dispone de una capacidad estructural que debe reutilizarse:

- `relatedIds` existe en defaults;
- varias obras/contenidos ya lo usan;
- las URLs, IDs, audience/jobs y jerarquía viven en el registry.

`data/tools-hub.json` describe cada herramienta con:

- `slug`;
- `name`;
- `href`;
- categoría;
- resumen;
- privacidad;
- tipo de input;
- source document.

Sin embargo, la autoridad de tools no contiene actualmente un campo `relatedContent` y no se ha demostrado una cobertura sistemática herramienta↔contenido.

La conclusión práctica es importante: **P.4 no necesita inventar infraestructura de enlaces internos**. Necesita extender el registry/autoridad adecuada y generar relaciones verificables desde allí.

## 5. Principio de diseño

Un enlace cruzado solo existe si responde a una intención humana clara.

Ejemplos válidos:

- herramienta de diálogo → guía sobre convenciones de diálogo;
- herramienta de metadatos → contenido sobre ficha de libro/OG/JSON-LD;
- herramienta de worldbuilding → artículo sobre worldbuilding real;
- artículo práctico → herramienta que permite aplicar inmediatamente lo explicado.

Ejemplos inválidos:

- enlazar todas las herramientas a todos los artículos de la misma categoría;
- inyectar bloques «También te puede interesar» sin relación semántica real;
- añadir enlaces solo para aumentar densidad interna;
- duplicar navegación principal o footer.

## 6. Modelo recomendado

Preferencia: reutilizar `content-registry.json` como grafo canónico.

Opciones compatibles a evaluar en implementación:

- ampliar `relatedIds` en entries de tipo `tool`;
- o añadir un campo tipado que distinga relaciones editoriales (`relatedContent`, `relatedTools`) si la semántica lo requiere.

No crear otro JSON paralelo si `relatedIds` puede expresar de forma suficiente el caso.

Cada relación debe resolver IDs canónicos y generar URLs desde el registry, nunca hardcodear la URL en dos sitios.

## 7. Reglas de densidad y jerarquía

- 1–3 relaciones de alta relevancia suelen ser suficientes;
- no repetir destinos ya presentes en navegación inmediata;
- priorizar un «siguiente paso» claro;
- el enlace debe describir el destino, no usar anchors SEO artificiales;
- relaciones bidireccionales solo cuando sean útiles en ambos sentidos;
- no convertir todas las relaciones en cards grandes si un enlace textual basta.

## 8. Implementación futura sugerida

1. inventariar herramientas y contenido con intención compartida;
2. seleccionar un piloto pequeño de 3–5 relaciones;
3. añadir relaciones en la autoridad existente;
4. generar/renderizar el bloque contextual;
5. checker de IDs/URLs inexistentes;
6. evitar duplicados y self-links;
7. comprobar navegación con teclado y responsive;
8. medir clics agregados solo si ya existe un evento adecuado y la métrica cambia una decisión.

## 9. Definition of Done

- relaciones almacenadas en autoridad canónica;
- ningún href huérfano;
- cero self-links;
- cero duplicados del mismo destino en el bloque;
- copy descriptivo y humano;
- no se rompe `noindex`/gating;
- herramientas privadas no cargan analytics/terceros por el bloque;
- no añade un nuevo registry paralelo;
- el checker entra en CI si la relación se convierte en contrato generado;
- se prueba al menos una relación herramienta→contenido y una contenido→herramienta cuando ambas direcciones tengan sentido.

## 10. Relación con otras ideas

- **A.3:** el grafo interno ya tiene auditor; P.4 debe integrarse, no duplicarlo.
- **A.1/A.2:** los hubs existentes siguen siendo autoridad de arquitectura.
- **D.11:** el bloque puede servir como siguiente acción en ciertos estados vacíos, pero no debe usarse como parche genérico.
- **P.1:** export y discoverability son capacidades distintas.
- **Q.3:** cualquier experimento de copy/posición del bloque puede registrarse en el registry de experimentos.

## 11. Conclusión

P.4 es trabajo válido y de alto retorno, pero después de la deuda actual. `main` ya tiene las piezas base —content registry, `relatedIds`, tools hub—, así que la implementación correcta consiste en extender esas autoridades y generar relaciones por intención real, no crear un segundo sistema de interlinking.