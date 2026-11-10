# Comunidades: Telegram, Discord y otras plataformas

Estado a 10 de noviembre de 2026. La página pública es `/comunidad/`. La genera `scripts/build-community-page.py` a partir de `data/communities.json`.

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

## Canales y ritmo (10 de noviembre de 2026)

Todo sale de los libros del día de la web (`/recomendaciones/`), a las 11:30 hora de Madrid. Si un día no hay libros nuevos, ese canal no publica nada.

| Qué | Telegram | Discord | Modo |
| --- | --- | --- | --- |
| Resumen del día: un mensaje con la lista y un enlace de Amazon con todos los ISBN | `todos_libros_dp` | `#resumen-del-dia` | `digest`, diario |
| Novedades libro a libro: portada, autor, editorial, género y descripción | `novedades_libros_dp` | `#novedades-del-dia` | `books`, diario |
| Próximos lanzamientos: los 7 días siguientes, cada lunes, sin repetir | `proximos_libros_dp` | `#proximos-lanzamientos` | `digest`, semanal (lunes) |
| Un canal por género (19), libro a libro | un canal por grupo `temas` | categoría «POR GÉNERO» | `books`, diario |
| Resumen por género (19), un mensaje | — | categoría «RESUMEN POR GÉNERO», `#<genero>-resumen` | `digest`, diario |

- «Ofertas de hoy» y «Los más votados» se retiraron (canales borrados en Telegram y Discord).
- Descripción del libro: la sinopsis si la hay; si no, la ficha de la edición (`edition_note`: formato, páginas y cómo la clasifica la editorial).
- Discord: onboarding con dos preguntas de géneros (ficción y no ficción; Discord admite 12 opciones por pregunta). Cada género abre su canal libro a libro y su resumen, y cada canal se puede silenciar por separado.

### Configuración privada

- El secreto `READING_TELEGRAM_CHANNELS_JSON` guarda la lista de destinos: `group` (un `id` de `data/communities.json`, del que salen las categorías), `platform`, `mode`, `period`, y `chat_id` + `token_env` (Telegram) o `webhook` (Discord).
- El worker lee `data/communities.json` de `main`: **mergear antes de actualizar el secreto** si este nombra grupos nuevos, o el ciclo falla en `resolve_groups`.
- Nunca guardar en el repositorio tokens de bot, `chat_id` privados ni URLs de webhook.

## Configuración recomendada

### Telegram

- **Canales, no grupos, para los avisos.** En un canal solo publica el bot, nadie ve el número de los demás y no hace falta moderar.
- **Canales públicos con nombre de usuario.** Telegram publica una vista previa indexable en `t.me/s/<nombre>` que enlaza a la web, y los canales aparecen en la búsqueda global.
- **Un bot para todos los canales**, administrador con permiso para publicar. Los canales por género reutilizan el filtro `categories` de su grupo.
- La descripción («about») de un canal admite unos 255 caracteres. Editar muchos seguidos provoca `FLOOD_WAIT` de unos 15 minutos.

### Discord

- Los avisos van por **webhooks por canal**: una URL secreta por canal y un `POST` en JSON, sin bot conectado al gateway.
- Los canales de «AL DÍA» y de «RESUMEN POR GÉNERO» son de anuncios: otros servidores pueden seguirlos.
- La invitación de la web es permanente y lleva a la bienvenida.

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
  - Descripción con las palabras clave «novedades editoriales», «resumen diario», «próximos lanzamientos» y «por género».
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
