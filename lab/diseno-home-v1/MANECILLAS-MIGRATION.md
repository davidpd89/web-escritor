# MANECILLAS — AUDITORÍA Y MIGRACIÓN V1

Estado: preparación de Fase 3. No sustituye todavía la ficha pública. Se ejecuta después de elegir Home V1-A/V1-B, pero deja cerrada la estructura, la preservación y la deuda legacy.

Rama auditada: `implementacion-web-2026`
HEAD de referencia: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`
Fuente visual: doc 20 — BOOK MASTER SPEC V1.

## 1. Diagnóstico

La página actual ya contiene casi todos los hechos y buena parte del contenido útil. El rediseño no necesita inventar una ficha; necesita **recomponerla**.

Problemas de la implementación actual frente a V1:

1. Hero usa `/assets/manecillas-book-mockup.webp`, un mockup 3D, mientras V1 exige portada oficial plana como objeto dominante.
2. La portada se duplica: mockup arriba + cubierta oficial plana dentro de «Ficha editorial».
3. Metadata (género, editorial, publicación, páginas, ISBN, PVP) aparece como seis `feature-card`; V1 exige ledger/margen editorial, no grid de tarjetas.
4. El hero contiene dos acciones hermanas (`Leer tres fragmentos` + `Recibir novedades`); V1 pide una principal y una secundaria solo si la tarea es realmente prioritaria.
5. `manecillas-extras.css` construye una identidad paralela con hex históricos, gradientes, paper surface, theme cards, quote band, shadows y decoración local. Está superado como gramática V1.
6. «Tres puertas de entrada» se presenta como tres cards iguales. El contenido puede sobrevivir, la primitiva visual no.
7. La muestra de lectura vive en una caja `manecillas-frame` sobre un fondo de papel simulado. V1 define fragmento como lectura editorial, no widget.
8. El bloque «También te puede interesar» convierte Samuel + fragmento en CTA comercial/recirculación. V1 requiere relación editorial explícita, no upsell.
9. El bloque final de Samuel ocupa una sección promocional completa con portada 3D y dos CTA. Para V1 debe reducirse a «otra obra» dentro de Related, sin competir con Manecillas.
10. La disponibilidad actual mezcla información de compra todavía pendiente con el formulario de newsletter. V1 separa disponibilidad/compra de suscripción.
11. El fragmento público existe y es valioso, pero el master pide una ruta de lectura clara hero → sinopsis → fragmento → disponibilidad/relacionados.
12. Falta un bloque específico prensa/eventos de la obra si hay elementos reales que mostrar; no se inventa para rellenar.
13. Sharing/print quedan como P1/funcionales; deben prepararse sin fila de iconos sociales.

## 2. Lo que se conserva sin reescritura automática

### Head/SEO

- URL/canonical `/las-manecillas-del-recuerdo/`.
- title actual salvo revisión editorial separada.
- meta description actual salvo revisión editorial separada.
- robots.
- Open Graph/Twitter.
- `og:image` / `twitter:image`.
- JSON-LD `WebPage` + `Book`.
- `@id` canónico `https://davidportodiaz.com/#book-manecillas`.
- author `#author`.
- primary image object de la cubierta oficial.
- BreadcrumbList.
- ISBN, páginas, fecha, formato, editorial, género si siguen siendo hechos aprobados.

### Contenido factual/editorial

- H1 `Las manecillas del recuerdo`.
- David Porto Díaz.
- Monza Ediciones.
- `3 de septiembre de 2026`.
- 272 páginas.
- ISBN `979-8-90514-935-1`.
- PVP 16 € mientras siga vigente.
- sinopsis coral existente.
- sinopsis editorial oficial / texto de cubierta.
- fragmento visible y enlace a `/las-manecillas-del-recuerdo/fragmentos/`.
- dedicatoria/cita solo si su publicación está autorizada; no se usa como relleno obligatorio.
- hooks de newsletter Manecillas hasta migrar el binding con paridad.

## 3. Nueva arquitectura semántica

Orden DOM propuesto:

```text
<header global V1>
<main>
  <article class="book-page book-page--manecillas">
    <nav class="breadcrumb">...</nav>
    <header class="book-hero">...</header>
    <section id="sinopsis">...</section>
    <section id="fragmento">...</section>
    <section id="contexto">...</section>        [solo contenido real]
    <section id="prensa-eventos">...</section> [solo si hay entradas reales]
    <section id="disponibilidad">...</section>
    <aside id="relacionado">...</aside>
  </article>
</main>
<footer global V1>
```

No duplicar la portada en otro bloque salvo que una descarga/prensa lo requiera con una tarea distinta.

## 4. Hero V1

### Desktop 1440

- 12 columnas.
- cubierta oficial plana: cols 1–4/2–5 según prueba, alto visual 560–680 px.
- copy: cols 6–11.
- ledger marginal: col 12 o 10–12 si la densidad lo pide.
- H1 72–96 px Instrument Serif, sin reducir artificialmente para forzar una línea.
- lead Newsreader 22–28 px.
- portada sin card, 3D, giro, glow ni humo.
- `view-transition-name` queda preparado, pero no se activa hasta aprobar Home estática.

### CTA

Primario de estructura: `Leer un fragmento` → `#fragmento` o página de fragmentos según prueba.

`Dónde comprar` puede ser secundaria o ruta textual hacia `#disponibilidad` cuando existan destinos comerciales. No convertir newsletter en segunda CTA de compra.

## 5. Metadata: cards → ledger

Transformación exacta:

| Legacy | V1 |
|---|---|
| `.features-grid` | `.book-meta-ledger` |
| seis `.feature-card` | filas `dt/dd` |
| badge/box por dato | filetes de 1 px + label pequeño |
| desktop grid de tarjetas | margen/columna estrecha |
| mobile cards | lista compacta en flujo |

Datos actuales: género, editorial, publicación, páginas, ISBN, PVP. `PVP` puede vivir en disponibilidad si el hero queda demasiado denso.

## 6. Sinopsis

Mantener dos niveles de contenido sin repetirlos:

A. lead/sinopsis corta en hero: 1–2 frases reales.

B. cuerpo `#sinopsis`: texto coral existente con ancho de lectura 58–72ch.

La sinopsis editorial oficial puede vivir dentro de `#contexto` como «Texto de cubierta» o sustituir a B si editorialmente se decide que es la versión canónica; no mostrar dos sinopsis largas casi equivalentes por acumulación.

No meter la prosa dentro de `prose-card`.

## 7. «Tres puertas»

El contenido Memoria / Valor / Futuro no se descarta automáticamente. Se recompone como índice editorial/ledger de tres entradas o se integra en el cuerpo de contexto. Prohibido conservar `.manecillas-theme-grid/.manecillas-theme-card` por inercia.

Gate: si eliminar este bloque no resta comprensión real, no se publica. No existe obligación de mostrar tres conceptos solo porque ya estén escritos.

## 8. Fragmento

La muestra pasa de `manecillas-frame` + `manecillas-paper` a `.excerpt-field`:

- fondo base Paper;
- heading/intro lateral o previo;
- texto Newsreader;
- ancho de lectura real;
- filete/indentación para marcar registro;
- sin comillas gigantes;
- sin textura falsa;
- sin card elevada;
- enlace visible a los tres fragmentos.

Conservar `data-nosnippet` solo si sigue siendo la estrategia SEO vigente y se valida antes de promoción.

## 9. Disponibilidad y newsletter

Separar dos tareas:

### `#disponibilidad`

- estado editorial/comercial del libro;
- retailers/formatos reales cuando existan;
- PVP/formato si aporta;
- enlaces textuales con destino nombrado.

### newsletter

Puede aparecer después o dentro de Related/continuidad, pero no sustituye la disponibilidad.

Hooks de primera migración a conservar:

- `newsletter-form-manecillas`
- `nl-email-manecillas`
- `nl-gdpr-manecillas`
- `nl-status-manecillas`
- `source = manecillas`

El copy de éxito actual del JS está desfasado respecto al estado permanente («Te avisaré cuando ... esté disponible»). Debe alinearse con doc 31 y la verdad del 03/09 antes de producción; no cambiar el backend para arreglar copy.

## 10. Relacionado

Samuel pasa de una sección promocional completa a una relación editorial secundaria:

- heading preferido: `Relacionado` o `Otra obra` según prueba;
- Samuel puede tener título + una frase + enlace normal;
- sin portada 3D obligatoria;
- sin Amazon CTA dentro del Related de Manecillas;
- fragmento de Samuel no es hermano de CTA de Manecillas.

Otros relacionados posibles solo si existen de verdad: artículo de proceso, evento, prensa o Autor. Máximo 1 pieza primaria + 2–4 enlaces secundarios según doc 20/32.

## 11. CSS legacy que no pasa a V1

No portar las siguientes primitivas de `assets/manecillas-extras.css`:

- `.book-hero--manecillas` con gradientes locales;
- `.manecillas-frame` y esquinas decorativas;
- `.manecillas-paper` y textura/gradiente simulado;
- `.manecillas-divider` ornamental;
- `.manecillas-theme-grid/.manecillas-theme-card`;
- `.manecillas-quote-band` como banda full-width obligatoria;
- `.manecillas-excerpt` como card;
- antiguos `--m-*` hex como tokens de componente;
- sombras múltiples de portada.

La cobertura real puede aportar acento local mediante roles semánticos V1. No se elimina el CSS legacy de la rama hasta que todas sus páginas consumidoras migren.

## 12. Responsive obligatorio

### 1024

Cubierta 4–5 cols + info 7–8; ledger sale del margen.

### 768

Recomponer: título/autor/fecha → cubierta + CTA → lead → ledger. No reducirlo a desktop estrecho.

### 390

Orden: label → H1 → autor → fecha → cubierta → lead → CTA → ledger.

### 320

Una columna; portada 62–76vw; retailers verticales; nada en dos columnas si comprime texto.

### 1728+

No escalar portada/título indefinidamente; usar margen editorial.

## 13. Print/share

Print CSS de ficha: oculta shell interactiva, dialog, CTA y decoraciones; conserva título, autor, cubierta si aporta, sinopsis, metadata y URL.

Sharing P1: `Compartir` con Web Share; fallback `Copiar enlace`; feedback `Enlace copiado.`. No SDKs ni fila de iconos sociales.

## 14. Preservación funcional

No romper al migrar:

- newsletter/Brevo source `manecillas`;
- GoatCounter/Metricool globales;
- canonical/schema/OG;
- enlaces `/fragmentos/`, `/prensa.html`, Samuel;
- service worker global;
- footer/nav hasta que shell V1 los sustituya con paridad.

## 15. Gate de la ficha piloto

No aprobar por una captura bonita. Debe demostrar:

- portada plana domina sin mockup;
- el libro se entiende antes de la acción comercial;
- metadata parece ledger editorial, no Amazon;
- fragmento se lee como texto, no widget;
- compra es encontrable sin dominar;
- mobile conserva escala editorial;
- sin media secundaria sigue funcionando;
- metadata parcial no rompe layout;
- related 0/1/3 no rompe composición;
- zoom 200 %, 320, keyboard, reduced motion, print;
- SEO/schema/canonical y hooks comerciales permanecen;
- visualmente pertenece a la misma web que Home sin repetir su mapa.

## 16. Estado de preparación

Estructura: CERRADA PARA PILOTO.
Contenido factual: SUFICIENTE PARA SCAFFOLD; validar cualquier cita/material de prensa antes de producción.
Compra: GATE DE DESTINOS COMERCIALES.
Newsletter: FUNCIÓN EXISTENTE; microcopy de éxito a corregir antes de producción.
CSS final: depende de tokens/shell globales y de la variante Home ganadora, no de `manecillas-extras.css`.



## POLÍTICA DE DRIFT DE RAMA — 20/08/2026

Último HEAD auditado para este paquete: `5c4a9afca7c009bd78d5dd44ca4b6c656239527c`.

Este SHA es una baseline informativa, no un bloqueo rígido. Antes de cualquier integración se compara este HEAD con el HEAD actual de `implementacion-web-2026`. Solo se reabre una decisión V1 si el delta toca archivos/contratos relevantes para esa decisión. Cambios aislados de CI, herramientas u otras familias no obligan a rehacer Home o Libro. `main` no es destino de integración.


## DELTA — GÉNERO + SOURCE MANECILLAS + COPY PERMANENTE

