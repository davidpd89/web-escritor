# Plan de comunidades lectoras (definición, 2 de noviembre de 2026)

Estado: **luz verde de David (2 nov, tarde): crear canales, servidor de Discord e imágenes.** Sin push ni workflows hasta que Actions esté libre.

## Correcciones de David (prevalecen sobre el resto del documento)

1. **Todos los géneros desde el lanzamiento.**
   - El catálogo se está llenando continuamente: el bot de ingesta añade novedades y fondo cada día.
   - El volumen medido hoy no limita qué canales se abren.
   - Poesía, Histórica, Religión, Terror, Ciencia ficción y Más votados se crean ya, cada uno con su canal. Se elimina la regla de «fase 2 por volumen».
2. **Horario de publicación fijo para no molestar** (hora de Madrid):
   - de lunes a viernes, a las **11:30**;
   - sábados y domingos, a las **18:30**.

   Cada canal recibe en esa franja lo que le toque ese día: una ficha por libro, en ráfaga corta y espaciada. Nada fuera de esa hora.
3. **Más votados con Goodreads.**
   - El catálogo ya guarda valoraciones de Goodreads (`assets/reading-market.json → ratings`, que hoy tiene 84 libros con puntuación y número de votos).
   - El canal publica un ranking con esos datos, que son los que ya se muestran en la web y enlazan a Goodreads.
4. **Un solo bot** (`@DavidPortoLibrosBot`) gestiona **muchos canales**.
   - Cada persona se suscribe solo a lo que quiere: solo Novedades («hoy sale X, mañana sale Y»), solo un género, etc.
   - Así no recibe mensajes de lo que no le interesa.
5. **Ofertas.** `reading-market.json → offers` ya existe como fuente de partida para el canal.

Complementa a `docs/comunidades-telegram-discord.md` (lo ya publicado en `/comunidad/`) y a `docs/telegram-libros-base.md` (el bot de Novedades que ya funciona).

---

## 0. Decisiones que propongo (resumen para aprobar)

| # | Decisión | Propuesta |
| --- | --- | --- |
| 1 | Plataformas | **Solo Telegram y Discord** en el lanzamiento. WhatsApp, RSS y boletín quedan para después (sección 5). |
| 2 | Tipo de grupo en Telegram | **Canales** (solo publica el bot), no grupos de chat. Un único grupo de charla opcional, vinculado como «comentarios». |
| 3 | Canales del lanzamiento | 3 «al día» + 7 por género (fusionando los de poco volumen). Los otros géneros, en fase 2 cuando haya libros suficientes. |
| 4 | Canal nuevo «Todos los libros» | Sí: recibe **cada libro** que entra en el catálogo. Es el canal «llévatelo todo». |
| 5 | Bots | **Un bot publicador** para todos los canales (los suscriptores no ven el bot; ver 2.1). Bots separados solo si hace falta aislar un canal. Fase 2: un bot conserje para elegir canales desde un menú. |
| 6 | Unirse | Enlace de **carpeta de Telegram** (`t.me/addlist/…`): un toque y cada persona marca los canales que quiere. Además, botón por canal y código QR. |
| 7 | Discord | Servidor en modo Comunidad, con Onboarding para elegir géneros, AutoMod nativo y webhooks. Sin bots de terceros en el lanzamiento. |
| 8 | SEO | La página `/comunidad/` apunta a «grupos/canales de Telegram de libros». Los canales públicos con `@usuario` son indexables (`t.me/s/…`). Alta en directorios. |
| 9 | Imágenes | Un sistema visual común: color por canal, palabra grande e icono, y `davidportodiaz.com` pequeño. Un prompt por canal (sección 8). |

---

## 1. Grupos: definición completa

### 1.1 Volumen real del catálogo (medido hoy)

- El catálogo tiene 181 libros. Unos 120 tienen fecha de publicación en octubre de 2026, así que el ritmo actual es de **≈100–120 libros al mes**.
- Libros por género (`libro_categorias`):

| Género (slug) | Libros | Lectura |
| --- | ---: | --- |
| fantasia + juvenil/oscura/romantasy | 21 | suficiente |
| misterio-y-thriller + novela negra | 18 | suficiente |
| desarrollo-personal | 17 | suficiente (no tenía canal) |
| infantil + juvenil | 40 | suficiente |
| cocina + nutrición | 24 | suficiente |
| romance + amor y pareja | 26 | suficiente |
| biografías y memorias | 14 | suficiente (no tenía canal) |
| cómic y novela gráfica | 13 | justo |
| ensayo + filosofía + divulgación | 13 | justo |
| poesía | 8 | bajo |
| novela histórica + historia | 8 | bajo |
| terror | 6 | bajo |
| ciencia ficción | 3 | muy bajo |
| religión y espiritualidad | 2 | muy bajo |

**Conclusión:** un canal con menos de un mensaje a la semana parece abandonado y la gente se va. Por eso:
- en el lanzamiento se abren los canales con volumen;
- los de poco volumen se fusionan (fantasía + ciencia ficción; terror dentro de thriller);
- o se aplazan a la fase 2. Abrirlos cuando la ingesta añada más editoriales: Planeta ya está conectada parcialmente.

### 1.2 Canales de Telegram

Las propuestas de `@usuario` están por confirmar: hay que comprobar en Telegram que estén libres. Todas siguen el mismo patrón, `@<tema>_libros_dp`, o la variante más corta si está libre.

**Para estar al día** (sección `al-dia`)

| id | Nombre visible | @usuario propuesto | Qué publica | Ritmo | Fase |
| --- | --- | --- | --- | --- | --- |
| `todos` | Todos los libros | `@todos_libros_dp` | Cada libro que entra en el catálogo, con su género. | 3–5/día | 1 |
| `novedades` | Novedades de libros | `@novedades_libros_dp` (hoy es privado) | Solo los libros que salen **hoy** a la venta. | 0–10/día | 1 (**ya activo**) |
| `ofertas-hoy` | Ofertas de libros hoy | `@ofertas_libros_dp` | Bajadas reales de precio en Amazon.es (antes → ahora), un resumen al día. | 1/día | 1b (necesita el comparador de precios) |
| `mas-votados` | Los más votados | `@masvotados_libros_dp` | Ranking semanal de libros mejor valorados. | 1/semana | 2 (necesita una fuente con licencia) |
| `proximos` | Próximos lanzamientos | `@proximos_libros_dp` | Resumen semanal de lo que sale en los próximos 7 días. Ya existe `proximos-lanzamientos.ics`. | 1/semana | 1 (opcional) |

**Por género** (sección `temas`)

| id | Nombre visible | Categorías del catálogo | Fase |
| --- | --- | --- | --- |
| `thriller` | Thriller, misterio y terror | misterio-y-thriller, misterio, tema-novela-negra, terror | 1 |
| `fantasia` | Fantasía y ciencia ficción | fantasia, fantasia-juvenil, fantasia-oscura, romantasy, ciencia-ficcion, mundos-paralelos | 1 |
| `romantica` | Novela romántica | romance, tema-amor-y-pareja | 1 |
| `infantil-juvenil` | Infantil y juvenil | infantil, juvenil, edad-* | 1 |
| `cocina` | Cocina y bienestar | cocina, nutricion-y-bienestar | 1 |
| `no-ficcion` | Ensayo, biografías y desarrollo personal | ensayo, filosofia, divulgacion-cientifica, biografias-y-memorias, desarrollo-personal | 1 (sustituye a `ensayo`) |
| `comic` | Cómic y novela gráfica | comic-y-novela-grafica | 1 |
| `historica` | Novela histórica | novela-historica, historia, epoca-* | 2 |
| `poesia` | Poesía | poesia | 2 |
| `religion` | Religión y espiritualidad | tema-religion-y-espiritualidad | 2 |
| `terror` | Terror (canal propio) | terror | 2, si se separa de thriller |
| `ciencia-ficcion` | Ciencia ficción (canal propio) | ciencia-ficcion | 2, si se separa de fantasía |

