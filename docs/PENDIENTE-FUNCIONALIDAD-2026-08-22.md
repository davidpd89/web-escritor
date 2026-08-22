# Funcionalidad pendiente — brief de ejecución

Fecha: 2026-08-22 · Rama base: `implementacion-web-2026` · Destino: esta PR

> **Para quién es esto.** Para la sesión que va a implementar. Todo lo que hay
> aquí está verificado con comandos contra el HEAD de la rama, no deducido de la
> documentación del dossier. Cada tarea trae la evidencia, el criterio de
> aceptación y la trampa concreta en la que es fácil caer.
>
> **Lo que NO entra aquí:** diseño visual final, motion, View Transitions,
> tratamiento de media y acabado del hero. Eso se hace en la otra sesión con el
> autor delante. Esta PR es solo código que falta, huecos y errores.

---

## Reglas de la casa (leer antes de tocar nada)

Estas cinco no son burocracia: son los cinco modos de fallo que ya han mordido
en este repo durante las tres rondas anteriores de PR.

1. **Una puerta que no se dispara se ve igual que una que pasa.** Van cuatro
   casos. Si añades o cambias un workflow, **rómpelo a propósito, míralo en
   rojo, revierte, y dilo en la PR**. Un check verde no demuestra que se haya
   ejecutado: mira el log del job.
2. **Escribir la assertion no es cumplirla.** Si añades un contrato, deja el
   producto cumpliéndolo en la misma PR, o marca la PR como DRAFT diciéndolo.
3. **No debilites una assertion para poner CI en verde.** Si una prueba falla,
   el fallo es la información. Si de verdad hay que relajarla, dilo
   explícitamente en la PR y explica por qué el caso que deja de cubrir no
   importa.
4. **No se toca `main` ni se despliega.** GitHub Pages publica `main` desde la
   raíz: mergear a `main` **es** desplegar. Esta PR va contra
   `implementacion-web-2026`.
5. **Medir en el tick correcto.** Leer `getComputedStyle` justo después de un
   `Tab` o un `hover`, con una `transition` de por medio, devuelve el valor de
   partida. Y bajo `prefers-reduced-motion` la receta del sitio es
   `transition-duration:.01ms!important`, **no `0s`**: hay transición real,
   cortísima. Deja pasar un frame y no exijas `=== 0`.

Cómo verificar en local (el servidor estático es lo único que hace falta):

```bash
python -m http.server 4173 --bind 127.0.0.1 &
node qa/<suite>.mjs                     # QA de navegador
python tests/<test>.py                  # tests de contrato
python scripts/check-<lo-que-sea>.py    # checks estáticos
```

Nota de entorno: no hay `package.json` en el repo, así que **`npm ci` no puede
funcionar**. Y `pdfinfo`/`pdftotext` solo existen en CI (los instala
`samuel-ecosystem-browser-qa.yml`); en local esas assertions se omiten con
aviso, y en CI su ausencia **falla a propósito**.

---

## 1. El shell está escrito a mano en 58 páginas y ha derivado — BLOQUEANTE

Es la tarea grande, y la única con consecuencia legal. Las tareas 2 y 4 son
subproductos suyos: si se hace bien, se cierran solas.

### El problema

`data/navigation.json` se declara a sí mismo como contrato:

```json
"runtimeOwnership": {
  "shell": "authored-static-v1-html",
  "contract": "data/navigation.json + CI parity"
}
```

**Esa «CI parity» no existe.** `scripts/check-navigation-coverage.py` compara
`navigation.json` contra `content-registry.json` y contra `sitemap.xml` —JSON
contra JSON— y **nunca abre una página** para comprobar que el HTML muestra lo
que el contrato dice que se muestra. El fichero declara una puerta que nadie
construyó, así que el shell lleva meses copiándose a mano y separándose del
contrato sin que ningún check pueda verlo.

### La evidencia

Medido sobre las 58–59 páginas que tienen shell (excluido `lab/`):

**a) La cabecera de `/ai/` no es la del resto del sitio.**

| Dónde | Enlaces |
|---|---|
| `navigation.json` → `header` | `works-hub`, `notebook-hub`, `tools-hub` |
| 58 páginas | Obra · Cuaderno · Herramientas |
| `ai/index.html` | Obra · **Autor · Prensa** |

**b) El pie de ninguna página se parece al pie declarado.**

| Dónde | Grupos |
|---|---|
| `navigation.json` → `footer` | Obras · Escribir · Leer · David · Sitio |
| Todas las páginas | Obra · Leer · Información |

Los grupos declarados incluyen destinos que hoy no están en ningún pie:
`editorials-hub`, `opportunities`, `external-tools`, `notebook-topics`,
`recommendations-hub`, `work-manecillas-fragments`, `awards`.

