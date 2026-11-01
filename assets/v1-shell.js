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
        // Runs twice (rAF + 80ms fallback); the second pass must not pull focus
        // back if the visitor has already moved on to another control.
        const restoreOpener = () => {
          const active = document.activeElement;
          if (active && active !== document.body && active !== opener && !dialog.contains(active)) return;
          if (Math.abs(window.scrollY - scrollBeforeOpen) > 4) window.scrollTo(0, scrollBeforeOpen);
          opener.focus({ preventScroll: true });
        };
        requestAnimationFrame(restoreOpener);
        setTimeout(restoreOpener, 80);
      }
    });

    // Trampa de foco endurecida (06/10/2026): el filtro anterior solo miraba
    // caja, asi que colaba controles dentro de [hidden]/[inert]/aria-hidden y
    // solo intervenia en los extremos de la lista, de modo que un foco que
    // llegase al dialogo desde fuera de esa lista se escapaba del modal.
    const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';
    const isTabbable = (el) => {
      if (!(el instanceof HTMLElement) || el.tabIndex < 0) return false;
      if (el.matches(':disabled') || el.closest('[hidden],[inert],[aria-hidden="true"]')) return false;
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
      return el.getClientRects().length > 0;
    };
    dialog.addEventListener('keydown', (event) => {
      if (event.key !== 'Tab') return;
      const items = [...dialog.querySelectorAll(FOCUSABLE)].filter(isTabbable);
      if (!items.length) {
        event.preventDefault();
        dialog.focus({ preventScroll: true });
        return;
      }
      const active = document.activeElement;
      const activeIndex = items.indexOf(active);
      const delta = event.shiftKey ? -1 : 1;
      const targetIndex = activeIndex === -1
        ? (event.shiftKey ? items.length - 1 : 0)
        : (activeIndex + delta + items.length) % items.length;
      event.preventDefault();
      items[targetIndex].focus({ preventScroll: true });
    });

    const preview = q('[data-explore-preview]', dialog);
    const label = q('[data-preview-label]', dialog);
    const copy = q('[data-preview-copy]', dialog);
    const media = q('[data-preview-media]', dialog);
    const content = {
      'works-hub': ['Obras', 'Las dos novelas publicadas, fragmentos y rutas de lectura.'],
      'notebook-hub': ['Cuaderno', 'Archivo de artículos del autor.'],
      'recommendations-hub': ['Libros recomendados', 'Catálogo de libros, editoriales y concursos.'],
      'tools-hub': ['Herramientas', 'Utilidades gratuitas para problemas concretos de escritura.'],
      author: ['Autor', 'Biografía, obra y trayectoria de David Porto Díaz.'],
      press: ['Prensa', 'Material de prensa, agenda y apariciones verificables.'],
      'site-map': ['Mapa del sitio', 'Índice completo para recorrer la web por secciones.'],
      manecillas: ['Las manecillas del recuerdo', 'La obra actual y punto de entrada editorial.'],
      autor: ['Autor', 'Biografía, obra y trayectoria de David Porto Díaz.'],
      samuel: ['Samuel entre mundos', 'Primera novela publicada.'],
      cuaderno: ['Cuaderno', 'Archivo de artículos y libros recomendados.'],
      herramientas: ['Herramientas', 'Utilidades gratuitas para problemas concretos de escritura y publicación.'],
      prensa: ['Prensa y eventos', 'Apariciones, materiales de prensa y agenda.'],
      'lectores-beta': ['Lectores beta', 'Lee material sin publicar y comparte una opinión honesta, o envía tu manuscrito para recibir la suya.'],
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
    if (seen || document.documentElement.classList.contains('intro-seen')) { intro.hidden = true; return; }
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
    // Volver con atras/adelante desde bfcache restaura la pagina tal como se
    // dejo: si ya se habia pulsado Entrar, terminar de cerrar la intro al
    // instante en vez de mostrar de nuevo la capa a medio salir.
    window.addEventListener('pageshow', (event) => {
      if (!event.persisted || !entered) return;
      intro.hidden = true;
      document.documentElement.classList.remove('intro-lock');
      behind.forEach((el) => el.removeAttribute('inert'));
    });
    // El enlace «Saltar al contenido» queda por encima de la introducción mientras tiene el foco (v1-home.css): al activarlo se entra.
    q('.skip-link')?.addEventListener('click', (event) => {
      if (!document.documentElement.classList.contains('intro-lock')) return;
      event.preventDefault();
      doEnter();
    });
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let fallback = setTimeout(doEnter, reduced ? 5000 : 9600);
    // When initHeroVideo (below) confirms autoplay was rejected, the visitor
    // is otherwise stuck looking at a frozen poster frame for up to 9.6s
    // ("Entrar" is visible from the start since 2026-10-31, but not everyone
    // notices it on a still frame). Reported live on a physical iPhone in Low Power Mode: no
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
        style.href = '/assets/assistant-widget.css?v=1';
        style.dataset.assistantWidgetStyle = 'true';
        document.head.append(style);
      }
      import('/assets/assistant-widget.js?v=2').catch(() => {});
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
          style.href = '/assets/assistant-widget.css?v=1';
          style.dataset.assistantWidgetStyle = 'true';
          document.head.append(style);
        }
        import('/assets/assistant-widget.js?v=2')
          .then(() => q('.assistant-widget__launcher')?.click())
          .catch(() => { location.href = '/asistente/'; });
      });
    });
  }

  // A mailto: link does nothing useful on a computer without a mail app
  // configured (most people use Gmail or Outlook in the browser): an empty
  // "Open with..." prompt or nothing at all. So every mailto: link, on any
  // device, opens a small chooser instead: webmail compose, the native app,
  // or copy the address.
  function initMailChooser() {
    let panel = null;
    let opener = null;
    let reopenGuard = null;
    let lastWidth = window.innerWidth;

    const close = (restoreFocus) => {
      if (!panel) return;
      panel.remove();
      panel = null;
      if (restoreFocus) opener?.focus({ preventScroll: true });
      opener = null;
    };

    const position = (link) => {
      const r = link.getBoundingClientRect();
      const w = panel.offsetWidth;
      const h = panel.offsetHeight;
      const left = Math.min(Math.max(8, r.left + r.width / 2 - w / 2), window.innerWidth - w - 8);
      const below = r.bottom + 8;
      const top = below + h <= window.innerHeight - 8 ? below : Math.max(8, r.top - h - 8);
      panel.style.left = `${Math.round(left)}px`;
      panel.style.top = `${Math.round(top)}px`;
    };

    // The async Clipboard API is refused without clipboard permission (some
    // browsers, embedded webviews, non-focused documents) and used to fail
    // silently, so the first click looked dead. Copy synchronously from a
    // selection of the visible address first, inside the click gesture, and
    // keep the async API as a second attempt.
    const copyText = (text, source) => {
      const selection = window.getSelection?.();
      let copied = false;
      if (selection) {
        const saved = selection.rangeCount ? selection.getRangeAt(0) : null;
        const range = document.createRange();
        range.selectNodeContents(source);
        selection.removeAllRanges();
        selection.addRange(range);
        try { copied = document.execCommand('copy'); } catch { copied = false; }
        selection.removeAllRanges();
        if (saved) selection.addRange(saved);
      }
      if (copied) return Promise.resolve();
      if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);
      return Promise.reject(new Error('clipboard unavailable'));
    };

    const selectAddress = (address) => {
      const range = document.createRange();
      range.selectNodeContents(address);
      window.getSelection()?.removeAllRanges();
      window.getSelection()?.addRange(range);
    };

    const open = (link) => {
      close(false);
      const url = new URL(link.href);
      const email = decodeURIComponent(url.pathname);
      const subject = url.searchParams.get('subject') || '';
      const body = url.searchParams.get('body') || '';
      // %20 rather than "+" for spaces: Outlook shows a literal "+".
      const compose = (base, params) => `${base}?${new URLSearchParams(
        Object.entries(params).filter(([, v]) => v),
      ).toString().replace(/\+/g, '%20')}`;
      const gmail = compose('https://mail.google.com/mail/', { view: 'cm', fs: '1', to: email, su: subject, body });
      const outlook = compose('https://outlook.live.com/mail/0/deeplink/compose', { to: email, subject, body });

      opener = link;
      panel = document.createElement('div');
      panel.className = 'mail-chooser';
      panel.setAttribute('role', 'dialog');
      panel.setAttribute('aria-label', 'Elegir cómo escribir el correo');
      const address = document.createElement('p');
      address.className = 'mail-chooser__address';
      address.textContent = email;
      const list = document.createElement('div');
      list.className = 'mail-chooser__list';
      const item = (label, href) => {
        const a = document.createElement('a');
        a.className = 'mail-chooser__item';
        a.href = href;
        a.textContent = label;
        if (href.startsWith('https:')) {
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
        }
        a.addEventListener('click', () => setTimeout(() => close(false)));
        list.append(a);
      };
      item('Abrir en Gmail', gmail);
      item('Abrir en Outlook', outlook);
      item('Usar mi app de correo', link.href);
      const copy = document.createElement('button');
      copy.type = 'button';
      copy.className = 'mail-chooser__item';
      copy.textContent = 'Copiar dirección';
      const status = document.createElement('p');
      status.className = 'mail-chooser__status';
      status.setAttribute('role', 'status');
      let resetTimer = null;
      copy.addEventListener('click', () => {
        clearTimeout(resetTimer);
        copyText(email, address).then(() => {
          copy.textContent = 'Dirección copiada ✓';
          status.textContent = 'Dirección copiada al portapapeles';
        }, () => {
          // Last resort: leave the address selected for Ctrl+C / long press.
          selectAddress(address);
          copy.textContent = 'Selecciónala y cópiala';
          status.textContent = 'No se pudo copiar: la dirección queda seleccionada';
        }).finally(() => {
          resetTimer = setTimeout(() => {
            copy.textContent = 'Copiar dirección';
            status.textContent = '';
          }, 4000);
        });
      });
      list.append(copy);
      panel.append(address, list, status);
      document.body.append(panel);
      position(link);
      list.querySelector('.mail-chooser__item')?.focus({ preventScroll: true });
    };

    document.addEventListener('click', (event) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target.closest?.('a[href^="mailto:"]');
      if (!link || link.closest('.mail-chooser')) return;
      event.preventDefault();
      // A second click on the link that opened the chooser just closes it.
      if (reopenGuard === link) {
        reopenGuard = null;
        return;
      }
      open(link);
    });
    // pointerdown, not click: the reveal trigger opens the chooser from inside
    // its own click, and that same click must not count as "outside".
    document.addEventListener('pointerdown', (event) => {
      reopenGuard = null;
      if (!panel || panel.contains(event.target)) return;
      if (opener?.contains(event.target)) reopenGuard = opener;
      close(false);
    });
    document.addEventListener('keydown', (event) => {
      if (!panel) return;
      if (event.key === 'Escape') close(true);
      // The chooser sits at the end of <body>: tabbing past either end hands
      // focus back to the link that opened it instead of leaving the page.
      if (event.key === 'Tab') {
        const items = panel.querySelectorAll('.mail-chooser__item');
        const edge = event.shiftKey ? items[0] : items[items.length - 1];
        if (document.activeElement === edge) {
          event.preventDefault();
          close(true);
        }
      }
    });
    // Tabbing out of the chooser closes it, so it never lingers behind focus.
    document.addEventListener('focusin', (event) => {
      if (panel && !panel.contains(event.target) && event.target !== opener) close(false);
    });
    // Only a real width change: phones fire resize while the URL bar shows
    // or hides during scroll, and that must not close the chooser.
    window.addEventListener('resize', () => {
      if (window.innerWidth !== lastWidth) close(false);
      lastWidth = window.innerWidth;
    });
    window.addEventListener('scroll', () => { if (panel && opener) position(opener); }, { passive: true });
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

  // Footer groups are an exclusive accordion on phones; from 768px they sit in
  // four columns, so all of them stay open (otherwise three columns look empty).
  function initFooterGroups() {
    const groups = qa('.site-footer details.ft-group');
    if (!groups.length || !window.matchMedia) return;
    const wide = matchMedia('(min-width: 768px)');
    const initial = groups.map((group) => group.open);
    const apply = () => groups.forEach((group, i) => {
      if (wide.matches) {
        group.removeAttribute('name');
        group.open = true;
      } else {
        group.open = initial[i];
        group.setAttribute('name', 'ft-nav');
      }
    });
    groups.forEach((group) => group.querySelector('summary')?.addEventListener('click', (event) => {
      if (wide.matches) event.preventDefault();
    }));
    wide.addEventListener?.('change', apply);
    apply();
  }

  initHeader();
  initExplore();
  initIntro();
  initHeroVideo();
  initAssistantWidget();
  initHeaderSearch();
  initMailChooser();
  initFooterGroups();
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
  const HOME_EDITORIAL_SRC = '/assets/v1-home-editorial-v3.js?v=13';
  const EDITORIAL_INTERIOR_SRC = '/assets/v1-editorial-interior-v4.js?v=12';
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

  function setSubmenuDismissed(item, dismissed) {
    if (!item) return;
    const submenu = item.querySelector(':scope > .masthead-nav__submenu');
    item.classList.toggle('is-dismissed', dismissed);
    if (!submenu) return;
    const props = ['opacity', 'visibility', 'pointer-events', 'transform', 'transition-delay'];
    if (dismissed) {
      submenu.style.opacity = '0';
      submenu.style.visibility = 'hidden';
      submenu.style.pointerEvents = 'none';
      submenu.style.transform = 'translateY(-2px)';
      submenu.style.transitionDelay = '0s';
    } else {
      props.forEach((prop) => submenu.style.removeProperty(prop));
    }
  }

  function closeSubmenus(except = null) {
    document.querySelectorAll('.masthead-nav__item.is-open').forEach((item) => {
      if (item === except) return;
      item.classList.remove('is-open');
      setSubmenuDismissed(item, true);
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
        setSubmenuDismissed(li, !willOpen);
        trigger.setAttribute('aria-expanded', String(willOpen));
        if (willOpen) emit('masthead_submenu_open', { territory: key, position: position + 1 });
      });
      li.addEventListener('mouseenter', () => setSubmenuDismissed(li, false));
      let escaping = false;
      li.addEventListener('focusin', () => { if (!escaping) setSubmenuDismissed(li, false); });
      li.addEventListener('mouseleave', () => setSubmenuDismissed(li, false));
      li.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape') return;
        li.classList.remove('is-open');
        setSubmenuDismissed(li, true);
        trigger.setAttribute('aria-expanded', 'false');
        escaping = true;
        trigger.focus({ preventScroll: true });
        escaping = false;
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
      // The Home opener now stays visible in both header states (v1-home.css).
      // Do not latch compact mode while it has focus: closing Explorar restores
      // that focus, which used to prevent the masthead from ever returning.
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