**Regla de fase 2:** se abre un canal cuando la previsión llega a **≥ 4 libros al mes** durante dos meses seguidos. Lo mide un script de informe, no una persona a ojo.

**Cambio en `data/communities.json`** (al implementar):
- añadir `todos`, `proximos` y `no-ficcion`;
- fusionar las categorías en `thriller` y `fantasia`;
- añadir el campo `phase` (1/2);
- la página muestra la fase 2 como «Próximamente».

### 1.3 Formato de los mensajes (igual en todos los canales)

- **Ficha de libro:** se reutiliza el formato definitivo del bot de Novedades: foto de cubierta verificada, título, autor, fecha, hasta 3 géneros y «Ver en Amazon».
- Se añade una línea fija: «Más canales: davidportodiaz.com/comunidad». Es lo que hace que cada mensaje reenviado traiga gente nueva.
- **Etiqueta según el canal:**
  - 📚 Novedad de hoy (en Novedades);
  - 🆕 Nuevo en el catálogo (en Todos);
  - 💸 Oferta (en Ofertas).
- **Ofertas:**
  - solo bajadas reales, con precio anterior y actual;
  - sin imagen de Amazon;
  - sin repetir el mismo libro en 7 días;
  - fecha de comprobación visible, porque los precios cambian.
- **Resúmenes semanales** (Próximos y Más votados): un único mensaje con una lista enlazada, no 20 mensajes.
- **Mensaje fijado** en cada canal: qué publica, cada cuánto, enlace a los demás canales y aviso de afiliación («Los enlaces a Amazon son de afiliado»).

---

## 2. Bots

### 2.1 Un bot o muchos: análisis

En un **canal** de Telegram los mensajes aparecen firmados por el canal, no por el bot. El suscriptor no ve cuántos bots hay detrás. Por eso «muchos bots» no mejora nada visible y multiplica tokens, secretos y puntos de fallo.

| | Un bot para todos los canales | Un bot por canal |
| --- | --- | --- |
| Lo que ve el lector | Igual | Igual |
| Secretos que guardar | 1 token | 15+ tokens |
| Límites de Telegram (≈20 mensajes/min por chat, ≈30/s globales) | Sobra con un margen enorme para ~100 mensajes al día | No aporta nada |
| Si un token se filtra | Afecta a todos (se regenera en BotFather en 1 minuto) | Solo afecta a un canal |
| Mantenimiento | 1 configuración | 15+ altas en BotFather y permisos |

**Recomendación:**
- **Un bot publicador**, el `@DavidPortoLibrosBot` que ya existe, como administrador con solo «Publicar mensajes» en todos los canales.
- El código ya admite `token_env` por canal. Si en algún momento se quiere aislar un canal (por ejemplo, Ofertas), se le da su bot sin tocar nada más.

**Lo que sí se parece a «muchos bots» y aporta valor** (fase 2):
- **Bot conserje** (`@DavidPortoLibrosBot` en privado). La persona escribe `/start` y recibe botones con todos los canales para unirse, más la carpeta «unirme a todos».
- También `/genero fantasia`, que devuelve el enlace del canal.
- Requiere responder a mensajes, o sea un webhook siempre disponible. GitHub Pages no lo permite; un Cloudflare Worker gratuito sí. Se decide al implementarlo.

### 2.2 Qué publica cada canal y de dónde sale

| Canal | Selección | Fuente | Estado de la fuente |
| --- | --- | --- | --- |
| Todos | Cada libro nuevo en `reading-catalogue.json` (primera vez que aparece) | Catálogo en main | Listo; falta el modo «nuevo en catálogo» en el worker |
| Novedades | `fecha_publicacion == hoy` (Madrid) | Catálogo + verificación editorial | **Funcionando** |
| Por género | Nuevo en catálogo **y** con alguna categoría del filtro | Catálogo | Listo; mismo modo que Todos más el filtro `categories`, que ya existe |
| Próximos | `fecha_publicacion` en los próximos 7 días, los lunes | Catálogo / `.ics` | Fácil |
| Ofertas | Precio actual < precio anterior (umbral ≥ 10 % o ≥ 1 €) | `precios_amazon_revision` + Creators API | Falta el histórico de precios y respetar la caché de 24 h |
| Más votados | Ranking semanal | Fuente con licencia (no se raspa Goodreads) | **Bloqueado**: Goodreads no tiene API pública desde 2020. Alternativas: reseñas propias de la web (`resenas`), Open Library ratings (CC0) o votación de la comunidad en Discord |

**Propuesta para Más votados sin Goodreads:** «Los más votados por la comunidad».
- Hay una votación semanal en Discord y en el grupo de comentarios.
- Se combina con las valoraciones de Open Library cuando las haya.
- Es honesto, no viola licencias y genera conversación. Si David quiere Goodreads explícitamente, solo se puede hacer con enlaces («ver en Goodreads»), sin cifras.

### 2.3 Operación

- Se usa el mismo workflow `Reading Telegram publish`.
  - Una sola ejecución recorre todos los canales.
  - El estado de entregas por canal y libro ya existe (claves HMAC).
  - No hacen falta workflows nuevos para los canales por género, solo ampliar `READING_TELEGRAM_CHANNELS_JSON`.
- **Ofertas** necesita su propio paso: comparar precios una vez al día. Se integra en el workflow de tarifas existente, no en uno nuevo.
- **Discord:** el mismo ciclo envía un `POST` al webhook del canal equivalente. Las URL de webhook van en un secreto `READING_DISCORD_WEBHOOKS_JSON`.
- **Arranque de un canal nuevo:** no se vuelca el histórico de 181 libros. Se publica desde el día de alta, más un mensaje de bienvenida con los 5 mejores del género.

---

## 3. Unirse: atractivo, claro y fácil

1. **Carpeta de Telegram (`t.me/addlist/…`).**
   - Telegram permite compartir una carpeta con hasta 100 canales.
   - Al abrirla, la persona ve la lista con casillas, desmarca lo que no quiere y se une a todo con un botón.
   - Es justo lo que se pide: «cada uno se apunta a lo que quiera».
   - Botón principal de `/comunidad/`: «Elegir mis canales de Telegram».
   - El validador debe aceptar `t.me/addlist/`.
2. **Botón por canal** en cada tarjeta («Unirme»), solo cuando hay enlace, como ahora.
3. **Código QR** en escritorio, para abrir en el móvil, generado en el build como SVG estático y sin servicios externos. Oculto en móvil.
4. **Vista previa:**
   - en cada tarjeta, «Último libro publicado» (título y cubierta) obtenido del catálogo en el build;
   - prueba de que el canal está vivo, sin *widgets* de Telegram ni cookies.
5. **Texto «Cómo funciona» en 3 pasos:**
   - 1) Elige tus géneros.
   - 2) Únete con un toque, sin dar tu número a nadie.
   - 3) Silencia o sal cuando quieras.
6. **Confianza:**
   - «Gratis, sin spam: máximo X mensajes al día por canal»;
   - «Nadie ve que estás suscrito»;
   - «Los enlaces a Amazon son de afiliado».
7. **Contador de suscriptores**, solo cuando supere 100. Se muestra un número redondeado («más de 300 lectores») leído con `getChatMemberCount` en el build. Si no, no se muestra.
8. **Tarjetas con la imagen del canal** (sección 8): la misma que el avatar de Telegram, para que se reconozca al llegar.

---

## 4. Discord: creación y configuración completa

### 4.1 Creación (paso a paso, lo hace David con su cuenta)

1. Crear el servidor: Crear un servidor → Para mí y mis amigos (luego se convierte). Nombre: **«Club de lectura · David Porto»**. Icono: imagen genérica (8.9).
2. **Activar la autenticación en dos pasos** en la cuenta del propietario. Es obligatoria para moderar con 2FA.
3. Ajustes del servidor → **Habilitar Comunidad**. Pide:
   - nivel de verificación;
   - filtro de contenido explícito;
   - canal de normas;
   - canal de actualizaciones para la moderación.