**c) Ocho páginas pierden destinos del pie que el resto sí tiene.**

| Página | Le falta en el pie |
|---|---|
| **`las-manecillas-del-recuerdo/index.html`** | **`/ai/`, `/aviso-legal.html`, `/fragmento/`, `/mapa-del-sitio/`** |
| `404.html` | `/ai/`, `/fragmento/` |
| `aviso-legal.html` | `/fragmento/` |
| `privacidad.html` | `/fragmento/` |
| `eventos.html` · `ferias.html` · `premios.html` · `prensa.html` | `/ai/` |

**La primera línea es la grave.** La ficha de *Las manecillas del recuerdo* es
la página a la que apunta todo el lanzamiento del 3 de septiembre, y hoy **no
tiene ni un solo enlace al aviso legal** (comprobado: `grep -c
'href="/aviso-legal.html"'` devuelve `0`, y tampoco está en la cabecera). Va a
ser la página más visitada del sitio y es la única sin salida a su nota legal.

### Lo que hay que hacer

Generar el shell desde `navigation.json` con un builder e inyectarlo entre
marcadores, **exactamente con el patrón que ya usa el repo**. Mira
`scripts/build-human-site-stats.py` antes de escribir nada: marcadores
`<!-- ... :start -->` / `:end`, `--inject-into`, `--check` que no escribe nada
y devuelve 1 si algo está desactualizado. `scripts/build-tools-hub.py` es el
otro ejemplo. No inventes un mecanismo nuevo.

Propuesta: `scripts/build-site-shell.py`, con marcadores para cabecera, pie y
diálogo Explorar, aplicado a las 58 páginas. Los textos visibles (`label`,
`shortLabel`) salen del `content-registry.json`, que es donde ya viven.

**La trampa: parte de la variación del pie es deliberada. No la aplanes.**

| Enlace | En cuántas páginas | Por qué |
|---|---|---|
| `/aviso-legal.html#afiliado` | 10/58 | Solo donde hay enlaces de afiliado. **Quitarlo o ponerlo en todas es peor** |
| `/cuaderno/feed.xml` | 12/58 | Solo en el Cuaderno |
| `/ferias.html` | 2/58 | Contextual |
| `/premios.html` | 4/58 | Contextual |

Diseña el builder con **núcleo común obligatorio + extras declarados por
página**, no con un pie único. Si un pie necesita un extra, que se declare en
un sitio y se vea; si pierde un enlace del núcleo, que el `--check` falle.

Y ojo con lo contrario: las 21 «variantes» del diálogo Explorar y las 22 del
pie que salen de un hash del bloque **no son 21 y 22 derivas**. Los seis
enlaces del Explorar son idénticos en las 58 páginas; lo que cambia es el texto
del preview por defecto, que es correcto que cambie. Medí primero por hash y me
dio un número alarmista y falso; el número real es el de arriba, medido por
conjunto de enlaces. Mide enlaces y destinos, no bytes.

### Criterio de aceptación

- [ ] `python scripts/build-site-shell.py --check` pasa, y **falla si alguien
      edita a mano el pie de una página** (demuéstralo en la descripción de la
      PR: rómpelo, pega el fallo, revierte).
- [ ] El check corre en un workflow que **se dispara en cualquier PR**, sin
      filtro de `paths:` que lo deje fuera, y sin `branches:` que lo deje sin
      ejecutar. Este es el error nº1 de la lista de arriba, y ya ha pasado
      cuatro veces.
- [ ] `las-manecillas-del-recuerdo/index.html` recupera los cuatro destinos.
- [ ] La cabecera de `/ai/` es la del contrato, o `navigation.json` declara
      explícitamente que esa página tiene cabecera propia y el check lo respeta.
      **Decide y déjalo escrito**; lo que no vale es que sea distinta por
      accidente.
- [ ] Los cuatro extras contextuales de la tabla siguen exactamente donde están.
- [ ] `python scripts/check-navigation-coverage.py`, `check-internal-graph.py`,
      `check-hrefs.py` y `check-heading-structure.py` siguen en verde.
- [ ] `node qa/global-discoverability-browser.mjs` y `node
      qa/findability-browser.mjs` en verde.
- [ ] **Geometría neutra:** el shell generado no puede mover nada. Mide ancho y
      alto de `main` en 5 rutas × 3 anchos (320, 768, 1440) antes y después y
      pega las diferencias en la PR. Deben ser 0.

---

## 2. Explorar: faltan los atajos y el mapa del sitio, y sobra un `aria-live`

### 2.1 El diálogo ignora la mitad del contrato

`navigation.json` declara tres bloques para Explorar y el diálogo solo pinta
uno, y ni siquiera ese:

| Declarado | Qué hay en el HTML |
|---|---|
| `exploreTerritories`: 5 (`works-hub`, `notebook-hub`, `tools-hub`, `author`, `press`) | 6 filas escritas a mano (Manecillas, Autor, Samuel, Cuaderno, Herramientas, Prensa) |
| `exploreShortcuts`: 5 («Leer un fragmento», «Revisar un texto», «Buscar editorial o convocatoria», «Preparar publicación o promoción», «Recursos para prensa») | **nada** |
| `exploreUtilities`: `["site-map"]` | **nada** |

Es el mismo agujero de la tarea 1: nadie renderiza `navigation.json`. Si la
tarea 1 genera el diálogo desde el contrato, esto se cierra solo. Si decides
que las 6 filas actuales son las correctas y las 5 territories están mal,
**arregla el JSON**, no lo ignores.

### 2.2 `aria-live` que contradice una decisión ya tomada

Las 58 páginas llevan:

```html
<aside class="explore-preview" aria-live="polite" aria-atomic="true" data-explore-preview>
```

El documento 13 del dossier decidió expresamente que **la preview no lleva
`aria-live`**, porque recorrer los destinos con teclado provoca una ráfaga de
anuncios: cada `focus` reescribe el preview y el lector de pantalla lo canta
entero, encima del nombre del enlace que el usuario está intentando oír. Es un
residuo de una versión anterior.

Quitar los dos atributos. El preview es contenido complementario del enlace
enfocado, no una región viva.

### Criterio de aceptación

- [ ] `aria-live` y `aria-atomic` fuera de `.explore-preview` en las 58 páginas.
- [ ] Atajos y mapa del sitio presentes en el diálogo, o `navigation.json`
      corregido con una razón escrita.
- [ ] La navegación por teclado dentro del diálogo sigue atrapada (ya hay trampa
      de foco explícita en `assets/v1-shell.js`; los atajos nuevos entran en el
      ciclo sin romperla) y `aria-expanded` sigue volviendo a `false` **de forma
      síncrona** al cerrar. Esa parte se arregló en la PR #48 y hay que no
      romperla: `<dialog>` quita `open` de forma síncrona pero encola `close`,
      así que confiar en el evento `close` deja una ventana en la que el diálogo
      ya no se ve y el disparador sigue diciendo `true`.
- [ ] `node qa/global-discoverability-browser.mjs` en verde.

---

## 3. Puntero y foco se pelean por el resalte del mapa de la Home

`assets/v1-shell.js`, dentro de `initMap()`:

```js
node.addEventListener('mouseenter', on);
node.addEventListener('mouseleave', off);
node.addEventListener('focus', on);
node.addEventListener('blur', off);
```

Los cuatro escriben y borran el mismo `map.dataset.active`, así que gana el
último evento que llegue, venga de donde venga. Si el ratón está parado encima
de un nodo y el usuario navega con Tab, el desplazamiento de la página dispara
un `mouseleave` tardío sobre el nodo del ratón y **le roba el resalte al nodo
que tiene el foco**. El usuario de teclado pierde de vista dónde está.

> Aviso: una revisión anterior dio esto por cerrado en la PR #31. No lo está —
> el código de arriba es el HEAD actual de la rama. Compruébalo antes de creerte
> ninguna de las dos versiones, incluida esta.

**Esto es una decisión, no un arreglo obvio.** La opción sensata es que el foco
mande: mientras haya un nodo enfocado, el puntero no puede quitar ni cambiar el
resalte. Se puede hacer con dos claves separadas (`data-hover` y `data-focus`,
y que el CSS prefiera la de foco) o guardando cuál fue la última entrada real.
Elige una, escríbela en la PR, y que el CSS no dependa de un orden de eventos.

### Criterio de aceptación

- [ ] Con el puntero quieto encima de un nodo, recorrer el mapa con Tab mantiene
      el resalte en el nodo enfocado, en los seis nodos.
- [ ] Con el teclado sin usar, el hover sigue comportándose igual que hoy.
- [ ] Caso mixto: enfocar con Tab, mover el ratón a otro nodo, sacar el ratón
      del mapa → el resalte sigue en el nodo enfocado.
- [ ] Test añadido a `qa/home-map-interaction.mjs`, y **enseña el rojo**: mete el
      caso, míralo fallar contra el código actual, arregla, pega las dos salidas.
- [ ] El widget del asistente ya no se auto-abre, pero **sí muestra un aviso una
      vez por sesión** (`showHintOnce` en `assets/assistant-widget.js`). Cualquier
      QA de la Home debe marcar antes la clave de sesión correspondiente, o el
      aviso se cuela en la medición.

