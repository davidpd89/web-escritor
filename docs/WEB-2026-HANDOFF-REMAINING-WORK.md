# WEB 2026 — HANDOFF / REMAINING WORK

> Documento operativo para continuar el proyecto desde otro equipo o con otro agente sin perder el estado actual, sin rehacer trabajo ya integrado y sin mezclar tareas.
>
> **Este documento NO autoriza merge a `main`, producción ni despliegue.** Cada bloque se trabaja en una rama propia, abre una PR contra `implementacion-web-2026` y se detiene sin integrar.

---

## 0. LEER ESTO PRIMERO

Repositorio:

`davidpd89/web-escritor`

Rama de integración del proyecto:

`implementacion-web-2026`

Estado observado al crear este handoff:

`c820b21f7d33d0014ba46cb61725ea8bf9933cee`

Mensaje del commit:

`fix(editoriales): stop the builder silently reverting the V1 directory`

**Ese SHA es solo procedencia del handoff. NO se reutiliza como base fija.** Antes de cada tarea hay que hacer `git fetch origin` y tomar el HEAD real de `origin/implementacion-web-2026`.

El proyecto está ya en fase avanzada. No hay que reiniciar investigación, rediseñar la arquitectura completa ni volver a plantear una dirección general.

La dirección cerrada es:

**CARTOGRAFÍA EDITORIAL VIVA — V1-B**

Principios visuales cerrados:

- shell claro + territorio central oscuro;
- diseño editorial contemporáneo, personal y legible;
- jerarquía por tipografía, espacio, composición, líneas y ritmo;
- evitar SaaS, bento, dashboard, cards genéricas y landing de IA;
- evitar estética de agencia beige genérica;
- evitar clichés de escritor: pergamino, pluma, máquina de escribir, papel envejecido;
- evitar WebGL ornamental;
- no migrar de framework ni rehacer stack;
- movimiento corto y funcional, normalmente 160–240 ms;
- base útil sin animación;
- `prefers-reduced-motion` obligatorio cuando haya movimiento.

Topología semántica de Home que debe preservarse:

- obra: **Manecillas → Autor → Samuel**;
- proceso: **Autor → Cuaderno → Herramientas**;
- esfera pública: **Autor → Prensa/Eventos**;
- Autor = origen humano y bisagra;
- Manecillas = territorio dominante actual;
- Samuel = segunda obra, secundaria;
- Cuaderno = proceso/pensamiento entre autor y obra;
- Herramientas = extensión práctica del Cuaderno;
- Prensa/Eventos = territorio público/exterior.

---

## 1. ARRANQUE RÁPIDO EN EL OTRO PC

Si el repositorio ya existe:

```bash
git fetch origin --prune
git switch implementacion-web-2026
git pull --ff-only origin implementacion-web-2026
git status
```

Si `git status` NO está limpio, **DETENTE**. No hagas `reset --hard`, no borres archivos y no descartes trabajo automáticamente.

Este handoff vive inicialmente en la rama:

`gpt/handoff-remaining-work-v1`

Mientras esta PR no esté integrada, puede leerse desde cualquier rama con:

```bash
git fetch origin --prune
git show origin/gpt/handoff-remaining-work-v1:docs/WEB-2026-HANDOFF-REMAINING-WORK.md
```

No crees tareas reales partiendo de la rama del handoff. Las tareas siempre nacen del HEAD actualizado de:

`origin/implementacion-web-2026`

Si el repositorio todavía no existe en el nuevo PC:

```bash
git clone https://github.com/davidpd89/web-escritor.git
cd web-escritor
git fetch origin --prune
git switch implementacion-web-2026
git pull --ff-only origin implementacion-web-2026
```

---

## 2. PROTOCOLO DE EJECUCIÓN — OBLIGATORIO

### 2.1 Una tarea = una rama = una PR

Para cada bloque de este documento:

1. `git fetch origin --prune`;
2. actualizar `implementacion-web-2026` con `--ff-only`;
3. registrar SHA base real;
4. crear la rama indicada;
5. ejecutar SOLO ese bloque;
6. probarlo;
7. revisar el diff;
8. push;
9. abrir PR contra `implementacion-web-2026`;
10. **DETENERSE**.

