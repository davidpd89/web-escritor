# Auditoría de migración — davidportodiaz.com → `implementacion-web-2026`

Fecha: 2026-08-22 · Base comparada: `origin/main` (lo que hoy sirve GitHub Pages)

> **Qué es esto.** Una comprobación de si la rama de implementación contiene todo lo
> que hay publicado hoy, más lo desarrollado en el dossier de ideas, y qué queda
> abierto antes de pasar a diseño. Todos los números salen de comandos reproducibles;
> ninguno es una impresión.

---

## 1. Paridad con producción

### 1.1 Páginas

| Medida | Resultado |
|---|---|
| Páginas HTML publicadas en `main` | 31 |
| Páginas HTML en la rama | 87 |
| **Páginas de producción ausentes en la rama** | **0** |
| Páginas nuevas en la rama | 36 |

No se ha perdido ninguna página. Las 36 nuevas son el asistente, las 17 herramientas,
el directorio de editoriales, las convocatorias, los fragmentos de Manecillas, los
temas del Cuaderno, la metodología editorial y el 404.

### 1.2 Activos

| Medida | Resultado |
|---|---|
| Activos bajo `/assets/` referenciados desde producción | 34 |
| **Ausentes en la rama** | **0** |

### 1.3 Destinos de enlace

Comparando el conjunto de destinos alcanzables (normalizando relativo↔absoluto y
quitando query/fragmento):

| Medida | Resultado |
|---|---|
| Destinos únicos en producción | 87 |
| Destinos alcanzables en la rama | 164 |
| **Destinos de producción que ya no existen en ninguna página** | **9** |

Los nueve son enlaces externos. Ninguno es una página del sitio:

| Destino perdido | Qué era | Peso |
|---|---|---|
| `metricool.com/privacy-policy/` | política de privacidad del rastreador que usa el sitio | **Legal.** Un tercero que procesa datos debe estar enlazado desde la página de privacidad |
| `app.thestorygraph.com/profile/david_porto` | perfil del autor | Identidad (`sameAs`) |
| `es.babelio.com/monprofil.php?id_user=114337` | perfil del autor | Identidad (`sameAs`) |
| `amazon.es/stores/author/B0GZFP1JV3` | página de autor en Amazon | Identidad + venta |
| `amazon.es/dp/B002ZPIQDI` · `amazon.es/dp/B00SHYJGUC` | dos libros recomendados en `/recomendaciones/magia-con-coste/` | Contenido editorial + afiliación |
| `ferialibromadrid.com/` | web oficial de la feria | Evidencia de la ficha |
| `hoymadrid.app/…/presentacion-de-samuel-entre-dos-mundos…` | mención externa del evento | Evidencia |
| `llmstxt.org/` | especificación de `llms.txt` | Referencia menor |

**Los cuatro primeros conviene recuperarlos.** El de Metricool es el más urgente: es
el enlace a la política de un procesador de datos y su ausencia deja la página de
privacidad incompleta. Los tres de identidad alimentan el `sameAs` del autor, que es
justo lo que sostiene el trabajo de autoridad para IA y buscadores.

---

## 2. El dossier «WEB DAVID PORTO nuevas ideas»

130 documentos `.md`. Comprobado ruta por ruta contra la rama:

**19 de 19 herramientas e ideas con implementación prevista están publicadas.**

Legibilidad · Repeticiones · Diálogo · Analizador de capítulos · Nombres de
personajes · Auditor web · Auditor de página de libro · Kit de prensa · Eventos ICS ·
Mapa de personajes · JSON-LD · Metadatos de libro · Radar de convocatorias ·
Entrevista familiar · Distribución de POV · Variedad léxica · Tiempo de lectura en voz
alta · Directorio de editoriales · Club de lectura.

Aviso: `00_IMPLEMENTACION_TRACKER.md` está **desfasado**. Marca como `PENDIENTE` cosas
que llevan tiempo publicadas (el radar de convocatorias, por ejemplo). Es un fichero
local excluido de git, así que no rompe nada, pero no sirve como fuente de verdad: la
verdad es la rama.

---

## 3. Incoherencias que ve un visitante

Estas dos las ve cualquiera que navegue dos páginas seguidas.

### 3.1 El sitio dice dos números distintos de herramientas

| Dónde | Qué dice |
|---|---|
| `/herramientas/` | «17 herramientas» |
| `autor.html`, «Esta web, en cifras» | «15 herramientas gratuitas» |

