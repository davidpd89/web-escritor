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

Comparar URLs exactas entre dos versiones de un sitio rediseñado da un resultado
engañoso: cualquier cambio de `autor.html` a `/autor.html`, o de la versión inglesa a
la española de una política de terceros, aparece como «enlace perdido» sin serlo. La
medida útil es por dominio: **¿queda algún destino externo de producción sin ninguna
referencia en la rama?**

| Medida | Resultado |
|---|---|
| Dominios externos referenciados desde producción | 43 |
| Dominios externos referenciados desde la rama | 80 |
| **Dominios de producción sin ninguna referencia en la rama** | **6** |

Los seis:

| Dominio | Qué era | Peso |
|---|---|---|
| `hoymadrid.app` | mención externa de la presentación de *Samuel entre mundos* | **Evidencia editorial.** El único con valor de contenido |
| `json-ld.org/playground/` | validador de JSON-LD | Herramienta de desarrollo |
| `validator.schema.org` | validador de schema.org | Herramienta de desarrollo |
| `search.google.com/test/rich-results` | test de resultados enriquecidos | Herramienta de desarrollo |
| `llmstxt.org` | especificación de `llms.txt` | Referencia |
| `w3.org/TR/rdf11-primer/` | primer de RDF | Referencia |

Cinco de los seis son enlaces de utilidad para quien programa, que vivían en
`/ai/index.html`. Su ausencia no afecta a ningún lector ni a ningún buscador.

**Lo que conviene recuperar es uno: `hoymadrid.app`**, porque acredita un evento real.

#### Tres cosas que parecían perdidas y no lo están

Las anoto porque son justo los falsos positivos que produce comparar URLs exactas, y
para que nadie abra una PR a arreglarlas:

- **Perfiles de autor** (StoryGraph, Babelio, página de autor de Amazon). Siguen en el
  `sameAs` del JSON-LD de `autor.html` e `index.html`, y en `llms.txt`,
  `editorial-facts.json` y el press-kit. Lo que cambió es que ya no son enlaces
  pinchables en `/ai/`. La autoridad de entidad está intacta.
- **Política de privacidad de Metricool.** Sigue enlazada desde `privacidad.html`, en
  la versión española (`metricool.com/es/politica-privacidad/`) en lugar de la inglesa.
  Para un sitio en español es mejor, no peor.
- **Los dos libros de `/recomendaciones/magia-con-coste/`.** Sus URL de Amazon estaban
  en el campo `url` del `Book` en JSON-LD, no como enlaces visibles. Poner un enlace de
  afiliado como `url` canónica del libro **de otro autor** es discutible de por sí, así
  que quitarlas no es una pérdida.

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

## 3. Incoherencias que ve un visitante — RESUELTAS 22/08/2026

Las dos las veía cualquiera que navegase dos páginas seguidas. Las dos venían del
mismo error de fondo: **contar por prefijo de URL**. Un prefijo es una decisión de
rutas, no la definición de qué es una obra publicada ni de qué es una herramienta
pública. Ahora cada cifra se cuenta desde su registro canónico.

### 3.1 El sitio decía dos números distintos de herramientas

| Dónde | Decía | Dice |
|---|---|---|
| `/herramientas/` | «17 herramientas» | «17 herramientas» |
| `autor.html`, «Esta web, en cifras» | «15 herramientas gratuitas» | «17 herramientas gratuitas» |

No era un error de cálculo: eran dos métodos distintos. El hub contaba las
herramientas del registro; la cifra contaba páginas indexables bajo
`/herramientas/*/`, que deja fuera las rutas internas y las herramientas publicadas
fuera de ese prefijo. Ambos números eran correctos según su método, y por eso no lo
detectaba ningún test.

`build-human-site-stats.py` cuenta ahora desde `data/tools-hub.json`, **la misma
fuente que usa el titular del hub**, así que los dos números ya no pueden divergir
por construcción. Y `tests/test-human-site-stats.py` compara explícitamente la cifra
publicada con el titular del hub: si alguien vuelve a separarlos, falla.

### 3.2 «Libros publicados: 1» → 2

El método declarado era «páginas indexables bajo `/libros/*/`». Manecillas vive en
`/las-manecillas-del-recuerdo/`, fuera de `/libros/`, así que no contaba: un autor con
dos novelas publicaba un «1» en su propia página de autor.

Ahora cuenta las entradas `type: work` de `data/content-registry.json` que no son el
propio hub y cuyo estado es público. Da 2, y da igual dónde viva cada ficha. *Dónde
empieza la jaula* queda fuera sola por su `status: noindex`, y entrará sola el día
que se publique.