No empezar automáticamente la siguiente tarea.

### 2.2 Prohibiciones

El trabajador NO debe:

- mergear su PR;
- tocar `main`;
- desplegar producción;
- abrir PR a `main`;
- apilar una tarea encima de otra rama todavía no integrada;
- convertir una tarea concreta en una refactorización global;
- reabrir decisiones visuales cerradas;
- rebajar tests, Lighthouse, CSP, accesibilidad o seguridad para obtener verde;
- ocultar bugs descubiertos;
- declarar PASS de una prueba que no ejecutó.

### 2.3 Si la PR anterior todavía no está integrada

No construir la siguiente rama encima de esa PR salvo instrucción explícita.

Esperar a que el revisor integre la anterior, después:

```bash
git switch implementacion-web-2026
git fetch origin --prune
git pull --ff-only origin implementacion-web-2026
git switch -c <rama-siguiente>
```

### 2.4 Ownership antes de editar

Antes de tocar una página generada hay que localizar:

- fuente de datos;
- template/builder;
- archivo generado;
- test asociado;
- workflow asociado.

No editar fuente y artefacto generado de forma independiente si existe un pipeline autoritativo.

### 2.5 Bug encontrado = bug corregido

Si aparece un bug dentro del scope:

1. reproducir;
2. encontrar causa;
3. corregir;
4. añadir/reforzar test cuando sea razonable;
5. repetir QA.

Si queda un bug real del scope sin resolver:

- PR DRAFT;
- declararlo;
- NO decir «listo para merge».

### 2.6 Estado de QA

Usar exactamente esta semántica:

- `PASS`: ejecutado y correcto;
- `FAIL`: ejecutado e incorrecto;
- `NO HECHO`: no se ejecutó;
- `INCOMPLETO`: comenzó pero no pudo terminar.

### 2.7 Viewports limpios

Para QA responsive usar contexto/página nueva o reload completo por viewport:

- 320×900;
- 390×900;
- 768×1000;
- 1024×900;
- 1440×1000;
- 1728×1000;
- 844×390.

No confiar únicamente en resize continuo de una página ya inicializada.

### 2.8 QA transversal mínimo

Según aplique al bloque:

- teclado;
- focus visible;
- zoom 200 %;
- WCAG text-spacing;
- reduced motion;
- no-JS;
- cero overflow horizontal;
- activos locales;
- enlaces internos;
- canonical;
- robots;
- JSON-LD;
- datos/facts;
- Lighthouse sin rebajar thresholds;
- CI existente;
- screenshots de estados realmente útiles.

---

## 3. TRABAJO YA INTEGRADO — NO REHACER

Antes de proponer algo nuevo, inspeccionar el HEAD real. Estos sistemas ya han pasado por implementación/revisión durante esta fase y no deben reabrirse como tareas independientes salvo regresión demostrada:

- Home/cartografía estructural;
- familia de herramientas de texto;
- herramientas de estructura: Personajes/Nombres/POV;
- herramientas utilitarias: ICS/Metadatos/JSON-LD/Kit de prensa;
- trust layer de herramientas;
- Hub de herramientas;
- Asistente local/remoto con endurecimiento, fuentes y citas;
- Privacidad/Aviso legal/telemetría/consentimiento V1;
- Recomendaciones V1;
- Samuel V1;
- ecosistema profesional para autor V1;
- Cuaderno editorial V1;
- canonical/machine-readable authority V1;
- search/discoverability V1;
- staging/readiness previo que ya exista en la rama.

**Importante:** no ejecutar de nuevo como “tareas pendientes” los prompts de Asistente y Privacidad que puedan existir en chats anteriores. La rama actual ya contiene el trabajo equivalente. Solo se vuelve a ellos si una tarea posterior encuentra una regresión reproducible.

---

## 4. HECHO NUEVO CRÍTICO DESCUBIERTO — EDITORIALES

El HEAD actual contiene una protección temporal en `scripts/build-editoriales.py` porque el builder legacy puede sobrescribir páginas V1.

El problema observado es concreto:

- las páginas de `/editoriales/` fueron migradas a V1;
- el builder/template siguió emitiendo markup legacy;
- ejecutar el builder real podía revertir esas páginas silenciosamente;
- se añadió una barrera para impedir que output legacy sobrescriba un archivo V1;
- la barrera evita pérdida de datos, pero **NO resuelve la divergencia de fuente/template**.

Este es el primer trabajo pendiente y debe resolverse antes de cualquier limpieza amplia de legacy.

---

# TAREA 1 — EDITORIALES BUILDER / TEMPLATE PARITY V1

Rama:

`gpt/editoriales-builder-parity-v1`

PR:

`Editoriales: reconcile V1 builder templates and generated pages`

## Objetivo

Eliminar la divergencia entre el pipeline de generación de `/editoriales/` y las páginas V1 actuales, de modo que ejecutar el builder vuelva a ser seguro, determinista e idempotente.

NO rediseñar Editoriales.

NO reescribir copy.

NO resolver el problema manteniendo indefinidamente un `skip` que impida generar.

## Empezar por

Inspeccionar:

- `scripts/build-editoriales.py`;
- todos los `data/editoriales/*.json` que consume;
- `/editoriales/index.html`;
- páginas hijas generadas;
- `assets/v1-editoriales.css`;
- tests del builder;
- workflows que ejecutan builder/checks;
- historial git de la migración V1 si hace falta entender ownership.

El builder actual contiene una protección para no sobrescribir V1 con output legacy. Esa protección es un **guard temporal**, no la solución final.

## Implementación requerida

1. Mapear exactamente qué páginas escribe el builder.
2. Identificar cuáles son generadas y cuáles tienen contenido/manual ownership.
3. Extraer o actualizar templates para que emitan el shell V1 actual.
4. Preservar exactamente:
   - contenido factual;
   - SEO;
   - canonical;
   - robots;
   - JSON-LD;
   - IDs/anclas públicas;
   - comportamiento de herramientas;
   - datasets;
   - navegación actual.
5. No copiar markup V1 a ciegas si existe ya un partial/helper autoritativo.
6. Ejecutar el builder en worktree limpio.
7. Tras generación, el diff debe ser:
   - cero, si la página actual ya representa la salida deseada; o
   - únicamente cambios intencionales explicados.
8. Ejecutar el builder dos veces y demostrar idempotencia.
9. Solo cuando el builder genere V1 correctamente, retirar/simplificar el guard temporal que impide el overwrite legacy.
10. Añadir una prueba determinista que impida que un futuro cambio del builder vuelva a emitir shell legacy sobre una página V1.

## Casos a proteger

- `<html class="v1">` o contrato equivalente actual;
- CSS V1 correcto;
- shell/navegación V1;
- no retorno a `styles.css`/markup legacy;
- metadatos idénticos;
- datasets completos;
- ningún child page perdido;
- ningún archivo manual sobrescrito.

## QA

Ejecutar:

- builder `--check` si existe;
- builder real;
- builder real por segunda vez;
- tests existentes del pipeline;
- links/activos locales;
- páginas Editoriales a 390 y 1440;
- teclado/no-JS si hay interacción;
- Lighthouse en índice + una hija representativa;
- CI completa que aplique.

## Stop condition

No abrir PR como lista si:

- el builder sigue necesitando bloquear generación por diseño legacy;
- un build cambia contenido sin explicación;
- no es idempotente;
- quedan páginas generadas sin ownership claro.

---

# TAREA 2 — GLOBAL SHELL / NAVEGACIÓN / FOOTER CLOSURE V1

Rama:

`gpt/global-shell-closure-v1`

PR:

`Global shell: close remaining V1 navigation surfaces`

## Objetivo

Cerrar las superficies públicas que todavía puedan usar shell, navegación, footer, CSS o JS legacy después de todas las migraciones ya integradas.

Esta es una tarea de **inventario + corrección de residuales**, no un rediseño global.

## Primero: inventario autoritativo

Obtener lista de rutas públicas desde:

- sitemap/indexes;
- builders;
- archivos HTML públicos;
- registry/hubs existentes.

Clasificar cada ruta:

- V1 completa;
- V1 con resto legacy;
- legacy intencional;
- redirect/archivo técnico;
- no pública.

Buscar al menos:

- `styles.css`;
- `styles.min.css`;
- `script.js`;
- `site-shell` legacy;
- `nav-toggle` legacy;
- logo/header antiguo;
- footer antiguo;
- navegación duplicada;
- rutas públicas sin Explore/shell previsto;
- links antiguos de Home/Libros/Cuaderno/Autor/Eventos/Prensa.

## Implementación

1. Migrar únicamente residuales públicos reales.
2. Mantener contenido y metadatos.
3. Preferir source/template/builder central antes que edición masiva de outputs.
4. No tocar páginas ya V1 solo para formatearlas.
5. No eliminar `styles.css`, `script.js` ni assets legacy mientras exista un consumidor real.
6. Si al final quedan sin consumidores y borrar es seguro, demostrarlo mediante búsqueda + test antes de eliminarlos.
7. Preservar:
   - skip links;
   - `aria-current`;
   - navegación principal;
   - Explore;
   - footer;
   - canonical/robots;
   - schema;
   - analytics/consent contract ya integrado.
8. No cambiar topología semántica de Home.
9. No reabrir diseño de header/footer si ya existe contrato V1.

## QA

- route inventory before/after;
- navegación teclado;
- Explore abrir/cerrar/focus trap si aplica;
- 320/390/768/1024/1440/1728/844×390;
- no-JS para contenido y navegación básica;
- internal graph/navigation coverage;
- links/activos;
- Lighthouse representativo;
- smoke sobre Home, Manecillas, Samuel, Cuaderno, Herramientas, Recomendaciones, Editoriales, Autor, Prensa, Eventos, Privacidad.

## Stop condition

Si el inventario descubre una familia coherente de más de varias páginas con lógica propia que haría esta PR demasiado grande, **NO la absorbas silenciosamente**. Documenta el bloque y propón split antes de continuar.

---

# TAREA 3 — NEWSLETTER / CONTACTO / BREVO — CIERRE DE CONVERSIÓN V1

Rama:

`gpt/newsletter-contact-v1`

PR:

`Conversion: harden newsletter and contact flows V1`

## Objetivo

Cerrar funcionalmente los puntos de conversión y contacto existentes sin convertir la web en ecommerce ni en una máquina agresiva de captación.

No rehacer la política de privacidad ya integrada.

No enviar emails reales durante QA.

## Inventario obligatorio

Localizar:

- todos los formularios de newsletter;
- CTA de suscripción;
- formularios/contact methods;
- integración Brevo;
- Worker/Functions/Cloudflare relacionados;
- campos `SOURCE` o provenance equivalente;
- consentimiento;
- estados de éxito/error;
- rate limits;
- configs/env;
- tests existentes.

Construir una tabla:

`SURFACE → FORM → ENDPOINT → DATA → SOURCE → CONSENT → SUCCESS → ERROR`

## Contratos a validar

1. Email válido.
2. Email inválido.
3. Campo vacío.
4. Consentimiento sin marcar.
5. Doble submit.
6. Timeout.
7. 429.
8. 500.
9. Offline.
10. Suscriptor duplicado si el backend tiene estado específico.
11. Keyboard/focus.
12. Mobile.
13. No-JS: no fingir funcionamiento.
14. Ningún secret en cliente.
15. Ningún email en URL/query string.
16. Ningún email completo enviado a analytics.
17. `SOURCE` correcto para cada superficie si ese es el contrato real.
18. No almacenar email en local/session storage salvo necesidad autoritativa explícita.

## Sentinel de privacidad

Usar un fixture claramente falso, por ejemplo:

`qa-newsletter-582931@example.test`

Debe aparecer únicamente en el request autorizado de suscripción/mock.

No en:

- GoatCounter;
- Metricool;
- URL;
- console;
- localStorage;
- sessionStorage;
- logs cliente.

## CI

No llamar Brevo real.

Stub/mock determinista para:

- success;
- duplicate si aplica;
- 400;
- 429;
- 500;
- timeout.

No guardar API keys reales.