La ficha V1 debe conservar visible el género ya aprobado en la página real: `Novela coral · Ficción especulativa`. No se añade un género nuevo; se traslada un dato existente al ledger editorial. El JSON-LD conserva además su lista actual `Novela coral`, `Ficción especulativa`, `Narrativa familiar`.

El formulario V1 declara `data-newsletter-source="manecillas"` como contrato de integración. No es un nuevo campo enviado al Worker: en producción `script.js` continúa derivando `source: "manecillas"` mediante `submitNewsletter(..., sourceLabel)`. El lab sigue sin red.

El microcopy de éxito legado «Te avisaré cuando Las manecillas del recuerdo esté disponible.» queda SUPERADO por el estado editorial permanente. Copy objetivo: «Te has suscrito correctamente. Recibirás las novedades de Las manecillas del recuerdo y de David Porto Díaz.» No promete una automatización ni una entrega específica.

Día 03/09: solo URLs comerciales verificadas y activación/ajuste del CTA de compra. No se cambia de nuevo «Publicada el 3 de septiembre de 2026», ni fecha, ISBN, editorial, páginas, PVP, canonical o @id.

## Delta 20/08/2026 — breadcrumb + WebPage/primaryImage + muestra

La auditoría contra `implementacion-web-2026` en HEAD `f9b0646884d4ebc4a29664e4144798b5094286ea` confirma que la ficha pública actual contiene dos capas de breadcrumb que deben sobrevivir juntas:

- visible: `Inicio → Libros → Las manecillas del recuerdo`;
- JSON-LD: `WebPage.breadcrumb` de tipo `BreadcrumbList` con esa misma jerarquía y URLs canónicas.

En V1 la miga usa **Libros**, no «Obra»: «Obra» puede seguir siendo una etiqueta de navegación global, pero no sustituye el nombre convencional del nivel `/libros/` dentro del breadcrumb.

El `WebPage` canónico también conserva `primaryImageOfPage` como `ImageObject` de la cubierta oficial `https://davidportodiaz.com/assets/portada-las-manecillas-del-recuerdo-1024.webp`, 1024×1536. No se sustituye por mockup 3D, retrato, OG genérico ni imagen decorativa.

La muestra pública actual mantiene `data-nosnippet` y enlace a `/las-manecillas-del-recuerdo/fragmentos/`. El scaffold V1 conserva ambos. Cambiar la estrategia `data-nosnippet` exige decisión SEO separada; el rediseño por sí solo no la elimina.

`data/manecillas-preservation.json` y `scripts/check_preservation.py` convierten estas reglas en gate ejecutable para el HTML candidato de producción.


## Delta 20/08 — deep links, dedicatoria y CTA comercial pendiente

La ficha pública actual expone anchors que pueden estar enlazados desde contenido interno/externo. V1 los preserva aunque la composición cambie:

- `#aviso` → ledger de datos editoriales;
- `#muestra` → alias de la muestra/fragmento;
- `#sinopsis-editorial` → alias del texto de cubierta;
- `#newsletter-manecillas` → newsletter contextual.

Los aliases no duplican contenido y reciben `scroll-margin` para que el header sticky no tape el destino.

La dedicatoria pública «A quienes alguna vez olvidaron que el tiempo no vuelve.» se conserva una sola vez como pausa editorial. Se elimina el patrón visual legacy `manecillas-quote-band`; no se añade una segunda cita ornamental para rellenar.

Mientras `commercial_gate.status = pending-verified-retailer-urls`, el CTA secundario del hero es `Recibir novedades` → `#newsletter-manecillas`. No se muestra un CTA de compra que aterrice en una sección sin retailers verificados. La activación comercial futura puede cambiar URLs/CTA, pero no fecha, ISBN, editorial, PVP, canonical, Book @id ni arquitectura aprobada.

## Delta responsive 768 — master 20

Se detectó una desviación objetiva: el scaffold inicial aplicaba la composición `max-width:1199` también a 768 y mantenía H1 mínimo de 72 px. Master 20 exige 48–64 px y una recomposición propia. V1 añade `@media (min-width:768px) and (max-width:899px)` con cabecera superior factual y un bloque portada 5/12 + información 7/12. A 767 e inferiores sigue la composición móvil; a 900+ vuelve la arquitectura 8/12 de tablet/desktop.
