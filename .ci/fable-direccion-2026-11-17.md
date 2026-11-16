# Dirección técnica de Fable — ronda 4 (entrega 17/11/2026, escrita el 16/11)

Opus: empieza por la sección 7 (backlog). Marca el estado en este fichero con las tres marcas de R4-17, no con `[x]` a secas.

**Cómo leer las marcas de cada afirmación**
- «leído» = lo leí en `origin/main` (ac6ba54c9c, #1379) o en el volcado de `gh pr diff`. Los números de línea de #1373, #1374 y #1380 son **líneas del volcado del diff**, no del fichero final.
- «sin verificar» = lo sé de memoria o lo deduzco; no lo comprobé. No medí nada en esta ronda (lo pedía el prompt).
- Nombres cortos: `sync.yml` = `.github/workflows/reading-catalogue-sync.yml`; `publish` = `scripts/publish-radar-refresh.py`; `refresh` = `scripts/refresh-reading-catalogue.py`; `juez` = `scripts/ci_intake_backup.py`; `cuarentena` = `scripts/reading_quarantine.py`; `build` = `scripts/build-reading-catalogue.py`.

## 0. Resumen en seis líneas

1. **El HTML generado no debe viajar por git.** Es la causa común de la mitad de los fallos de la carga y lo primero que se rompe a 10×. Main guarda datos y código; el HTML se construye al desplegar (R4-9).
2. **El día de la web es un parámetro del despliegue, no de los datos.** Ni build diario de 6.000 HTML ni pintar en el cliente (R4-4).
3. **Una GitHub App propia** abre las PR de arreglo y, después, también la PR de la carga. Así corre la CI real y desaparecen los statuses escritos a mano (R4-5, R4-8).
4. **La unidad del ciclo de arreglo es una comprobación que falla y se puede reejecutar**, no una issue en prosa. Lo que no se reproduce no entra al reparador (R4-6).
5. **Un libro de la noche** (un JSON en la rama `catalogo-estado`) sustituye a las tres deducciones sobre listas de ejecuciones (R4-1).
6. **Los fallos viajan como datos (id, regla), no como texto** que luego se lee con expresiones regulares (R4-2).

## 1. Decisiones de la pregunta 0

### D1. Ancla diaria: el día es un parámetro del despliegue
- **Decisión.** Se separan dos conceptos que hoy son uno: `data_anchor` (frescura de los datos; se queda como está) y `hoy` (día civil de Madrid). `hoy` solo lo usan las superficies relativas a la fecha: portal, novedades, página 1 del catálogo, ICS y su `lastmod`.
- **Cómo.** `deploy-pages.yml` recibe `hoy` y regenera solo esas superficies justo antes de subir el artefacto. No hay commit ni PR. El reloj externo (Worker) lo lanza a las 00:05 de Madrid. Si la carga falla, la web cambia de día igualmente.
- **Requisito previo.** Hoy la ficha depende del día: `render_book` usa `upcoming_books` y `data_anchor` (leído: `build:1230` y `build:1242`). La ficha pasa a llevar solo fechas absolutas en `<time datetime>`; la etiqueta relativa («hoy», «mañana», «ya a la venta») la pone un script mínimo, y sin JavaScript se ve la fecha.
- **Por qué no las dos opciones de Opus.** Reconstruir 6.000 HTML a diario pasa por una PR con 75 min de CI y compite con la carga. Pintar en el cliente depende de P1-4 y deja sin novedades a quien no ejecute JavaScript. La propuesta de Opus («solo portal, novedades y sitemap») es correcta en el alcance; le faltaba decir que no pasa por git.
- **Test que lo fija.** Construir con `hoy = D` y con `hoy = D+1` y comparar la lista de ficheros distintos: debe ser exactamente la lista declarada `SALIDAS_DEL_DIA`. Si cambia una ficha, falla.

### D2. Fallo determinista de madrugada: nadie arregla código de noche
- **Decisión.** De noche solo se publica lo publicable y se aparta lo demás. El arreglo de código va por el ciclo único de la sección 2, de día y en Actions. El PC de David deja de ser dependencia: el autorepair local queda como «hombre muerto» que avisa, no como reparador.
- **Clasificación al terminar cada carga** (la escribe la carga, no se deduce después):
  - *transitorio* (red, 5xx, cola): un reintento sobre el mismo commit;
  - *dato* (un libro malo): cuarentena, que ya existe;
  - *código* (una prueba que depende del tamaño o del contenido del catálogo): no se reintenta; se abre una issue `fallo` con la firma y la orden que falla.
- **#1380 se fusiona con un cambio.** Su guarda es «main avanzó» (leído: `pr1380.diff`). Cualquier commit de un bot mueve main (el de seguidores, por ejemplo) y reabre el reintento sin que haya llegado ningún arreglo. La condición correcta es «no hay otro intento esta noche con la misma firma y el mismo SHA de código», leída del libro de la noche (R4-1). Su test comprueba cadenas del YAML; debe ejecutar la decisión con un libro de la noche de ejemplo.

### D3. Contratos por id: sí, y un paso más
- **Decisión.** Todos los validadores y contratos devuelven una lista de fallos estructurados (`id`, `isbn`, `regla`, `mensaje`). El texto es solo para personas.
- **Por qué va más allá de la propuesta.** El fallo de anoche es un caso de una clase: la cuarentena deduce el culpable leyendo mensajes. `culprit` extrae el id con una expresión regular al principio del mensaje (leído: `cuarentena:38-42`); la portada duplicada se detecta por el texto (leído: `cuarentena:118`); `flagged_books` toma cualquier palabra con guion como id y no ve los ids sin guion (leído: `cuarentena:151-167`).
- **Test que lo fija.** Propiedad: cambiar títulos (incluidos títulos que contienen el id de otro libro, ids sin guion y mensajes reescritos) no cambia el conjunto apartado. Guarda: prohibido `re.` sobre mensajes de fallo dentro de `cuarentena`.

### D4. I04, precedencia de fechas: se guardan las observaciones, no el ganador
- **Decisión.** Acepto el orden que trae GPT (editorial > todostuslibros > Amazon `publicationDate` > `releaseDate`) con tres cambios.
  1. Cada libro guarda `fechas_observadas: [{fuente, valor, precision, visto}]`. La fecha publicada la calcula una función pura. La propiedad «permutar observaciones no cambia el resultado» se cumple por construcción, y cambiar el orden más adelante no exige volver a consultar las fuentes. `date_status` no se guarda: se deriva.
  2. La precedencia es por edición (ISBN), no por obra.
  3. Rechazo la regla «tras publicar, solo cambios ≤ 7 días de la misma fuente; el resto a revisión». No hay revisor y las novedades tienen prioridad. Una fuente de mayor rango gana siempre. Si el cambio mete o saca un libro de la ventana hoy..hoy+2, se anota en el resumen de la carga.
- **Se mantiene.** Un año-mes nunca se convierte en día 1 y esos libros quedan fuera de las listas diarias.
- **Sin verificar.** Que `releaseDate` de Amazon sea disponibilidad comercial y no fecha de edición. La consulta se hizo en «Instant», contra la regla: encargo E4.

## 2. Pregunta 1 — El ciclo issue → fusión sin David

### 2.1 Comparación y elección

| Vía | Dispara la CI real | Identidad | Riesgo principal | Veredicto |
|---|---|---|---|---|
| (a) GitHub App propia | Sí | Bot propio, fuera del bypass | Custodia de la clave privada (un secreto) | **Elegida** |
| (b) PAT fine-grained | Sí | David | Hereda lo que pueda David, incluido el bypass si su rol está en él (sin verificar quién figura en el bypass); caduca; las PR parecen de una persona | Válido para el Worker (solo Actions). No para escribir código |
| (c) `claude-code-action` por etiqueta + `workflow_dispatch` | No: hay que escribir los statuses requeridos a mano | `github-actions` | Quien escribe el código puede escribir su propio verde (`statuses: write`), y la lista de checks se duplica como en `publish:44-57` (leído) | Rechazada como identidad; se usa como motor |

Se elige (a). `claude-code-action` es el motor que propone el parche, pero nunca tiene el token que escribe. El token de la App se genera en cada ejecución y dura una hora (acción `actions/create-github-app-token`; sin verificar la versión actual). Permisos de la App: `contents: write`, `pull-requests: write`, `issues: write`. Sin `workflows`, sin `administration`, fuera de la lista de bypass.

### 2.2 Diseño: un workflow `reparador.yml`, cuatro jobs con poderes separados

1. **`triaje`** — sin modelo, `GITHUB_TOKEN` con `issues: write`. Decide qué issue entra (2.3).
2. **`arreglo`** — con modelo, `contents: read`, sin token de escritura. Recibe el bloque de máquina de la issue (no su prosa) y deja un parche como artefacto. Herramientas: leer, editar y las órdenes de prueba de una lista cerrada. Sin `WebFetch`.
3. **`publicar`** — sin modelo, token de la App. Valida el parche: rutas permitidas, tamaño máximo, nada en `.github/`, `publish`, `refresh`, el propio reparador ni el manejo de secretos. Empuja `reparacion/issue-N` y abre la PR. La CI corre sola por `pull_request`.
4. **`portero`** — sin modelo, token de la App, cada hora. Fusiona con `--squash --match-head-commit` si se cumple todo esto:
   - los 6 checks requeridos están en verde;
   - CodeRabbit y Codex **han publicado** su revisión (presencia, no un temporizador de 20 min como en `turno_issues`, leído en `pr1374.diff`);
   - no hay hilos sin resolver ni revisión `CHANGES_REQUESTED` (`turno_issues` solo mira `reviewThreads`, leído);
   - no hay carga en curso ni en cola según el libro de la noche.

Reglas del portero:
- El reparador responde a los hilos y hace como mucho 2 rondas de corrección. **No resuelve hilos por su cuenta** (hoy `resolver_hilos` lo hace, leído en `pr1374.diff`). Un hilo se da por resuelto solo si el commit de corrección toca las líneas comentadas, cosa que se comprueba sin modelo.
- El portero sirve también para las PR de Opus. Así no se repite la fusión de #1314 con 8 hallazgos sin leer (leído: `revision-carga-nocturna-2026-11-14.md:100`).

### 2.3 Quién decide que una issue se arregla sola

Ni el modelo ni el autor de la issue. Lo decide `triaje` con reglas fijas:
- La issue lleva un bloque de máquina que solo escriben nuestros scripts: `clase`, `firma`, `origen`, `orden` (elegida de una lista cerrada, nunca texto libre) y `ficheros`.
- `triaje` **reejecuta la orden y exige que falle**. Si no falla, cierra la issue como «ya no se reproduce».
- «Hecho» es que la misma orden pase, más la CI.
- Las issues `experto` no llevan bloque y nunca entran directas. Un hallazgo de experto entra solo si una herramienta determinista lo convierte en una orden que falla.
- Lo que no se puede reproducir va a un resumen semanal para David: una sola issue fijada.

### 2.4 Topes, choques y escalado

- **Topes.** Una PR de reparación abierta a la vez; 2 al día; 2 intentos por firma. El recurso escaso no son los minutos (el repositorio es público), sino la cola: 75 min por ciclo de CI.
- **Choques con la carga.** Reparto del día: el reparador trabaja de 08:00 a 20:00 de Madrid y la noche es de la carga. No comparte el grupo de concurrencia `reading-catalogue-intake`, porque GitHub guarda un solo pendiente por grupo y desplazaría una carga encadenada (leído: `sync.yml:70-74`).
- **Dos reparadores.** Solo hay uno. `turno_issues.py` (#1374) **no se fusiona como ejecutor**: sus límites y rondas pasan a `reparador.yml`, y su estado deja de vivir en `state.json` del PC (leído en `pr1374.diff`). El cerrojo es la rama: empujar `reparacion/issue-N` falla si ya existe.
- **Se escala a David** (todo en la misma issue fijada, no en avisos sueltos) cuando:
  - una firma agota sus 2 intentos;
  - el parche toca rutas protegidas;
  - un hilo sigue abierto tras 2 rondas;
  - una issue elegible lleva 72 h sin PR;
  - el reparador lleva 3 días seguidos sin ningún arreglo fusionado habiendo issues elegibles.

### 2.5 Lo que necesita a David una sola vez
Crear la App e instalarla en el repositorio (o aprobarlo en el navegador mientras Opus lo hace en Edge 9240) y guardar la clave privada como secreto.

## 3. Pregunta 2 — Crítica del equipo de expertos (#1373)

**Discrepancia con el prompt.** El prompt r4 dice «Claude Sonnet, `--max-turns 25`, `--permission-mode default`». El diff usa GitHub Models (`openai/gpt-4.1`) con `GITHUB_TOKEN`; el modelo devuelve JSON y el script crea las issues (leído: `.ci/empleados-expertos.md`, línea 16 del volcado). Es **mejor** forma que la descrita: el modelo no tiene herramientas ni token. `CLAUDE_CODE_OAUTH_TOKEN` queda libre para el reparador.

### 3.1 Qué falla

| # | Dónde (volcado de #1373) | Problema | Solución |
|---|---|---|---|
| X1 | `ux.md` l.266; `seo.md` l.242; `rendimiento.md` l.200-203; `arquitecto.md` frente a `datos_rol` l.679-681 | Los prompts prometen entradas que el modelo no recibe (WebFetch, ficheros, código). El modelo rellena con invención | Test: cada entrada que nombra un prompt existe en `datos_rol` de ese rol. Rol sin datos, rol apagado |
| X2 | `MAX_DATOS=14000` l.662; `resumir_siteone` l.513-528; `equipo[:3000]` l.699-705 | Recortes en silencio: el experto opina sobre datos truncados sin saberlo | El prompt dice qué se recortó y cuánto; se recorta por unidades enteras (páginas, hallazgos), no por caracteres |
| X3 | `_gh` l.668-670 | Un error de `gh` devuelve `''`, que se lee como «no hay issues abiertas» y produce duplicados | Error ⇒ el rol no publica ese día |
| X4 | `publicar` l.744-758 | No comprueba el resultado de `issue create` | `check=True` y recuento en el resumen |
| X5 | workflow l.352 y l.364 | `continue-on-error` y `\|\| true`: si SiteOne falla, el experto opina sin datos | Sin datos de la herramienta, el rol no corre |
| X6 | workflow l.357 | SiteOne se baja con `curl` sin suma de control, en un job con `issues: write` | Versión fijada con SHA-256, en un job aparte sin permisos de escritura |

### 3.2 Qué producirá ruido
- **Muestra determinista** (`ordenar_muestra`, l.488-510): cada rotación ve las mismas páginas y repite los mismos hallazgos. Solución: muestra con semilla = fecha, estratificada (fichas nuevas, antiguas, sin sinopsis…).
- **Deduplicación por título exacto y solo contra issues abiertas** (l.744-758): un hallazgo reescrito entra otra vez, y uno cerrado como «no procede» vuelve a abrirse. Solución: firma = rol + regla + ruta afectada, comparada también contra las cerradas de los últimos 90 días.
- **`propuestas` solo exige campos no vacíos** (l.717-730): no pide evidencia. Solución en 3.3.
- **Hasta 3 issues al día sin consumidor**: 21 por semana que nadie lee.

### 3.3 Huecos de seguridad
- **Cadena de inyección.** Contenido web o de terceros → prompt → issue firmada por `github-actions` → `turno_issues.AUTORES` confía en ese autor (leído en ambos volcados). El único cortafuegos es la etiqueta: `fallo` entra y `experto` no.
- **`comun.md` l.139-159 no declara los datos como no fiables.** Declararlo ayuda poco. Lo que protege es comprobar la salida sin modelo:
  - cada hallazgo cita una evidencia y el script comprueba que la cita es subcadena de los datos de entrada, que la ruta existe y que la URL estaba en el conjunto rastreado; si no, se descarta;
  - el cuerpo de la issue se limpia de enlaces externos, imágenes, HTML y menciones (`_sin_menciones`, l.733, solo quita menciones);
  - las issues de expertos nunca llevan bloque de máquina (2.3), así que no pueden disparar al reparador aunque alguien les cambie la etiqueta.
- **Investigador** (l.688-695): mete descripciones de repositorios de terceros en el prompt. Solución: solo nombre, URL, licencia y estrellas; su salida va al resumen semanal y no a issues.
- **`WebFetch`**: no existe en esta implementación. Que siga así. En el reparador tampoco (2.2).
- **`gh label create --force`** (l.340): innecesario en cada ejecución; se crea una vez.

### 3.4 Métrica y despido
Por rol, en ventana móvil de 4 semanas y con al menos 8 issues:
- **Conversión** = issues cerradas por una PR fusionada / issues abiertas por el rol.
- **Ruido** = issues cerradas como duplicada o «no procede» / issues abiertas.
- Conversión < 25 %: se cambian el prompt o las entradas una vez. Segunda ventana < 25 %: el rol se retira.
- Ruido > 20 %: el rol se para hasta arreglar la firma de deduplicación.
- Sin consumidor (sección 2) la conversión no existe. Hasta que el reparador funcione, cada rol escribe **un comentario en una issue fija por rol**, no issues nuevas.

### 3.5 Juicio sobre la desviación de R3-14
- **La ingeniería es buena:** un workflow, rotación y modelo sin herramientas.
- **La secuencia no:** R3-14 pedía un solo rol para aprender el mecanismo antes de multiplicarlo. Siete roles sin consumidor y sin métrica son siete fuentes de ruido.
- **Decisión:** se conserva el workflow único y se encienden los roles de uno en uno. Primero los que tienen una herramienta determinista detrás (rendimiento y SEO con SiteOne). Apagados hasta que `datos_rol` les dé lo que su prompt promete: UX y arquitecto. El siguiente rol se enciende cuando el anterior supera el 25 %.

## 4. Pregunta 3 — Clases de fallo abiertas en la carga nocturna

| Clase | Dónde (leído en main) | Qué pasa | Test que la fija | Prio |
|---|---|---|---|---|
| F1. El estado de la noche se deduce, no se registra | `juez:77-78` («hoy» = 00:00 UTC, 50 ejecuciones sin paginar); `sync.yml:165-170` («hoy» = medianoche de Madrid, `--limit 30`); `sync.yml:62` (la cadena y el reintento saltan el juez) | Dos definiciones de «esta noche». Una ejecución creada entre las 23:00 y las 00:00 UTC cuenta para el reintento y no para el juez. Las listas se truncan en noches largas | Noche simulada de 60 ejecuciones que cruza las dos medianoches: juez, cadena y reintento dan la misma respuesta leyendo un solo libro de la noche | P0 |
| F2. Carga que publica y aun así acaba en rojo | `refresh:234-262` y `refresh:272-275` (`raise` aplazado); `sync.yml:159` (`failure()` no cubre el corte por tiempo); `juez:51` (sí trata `timed_out` y `cancelled`) | Un fallo de Amazon o del mercado tras publicar marca la ejecución como fallida, lanza el reintento ciego y el juez la cuenta como noche perdida. Juez y reintento no coinciden en qué es fallar | Excepción inyectada en mercado ⇒ código 0, informe con `degradado: [mercado]`, issue `fallo` y la cadena sigue | P0 |
| F3. Muerte entre dos pasos que no son atómicos | `publish:346` y `publish:359-364` (fusiona y luego despacha Pages); `refresh:270` (`estado.guardar` antes de `assemble`); `refresh:516-519` (cierra la PR vieja antes de crear la nueva); `refresh:146-148` (`check=False`); `refresh:219-222` | Si la ejecución muere tras fusionar, nadie despliega. Si `carry` choca, los datos se descartan con el mensaje «ya está en main o choca con él»: pérdida silenciosa | Puntos de muerte: abortar tras cada paso k y relanzar ⇒ estado final igual al de una ejecución sin cortes. Un paso inicial «reconciliar» (¿main desplegado?, ¿PR huérfanas?, ¿checkpoints?) hace el trabajo. Regla: crear antes de destruir | P0 |
| F4. Fallo abierto que destruye | `cuarentena:53-58` (`committed` devuelve `None` ante cualquier error) | Con `previous=None` todo libro cuenta como nuevo: el tope crece al catálogo entero y los libros publicados se borran en vez de volver a su versión buena | `git show` que falla ⇒ la cuarentena aborta; ningún libro publicado desaparece | P0 |
| F5. Diagnóstico por texto | `cuarentena:38-42`, `cuarentena:118`, `cuarentena:151-167` | Decisión D3 | Propiedad de renombrado de D3 | P0 |
| F6. La lista de checks se copia a mano del ruleset | `publish:44-57`; `publish:60-65` | Si el ruleset cambia, la PR no fusiona nunca o un check requerido figura en verde sin haber corrido | A corto plazo, contrato que compara `REQUIRED_JOBS` con el ruleset por API. A fondo, R4-8: la carga abre su PR con la App y esta maquinaria se borra | P1 |
| F7. Escrituras a GitHub sin reintento | `publish:99-113` (solo reintenta lecturas y `pr create`) | Un 5xx en `workflow run`, `pr merge`, `rerun` o un status tumba una carga de 75 min | `gh` falso que devuelve 502 una vez en cada escritura ⇒ la carga termina. Antes de repetir una escritura se comprueba si ya ocurrió | P1 |
| F8. Varios pendientes exigen una persona | `refresh:200-201` («Hay varias cargas pendientes»); `refresh:217-227` (un checkpoint por ejecución); `sync.yml:149` (la cadena exige `accepted > 0`) | Dos PR abiertas paran la carga hasta que alguien cierra una. Varios checkpoints necesitan varias noches, porque una carga recuperada no encadena | Tres checkpoints y dos PR abiertas ⇒ converge en N ejecuciones sin intervención (se queda la PR más nueva y se traslada el resto) | P1 |
| F9. Constantes que eran verdad con N libros | `publish:158-170` (`--limit 20`, solo `in_progress`, no ve `queued`); `publish:322` (jobs sin paginar); `refresh:197` (`--limit 100`); `publish:141-155` y `publish:183-191` (`compare` topa en 300 ficheros) | Con una PR de 8.103 ficheros (leído: `revision-carga-nocturna-2026-11-14.md:70`) `compare` trunca siempre: «main cambió» es la respuesta permanente y se regenera cada vez | Guarda: toda llamada a `gh` con `--limit` o `per_page` pasa por un ayudante que pagina o falla si llega al tope. Ensayo de escala (P0-5) | P1 |
| F10. Carreras con otros escritores de main | `sync.yml:124-133` (2 intentos ante el código 75); `refresh:67-85` (si `follow_main` choca, la PR sale de la base antigua) | Un tercer movimiento de main durante la CI tumba la carga. Cada commit de bot en la ventana cuesta un ciclo | Simulación con main moviéndose tres veces. Solución: ningún bot escribe en main durante la ventana de la carga (el libro de la noche hace de semáforo), y R4-9 reduce el ciclo | P1 |
| F11. Cuarentena sin salida y de coste creciente | `cuarentena:83-148` (revalida todo el catálogo por cada libro apartado); `refresh:489-504` (un build completo por ronda, sin tope); `cuarentena:292-312` (sin caducidad ni tope de `intentos`) | Coste = apartados × N. Un libro puede quedar apartado para siempre sin que nadie lo vea | Propiedad: el número de validaciones completas no crece con los apartados (validar solo lo afectado). Libro con `intentos > 3` ⇒ una issue, una vez | P2 |
| F12. El PC como pieza del sistema | § 0bis del 15/11 (tarea colgada, PT72H e `IgnoreNew`) | Decisión D2 | Con el PC apagado 48 h, la carga y el ciclo de arreglo siguen | P1 |

Nota sobre F4: el fallo abierto del juez (`juez:104-110`, sin API se carga) es deliberado y correcto. El de la cuarentena no lo es, porque su lado «abierto» borra.

## 5. Pregunta 4 — Escala a 60.000 fichas

Orden en que se rompe, de primero a último.

### 5.1 Git como transporte del HTML generado (ya está al límite)
- Con 4.031 libros una carga fue una PR de 8.103 ficheros (leído: `revision-carga-nocturna-2026-11-14.md:70`). A 10× son unos 100.000 ficheros por PR. `compare` ya trunca en 300 (F9).
- La CI ya ejecuta `materializar` antes de probar (leído: `fable-direccion-2026-11-15.md:34`), así que el HTML versionado es redundante.
- **Arquitectura.** Main guarda datos, plantillas y código. El HTML se construye en `deploy-pages.yml` y en la CI. La PR de la carga solo lleva datos.
- **Lo que desaparece con esto:** los renombrados `a -> b` y el `pathspec` de borrados (14/11), el coste de F9 y F10, los conflictos de `follow_main` sobre HTML y D1 queda gratis.
- **Los datos también se parten.** `data/reading-catalogue.json` y `data/content-registry.json` se reescriben enteros (leído: `build:1640-1648`). A 60.000 libros son ficheros de decenas de MB con conflicto en cada escritura (sin verificar su tamaño actual; el límite de GitHub por fichero es 100 MB, de memoria). Destino: un fichero por tramo, por ejemplo por prefijo de ISBN o por mes de publicación.

### 5.2 Tiempo del ciclo de la carga
- Hoy: 75 min por ciclo de CI y límite del job en 240 min (leído: `sync.yml:75-77`). La QA offline pasó de 15 a 45 min con 4.946 libros (leído: `revision-carga-nocturna-2026-11-14.md:152`). El máximo de un job en GitHub es 6 h (de memoria).
- **Arquitectura.** Validación incremental: solo los libros cambiados más invariantes globales lineales. QA de navegador por muestra estratificada con semilla. Contratos lineales por id, en la línea de #1340.

### 5.3 Tamaño y peso en Pages
- Cada página del catálogo pesa 554 kB sin comprimir (leído: `fable-direccion-2026-11-15.md:45`) y hay una cada 96 libros (leído: `build:1126`). A 60.000 libros son 625 páginas y unos 346 MB solo de listados, antes de contar 60.000 fichas.
- El límite de un sitio de Pages es 1 GB y el despliegue tiene 10 min (de memoria, sin verificar). El tamaño actual del artefacto no lo medí: encargo E2.
- **Arquitectura.** Tarjetas ligeras en los listados y los datos de filtro fuera del HTML (P1-4).

### 5.4 Filtros en el cliente
- El primer filtrado baja todas las páginas: 2,8 MB y 58 peticiones con 5.000 libros (leído: `fable-direccion-2026-11-15.md:45`). A 10× son unos 28 MB y 625 peticiones. No es viable en móvil.
- Un índice único (P1-4 tal como está escrito) tampoco escala: 60.000 entradas son varios MB.
- **Decisión.** P1-4 se diseña troceado desde el principio: recuentos de facetas precalculados y listas de resultados por faceta en ficheros paginados. El cliente solo cruza los trozos que el usuario pide.
- **Idea que ya conozco, para probar tras el interruptor:** Pagefind ya está en el proyecto (leído: `package.json:11`) y tiene filtros y orden sobre un índice troceado. Puede ser el motor global a escala, con el motor actual como oráculo de paridad. Sin verificar a este tamaño: encargo E3.

### 5.5 Sitemap
- `render_xml` genera un solo `<urlset>` (leído: `build-sitemap.py:253`; no hay `sitemapindex` en el fichero). El protocolo admite 50.000 URL y 50 MB por fichero (de memoria). Con 60.000 fichas más autores, sellos y páginas, se supera.
- `collect_urls` abre cada HTML para leer canonical y fecha (leído: `build-sitemap.py:221`).
- **Arquitectura.** Índice de sitemaps partido por tipo y por mes, generado desde el índice del catálogo y no releyendo HTML.

### 5.6 Build: puntos cuadráticos
Leído en main; #1341 («build lineal») sigue abierta y puede cubrir parte.
- `render_hub` se llama una vez por página y en cada llamada reordena todos los libros y calcula el hash del catálogo entero (`build:1142-1159`, `build:1614-1616`).
- `render_book` recalcula la lista de publicados tres veces por ficha (`build:1226`, `build:1230`, `build:1242`), y `book_title` recorre todos los libros (`build:556-563`).
- `related_books` recorre todos los candidatos por ficha (`build:1305-1332`).
- Autores y sellos: `any(... for b in books)` por cada uno (`build:1360`, `build:1466`, `build:1622`, `build:1627`).
- `render_outputs` guarda todas las salidas en memoria antes de escribir (`build:1606-1649`).
- **Arquitectura.** Un objeto `Catalogo` construido una vez (publicados, por id, por autor, por sello, órdenes y hash) que reciben todos los renderizadores. Render incremental con clave = hash del registro + versión de plantilla + vecinos. Escritura en flujo.
- **Test.** Contador de operaciones con 1.000 y 2.000 libros sintéticos: la razón debe quedar por debajo de 2,5. No depende del reloj.

### 5.7 Ficheros únicos que crecen sin tope
`render_map` (un HTML con todos los enlaces, `build:1592-1601`), `render_llms_index` (`build:952-964`), y `orphans` para el build por una sola ficha sin dato (`build:1634-1639`). Se paginan igual que el catálogo; `orphans` pasa a cuarentena en vez de parar.

## 6. Pregunta 5 — Lo que Opus hace mal de forma sistemática

| Patrón | Evidencia (leído) | Comprobación automática que lo evita |
|---|---|---|
| O1. Arregla el caso y relanza; aparece el siguiente | Madrugada del 15/11: corte a 15 min, luego `pagina=99`, luego orden de filtros; cada uno costó una carga de 997 altas (`revision-carga-nocturna-2026-11-14.md:152-156`) | Tras un fallo de la carga no se relanza hasta que la QA **completa** pasa sobre la rama de datos que falló (`workflow_dispatch` de la QA sobre esa rama). Todos los pasos corren aunque falle uno |
| O2. El arreglo pierde la carrera contra la cadena | Tres veces la misma noche: la PR de la carga se abrió antes de que entrara el arreglo (`…:153-156`) | Mientras hay un arreglo en vuelo se pausa la cadena con la variable que ya existe, `READING_INTAKE_ENABLED` (`sync.yml:68`), y se reactiva al fusionar |
| O3. Tests que no ejercen lo real | Los tests de #1311 simulaban git y no vieron el `pathspec` (`…:33-34`); el test de #1380 compara cadenas del YAML; 62/62 en local y rojo en Actions por PyYAML (`fable-direccion-2026-11-15.md:32`) | Job para las PR de arreglo: se ejecutan los tests nuevos sobre el commit base y **deben fallar**. Si pasan en la base, no prueban el arreglo |
| O4. Fusiona sin leer a los revisores | #1314 con 8 hallazgos de CodeRabbit sin leer (`…:100`) | El portero de 2.2, para todas las PR |
| O5. Varias variables a la vez | El cupo pasó de 200 a 1.000 la misma noche que entraban #1325 y #1326, y hubo cuatro cargas fallidas (`…:118`, `…:145-156`) | Un cambio de cupo o de límite exige un ensayo de escala en verde con ese tamaño y va solo esa noche |
| O6. Constantes ajustadas al catálogo de hoy | 15 min, página 99 (`…:152-153`) | Ensayo de escala en cada PR que toque `qa/` o el build (P0-5) y guarda contra literales de tamaño en `qa/` |
| O7. `[x]` significa «programado», no «verificado» | R3-13 «sin push», R3-15 «PR tras #1341», R3-16 «en la cola», todas con `[x]` (`fable-direccion-2026-11-16.md:309-315`) | Tres marcas: `[c]` programado, `[m]` fusionado, `[x]` criterio de hecho comprobado. Un script exige en cada `[m]` y `[x]` un número de PR con estado fusionado |
| O8. Demasiado trabajo abierto para una cola en serie | 13 PR abiertas a 75 min de CI cada una (medido en el tramo anterior de esta sesión con `gh pr list`) | Tope de 3 PR de código abiertas; con más, solo se abren P0. Agrupar por clase de fallo |
| O9. `except` amplio y `check=False` como estilo | `cuarentena:53-58`, `cuarentena:196-202`, `cuarentena:282-289`, `refresh:146-148`, `_gh` en #1373 | Ruff `BLE001` y `PLW1510` en la puerta con línea base: no se admiten nuevos |
| O10. Local distinto de la CI | Dependencias solo en el PC, generados sin regenerar, falsos fallos de Windows (`…:74`, `…:104-106`; `fable-direccion-2026-11-15.md:55`) | Ya ordenado en P0-1 y P0-3. Sin verificar si están en main |
| O11. El encargo describe un sistema que no es el del código | El prompt r4 dice Sonnet con `--max-turns`; el diff usa GitHub Models | El contexto del prompt se genera desde `gh pr view --json files` y la cabecera del diff, no de memoria |
| O12. Se salta reglas propias cuando hay prisa | Consulta a GPT en «Instant» (`fable-direccion-2026-11-15.md:197`); un byte `\x08` en una regex por una edición (`continuidad-2026-11-15-paginacion.md:25`) | `gpt-nuevo.mjs` rechaza el modo que no sea High; la puerta busca caracteres de control en el código |

Lo que Opus hace bien y debe seguir: documenta las desviaciones (P0-2, P0-6, R3-14) y separa «hecho» de «lanzado» en los informes.

## 7. Backlog R4 (en orden; criterio de «hecho» en cada uno)

**P0 — antes de tocar nada más de la carga**
- [ ] **R4-1. Libro de la noche.** `noche.json` en `catalogo-estado`: día (de Madrid), intentos con ejecución, SHA de código, clase, firma y resultado. Lo escribe solo el job `intake`. Lo leen el juez, la cadena, el reintento y el portero. Hecho: el test de F1 pasa y no queda ningún `gh run list` en esas decisiones.
- [ ] **R4-2. Fallos estructurados.** D3 y F5. Hecho: propiedad de renombrado en verde y guarda contra `re.` sobre mensajes en `cuarentena`.
- [ ] **R4-3. La cuarentena aborta si no puede leer la versión publicada.** F4. Hecho: test de F4.
- [ ] **R4-4. Día como parámetro del despliegue.** D1. Hecho: test `SALIDAS_DEL_DIA`; un despliegue con `hoy` distinto cambia solo esas salidas; con la carga desactivada una noche, el portal cambia de día.
- [ ] **R4-5. Resultado de la carga en tres estados** (publicado, degradado, fallido) y clasificación del fallo. D2 y F2. #1380 se fusiona con la guarda por firma. Hecho: test de F2 y test de la guarda con un libro de la noche de ejemplo.
- [ ] **R4-6. Reconciliar al empezar y crear antes de destruir.** F3. Hecho: tests de puntos de muerte; `carry` que choca deja el checkpoint y abre una issue, nunca descarta.

**P1 — el ciclo**
- [ ] **R4-7. GitHub App `web-escritor-reparador`** con los permisos de 2.1, fuera del bypass. Hecho: una PR de prueba abierta con su token dispara los 6 checks sin statuses manuales.
- [ ] **R4-8. `reparador.yml`** con los cuatro jobs de 2.2 y el bloque de máquina de 2.3. #1374 se cierra o se reduce a hombre muerto. Hecho: una issue `fallo` sembrada con una orden que falla acaba fusionada sin intervención; una issue con texto inyectado en el cuerpo no cambia el parche; una issue `experto` no entra.
- [ ] **R4-9. La carga abre su PR con la App** y se borran `WORKFLOWS`, `REQUIRED_JOBS` y `report_job` de `publish`. Depende de R4-7 y de excluir esa PR de los revisores. Hecho: una carga completa sin un solo status escrito a mano.
- [ ] **R4-10. Escrituras a GitHub con reintento y comprobación previa.** F7. Hecho: test de F7.
- [ ] **R4-11. Pendientes múltiples sin persona.** F8. Hecho: test de F8.
- [ ] **R4-12. Ayudante único de paginación para `gh`.** F9. Hecho: guarda en verde.
- [ ] **R4-13. Expertos: arreglos X1–X6, evidencia verificada, firma de deduplicación y encendido de uno en uno.** Sección 3. Hecho: tests de X1 y X3; un hallazgo con cita inventada se descarta; solo dos roles activos.
- [ ] **R4-14. Métrica de expertos** en el resumen semanal (3.4). Hecho: el resumen muestra conversión y ruido por rol.

**P1 — escala**
- [ ] **R4-15. HTML generado fuera de git.** 5.1. Empieza por una prueba de paridad: el artefacto construido en el despliegue es idéntico byte a byte al HTML versionado, tres noches seguidas. Después se retira el HTML de main. Hecho: la PR de una carga solo contiene datos.
- [ ] **R4-16. Objeto `Catalogo` y test de complejidad.** 5.6, sobre #1341. Hecho: test del contador con razón < 2,5.

**P2**
- [ ] **R4-17. Tres marcas de estado y su comprobación.** O7.
- [ ] **R4-18. Comprobaciones de proceso:** tests que fallan en la base (O3), tope de PR abiertas (O8), Ruff con línea base (O9), pausa de la cadena con arreglo en vuelo (O2).
- [ ] **R4-19. Índice de sitemaps partido.** 5.5. Hecho: test con 60.000 URL sintéticas, ningún fichero pasa de 50.000.
- [ ] **R4-20. Datos partidos por tramos.** 5.1. Después de R4-15.
- [ ] **R4-21. Cuarentena incremental con caducidad.** F11.
- [ ] **R4-22. I04 con `fechas_observadas`.** D4. Hecho: propiedad de permutación; ningún año-mes en listas diarias.

## 8. Encargos de investigación (Opus con GPT en High y búsqueda web; yo no abrí ninguna web)

- **E1.** `claude-code-action` con `claude_code_oauth_token`: ¿puede el modelo leer el token desde Bash o desde el entorno? ¿Qué opciones gratuitas hay para cortar la salida de red del job (por ejemplo `step-security/harden-runner` en repositorios públicos)? Buscar un repositorio público que separe «el modelo propone un parche» de «otro job lo publica» y reutilizar su workflow.
- **E2.** Medir el artefacto de Pages actual (tamaño y número de ficheros) y confirmar los límites vigentes de Pages. Si la proyección a 60.000 fichas pasa del límite, buscar alojamiento estático gratuito sin tope de ficheros que lo impida.
- **E3.** Pagefind con filtros y orden sobre 60.000 páginas: tamaño del índice, tiempo de indexado y sitios públicos que lo usen a ese tamaño.
- **E4.** Significado exacto de `publicationDate` y `releaseDate` en la Creators API, con la documentación delante.
- **E5.** ¿Reciben CodeRabbit y Codex las PR abiertas con `GITHUB_TOKEN` y con una App? Cómo excluir por autor o por rama la PR de la carga.
- **E6.** Quién figura hoy en la lista de bypass del ruleset y con qué identidad empuja `gpt_social_publish.py` (`gh api` sobre el ruleset; es una lectura, no una búsqueda).

## 9. Desacuerdos

- **Con el prompt r4:** describe los expertos como Claude Sonnet con herramientas. No lo son (3). Tres vías comparadas, pero la elegida es una cuarta: App como identidad y `claude-code-action` como motor sin token.
- **Con Opus:**
  - `turno_issues.py` local como consumidor de issues: depende del PC, resuelve él mismo los hilos de los bots y espera 20 min fijos. No se fusiona así.
  - #1380: la guarda «main avanzó» no distingue un arreglo de un commit de bot.
  - Siete roles a la vez (3.5).
  - Build diario parcial pasando por git (D1).
- **Con GPT:** la regla de los 7 días y guardar el ganador en vez de las observaciones (D4).
- **Con mi ronda 3:** P1-4 como índice único no escala a 10× (5.4). Y en la ronda 3 di por bueno el despliegue tras fusionar (`fable-direccion-2026-11-15.md:41`); no vi que una muerte entre la fusión y el despacho deja main sin desplegar (F3).

## 10. Lo que no hice y por qué

- **No medí nada** (build, tamaños, tiempos, tráfico): lo prohibía el prompt. Todo lo cuantitativo sale de informes anteriores o es proyección.
- **No abrí webs ni documentación.** Los límites de Pages, del sitemap, de los jobs y de los ficheros de GitHub, y los nombres de acciones, son de memoria: comprobar en E1–E5.
- **No leí** `scripts/night-autorepair.py`, `workers/intake-dispatch.mjs`, `scripts/empleados_expertos.py` en main (solo el volcado de #1373), el generador del índice de búsqueda, `build-sitemap.py` entero (solo dos búsquedas), ni `refresh:300-423`.
- **No leí** `gpt-auditoria-catalogo-2026-11-15.md`, `plan-catalogo-2026-11-15.md`, `gpt-empleados-fable-2026-11-15.md` ni `gpt-seo-catalogo-2026-11-16.md`: la pregunta 5 sale de los cuatro informes de Opus y de las dos entregas anteriores.
- **No comprobé** qué órdenes P0/R3 están ya en main (P0-1, P0-3, P0-5, #1341); donde importa lo marco.
- **No verifiqué** quién está en el bypass del ruleset (E6); de ello depende lo grave que es la vía (b).
- **No ejecuté ni escribí código, ni toqué PR, ramas o secretos.** El único cambio es este fichero, sin commit.

## 11. Continuidad

- **Fecha:** 16/11/2026. **Cambios:** solo este fichero (sin commit; la rama local `fix/portada-duplicada` va muy por detrás de main, así que conviene subirlo desde una rama creada sobre `origin/main`).
- **Verificaciones:** ninguna ejecución; lecturas sobre `origin/main` ac6ba54c9c y los volcados de #1373, #1374 y #1380.
- **Procesos:** no abrí ninguno.
- **Prompt para Opus (chat nuevo):**
  > Lee `.ci/fable-direccion-2026-11-17.md`. Ejecuta el backlog de la sección 7 en orden, empezando por R4-1 a R4-6, una PR por clase de fallo y con el test indicado fallando antes del arreglo. Lanza los encargos E1–E6 de la sección 8 con GPT en High y búsqueda web, y anota los resultados con su fuente en ese mismo fichero. No fusiones #1374 ni #1380 tal como están (secciones 2.4 y D2). Marca el estado con `[c]`, `[m]` y `[x]` y el número de PR.