## Diseño/UX

Los formularios deben pertenecer al sistema editorial V1:

- claros;
- discretos;
- sin modales agresivos;
- sin dark patterns;
- sin popups automáticos salvo contrato existente explícito;
- CTA proporcionado a la importancia real de newsletter/contacto.

## No tocar

Texto legal salvo contradicción técnica demostrada. Si aparece una contradicción con Privacidad/Aviso:

- documentarla exactamente;
- corregir implementación cuando esa sea la intención autoritativa;
- si requiere juicio jurídico: `LEGAL_REVIEW_REQUIRED`;
- no improvisar redacción legal.

---

# TAREA 4 — EDITORIAL VISUAL FINISH — MARCOS / FONDOS / LÍNEAS / RUTAS / MEDIA TREATMENT

Rama:

`gpt/editorial-visual-finish-v1`

PR:

`Visual system: finish editorial frames routes and media treatment V1`

## Objetivo

Aplicar la capa visual que todavía debe convertir el conjunto ya funcional en una web editorial con identidad propia.

**Esta tarea NO consiste en generar más fotos del autor, manuscritos falsos ni imágenes documentales sintéticas.**

Lo que falta aquí es DISEÑO:

- fondos;
- marcos;
- bordes;
- líneas;
- conectores;
- separadores;
- microdetalles;
- tratamiento de las imágenes reales ya existentes.

## Dirección cerrada

### Marcos editoriales

Crear 2–3 primitivas reutilizables, como máximo:

- esquina incompleta;
- filete/hairline lateral o inferior;
- bracket/offset frame.

Deben sentirse editoriales, no “card component”.

Acento cobre + neutrales del sistema actual.

### Home / cartografía

Mejorar la gramática de rutas manteniendo la topología actual:

- segmentos/curvas;
- anclas/nodos;
- halos discretos;
- jerarquía por grosor/opacidad;
- énfasis suave en hover/focus;
- si se añade proximidad de puntero, debe ser progressive enhancement y no requisito de comprensión.

No convertir la Home en diagrama técnico ni mapa de metro.

### Fondos

Usar CSS/SVG:

- variaciones de plano;
- gradientes radiales/lineales extremadamente sutiles;
- reglas;
- contornos;
- grid editorial casi imperceptible si aporta.

No raster “paper texture”.

### Microornamentos

Uso restringido de:

- índices;
- coordenadas/marcas editoriales;
- puntos/anclas;
- filetes;
- numeración de sección;
- caption rails.

No decoración por decoración.

### Tratamiento de media real

Sobre imágenes existentes:

- crops consistentes;
- frame offset;
- máscara cuando tenga sentido;
- caption rail;
- corner index;
- borde/contrapunto tipográfico.

Evitar thumbnails genéricos redondeados.

## Media authority

Documento master existente:

`30 — MEDIA + VIDEO PRODUCTION SYSTEM V1 — SHOT LIST · CROPS · POSTERS · CAPTIONS · JSON MANIFEST`

Drive ID de referencia del proyecto:

`1VEsYDN21wNgfrHZ6A_fzYpzKqR41IenkmPWNejxEIoQ`

Autoridades de media:

- M1: portada oficial;
- M2: retrato real;
- M3: libro físico;
- M4: manuscrito/corrección/página/firma/nota real;
- M5: evento/feria/presentación/prensa;
- M6: vídeo editorial real;
- M7: geometría neutra CSS/SVG.

Documento anti-IA/provenance de referencia del proyecto:

Drive ID:

`1EHFQZ6t3jy3aCWJdKkPS27lFK3e4LBOnKT_b5p-YYoc`

Regla:

- canonical site = material real;
- generado = auxiliar/social/campaña/experimental/prototipo, salvo cambio explícito de autoridad;
- no inventar contenido privado de manuscritos;
- no alterar texto de portadas oficiales.

Retrato seleccionado conocido:

`/assets/david-porto-foto-portada-sinfondo.webp`

No sustituir silenciosamente por otra versión de mayor resolución sin comprobar composición/LCP y sin justificar el cambio.

## Restricciones técnicas

