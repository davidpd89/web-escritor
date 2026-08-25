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
  const SAMUEL_AMAZON_URL = 'https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21';
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

  function createBanner(config) {
    const section = make('section', `feature-banner feature-banner--${config.key}`);
    section.setAttribute('aria-labelledby', `feature-banner-${config.key}`);
    section.dataset.bannerKey = config.key;
    if (config.imageOnly) section.classList.add('feature-banner--image-only');

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
    loadFirstImage(media, bannerAssets[config.key], { eager: config.key === 'manecillas' });
    return section;
  }

  function createCard(config) {
    const article = make('article', `editorial-card${config.lead ? ' editorial-card--lead' : ''}${config.tone ? ` editorial-card--${config.tone}` : ''}`);
    if (config.key) article.dataset.cardKey = config.key;

    if (config.media) {
      const media = make('a', 'editorial-card__media');
      media.href = config.href;
      media.setAttribute('aria-hidden', 'true');
      media.tabIndex = -1;
      const image = new Image();
      image.src = config.media;
      image.alt = '';
      image.loading = 'lazy';
      image.decoding = 'async';
      media.append(image);
      article.append(media);
    }

    const body = make('div', config.lead ? 'editorial-card__body' : '');
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
    if (config.text) article.append(make('p', 'editorial-card__text', config.text));

    if (config.form) {
      const form = make('form', 'newsletter__form editorial-mini-form');
      form.id = 'newsletter-form-home-manecillas-card';
      form.noValidate = true;
      form.dataset.newsletterSource = 'manecillas';
      const label = make('label', 'sr-only', 'Email para novedades');
      label.htmlFor = 'home-manecillas-card-email';
      const input = make('input', 'form-input');
      input.id = 'home-manecillas-card-email';
      input.name = 'email';
      input.type = 'email';
      input.inputMode = 'email';
      input.autocomplete = 'email';
      input.placeholder = 'tu@email.com';
      input.required = true;
      input.setAttribute('aria-describedby', 'home-manecillas-card-status');
      const button = make('button', 'install-web__button', 'Suscribirme');
      button.type = 'submit';
      const consent = make('label', 'form-consent editorial-mini-form__consent');
      consent.htmlFor = 'home-manecillas-card-gdpr';
      const checkbox = make('input');
      checkbox.id = 'home-manecillas-card-gdpr';
      checkbox.name = 'consent';
      checkbox.type = 'checkbox';
      checkbox.required = true;
      checkbox.setAttribute('aria-describedby', 'home-manecillas-card-status');
      const consentText = make('span');
      consentText.innerHTML = 'Acepto recibir novedades. <a href="/privacidad.html">Privacidad</a>.';
      consent.append(checkbox, consentText);
      const status = make('p', 'newsletter-status');
      status.id = 'home-manecillas-card-status';
      status.setAttribute('role', 'status');
      status.setAttribute('aria-live', 'polite');
      form.append(label, input, button, consent, status);
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
      arrowInner.textContent = 'â†’';
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
    addTextLink(head, '/eventos.html', 'Ver agenda completa →', 'editorial-cluster__all');

    const events = [
      ['2026-06-10', '10 junio 2026', 'Feria del Libro de Madrid', 'Firma de Samuel entre mundos en el Parque del Retiro, caseta 337.'],
      ['2026-05-23', '23 mayo 2026', 'Feria del Libro de Aranjuez', 'Firma de Samuel entre mundos en la Plaza de la Constitución.'],
      ['2026-01-31', '31 enero 2026', 'Presentación en La Vecinal', 'Encuentro con lectores, coloquio y firma de ejemplares en Madrid.'],
      ['2026-01-15', '15 enero 2026', 'Presentación oficial de Samuel entre mundos', 'Presentación del debut de David Porto Díaz en Bar Aleatorio, Madrid.']
    ];
    const grid = make('div', 'home-events__grid');
    events.forEach(([datetime, date, eventTitle, text]) => {
      const item = make('article', 'home-event');
      const time = make('time', '', date);
      time.dateTime = datetime;
      item.append(time, make('h3', '', eventTitle), make('p', '', text));
      grid.append(item);
    });

    const cta = make('div', 'home-events__cta');
    const ctaCopy = make('div');
    ctaCopy.append(make('h3', '', '¿Quieres organizar una presentación, firma o club de lectura?'));
    ctaCopy.append(make('p', '', 'Para librerías, ferias, centros culturales, institutos y clubes de lectura.'));
    cta.append(ctaCopy);
    const mail = addTextLink(cta, 'mailto:davidportodiaz@gmail.com?subject=Solicitud%20de%20presentaci%C3%B3n%20%E2%80%94%20David%20Porto%20D%C3%ADaz', 'Escribir →');
    mail.addEventListener('click', () => emit('home_event_contact_click'));

    section.append(head, grid, cta);
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
    copy.append(make('p', '', 'Instala davidportodiaz.com en tu pantalla de inicio para abrir la web como una aplicación, sin perder el acceso normal desde el navegador.'));

    const panel = make('div', 'install-web__panel');
    const button = make('button', 'install-web__button', 'Instalar web');
    button.type = 'button';
    button.dataset.installWeb = 'true';
    const status = make('p', 'install-web__status', 'Si tu navegador admite instalación, aparecerá el diálogo nativo.');
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
        status.textContent = 'Disponible para instalar en este dispositivo.';
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

      const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
      status.textContent = isIos
        ? 'En iPhone o iPad: Compartir → Añadir a pantalla de inicio.'
        : 'Abre el menú del navegador y elige “Instalar aplicación” o “Añadir a pantalla de inicio” si aparece disponible.';
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

  function buildFlow() {
    if (!isHome() || root.dataset.homeEditorialV3 === 'true') return;
    const river = document.querySelector('.river-grid');
    if (!river) return;

    const flow = make('div', 'editorial-home-flow');
    flow.dataset.editorialHomeFlow = 'true';

    flow.append(createBanner({
      key: 'manecillas',
      eyebrow: 'Lanzamiento · 3 septiembre 2026',
      title: 'Las manecillas del recuerdo',
      deck: 'Una novela coral de vidas conectadas por un reloj que cambia de significado en cada mano.',
      href: SAMUEL_AMAZON_URL,
      cta: 'Comprar en Amazon',
      imageOnly: true
    }));

    flow.append(createCluster({
      key: 'manecillas',
      eyebrow: 'Obra actual',
      title: 'Las manecillas del recuerdo',
      allHref: '/las-manecillas-del-recuerdo/',
      allLabel: 'Ver la obra →',
      layout: 'book-actions',
      cards: [
        {
          key: 'manecillas-book', media: '/assets/manecillas-del-recuerdo-3d-transparent.png',
          eyebrow: 'Monza Ediciones', title: 'La nueva novela de David Porto Díaz',
          meta: '3 septiembre 2026', text: 'Ficha, publicación, fragmentos y materiales de la obra.',
          href: '/las-manecillas-del-recuerdo/'
        },
        {
          key: 'manecillas-author', tone: 'blue', eyebrow: 'Autor', title: 'David Porto Díaz',
          meta: 'Biografía · materiales · contacto', text: 'Trayectoria, fotografías y recursos para lectores, librerías y medios.',
          href: '/prensa.html'
        },
        {
          type: 'action', key: 'manecillas-buy', tone: 'sage', eyebrow: 'Comprar', title: 'Comprar en Amazon',
          text: 'Enlace temporal hasta tener destino comercial definitivo de la novela.',
          href: SAMUEL_AMAZON_URL
        },
        {
          type: 'action', key: 'manecillas-subscribe', tone: 'blush', eyebrow: 'Novedades', title: 'Suscribirte',
          text: 'Deja tu email y recibe avisos de publicación, presentaciones y materiales nuevos.',
          form: true
        },
        {
          type: 'action', key: 'manecillas-email', eyebrow: 'Te leo', title: 'Escríbeme',
          text: 'Para lectores, librerías, prensa o clubes de lectura.',
          href: AUTHOR_EMAIL_URL
        }
      ]
    }));

    flow.append(createBanner({
      key: 'samuel',
      eyebrow: 'Primera novela publicada',
      title: 'Samuel entre mundos',
      deck: 'Noveris, portales, canalizadores y una magia que siempre exige un precio.',
      href: SAMUEL_AMAZON_URL,
      cta: 'Comprar en Amazon',
      imageOnly: true
    }));

    flow.append(createCluster({
      key: 'samuel',
      eyebrow: 'Universo publicado',
      title: 'Samuel entre mundos',
      allHref: '/libros/samuel-entre-mundos/',
      allLabel: 'Ver el libro →',
      cards: [
        {
          key: 'samuel-book', lead: true, media: '/assets/samuel_entre_mundos_3d.webp',
          eyebrow: 'Libros Indie', title: 'Samuel entre mundos', meta: '422 páginas · fantasía juvenil',
          text: 'Una ciudad atravesada por fisuras entre dimensiones y un niño que descubre que su existencia podría estar en el centro de todo.',
          href: '/libros/samuel-entre-mundos/'
        },
        {
          key: 'samuel-portal', eyebrow: 'Del cuaderno', title: '¿Qué es el portal fantasy?',
          meta: 'Guía para lectores', text: 'Puertas, grietas y objetos que conectan nuestro mundo con otros.',
          href: '/cuaderno/que-es-el-portal-fantasy/'
        },
        {
          key: 'samuel-feria', tone: 'sage', eyebrow: 'Crónica', title: 'Samuel en la Feria del Libro de Madrid',
          meta: '10 junio 2026', text: 'Firma de ejemplares en el Parque del Retiro, caseta 337.',
          href: '/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/'
        }
      ]
    }));

    flow.append(createInterlude());

    flow.append(createBanner({
      key: 'memoria',
      eyebrow: 'Relato · Antología',
      title: 'La memoria de las tierras del norte',
      deck: 'Un relato de David Porto Díaz dentro de una antología de fantasía publicada por Diversidad Literaria.',
      href: 'https://www.diversidadliteraria.com/la-memoria-de-las-tierras-del-norte',
      cta: 'Conocer el relato →'
    }));

    flow.append(createCluster({
      key: 'memoria',
      eyebrow: 'Otras historias',
      title: 'La memoria de las tierras del norte',
      allHref: '/libros/',
      allLabel: 'Ver todas las obras →',
      cards: [
        {
          key: 'memoria-main', lead: true, eyebrow: 'Antología colaborativa', title: 'La memoria de las tierras del norte',
          meta: 'Diversidad Literaria', text: 'Relato de David Porto Díaz publicado en una antología de fantasía.',
          href: 'https://www.diversidadliteraria.com/la-memoria-de-las-tierras-del-norte'
        },
        {
          key: 'memoria-works', eyebrow: 'Biblioteca', title: 'Todas las obras', meta: 'Novelas · relatos',
          text: 'Un acceso único a los libros y textos publicados de David Porto Díaz.', href: '/libros/'
        },
        {
          key: 'memoria-author', tone: 'blush', eyebrow: 'Autor', title: 'Trayectoria y reconocimientos',
          meta: 'Biografía · premios', text: 'El recorrido del autor, sus publicaciones y reconocimientos literarios.', href: '/autor.html'
        }
      ]
    }));

    flow.append(createBanner({
      key: 'tools',
      eyebrow: 'Recursos gratuitos',
      title: 'Herramientas para escritores',
      deck: 'Utilidades para revisar manuscritos, detectar repeticiones, medir diálogo y preparar mejor un texto.',
      href: '/herramientas/',
      cta: 'Explorar herramientas →'
    }));

    flow.append(createCluster({
      key: 'tools',
      eyebrow: 'Para escribir y revisar',
      title: 'Herramientas gratuitas',
      allHref: '/herramientas/',
      allLabel: 'Ver todas →',
      cards: [
        {
          key: 'tools-hub', lead: true, eyebrow: 'Hub', title: 'Revisa tu texto con herramientas concretas',
          meta: 'Sin registro', text: 'Un espacio para detectar problemas medibles sin convertir la escritura en una plantilla.',
          href: '/herramientas/'
        },
        {
          key: 'tools-manuscript', eyebrow: 'Manuscrito', title: 'Analizador de manuscrito',
          meta: 'Diagnóstico rápido', text: 'Comprueba señales útiles antes de una revisión más profunda.', href: '/herramientas/manuscrito/'
        },
        {
          key: 'tools-repetition', tone: 'blue', eyebrow: 'Estilo', title: 'Repeticiones y diálogo',
          meta: 'Dos comprobaciones frecuentes', text: 'Localiza repeticiones y revisa el equilibrio de diálogo desde la propia web.', href: '/herramientas/repeticiones/'
        }
      ]
    }));

    flow.append(createEvents());
    flow.append(createInstallBlock());

    river.before(flow);
    const promo = document.querySelector('.promo-band');
    river.remove();
    promo?.remove();
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