4. Configurar **Onboarding** (Bienvenida → Integración), como se describe en 4.4.
5. Crear roles, canales y permisos (4.2 y 4.3).
6. Crear los **webhooks** (Ajustes del canal → Integraciones → Webhooks) para `#novedades`, `#todos-los-libros`, `#ofertas` y los canales de género. Pasar las URL a David **solo por un canal privado** y guardarlas como secreto de GitHub. Nunca en el repositorio ni en el chat.
7. **Invitación permanente**: Invitar → Editar → Caducidad «Nunca», usos «Sin límite», canal de destino `#bienvenida`. Esa URL va en `platforms.discord.invite`.
8. Probar entrar con una cuenta secundaria desde móvil y escritorio.

### 4.2 Roles

| Rol | Quién | Permisos clave |
| --- | --- | --- |
| `Admin` | David | Administrador (solo él) |
| `Moderación` | 1–3 personas de confianza | Gestionar mensajes, Aislar miembros (timeout), Gestionar hilos, Ver registro de auditoría. **Sin** expulsar ni banear al principio; eso lo hace Admin. |
| `Bots` | Webhooks / bots | Enviar mensajes en los canales de avisos |
| `Lector` | Todos tras aceptar las normas | Leer, escribir en los canales de charla, reaccionar, crear hilos |
| Roles de género (`Fantasía`, `Thriller`, `Romántica`…) | Los elige cada persona en Onboarding | Sin permisos; sirven para ver u ocultar canales y para menciones opcionales |
| `Avisos` | Opcional | Recibir @mención en novedades importantes |

**Ajustes de `@everyone`:**
- quitar «Mencionar @everyone», «Crear invitación» (solo moderación) y «Insertar enlaces» en los canales de charla durante la primera semana de cada miembro (AutoMod, 4.5);
- notificaciones predeterminadas: **solo @menciones**.

### 4.3 Categorías y canales

```
📌 INICIO
  #bienvenida          (solo lectura: qué es esto, cómo elegir géneros)
  #normas              (solo lectura; el canal de reglas de Comunidad)
  #anuncios            (Anuncios; solo Admin; los demás servidores pueden seguirlo)

📚 AL DÍA                (solo lectura; publican webhooks)
  #novedades           (Anuncios)
  #todos-los-libros
  #ofertas
  #proximos-lanzamientos

🏷️ POR GÉNERO            (solo lectura; cada uno visible para su rol de género)
  #thriller-misterio-terror
  #fantasia-y-ciencia-ficcion
  #romantica
  #infantil-y-juvenil
  #cocina-y-bienestar
  #no-ficcion
  #comic

💬 CHARLA
  #que-estas-leyendo   (texto; modo lento 10 s)
  #pide-recomendacion  (Foro, con etiquetas por género; un hilo por petición)
  #club-de-lectura     (Foro: un hilo por libro del mes, con aviso de spoilers)
  #votaciones          (encuestas nativas de Discord para «los más votados»)
  #off-topic           (opcional; modo lento 30 s)

🎙️ VOZ (opcional, fase 2)
  🔊 Club de lectura en vivo (Escenario)

🛡️ MODERACIÓN            (oculto, solo Moderación y Admin)
  #registro-moderacion (alertas de AutoMod y avisos de Comunidad)
  #moderacion-chat
```

**Por qué así:**
- Los avisos y la charla van separados, de modo que nadie se pierde los libros entre conversaciones.
- Los foros evitan que las peticiones de recomendación se pierdan.
- Los canales de género solo aparecen a quien los eligió, así que el servidor no abruma.

### 4.4 Onboarding (lo que ve alguien al entrar)

1. Pantalla de bienvenida con 3 canales destacados: `#novedades`, `#pide-recomendacion`, `#que-estas-leyendo`.
2. **Pregunta 1:** «¿Qué te gusta leer?». Selección múltiple con los 7 géneros, cada uno con su emoji. Asigna el rol de género y muestra su canal.
3. **Pregunta 2:** «¿Qué quieres recibir?». Opciones: novedades, ofertas, próximos lanzamientos. Muestra u oculta esos canales.
4. **Normas** (Reglas del servidor en Onboarding): hay que aceptarlas para escribir.
5. Lista de «Primeros pasos»: presentarte en `#que-estas-leyendo` y pedir una recomendación.

Esto sustituye a los bots de «reaction roles». Se puede cambiar después desde «Canales y roles».

### 4.5 Control y seguridad

- **Nivel de verificación:** *Medio* (cuenta con más de 5 minutos y correo verificado). Subir a *Alto* (10 minutos en el servidor) si llega spam.
- **Filtro de contenido explícito:** analizar el contenido de **todos los miembros**.
- **AutoMod nativo** (Ajustes → Seguridad → AutoMod):
  - bloquear spam sospechoso;
  - bloquear menciones masivas (más de 5);
  - bloquear palabras de la lista de Discord (insultos, contenido sexual);
  - una regla propia contra enlaces de invitación a otros servidores (`discord.gg/`, `discord.com/invite`) y acortadores;
  - enviar las alertas a `#registro-moderacion`;
  - aislamiento automático de 60 s en reincidencia.
- **Configuración de seguridad:**
  - activar «Ocultar enlaces sospechosos» y la protección contra incursiones (*raid protection*) con alertas;
  - requerir 2FA para acciones de moderación.
- **Modo lento:** 10 s en charla y 30 s en off-topic. Los foros, con 1 hilo cada 10 minutos por persona.
- **Invitaciones:** solo Admin y Moderación pueden crearlas. Revisar y borrar las temporales cada mes.
- **Spoilers:** norma de usar `||spoiler||`. En el foro de club de lectura, hilos separados por capítulos.
- **Afiliación:** aviso en `#normas` y en cada canal de avisos de que los enlaces a Amazon son de afiliado.

**Normas** (borrador corto; se cierran más adelante, como pidió David):
1. Respeto; nada de odio ni acoso.
2. Sin spam ni autopromoción salvo en el hilo mensual de autores.
3. Spoilers marcados.
4. Nada de piratería (PDF, enlaces de descarga).
5. Las decisiones de moderación se comentan por privado.

### 4.6 Bots auxiliares

| Necesidad | Solución recomendada | Alternativa |
| --- | --- | --- |
| Publicar libros | **Webhooks** desde el mismo workflow, sin servidor ni bot conectado | — |
| Roles por género | **Onboarding nativo** | Carl-bot (reaction roles) |
| Moderación automática | **AutoMod nativo** | Carl-bot o Dyno (más reglas, logs) |
| Registro de mensajes borrados y editados | Registro de auditoría nativo (limitado) | Carl-bot (logs completos) si hay 2+ moderadores |
| Encuestas | Encuestas nativas de Discord | — |
| Bienvenida | Pantalla de bienvenida y Onboarding nativos | — |

**Recomendación:**
- Lanzar **sin bots de terceros**: menos permisos concedidos a terceros y menos datos compartidos.
- Añadir Carl-bot solo para logs cuando haya moderadores y algo que auditar, con permisos mínimos y sin Administrador.

### 4.7 Moderación humana

- Empezar con **David y 1 moderador** de confianza (alguien de la comunidad de lectores que ya interactúe en redes).
- Revisar `#registro-moderacion` una vez al día durante el primer mes.
- **Escalado:** aviso → aislamiento 1 h → aislamiento 1 día → expulsión (Admin).
- **Discovery** (aparecer en el buscador de servidores de Discord) pide modo Comunidad, servidor con cierta antigüedad, actividad y un mínimo de miembros (el umbral histórico era 1.000). Hay que confirmarlo cuando se acerque. No se cuenta con ello para el lanzamiento.

---