- Preferencia CSS y SVG pequeño.
- No librerías de animación nuevas.
- No WebGL.
- No canvas ornamental.
- No nueva dependencia.
- No nuevo JS salvo que aporte interacción concreta y siga funcionando sin él.
- No cambios de copy/SEO/schema.
- No CLS.
- reduced motion.
- touch usable.

## QA

Capturas antes/después de superficies representativas:

- Home 390 y 1440;
- Manecillas 390 y 1440;
- Autor 390 y 1440;
- una página editorial de Cuaderno;
- Herramientas/Recomendaciones si reciben una primitiva compartida.

Además:

- contraste;
- focus;
- reduced motion;
- 320 → 1728;
- Lighthouse;
- CLS;
- LCP;
- no overflow.

## Regla de tamaño

Si la tarea empieza a requerir modificar demasiadas familias con comportamientos distintos, detenerse y dividir en PR coherentes. No entregar una PR visual monstruosa.

---

# TAREA 5 — FULL-SITE RESIDUAL AUDIT + LEGACY CLEANUP

Rama:

`gpt/site-residual-cleanup-v1`

PR:

`Site audit: remove residual legacy and integration regressions V1`

## Cuándo se ejecuta

Solo después de que Tareas 1–4 hayan sido revisadas e integradas en `implementacion-web-2026`.

## Objetivo

Hacer una auditoría transversal del ESTADO FINAL REAL de la rama de integración y corregir únicamente residuos/regresiones demostradas.

No repetir la auditoría de staging antigua.

No inventar nuevas features.

No rediseñar.

## Inventario completo

Catalogar todas las rutas públicas y verificar:

- shell;
- CSS/JS;
- navegación;
- redirect/index;
- canonical;
- robots;
- JSON-LD;
- facts;
- imágenes;
- links;
- no-JS;
- accessibility;
- responsive;
- ownership generado/manual.

Buscar especialmente:

- markup legacy restante;
- `styles.css`/`script.js` restante;
- archivos antiguos todavía indexados;
- rutas duplicadas;
- redirects rotos;
- orphan pages;
- sitemap/indexes obsoletos;
- assets sin ruta o rutas sin asset;
- referencias a contenido retirado;
- source/generated drift;
- navegación inconsistente;
- schema duplicado/contradictorio;
- fechas/facts discrepantes;
- regressions introducidas por merges sucesivos.

## Herramientas

Confirmar las 17 herramientas autorizadas del Hub actual y que cada una conserva:

- ruta;
- engine;
- local-first/privacy contract;
- no regresión de funcionalidad;
- accesibilidad.

No añadir herramientas nuevas en esta tarea.

## QA global

Ejecutar matrices automáticas existentes y completar gaps reales:

- local assets;
- internal links/graph;
- indexes;
- machine authority;
- editorial facts;
- tools tests;
- browser QA;
- privacy/security tests;
- Lighthouse;
- responsive;
- keyboard;
- zoom 200 %;
- text spacing;
- reduced motion;
- no-JS.

No bajar thresholds.

## Fix policy

Hallazgo reproducible dentro de scope:

`REPRODUCE → FIX → TEST → REGRESSION TEST`

Hallazgo que es una nueva feature:

NO implementar aquí.

Hallazgo que exige refactor grande no previsto:

documentar y separar.

## Limpieza de legacy

Solo borrar un archivo legacy cuando se demuestre:

1. cero referencias runtime/generación;
2. cero consumers públicos;
3. pipeline no lo necesita;
4. tests siguen verdes.

No hacer limpieza estética del repo basada solo en “parece viejo”.

---

# TAREA 6 — RELEASE READINESS / PRE-MAIN PACKAGE

Rama:

`gpt/release-readiness-v1`

PR:

`Release: prepare implementation branch for final production review V1`

## Cuándo

Solo cuando Tareas 1–5 estén revisadas e integradas.

## Objetivo

Preparar la rama `implementacion-web-2026` para una decisión humana final de promoción a `main`/producción.

**Esta tarea NO autoriza el merge a main.**

**Esta tarea NO despliega.**

## Debe producir evidencia, no confianza verbal

Registrar:

