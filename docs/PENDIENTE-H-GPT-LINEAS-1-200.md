# Pendiente H — Auditoría de `pendiente funcionalidad gpt.txt`, líneas 1–200

Fecha de auditoría: 2026-08-23  
Rama base auditada: `implementacion-web-2026`  
HEAD auditado: `4694799edc6d9c9e729b896cadda1eef9726d083`

> Esta PR nace de contrastar **las primeras 200 líneas** de `pendiente funcionalidad gpt.txt` contra el repositorio real, no de asumir que el TXT sigue vigente. Su objetivo es recoger únicamente deuda funcional/técnica que continúa siendo real y que **no está ya cubierta por otra PR abierta**. No autoriza `main`, producción ni despliegue.

## 1. Resultado de la auditoría

### 1.1 Correcto o sustancialmente cerrado — no reabrir

En el alcance de las líneas 1–200 se comprobó que ya existe o quedó absorbido por trabajo posterior:

- normalización editorial y machine-readable de Samuel;
- reconstrucción de los contenidos de portal fantasy y magia con coste;
- cuarentena técnica del contenido 2025–2026 (`noindex` y fuera de superficies de descubrimiento); la decisión editorial definitiva sigue siendo contenido, no un bug de runtime;
- separación de Manecillas y Samuel en arquitectura y navegación;
- `/empieza-aqui/` y shell/navegación V1;
- PWA/manifest y baterías actuales de CI/QA;
- RSS, sitemap, redirects, JSON-LD, discoverability y módulos relacionados ya presentes en la rama;
- la antigua observación de `eventos.html` con `data-newsletter-source="eventos"` está **obsoleta**: el HTML actual ya no contiene ese source, por lo que no hay que ampliar `SOURCE_MAP` por ese motivo.

### 1.2 Ya está cubierto por PR abiertas — NO duplicar

- **Rate limiting / honeypot / retorno DOI de Brevo:** PR #55.
- **Triggers del popup de newsletter (60 % / timer / exit-intent frente a la spec):** PR #56.
- **Smoke test real post-deploy y `build-public-dist --check-contents` en CI:** PR #58.
- **Inventario de assets sin referenciar:** PR #60. Esta PR no debe convertir ese informe en borrado automático.

### 1.3 Gates externos/editoriales — no convertir en bug de código

- `purchaseUrl` y selector real de tiendas de Manecillas: dependen de URLs comerciales verificadas. No crear ofertas ni tiendas ficticias.
- validación visual final, dirección fotográfica y materiales de marca: gate humano/diseño.
- permisos/activos editoriales de prensa: gate externo.
- artículo 2025–2026 en cuarentena: falta decisión/revisión editorial antes de reindexarlo, no infraestructura de indexación.
- cluster editorial de Manecillas todavía no publicado: trabajo de contenido; la arquitectura puede existir sin inventar artículos.
- confirmación end-to-end de DOI en Brevo: la parte de código está siendo tratada en #55; la automatización/configuración real sigue siendo externa.

---

# 2. DEUDA NUEVA REAL

## H.1 — `script.js` sigue siendo un runtime global monolítico y el popup mantiene CSS dentro de JavaScript

### Evidencia actual

`script.js` continúa concentrando responsabilidades que no pertenecen a todas las páginas:

- cliente de newsletter;
- registro de service worker;
- navegación móvil legacy;
- botón «volver arriba»;
- progreso de lectura;
- quiz completo de Noveris;
- popup de newsletter;
- modal de compra de Samuel;
- instrumentación GoatCounter y handlers de enlaces.

El popup sigue creando un `<style>` en runtime con un bloque CSS grande. Además, sus estados de éxito/duplicado continúan inyectando estilos inline con `font-family:Cormorant Garamond,Georgia,serif`, de modo que la afirmación del TXT de que esa parte seguía legacy **no está completamente cerrada** pese a limpiezas posteriores.

El modal de compra de Samuel también sigue dentro del runtime global. Esto deja código específico de Samuel/Noveris/newsletter en un fichero cargado por superficies que no necesitan esas funciones.

### Implementación requerida

1. Separar responsabilidades de `script.js` por alcance real de página, sin migrar de stack ni introducir framework/bundler.
2. Extraer el popup de newsletter a módulo/asset propio y mover su CSS a una hoja dedicada o al sistema visual autoritativo; no inyectar un stylesheet grande mediante `style.textContent`.
3. Eliminar la tipografía legacy del HTML de estados del popup y usar los tokens/fuentes vigentes del sistema V1.
4. Extraer el modal de compra de Samuel para que solo cargue donde exista un trigger válido de Samuel.
5. Extraer o cargar bajo demanda el quiz de Noveris únicamente en su superficie real.
6. Mantener `script.js` como núcleo pequeño para funciones verdaderamente sitewide; no fijar un umbral de bytes arbitrario si no se demuestra primero el coste, pero sí registrar before/after.
7. Preservar el contrato que resulte de #56; si #56 entra antes, rebasar esta rama y no reintroducir timer/scroll/exit-intent antiguos.

### Criterios de aceptación

- [ ] páginas sin popup no descargan/ejecutan el módulo del popup;
- [ ] páginas sin compra de Samuel no descargan/ejecutan el modal de Samuel;
- [ ] páginas fuera de Noveris no descargan/ejecutan el quiz de Noveris;
- [ ] el popup no crea su hoja principal mediante `style.textContent`;
- [ ] no queda `Cormorant Garamond`/`Inter` hardcodeado como tipografía legacy en el markup runtime del popup;
- [ ] newsletter, popup, modal de Samuel, fragmento, Noveris y navegación mantienen comportamiento y accesibilidad;
- [ ] `node --check` pasa sobre todos los módulos JS afectados;
- [ ] los tests/browser QA existentes afectados siguen en verde;
- [ ] añadir un test/check de **runtime scoping** que falle si una responsabilidad específica vuelve a cargarse globalmente donde no corresponde.

