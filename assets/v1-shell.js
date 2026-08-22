// V1 editorial shell — Explorar <dialog>, header scroll state, cartography
// hover preview. Ported from lab/diseno-home-v1/js/lab.js (initHeader,
// initExplore, initMap only — the lab's demo-form/fixtures/share helpers
// are lab-only and not needed here: production newsletter submission stays
// in script.js's submitNewsletter(), bound by the same element IDs).
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
    const open = q('[data-explore-open]');
    const close = q('[data-explore-close]');
    if (!dialog || !open || !close || typeof dialog.showModal !== 'function') return;

    ensureAssistantExploreLink(dialog);

    let opener = null;
    open.addEventListener('click', () => {
      opener = document.activeElement;
      open.setAttribute('aria-expanded', 'true');
      dialog.showModal();
      close.focus();
    });
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('close', () => {
      open.setAttribute('aria-expanded', 'false');
      if (opener instanceof HTMLElement) opener.focus({ preventScroll: true });
    });

    // Trampa de foco explicita. El <dialog> modal ya impide llegar al contenido
    // de detras —el fondo es inerte—, pero el ciclo nativo de Chromium mete dos
    // paradas muertas por vuelta: al pasar del ultimo enlace el foco cae en
    // <body> y despues en el propio <dialog>, y solo entonces vuelve al boton de
    // cerrar. Para quien navega con teclado son dos tabulaciones que no llevan a
    // ningun sitio, cada vuelta. Con esto, del ultimo elemento se pasa al
    // primero y al reves con Shift.
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
      manecillas: ['Las manecillas del recuerdo', 'La obra actual y punto de entrada editorial.'],
      autor: ['Autor', 'Biografía, obra y trayectoria de David Porto Díaz.'],
      samuel: ['Samuel entre mundos', 'Primera novela publicada.'],
      cuaderno: ['Cuaderno', 'Artículos y piezas editoriales.'],
      herramientas: ['Herramientas', 'Utilidades gratuitas para problemas concretos de escritura y publicación.'],
      prensa: ['Prensa y eventos', 'Apariciones, materiales de prensa y agenda.'],
      asistente: ['Asistente', 'Pregunta por libros, recursos, prensa o escritura y abre la fuente correcta.']
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

  function initMap() {
    const map = q('[data-map]');
    if (!map) return;
    qa('[data-map-node]', map).forEach((node) => {
      const on = () => { map.dataset.active = node.dataset.mapNode; };
      const off = () => { delete map.dataset.active; };
      node.addEventListener('mouseenter', on);
      node.addEventListener('mouseleave', off);
      node.addEventListener('focus', on);
      node.addEventListener('blur', off);
    });
  }

  function initAssistantWidget() {
    if (/^\/asistente(?:\/|$)/.test(location.pathname)) return;
    // The widget runs the assistant inside a same-origin iframe, so pages that
    // declare frame-src 'none' (tools, directories and other CSP-locked routes)
    // must not mount it: the browser would block the frame and log a CSP
    // violation on every visit. Those pages still reach /asistente/ via Explorar.
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

  initHeader();
  initExplore();
  initMap();
  initAssistantWidget();
})();