- HEAD exacto;
- commits incluidos;
- CI final;
- checks requeridos;
- sitemap/route inventory;
- smoke global;
- Lighthouse;
- browser QA;
- no-JS;
- accessibility;
- responsive;
- machine-readable authority;
- SEO;
- privacy/security;
- forms/conversion;
- tools;
- media/assets;
- build pipelines;
- redirects;
- rollback.

## Facts de lanzamiento a preservar

### Las manecillas del recuerdo

- publicación: 3 de septiembre de 2026;
- editorial: Monza Ediciones;
- ISBN: `979-8-90514-935-1`;
- 272 páginas;
- PVP: 16 €.

No inventar disponibilidad comercial futura si todavía no está confirmada en fuentes autoritativas del repo.

### Samuel entre mundos

- ISBN: `9791387659776`;
- 422 páginas;
- Libros Indie;
- paperback;
- `datePublished`: 2025 según autoridad actual del proyecto.

### Eventos conocidos completados

- Aranjuez: 23/05/2026;
- Feria del Libro de Madrid: 10/06/2026, 19:00–20:00, caseta 337.

No inventar eventos futuros.

### Jaula

Mantener restricciones existentes. No exponer ni reescribir material no publicado/protegido por aprovechar la fase de release.

## Pruebas finales

Matriz mínima:

- `/`;
- Manecillas;
- Samuel;
- Autor;
- Cuaderno;
- Herramientas;
- una muestra representativa de las 17 herramientas + suite completa automatizada;
- Recomendaciones;
- Editoriales;
- Prensa;
- Eventos;
- Asistente;
- Privacidad;
- Aviso legal;
- sitemap/AI/machine surfaces.

Viewports limpios:

320, 390, 768, 1024, 1440, 1728, landscape móvil.

## Rollback

Documentar procedimiento de rollback concreto:

- SHA anterior conocido;
- cómo identificar deploy malo;
- qué checks ejecutar después del rollback.

No ejecutar rollback salvo necesidad real y autorización correspondiente.

## Resultado permitido

A. `READY_FOR_HUMAN_MAIN_REVIEW`

solo si no existen blockers y toda evidencia requerida está ejecutada.

B. `BLOCKED`

si hay cualquier regresión relevante.

Nunca:

- mergear a `main`;
- deployar;
- decir “sin bugs” como garantía absoluta.

---

## 5. REGLA CONDICIONAL DE SPLIT

No forzar una tarea grande a caber en una PR.

Si durante Tarea 2, 4 o 5 aparece una familia coherente que:

- afecta muchas rutas;
- tiene lógica propia;
- necesita QA propio;
- genera demasiado conflicto;

entonces:

1. detener implementación de esa familia;
2. documentar rutas/causa;
3. abrir la PR actual solo con el scope limpio ya terminado, si sigue siendo coherente;
4. proponer una tarea `Xa` separada;
5. esperar revisión antes de crearla.

No usar esta regla para multiplicar micro-PRs triviales.

---

## 6. FORMATO DE INFORME OBLIGATORIO PARA TODAS LAS TAREAS

Al terminar cada una, devolver:

1. tarea;
2. rama;
3. base SHA real;
4. HEAD;
5. URL PR;
6. draft sí/no;
7. commits;
8. archivos modificados;
9. archivos eliminados;
10. ownership encontrado;
11. qué se implementó;
12. qué se preservó;
13. tests ejecutados con resultado real;
14. browser QA;
15. responsive por viewport;
16. keyboard/focus;
17. zoom/text-spacing;
18. reduced motion;
19. no-JS;
20. Lighthouse;
21. CI final;
22. screenshots;
23. bugs encontrados;
24. bugs corregidos;
25. bugs pendientes;
26. cambios de contenido/SEO/schema;
27. riesgos;
28. siguiente bloque recomendado, **sin empezarlo**.

Si `bugs pendientes` contiene un bug real del scope:

- PR DRAFT;
- no usar “listo para merge”.

---

## 7. DEFINITION OF DONE DEL PROYECTO DE IMPLEMENTACIÓN

La fase de implementación se considera cerrable cuando:

