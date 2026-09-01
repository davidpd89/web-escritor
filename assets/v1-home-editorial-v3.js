/* Home editorial flow v3.
   Progressive enhancement: without JS the existing Home remains intact.
   With JS, the existing river/promo content is reorganised into a repeated
   MUBI-banner + LRB-reading-cluster rhythm, plus events, install and back-top. */
(() => {
  'use strict';

  const root = document.documentElement;
  const isHome = () => root.dataset.lrbHome === 'true' || Boolean(document.querySelector('.masthead-nav'));

  const bannerAssets = {
    manecillas: [
      '/assets/banners/manecillas-home-banner-final.png',
      '/assets/banners/manecillas-home-banner.webp',
      '/assets/banners/manecillas-home-banner.jpg',
      '/assets/og-manecillas.webp'
    ],
    samuel: [
      '/assets/banners/samuel-home-banner-final.png',
      '/assets/banners/samuel-home-banner.webp',
      '/assets/banners/samuel-home-banner.jpg',
      '/assets/samuel_entre_mundos_3d.webp'
    ],
    memoria: [
      '/assets/banners/memoria-tierras-norte-home-background.png',
      '/assets/banners/memoria-tierras-norte-home-banner.webp',
      '/assets/banners/memoria-tierras-norte-home-banner.jpg',
      '/assets/la-memoria-de-las-tierras-del-norte-libro.jpg'
    ],
    tools: [
      '/assets/banners/herramientas-home-banner.webp',
      '/assets/banners/herramientas-home-banner.jpg',
      '/assets/manuscrito-herramientas-placeholder.webp'
    ]
  };
  const artDirectedBannerExtensions = {
    manecillas: 'png',
    samuel: 'png',
    memoria: 'webp',
    tools: 'webp'
  };
  const SAMUEL_AMAZON_URL = 'https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21';
  // PREPUBLICACIÓN: Manecillas reutiliza provisionalmente el destino de Samuel
  // hasta que editorial-facts.json tenga purchaseUrl real. Mantener una constante
  // distinta evita que el placeholder parezca una relación semántica entre obras.
  const MANECILLAS_BUY_URL = SAMUEL_AMAZON_URL;
  const AUTHOR_EMAIL_URL = 'mailto:davidportodiaz@gmail.com?subject=Te%20leo%20%E2%80%94%20David%20Porto%20D%C3%ADaz';

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

  function addTextLink(parent, href, text, className = '') {
    const link = make('a', className, text);
    link.href = href;
    if (/^https?:\/\//.test(href)) {
      link.target = '_blank';
      // Amazon Associates tag=... is an affiliate link (K.3): needs
      // sponsored/nofollow, not just noopener/noreferrer. Scoped to Amazon
      // hosts so an unrelated future ?tag= param on another domain isn't
      // misclassified as affiliate.
      const isAmazonAffiliate = /^https?:\/\/([^/]+\.)?amazon\.[a-z.]+\//i.test(href) && /[?&]tag=/.test(href);
      link.rel = isAmazonAffiliate ? 'sponsored nofollow noopener noreferrer' : 'noopener noreferrer';
    }
    parent.append(link);
    return link;
  }

  function loadFirstImage(container, candidates, { eager = false } = {}) {
    if (!container || !candidates?.length) return;
    let index = 0;
    const next = () => {
      if (index >= candidates.length) {
        container.closest('.feature-banner')?.classList.add('feature-banner--asset-missing');
        return;
      }
      const src = candidates[index++];
      const probe = new Image();
      probe.decoding = 'async';
      probe.alt = '';
      // This probe is a detached Image() -- native loading="lazy" needs the
      // element connected to the DOM to compute viewport intersection, so it
      // would never fire and the banner would sit "pendiente" forever.
      // fetchPriority is still meaningful for a detached fetch, so that part
      // of the eager/lazy distinction is kept.
      probe.fetchPriority = eager ? 'high' : 'low';
      probe.addEventListener('load', () => {
        probe.className = 'feature-banner__image';
        container.append(probe);
        container.closest('.feature-banner')?.classList.add('feature-banner--asset-loaded');
      }, { once: true });
      probe.addEventListener('error', next, { once: true });
      probe.src = src;
    };
    next();
  }

  function applyBannerArtDirection(section, config) {
    if (!section || !config?.imageOnly) return;
    const base = config.artBase || `${config.key}-home-banner`;
    const ext = config.artExt || artDirectedBannerExtensions[config.key] || 'webp';
    section.style.setProperty('--feature-banner-desktop-image', `url("/assets/banners/${base}-desktop.${ext}")`);
    section.style.setProperty('--feature-banner-mobile-image', `url("/assets/banners/${base}-mobile.${ext}")`);
  }

  function createBanner(config) {
    const section = make('section', `feature-banner feature-banner--${config.key}`);
    section.setAttribute('aria-labelledby', `feature-banner-${config.key}`);
    section.dataset.bannerKey = config.key;
    if (config.imageOnly) section.classList.add('feature-banner--image-only');
    applyBannerArtDirection(section, config);

    const media = make('div', 'feature-banner__media');
    media.setAttribute('aria-hidden', 'true');
    if (config.imageOnly) {
      const title = make('h2', 'sr-only', config.title);
      title.id = `feature-banner-${config.key}`;
      const link = make('a', 'feature-banner__image-link');
      link.href = config.href;
      if (/^https?:\/\//.test(config.href)) {
        link.target = '_blank';
        link.rel = 'sponsored nofollow noopener noreferrer';
      }
      link.setAttribute('aria-label', config.cta || config.title);
      link.append(media);
      link.addEventListener('click', () => emit('home_banner_click', { banner: config.key }));
      section.append(title, link);
      loadFirstImage(media, bannerAssets[config.key], { eager: config.key === 'manecillas' });
      return section;
    }
    const inner = make('div', 'feature-banner__inner');
    const copy = make('div', 'feature-banner__copy');
    const eyebrow = make('p', 'feature-banner__eyebrow', config.eyebrow);
    const title = make('h2', '', config.title);
    title.id = `feature-banner-${config.key}`;
    const deck = make('p', 'feature-banner__deck', config.deck);
    const link = addTextLink(copy, config.href, config.cta, 'feature-banner__link');
    link.addEventListener('click', () => emit('home_banner_click', { banner: config.key }));

    copy.prepend(eyebrow, title, deck);
    inner.append(copy);
    section.append(media, inner);
    if (config.cssBackground) {
      section.classList.add('feature-banner--final-asset');
    } else {
      loadFirstImage(media, bannerAssets[config.key], { eager: config.key === 'manecillas' });
    }
    return section;
  }

  function createCard(config) {
    const article = make('article', `editorial-card${config.lead ? ' editorial-card--lead' : ''}${config.tone ? ` editorial-card--${config.tone}` : ''}`);
    if (config.key) article.dataset.cardKey = config.key;

    if (config.media) {
      const media = make('a', 'editorial-card__media');
      media.href = config.href;
      media.setAttribute('aria-label', config.title);
      media.tabIndex = -1;
      const image = new Image();
      image.src = config.media;
      image.alt = config.title || '';
      image.loading = config.loading || 'eager';
      image.decoding = 'async';
      media.append(image);
      article.append(media);
    }

    const body = make('div', 'editorial-card__body');
    if (config.eyebrow) body.append(make('p', 'editorial-card__eyebrow', config.eyebrow));
    const heading = make('h3');
    addTextLink(heading, config.href, config.title);
    body.append(heading);
    if (config.meta) body.append(make('p', 'editorial-card__meta', config.meta));
    if (config.text) body.append(make('p', 'editorial-card__text', config.text));

    const arrow = make('a', 'editorial-card__arrow');
    arrow.href = config.href;
    arrow.setAttribute('aria-label', `Abrir ${config.title}`);
    const arrowInner = make('span');
    arrowInner.textContent = '→';
    arrow.append(arrowInner);
    arrow.addEventListener('click', () => emit('home_editorial_card_click', { key: config.key || config.title }));
    body.append(arrow);
    article.append(body);
    return article;
  }

  function createActionCard(config) {
    const article = make('article', `editorial-card editorial-card--action${config.tone ? ` editorial-card--${config.tone}` : ''}`);
    if (config.key) article.dataset.cardKey = config.key;
    if (config.eyebrow) article.append(make('p', 'editorial-card__eyebrow', config.eyebrow));

    const heading = make('h3');
    if (config.href) {
      const link = addTextLink(heading, config.href, config.title);
      if (/^https?:\/\//.test(config.href)) {
        link.target = '_blank';
        link.rel = 'sponsored nofollow noopener noreferrer';
      }
    } else {
      heading.textContent = config.title;
    }
    article.append(heading);
    if (config.emailParts) {
      const text = make('p', 'editorial-card__text editorial-card__email');
      config.emailParts.forEach((part) => text.append(make('span', '', part)));
      article.append(text);
    } else if (config.text) {
      article.append(make('p', 'editorial-card__text', config.text));
    }

    if (config.form) {
      const form = make('form', 'newsletter__form editorial-mini-form');
      const formId = config.key || 'home-card';
      form.id = `newsletter-form-home-${formId}`;
      form.noValidate = true;
      form.dataset.newsletterSource = config.newsletterSource || 'manecillas';
      const label = make('label', 'sr-only', config.inputLabel || 'Email');
      label.htmlFor = `home-${formId}-email`;
      const input = make('input', 'form-input');
      input.id = `home-${formId}-email`;
      input.name = 'email';
      input.type = 'email';
      input.inputMode = 'email';
      input.autocomplete = 'email';
      input.placeholder = 'tu@email.com';
      input.required = true;
      input.setAttribute('aria-describedby', `home-${formId}-status`);
      const button = make('button', 'install-web__button', config.formCta || 'Recibir novedades');
      button.type = 'submit';
      const status = make('p', 'newsletter-status');
      status.id = `home-${formId}-status`;
      status.setAttribute('role', 'status');
      status.setAttribute('aria-live', 'polite');
      form.append(label, input, button, status);
      article.append(form);
    }

    if (config.href) {
      const arrow = make('a', 'editorial-card__arrow');
      arrow.href = config.href;
      arrow.setAttribute('aria-label', `Abrir ${config.title}`);
      if (/^https?:\/\//.test(config.href)) {
        arrow.target = '_blank';
        arrow.rel = 'sponsored nofollow noopener noreferrer';
      }
      const arrowInner = make('span');
      arrowInner.textContent = '→';
      arrow.append(arrowInner);
      article.append(arrow);
    }
    return article;
  }

  function createCluster(config) {
    const section = make('section', 'editorial-cluster');
    section.setAttribute('aria-labelledby', `cluster-${config.key}`);
    section.dataset.cluster = config.key;

    const head = make('div', 'editorial-cluster__head');
    const titleWrap = make('div');
    if (config.eyebrow) titleWrap.append(make('p', 'editorial-card__eyebrow', config.eyebrow));
    const title = make('h2', '', config.title);
    title.id = `cluster-${config.key}`;
    titleWrap.append(title);
    head.append(titleWrap);
    if (config.allHref && config.allLabel) addTextLink(head, config.allHref, config.allLabel, 'editorial-cluster__all');

    const grid = make('div', 'editorial-cluster__grid');
    if (config.layout) grid.dataset.layout = config.layout;
    config.cards.forEach((card) => grid.append(card.type === 'action' ? createActionCard(card) : createCard(card)));
    section.append(head, grid);
    return section;
  }

  function createInterlude() {
    const band = make('aside', 'editorial-interlude');
    band.setAttribute('aria-labelledby', 'home-interlude-title');
    band.append(make('p', 'editorial-interlude__label', 'El cuaderno'));
    const title = make('h2', '', 'Detrás de las historias: lectura, escritura y proceso editorial.');
    title.id = 'home-interlude-title';
    band.append(title);
    const link = addTextLink(band, '/cuaderno/', 'Entrar en el cuaderno →');
    link.addEventListener('click', () => emit('home_interlude_click', { destination: 'cuaderno' }));
    return band;
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
    media.append(image);

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
      const cardHeading = make('h3');
      addTextLink(cardHeading, href, cardTitle);
      card.append(cardHeading);
      if (text) card.append(make('p', '', text));
      addTextLink(card, href, 'Abrir', 'yale-text-link yale-text-link--gradient');
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
      media.append(img);
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
      const h = make('h3');
      addTextLink(h, href, cardTitle);
      card.append(h);
      if (text) card.append(make('p', '', text));
      addTextLink(card, href, 'Abrir', 'yale-text-link');
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
    media.append(image);
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
    const consentLabel = make('label', 'form-consent');
    consentLabel.htmlFor = 'nl-gdpr-home-yale';
    const consentInput = document.createElement('input');
    consentInput.id = 'nl-gdpr-home-yale';
    consentInput.name = 'consent';
    consentInput.type = 'checkbox';
    consentInput.required = true;
    consentInput.setAttribute('aria-describedby', 'nl-status-home-yale');
    const consentText = make('span');
    const consentLink = make('a', '', 'política de privacidad');
    consentLink.href = '/privacidad.html';
    consentText.append('He leído y acepto la ', consentLink, '.');
    consentLabel.append(consentInput, consentText);
    const status = make('p', 'form-status');
    status.id = 'nl-status-home-yale';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    form.append(label, row, consentLabel, status);
    section.append(copy, form);
    return section;
  }

  function buildFlow() {
    if (!isHome() || root.dataset.homeEditorialV3 === 'true') return;
    const river = document.querySelector('.river-grid');
    if (!river) return;

    const flow = make('div', 'editorial-home-flow yale-home-flow');
    flow.dataset.editorialHomeFlow = 'true';

    flow.append(createYaleHero());
    flow.append(createYaleWorksGrid());
    flow.append(createYaleSamuelFeature());
    flow.append(createYaleToolsFeature());
    flow.append(createEvents());
    flow.append(createYaleSignupStrip());
    flow.append(createInstallBlock());
    river.before(flow);
    const yalePromo = document.querySelector('.promo-band');
    const yaleFaq = document.getElementById('faq');
    const yaleNewsletter = document.getElementById('newsletter');
    river.remove();
    yalePromo?.remove();
    yaleFaq?.remove();
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
