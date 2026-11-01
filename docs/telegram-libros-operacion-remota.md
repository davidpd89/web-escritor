# Novedades de libros: operación remota

El canal se ejecuta en GitHub Actions. No depende del ordenador, del navegador ni de una sesión de Windows. Código y workflow forman parte de Web Escritor, integrados en main mediante la PR #1046. La antigua tarea `WEB_Libros_Telegram_Novedades` está deshabilitada y no debe volver a activarse en paralelo.

## Ciclo automático

`Reading Telegram publish` se activa a los minutos 7, 22, 37 y 52 de cada hora y después de una ejecución correcta de `Reading catalogue intake`. Usa runners Linux estándar alojados en GitHub. El cron puede retrasarse por la plataforma: la regla es publicar dentro del día de Madrid, sin prometer una hora exacta.

En cada ciclo:

1. Obtiene de main el catálogo y los perfiles editoriales actuales.
2. Revalida ISBN, título, autores y fecha en las fuentes editoriales conectadas. Un cambio de fecha se respeta y un producto ambiguo queda pendiente.
3. Obtiene el enlace de producto Amazon de la ficha editorial exacta y conserva la afiliación del proyecto. No convierte ISBN en ASIN ni usa búsquedas como productos comprobados.
4. Publica solo las ediciones cuya fecha coincide con hoy en Europe/Madrid y que no constan como enviadas a ese destino.
5. Envía portada editorial verificada, título, autor, fecha, hasta tres géneros y enlace Amazon. Ante un rechazo definitivo de la imagen puede enviar texto; ante una respuesta incierta no reintenta a ciegas.

No anuncia todos los libros de España: cubre lo incorporado a main desde las fuentes conectadas. No presenta libros atrasados como novedades de hoy ni usa una fecha de ingesta como fecha de lanzamiento.

## Credenciales y control

Los secretos de Actions son `READING_TELEGRAM_BOT_TOKEN`, `READING_TELEGRAM_CHANNELS_JSON` y `READING_TELEGRAM_STATE_KEY`. No están en el código o en el artefacto público. La configuración y los informes privados se crean en el directorio temporal de cada runner y no se suben como artifacts. Solo se cachean respuestas editoriales públicas.

La variable de repositorio `READING_TELEGRAM_ENABLED=true` habilita el servicio. Ponerla en false detiene futuros envíos remotos. No hay que iniciar ningún proceso local. Una ejecución que ya esté en marcha debe terminar o cancelarse antes de modificar su estado operativo.

La clave de estado es estable e independiente del token del bot. Renovar el token no debe reiniciar el historial. No rotar la clave de estado arbitrariamente: el servicio detecta que no coincide y bloquea el envío.

## Historial duradero y duplicados

La rama `automation/telegram-delivery-state` guarda `state.json`. Al ser un repositorio público, ese archivo también lo es, pero contiene exclusivamente identificadores HMAC irreversibles, un comprobante de la clave y estados. No contiene IDs de canales o mensajes, títulos, ASIN, propietarios, invitaciones, tokens o participantes. Esa rama no se publica como parte de la web.

Cada ejecución reconstruye su estado desde ese historial. Antes de enviar confirma `sending` remotamente; después confirma `sent`, rechazo o reintento. Si falla el guardado previo, no envía. Si el proceso cae después de publicar, el `sending` conservado impide un reenvío automático. Un historial inexistente, corrupto o inaccesible no se trata como un historial vacío.

Hay un único publicador remoto a la vez, más comparación del SHA del archivo para rechazar escrituras concurrentes. No se usa un cache o artifact efímero como memoria de publicaciones. Ante HTTP 429 se guarda el plazo `retry_after` y se espera a un ciclo posterior.

No borrar o reiniciar el historial para resolver un fallo. Para un registro `sending` o `uncertain`, comprobar primero el canal y el resultado real antes de corregir ese registro. Una vuelta al publicador local requiere restaurar antes el historial remoto; no basta con reactivar su tarea antigua.

## Prueba real y migración completada

El 1 de noviembre de 2026 se fusionó #1046 tras aprobar todos los checks requeridos, con 222 pruebas locales de lectura correctas. Se preservó el historial diario local al inicializar el remoto y se deshabilitó la tarea Windows durante el cambio.

- [Primer ciclo diario remoto correcto](https://github.com/davidpd89/web-escritor/actions/runs/41342820872): ejecutado por un runner de GitHub Actions, sin novedades del día en el catálogo conectado.
- [Publicación remota con portada](https://github.com/davidpd89/web-escritor/actions/runs/41342878248): ejemplo de «La casa de los espíritus», con fecha editorial real y etiqueta expresa de prueba.
- [Segunda ejecución independiente correcta](https://github.com/davidpd89/web-escritor/actions/runs/41342997947): recordó la entrega anterior y no la repitió. El historial remoto no cambió y se comprobó un único mensaje con la portada y el enlace esperados en Telegram.

La entrada manual `test_asin` sirve para reproducir ejemplos etiquetados, con un namespace de historial separado del diario. No cambiar fechas del catálogo para fingir un lanzamiento actual.

## Siguientes fases

La siguiente fase es una página propia de Telegram dentro de redes sociales, con acceso a los canales y enlaces desde los libros. Para sumar un canal de novedades por género, reutilizar el servicio y añadir su destino y filtros al secreto de configuración. Un mismo bot puede publicar en varios canales; crear bots adicionales no es necesario para separar temáticas.

Los fallos quedan reflejados en Actions y sus resúmenes agregados. Nuevas fuentes, más tipos de canal y alertas adicionales se incorporarán sobre esta base remota, sin volver a introducir dependencia del ordenador.