## 5. Plataformas: respuesta clara

**Empezamos solo con Telegram y Discord.** Motivos:
- son las dos únicas plataformas con publicación automática gratuita y fiable;
- en ambas el lector se une con un toque sin dar su número a otros;
- ya tenemos el bot funcionando en Telegram.

| Plataforma | Decisión | Cuándo |
| --- | --- | --- |
| **Telegram** | Sí: canales + carpeta + bot | Lanzamiento |
| **Discord** | Sí: servidor + webhooks | Lanzamiento |
| WhatsApp Canales | **No en el lanzamiento.** No hay una API pública general para publicar en canales (lo confirmo de nuevo antes de decidir). Como mucho, un canal manual «Libros de la semana» con un resumen semanal | Fase 3, si se piden |
| RSS (`/recomendaciones/novedades.xml`) | Sí, es barato y no requiere comunidad | Fase 2 |
| Boletín por correo | Sí, es la mejor retención, pero exige proveedor, privacidad y doble confirmación | Fase 3 |
| Bluesky / Mastodon | Ya hay perfiles; una cuenta-bot no aporta más que Telegram | No |
| Signal, Reddit, grupos de Facebook | Sin canal de difusión útil o con moderación costosa | No |

---

## 6. Dónde se muestran los grupos (para que se vean)

Ya hecho en la rama (commit a4fd0305e):
- iconos de Telegram y Discord en el pie;
- tarjetas en `/redes-sociales/`;
- línea en la cabecera de `/recomendaciones/` y enlace inferior;
- mapa del sitio.

| Lugar | Qué añadir | Prioridad |
| --- | --- | --- |
| **Pie** | Además de los iconos, una línea en la columna de marca: «Recibe las novedades en Telegram →». Los iconos solos se confunden con perfiles personales. | Alta |
| **`/recomendaciones/` con filtro de género** (`?tag=fantasia`) | Banda pequeña bajo los filtros: «📣 Canal de Telegram de Fantasía — Unirme». Sale de `communities.json` por categoría. | **Alta**: es el momento de máxima intención |
| **Fichas de libro** (`/recomendaciones/libros/<slug>/`, 181 páginas) | Bajo «Comprar»: «¿Te avisamos de libros como este? Canal de <género> en Telegram». Generado en el build a partir del primer género que tenga canal. | **Alta**: son las páginas que más tráfico de búsqueda reciben |
| **Inicio** | Un bloque en la sección de lecturas, no en la intro. | Media |
| **`/redes-sociales/`** | Ya hecho; añadir la carpeta «Elegir mis canales» cuando exista. | Media |
| **Próximos lanzamientos** (calendario `.ics` y su página) | «Recíbelos cada lunes en Telegram». | Media |
| **Mensajes de Telegram/Discord** | Línea fija con `davidportodiaz.com/comunidad` (bucle de crecimiento). | Alta |
| **Redes (Instagram, TikTok, X)** | Enlace en bio a `/comunidad/` y publicación de lanzamiento con la imagen de los canales. | Alta, manual |

Sin ventanas emergentes nuevas: compiten con la de apoyo y empeoran la experiencia.

---

## 7. SEO

### 7.1 Búsquedas objetivo

Volumen relativo estimado; se confirma con Search Console tras el lanzamiento.

| Intención | Consultas | Dónde responder |
| --- | --- | --- |
| Principal | «grupos de Telegram de libros», «canales de Telegram de libros», «canal Telegram libros» | `/comunidad/` (título y H1) |
| Novedades | «novedades editoriales Telegram», «canal novedades libros» | Tarjeta y sección Novedades |
| Ofertas | «ofertas libros Telegram», «libros rebajados hoy Amazon» | Tarjeta Ofertas; página propia en fase 2 |
| Género | «grupo Telegram fantasía libros», «canal Telegram libros romántica», «Telegram thriller libros» | Anclas y, en fase 2, páginas por canal |
| Discord | «Discord de libros en español», «servidor Discord club de lectura» | Sección `#discord` |

**Nota de honestidad:** quien busca «grupos de Telegram de libros» a veces busca PDF pirata. La página dirá claramente «sin PDF ni piratería; novedades, ofertas y recomendaciones legales». Eso filtra a ese público y es coherente con las normas.

### 7.2 Cambios en la página

- **Título:** «Canales y grupos de Telegram de libros + Discord | David Porto Díaz». Si supera ~60 caracteres, la marca va al final, donde no importa que se corte.
- **H1 manuscrito:** «Comunidad lectora». Debajo, un subtítulo en texto normal con la palabra clave: «Canales de Telegram de libros por género y servidor de Discord en español».
- **Meta description:** «Únete gratis a canales de Telegram de libros: novedades del día, ofertas, thriller, fantasía, romántica… y a nuestro Discord de lectura en español. Sin spam ni piratería.»
- **Preguntas frecuentes** con las consultas reales:
  - «¿Hay grupos de Telegram de libros en español?»
  - «¿Es gratis?»
  - «¿Comparten PDFs?» → No.
  - «¿Cómo me salgo?»
  - «¿Qué diferencia hay entre canal y grupo?»
- **Contenido fresco:** «Últimos libros publicados en los canales», generado desde el catálogo en cada build. Google ve que la página cambia.
- **Datos estructurados:** mantener `CollectionPage` + `ItemList`. Cada elemento lleva `url` a `t.me/<usuario>` cuando sea público.

### 7.3 Fuera de la web

- **Canales públicos con `@usuario`.** `t.me/s/<usuario>` es indexable. Cada canal enlaza a la web en la descripción y en el mensaje fijado.
- **Directorios de Telegram**, con alta manual y gratuita: TGStat (el más usado en español), telegramchannels.me y Telegram Directory.
- **Directorios de Discord:** Disboard y Discord.me.
- **Enlaces desde las redes de David** y desde la ficha de autor.

### 7.4 Fase 2: una página por canal

`/comunidad/telegram/fantasia/` y similares, **solo cuando el canal tenga ≥ 20 publicaciones**. Llevarían:
- el texto del canal;
- los últimos 10 libros;
- el enlace y el QR;
- un enlace al género del catálogo.

Antes de eso serían páginas vacías y Google las trataría como contenido escaso.

---

## 8. Imágenes de los canales (prompts para ChatGPT)

### 8.1 Sistema visual común

**Formato y tamaño**
- Avatar cuadrado de 1024×1024. Telegram lo recorta en **círculo** y lo muestra a 40–50 px en la lista de chats.

**Zona segura**
- Todo lo importante dentro de un círculo central del 80 %, sin nada en las esquinas.

**Estructura de cada avatar**
- Fondo de color plano o con un degradado muy suave, propio de cada canal.
- Un **icono** simple y grueso en el centro superior, en blanco.
- Una **palabra** grande y corta en blanco: máximo 9–10 letras, sans serif geométrica en negrita.
- `davidportodiaz.com` muy pequeño abajo, centrado, dentro del círculo. A 40 px no se leerá; es una firma para cuando se abre el perfil.

**Paleta** (contraste AA del blanco sobre el fondo):

| Canal | Color | Hex | Icono | Palabra |
| --- | --- | --- | --- | --- |
| Todos | azul tinta de la web | #0d2c57 | pila de libros | LIBROS |
| Novedades | rojo coral | #c8372d | libro con destello / estrella | NOVEDADES |
| Ofertas | verde | #1c7a43 | etiqueta de precio | OFERTAS |
| Más votados | dorado oscuro | #8a6100 | estrella / trofeo | TOP |
| Próximos | violeta | #5b3fa8 | calendario | PRÓXIMOS |
| Thriller | casi negro con rojo | #1b1b1f + #c8372d | lupa / huella | THRILLER |
| Fantasía | índigo | #2e2a7a | dragón / estrellas | FANTASÍA |
| Romántica | frambuesa | #b0255e | corazón con página | ROMÁNTICA |
| Infantil y juvenil | naranja | #c55a00 | globo o cometa | INFANTIL |
| Cocina | verde oliva / terracota | #8a4b1f | cuchara de madera + vapor | COCINA |
| No ficción | azul petróleo | #0f5e66 | bombilla | ENSAYO |
| Cómic | amarillo + negro | #f2c200 con texto negro | bocadillo de cómic | CÓMIC |
| Poesía (fase 2) | azul noche | #23305e | pluma | POESÍA |
| Histórica (fase 2) | granate | #7a2330 | columna / reloj de arena | HISTORIA |
| Religión (fase 2) | morado suave oscuro | #4b3a6b | rayo de luz | ESPÍRITU |
| Discord | blurple | #5865f2 | libro abierto con bocadillo | CLUB |

