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

  // Territories are plain, flat, sequentially-numbered rows (no "Secciones /
  // Accesos directos" grouping); JS-injected rows just continue that same
  // numbering appended at the end, each wrapped in its own .explore-item so
  // the divider styling matches the static rows exactly.
  function renumberExploreRows(list) {
    qa('.explore-row__index', list).forEach((idx, position) => {
      idx.textContent = String(position + 1);
    });
  }

  function ensureAssistantExploreLink(dialog) {
    const list = q('.explore-list', dialog);
    if (!list || q('[data-assistant-menu-link]', list)) return;
    const item = document.createElement('div');
    item.className = 'explore-item';
    const link = document.createElement('a');
    link.className = 'explore-row';
    link.href = '/asistente/';
    link.dataset.preview = 'asistente';
    link.dataset.assistantMenuLink = 'true';

    const index = document.createElement('span');
    index.className = 'explore-row__index';
    const body = document.createElement('span');
    body.className = 'explore-row__body';
    const strong = document.createElement('strong');
    strong.textContent = 'Asistente';
    const small = document.createElement('small');
    small.textContent = 'Pregunta y encuentra la página que necesitas.';
    body.append(strong, small);
    link.append(index, body);
    item.append(link);
    list.append(item);
    renumberExploreRows(list);
  }

  function initExploreToggles(dialog) {
    qa('.explore-row__toggle', dialog).forEach((button) => {
      if (button.dataset.exploreToggleBound) return;
      button.dataset.exploreToggleBound = 'true';
      button.addEventListener('click', () => {
        const panel = q('#' + button.getAttribute('aria-controls'), dialog);
        if (!panel) return;
        const open = button.getAttribute('aria-expanded') === 'true';
        button.setAttribute('aria-expanded', String(!open));
        panel.hidden = open;
      });
    });
  }

  function initExplore() {
    const dialog = q('[data-explore-dialog]');
    const opens = qa('[data-explore-open]');
    const close = q('[data-explore-close]');
    if (!dialog || !opens.length || !close || typeof dialog.showModal !== 'function') return;

    ensureAssistantExploreLink(dialog);
    initExploreToggles(dialog);
    let opener = null;
    let scrollBeforeOpen = 0;
    opens.forEach((open) => {
      open.addEventListener('click', () => {
        opener = open;
        scrollBeforeOpen = window.scrollY;
        opens.forEach((o) => o.setAttribute('aria-expanded', 'true'));
        document.documentElement.classList.add('explore-open');
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
      document.documentElement.classList.remove('explore-open');
      dispatchEvent(new CustomEvent('dp:explore-close'));
      if (opener instanceof HTMLElement) {
        const restoreOpener = () => {
          if (Math.abs(window.scrollY - scrollBeforeOpen) > 4) window.scrollTo(0, scrollBeforeOpen);
          opener.focus({ preventScroll: true });
        };
        requestAnimationFrame(restoreOpener);
        setTimeout(restoreOpener, 80);
      }
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
    const enter = q('[data-intro-enter]', intro);
    const behind = qa('.site-header, main, .site-footer');
    behind.forEach((el) => el.setAttribute('inert', ''));
    document.documentElement.classList.add('intro-lock');
    if (!enter) return;
    let entered = false;
    const doEnter = () => {
      if (entered) return;
      entered = true;
      // Marked "seen" only once the intro is actually being dismissed, not
      // at page load -- if the visitor reloads while it's still stuck (e.g.
      // a frozen poster on a device where the video never played), the next
      // load gets a genuine fresh attempt instead of silently skipping the
      // intro for the rest of the session.
      try { sessionStorage.setItem('dp-intro-seen', '1'); } catch {}
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
    let fallback = setTimeout(doEnter, reduced ? 5000 : 9600);
    // When initHeroVideo (below) confirms autoplay was rejected, the visitor
    // is otherwise stuck looking at a frozen poster frame for up to 9.6s with
    // "Entrar" still invisible (it's timed to fade in only once the ink
    // reveal would have finished, ~4.6s in, so it doesn't fight the video for
    // attention). Reported live on a physical iPhone in Low Power Mode: no
    // motion ever starts, so the wait just reads as a broken/hung page.
    // Skip that wait once we know there's nothing to wait for.
    intro.addEventListener('dp-hero-video-blocked', () => {
      if (entered) return;
      clearTimeout(fallback);
      fallback = setTimeout(doEnter, 2200);
    }, { once: true });
  }

  function initHeroVideo() {
    const video = q('[data-hero-video]');
    if (!video) return;
    const intro = video.closest('[data-intro]');
    if (intro?.hidden) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    // iOS Safari treats preload as a hint, not a guarantee: it can sit at
    // readyState 0 (HAVE_NOTHING) indefinitely without ever firing
    // loadeddata unless something actually calls play() first -- so gating
    // play() behind "wait for loadeddata" can deadlock (reported live on a
    // physical iPhone: frozen poster, nothing else, indefinitely). Call
    // play() immediately instead of waiting on any readyState/event gate.
    // Force the muted/playsinline state via properties too, not just the
    // HTML attributes -- belt-and-suspenders per Apple's own guidance for
    // autoplay(muted+playsinline) reliability across WebKit versions.
    video.muted = true;
    video.defaultMuted = true;
    video.playsInline = true;
    // Low Power Mode (and similar battery/data-saver states) can silently
    // reject a muted+playsinline autoplay call even once the video has
    // loaded correctly. That's not recoverable programmatically, but a real
    // user gesture is exempt from that restriction -- retry once on the
    // first tap/click anywhere on the intro, in case the visitor interacts
    // with it (e.g. tapping "Entrar") before the video has started.
    video.play().catch(() => {
      if (!intro) return;
      intro.classList.add('intro--stalled');
      intro.dispatchEvent(new Event('dp-hero-video-blocked'));
      const retry = () => video.play().catch(() => {});
      intro.addEventListener('pointerdown', retry, { once: true, passive: true });
    });
    // Opt-in diagnostic overlay (?video-debug=1) for isolating a real-device
    // report against the actual intro runtime, not just the isolated
    // /video-ios-test/ page -- if that page plays fine but this overlay
    // shows the same freeze, the bug is in this page's CSS/paint/layering,
    // not in loading or autoplay policy. Never runs without the query flag.
    if (/[?&]video-debug=1\b/.test(location.search)) {
      const box = document.createElement('pre');
      box.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:99999;max-height:40vh;overflow:auto;margin:0;padding:8px;background:rgba(0,0,0,.85);color:#0f0;font:11px/1.4 ui-monospace,Menlo,monospace;white-space:pre-wrap;word-break:break-all';
      document.body.appendChild(box);
      const lines = [];
      const t0 = performance.now();
      const snap = (label) => `${label} @${((performance.now() - t0) / 1000).toFixed(2)}s | readyState=${video.readyState} paused=${video.paused} currentTime=${video.currentTime.toFixed(2)} error=${video.error ? video.error.code : 'null'}`;
      const log = (line) => { lines.push(line); box.textContent = lines.join('\n'); box.scrollTop = box.scrollHeight; };
      log(snap('init'));
      ['loadstart', 'loadedmetadata', 'loadeddata', 'canplay', 'playing', 'waiting', 'stalled', 'suspend', 'pause', 'error'].forEach((evt) => {
        video.addEventListener(evt, () => log(snap(evt)));
      });
      video.play().then(() => log('play() resolved')).catch((err) => log(`play() rejected: ${err.name} ${err.message}`));
    }
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

  // A visitor without a mail client configured (common on desktop browsers
  // that use webmail) sees a mailto: link do nothing when clicked. Copy the
  // address to the clipboard alongside the native mailto attempt and show a
  // brief confirmation, so there's always a usable fallback either way.
  function initMailtoCopyFallback() {
    if (!navigator.clipboard?.writeText) return;
    let toast = null;
    let hideTimer = null;
    const showToast = (link, email) => {
      if (!toast) {
        toast = document.createElement('div');
        toast.className = 'mailto-copy-toast';
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
        toast.style.cssText = 'position:fixed;left:50%;bottom:1.5rem;transform:translateX(-50%);z-index:9999;background:var(--dp-ink,#171614);color:#fff;font:500 .85rem/1.4 var(--font-ui,system-ui,sans-serif);padding:.65rem 1.1rem;border-radius:.5rem;box-shadow:0 8px 24px rgba(0,0,0,.25);max-width:min(90vw,26rem);text-align:center;opacity:0;transition:opacity .2s ease';
        document.body.append(toast);
      }
      toast.textContent = `Email copiado: ${email}`;
      requestAnimationFrame(() => { toast.style.opacity = '1'; });
      clearTimeout(hideTimer);
      hideTimer = setTimeout(() => { if (toast) toast.style.opacity = '0'; }, 4000);
    };
    document.addEventListener('click', (event) => {
      const link = event.target.closest('a[href^="mailto:"]');
      if (!link) return;
      const email = decodeURIComponent(link.href.replace(/^mailto:/, '').split('?')[0]);
      if (!email) return;
      navigator.clipboard.writeText(email).then(() => showToast(link, email)).catch(() => {});
    });
  }

  // A browser's default action for dropping a file anywhere on the page is
  // to navigate away and display that file, discarding whatever the visitor
  // was typing -- confirmed live (dragover/drop both fire with
  // defaultPrevented:false today). The site's manuscript/text tools are all
  // plain textareas with real writer input at stake, and there's no
  // legitimate file-drop feature anywhere to preserve, so this is safe to
  // block globally. Only blocks when the drag carries Files (an OS-level
  // file drag) -- a same-page text drag (e.g. reordering a selection
  // between two fields) reports other types and is left alone.
  function initDropProtection() {
    function isFileDrag(event) {
      return Array.prototype.includes.call(event.dataTransfer?.types || [], 'Files');
    }
    window.addEventListener('dragover', (event) => { if (isFileDrag(event)) event.preventDefault(); });
    window.addEventListener('drop', (event) => { if (isFileDrag(event)) event.preventDefault(); });
  }

  initHeader();
  initExplore();
  initIntro();
  initHeroVideo();
  initAssistantWidget();
  initHeaderSearch();
  initMailtoCopyFallback();
  initDropProtection();
})();

// LRB-inspired utility/header + Home/inner editorial enhancement.
(() => {
  'use strict';

  // Both scripts below are injected via loadScript() (a real <script src>
  // element, not an import()), so they're subject to ordinary HTTP caching
  // like any other asset -- but until this fix neither URL carried a
  // ?v=, so editing either file's content could never bust a returning
  // visitor's cached copy (the exact silent-stale-cache class of bug
  // scripts/check-asset-versions.py exists to catch for statically
  // <script src>-loaded assets; these two were invisible to it because
  // they're only ever referenced from inside this JS string, never from an
  // HTML href/src attribute). Bump the ?v= here AND the matching
  // TRACKED_ASSETS entry in check-asset-versions.py whenever either file's
  // content changes.
  const HOME_EDITORIAL_SRC = '/assets/v1-home-editorial-v3.js?v=4';
  const EDITORIAL_INTERIOR_SRC = '/assets/v1-editorial-interior-v4.js?v=2';
  const root = document.documentElement;
  const houseSvg = `
    <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
      <path d="M3.5 10.5 12 3.7l8.5 6.8"/>
      <path d="M5.5 9.2V20h13V9.2"/>
      <path d="M9.5 20v-6h5v6"/>
    </svg>`;
  // Submenu content (chevron + dropdown links) is now emitted directly in
  // index.html so it exists before first paint; this layer only wires the
  // click/keyboard behaviour onto that static markup.

  function emit(name, detail = {}) {
    document.dispatchEvent(new CustomEvent('dp:analytics', {
      detail: { event: name, ...detail }
    }));
  }

  function enhanceUtilityHeader() {
    // The left group (Asistente + Inicio + hamburger) is now emitted directly
    // by scripts/build-site-shell.py's render_header() -- this only wires
    // analytics and covers any legacy/unbuilt markup as a defensive fallback,
    // it must not rearrange nodes that already paint in the right order.
    document.querySelectorAll('.site-header__inner').forEach((inner) => {
      if (inner.dataset.lrbEnhanced === 'true') return;
      const assistant = inner.querySelector('.header-search');
      const menu = inner.querySelector('.explore-trigger');
      if (!assistant || !menu) return;

      let left = inner.querySelector('.site-header__left');
      if (!left) {
        left = document.createElement('div');
        left.className = 'site-header__left';
        assistant.before(left);
        left.append(assistant);
      }

      let home = left.querySelector('.header-home');
      if (!home) {
        home = document.createElement('a');
        home.className = 'header-home';
        home.href = '/';
        home.setAttribute('aria-label', 'Volver a inicio');
        home.title = 'Inicio';
        home.innerHTML = houseSvg;
        left.append(home);
      }
      if (menu.parentElement !== left) left.append(menu);

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

    const candidates = [
      '/assets/david-porto-diaz-escritor-banner-cropped.png',
      '/assets/david-porto-diaz-escritor-banner.png',
      '/assets/david-porto-header-lettering-transparent.png',
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

    list.querySelectorAll(':scope > .masthead-nav__item').forEach((li, position) => {
      const anchor = li.querySelector(':scope > a[data-territory]');
      const trigger = li.querySelector(':scope > .masthead-nav__submenu-trigger');
      if (!anchor || !trigger) return;
      const key = anchor.dataset.territory;
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

  function loadScript(src, dataKey, { module = false } = {}) {
    if (document.querySelector(`script[src="${src}"]`)) return;
    const script = document.createElement('script');
    script.src = src;
    script.async = false;
    if (module) script.type = 'module';
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
      const compact = window.scrollY > compactAt || root.classList.contains('explore-open');
      // Chromium resets the whole page's scroll position to 0 when focus
      // lands on a descendant of a position:sticky ancestor (the utility
      // bar) -- a long-standing browser quirk, not something this site
      // triggers. Left alone, that reset fires this same scroll handler,
      // computes compact=false and hides the very hamburger that just
      // received focus, so a keyboard user tabbing to it mid-scroll would
      // watch their target vanish under them. While focus sits inside the
      // header, only allow entering compact, never leaving it -- checked
      // against the reset-to-0 case too, not just a partial scroll-up.
      if (!compact && root.classList.contains('lrb-compact') && document.activeElement?.closest?.('.site-header')) return;
      root.classList.toggle('lrb-compact', compact);
      if (compact) closeSubmenus();
    };
    measure();
    update();
    addEventListener('resize', () => { measure(); update(); }, { passive: true });
    addEventListener('scroll', update, { passive: true });
    addEventListener('dp:explore-close', () => {
      requestAnimationFrame(() => {
        measure();
        update();
      });
    });
    loadScript(HOME_EDITORIAL_SRC, 'homeEditorialV3', { module: true });
    scheduleHomeEditorialFallback();
  }

  // Safety net for a real failure mode index.html's hide rule never covered:
  // it hides .river-grid/.promo-band/#faq/#newsletter until buildFlow() in
  // the dynamically-loaded v1-home-editorial-v3.js module sets
  // data-home-editorial-v3="true" as its last step, with <noscript> as the
  // only escape hatch -- which only fires when JS itself is disabled. If
  // that module (or its static `import` of editorial-public-facts.mjs)
  // fails to load for a JS-enabled visitor -- network hiccup, ad/content
  // blocker, CDN error -- buildFlow() never runs and the attribute never
  // gets set, so Home's entire main content stays invisible forever with no
  // fallback (confirmed live: blocking either file leaves .river-grid
  // visibility:hidden permanently, zero visible buy CTA). 5s is comfortably
  // above home-runtime's real load time (~29KB/2 requests per
  // data/performance-budgets.json) so it never fires on a legitimately
  // slow-but-working load and reintroduces the pre-JS-flash CLS regression
  // this hide rule exists to prevent (see test-home-fallback-cls-contract.py).
  function scheduleHomeEditorialFallback() {
    setTimeout(() => {
      if (root.dataset.homeEditorialV3 === 'true') return;
      const style = document.createElement('style');
      style.textContent = 'html.v1[data-lrb-home="true"]:not([data-home-editorial-v3="true"]) .river-grid,'
        + 'html.v1[data-lrb-home="true"]:not([data-home-editorial-v3="true"]) .promo-band,'
        + 'html.v1[data-lrb-home="true"]:not([data-home-editorial-v3="true"]) #faq,'
        + 'html.v1[data-lrb-home="true"]:not([data-home-editorial-v3="true"]) #newsletter{visibility:visible}';
      document.head.append(style);
    }, 5000);
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
