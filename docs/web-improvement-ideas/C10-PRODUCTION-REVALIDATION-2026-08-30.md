# C.10 · Revalidación de producción — archivo de prensa

Fecha: 2026-08-30  
Base comprobada: `main@291c8c677aaa7df635142687d1a6848e80ffcaa2`.

## Veredicto

**CONDITIONAL · ARCHIVE_MODEL_READY · VERIFIED_COVERAGE_VOLUME_GATE_NOT_MET · NO_CODE**

La idea sigue siendo válida como evolución de `prensa.html`, pero hoy no existe volumen suficiente de cobertura externa independiente y verificada para justificar publicar una cronología de prensa.

## 1. Owner público existente

`prensa.html` ya es la autoridad pública de prensa y contiene el press kit: biografías, fichas técnicas, materiales, recursos y contacto. C.10 no debe crear `/archivo-prensa/`, `/media/` ni otra landing paralela.

La evolución correcta, cuando exista material suficiente, sigue siendo:

```text
una autoridad factual de datos
→ validación
→ sección de cobertura/apariciones dentro de prensa.html
```

## 2. Drive confirma el patrón, pero añade un gate que importa

El documento de Drive `22 — AUTOR + PRENSA + EVENTOS MASTER SPEC V1 — RETRATO · TRAYECTORIA · AGENDA · ARCHIVO · MEDIA` ya define el diseño de cobertura:

```text
fecha | medio/publicación | tipo | titular/contexto | enlace
```

También fija una condición explícita antes de extender el patrón: probar una lista de prensa con **5–8 entradas reales**.

Ese requisito evita diseñar primero una cronología vacía y buscar después contenido con el que rellenarla.

## 3. Investigación externa actual

La búsqueda web del 30/08/2026 distingue cuatro clases que no deben mezclarse:

### A. Cobertura editorial independiente candidata

Se localiza al menos una pieza de Bookdala publicada por la propia cabecera/redacción sobre `Samuel entre mundos` y la Feria del Libro de Madrid:

- `Fantasía juvenil con voz propia en la Feria del Libro de Madrid` — Bookdala, junio de 2026.

La propia presencia de Bookdala en LinkedIn la describe como pieza de `Redacción` / `Bookdala Ediciones`.

Estado: **CANDIDATE_FOR_VERIFICATION**. Antes de registrarla debe abrirse la URL final y fijar título, fecha, autor/byline, canonical y `verifiedAt`.

### B. Artículos firmados por David en medios externos

Ejemplos encontrados:

- `Por qué la fantasía juvenil española necesita mundos propios` — Bookdala — firmado por David Porto Díaz.
- `Fantasía juvenil: El portal no es una escapatoria, es una grieta` — Árbol Invertido — firmado por David Porto Díaz.

Son publicaciones externas legítimas y pueden tener valor bibliográfico/de trayectoria, pero **no son cobertura independiente sobre David**. No deben inflar el archivo de prensa ni presentarse como earned media.

### C. Reseñas de usuarios/plataformas

Goodreads contiene reseñas de lectores de `Samuel entre mundos`. Son reseñas reales de usuarios, no una cabecera periodística. Pueden conservarse como fuente externa cuando proceda, pero no deben convertirse automáticamente en registros de prensa ni copiarse a AggregateRating/Review propio.

### D. Fichas comerciales/catálogos

Librerías y retailers pueden confirmar disponibilidad o metadatos bibliográficos, pero una ficha comercial no es una reseña ni cobertura editorial.

## 4. Gate de volumen

Con la evidencia verificada en esta pasada **no se alcanzan 5–8 apariciones independientes de calidad**.

Por tanto:

```text
modelo UX/datos = READY
owner = READY
fuentes candidatas = EXISTEN
volumen editorial verificado = INSUFICIENTE
publicación del archivo = BLOCKED_BY_VOLUME_GATE
```

No se rebaja el umbral contando:

- bylines del propio David;
- posts sociales que replican una pieza;
- fichas de retailer;
- perfiles de catálogo;
- reseñas individuales de Goodreads como prensa;
- autopublicaciones del sitio propio.

## 5. Contrato futuro de datos

Una entrada apta debe tener como mínimo:

```json
{
  "id": "medio-fecha-slug",
  "type": "INTERVIEW|REVIEW|PRESS_MENTION|PODCAST|RADIO_TV|EVENT_COVERAGE|CATALOG_PROFILE",
  "medium": "Nombre del medio",
  "title": "Título real",
  "publishedAt": "YYYY-MM-DD",
  "url": "https://fuente-real.example/...",
  "about": ["David Porto Díaz"],
  "verifiedAt": "YYYY-MM-DD",
  "status": "VERIFIED"
}
```

`CATALOG_PROFILE` puede existir como categoría documental si aporta valor, pero no debe presentarse visualmente como reseña/editorial coverage.

## 6. R.20 y R.50 se mantienen

Google Alerts, búsquedas y monitorización externa sirven para **descubrir candidatos**, no para validarlos automáticamente.

Link reclamation solo procede para corregir un destino roto, HTTP/host antiguo o dato factual incorrecto. Nunca se solicita anchor optimizado ni contraprestación.

## 7. Trigger de implementación

Reabrir runtime cuando existan simultáneamente:

```text
>= 5 entradas externas reales y verificadas
AND clasificación independiente/autorial/comercial resuelta
AND URLs finales comprobadas
AND publishedAt + verifiedAt
AND owner de mantenimiento
```

Entonces:

1. crear una única autoridad de datos;
2. renderizar dentro de `prensa.html`;
3. mantener HTML semántico y escaneable;
4. no añadir filtros hasta que el volumen real los necesite;
5. añadir QA de duplicados, URL y fecha.

## 8. Decisión final

C.10 no se rechaza: el patrón está bien definido y encaja con el master de Drive. Pero implementarlo hoy obligaría a construir el contenedor antes que la evidencia.

**Estado final: `CONDITIONAL · ARCHIVE_MODEL_READY · VERIFIED_COVERAGE_VOLUME_GATE_NOT_MET · NO_CODE`.**