No es un error de cálculo: son dos métodos distintos. El hub cuenta las herramientas
del registro; la cifra cuenta páginas indexables bajo `/herramientas/*/`, y hay dos
rutas internas (`auditor-web`, y el hub mismo) que quedan fuera. Ambos números son
correctos según su método, y por eso el problema no lo detecta ningún test: hay que
decidir **qué número se publica** y que los dos sitios usen el mismo.

### 3.2 «Libros publicados: 1»

El método declarado es «páginas indexables bajo `/libros/*/`». Manecillas vive en
`/las-manecillas-del-recuerdo/`, fuera de `/libros/`, así que no cuenta. Un autor con
dos novelas publica un «1» en su propia página de autor.

---

## 4. Fecha de publicación de Manecillas

`editorial-facts.json` declara:

```json
"publicationDate": "2026-09-03",
"statusBeforePublication": "published"
```

Ese `statusBeforePublication` empezó siendo `"scheduled"` y se cambió a `"published"`
en el commit `ced4799` («permanent Manecillas copy»). El efecto es que el sitio dice
hoy —22 de agosto— que el libro **fue publicado** el 3 de septiembre, doce días antes
de que ocurra. El verificador del repo lo acepta porque corre en `mode=prelaunch`, así
que es coherente consigo mismo y ningún test lo marca.

**No es un problema mientras la rama no sea producción.** Si el paso a `main` ocurre el
3 de septiembre o después, todo el copy es correcto sin tocar nada. Si se adelanta,
hay que volver a `"scheduled"` antes.

Se deja anotado porque es una afirmación de hecho sobre una obra, no un detalle
técnico, y la decisión es del autor.

---

## 5. Estado técnico

Sobre el HEAD de la rama, ejecutado en local:

| Bloque | Resultado |
|---|---|
| Comprobaciones de contenido, paridad y contrato | **23 PASS / 0 FAIL** |
| Tests de motor y contrato | **44 PASS / 0 FAIL** |
| Suites de QA de navegador | **12 PASS / 0 FAIL** |
| Gate de reflow (zoom 200 % + text-spacing WCAG) | **66 rutas × 2 viewports = 132 checks** |
| Pa11y WCAG2AA | 55/55 |

Puertas que existen hoy y no existían al empezar la sesión anterior: reflow sitewide,
escaneo de secretos en todas las PR, frescura real del radar, idempotencia de
builders, contrato del registro público del hub, paridad de builders de Editoriales y
Convocatorias, y contrato de cliente de la newsletter.

---

## 6. Lo que queda abierto

Nada de esto bloquea el paso a diseño. Ordenado por lo que costaría dejarlo sin hacer.

| # | Asunto | Tipo |
|---|---|---|
| 1 | Recuperar el enlace a la política de privacidad de Metricool | **Legal** |
| 2 | Recuperar los tres perfiles de autor (StoryGraph, Babelio, Amazon) en el `sameAs` | Autoridad |
| 3 | Unificar «17» vs «15» herramientas | Coherencia pública |
| 4 | Decidir el método de «Libros publicados» para que cuente Manecillas | Coherencia pública |
| 5 | Recuperar los dos libros recomendados que perdieron su enlace de compra | Contenido |
| 6 | Confirmar la fecha de promoción a `main` frente al 3 de septiembre | Decisión del autor |
| 7 | Confirmar la reducción del río editorial de la Home (9 → 5 tarjetas) | Diseño |
| 8 | Puntero vs foco en el resalte del mapa de la Home | Interacción |
| 9 | El asistente se auto-abre encima del contenido principal de la Home | Producto |
| 10 | 292,8 MB de imágenes sin referenciar (`assets/alicia_capitulo_*`) | Informe pendiente |
| 11 | 26 páginas fuera de la guía de longitud de `title`/`description` | Informe pendiente |
| 12 | Segundo email de contacto propuesto (`davidportodiaz@gmail.com`) | Decisión del autor |

Los puntos 10 y 11 ya tienen tarea escrita en el handoff como **informe, no
implementación**: los dos tocan material publicado o copy del autor.

---

## 7. Conclusión

**La rama contiene todo lo que hay en producción, y bastante más.** Cero páginas
perdidas, cero activos perdidos, 19 de 19 herramientas del dossier publicadas, y nueve
enlaces externos caídos de los que cuatro merecen recuperarse.

Las dos incoherencias numéricas del punto 3 son las únicas que un visitante nota hoy,
y ninguna la detecta un test porque cada número es correcto según su propio método.
Esa es la clase de fallo que sobrevive a una CI verde, y por eso están aquí y no en un
check.
