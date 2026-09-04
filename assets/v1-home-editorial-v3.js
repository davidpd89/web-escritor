/* Home editorial flow v3.
   Progressive enhancement: without JS the existing Home remains intact.
   With JS, the existing river/promo content is reorganised into the
   Yale-style editorial home (see createYale* below), plus events, install
   and back-top. An earlier MUBI-banner + LRB-reading-cluster rhythm was
   replaced by that redesign (commit "Apply editorial home redesign") but
   left its now-dead createBanner/createCluster/createInterlude code and
   assets/banners/* behind; both were removed as part of a later cleanup.

   Loaded as a module (assets/v1-shell.js's loadScript(..., {module:true}))
   specifically so it can import EDITORIAL_PUBLIC_FACTS below instead of
   hand-duplicating a literal that would silently drift from
   editorial-facts.json. */
import { EDITORIAL_PUBLIC_FACTS } from './editorial-public-facts.mjs';

(() => {
  'use strict';

  const root = document.documentElement;
  const isHome = () => root.dataset.lrbHome === 'true' || Boolean(document.querySelector('.masthead-nav'));

  const SAMUEL_AMAZON_URL = 'https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21';
  // 2026-09-04: Las manecillas del recuerdo now has its own real, verified
  // purchase URL (its Kindle edition) -- editorial-facts.json
  // books.lasManecillasDelRecuerdo.purchaseUrl is the single source of
  // truth, consumed here via the generated assets/editorial-public-facts.mjs
  // projection (scripts/build-public-editorial-facts.py) rather than a
  // hand-typed literal, so changing the URL in editorial-facts.json can't
  // drift from what Home's dynamically-built CTAs actually link to.
  const MANECILLAS_BUY_URL = EDITORIAL_PUBLIC_FACTS.manecillas.purchaseUrl;
  const AUTHOR_EMAIL_URL = 'mailto:davidportodiaz@gmail.com?subject=Te%20leo%20%E2%80%94%20David%20Porto%20D%C3%ADaz';

  // Explicit host allowlist (K.3): a pattern like /amazon\.[a-z.]+/ would also
  // match a lookalike host such as "amazon.evil.com". Parsing the URL and
  // checking the real hostname avoids that. amzn.to is the author's own
  // Amazon Associates short-link domain (used for MANECILLAS_BUY_URL): it
  // never carries a visible ?tag= itself (the tag lives server-side in the
  // redirect target), so it's always treated as affiliate outright, unlike
  // amazon.es/etc. links which still require an explicit tag= to qualify.
  const AMAZON_HOSTS = ['amazon.es'];
  const AMAZON_SHORTLINK_HOSTS = ['amzn.to'];
  function isAmazonAffiliateUrl(href) {
    try {
      const { hostname, protocol } = new URL(href);
      if (protocol !== 'http:' && protocol !== 'https:') return false;
      if (AMAZON_SHORTLINK_HOSTS.some((host) => hostname === host)) return true;
      const isAmazonHost = AMAZON_HOSTS.some((host) => hostname === host || hostname.endsWith(`.${host}`));
      return isAmazonHost && /[?&]tag=/.test(href);
    } catch {
      return false;
    }
  }

  const arrowSvg = `
    <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
      <path d="M12 19V5"/><path d="m6 11 6-6 6 6"/>
    </svg>`;

  function emit(name, detail = {}) {
    document.dispatchEvent(new CustomEvent('dp:analytics', {
      detail: { event: name, ...detail }
    }));
  }

  function make(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  // The corner-bracket decoration (.media-frame::before/::after) must hug
  // the image's own rendered box, not whatever larger centering container
  // it sits inside -- .yale-lead__media/.yale-tile__media/.yale-feature-
  // book__media all use display:grid+place-items to center a variable-
  // ratio image inside a fixed-height slot, which leaves real empty space
  // between the container's corners and the image's own corners. A shared
  // inline-block wrapper naturally shrinks to the image's rendered size,
  // so the brackets end up on the image, not floating in that gap
  // (2026-09-02, reported: bracket appearing detached near the hero text).
  function wrapMediaFrame(image) {
    const frame = make('span', 'media-frame');
    frame.append(image);
    return frame;
  }

  function addTextLink(parent, href, text, className = '', bookContext = '') {
    const link = make('a', className, text);
    link.href = href;
    if (/^https?:\/\//.test(href)) {
      link.target = '_blank';
      // Amazon Associates links are affiliate (K.3): need sponsored/nofollow,
      // not just noopener/noreferrer. Scoped to an explicit host allowlist
      // (not a pattern match) so a lookalike host such as amazon.evil.com
      // can't be misclassified as affiliate.
      const isAmazonAffiliate = isAmazonAffiliateUrl(href);
      link.rel = isAmazonAffiliate ? 'sponsored nofollow noopener noreferrer' : 'noopener noreferrer';
      // No visible "afiliado" text next to these CTAs (author decision,
      // 2026-09-01) -- aria-label keeps the disclosure available to
      // screen-reader users without adding visible copy. rel=sponsored
      // above is the signal search engines read; the required sitewide
      // Amazon Associates statement lives on aviso-legal.html.
      //
      // bookContext (2026-09-05): Home has two separate "Comprar en Amazon"
      // cards (Manecillas' rail card, Samuel's feature card), each with a
      // generic-text heading link AND a generic "Abrir" link -- all four
      // produced an *identical* accessible name ("Comprar en Amazon — enlace
      // de afiliado" / "Abrir — enlace de afiliado") with no book named,
      // indistinguishable out of visual context. A user scrolling fast on
      // mobile (or navigating by screen reader) could easily tap/activate
      // the wrong book's buy link while believing it was for the other --
      // plausibly what a live report of "Comprar" leading to the wrong book
      // was actually describing. Threading the book name into the
      // aria-label (not the visible label, to avoid visual/design changes)
      // disambiguates them without touching layout.
      const suffix = bookContext ? ` — ${bookContext}` : '';
      if (isAmazonAffiliate) link.setAttribute('aria-label', `${text}${suffix} — enlace de afiliado`);
    }
    parent.append(link);
    return link;
  }

  function createEvents() {
    const section = make('section', 'home-events');
    section.setAttribute('aria-labelledby', 'home-events-title');

    const head = make('div', 'home-events__head');
    const titleWrap = make('div');
    titleWrap.append(make('p', 'editorial-card__eyebrow', 'Agenda · Archivo'));
    const title = make('h2', '', 'Eventos y encuentros.');
    title.id = 'home-events-title';
    titleWrap.append(title);
    head.append(titleWrap);
    addTextLink(head, '/eventos.html', 'Ver agenda completa', 'yale-text-link');

    const wrap = make('div', 'home-events__feature');
    const lead = make('article', 'home-event home-event--lead');
    const leadMedia = make('a', 'home-event__media');
    leadMedia.href = '/eventos.html#feria-libro-madrid-2026';
    leadMedia.setAttribute('aria-label', 'Feria del Libro de Madrid');
    const leadImage = new Image();
    leadImage.src = '/assets/eventos/david-porto-diaz-lectores-feria-libro-madrid-2026-samuel.webp';
    leadImage.alt = 'David Porto Díaz sosteniendo Samuel entre mundos en su caseta de la Feria del Libro de Madrid';
    leadImage.loading = 'eager';
    leadImage.decoding = 'async';
    leadMedia.append(leadImage);
    const leadTime = make('time', '', '10 junio 2026');
    leadTime.dateTime = '2026-06-10';
    const leadTitle = make('h3');
    addTextLink(leadTitle, '/eventos.html#feria-libro-madrid-2026', 'Feria del Libro de Madrid');
    lead.append(leadMedia, leadTime, leadTitle, make('p', '', 'Firma de Samuel entre mundos en el Parque del Retiro, caseta 337.'));
    addTextLink(lead, '/eventos.html#feria-libro-madrid-2026', 'Abrir', 'home-event__link');

    const events = [
      ['2026-05-23', '23 mayo 2026', 'Feria del Libro de Aranjuez', 'Firma de Samuel entre mundos en la Plaza de la Constitución.', '/eventos.html#feria-libro-aranjuez-2026'],
      ['2026-01-31', '31 enero 2026', 'Presentación en La Vecinal', 'Encuentro con lectores, coloquio y firma de ejemplares en Madrid.', '/eventos.html#la-vecinal-2026'],
      ['2026-01-15', '15 enero 2026', 'Presentación oficial de Samuel entre mundos', 'Presentación del debut de David Porto Díaz en Bar Aleatorio, Madrid.', '/eventos.html#bar-aleatorio-2026']
    ];
    const grid = make('div', 'home-events__grid');
    events.forEach(([datetime, date, eventTitle, text, href]) => {
      const item = make('article', 'home-event');
      const time = make('time', '', date);
      time.dateTime = datetime;
      const heading = make('h3');
      addTextLink(heading, href, eventTitle);
      item.append(time, heading, make('p', '', text));
      addTextLink(item, href, 'Abrir', 'home-event__link');
      grid.append(item);
    });
    const cta = make('div', 'home-events__cta');
    const ctaCopy = make('div');
    ctaCopy.append(make('h3', '', '¿Quieres organizar una presentación, firma o club de lectura?'));
    ctaCopy.append(make('p', '', 'Para librerías, ferias, centros culturales, institutos y clubes de lectura.'));
    cta.append(ctaCopy);
    const mail = addTextLink(cta, 'mailto:davidportodiaz@gmail.com?subject=Solicitud%20de%20presentaci%C3%B3n%20%E2%80%94%20David%20Porto%20D%C3%ADaz', 'Escribir', 'yale-text-link');
    mail.addEventListener('click', () => emit('home_event_contact_click'));
    grid.append(cta);

    wrap.append(lead, grid);
    section.append(head, wrap);
    return section;
  }

  function createInstallBlock() {
    const section = make('section', 'install-web');
    section.setAttribute('aria-labelledby', 'install-web-title');
    const copy = make('div');
    copy.append(make('p', 'editorial-card__eyebrow', 'Acceso directo'));
    const title = make('h2', '', 'Lleva la web contigo.');
    title.id = 'install-web-title';
    copy.append(title);
    copy.append(make('p', '', 'Instala davidportodiaz.com en tu pantalla de inicio para abrir la web como una aplicación.'));

    const panel = make('div', 'install-web__panel');
    const button = make('button', 'install-web__button', 'Instalar web');
    button.type = 'button';
    button.dataset.installWeb = 'true';
    const status = make('p', 'install-web__status', '');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    panel.append(button, status);
    section.append(copy, panel);

    let installPrompt = null;
    const standalone = matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
    if (standalone) {
      button.textContent = 'Web instalada';
      button.disabled = true;
      status.textContent = 'Esta web ya está abierta en modo instalado.';
    }

    window.addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault();
      installPrompt = event;
      if (!button.disabled) {
        button.textContent = 'Instalar web';
        status.textContent = '';
      }
    });

    button.addEventListener('click', async () => {
      if (installPrompt) {
        installPrompt.prompt();
        const choice = await installPrompt.userChoice.catch(() => null);
        if (choice?.outcome === 'accepted') {
          status.textContent = 'Instalación iniciada.';
          emit('home_install_accept');
        } else {
          status.textContent = 'Instalación cancelada. Puedes volver a intentarlo cuando quieras.';
          emit('home_install_dismiss');
        }
        installPrompt = null;
        return;
      }

      // No beforeinstallprompt to replay: either the browser never offered
      // one (Safari/iOS never does; Chrome/Edge withhold it after a recent
      // dismissal or once already installed), or this device doesn't meet
      // the platform's install criteria this session. No JS can force the
      // native install flow past that -- it's a browser security boundary
      // by design, the same for every PWA on the web -- so this points at
      // the closest thing to a one-click path each platform actually has.
      const ua = navigator.userAgent;
      const isIos = /iphone|ipad|ipod/i.test(ua);
      const isAndroid = /android/i.test(ua);
      const isMobile = isIos || isAndroid || /mobile/i.test(ua);
      if (isIos) {
        status.textContent = 'En iPhone o iPad: pulsa el icono Compartir (el cuadrado con la flecha) y elige "Añadir a pantalla de inicio".';
      } else if (isAndroid) {
        status.textContent = 'Si no ha aparecido un aviso para instalar, es que Chrome ya la tiene instalada o descartaste el aviso hace poco: abre el menú ⋮ (arriba a la derecha) y busca "Instalar aplicación".';
      } else if (isMobile) {
        status.textContent = 'Abre el menú del navegador y busca "Instalar aplicación" o "Añadir a pantalla de inicio".';
      } else {
        status.textContent = 'Busca el icono de instalar junto a la barra de direcciones (a la derecha, cerca de la ⭐) y haz clic ahí.';
      }
      emit('home_install_help');
    });

    window.addEventListener('appinstalled', () => {
      button.textContent = 'Web instalada';
      button.disabled = true;
      status.textContent = 'Instalación completada.';
      emit('home_install_complete');
    });

    return section;
  }

  function createBackToTop() {
    if (document.querySelector('.back-to-top')) return;
    const button = make('button', 'back-to-top');
    button.type = 'button';
    button.setAttribute('aria-label', 'Volver arriba');
    button.title = 'Volver arriba';
    button.innerHTML = arrowSvg;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => button.classList.toggle('is-visible', window.scrollY > 720);
    button.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: reduced.matches ? 'auto' : 'smooth' });
      emit('home_back_to_top');
    });
    addEventListener('scroll', update, { passive: true });
    update();
    document.body.append(button);
  }

  function createYaleHero() {
    const section = make('section', 'yale-home-issue');
    section.setAttribute('aria-labelledby', 'yale-home-title');

    const heading = make('header', 'yale-home-issue__heading');
    heading.append(make('p', 'yale-home-issue__kicker', 'Obra actual'));
    const title = make('h1', '', 'Las manecillas del recuerdo');
    title.id = 'yale-home-title';
    heading.append(title);

    const grid = make('div', 'yale-home-issue__grid');
    const lead = make('article', 'yale-lead');
    const media = make('a', 'yale-lead__media');
    media.href = '/las-manecillas-del-recuerdo/';
    media.setAttribute('aria-label', 'Las manecillas del recuerdo');
    const image = new Image();
    image.src = '/assets/manecillas-del-recuerdo-3d-transparent.png';
    image.alt = 'Portada de Las manecillas del recuerdo';
    image.loading = 'eager';
    image.decoding = 'async';
    image.fetchPriority = 'high';
    media.append(wrapMediaFrame(image));

    const copy = make('div', 'yale-lead__copy');
    copy.append(make('p', 'editorial-card__eyebrow', 'Monza Ediciones'));
    const h = make('h2');
    addTextLink(h, '/las-manecillas-del-recuerdo/', 'La nueva novela de David Porto Díaz');
    copy.append(h);
    copy.append(make('p', 'yale-lead__deck', 'Un reloj pasa de mano en mano y cambia de significado en cada vida que toca.'));
    copy.append(make('p', 'editorial-card__meta', '3 septiembre 2026 · novela coral · memoria'));
    const actions = make('div', 'yale-lead__actions');
    addTextLink(actions, '/las-manecillas-del-recuerdo/', 'Ver la obra', 'yale-text-link yale-text-link--gradient');
    addTextLink(actions, '/las-manecillas-del-recuerdo/fragmentos/', 'Leer fragmentos', 'yale-text-link yale-text-link--gradient');
    addTextLink(actions, MANECILLAS_BUY_URL, 'Comprar', 'yale-text-link yale-text-link--gradient');
    copy.append(actions);
    lead.append(media, copy);

    const rail = make('aside', 'yale-rail');
    rail.setAttribute('aria-label', 'Otros accesos destacados');
    [
      ['Autor', 'David Porto Díaz', 'Biografía, fotografías y recursos para lectores, librerías y medios.', '/autor.html'],
      ['Comunidad', 'Lectores beta', 'Sé el primero en leer contenido y opina antes de que llegue a todos.', '/lectores-beta/#quiero-ser-lector'],
      ['Comprar', 'Comprar en Amazon', '', MANECILLAS_BUY_URL],
      ['Te leo', 'Escríbeme', '', AUTHOR_EMAIL_URL]
    ].forEach(([eyebrow, cardTitle, text, href]) => {
      const card = make('article', 'yale-rail-card');
      card.append(make('p', 'editorial-card__eyebrow', eyebrow));
      const bookContext = href === MANECILLAS_BUY_URL ? 'Las manecillas del recuerdo' : '';
      const cardHeading = make('h3');
      addTextLink(cardHeading, href, cardTitle, '', bookContext);
      card.append(cardHeading);
      if (text) card.append(make('p', '', text));
      addTextLink(card, href, 'Abrir', 'yale-text-link yale-text-link--gradient', bookContext);
      rail.append(card);
    });

    grid.append(lead, rail);
    section.append(heading, grid);
    return section;
  }

  function createYaleWorksGrid() {
    const section = make('section', 'yale-home-section yale-home-section--works');
    section.setAttribute('aria-labelledby', 'yale-works-title');
    const head = make('div', 'yale-home-section__head');
    const titleWrap = make('div');
    titleWrap.append(make('p', 'editorial-card__eyebrow', 'Obras'));
    const title = make('h2', '', 'Libros y territorios.');
    title.id = 'yale-works-title';
    titleWrap.append(title);
    head.append(titleWrap);
    addTextLink(head, '/libros/', 'Todas las obras', 'yale-text-link');

    const grid = make('div', 'yale-tile-grid yale-tile-grid--works');
    [
      ['Obra actual', 'Las manecillas del recuerdo', 'Novela coral de memoria, objetos heredados y vidas conectadas.', '/las-manecillas-del-recuerdo/', '/assets/manecillas-del-recuerdo-3d-transparent.png'],
      ['Publicada', 'Samuel entre mundos', 'Fantasía juvenil española: portales, canalizadores y secretos familiares.', '/libros/samuel-entre-mundos/', '/assets/samuel_entre_mundos_3d.webp'],
      ['Antología', 'La memoria de las tierras del norte', 'Antología colaborativa de fantasía.', '/libros/#memoria-tierras-norte', '/assets/david-porto-memoria-sinfondo.webp']
    ].forEach(([eyebrow, cardTitle, text, href, src]) => {
      const card = make('article', 'yale-tile yale-tile--with-media');
      const media = make('a', 'yale-tile__media');
      media.href = href;
      media.setAttribute('aria-label', cardTitle);
      const img = new Image();
      img.src = src;
      img.alt = cardTitle;
      img.loading = 'lazy';
      img.decoding = 'async';
      media.append(wrapMediaFrame(img));
      const body = make('div', 'yale-tile__body');
      body.append(make('p', 'editorial-card__eyebrow', eyebrow));
      const h = make('h3');
      addTextLink(h, href, cardTitle);
      body.append(h, make('p', '', text));
      addTextLink(body, href, 'Abrir', 'yale-text-link');
      card.append(media, body);
      grid.append(card);
    });

    section.append(head, grid);
    return section;
  }

  function createYaleSamuelFeature() {
    const section = make('section', 'yale-home-section yale-feature yale-feature--samuel');
    section.setAttribute('aria-labelledby', 'yale-samuel-title');
    const head = make('div', 'yale-home-section__head');
    const titleWrap = make('div');
    titleWrap.append(make('p', 'editorial-card__eyebrow', 'Universo publicado'));
    const title = make('h2', '', 'Samuel entre mundos.');
    title.id = 'yale-samuel-title';
    titleWrap.append(title);
    head.append(titleWrap);
    addTextLink(head, '/libros/samuel-entre-mundos/', 'Ver el libro', 'yale-text-link');

    const grid = make('div', 'yale-feature__grid yale-feature__grid--reverse');
    const stack = make('div', 'yale-feature__stack');
    [
      ['Del cuaderno', 'Qué es el portal fantasy', 'Guía para lectores.', '/cuaderno/que-es-el-portal-fantasy/', ''],
      ['Crónica', 'Samuel en la Feria del Libro de Madrid', '10 junio 2026.', '/eventos.html#feria-libro-madrid-2026', 'yale-feature-card--blue'],
      ['Comprar', 'Comprar en Amazon', '', SAMUEL_AMAZON_URL, '']
    ].forEach(([eyebrow, cardTitle, text, href, className]) => {
      const card = make('article', `yale-feature-card ${className}`.trim());
      card.append(make('p', 'editorial-card__eyebrow', eyebrow));
      const bookContext = href === SAMUEL_AMAZON_URL ? 'Samuel entre mundos' : '';
      const h = make('h3');
      addTextLink(h, href, cardTitle, '', bookContext);
      card.append(h);
      if (text) card.append(make('p', '', text));
      addTextLink(card, href, 'Abrir', 'yale-text-link', bookContext);
      stack.append(card);
    });

    const book = make('article', 'yale-feature-book');
    const media = make('a', 'yale-feature-book__media');
    media.href = '/libros/samuel-entre-mundos/';
    media.setAttribute('aria-label', 'Samuel entre mundos');
    const image = new Image();
    image.src = '/assets/samuel_entre_mundos_3d.webp';
    image.alt = 'Portada de Samuel entre mundos';
    image.loading = 'eager';
    image.decoding = 'async';
    media.append(wrapMediaFrame(image));
    const body = make('div', 'yale-feature-book__body');
    body.append(make('p', 'editorial-card__eyebrow', 'Libros Indie'));
    const h = make('h3');
    addTextLink(h, '/libros/samuel-entre-mundos/', 'Samuel entre mundos');
    body.append(h);
    body.append(make('p', 'editorial-card__meta', '422 páginas · fantasía juvenil'));
    body.append(make('p', '', 'Una ciudad atravesada por fisuras entre dimensiones y un niño que descubre que su existencia podría estar en el centro de todo.'));
    addTextLink(body, '/libros/samuel-entre-mundos/', 'Abrir', 'yale-text-link');
    book.append(media, body);

    grid.append(stack, book);
    section.append(head, grid);
    return section;
  }

  function createYaleToolsFeature() {
    const section = make('section', 'yale-home-section yale-home-section--tools');
    section.setAttribute('aria-labelledby', 'yale-tools-title');
    const head = make('div', 'yale-home-section__head');
    const titleWrap = make('div');
    titleWrap.append(make('p', 'editorial-card__eyebrow', 'Para escribir'));
    const title = make('h2', '', 'Herramientas gratuitas.');
    title.id = 'yale-tools-title';
    titleWrap.append(title);
    head.append(titleWrap);
    addTextLink(head, '/herramientas/', 'Todas las herramientas', 'yale-text-link');

    const grid = make('div', 'yale-tile-grid yale-tile-grid--tools');
    [
      ['Hub', 'Recursos gratuitos', 'Utilidades para revisar textos, preparar materiales y trabajar una obra desde el navegador.', '/herramientas/', ''],
      ['Lectores beta', 'Tengo un manuscrito y me gustarían opiniones de lectores beta', 'Un punto de entrada para autores que buscan primeras lecturas antes de mover el texto.', '/lectores-beta/#enviar-manuscrito', 'yale-tile--blue'],
      ['Manuscrito', 'Analizador de manuscrito', 'Una herramienta para ordenar capítulos, detectar señales del texto y revisar estructura.', '/herramientas/manuscrito/', '']
    ].forEach(([eyebrow, cardTitle, text, href, className]) => {
      const card = make('article', `yale-tile ${className}`.trim());
      card.append(make('p', 'editorial-card__eyebrow', eyebrow));
      const h = make('h3');
      addTextLink(h, href, cardTitle);
      card.append(h, make('p', '', text));
      addTextLink(card, href, 'Abrir', 'yale-text-link');
      grid.append(card);
    });

    section.append(head, grid);
    return section;
  }

  function createYaleReadingGrid() {
    const section = make('section', 'yale-home-section yale-home-section--reading');
    section.setAttribute('aria-labelledby', 'yale-reading-title');
    const head = make('div', 'yale-home-section__head');
    head.append(make('p', 'editorial-card__eyebrow', 'Leer y recursos'));
    const title = make('h2', '', 'Cuaderno, prensa y herramientas.');
    title.id = 'yale-reading-title';
    head.append(title);

    const grid = make('div', 'yale-tile-grid yale-tile-grid--reading');
    [
      ['Del cuaderno', 'Qué es el portal fantasy', 'Una guía para entender puertas, grietas y mundos conectados.', '/cuaderno/que-es-el-portal-fantasy/'],
      ['Herramientas', 'Tengo un manuscrito y quiero opiniones', 'Acceso para autores que buscan lectores beta antes de mover su texto.', '/lectores-beta/#enviar-manuscrito'],
      ['Prensa', 'Materiales para medios', 'Bio, fichas, portadas, fotos y datos verificados para entrevistas o librerías.', '/prensa.html'],
      ['Agenda', 'Eventos y encuentros', 'Firmas, ferias, presentaciones y actividades con lectores.', '/eventos.html']
    ].forEach(([eyebrow, cardTitle, text, href], index) => {
      const card = make('article', `yale-tile${index === 1 ? ' yale-tile--blue' : ''}`);
      card.append(make('p', 'editorial-card__eyebrow', eyebrow));
      const h = make('h3');
      addTextLink(h, href, cardTitle);
      card.append(h, make('p', '', text));
      addTextLink(card, href, 'Abrir', 'yale-text-link');
      grid.append(card);
    });
    section.append(head, grid);
    return section;
  }

  function createYaleSignupStrip() {
    const section = make('section', 'yale-signup');
    section.setAttribute('aria-labelledby', 'yale-signup-title');
    const copy = make('div', 'yale-signup__copy');
    copy.append(make('p', 'editorial-card__eyebrow', 'Novedades'));
    const title = make('h2', '', 'Recibe solo lo importante.');
    title.id = 'yale-signup-title';
    copy.append(title, make('p', '', 'Publicaciones, fragmentos, fechas y recursos cuando haya algo que merezca llegar al correo.'));

    const form = make('form', 'newsletter__form yale-signup__form');
    form.id = 'newsletter-form-home-yale';
    form.noValidate = true;
    form.dataset.newsletterSource = 'home';
    const label = make('label', 'sr-only', 'Email');
    label.htmlFor = 'nl-email-home-yale';
    const row = make('div', 'form-row');
    const input = make('input', 'form-input');
    input.id = 'nl-email-home-yale';
    input.name = 'email';
    input.type = 'email';
    input.autocomplete = 'email';
    input.inputMode = 'email';
    input.required = true;
    input.placeholder = 'tu@email.com';
    input.setAttribute('aria-describedby', 'nl-status-home-yale');
    const button = make('button', 'form-submit', 'Enviar');
    button.type = 'submit';
    row.append(input, button);
    const consentNote = make('p', 'yale-signup__consent-note');
    const consentLink = make('a', '', 'política de privacidad');
    consentLink.href = '/privacidad.html';
    consentNote.append('Al enviar tu email, aceptas la ', consentLink, '.');
    const status = make('p', 'form-status');
    status.id = 'nl-status-home-yale';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    form.append(label, row, consentNote, status);
    section.append(copy, form);
    return section;
  }

  function buildFlow() {
    if (!isHome() || root.dataset.homeEditorialV3 === 'true') return;
    const river = document.querySelector('.river-grid');
    if (!river) return;

    const flow = make('div', 'editorial-home-flow yale-home-flow');
    flow.dataset.editorialHomeFlow = 'true';

    // #faq holds real reader-facing content (buying options, events, press
    // contact...), not just FAQPage schema -- move it into the flow instead
    // of deleting it, so it stays visible for JS users too.
    const yaleFaq = document.getElementById('faq');

    flow.append(createYaleHero());
    flow.append(createYaleWorksGrid());
    flow.append(createYaleSamuelFeature());
    flow.append(createYaleToolsFeature());
    flow.append(createEvents());
    if (yaleFaq) flow.append(yaleFaq);
    flow.append(createYaleSignupStrip());
    flow.append(createInstallBlock());
    river.before(flow);
    const yalePromo = document.querySelector('.promo-band');
    const yaleNewsletter = document.getElementById('newsletter');
    river.remove();
    yalePromo?.remove();
    yaleNewsletter?.remove();
    root.dataset.homeEditorialV3 = 'true';
    document.dispatchEvent(new CustomEvent('dp:home-editorial-ready'));
    createBackToTop();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildFlow, { once: true });
  } else {
    buildFlow();
  }
})();
