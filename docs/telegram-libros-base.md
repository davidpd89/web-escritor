# Telegram: base conectada a Web Escritor

**Estado actual:** canal «Novedades de libros» y tarea local activos. Formato definitivo con portada verificada, título, autor, fecha, hasta tres géneros y enlace Amazon. Las comprobaciones de ejemplo se mantienen separadas de las entregas diarias; los apartados de la primera prueba conservan su contexto histórico.

## Orientación y relación con lo existente

Esta base pertenece a Web Escritor. Consume `data/reading-catalogue.json`, sus relaciones `libro_categorias`, `fecha_publicacion`, fuente editorial y `url_amazon_afiliada`. No crea un catálogo de producción alternativo ni modifica fichas públicas. Telegram enlaza directamente a Amazon, como ha solicitado el propietario; el recorrido Pinterest → web → Amazon permanece independiente.

La ingesta editorial existente (`reading-catalogue-sync.yml`, 06:30 UTC cuando esté habilitada) ya descubre y comprueba novedades de Penguin Libros España. No ofrece cobertura completa de España ni garantía de detectar todos los libros antes del día de lanzamiento: admite un número limitado por ciclo y la publicación pasa por PR y despliegue. Telegram solo conoce el catálogo incorporado al checkout. No usar la fecha de ingesta como fecha de lanzamiento.

De Bet (revisado en main, commit 4781a7901683396d9a26e31d87a86c81332c59dc) se aprovecha el patrón probado de envío HTTP de `sendMessage`, variables de entorno y texto HTML. Aquí se añade control de respuesta, registro persistente por canal y edición y zona horaria Europe/Madrid. Es una adaptación del patrón, no una afirmación de que el bot antiguo esté conectado a este proyecto.

No se trasladan: motores y modelos de apuestas, Betfair, claves de cuotas, bancos y liquidaciones, dashboards, caché de avisos en memoria, scheduler que silencia errores ni conversión fija UTC+2. Tampoco se copian tokens, IDs privados o `.env` de Bet a este repositorio público.

## Archivos y configuración

- `scripts/reading_telegram.py`: adaptación del catálogo, vista previa, envío y ciclo continuo.
- `data/reading-telegram.example.json`: dos destinos ficticios; el modo demo bloquea envíos reales.
- `scripts/requirements-telegram.txt`: dependencias exactas para el proceso separado.
- `tests/test_reading_telegram.py`: pruebas offline con unittest, como el resto del proyecto.
- `Reading Telegram preview`: workflow manual/de PR, sin secretos ni publicaciones.

Copiar el ejemplo a `.local/telegram/channels.json`. Poner los IDs reales del canal privado (cadena numérica o @usuario) y sus categorías; `[]` recibe todos los libros elegibles. Un bot puede servir varios canales; `token_env` permite bots distintos. Para enviar, establecer `demo: false` y mantener `enabled: true`; `enabled: false` detiene la ejecución. Configurar la variable `READING_TELEGRAM_BOT_TOKEN` en el entorno del proceso. No se carga `.env` automáticamente ni se guarda el token en JSON.

El enlace se conserva exactamente desde el catálogo, incluido el tag real existente, y solo se admite una URL de producto Amazon.es reconocida por `reading_amazon_market.asin_from_url`. Una búsqueda por ISBN se deja pendiente; no se inventa ASIN ni se sustituye por un producto parecido. Por indicación del propietario, se ha retirado el pie largo sobre comisiones. Las fichas muestran título, autor, fecha editorial, géneros y «Ver en Amazon», sin vista previa de Amazon. No se consultan precios ni se usan imágenes de Amazon.

## Pruebas reproducibles

Desde la raíz, con entorno Python propio (CI: Python 3.12):

```sh
python -m pip install -r scripts/requirements-telegram.txt
python -m unittest discover -s tests -p 'test_reading_telegram.py' -v
python scripts/reading_telegram.py --channels data/reading-telegram.example.json
python scripts/reading_telegram.py --channels data/reading-telegram.example.json --date 2009-06-01
```