**Inspiración** (estilo, no copiar marcas):
- iconos de app de Spotify, Duolingo y Headspace: colores planos y una sola forma;
- colecciones de Penguin Classics: color por género y tipografía limpia.

**Prohibido:**
- fotos;
- texturas baratas, 3D brillante, degradados arcoíris, sombras paralelas o marcos;
- más de una palabra grande;
- imitar logos de Telegram, Discord o Amazon.

**Revisión obligatoria antes de usar:**
- encoger a 48 px y comprobar que se distingue el icono y el color;
- comprobar que **la palabra está bien escrita** (ChatGPT a veces se come las tildes);
- comprobar que el recorte circular no corta nada.

### 8.2 Prompt base (se cambia lo que va entre corchetes)

```
Diseña un avatar cuadrado de 1024×1024 para un canal de Telegram de libros en español.
Estilo: icono de app moderno y premium, diseño plano, vectorial, limpio, como los iconos de Spotify o Duolingo y las portadas por colores de Penguin Classics. Nada de fotografía, 3D, brillos, texturas ni sombras.
Fondo: color plano [COLOR] ([HEX]) con un degradado radial muy sutil un 8 % más claro en el centro. Sin bordes ni marcos.
Composición centrada y pensada para recorte circular: todo dentro del 80 % central, esquinas vacías.
Arriba en el centro: un icono blanco, grueso y simple de [ICONO], trazo redondeado, que ocupe aprox. el 35 % del ancho.
Debajo: la palabra «[PALABRA]» en mayúsculas, blanco, tipografía sans serif geométrica extra negrita (tipo Montserrat ExtraBold), escrita exactamente así, con su tilde, ocupando aprox. el 70 % del ancho.
Abajo del todo, dentro del círculo: «davidportodiaz.com» muy pequeño, blanco al 75 % de opacidad, sans serif regular.
Debe leerse y reconocerse a 48 píxeles. Contraste alto. Sin más texto.
```

### 8.3 Prompts por canal (lanzamiento)

1. **Todos los libros**
   - [COLOR] azul tinta, [HEX] #0d2c57.
   - [ICONO] una pila de tres libros vistos de lado, con un pequeño punto dorado #f2c200 a modo de marcapáginas.
   - [PALABRA] LIBROS.
   - Extra: «Debajo de LIBROS, en una segunda línea más pequeña: “TODOS”».
2. **Novedades**
   - [COLOR] rojo coral, #c8372d.
   - [ICONO] un libro cerrado de frente con una estrella de cuatro puntas brillando en la esquina superior derecha.
   - [PALABRA] NOVEDADES.
3. **Ofertas de hoy**
   - [COLOR] verde, #1c7a43.
   - [ICONO] una etiqueta de precio con agujero y un libro pequeño dentro, con el símbolo «%».
   - [PALABRA] OFERTAS.
4. **Próximos lanzamientos**
   - [COLOR] violeta, #5b3fa8.
   - [ICONO] una hoja de calendario con un libro en lugar del número.
   - [PALABRA] PRÓXIMOS.
5. **Más votados** (fase 2)
   - [COLOR] dorado oscuro, #8a6100.
   - [ICONO] una estrella grande sobre un libro abierto.
   - [PALABRA] TOP.
   - Extra: «segunda línea pequeña: “MÁS VOTADOS”».
6. **Thriller, misterio y terror**
   - [COLOR] casi negro, #1b1b1f.
   - [ICONO] una lupa con una pequeña gota roja #c8372d en el cristal.
   - [PALABRA] THRILLER.
7. **Fantasía y ciencia ficción**
   - [COLOR] índigo, #2e2a7a.
   - [ICONO] la silueta de un dragón pequeño enroscado sobre un libro abierto, con dos estrellas.
   - [PALABRA] FANTASÍA.
8. **Romántica**
   - [COLOR] frambuesa, #b0255e.
   - [ICONO] un libro abierto cuyas páginas forman un corazón.
   - [PALABRA] ROMÁNTICA.
9. **Infantil y juvenil**
   - [COLOR] naranja, #c55a00.
   - [ICONO] una cometa con forma de libro y una cola con lazos.
   - [PALABRA] INFANTIL.
   - Extra: «segunda línea pequeña: “Y JUVENIL”».
10. **Cocina y bienestar**
    - [COLOR] terracota, #8a4b1f.
    - [ICONO] una cuchara de madera y un libro de recetas abierto con tres líneas de vapor.
    - [PALABRA] COCINA.
11. **No ficción**
    - [COLOR] azul petróleo, #0f5e66.
    - [ICONO] una bombilla cuya base es un libro.
    - [PALABRA] ENSAYO.
    - Extra: «segunda línea pequeña: “Y NO FICCIÓN”».
12. **Cómic**
    - [COLOR] amarillo, #f2c200.
    - Texto e icono en **negro** #1b1b1f en vez de blanco.
    - [ICONO] un bocadillo de cómic con tres puntos.
    - [PALABRA] CÓMIC.

**Fase 2:**
- **Poesía:** #23305e; una pluma estilográfica dibujando una línea ondulada; POESÍA.
- **Histórica:** #7a2330; un reloj de arena con un libro en la base; HISTORIA.
- **Religión:** #4b3a6b; un libro abierto del que salen rayos de luz suaves; ESPÍRITU.

### 8.4 Discord (genérico)

- **Icono del servidor (1024×1024, recorte circular).** Prompt base con:
  - [COLOR] blurple, #5865f2;
  - [ICONO] un libro abierto con un bocadillo de conversación saliendo de sus páginas;
  - [PALABRA] CLUB;
  - segunda línea pequeña: «DE LECTURA».
- **Banner de invitación (960×540)**, un prompt aparte:

```
Banner horizontal 960×540 para el servidor de Discord «Club de lectura · David Porto». Diseño plano, premium, fondo azul tinta #0d2c57 con una franja diagonal blurple #5865f2. A la izquierda, ilustración vectorial simple de varios libros de colores (rojo #c8372d, índigo #2e2a7a, verde #1c7a43, amarillo #f2c200) en una estantería. A la derecha, el texto «Club de lectura» en blanco, sans serif geométrica negrita, y debajo, más pequeño, «Novedades, recomendaciones y charla». Abajo a la derecha, pequeño: «davidportodiaz.com». Sin fotos, sin 3D, sin logos de marcas. Deja libre el 15 % superior izquierdo (Discord superpone el icono).
```

### 8.5 Procedimiento de generación (cuando haya luz verde)

1. **ChatGPT** en la sesión del navegador del puerto 9240. Es compartida con otra sesión, así que hay que coordinarse para no pisarla.
2. **Generar en lotes** de 3–4 canales. Para mantener la coherencia, pedir: «mismo estilo exacto que la imagen anterior; cambia solo color, icono y palabra».
3. **Revisar cada imagen** según 8.1, encogiéndola a 48 px. Regenerar si la tilde o la palabra salen mal.
4. **Guardar originales** en `assets/community-avatars/<id>.png` (512×512, optimizado) para que las tarjetas de `/comunidad/` usen la misma imagen.
5. **Subir a Telegram** (foto del canal) y a Discord (icono y banner) desde la cuenta de David.