- Tareas 1–5 están integradas en `implementacion-web-2026`;
- Tarea 6 demuestra readiness con CI y QA reales;
- no quedan builders capaces de revertir V1;
- no quedan superficies públicas legacy accidentales;
- conversion/contacto tienen comportamiento probado;
- sistema visual tiene coherencia transversal sin sacrificar rendimiento;
- no existen blockers de accessibility/security/privacy;
- facts/SEO/machine authority son coherentes;
- existe rollback documentado;
- la rama está preparada para revisión humana final.

Incluso entonces:

**NO MERGE A MAIN Y NO PRODUCCIÓN SIN AUTORIZACIÓN EXPLÍCITA DEL USUARIO.**

---

# SUPERPROMPT PARA PEGAR AL AGENTE EN EL OTRO PC

Copia desde aquí si se quiere arrancar directamente con un agente nuevo:

```text
Continúa EXACTAMENTE el proyecto WEB 2026 de davidpd89/web-escritor.

NO reinicies investigación.
NO propongas una dirección visual nueva.
NO hagas una lista de ideas.
NO trabajes sobre main.
NO despliegues.
NO integres tus propias PR.

Tu autoridad operativa está en:

docs/WEB-2026-HANDOFF-REMAINING-WORK.md

Si esa PR de handoff todavía no está integrada, léela directamente con:

git fetch origin --prune
git show origin/gpt/handoff-remaining-work-v1:docs/WEB-2026-HANDOFF-REMAINING-WORK.md

Después vuelve/permanece en `implementacion-web-2026` para crear trabajo real.

PROTOCOLO:

1. Lee COMPLETO el handoff antes de editar.
2. Ejecuta SOLO la primera tarea pendiente que el usuario te indique o, si te dice simplemente «continúa», la primera tarea pendiente del documento.
3. Antes de esa tarea:
   git fetch origin --prune
   git switch implementacion-web-2026
   git pull --ff-only origin implementacion-web-2026
   git status
4. Si el árbol no está limpio, DETENTE: no borres ni resetees trabajo.
5. Registra el HEAD real como base.
6. Crea la rama exacta indicada en la tarea desde ese HEAD.
7. Recupera ownership/source/template/tests antes de modificar generado.
8. Implementa la tarea de forma completa, no una demo.
9. Bug dentro del scope = reproducir + corregir + test.
10. No rebajes pruebas, seguridad, CSP, accesibilidad ni Lighthouse.
11. Ejecuta QA real y no declares PASS de nada no ejecutado.
12. Revisa tu diff completo antes de push.
13. Abre UNA PR contra `implementacion-web-2026`.
14. NO MERGE.
15. NO MAIN.
16. NO PRODUCCIÓN.
17. Devuelve el informe exacto exigido por el handoff.
18. DETENTE y espera revisión antes de iniciar la siguiente tarea.

IMPORTANTE:
- No apiles la siguiente tarea sobre tu rama actual.
- Después de que otra persona integre una PR, vuelve a hacer fetch/pull de `implementacion-web-2026` y crea la siguiente rama desde ese nuevo HEAD.
- Asistente y Privacidad/Legal ya fueron trabajados e integrados: no los rehagas como tareas independientes salvo regresión demostrada.
- La primera tarea pendiente prioritaria es reconciliar el builder/template de Editoriales con V1; existe un guard temporal porque el builder legacy podía sobrescribir páginas V1. No confundas ese guard con una solución definitiva.

Empieza ahora SOLO por la tarea que corresponda y detente al abrir su PR.
```

---

## 8. NOTA PARA EL REVISOR / CONTROL TOWER

No aprobar una PR basándose únicamente en el informe del trabajador.

Antes de integrar verificar independientemente:

- HEAD de la rama;
- base real;
- diff;
- archivos inesperados;
- CI;
- bugs declarados;
- regresiones de metadata/content;
- comportamiento relevante en navegador cuando la tarea lo requiera.

Después de integrar una PR, comprobar HEAD nuevo de `implementacion-web-2026` antes de autorizar la siguiente tarea.

Este procedimiento permite paralelizar la implementación sin convertir la rama de integración en una cadena de supuestos no verificados.