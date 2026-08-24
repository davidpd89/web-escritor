/* V1 shell loader + LRB-inspired header enhancement.
   The original production shell is preserved byte-for-byte as
   /assets/v1-shell-base.js; this file loads it first, then adds the new
   header behaviour without duplicating the existing dialog/assistant logic. */
(() => {
  'use strict';

  const BASE_SRC = '/assets/v1-shell-base.js';
  const root = document.documentElement;

  const houseSvg = `
    <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
      <path d="M3.5 10.5 12 3.7l8.5 6.8"/>
      <path d="M5.5 9.2V20h13V9.2"/>
      <path d="M9.5 20v-6h5v6"/>
    </svg>`;

  const chevronSvg = `
    <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false">
      <path d="m4 6 4 4 4-4"/>
    </svg>`;

  const submenuData = {
    'works-hub': [
      ['/libros/', 'Todas las obras'],
      ['/las-manecillas-del-recuerdo/', 'Las manecillas del recuerdo'],
      ['/libros/samuel-entre-mundos/', 'Samuel entre mundos']
    ],
    author: [
      ['/autor.html', 'Sobre David Porto Díaz'],
      ['/premios.html', 'Premios y reconocimientos'],
      ['/eventos.html', 'Eventos y firmas'],
      ['/prensa.html', 'Prensa y kit de prensa']
    ],
    'notebook-hub': [
      ['/cuaderno/', 'Todos los artículos'],
      ['/cuaderno/temas/', 'Temas'],
      ['/recomendaciones/', 'Lecturas y recomendaciones']
    ],
    'tools-hub': [
      ['/herramientas/', 'Todas las herramientas'],
      ['/herramientas/manuscrito/', 'Analizador de manuscrito'],
      ['/herramientas/dialogo/', 'Medidor de diálogo'],
      ['/herramientas/repeticiones/', 'Detector de repeticiones']
    ],
    press: [
      ['/prensa.html', 'Prensa y materiales'],
      ['/eventos.html', 'Agenda de eventos'],
      ['/premios.html', 'Premios y reconocimientos']
    ]
  };

  function emit(name, detail = {}) {
    document.dispatchEvent(new CustomEvent('dp:analytics', {
      detail: { event: name, ...detail }
    }));
  }

  function enhanceUtilityHeader() {
    document.querySelectorAll('.site-header__inner').forEach((inner) => {
      if (inner.dataset.lrbEnhanced === 'true') return;
      const assistant = inner.querySelector('.header-search');
      const actions = inner.querySelector('.site-header__actions');
      const menu = actions?.querySelector('.explore-trigger');
      if (!assistant || !actions || !menu) return;

      const left = document.createElement('div');
      left.className = 'site-header__left';
      assistant.before(left);
      left.append(assistant);

      const home = document.createElement('a');
      home.className = 'header-home';
      home.href = '/';
      home.setAttribute('aria-label', 'Volver a inicio');
      home.title = 'Inicio';
      home.innerHTML = houseSvg;
      left.append(home, menu);

      home.addEventListener('click', () => emit('header_home_click'));
      menu.addEventListener('click', () => emit('header_menu_click', { side: 'left' }));
      inner.dataset.lrbEnhanced = 'true';
    });
  }

  function tryMastheadLogo(name) {
    if (!name || name.querySelector('.masthead__logo-image')) return;
    const originalText = name.textContent.trim() || 'David Porto Díaz';
    name.textContent = '';
    const text = document.createElement('span');
    text.className = 'masthead__name-text';
    text.textContent = originalText;
    name.append(text);

    /* The exact user-supplied binary is local and is intentionally not
       fabricated here. Once it is versioned with this canonical filename,
       the masthead switches to it automatically; a failed request leaves the
       accessible text fallback visible instead of a broken-image icon. */
    const candidates = [
      '/assets/london-david-porto-logo-central.png',
      '/assets/london-david-porto-logo-central.webp'
    ];
    let index = 0;
    const probe = () => {
      if (index >= candidates.length) {
        root.dataset.lrbLogoAsset = 'missing';
        return;
      }
      const src = candidates[index++];
      const image = new Image();
      image.className = 'masthead__logo-image';
      image.alt = '';
      image.decoding = 'async';
      image.addEventListener('load', () => {
        name.append(image);
        name.classList.add('has-logo-image');
        root.dataset.lrbLogoAsset = 'loaded';
      }, { once: true });
      image.addEventListener('error', probe, { once: true });
      image.src = src;
    };
    probe();
  }

  function closeSubmenus(except = null) {
    document.querySelectorAll('.masthead-nav__item.is-open').forEach((item) => {
      if (item === except) return;
      item.classList.remove('is-open');
      item.querySelector('.masthead-nav__submenu-trigger')?.setAttribute('aria-expanded', 'false');
    });
  }

  function enhanceMastheadNav(nav) {
    if (!nav || nav.dataset.lrbEnhanced === 'true') return;
    const list = nav.querySelector('.masthead-nav__list');
    if (!list) return;

    list.querySelectorAll(':scope > li').forEach((li, position) => {
      const anchor = li.querySelector(':scope > a[data-territory]');
      if (!anchor) return;
      const key = anchor.dataset.territory;
      const entries = submenuData[key];
      li.classList.add('masthead-nav__item');
      if (!entries?.length) return;

      const id = `masthead-submenu-${key}`;
      const trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'masthead-nav__submenu-trigger';
      trigger.setAttribute('aria-label', `Ver opciones de ${anchor.textContent.trim()}`);
      trigger.setAttribute('aria-expanded', 'false');
      trigger.setAttribute('aria-controls', id);
      trigger.innerHTML = chevronSvg;

      const submenu = document.createElement('div');
      submenu.className = 'masthead-nav__submenu';
      submenu.id = id;
      submenu.setAttribute('aria-label', `Opciones de ${anchor.textContent.trim()}`);
      entries.forEach(([href, label]) => {
        const link = document.createElement('a');
        link.href = href;
        link.textContent = label;
        submenu.append(link);
      });

      anchor.after(trigger);
      li.append(submenu);

      trigger.addEventListener('click', (event) => {
        event.stopPropagation();
        const willOpen = !li.classList.contains('is-open');
        closeSubmenus(willOpen ? li : null);
        li.classList.toggle('is-open', willOpen);
        trigger.setAttribute('aria-expanded', String(willOpen));
        if (willOpen) emit('masthead_submenu_open', { territory: key, position: position + 1 });
      });

      li.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape') return;
        li.classList.remove('is-open');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.focus({ preventScroll: true });
      });
    });

    nav.dataset.lrbEnhanced = 'true';
  }

  function enhanceHomeMasthead() {
    const masthead = document.querySelector('.masthead');
    const nav = document.querySelector('.masthead-nav');
    if (!masthead || !nav) {
      root.dataset.lrbHome = 'false';
      return;
    }

    root.dataset.lrbHome = 'true';
    tryMastheadLogo(masthead.querySelector('.masthead__name'));
    enhanceMastheadNav(nav);

    if (!masthead.closest('.masthead-sticky')) {
      const sticky = document.createElement('div');
      sticky.className = 'masthead-sticky';
      const inner = document.createElement('div');
      inner.className = 'masthead-sticky__inner';
      masthead.before(sticky);
      sticky.append(inner);
      inner.append(masthead, nav);
    }

    const sticky = document.querySelector('.masthead-sticky');
    let compactAt = 170;
    const measure = () => {
      compactAt = Math.max(140, Math.min(230, Math.round((sticky?.offsetHeight || 160) + 20)));
    };
    const update = () => {
      const compact = window.scrollY > compactAt;
      root.classList.toggle('lrb-compact', compact);
      if (compact) closeSubmenus();
    };
    measure();
    update();
    addEventListener('resize', () => { measure(); update(); }, { passive: true });
    addEventListener('scroll', update, { passive: true });
  }

  function initLrbHeaderV2() {
    enhanceUtilityHeader();
    enhanceHomeMasthead();
    document.addEventListener('click', (event) => {
      if (!event.target.closest('.masthead-nav__item')) closeSubmenus();
    });
  }

  const base = document.createElement('script');
  base.src = BASE_SRC;
  base.async = false;
  base.dataset.shellBase = 'true';
  base.addEventListener('load', initLrbHeaderV2, { once: true });
  base.addEventListener('error', initLrbHeaderV2, { once: true });
  document.head.append(base);
})();