---

## 9. Implementación tras la luz verde (orden propuesto)

1. **David crea los canales y la carpeta.**
   - Crea en Telegram los 10 canales de fase 1, públicos y con los `@usuario` libres.
   - Añade `@DavidPortoLibrosBot` como administrador con solo «Publicar».
   - Crea la carpeta compartible.
   - Pone Novedades en público.
2. **David crea el servidor de Discord** (sección 4) y los webhooks.
3. **Generación de imágenes** (8.5).
4. **Código** (un solo PR):
   - `communities.json` con los canales nuevos, `phase`, `addlist` e invitaciones;
   - validador con `t.me/addlist`;
   - tarjetas con imagen, último libro y QR;
   - ajustes SEO (título, subtítulo, FAQ);
   - banda por género en `/recomendaciones/?tag=`;
   - línea en las fichas de libro;
   - línea en el pie.
5. **Worker**:
   - modo «nuevo en catálogo» para Todos y los géneros;
   - resumen semanal de Próximos;
   - pie de mensaje con la URL de la comunidad;
   - envío a los webhooks de Discord;
   - secretos `READING_TELEGRAM_CHANNELS_JSON` y `READING_DISCORD_WEBHOOKS_JSON` actualizados por David.
6. **Pruebas:**
   - suite local;
   - vista previa en móvil y escritorio;
   - unirse con la carpeta desde el móvil;
   - un envío etiquetado de prueba por canal (`--test-asin`).
7. **Pagefind:** regenerar el índice con `pagefind@1.6.0`.
8. **Publicación:** push y PR **cuando Actions esté libre**, y alta en directorios.
9. **Después:** Ofertas (comparador de precios), Más votados (votación de la comunidad), bot conserje, páginas por canal, RSS.

## 10. Estado real (creado el 2 de noviembre de 2026 desde el Edge de David)

### 10.1 Telegram

- **17 canales de difusión** creados con título, descripción (horario y enlace a /comunidad/) y foto propia:
  - Al día: Novedades, Todos los libros nuevos, Ofertas de hoy, Próximos lanzamientos, Más votados.
  - Géneros: Thriller, Romántica, Fantasía, Terror, Ciencia ficción, Histórica, Infantil y juvenil, Ensayo y no ficción, Cocina y bienestar, Cómic, Poesía, Religión y espiritualidad.
- `@DavidPortoLibrosBot` es administrador de los 17 canales, con permisos para publicar, editar y borrar mensajes.
- Carpeta compartible **«Libros DP»** con los 17 canales: <https://t.me/addlist/lja92v39DGE4YmM0>. Es el botón «Unirme a todos» de /comunidad/.
- **Usernames públicos (10):** novedades, todos, ofertas, más votados, próximos, thriller, romántica, fantasía, terror y ciencia ficción, todos con el formato `<tema>_libros_dp`.
  - Telegram permite como máximo 10 canales públicos por cuenta sin Premium (`CHANNELS_ADMIN_PUBLIC_TOO_MUCH`).
  - Los otros 7 (histórica, infantil y juvenil, ensayo, cocina, cómic, poesía y religión) usan un enlace de invitación `t.me/+…` y también están en la carpeta.
- Las 17 fotos de canal están puestas.
- Los chat_id de los canales **no** se guardan en el repositorio. Van en el secreto `READING_TELEGRAM_CHANNELS_JSON`: un mapa `id → @usuario o chat_id`, que gestiona David.

### 10.2 Discord: «Club de lectura · David Porto»

- **Estructura:**
  - INICIO: #bienvenida, #normas, #anuncios.
  - AL DÍA: #novedades, #todos-los-libros, #ofertas, #proximos-lanzamientos, #mas-votados.
  - POR GÉNERO: 12 canales.
  - CHARLA: foros #pide-recomendacion y #club-de-lectura, más #que-estas-leyendo, #votaciones y #off-topic.
  - MODERACIÓN: #registro-moderacion, privado.
- **Configuración:**
  - Icono, banner, descripción y roles.
  - Filtro de contenido sensible.
  - Tres reglas de AutoMod (spam de menciones con límite de 5, spam sospechoso y palabras marcadas). Bloquean el mensaje y envían una alerta a #registro-moderacion.
  - Modo lento: 10 s en #que-estas-leyendo y 30 s en #off-topic, con sus temas.
  - Mensajes publicados en #normas (7 normas) y #bienvenida.
- **Propiedad:** el servidor es de la cuenta «David Porto» (davidportodiaz.com) desde el 2 de noviembre de 2026. La cuenta antigua que lo creó ya no es miembro, sus invitaciones están revocadas y no hay webhooks ni apps suyas.
- **Invitación permanente:** <https://discord.gg/g7dEWxj3F>, creada por David Porto. No caduca y no tiene límite de usos.
- **Modo Comunidad activado** (directrices aceptadas con autorización de David): correo verificado obligatorio, notificaciones «Solo menciones», permisos arriesgados quitados a @everyone, canal de normas #normas y canal de avisos de Discord #moderator-only (creado por el asistente).
- **Canales de anuncios:** #anuncios y los 5 de AL DÍA (#novedades, #todos-los-libros, #ofertas, #proximos-lanzamientos y #mas-votados). Se pueden seguir desde otros servidores.
- #normas y #bienvenida vuelven a estar publicados desde David Porto. Los 2 mensajes antiguos de la cuenta anterior los borra David a mano.
- **Roles (todos autoasignables en el onboarding salvo staff y niveles):**
  - Staff: Administración, Moderación, Bots, Lector.
  - Géneros (12): Thriller, Romántica, Fantasía, Terror, Ciencia ficción, Histórica, Infantil-juvenil, Ensayo, Cocina, Cómic, Poesía, Espiritualidad.
  - Avisos con campana: 🔔 Novedades, 🔔 Ofertas, 🔔 Lanzamientos, 🔔 Club de lectura. Son los únicos que hacen sonar el móvil (los publica el bot mencionando el rol).
  - Niveles (separados en la lista de miembros): Lector/a novel → Lector/a habitual → Ratón de biblioteca → Bibliófilo/a → Leyenda de la biblioteca. Los asigna el bot de niveles (10.5).
- **Onboarding activado** (2 de noviembre de 2026):
  - 9 canales por defecto (INICIO, AL DÍA y CHARLA); los 12 de género se abren al elegirlos.
  - P1 (antes de entrar, múltiple): «¿Qué géneros te gustan?» → canal + rol de cada género.
  - P2 (antes de entrar, múltiple): «¿De qué quieres enterarte con aviso? (Lo demás llega en silencio)» → roles 🔔, o «🤫 Prefiero silencio».
  - P3 (después de entrar): «¿Quieres ver algo más del catálogo?» → #todos-los-libros, #mas-votados.
  - Guía: cartel de bienvenida (menciona `/libro`), 5 tareas (contar qué lees, pedir recomendación, votar, mirar novedades, leer normas). Sin páginas de recursos: Discord no ofrece ningún canal elegible.
  - **Sonido:** el onboarding no puede silenciar canales; por eso el servidor está en «Solo @mentions» y solo suenan las menciones a los roles 🔔 que cada uno eligió.
- **Webhooks:** no se crean desde aquí. David los crea, uno por canal de avisos, y los guarda en el secreto `READING_DISCORD_WEBHOOKS_JSON` (mapa `id → URL`). Nunca se guardan en el repositorio.

### 10.3 Publicación (worker, siguiente PR)

- **Horario:**
  - Un solo envío por canal y día: de lunes a viernes a las 11:30 y los fines de semana a las 18:30 (Europe/Madrid).
  - Próximos lanzamientos se publica los lunes a las 11:30.
  - Más votados se publica los sábados a las 18:30.
