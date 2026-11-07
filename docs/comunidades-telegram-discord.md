# Comunidades: Telegram, Discord y otras plataformas

Estado a 2 de noviembre de 2026. La página pública es `/comunidad/`. La genera `scripts/build-community-page.py` a partir de `data/communities.json`.

## Qué hay publicado

- **Página `/comunidad/`**
  - Una sección `#telegram` con dos bloques: «Para estar al día» y «Por género y temática».
  - Una sección `#discord`.
  - Además: cómo funciona, preguntas frecuentes y enlaces internos.
- **Enlaces a la página**
  - Pie de todas las páginas: iconos de Telegram y Discord que llevan a `/comunidad/#telegram` y `/comunidad/#discord`. Son enlaces internos, sin `target` ni `rel=me`.
  - `/redes-sociales/`: tarjetas «Comunidad de Telegram» y «Comunidad de Discord».
  - `/recomendaciones/`: tercera línea en la cabecera y el enlace inferior (antes llevaba a las guías del Cuaderno).
  - Mapa del sitio, `sitemap.xml`, registro (`community`) y la columna «Información» del pie.
- **Botones honestos.** Un grupo solo muestra el botón «Unirme» si tiene un enlace público en `invite`. Si no lo tiene:
  - si está activo, aparece «Enlace muy pronto»;
  - si está previsto, aparece «Próximamente».

  El validador rechaza:
  - enlaces que no sean `https://t.me`, `telegram.me`, `discord.gg` o `discord.com`;
  - un grupo previsto que tenga enlace.

## Qué falta del propietario

1. **Enlace público de Novedades.**
   - Si el canal es privado, crear un enlace de invitación sin caducidad.
   - Mejor aún: dar al canal un nombre público, por ejemplo `t.me/libros_novedades`.
   - Ponerlo en `groups[id=novedades].invite` y ejecutar `python scripts/build-community-page.py`.
2. **Abrir el resto de canales.** Crear cada canal, pasarlo a `status: "active"` y añadir su `invite`.
3. **Discord.** Crear el servidor y poner la invitación permanente en `platforms.discord.invite`.
4. **Reglas de cada grupo.** Quedan para más adelante; el modelo de datos ya permite añadirlas como campo nuevo.

Nunca guardar en el JSON tokens de bot, `chat_id` privados ni enlaces personales.

## Configuración recomendada

### Telegram (los avisos ya funcionan con Novedades)

- **Canales, no grupos, para los avisos.** En un canal solo publica el bot, nadie ve el número de los demás y no hace falta moderar.
- **Conversación.** Si se quiere, se añade un único grupo de debate vinculado a un canal (función «Comentarios»), en vez de un grupo por género.
- **Canales públicos con nombre de usuario.**
  - Es lo que más ayuda al SEO: Telegram publica una vista previa indexable en `t.me/s/<nombre>` que enlaza a la web.
  - Los canales también aparecen en la búsqueda global de Telegram.
- **Un bot para todos los canales.**
  - El bot es administrador con permiso solo para «Publicar mensajes».
  - Los canales por género reutilizan el filtro `categories` (los slugs del catálogo), igual que Novedades.
- **Ofertas de hoy.**
  - Requiere comparar el precio actual con el anterior en cada revisión de tarifas.
  - Publicar solo bajadas reales, mostrando el precio anterior y el nuevo.
  - Respetar la licencia de datos de la Creators API: caché de 24 h y sin imágenes de Amazon.
- **Los más votados.**
  - Exige una fuente de valoraciones de Goodreads con licencia clara.
  - No publicar cifras raspadas.
  - Hasta tenerla, el canal sigue como «Próximamente».

### Discord

- Para publicar avisos bastan los **webhooks por canal**: una URL secreta por canal y un `POST` en JSON. No hace falta un bot conectado al gateway ni un servidor encendido.
- La URL del webhook es un secreto: guardarla en los *secrets* de GitHub Actions, nunca en el repositorio.
- **Canales de anuncios** (Announcement):
  - Otros servidores pueden «seguirlos».
  - Exigen activar el modo Comunidad del servidor.
- **Estructura propuesta:**
  - `#novedades`, `#ofertas` y `#mas-votados`: solo lectura, alimentados por webhooks.
  - Un canal o hilo de foro por género.
  - `#que-estas-leyendo` y `#pide-recomendacion` para conversar.
  - `#normas` y verificación de nivel bajo (correo verificado).
- **Discovery** (aparecer en el buscador de servidores) exige el modo Comunidad y un mínimo de miembros. No cuenta para el lanzamiento.
- La invitación de la web debe ser permanente (sin caducidad ni límite de usos) y llevar a `#normas` o a la bienvenida.

### Otras plataformas

| Plataforma | ¿Bot o API para publicar? | Recomendación |
| --- | --- | --- |
| Canales de WhatsApp | No hay API oficial para publicar en canales; la API de WhatsApp Business sirve para mensajes 1:1 (de pago por conversación) | **No automatizar.** Si se abre, un canal manual con un resumen semanal |
| Bluesky / Mastodon | Sí, API abierta y gratuita | Ya hay perfiles. Se podría añadir una cuenta-bot de novedades, aunque tiene menos sentido que Telegram |
| RSS | Sí (feed estático) | Es barato y lo leen agregadores y apps. Buen complemento: `/recomendaciones/novedades.xml` |
| Boletín por correo | Sí, mediante un proveedor (Buttondown, MailerLite…) | Es la mejor retención a largo plazo. Requiere aviso de privacidad y doble confirmación |
| Signal | No hay canales de difusión públicos | Descartar |

Orden sugerido: completar Telegram (enlaces y canales por género), luego Discord por webhooks, después RSS y, por último, el boletín.

## SEO de `/comunidad/`

- **Etiquetas de la página**
  - Título: «Comunidad lectora en Telegram y Discord | David Porto Díaz» (menos de 60 caracteres útiles antes de la marca).
  - Descripción con las palabras clave «novedades editoriales», «ofertas de libros», «más votados» y «por género».
  - Canonical, Open Graph y Twitter con la imagen de compartir de la web.
- **Datos estructurados (JSON-LD)**
  - `CollectionPage` con `ItemList` de los grupos.
  - `BreadcrumbList` (Inicio › Redes sociales › Comunidad), con migas visibles.
  - Las preguntas frecuentes son `<details>` visibles, pero no se marcan como `FAQPage`: Google ya no muestra ese resultado enriquecido en webs como esta.
- **Enlazado interno**
  - Llegan enlaces desde el pie de todas las páginas, `/redes-sociales/`, `/recomendaciones/` y el mapa del sitio.
  - Cada tarjeta tiene un ancla (`/comunidad/#thriller`) para enlazarla desde las páginas de cada género.
- **Siguiente mejora**
  - Enlazar cada página de categoría del catálogo con su canal (por ejemplo, de `/recomendaciones/terror/` a `/comunidad/#terror`) cuando el canal esté activo.
  - Cuando haya canales públicos, mostrar en la página las últimas publicaciones de Telegram (`t.me/s/<nombre>`) como contenido fresco, sin incrustar *widgets* de terceros que carguen cookies.
- **Índice de búsqueda interno (Pagefind)**: pendiente de regenerar con `python scripts/build-pagefind-index.py` en una copia con `node_modules`.