---

## H.2 — Falta un contrato completo y verificable del funnel de Manecillas en la analítica vigente

### Evidencia actual

Las líneas auditadas pedían un funnel equivalente a:

- inicio de muestra;
- final/lectura de muestra;
- apertura de compra;
- clic de compra.

No se debe introducir GA4 solo para conservar nombres históricos: la instrumentación vigente del repositorio usa GoatCounter/eventos propios.

En el HEAD auditado:

- el modal de compra emite un evento genérico de apertura y es específico de Samuel;
- existen clics genéricos de compra/fragmento;
- el tracking de profundidad que busca rutas con `/fragmento/` no cubre por sí mismo la ruta actual `/las-manecillas-del-recuerdo/fragmentos/`;
- la página de fragmentos de Manecillas no contiene un contrato explícito y probado que permita reconstruir el funnel completo por libro.

Por tanto, el requisito funcional sigue sin estar cerrado aunque existan eventos genéricos.

### Implementación requerida

1. Definir eventos semánticos en la analítica **actual**, con una dimensión estable `book=manecillas` (o equivalente documentado).
2. Instrumentar entrada/inicio de la muestra de Manecillas y un final/umbral de lectura que permita medir consumo sin doble conteo.
3. Preparar `buy_open`/`buy_click` para Manecillas **solo cuando exista una CTA/tienda real verificable**. Mientras no exista minorista, el evento correcto debe seguir siendo espera/newsletter, no «compra» ficticia.
4. Evitar que el funnel de Samuel y el de Manecillas se mezclen bajo eventos sin identidad de libro.
5. Añadir QA determinista/browser que compruebe nombres/dimensiones y ausencia de dobles disparos.

### Criterios de aceptación

- [ ] una visita a `/las-manecillas-del-recuerdo/fragmentos/` puede producir eventos de muestra identificados como Manecillas;
- [ ] el consumo significativo/final de muestra se registra una sola vez por condición prevista;
- [ ] un evento de compra nunca se genera si el CTA continúa siendo lista de espera;
- [ ] cuando haya tienda real, apertura y salida a tienda incluyen identidad de Manecillas y destino;
- [ ] los eventos de Samuel siguen diferenciados;
- [ ] test automatizado demuestra el contrato.

---

## H.3 — Falta un gate global y reproducible de imágenes responsive

### Evidencia actual

Hay optimizaciones y variantes responsive en piezas concretas, y Lighthouse/reflow están en CI. Sin embargo, en el HEAD auditado no existe un checker específico que recorra las superficies públicas y haga cumplir de forma reproducible la política pedida en las líneas 84–137 para imágenes editoriales: dimensiones intrínsecas y, cuando corresponde por tamaño/uso, `srcset`/`sizes`.

La PR #60 resuelve otra pregunta —assets no referenciados— y **no sustituye** este control.

### Implementación requerida

Crear un auditor reproducible de imágenes de HTML público que clasifique, sin aplicar arreglos mecánicos:

- imágenes de contenido sin `width`/`height` cuando deberían reservar espacio;
- imágenes editoriales grandes servidas como un único fichero cuando existe/conviene una familia responsive;
- `srcset` sin `sizes` útil o candidatos rotos;
- referencias a variantes inexistentes;
- uso de eager/lazy/fetchpriority incoherente con la función de la imagen cuando el contrato pueda determinarlo con seguridad.

Debe distinguir iconos, SVG, elementos decorativos, imágenes pequeñas y casos deliberados para evitar falsos positivos.

### Criterios de aceptación

- [ ] checker con fixtures positivos y negativos;
- [ ] inventario/base real del sitio producido antes de endurecer CI;
- [ ] corregir los incumplimientos objetivos o documentar excepciones estrechas con motivo;
- [ ] después de sanear la baseline, el checker corre en CI sobre cambios relevantes;
- [ ] demostrar una vez que una regresión de fixture lo pone en rojo;
- [ ] Lighthouse, Pa11y y reflow siguen en verde tras las correcciones.

---

# 3. Orden recomendado dentro de esta PR

1. **H.1 runtime scoping**, porque reduce código global y evita seguir ampliando `script.js`.
2. **H.2 analítica Manecillas**, ya sobre el runtime resultante.
3. **H.3 imágenes responsive**, independiente pero agrupado aquí porque procede de la misma auditoría 1–200 y no tenía PR propia.

Si el volumen de H.3 hace que el diff deje de ser revisable, separar su implementación a una PR hija está permitido, pero este documento debe quedar como trazabilidad y enlazarla.

# 4. QA / no-regresiones obligatorias

Antes de declarar implementado:

- rebasar sobre el HEAD fresco de `implementacion-web-2026` después de integrar las PR que toquen áreas comunes;
- no debilitar tests existentes para poner CI verde;
- revisar diff completo;
- ejecutar suites de newsletter/runtime/herramientas afectadas;
- ejecutar browser QA relevante en móvil y escritorio;
- ejecutar Lighthouse, Pa11y y reflow cuando cambie carga/markup/CSS;
- comprobar que la PR no reintroduce ningún punto ya resuelto en #54–#60.

**No mergear esta PR automáticamente. No tocar `main`. No desplegar producción.**