El segundo preview permite inspeccionar Coraline y su enlace existente sin cambiar su fecha para fingir una novedad actual. En la fecha actual puede haber cero libros elegibles: es un resultado válido. Se informan cantidades elegibles/pendientes; no se publican candidatos incompletos. Las pruebas usan fixtures en memoria y no acceden a Telegram ni Amazon.

Para una prueba real, crear/elegir el bot con BotFather, añadirlo al canal privado con permiso de publicar, configurar el entorno y revisar primero el preview. Después:

```sh
python scripts/reading_telegram.py --channels .local/telegram/channels.json --send
python scripts/reading_telegram.py --channels .local/telegram/channels.json --send --watch
```

Para probar en cualquier fecha una edición revisada sin presentarla como novedad de hoy:

```sh
python scripts/reading_telegram.py --channels .local/telegram/channels.json --test-asin 8498382378
python scripts/reading_telegram.py --channels .local/telegram/channels.json --test-asin 8498382378 --send
```

`--test-asin` conserva la fecha editorial real y añade «PRUEBA · ficha de libro / No es una novedad de hoy». Usa `.local/telegram/smoke.db`, separada de las entregas diarias. No admite `--watch` ni `--date`. El catálogo demo continúa bloqueando envíos reales. Repetir esta prueba con la misma base omite la edición ya enviada; no borrar la base para comprobar duplicados.

`--date` solo sirve para previews. Los envíos usan la fecha actual de Madrid. Si no hay novedades reales ese día, esperar a una fecha elegible o preparar un catálogo de prueba **separado** con `--catalog`; no alterar las fechas del catálogo editorial compartido. Repetir el comando con la misma base debe omitir lo ya enviado.

## Ejecución automática y estado

La web es estática: GitHub Pages no ejecuta el bot. Para la primera operación continua usar un proceso separado con `--watch`, supervisor y almacenamiento persistente. Relee catálogo/configuración cada cinco minutos. El operador debe actualizar el checkout desde main entre ciclos; el piloto no ejecuta pulls ni publica la ingesta por su cuenta. Usar rutas absolutas para catálogo, configuración y `--db`, y hacer copias de la base. `.local/` está ignorado y los scripts/datos operativos quedan fuera del artefacto público por su allowlist existente.

La base predeterminada es `.local/telegram/deliveries.db`. La clave es canal + ASIN. `sending` se confirma antes de HTTP; `sent` guarda message_id; `uncertain` y `rejected` quedan bloqueados para revisión. Antes de restablecer una fila, comprobar el canal: un timeout puede haber entregado el mensaje. No prometer exactamente una entrega ni borrar la base entre ejecuciones.

No programar envíos reales desde Actions con una base efímera o un caché como única memoria: podría perderse el estado y duplicarse la publicación. El workflow de esta PR es solo preview. GitHub no tiene secretos de Telegram ni un cron de envío: la operación local se documenta más abajo.

## Próximas piezas, en este orden

### Página de acceso y enlaces internos

Decisión del propietario (1 de noviembre de 2026): una página propia de Telegram dentro de redes sociales, propuesta `/redes-sociales/telegram/`. Enlazarla desde `/redes-sociales/` y el apartado de libros/recomendaciones. Reservar la posibilidad de otras páginas como Discord, sin presentar comunidades aún inexistentes como disponibles. El texto promocional se definirá después de validar el canal.

Antes de publicar la página: disponer del enlace real del canal, probar unirse desde móvil y escritorio, explicar si es un canal de avisos o un grupo de conversación y comprobar las publicaciones. El bot publica; las personas se unen al canal, no necesitan abrir una conversación con el bot para recibir las publicaciones del canal. La URL y los enlaces se integrarán con los generadores de navegación, registro, sitemap y contratos existentes. Evitar una página pública vacía o botones ficticios mientras falta el destino.

### Orden de activación