En los dos casos el registro decide **qué** cuenta y el HTML decide **si de verdad
está publicado**: toda ruta declarada tiene que existir, no ser `noindex` y llevar
canonical en el dominio canónico. Si el registro y la página se contradicen, el build
falla en vez de publicar una cifra falsa.

---

## 4. Fecha de publicación de Manecillas — DECIDIDO 22/08/2026

`editorial-facts.json` declara:

```json
"publicationDate": "2026-09-03",
"statusBeforePublication": "published"
```

Ese `statusBeforePublication` empezó siendo `"scheduled"` y se cambió a `"published"`
en el commit `ced4799` («permanent Manecillas copy»). El efecto es que el sitio dice
hoy —22 de agosto— que el libro **fue publicado** el 3 de septiembre.

**Decisión del autor: se queda como está.** La web se lanza *con* el libro, así que
para cualquiera que lea estas páginas la publicación ya habrá ocurrido. El copy está
escrito para el lector que llega, no para la fecha en que se escribió.

Queda por tanto cerrado, no abierto. Lo único que sigue vivo es la comprobación final
de release: el día real de promoción a `main`, verificar que fecha, estado y enlaces
de compra son los correctos.

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

### Cerrados el 22/08/2026

| # | Asunto | Cómo se cerró |
|---|---|---|
| 1 | Unificar «17» vs «15» herramientas | Las dos cifras salen ya de `data/tools-hub.json`, y un test compara la publicada con el titular del hub |
| 2 | «Libros publicados» debe contar Manecillas | Se cuenta desde `data/content-registry.json`: da 2, sin depender del prefijo de URL |
| 3 | Fecha de promoción frente al 3 de septiembre | Decisión del autor: la web se lanza con el libro, el copy se queda en «publicada» |
| 5 | Reducción del río editorial de la Home (9 → 5) | Revisada: las cuatro tarjetas retiradas (`/cuaderno/`, `/herramientas/`, `/eventos.html`, `/prensa.html`) siguen enlazadas desde la propia Home 4, 4, 2 y 4 veces por cartografía, cabecera y pie. Se quitaron duplicados, no destinos |
| 6 | Segundo email de contacto | Decisión del autor: **hay un solo email suyo, `davidportodiaz@gmail.com`**. `samuelentremundos@gmail.com` desaparece del sitio (22 ficheros). Los correos de editoriales o terceros no se tocan |

### Siguen abiertos

| # | Asunto | Tipo |
|---|---|---|
| 4 | Recuperar el enlace a la mención de `hoymadrid.app` | Evidencia editorial |
| 7 | Puntero vs foco en el resalte del mapa de la Home | Interacción |
| 8 | El asistente se auto-abre encima del contenido principal de la Home | Producto |
| 9 | 292,8 MB de imágenes sin referenciar (`assets/alicia_capitulo_*`) | Informe pendiente |
| 10 | 26 páginas fuera de la guía de longitud de `title`/`description` | Informe pendiente |
| 11 | Devolver a `/ai/` los enlaces a validadores y especificaciones, si se quieren | Opcional |

Los puntos 9 y 10 ya tienen tarea escrita en el handoff como **informe, no
implementación**: los dos tocan material publicado o copy del autor.

## 7. Conclusión

**La rama contiene todo lo que hay en producción, y bastante más.** Cero páginas
perdidas, cero activos perdidos, 19 de 19 herramientas del dossier publicadas, y un
solo destino externo con valor de contenido sin recuperar.

Las dos incoherencias numéricas del punto 3 eran las únicas que un visitante notaba, y
ninguna la detectaba un test porque cada número era correcto según su propio método.
Esa es la clase de fallo que sobrevive a una CI verde, y por eso aparecieron aquí y no
en un check. Al arreglarlas se ha añadido el check que faltaba: comparar las dos cifras
entre sí, que es lo que ningún método por separado podía ver.

### Nota de método

La primera versión de esta auditoría comparaba URLs exactas y concluía que había nueve
destinos perdidos, cuatro de ellos importantes. Al verificarlos uno a uno, tres eran
falsos positivos —los perfiles de autor siguen en el `sameAs`, la política de Metricool
sigue enlazada en su versión española, y las URL de Amazon eran campos de JSON-LD, no
enlaces—. Comparar URLs exactas entre dos versiones de un sitio rediseñado no mide lo
que parece medir. La comparación por dominio, más los tres desmentidos de arriba, es lo
que queda en pie.
