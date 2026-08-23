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
    // Puede haber mas de un disparador (el del header y, en la home
    // cinematica, el del panel del hero) que abren el mismo dialogo.
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
    // aria-expanded se pone a false aqui ademas de en el evento 'close'. El
    // <dialog> quita su atributo open de forma sincrona, pero 'close' se
    // encola como tarea: entre las dos cosas hay un hueco en el que el dialogo
    // ya no se ve y el disparador sigue anunciando aria-expanded="true". Un
    // lector de pantalla puede leer ese estado, y medido con Playwright falla
    // ~la mitad de las veces. Marcarlo tambien al cerrar cierra el hueco; el
    // handler de 'close' se queda como red de seguridad para los cierres que
    // no pasan por aqui y es quien devuelve el foco.
    const markClosed = () => opens.forEach((o) => o.setAttribute('aria-expanded', 'false'));
    close.addEventListener('click', () => { markClosed(); dialog.close(); });
    dialog.addEventListener('cancel', markClosed);
    dialog.addEventListener('click', (event) => { if (event.target === dialog) { markClosed(); dialog.close(); } });
    dialog.addEventListener('close', () => {
      markClosed();
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

  function initMap() {
    const map = q('[data-map]');
    if (!map) return;
    let focusKey = '';
    let hoverKey = '';
    const sync = () => {
      const active = focusKey || hoverKey;
      if (active) map.dataset.active = active;
      else delete map.dataset.active;
      if (focusKey) map.dataset.focusActive = focusKey;
      else delete map.dataset.focusActive;
    };
    qa('[data-map-node]', map).forEach((node) => {
      const key = node.dataset.mapNode || '';
      node.addEventListener('mouseenter', () => {
        hoverKey = key;
        sync();
      });
      node.addEventListener('mouseleave', () => {
        if (hoverKey === key) hoverKey = '';
        sync();
      });
      node.addEventListener('focus', () => {
        focusKey = key;
        sync();
      });
      node.addEventListener('blur', () => {
        if (focusKey === key) focusKey = '';
        sync();
      });
    });
  }

  // Trocea .intro__leaf en N tiras verticales anidadas (cada una dentro de
  // la anterior) para que el giro de "pasar pagina" se vea curvado en vez
  // de una tabla rigida girando de una pieza: al estar anidadas, la
  // rotacion de cada tira se suma a la de sus antecesoras, asi que la
  // hoja se va "enrollando" de derecha (borde libre) a izquierda (lomo).
  function buildCurlStrips(leaf) {
    const src = leaf.dataset.src;
    if (!src) return;
    leaf.textContent = '';
    const n = 6;
    const w = window.innerWidth;
    const h = window.innerHeight;
    const stripW = w / n;
    // Rotacion incremental igual en cada tira: acumulada a lo largo de las
    // n tiras anidadas suma unos -168deg en la ultima (el borde libre),
    // suficiente para que backface-visibility:hidden la haga desaparecer.
    const rotatePerStrip = -168 / n;
    let parent = leaf;
    for (let i = 0; i < n; i += 1) {
      const strip = document.createElement('div');
      strip.className = 'intro__leaf-strip';
      strip.style.left = i === 0 ? '0' : '100%';
      strip.style.width = `${stripW}px`;
      strip.style.backgroundImage = `url('${src}')`;
      strip.style.backgroundSize = `${w}px ${h}px`;
      strip.style.backgroundPosition = `${-i * stripW}px 0`;
      // El borde libre (tira n-1) empieza a moverse casi de inmediato; el
      // lomo (tira 0) se retrasa: la curva "viaja" de derecha a izquierda.
      strip.style.setProperty('--curl-delay', `${(n - 1 - i) * 18}ms`);
      strip.style.setProperty('--curl-rotate', `${rotatePerStrip}deg`);
      // Tiras mas giradas (mas cerca del borde libre) quedan mas de canto
      // y reciben menos luz: una sombra propia progresiva por tira.
      const shade = document.createElement('div');
      shade.className = 'intro__leaf-strip__shade';
      shade.style.setProperty('--curl-delay', `${(n - 1 - i) * 18}ms`);
      shade.style.setProperty('--curl-shade', String(0.12 + (i / (n - 1)) * 0.5));
      strip.append(shade);
      parent.append(strip);
      parent = strip;
    }
  }

  // Sonido de pagina sintetizado con Web Audio (rafaga corta de ruido
  // filtrado) para no depender de un fichero de audio con licencia dudosa.
  // Solo suena aqui, tras el clic de Entrar -- no en el resto de la web.
  function playPageTurnSound() {
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      const ctx = new Ctx();
      const duration = 0.45;
      const buffer = ctx.createBuffer(1, ctx.sampleRate * duration, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < data.length; i += 1) data[i] = Math.random() * 2 - 1;
      const noise = ctx.createBufferSource();
      noise.buffer = buffer;
      const bandpass = ctx.createBiquadFilter();
      bandpass.type = 'bandpass';
      bandpass.frequency.value = 2600;
      bandpass.Q.value = 0.6;
      const gain = ctx.createGain();
      const now = ctx.currentTime;
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.28, now + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
      noise.connect(bandpass).connect(gain).connect(ctx.destination);
      noise.start(now);
      noise.stop(now + duration);
      noise.onended = () => ctx.close().catch(() => {});
    } catch (_) { /* audio no critico: si falla, la transicion sigue igual */ }
  }

  function initIntro() {
    const intro = q('[data-intro]');
    if (!intro) return;
    const enter = q('[data-intro-enter]', intro);
    const leaf = q('[data-intro-leaf]', intro);
    // La Home normal esta en el DOM desde el inicio (SEO/no-JS ven contenido
    // real), pero mientras la intro cubre la pantalla no debe poder
    // recibir foco por teclado ni scroll.
    const behind = qa('.site-header, main, .site-footer');
    behind.forEach((el) => el.setAttribute('inert', ''));
    document.documentElement.classList.add('intro-lock');
    if (!enter) return;
    enter.addEventListener('click', () => {
      const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (!reduced) {
        if (leaf) buildCurlStrips(leaf);
        playPageTurnSound();
      }
      // Las tiras se acaban de insertar en su estado de reposo (rotateY 0).
      // Sin forzar un reflow aqui, anadir la clase que dispara el giro en
      // el mismo tick hace que el navegador nunca "vea" ese estado previo
      // y salte directo al final: la transicion de las tiras no se
      // reproduce, solo aparecen ya giradas. offsetWidth fuerza el layout
      // sincrono antes del cambio de clase para que el giro si se anime.
      if (leaf) void leaf.offsetWidth;
      intro.classList.add('intro--leaving');
      setTimeout(() => {
        intro.hidden = true;
        document.documentElement.classList.remove('intro-lock');
        behind.forEach((el) => el.removeAttribute('inert'));
        const main = q('#contenido');
        if (main) main.focus();
      }, reduced ? 350 : 850);
    });
  }

  function initHeroVideo() {
    const video = q('[data-hero-video]');
    if (!video) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const play = () => video.play().catch(() => {});
    if (video.readyState >= 2) play();
    else video.addEventListener('loadeddata', play, { once: true });
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
  initIntro();
  initHeroVideo();
  initAssistantWidget();
})();