1. Verificar la prueba privada con una edición y enlace reales; guardar el resultado sin credenciales.
2. Establecer alojamiento y estado duradero, actualizaciones de catálogo y un solo escritor por conjunto de canales.
3. Añadir reintentos acotados de rechazos seguros/429, alertas y resolución de estados inciertos. Hoy se espacian envíos un segundo, sin reintentos automáticos.
4. Definir recuperación de días perdidos y cambios de fecha: hoy solo selecciona el día actual y no edita mensajes antiguos.
5. Medir cobertura del calendario editorial y conectar más fuentes a la ingesta existente antes de ampliar canales.

La base permite probar selección y entrega; el servicio completo de novedades del día aún requiere validar estas piezas. Las condiciones de afiliación para los canales concretos se revisarán antes de activar su operación pública.

## Hallazgo de la revisión inicial (1 de noviembre de 2026)

En el catálogo revisado hay 161 entradas: solo una cumple todos los requisitos del piloto, Coraline, que tiene enlace de producto. Las otras 160 quedan pendientes según los requisitos combinados; muchas fichas usan búsquedas por ISBN. Por tanto, el catálogo automatizado actual no basta todavía para alimentar diariamente este canal con enlaces de producto. La siguiente tarea concreta es resolver destinos de edición verificados para las novedades, o definir expresamente otro formato que identifique las búsquedas como búsquedas. No se relajó esa validación para aparentar que la automatización ya está completa.

## Prueba real realizada (1 de noviembre de 2026)

Con autorización del propietario se creó `@DavidPortoLibrosBot` en BotFather y se conectó al canal privado «Libros · Pruebas David Porto». La API verificó el bot y su estado de administrador con permiso de publicar; sin permisos de editar/borrar mensajes ajenos o promover administradores. El token y la configuración del destino permanecen exclusivamente en `.local/telegram/`, ignorado por Git. No se incluyen credenciales ni enlace de invitación privado en esta documentación.

Se ejecutó `--test-asin 8498382378 --send`: estado `sent`, ficha de Coraline visible en Telegram Web, marcada como prueba con fecha editorial 2009-06-01. El enlace renderizado conserva `https://www.amazon.es/dp/8498382378?tag=davidporto-21`. La segunda ejecución devolvió `skipped:sent`; no apareció otro mensaje. La lectura del canal y el enlace se comprobaron mediante el Edge existente por CDP 9240, sin abrir otro perfil.

Esta prueba acredita entrega real e idempotencia tras una segunda ejecución. No acredita todavía descubrimiento diario completo, servidor permanente, entrega exactamente una vez ante fallos de red o publicación automática de todas las novedades. En aquella primera prueba no se activó un proceso continuo; la activación posterior se documenta más abajo.


## Canal de novedades: operación local activada

Configuración aprobada el 1 de noviembre de 2026. El canal se llama «Novedades de libros», sin la etiqueta de pruebas en nombre ni descripción. Sigue siendo privado con acceso por invitación, conserva su ID y suscriptores y no tiene grupo de discusión. Las firmas de administrador siguen desactivadas. El token y el enlace de invitación continúan fuera del repositorio.

`reading_telegram_worker.py` ejecuta un ciclo completo, sin navegador ni API de pago:

1. Lee el catálogo y configuración editorial actuales de main desde GitHub. No hace pull sobre el checkout ni sobrescribe trabajo ajeno. Si la descarga falla no publica desde un catálogo antiguo.
2. Revisa las ediciones desde tres días atrás hasta treinta días por delante. Reutiliza los parsers de Penguin, Planeta y fuentes genéricas revisadas; respeta robots, hosts, caché de una hora y presupuesto HTTP.
3. Comprueba ISBN, título y autores de la edición seleccionada. Usa la fecha editorial actual, de modo que un aplazamiento no se convierta en una falsa novedad de hoy.
4. Busca un único producto Amazon.es enlazado en esa ficha editorial. No visita Amazon, no deriva ASIN de ISBN, no acepta búsquedas ni escoge entre productos ambiguos. Compone el enlace con el tag existente configurado para el proyecto.
5. Guarda un snapshot privado, prepara el mensaje con los nombres de género del catálogo y publica únicamente si la fecha coincide con hoy en Europe/Madrid. No recupera días anteriores como novedades actuales.
6. Persiste las entregas SQLite y el informe `last-run.json`. Un libro sin verificación suficiente no bloquea los demás. Un fallo de entrega incierto no se reenvía automáticamente.

