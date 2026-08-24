// V1 editorial shell — Explorar <dialog>, header scroll state, intro and assistant.
// Base runtime + LRB-inspired header enhancement live in one production file
// so static contracts, CSP review and browser behaviour all inspect the same source.
(() => {
  'use strict';
  const q = (s, c = document) => c.querySelector(s);
  const qa = (s, c = document) => [...c.querySelectorAll(s)];

  function initHeader() {
    const header = q('[data-header]');
    if (!header) return;
    let ticking = false;
    const update = () => {
      header.dataset.scrolled = window.scrollY > 18 ? 'true' : 'false';
      ticking = false;
    };
    addEventListener('scroll', () => {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
    update();
  }

  function ensureAssistantExploreLink(dialog) {
    const list = q('.explore-list', dialog);
    if (!list || q('[data-assistant-menu-link]', list)) return;
    const link = document.createElement('a');
    link.className = 'explore-row';
    link.href = '/asistente/';
    link.dataset.preview = 'asistente';
    link.dataset.assistantMenuLink = 'true';

    const index = document.createElement('span');
    index.className = 'explore-row__index';
    index.textContent = String(qa('.explore-row__index', list).length + 1).padStart(2, '0');
    const body = document.createElement('span');
    body.className = 'explore-row__body';
    const strong = document.createElement('strong');
    strong.textContent = 'Asistente';
    const small = document.createElement('small');
    small.textContent = 'Pregunta y encuentra la página que necesitas.';
    body.append(strong, small);
    link.append(index, body);
    list.append(link);
  }

  function initExplore() {
    const dialog = q('[data-explore-dialog]');
    const opens = qa('[data-explore-open]');
    const close = q('[data-explore-close]');
    if (!dialog || !opens.length || !close || typeof dialog.showModal !== 'function') return;

    ensureAssistantExploreLink(dialog);
    let opener = null;
    opens.forEach((open) => {
      open.addEventListener('click', () => {
        opener = document.activeElement;
        opens.forEach((o) => o.setAttribute('aria-expanded', 'true'));
        dialog.showModal();
        close.focus();
      });
    });
    const markClosed = () => opens.forEach((o) => o.setAttribute('aria-expanded', 'false'));
    close.addEventListener('click', () => { markClosed(); dialog.close(); });
    dialog.addEventListener('cancel', markClosed);
    dialog.addEventListener('click', (event) => { if (event.target === dialog) { markClosed(); dialog.close(); } });
    dialog.addEventListener('close', () => {
      markClosed();
      if (opener instanceof HTMLElement) opener.focus({ preventScroll: true });
    });

    const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
    dialog.addEventListener('keydown', (event) => {
      if (event.key !== 'Tab') return;
      const items = [...dialog.querySelectorAll(FOCUSABLE)]
        .filter((el) => el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length);
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement;
      if (event.shiftKey && (active === first || active === dialog)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    });

    const preview = q('[data-explore-preview]', dialog);
    const label = q('[data-preview-label]', dialog);
    const copy = q('[data-preview-copy]', dialog);
    const media = q('[data-preview-media]', dialog);
    const content = {
      'works-hub': ['Obras', 'Las dos novelas publicadas, fragmentos y rutas de lectura.'],
      'notebook-hub': ['Cuaderno', 'Artículos y piezas editoriales sobre proceso y lecturas.'],
      'tools-hub': ['Herramientas', 'Utilidades gratuitas para problemas concretos de escritura.'],
      author: ['Autor', 'Biografía, obra y trayectoria de David Porto Díaz.'],
      press: ['Prensa', 'Material de prensa, agenda y apariciones verificables.'],
      'site-map': ['Mapa del sitio', 'Índice completo para recorrer la web por secciones.'],
      manecillas: ['Las manecillas del recuerdo', 'La obra actual y punto de entrada editorial.'],
      autor: ['Autor', 'Biografía, obra y trayectoria de David Porto Díaz.'],
      samuel: ['Samuel entre mundos', 'Primera novela publicada.'],
      cuaderno: ['Cuaderno', 'Artículos y piezas editoriales.'],
      herramientas: ['Herramientas', 'Utilidades gratuitas para problemas concretos de escritura y publicación.'],
      prensa: ['Prensa y eventos', 'Apariciones, materiales de prensa y agenda.'],
      asistente: ['Asistente', 'Pregunta y encuentra la página que necesitas.']
    };
    const setPreview = (key) => {
      if (!preview || !content[key]) return;
      label.textContent = content[key][0];
      copy.textContent = content[key][1];
      media.dataset.preview = key;
    };
    qa('[data-preview]', dialog).forEach((link) => {
      link.addEventListener('mouseenter', () => setPreview(link.dataset.preview));
      link.addEventListener('focus', () => setPreview(link.dataset.preview));
    });
  }

  function initIntro() {
    const intro = q('[data-intro]');
    if (!intro) return;
    let seen = false;
    try { seen = sessionStorage.getItem('dp-intro-seen') === '1'; } catch {}
    if (seen) { intro.hidden = true; return; }
    try { sessionStorage.setItem('dp-intro-seen', '1'); } catch {}
    const enter = q('[data-intro-enter]', intro);
    const behind = qa('.site-header, main, .site-footer');
    behind.forEach((el) => el.setAttribute('inert', ''));
    document.documentElement.classList.add('intro-lock');
    if (!enter) return;
    let entered = false;
    const doEnter = () => {
      if (entered) return;
      entered = true;
      const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
      intro.classList.add('intro--leaving');
      setTimeout(() => {
        intro.hidden = true;
        document.documentElement.classList.remove('intro-lock');
        behind.forEach((el) => el.removeAttribute('inert'));
        const main = q('#contenido');
        if (main) main.focus();
      }, reduced ? 350 : 820);
    };
    enter.addEventListener('click', doEnter);
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    setTimeout(doEnter, reduced ? 5000 : 9600);
  }

  function initHeroVideo() {
    const video = q('[data-hero-video]');
    if (!video) return;
    if (video.closest('[data-intro]')?.hidden) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const play = () => video.play().catch(() => {});
    if (video.readyState >= 2) play();
    else video.addEventListener('loadeddata', play, { once: true });
  }

  function initAssistantWidget() {
    if (/^\/asistente(?:\/|$)/.test(location.pathname)) return;
    const csp = document.querySelector('meta[http-equiv="Content-Security-Policy"]')?.content || '';
    if (/frame-src\s+'none'/i.test(csp)) return;
    let scheduled = false;
    const load = () => {
      if (scheduled) return;
      scheduled = true;
      if (!q('link[data-assistant-widget-style]')) {
        const style = document.createElement('link');
        style.rel = 'stylesheet';
        style.href = '/assets/assistant-widget.css';
        style.dataset.assistantWidgetStyle = 'true';
        document.head.append(style);
      }
      import('/assets/assistant-widget.js').catch(() => {});
    };
    const schedule = () => {
      if ('requestIdleCallback' in window) requestIdleCallback(load, { timeout: 1400 });
      else setTimeout(load, 350);
    };
    if (document.readyState === 'complete') schedule();
    else addEventListener('load', schedule, { once: true });
  }

  function initHeaderSearch() {
    const triggers = qa('[data-assistant-search-open]');
    if (!triggers.length) return;
    const csp = document.querySelector('meta[http-equiv="Content-Security-Policy"]')?.content || '';
    const widgetBlocked = /frame-src\s+'none'/i.test(csp) || /^\/asistente(?:\/|$)/.test(location.pathname);
    triggers.forEach((btn) => {
      btn.addEventListener('click', () => {
        if (widgetBlocked) { location.href = '/asistente/'; return; }
        const launcher = q('.assistant-widget__launcher');
        if (launcher) { launcher.click(); return; }
        if (!q('link[data-assistant-widget-style]')) {
          const style = document.createElement('link');
          style.rel = 'stylesheet';
          style.href = '/assets/assistant-widget.css';
          style.dataset.assistantWidgetStyle = 'true';
          document.head.append(style);
        }
        import('/assets/assistant-widget.js')
          .then(() => q('.assistant-widget__launcher')?.click())
          .catch(() => { location.href = '/asistente/'; });
      });
    });
  }

  initHeader();
  initExplore();
  initIntro();
  initHeroVideo();
  initAssistantWidget();
  initHeaderSearch();
})();

// LRB-inspired utility/header + Home/inner editorial enhancement.
(() => {
  'use strict';

  const HOME_EDITORIAL_SRC = '/assets/v1-home-editorial-v3.js';
  const EDITORIAL_INTERIOR_SRC = '/assets/v1-editorial-interior-v4.js';
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
      const menu = inner.querySelector('.explore-trigger');
      if (!assistant || !actions || !menu) return;

      let left = inner.querySelector('.site-header__left');
      if (!left) {
        left = document.createElement('div');
        left.className = 'site-header__left';
        assistant.before(left);
      }
      if (assistant.parentElement !== left) left.append(assistant);

      let home = left.querySelector('.header-home');
      if (!home) {
        home = document.createElement('a');
        home.className = 'header-home';
        home.href = '/';
        home.setAttribute('aria-label', 'Volver a inicio');
        home.title = 'Inicio';
        home.innerHTML = houseSvg;
        home.addEventListener('click', () => emit('header_home_click'));
      }
      if (home.parentElement !== left) left.append(home);
      if (menu.parentElement !== left) left.append(menu);

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

  function loadScript(src, dataKey) {
    if (document.querySelector(`script[src="${src}"]`)) return;
    const script = document.createElement('script');
    script.src = src;
    script.async = false;
    if (dataKey) script.dataset[dataKey] = 'true';
    document.head.append(script);
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
    loadScript(HOME_EDITORIAL_SRC, 'homeEditorialV3');
  }

  function initLrbHeaderV2() {
    enhanceUtilityHeader();
    enhanceHomeMasthead();
    loadScript(EDITORIAL_INTERIOR_SRC, 'editorialInteriorV4');
    document.addEventListener('click', (event) => {
      if (!event.target.closest('.masthead-nav__item')) closeSubmenus();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLrbHeaderV2, { once: true });
  } else {
    initLrbHeaderV2();
  }
})();
