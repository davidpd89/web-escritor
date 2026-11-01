# Telegram: base conectada a Web Escritor

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

El enlace se conserva exactamente desde el catálogo, incluido el tag real existente, y solo se admite una URL de producto Amazon.es reconocida por `reading_amazon_market.asin_from_url`. Una búsqueda por ISBN se deja pendiente; no se inventa ASIN ni se sustituye por un producto parecido. Los mensajes con tag muestran aviso de afiliación. No se consultan precios ni se usan imágenes de Amazon.

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

`--date` solo sirve para previews. Los envíos usan la fecha actual de Madrid. Si no hay novedades reales ese día, esperar a una fecha elegible o preparar un catálogo de prueba **separado** con `--catalog`; no alterar las fechas del catálogo editorial compartido. Repetir el comando con la misma base debe omitir lo ya enviado.

## Ejecución automática y estado

La web es estática: GitHub Pages no ejecuta el bot. Para la primera operación continua usar un proceso separado con `--watch`, supervisor y almacenamiento persistente. Relee catálogo/configuración cada cinco minutos. El operador debe actualizar el checkout desde main entre ciclos; el piloto no ejecuta pulls ni publica la ingesta por su cuenta. Usar rutas absolutas para catálogo, configuración y `--db`, y hacer copias de la base. `.local/` está ignorado y los scripts/datos operativos quedan fuera del artefacto público por su allowlist existente.

La base predeterminada es `.local/telegram/deliveries.db`. La clave es canal + ASIN. `sending` se confirma antes de HTTP; `sent` guarda message_id; `uncertain` y `rejected` quedan bloqueados para revisión. Antes de restablecer una fila, comprobar el canal: un timeout puede haber entregado el mensaje. No prometer exactamente una entrega ni borrar la base entre ejecuciones.

No programar envíos reales desde Actions con una base efímera o un caché como única memoria: podría perderse el estado y duplicarse la publicación. El workflow de esta PR es solo preview. No hay cron de envío activado, secretos añadidos ni despliegue realizado.

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