En la comprobación real se revisaron 21 ediciones: se resolvieron 20 productos, incluidos 13 lanzamientos de noviembre. Una edición antigua con enlace ambiguo quedó pendiente. Hoy no hubo libros del día en el catálogo conectado: el ciclo terminó correctamente sin publicar novedades. El primer lanzamiento próximo verificado es del 3 de noviembre de 2026. Estas cifras describen el catálogo conectado, no todos los libros publicados en España.

### Instalación y verificación

El instalador `scripts/install-reading-telegram-task.ps1` recibe `-PrivateRoot` y `-PythonExecutable`. Requiere `channels.json`, `bot-token.txt` privados y las dependencias de `scripts/requirements-telegram.txt` en ese Python. Usar `pythonw.exe` evita ventanas. Crea una copia congelada de los módulos en el runtime privado, sin actualizar silenciosamente código operativo desde una PR. Rechaza sobrescribir una tarea existente.

La tarea Windows `WEB_Libros_Telegram_Novedades` comprueba el catálogo cada quince minutos, con la cuenta actual sin elevación ni contraseña guardada. Evita instancias simultáneas y recupera una ejecución pendiente. El primer ciclo real se verificó con resultado 0 e informe `status=ok`, `live=true`, sin entregas pendientes para hoy.

Requiere este ordenador encendido, conectado y la sesión de Windows iniciada. No es un servidor remoto permanente. La ingesta editorial existente está habilitada mediante `READING_INTAKE_ENABLED=true`; Telegram consume lo incorporado a main. Si un libro todavía no ha llegado a main el día de salida no puede anunciarlo. Antes de ampliar la difusión debe medirse ese retraso y la cobertura de fuentes.

Estado privado: `last-run.json`, `editorial-verification.json`, `catalogue.json` y `deliveries.db` bajo PrivateRoot. Fallo global devuelve 1; novedades del día bloqueadas o entregas inciertas devuelven 2. Los pendientes de fechas distintas a hoy quedan en el informe sin convertir un ciclo vacío correcto en error. No hay alertas externas ni reintentos ciegos.

Para detener la operación: deshabilitar la tarea Windows o poner `enabled: false` en channels.json. Para actualizar el runtime: detener la tarea, revisar los cambios y reemplazar deliberadamente los módulos congelados antes de reactivarla. No borrar deliveries.db. Una futura instalación en servidor utilizará la misma selección y necesitará migrar el estado y el token por un canal privado.

## Formato definitivo y comprobaciones de portada

Una publicación es una foto con caption HTML: 📚 Novedad de hoy, título destacado, autor, 📅 fecha editorial, 🏷️ hasta tres géneros y enlace «Ver en Amazon». Se omiten géneros no declarados; no se inventan por el título. La clasificación procede del catálogo compartido. Se mantienen título, autor y fecha completos; no se añaden sinopsis, precios, estrellas o llamadas comerciales repetidas.

La foto usa exclusivamente una cubierta marcada como edición verificada y alojada bajo `/assets/reading-covers/` de la web. No se descargan imágenes de Amazon, no se generan cubiertas y no se permiten rutas arbitrarias. `sendPhoto` conserva foto y texto en una única entrega registrada. Si no hay cubierta verificada, se envía texto; si Telegram rechaza definitivamente la foto con HTTP 400, se intenta el texto una sola vez. Un timeout o respuesta ambigua no dispara un segundo mensaje, para evitar duplicados.