---

## 4. No existe la página de Accesibilidad

Comprobado: no hay `accesibilidad.html` ni `/accesibilidad/`, y el pie enlaza
Autor, Prensa, Eventos, Privacidad, Aviso legal e IA, pero no Accesibilidad.

La matriz 13 del dossier la adopta como **P1 antes de producción**. Es además
lo que se espera de un sitio público que declara conformidad WCAG, y este la
declara: hay gate de reflow, pa11y 55/55 y suites de teclado.

Contenido mínimo, siguiendo el modelo del W3C:

- estándar aplicado (WCAG 2.1 AA) y hasta dónde se ha verificado;
- **limitaciones reales conocidas**, no una declaración de perfección;
- medidas concretas ya tomadas (navegación por teclado, reflow a 320 px con
  zoom 200 %, `prefers-reduced-motion`, contraste, funcionamiento sin JS);
- vía de contacto: `davidportodiaz@gmail.com`;
- fecha de la declaración.

**No inventes conformidad.** Si algo no está verificado, se dice que no está
verificado. Una declaración de accesibilidad falsa es peor que no tenerla.

### Criterio de aceptación

- [ ] Página creada, indexable, con canonical en `davidportodiaz.com`, en el
      registro (`content-registry.json`) y en el sitemap.
- [ ] Enlazada desde el pie de las 58 páginas (sale gratis si se hace la tarea 1).
- [ ] `check-social-cards.py --strict`, `check-heading-structure.py`,
      `check-navigation-coverage.py` y `build-sitemap.py --check` en verde.
- [ ] pa11y en verde sobre la ruta nueva.
- [ ] El texto lo revisa el autor antes de mergear: es copy suyo, no técnico.

---

## 5. Recuperar la mención externa de `hoymadrid.app`

De los seis dominios externos que existían en producción y no están en la rama,
cinco son herramientas de desarrollo que vivían en `/ai/` (validadores de
JSON-LD y schema, test de resultados enriquecidos, `llmstxt.org`, primer de
RDF) y no le importan a ningún lector. **El sexto sí importa**: `hoymadrid.app`
documentaba la presentación de *Samuel entre mundos*, o sea acredita un evento
real.

Antes de tocar nada:

1. Comprueba que **la URL concreta sigue viva** y sigue mostrando la mención. Si
   ha caducado, no la pongas: un enlace de evidencia roto es peor que ninguno.
   Dilo en la PR y para aquí.
2. Si vive, colócala **donde acredita algo** —la ficha del evento en
   `eventos.html` o la sección de apariciones de `prensa.html`— como fuente, con
   `rel="noopener noreferrer"`. No la metas en el pie.

### Criterio de aceptación

- [ ] URL verificada viva, o tarea cerrada con la comprobación escrita.
- [ ] Colocada como evidencia junto al hecho que acredita, no como enlace suelto.
- [ ] `check-hrefs.py` y `check-internal-graph.py` en verde.

---

## Lo que ya está decidido y no hay que reabrir

Para que no se gaste trabajo en cosas cerradas:

| Asunto | Estado |
|---|---|
| Cifras de «Esta web, en cifras» (2 libros, 17 herramientas) | **Hecho** en la PR #50: se cuentan desde `content-registry.json` y `tools-hub.json` |
| Email del autor | **Hecho** en la PR #50: solo `davidportodiaz@gmail.com` |
| Fecha de publicación de Manecillas en «publicada» | **Decisión del autor.** La web se lanza con el libro |
| Río editorial de la Home (9 → 5 tarjetas) | **Revisado.** Los cuatro destinos retirados siguen enlazados 4, 4, 2 y 4 veces desde la propia Home |
| Auto-apertura del asistente | **Cerrado.** Ahora es un aviso una vez por sesión, no un panel |
| Generar imágenes con IA para la V1 | **Descartado** por la autoridad visual. Si falta una imagen se usa material real o geometría neutra CSS/SVG |
| Buscador global, Atlas, red de autores, popup de newsletter | **Pospuestos** a propósito |
| Hero, motion, View Transitions, preview con media real | **Fase de diseño.** No en esta PR |
| 292,8 MB de imágenes sin referenciar · 26 páginas fuera de la guía de longitud de `title`/`description` | **Informe, no implementación.** Tocan material publicado y copy del autor |

---

## Orden sugerido

1 → 2 → 4 son la misma pieza: haz el builder del shell primero y las otras dos
caen casi solas. 3 y 5 son independientes y se pueden hacer en cualquier
momento.

Si algo de esto resulta estar mal —y la tarea 3 ya viene con un desmentido de
una revisión anterior—, **dilo en la PR con el comando que lo demuestra** en
lugar de implementarlo igual.
