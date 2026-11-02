# Directorios: DISBOARD, Top.gg, Discadia y Telegram

Guía para dar a conocer el servidor «Club de lectura · David Porto» y los canales de Telegram. Lo hace David, porque añadir bots por OAuth y registrarse en cada web va con su cuenta. Tiempo: unos 30 min la primera vez y 1 min al día después.

Enlaces que se usan en todas partes:
- Discord: <https://discord.gg/g7dEWxj3F> (permanente, sin límite de usos).
- Telegram, todos los canales: <https://t.me/addlist/lja92v39DGE4YmM0> (carpeta «Libros DP»).
- Web: <https://davidportodiaz.com/comunidad/>.

## Textos comunes (copiar y pegar)

**Descripción corta (≤ 120 caracteres):**
> Club de lectura en español: novedades, ofertas y recomendaciones de libros por género, sin ruido. Tú eliges qué suena.

**Descripción larga:**
> Comunidad para lectores en español. Al entrar eliges tus géneros (thriller, romántica, fantasía, terror, ciencia ficción, histórica, infantil y juvenil, ensayo, cómic, poesía…) y solo ves esos canales.
>
> - Novedades, ofertas del día y próximos lanzamientos, publicados en silencio: solo te suena lo que tú marques con 🔔.
> - Pide recomendaciones en el foro o escribe `/libro busco: fantasía para 11 años` y el buscador te propone tres libros del catálogo.
> - Club de lectura con votaciones y quedadas.
> - Niveles por participar en la charla (sin spam de avisos).
>
> Sin publicidad de otros servidores ni autopromoción. Lo lleva el escritor David Porto.

**Etiquetas (por orden de prioridad):** `libros`, `lectura`, `club de lectura`, `español`, `literatura`, `fantasía`, `thriller`, `recomendaciones`, `book club`, `books`.

**Idioma:** español. **Categoría:** Comunidad / Libros y literatura (o «Education/Hobbies» si no existe).

## DISBOARD (el que más tráfico trae)

1. Entrar en <https://disboard.org> con la cuenta «David Porto» → Dashboard → «Add new server» → elegir el servidor.
2. Invitar al bot de DISBOARD con los permisos que propone (solo necesita ver y escribir en un canal).
3. Rellenar: descripción larga, idioma Español, etiquetas (DISBOARD admite hasta 5: `libros`, `lectura`, `club-de-lectura`, `espanol`, `literatura`), NSFW desactivado.
4. Canal para el bump: **#off-topic**. Darle al rol del bot permiso de escribir solo ahí (quitarle «Ver canal» en el resto si hace falta).
5. Rutina: escribir `/bump` en #off-topic **cada 2 horas** cuando se pueda; cada bump sube el servidor al principio de la lista de sus etiquetas. Con 2–3 bumps al día basta para empezar.
6. Opcional: invitar a moderadores o miembros activos a hacer bump (cualquiera puede hacerlo).

## Top.gg (servidores)

1. <https://top.gg> → iniciar sesión con Discord → «Add» → «Server» → elegir el servidor (no hace falta bot).
2. Descripción corta y larga (admite Markdown), etiquetas (`Books`, `Community`, `Spanish`, `Reading`, `Literature`), idioma Español, enlace de invitación permanente.
3. Banner: reutilizar el banner del servidor de Discord.
4. Los votos (uno cada 12 h por usuario) suben el puesto. Fijar en #anuncios, una vez, un mensaje discreto: «Si te gusta el club, puedes votarlo en Top.gg cada 12 h: <enlace>». Sin recompensas por votar (Top.gg lo prohíbe si son de pago).

## Discadia

1. <https://discadia.com> → iniciar sesión con Discord → «Add server».
2. Mismos textos y etiquetas. Elegir idioma Español y categoría Libros/Comunidad.
3. Bump desde la web (botón «Bump») cuando lo permita; la web indica cuánto falta para el siguiente. Con uno al día es suficiente.
4. Tiene bot opcional para bump desde Discord: no hace falta añadirlo.

## Descubrimiento de Discord (cuando el servidor crezca)

El servidor ya está en modo Comunidad. «Descubrimiento del servidor» (Ajustes → Descubrimiento) pide un mínimo de miembros y antigüedad que Discord fija; cuando lo cumpla, activarlo con la descripción corta, las mismas palabras clave y la categoría «Libros/Literatura». Es el escaparate con más tráfico y no requiere bumps.

## Telegram: configuración recomendada

Ya hecho: 17 canales con foto y descripción, carpeta «Libros DP», bot admin en todos (ver `docs/comunidades-plan.md` §10.1).

Lo que más ayuda ahora:
1. **Grupo de debate** vinculado a @novedades_libros_dp (§10.6 del plan): los comentarios de cada envío llevan al grupo, que es donde se crea comunidad. Temas con los mismos nombres que CHARLA en Discord.
2. **Buscador inline**: tras ejecutar `bots/deploy-community-bot.ps1`, `@DavidPortoLibrosBot terror` funciona en cualquier chat; es la forma más fácil de que otros compartan libros del catálogo.
3. **Directorios de canales:**
   - **TGStat** (<https://tgstat.com>): añadir los 10 canales públicos (`<tema>_libros_dp`) con «Añadir canal»; categoría Libros, idioma español. Para verificarlos pide publicar un código temporal en el canal o en su descripción: hacerlo en la descripción y quitarlo después.
   - **Telemetr** (<https://telemetr.io>): mismo proceso; útil para ver de dónde llegan suscriptores.
   - Los 7 canales privados (`t.me/+…`) no se listan en directorios: se llega a ellos por la carpeta.
4. **Enlaces cruzados:** en la descripción de cada canal de Telegram, una línea «Charla y recomendaciones: discord.gg/g7dEWxj3F»; en #bienvenida de Discord ya está el enlace a /comunidad/, que lleva a la carpeta de Telegram.
5. **Silencio:** mantener un único envío diario por canal y que solo Novedades notifique con sonido; es lo que más reduce las bajas.

## Qué no hacer

- No comprar miembros ni votos, ni usar servidores de «intercambio de anuncios»: DISBOARD y Top.gg lo penalizan y Discord puede cerrar el servidor.
- No hacer bump automático con self-bots (va contra las condiciones de Discord).
- No publicar el enlace en otros servidores sin permiso de su staff.
