# 10 — Referencias, expertos y patrones: criterio, no copia

## 1. Objetivo

El proyecto ya dispone en Drive de una matriz de referencias reales. Esta PR no crea otra galería de inspiración.

Crea un **protocolo de investigación** para que Claude pueda consultar fuentes profesionales, extraer decisiones y justificar dónde aplicarlas sin copiar una estética completa.

## 2. Regla de procedencia

Toda referencia debe responder:

```text
qué problema resolvía
qué decisión concreta tomamos de ella
qué rechazamos
por qué aplica a David
qué riesgo tiene
cuándo fue revisada
```

Si solo podemos decir «se ve premium», no entra.

## 3. Jerarquía de fuentes

### Nivel A — normas / plataformas

- W3C/WAI;
- MDN/web.dev para comportamiento del navegador;
- Apple HIG para principios de plataforma/mobile cuando corresponda;
- documentación oficial de motores/herramientas.

Gobiernan constraints y comportamiento, no estética.

### Nivel B — criterios profesionales

- Webby Awards judging criteria;
- CSS Design Awards criterios/metodología;
- Awwwards como observatorio de tendencias/patrones, no estándar técnico.

Sirven para formular preguntas de calidad global.

### Nivel C — case studies de estudios

Priorizar estudios que explican proceso/constraints:

- Pentagram;
- AREA 17;
- Bureau for Visual Affairs;
- Grape;
- UNCOMMON;
- otros estudios con case study verificable.

### Nivel D — productos editoriales reales

- publicaciones literarias;
- revistas culturales;
- editoriales;
- museos/archivos cuando la tarea sea comparable;
- herramientas editoriales.

Analizar el producto vivo, no capturas antiguas aisladas.

### Nivel E — galerías

- Awwwards;
- CSSDA galleries;
- SiteInspire;
- Httpster;
- Godly;
- Land-book;
- Page Flows para flujos/UI cuando corresponda.

Solo para descubrir candidatos. Después verificar el sitio/case study real.

## 4. Webby: scorecard de preguntas

Los criterios actuales de websites/mobile sites se pueden traducir a preguntas internas:

### Content

- ¿el diseño deja que el contenido real domine?;
- ¿hay información de relleno?

### Structure & Navigation

- ¿una persona entiende dónde está?;
- ¿la arquitectura es clara sin tutorial?

### Visual Design

- ¿hay jerarquía, craft y coherencia?;
- ¿es reconocible sin efectos?

### Functionality

- ¿todo responde correctamente en estados reales?

### Interactivity

- ¿la interacción aporta comprensión/continuidad?

### Innovation

- ¿la solución es propia del contenido o un efecto de moda?

### Overall Experience

- ¿las decisiones forman un todo coherente?

No convertir este scorecard en una nota falsa de jurado.

## 5. Apple HIG: uso adecuado

Utilizar para revisar principios como:

- hierarchy;
- legibility;
- adaptability;
- touch;
- platform conventions;
- typography/readability.

No aplicar patrones nativos iOS a una web porque «Apple diseña bien».

La web debe seguir sintiéndose web.

## 6. W3C/WCAG

Normativa para:

- reflow;
- zoom;
- orientation;
- target size;
- text spacing;
- focus;
- contrast;
- motion.

No usar una galería de premios para contradecir estas restricciones.

## 7. Referencias ya establecidas en Drive

El doc 16 ya cita entre otras:

### Pentagram — The Paris Review

Tomar como pregunta/metodología:

- cómo actualizar una institución literaria sin perder herencia;
- cómo identidad/editorial pueden convivir con archivo y contenido.

No copiar:

- logo;
- grilla exacta;
- color;
- tipografía.

### AREA 17 — Fondation Cartier

Tomar:

- relaciones entre archivo, contenido y navegación;
- digital experience como extensión de institución/contenido.

### AREA 17 — Harvard University Press

Tomar:

- arquitectura de contenido editorial;
- lectura/descubrimiento;
- tratamiento de catálogo.

### Grape — Son Daven

Tomar:

- craft físico real;
- proceso material con procedencia.

Rechazar para nuestro contexto:

- WebGL/parallax/espectáculo si no aporta lectura.

### Bureau for Visual Affairs / It's Nice That

Tomar:

- sistemas editoriales contemporáneos;
- relación entre contenido dinámico y personalidad.

### UNCOMMON — PieterKoopt

Tomar solo decisiones que el case study permita justificar; no importar lenguaje gráfico sin relación con autor/literatura.

## 8. Publicaciones editoriales

### London Review of Books

Analizar:

- tipografía como navegación;
- densidad editorial;
- grids/ledgers;
- escasez de UI ornamental;
- tratamiento de archivo.

No copiar su apariencia literal.

### The Paris Review

Analizar:

- relación identidad/contenido;
- peso de imagen y texto;
- archivo literario.

### The New York Review of Books / The New Yorker / Granta / n+1 / The Marginalian, etc.

Pueden ser útiles para estudiar problemas concretos, pero cada incorporación necesita una ficha de procedencia actualizada.

No meter diez referencias porque «son revistas».

## 9. Page Flows

Uso potencial:

- navegación;
- search;
- subscription;
- onboarding ligero;
- dialogs;
- task flows.

No es autoridad de art direction editorial. Sirve para patrones de flujo e interacción.

## 10. Mobbin / patrones de producto

Solo si una tarea se aproxima a producto/app —p. ej., filtros, formularios, results—.

No convertir una web literaria en interfaz SaaS por importar patrones móviles de apps.

## 11. CSS Design Awards / Awwwards

Usar para:

- descubrir estudios;
- observar craft;
- identificar motion/interaction patterns;
- comparar ambición.

Aplicar filtro fuerte:

- ¿funciona sin loader?;
- ¿funciona mobile?;
- ¿contenido sigue accesible?;
- ¿hay WebGL innecesario?;
- ¿la estética depende de scroll-jacking?;
- ¿sería adecuada para un autor?

Una web premiada puede ser una mala referencia para nuestro problema.

## 12. Registro de referencias

Proponer fichero futuro interno:

```text
data/design-reference-ledger.json
```

Ejemplo:

```json
{
  "id": "ref-paris-review-pentagram",
  "name": "The Paris Review — Pentagram",
  "sourceUrl": "https://www.pentagram.com/work/the-paris-review",
  "reviewedAt": "2026-08-27",
  "problem": ["literary identity", "archive"],
  "take": ["heritage + contemporary system"],
  "reject": ["literal visual copying"],
  "appliesTo": ["author", "editorial"],
  "status": "reference"
}
```

No copiar screenshots ajenos al repo sin revisar derechos. Guardar URL/notas y, si hace falta evidencia temporal, usar captura solo dentro del entorno de investigación autorizado.

## 13. Protocolo de benchmark por problema

Ejemplo: «los artículos mobile son planos».

No buscar:

> best mobile design 2026

Buscar conjuntos comparables:

1. publicación con artículo largo;
2. editorial/book page;
3. archivo/autor;
4. uno o dos ganadores con solución móvil fuerte;
5. guideline de plataforma.

Para cada uno:

- screenshot mobile actual;
- apertura;
- ritmo;
- media;
- navegación;
- section boundaries;
- related content;
- footer;
- qué NO funciona para nosotros.

## 14. Copying detector

Antes de aprobar una propuesta basada en referencia, responder:

- si quitamos logo/nombre de David, ¿parece demasiado el referente?;
- ¿hemos copiado composición + color + tipo + interacción simultáneamente?;
- ¿la decisión se justifica por contenido propio?;
- ¿podríamos explicarla sin mencionar al referente?

Si no, volver atrás.

## 15. Trend decay

Toda referencia de tendencia tiene fecha.

Revisar cada 6–12 meses o cuando se reabra una familia importante.

Normas/WCAG se actualizan por versión oficial; case studies/galleries pueden envejecer más rápido.

## 16. Referencias negativas

Guardar también anti-referencias:

- templates de landing SaaS;
- bento portfolios;
- black/gold author sites;
- AI-generated literary landing pages;
- hero + 3 feature cards + testimonials + CTA;
- websites con scroll-jacking espectacular pero mala lectura.

Sirven para que Claude reconozca patrones que debe rechazar.

## 17. Herramientas de búsqueda web

Claude puede usar web research para:

- localizar case studies actuales;
- comprobar que una referencia sigue viva;
- contrastar documentación;
- ver actualizaciones de premios/criterios;
- encontrar herramientas nuevas.

Pero debe guardar la **fuente**, no solo la conclusión.

## 18. Revisión mensual de tooling/referencias

No hace falta investigar todas las semanas.

Revisar cuando:

- aparece una nueva capacidad MCP relevante;
- cambia el stack;
- una herramienta se depreca;
- se abre un rediseño de familia;
- necesitamos resolver un problema nuevo.

## 19. Preguntas para el agente de referencias

1. ¿Cuál es el problema exacto?
2. ¿Qué sitios lo resuelven de manera comparable?
3. ¿Hay un case study que explique por qué?
4. ¿Qué decisión es transferible?
5. ¿Qué depende de su marca/contenido?
6. ¿Qué falla en mobile/a11y/performance?
7. ¿Qué parte debemos rechazar?
8. ¿Cómo se traduce a nuestro contrato 16/17?

## 20. Criterio final

Una buena referencia **reduce incertidumbre**.

Una mala referencia solo añade cosas que copiar.

El repositorio debe recordar decisiones, no coleccionar tendencias.