Ante HTTP 429, se persiste el instante indicado por `retry_after`: los ciclos siguientes esperan hasta entonces y solo después reintentan. Otros rechazos y entregas inciertas requieren revisión. No se reenvía una novedad en un día posterior por haber pasado el plazo.

Se enviaron dos ejemplos reales con cubiertas distintas, de Anagrama y Penguin: «Tres cuentos» y «Sin piedad (Harry Hole 14)». Se comprobaron visualmente en Telegram Web las dos fotos, la legibilidad del caption y los destinos Amazon; ambas entregas quedaron como `sent`. Se repitieron con la misma base de ejemplos y se omitieron sin duplicar. Están identificadas como pruebas y conservan sus fechas futuras reales; no entran en la base de publicaciones diarias. El formato automático diario usa «Novedad de hoy» únicamente cuando la fecha coincide.

La versión local definitiva se actualiza de forma controlada: se pausa la tarea, se respaldan sus módulos, se instala la versión revisada y se vuelve a verificar un ciclo real. El nombre y descripción ya no hablan de pruebas. El alojamiento continúa siendo este ordenador, no un servidor 24/7; esa limitación no desaparece por cerrar el formato editorial.

## Ejecución remota en GitHub Actions

El flujo `Reading Telegram publish` sustituye a la tarea Windows al completar la migración. No necesita Edge, una sesión de Windows o el ordenador del propietario. Se ejecuta en un runner de GitHub a los minutos 7, 22, 37 y 52 de cada hora y después de completar correctamente `Reading catalogue intake`. GitHub puede retrasar los cron; el criterio editorial sigue siendo el día de Madrid, no una hora exacta garantizada.

El código sigue en Web Escritor y el flujo solo ejecuta main. La variable `READING_TELEGRAM_ENABLED=true` habilita los envíos; false es el interruptor remoto. Los secretos son `READING_TELEGRAM_BOT_TOKEN`, `READING_TELEGRAM_CHANNELS_JSON` y `READING_TELEGRAM_STATE_KEY`. La clave de estado es independiente del token del bot para conservar el historial si se renueva este último; no se debe rotar arbitrariamente. La instalación inicial importa el historial diario local, no lo reinicia.

El historial persistente vive en la rama separada `automation/telegram-delivery-state`, sin archivos de la web. Es pública porque el repositorio lo es, pero contiene exclusivamente claves HMAC irreversibles y estados de entrega. No guarda canal, libro/ASIN, mensaje, token, propietario, enlace privado o lista de participantes. Un comprobante de la clave estable impide continuar con una clave equivocada. Los informes completos y la configuración solo existen en el directorio temporal del runner y no se suben como artifacts. El cache solo contiene respuestas editoriales públicas.

Antes de cada envío se confirma `sending` remotamente usando el SHA actual del archivo; si no se puede confirmar o hay conflicto, no se llama a Telegram. Después se confirma `sent`, rechazo o reintento. Si un runner cae tras enviar, el `sending` remoto impide que el siguiente publique de nuevo a ciegas. La exclusión de ejecuciones y la comparación del SHA evitan escritores simultáneos. Un historial inaccesible no se interpreta como vacío. No se usa un cache/artifact efímero como memoria de publicaciones.

`workflow_dispatch` admite `test_asin` para una prueba etiquetada, con un namespace HMAC independiente del diario. La puesta en marcha debe demostrar un envío desde el runner de GitHub, repetirlo desde otro runner y comprobar que se omite, además de verificar un ciclo diario. Solo entonces se deshabilita la tarea local para conservar un único publicador.

Las ejecuciones usan runners Linux estándar del repositorio público, como el resto de automatizaciones de la web; no se contrata un servidor ni un runner de pago. Las averías o novedades bloqueadas producen un fallo de Actions y su resumen operativo, sin imprimir datos privados. Recuperación de entregas inciertas y ampliación de cobertura editorial siguen siendo tareas de mantenimiento; no se recuperan libros atrasados presentándolos como novedades de hoy.