- **Más votados:** ranking a partir de `assets/reading-market.json → ratings` (nota y número de valoraciones de Goodreads), con un mínimo de votos para entrar.
- **Ofertas:** a partir de `reading-market.json → offers`. Solo bajadas reales (antes → ahora).
- **Pie común:** «Más canales: davidportodiaz.com/comunidad · Enlaces de afiliado».

### 10.4 Bot buscador `/libro` (Discord) y `@DavidPortoLibrosBot` (Telegram)

Código listo y probado en local; **no desplegado** (GitHub Actions está parado, así que se despliega a mano desde el PC de David).

- `scripts/build-bot-index.py` genera `data/bot-books.json` desde el catálogo de /lecturas/ (título, autores, sinopsis, categorías, edad, fecha, formatos con precio y enlace de Amazon con afiliado). Se publica con la web; el bot lo lee cada 10 min, así que **siempre está sincronizado con la web** sin redesplegar.
- `bots/book-finder.mjs` interpreta frases libres («fantasía para mi hijo de 11 años», «thriller de menos de 10 €», «algo de Neil Gaiman», «audiolibro de terror») y devuelve 3 libros variados con enlace de afiliado y enlace a la ficha.
- `bots/community-bot-worker.mjs` (Cloudflare Worker gratuito): `POST /discord` (verifica firma Ed25519, comando `/libro busco:`) y `POST /telegram` (privado, `/buscar` en grupos y modo inline `@bot texto` en cualquier chat).
- IA opcional: con `BOT_AI=true`, Workers AI (Llama 3.1 8B, cuota gratuita) solo reescribe la petición en palabras clave cuando la búsqueda directa no encuentra nada. Los libros siempre salen del catálogo real (sin inventar).
- Tests: `node tests/test-book-finder.mjs` y `node tests/test-community-bot-worker.mjs`.

**Despliegue (David, una vez, ~15 min):** desde la raíz del repo, `powershell -ExecutionPolicy Bypass -File bots/deploy-community-bot.ps1`. El script:
1. Comprueba Node, crea `wrangler.community-bot.jsonc` desde el ejemplo (ignorado en git) y despliega el worker con `wrangler deploy`.
2. Pide de forma oculta la Public Key de Discord y el token de Telegram, genera `TELEGRAM_WEBHOOK_SECRET` aleatorio y los sube con `wrangler secret bulk` (fichero temporal que se borra al terminar).
3. Indica la Interactions Endpoint URL (`…/discord`) para pegarla en el Developer Portal y espera.
4. Abre la invitación de la app al servidor (`applications.commands`), pide el Bot Token y registra `/libro` (debe imprimir `200 /libro`).
5. Configura en Telegram `setWebhook` (`…/telegram`, `secret_token`, `message` + `inline_query`) y `setMyCommands` (`buscar`).
6. Queda a mano en @BotFather: `/setinline` (marcador «qué te apetece leer…»).
7. Probar: `/libro busco: fantasía para 11 años` en Discord, `/buscar thriller` al bot y `@DavidPortoLibrosBot terror` en cualquier chat.

`-SoloDiscord` o `-SoloTelegram` repiten solo esa parte.

### 10.5 Bots externos

- **Niveles: Lurkr — instalado y configurado** (2 de noviembre de 2026, verificado tras recargar el panel):
  - XP solo en 18 canales (whitelist): los 12 de género, #pide-recomendacion, #club-de-lectura, #que-estas-leyendo, #votaciones, #off-topic y #recomendador-ia. Sin XP en INICIO ni AL DÍA.
  - XP en hilos sí; XP por comandos no; reinicio de nivel al banear.
  - **Sin anuncios de subida de nivel** (canal de avisos: ninguno).
  - Recompensas (acumulables): 1 Lector/a novel, 5 Lector/a habitual, 10 Ratón de biblioteca, 20 Bibliófilo/a, 35 Leyenda de la biblioteca.
  - El rol de Lurkr está justo encima de «Leyenda de la biblioteca» (debajo de 🔔 Club de lectura) y tiene «Gestionar roles».
- **Directorios (DISBOARD, Top.gg, Discadia) y Telegram:** guía en `docs/comunidades-directorios.md`.
- **Moderación:** AutoMod nativo (ya activo) basta al tamaño actual; no se añade bot extra.
- **Club de lectura:** las votaciones usan las encuestas nativas de Discord en #votaciones y los Eventos del servidor para las quedadas; no hace falta bot.

### 10.6 Telegram: mejoras paralelas

- Mismo buscador: `@DavidPortoLibrosBot` responde en privado, con `/buscar` en grupos y en modo inline (se despliega con el paso 7 de 10.4).
- Grupo de comentarios: crear un grupo «Club de lectura · David Porto (charla)» y vincularlo como grupo de debate de @novedades_libros_dp (Ajustes del canal → Debate). Activar en el grupo los Temas (Topics) con los mismos nombres que CHARLA en Discord y añadir el bot como admin para `/buscar`.
- Silencio: los canales ya publican un solo envío al día; en la descripción se indica que se pueden silenciar y que el aviso con sonido es solo el de Novedades.

## 11. Pendiente de confirmar con David

- Borrar los 2 mensajes antiguos de #normas y #bienvenida (los de la cuenta anterior).
- Ejecutar `bots/deploy-community-bot.ps1` (10.4) y `/setinline` en @BotFather.
- Dar de alta el servidor en DISBOARD, Top.gg y Discadia y los canales en TGStat (`docs/comunidades-directorios.md`).
- Crear el grupo de comentarios de Telegram (10.6).
- Crear los webhooks de Discord y los dos secretos (`READING_TELEGRAM_CHANNELS_JSON` y `READING_DISCORD_WEBHOOKS_JSON`).
- Quién modera Discord, además de David.
- Instalar los bots de §12.2 (OAuth de David) y arrancar los rituales de §12.3.
- Dar de alta Discord y Telegram como sitios en Amazon Afiliados (§12.10).

## 12. Interacción, bots gratuitos y crecimiento (investigación del 2 de noviembre de 2026)

Fuentes: documentación de Discord, Telegram y Amazon Afiliados, fichas de servidores de libros en DISBOARD y Top.gg, y dos consultas a ChatGPT (resumidas aquí). Lo que depende de condiciones de terceros lleva «comprobar» y se revisa al ejecutar la PR.

### 12.1 Principio

- Discord sirve para conversar, Telegram para la difusión por género y la web para el catálogo y la compra. El diferencial es el bot propio (`/libro` y el modo inline).
- Éxito no es tener más canales ni más bots. Es que alguien llegue buscando su próxima lectura, acierte y se quede por la gente.
- Hay pocos bots y cada uno hace una sola cosa. No se añaden bots que repitan algo nativo (encuestas, eventos, AutoMod, onboarding) ni MEE6, que tiene funciones de pago y anuncios.

### 12.2 Bots gratuitos: uno por función

| Prioridad | Bot | Función | Plan gratis | Dónde |
|---|---|---|---|---|
| ya | Lurkr | Niveles sin anuncios (§10.5) | sí | 18 canales |
| ya | `@DavidPortoLibrosBot` / `/libro` | 3 libros reales del catálogo | propio | todo |
| 1 | **Apollo** | Eventos con inscripción y recordatorio: tertulia mensual y lectura silenciosa semanal | sí: eventos ilimitados, 5 series recurrentes | #club-de-lectura y el canal de voz |
| 2 | **Suggestions** (suggestions.gg) | Sugerencias con votos y estados | núcleo gratis | Opcional. El foro nativo #sugerencias (§12.4) ya lo cubre, así que solo se instala si se queda corto |
| 3 | **Fumiko** *o* **Marginalia** (solo uno) | Seguimiento de lecturas, retos e importación de Goodreads o StoryGraph | comprobar límites | Se prueba con 5 lectores y se queda el más simple |
| 4 | **Carl-bot** (solo starboard) | #joyas-del-club: los mensajes con ⭐ de 3 personas distintas | starboard gratis | Se activa cuando haya reseñas de miembros |
| 5 | **CUB PROTECTOR** / pregunta del día | 3 preguntas semanales de libros, respuesta en hilo | gratis | Cuando haya participación |
| más tarde | Birthday Bot, GiveawayBot | Cumpleaños voluntarios y sorteos puntuales de libros | gratis | Solo con la comunidad activa; los sorteos nunca como gancho principal |

Instalar cada bot requiere OAuth con la cuenta de David: se hace al ejecutar la PR, uno a uno, con los permisos mínimos y sin rol de administrador.

### 12.3 Rituales semanales (interacción y clics, no spam)

Se empieza con tres (martes, jueves y domingo) y se añaden más cuando haya habituales:

- **Lunes · ¿Qué estás leyendo?** Empezando, a medias o terminado, con foto de la portada. Sin enlaces.
- **Martes · Tres libros para un mismo gusto.** Selección temática del catálogo con enlace a la ficha de la web.
- **Miércoles · Batalla de portadas.** Encuesta nativa entre dos libros.
- **Jueves · Consultorio lector.** Un miembro pide algo, la gente responde y `/libro` propone tres.
- **Viernes · Descubrimiento de la semana.** Reseña de un miembro, con su permiso.
- **Sábado · Lectura compartida.** Voz de 30–45 min sin cámara y charla opcional al final.
- **Domingo · Balance lector.** Un libro terminado, uno abandonado y uno pendiente. Recopilación mensual en la web.

Además:
- **Libro del mes** votado: cada persona propone uno, se eligen 4 finalistas y se vota en #votaciones.
- **Sprints de lectura** en voz.
- **Reto anual sin presión:** 6, 12, 24 o 52 libros, o libre. Insignias por constancia y variedad, nunca por comprar.

### 12.4 Voz y voto

- **Foro #sugerencias (creado y verificado el 2 de noviembre de 2026):**
  - una propuesta por publicación;
  - etiquetas 💡 Idea, 📚 Libro para el club y 🛠️ Mejora del servidor, más las de moderación 👀 En estudio, ✅ Aceptada, 🚀 Hecha y ❌ Descartada;
  - etiqueta obligatoria y reacción por defecto 👍;
  - publicación semilla «¿Qué te gustaría encontrar en el club?».
- **Revisión mensual:** las más votadas pasan a un estado con su motivo y se publica en #anuncios «Lo que habéis cambiado» con 3 decisiones aplicadas. Votar sin consecuencias desanima.
- **Consejo lector rotatorio:** 3 voluntarios al mes que proponen actividades, sin moderar.
- **Encuesta trimestral de 5 preguntas:** facilidad, notificaciones, utilidad, qué sobra y una mejora libre.
- **Reconocimientos:** «Recomendación del mes» y «Reseña más útil», nunca ligados a compras ni a enlaces.
- **Biblioteca viva:** las mejores recomendaciones pasan a las fichas de la web («Recomendado por 3 miembros», «ideal si te gustó…») tras revisión editorial.

### 12.5 Lo que nadie más ofrece

1. **Perfil lector en `/libro`:** «fantasía adulta, sin triángulo amoroso, menos de 400 páginas, final cerrado», con 3 resultados y el porqué de cada uno. Siguiente PR del bot.
2. **Botones en Telegram:** «Otro parecido», «Menos romance», «Más oscuro» y «Ver ficha».
3. **Radar personal:** avisos por autor o saga elegidos por el usuario (los roles 🔔 ya cubren el género).
4. **Buddy reading:** emparejar lectores del mismo título en un hilo con fecha y normas antispoiler.
5. **Mapa literario:** «viajamos a través de un libro», enlazado con `/atlas-literario/`.
6. **Legal y curado:** muchos canales de libros en español de Telegram reparten PDF pirata. Aquí solo hay recomendaciones con ficha y compra legal, y conviene decirlo en las descripciones.

### 12.6 Discord y Google: que nos encuentren

- **Descubrimiento de Discord** (requisitos actualizados en octubre de 2026, comprobar al ejecutar):
  - servidor Comunidad con al menos 1000 miembros y 8 semanas de antigüedad;
  - actividad suficiente;
  - 2FA para moderadores.
  - Los servidores descubribles tienen una página pública indexable, con resúmenes de canales anunciados para el 16 de noviembre y mensajes para mediados de diciembre de 2026. Esa presencia web no se aplica en la UE.
  - Hasta entonces, el SEO lo hace `/comunidad/`.
- **`/comunidad/`** como página de destino para «club de lectura online gratis», «Discord libros español», «canales de Telegram de libros» y «club de lectura de fantasía». Enlazada desde la cabecera, las fichas, los artículos y la newsletter.
- **Invitaciones distintas por origen** (web, Instagram, Reddit, directorios, colaboraciones) para saber qué fuente trae gente que participa. Discord muestra los usos por invitación.
- **Directorios y dónde anunciarse:** `docs/comunidades-directorios.md`.

### 12.7 Telegram: configuración ideal

- **Índice:** mensaje fijado en Novedades y en la carpeta con los 17 canales, cómo silenciarlos y la declaración comercial.
- **Reacciones limitadas:** 👀 me interesa, 📖 leído, ❤️ recomendado y 👎 no me convence.
- **Un único grupo de debate** con Temas (General, Pide un libro, Leyendo ahora, Club de lectura, Sugerencias), vinculado a los canales generales (§10.6). Nunca 17 chats.
- **Encuesta nativa semanal** en Novedades o en el grupo, sin duplicarla en los 17 canales.
- **Formato de envío:** portada, título, autor, gancho de una línea, «para quien le gustó…» y un solo enlace a la ficha. Sin muchos hashtags.
- **Boosts e Historias:** las Historias de canal requieren nivel de boost. Se piden boosts a los suscriptores Premium una vez, sin insistir. Uso previsto: preguntas rápidas y recordatorios, no repetir novedades.
- **Mensajes directos al canal y publicaciones sugeridas** (Telegram, 2025): sirven para recibir propuestas de lectores.
- **Métricas:**
  - vistas por envío entre el 30 y el 60 % de los suscriptores es sano;
  - vigilar bajas y silenciados tras cada cambio de frecuencia.

### 12.8 Errores que hunden estas comunidades

- Muchos canales vacíos. Mejor fusionar (p. ej. #votaciones con Más votados) que tener 20 canales muertos.
- Automatizarlo todo: los bots publican, pero no crean vínculos. Hace falta una actividad humana semanal.
- Confundir clics con fidelidad, forzar la atención con menciones o hacer sorteos constantes.
- Retos competitivos, spoilers sin control y convertir el servidor en escaparate del autor.

### 12.9 Métricas (línea base de 4 semanas antes de fijar objetivos)

- Miembros nuevos activos a 7 días y retención a 30 días.
- Participantes únicos por semana (sin bots).
- Peticiones de recomendación respondidas y asistentes a eventos.
- Visitas a fichas desde Discord y Telegram; clics salientes a Amazon.
- Bajas y silenciados en Telegram.

### 12.10 Amazon Afiliados (comprobar antes de difundir enlaces fuera de la web)

- Amazon.es enumera como redes sociales admitidas Instagram, Facebook, X, YouTube, TikTok y Twitch. **Discord y Telegram no figuran:** hay que darlos de alta como sitios en la cuenta de Afiliados (Central → Información de la cuenta → sitios web y apps) o, mientras tanto, enlazar a la ficha de la web, que es la que lleva el enlace de afiliado.
- Sin acortadores ni redirecciones que oculten el destino.
- «#publicidad» o un aviso equivalente junto a cada enlace comercial, más la declaración de afiliado en la web.
- No publicar precios ni descuentos sin la hora de consulta y la nota «el precio puede cambiar». Nada de alertas de precio automáticas.
- Sin recompensas, XP ni sorteos por comprar o por pulsar enlaces. Todas las actividades se pueden hacer sin comprar.
