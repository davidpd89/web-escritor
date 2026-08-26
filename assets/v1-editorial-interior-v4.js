/* PR95 V4 — persistent local navigation + editorial media placeholders.
   Progressive enhancement: every destination remains a real static URL and
   the global Explore/footer continue to work if JavaScript is unavailable. */
(() => {
  'use strict';

  const root = document.documentElement;
  if (!root.classList.contains('v1')) return;

  const MEMORIA_EXTERNAL_URL = 'https://www.diversidadliteraria.com/la-memoria-de-las-tierras-del-norte';
  const MEMORIA_INTERNAL_URL = '/libros/#memoria-tierras-norte';
  const BETA_READER_URL = '/lectores-beta/';
  const BETA_MANUSCRIPT_URL = '/lectores-beta/enviar-manuscrito/';

  const normalise = (value) => {
    const url = new URL(value, location.origin);
    let path = url.pathname.replace(/\/index\.html$/, '/');
    if (path.length > 1 && !path.endsWith('/') && !/\.html$/i.test(path)) path += '/';
    return path;
  };

  const currentPath = normalise(location.pathname);

  /* Mirrors data/navigation.json localNavSets, with labels chosen for the
     compact visual strip. The canonical registry remains the source of truth
     for destinations; this runtime layer only makes those existing routes
     persist visually after navigation. */
  const contexts = [
    {
      key: 'manecillas', label: 'Manecillas', home: '/las-manecillas-del-recuerdo/',
      matches: (path) => path.startsWith('/las-manecillas-del-recuerdo/'),
      links: [
        ['/libros/', '← Obras'],
        ['/las-manecillas-del-recuerdo/', 'La novela'],
        ['/las-manecillas-del-recuerdo/fragmentos/', 'Fragmentos'],
        ['/prensa.html#ficha-manecillas', 'Ficha de prensa']
      ]
    },
    {
      key: 'samuel', label: 'Samuel entre mundos', home: '/libros/samuel-entre-mundos/',
      matches: (path) => path.startsWith('/libros/samuel-entre-mundos/') || path === '/fragmento/' || path.startsWith('/universo/noveris/') || path.startsWith('/clubes-de-lectura/samuel-entre-mundos/'),
      links: [
        ['/libros/', '← Obras'],
        ['/libros/samuel-entre-mundos/', 'El libro'],
        ['/fragmento/', 'Capítulo 1'],
        ['/universo/noveris/', 'Noveris'],
        ['/clubes-de-lectura/samuel-entre-mundos/', 'Club de lectura'],
        ['/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/', 'Guía imprimible']
      ]
    },
    {
      key: 'obras', label: 'Obras', home: '/libros/',
      matches: (path) => path === '/libros/',
      links: [
        ['/libros/', 'Todas las obras'],
        ['/las-manecillas-del-recuerdo/', 'Las manecillas del recuerdo'],
        ['/libros/samuel-entre-mundos/', 'Samuel entre mundos']
      ]
    },
    {
      key: 'cuaderno', label: 'Cuaderno', home: '/cuaderno/',
      matches: (path) => path.startsWith('/cuaderno/') || path.startsWith('/recomendaciones/'),
      links: [
        ['/cuaderno/', 'Archivo'],
        ['/cuaderno/temas/', 'Temas'],
        ['/recomendaciones/', 'Recomendaciones']
      ]
    },
    {
      key: 'herramientas', label: 'Herramientas', home: '/herramientas/',
      matches: (path) => path.startsWith('/herramientas/') || path.startsWith('/editoriales/') || path.startsWith('/convocatorias-escritores/') || path.startsWith('/metodologia-editorial/'),
      links: [
        ['/herramientas/', 'Herramientas'],
        ['/editoriales/', 'Editoriales'],
        ['/convocatorias-escritores/', 'Convocatorias'],
        ['/metodologia-editorial/', 'Metodología']
      ]
    },
    {
      key: 'autor', label: 'Autor', home: '/autor.html',
      matches: (path) => path === '/autor.html' || path === '/premios.html' || path.startsWith('/lectores-beta/'),
      links: [
        ['/autor.html', 'Autor'],
        ['/premios.html', 'Premios'],
        ['/lectores-beta/', 'Lectores beta'],
        ['/eventos.html', 'Eventos'],
        ['/prensa.html', 'Prensa']
      ]
    },
    {
      key: 'prensa', label: 'Prensa y agenda', home: '/prensa.html',
      matches: (path) => path === '/prensa.html' || path === '/eventos.html' || path === '/ferias.html',
      links: [
        ['/prensa.html', 'Prensa'],
        ['/eventos.html', 'Eventos'],
        ['/ferias.html', 'Ferias'],
        ['/premios.html', 'Premios']
      ]
    }
  ];

  function buildContextNav() {
    if (root.dataset.lrbHome === 'true' || document.querySelector('.section-context')) return;
    const context = contexts.find((item) => item.matches(currentPath));
    if (!context) return;

    root.dataset.editorialContext = context.key;
    const header = document.querySelector('.site-header');
    if (!header) return;

    const nav = document.createElement('nav');
    nav.className = 'section-context';
    nav.setAttribute('aria-label', `Navegación de ${context.label}`);
    nav.dataset.editorialContextNav = context.key;

    const inner = document.createElement('div');
    inner.className = 'section-context__inner';

    const title = document.createElement('a');
    title.className = 'section-context__title';
    title.href = context.home;
    title.textContent = context.label;

    const links = document.createElement('div');
    links.className = 'section-context__links';
    context.links.forEach(([href, label]) => {
      const link = document.createElement('a');
      link.href = href;
      link.textContent = label;
      const linkPath = normalise(href);
      const exact = currentPath === linkPath;
      const familyCurrent = !exact && linkPath.endsWith('/') && linkPath !== '/' && currentPath.startsWith(linkPath);
      if (exact || familyCurrent) link.setAttribute('aria-current', 'page');
      links.append(link);
    });

    inner.append(title, links);
    nav.append(inner);
    header.insertAdjacentElement('afterend', nav);

    const active = links.querySelector('[aria-current="page"]');
    if (active) requestAnimationFrame(() => {
      // Element.scrollIntoView() here (even with block/inline:'nearest') was
      // shifting Chromium's sequential focus-navigation starting point to
      // this link on page load, so the very first real Tab press landed on
      // it instead of the skip-link -- a serious a11y regression. Adjusting
      // the strip's own scrollLeft directly reveals the active item in its
      // horizontally-scrollable row without touching document-level scroll
      // or focus navigation at all.
      const linkLeft = active.offsetLeft;
      const linkRight = linkLeft + active.offsetWidth;
      const viewLeft = links.scrollLeft;
      const viewRight = viewLeft + links.clientWidth;
      if (linkLeft < viewLeft) links.scrollLeft = linkLeft;
      else if (linkRight > viewRight) links.scrollLeft = linkRight - links.clientWidth;
    });
  }

  // Mirrors renumberExploreRows in v1-shell.js: flat sequential numbering,
  // no Secciones/Accesos directos grouping.
  function renumberExploreRows(list) {
    [...list.querySelectorAll('.explore-row__index')].forEach((idx, position) => {
      idx.textContent = String(position + 1);
    });
  }

  function makeExploreRow({ href, label, copy, preview }) {
    const item = document.createElement('div');
    item.className = 'explore-item';
    const link = document.createElement('a');
    link.className = 'explore-row';
    link.href = href;
    link.dataset.preview = preview;
    link.dataset.betaExplore = preview;

    const index = document.createElement('span');
    index.className = 'explore-row__index';
    const body = document.createElement('span');
    body.className = 'explore-row__body';
    const strong = document.createElement('strong');
    strong.textContent = label;
    const small = document.createElement('small');
    small.textContent = copy;
    body.append(strong, small);
    link.append(index, body);
    item.append(link);
    return item;
  }

  function ensureBetaExploreRows() {
    const dialog = document.querySelector('[data-explore-dialog]');
    const list = dialog?.querySelector('.explore-list');
    if (!dialog || !list || list.querySelector('[data-beta-explore]')) return;

    const rows = [
      makeExploreRow({
        href: BETA_READER_URL,
        label: 'Quiero ser lector beta',
        copy: 'Apúntate para recibir materiales sin publicar y compartir una opinión honesta.',
        preview: 'lectores-beta'
      }),
      makeExploreRow({
        href: BETA_MANUSCRIPT_URL,
        label: 'Quiero enviar mi manuscrito',
        copy: 'Información para autores que quieren consultar una valoración beta antes de compartir el archivo.',
        preview: 'lectores-beta-manuscrito'
      })
    ];
    const assistantLink = list.querySelector('[data-assistant-menu-link]');
    const assistantItem = assistantLink ? assistantLink.closest('.explore-item') : null;
    rows.forEach((row) => list.insertBefore(row, assistantItem || null));
    renumberExploreRows(list);

    const labelNode = dialog.querySelector('[data-preview-label]');
    const copyNode = dialog.querySelector('[data-preview-copy]');
    const media = dialog.querySelector('[data-preview-media]');
    const previews = {
      'lectores-beta': ['Lectores beta', 'Lee material sin publicar y comparte una opinión honesta en una lista separada de la newsletter.'],
      'lectores-beta-manuscrito': ['Enviar manuscrito', 'Consulta disponibilidad y condiciones antes de compartir un archivo para valoración beta.']
    };
    rows.forEach((row) => {
      const link = row.querySelector('a');
      if (!link) return;
      const show = () => {
        const value = previews[link.dataset.preview];
        if (!value) return;
        if (labelNode) labelNode.textContent = value[0];
        if (copyNode) copyNode.textContent = value[1];
        if (media) media.dataset.preview = link.dataset.preview;
      };
      link.addEventListener('mouseenter', show);
      link.addEventListener('focus', show);
    });
  }

  function ensureHomeBetaNav() {
    if (root.dataset.lrbHome !== 'true') return;
    const nav = document.querySelector('.masthead-nav');
    const list = nav?.querySelector('.masthead-nav__list');
    if (!nav || !list || list.querySelector('[data-beta-masthead]')) return;

    const item = document.createElement('li');
    item.className = 'masthead-nav__item';
    item.dataset.betaMasthead = 'true';
    const submenuId = 'masthead-submenu-lectores-beta';
    item.innerHTML = `
      <a href="/lectores-beta/" data-territory="lectores-beta" aria-haspopup="true">Lectores beta</a>
      <button type="button" class="masthead-nav__submenu-trigger" aria-label="Ver opciones de Lectores beta" aria-expanded="false" aria-controls="${submenuId}">
        <svg aria-hidden="true" viewBox="0 0 16 16" focusable="false"><path d="m4 6 4 4 4-4"/></svg>
      </button>
      <div class="masthead-nav__submenu" id="${submenuId}" aria-label="Opciones de Lectores beta">
        <a href="${BETA_READER_URL}">Quiero ser lector beta</a>
        <a href="${BETA_MANUSCRIPT_URL}">Quiero enviar mi manuscrito</a>
      </div>`;
    list.append(item);

    const trigger = item.querySelector('.masthead-nav__submenu-trigger');
    trigger?.addEventListener('click', (event) => {
      event.stopPropagation();
      const willOpen = !item.classList.contains('is-open');
      document.querySelectorAll('.masthead-nav__item.is-open').forEach((other) => {
        if (other === item) return;
        other.classList.remove('is-open');
        other.querySelector('.masthead-nav__submenu-trigger')?.setAttribute('aria-expanded', 'false');
      });
      item.classList.toggle('is-open', willOpen);
      trigger.setAttribute('aria-expanded', String(willOpen));
    });
    item.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') return;
      item.classList.remove('is-open');
      trigger?.setAttribute('aria-expanded', 'false');
      trigger?.focus({ preventScroll: true });
    });
  }

  function normalizeMemoriaLinks(scope = document) {
    scope.querySelectorAll?.(`a[href="${MEMORIA_EXTERNAL_URL}"]`).forEach((link) => {
      if (link.hasAttribute('data-memoria-official-source')) return;
      link.href = MEMORIA_INTERNAL_URL;
      link.removeAttribute('target');
      const rel = (link.getAttribute('rel') || '').split(/\s+/).filter(Boolean)
        .filter((token) => !['noopener', 'noreferrer', 'sponsored', 'nofollow'].includes(token));
      if (rel.length) link.setAttribute('rel', rel.join(' '));
      else link.removeAttribute('rel');
    });
  }

  function auditBannerAsset(banner) {
    if (!(banner instanceof HTMLElement)) return;
    if (!banner.querySelector('.feature-banner__placeholder')) {
      const key = banner.dataset.bannerKey || 'editorial';
      const labels = {
        manecillas: 'Banner pendiente · Las manecillas del recuerdo',
        samuel: 'Banner pendiente · Samuel entre mundos',
        memoria: 'Banner pendiente · La memoria de las tierras del norte',
        tools: 'Banner pendiente · Herramientas para escritores'
      };
      const placeholder = document.createElement('span');
      placeholder.className = 'feature-banner__placeholder';
      placeholder.setAttribute('aria-hidden', 'true');
      placeholder.textContent = `${labels[key] || 'Banner pendiente'} · 2400 × 900 px · foco central`;
      banner.prepend(placeholder);
    }

    const image = banner.querySelector('.feature-banner__image');
    if (!image) {
      banner.classList.add('feature-banner--placeholder-only');
      return;
    }
    const path = new URL(image.currentSrc || image.src, location.origin).pathname;
    const isFinalBanner = path.startsWith('/assets/banners/') || path === '/assets/david-porto-memoria-sinfondo.webp';
    banner.classList.toggle('feature-banner--placeholder-only', !isFinalBanner);
    banner.classList.toggle('feature-banner--final-asset', isFinalBanner);
  }

  function prepareMediaSlots() {
    document.querySelectorAll('.feature-banner').forEach(auditBannerAsset);
    if (root.dataset.lrbHome !== 'true') return;
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        const ownerBanner = mutation.target instanceof Element ? mutation.target.closest?.('.feature-banner') : null;
        if (ownerBanner) auditBannerAsset(ownerBanner);
        for (const node of mutation.addedNodes) {
          if (!(node instanceof Element)) continue;
          if (node.matches?.('.feature-banner')) auditBannerAsset(node);
          node.querySelectorAll?.('.feature-banner').forEach(auditBannerAsset);
          normalizeMemoriaLinks(node);
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => observer.disconnect(), 6000);
  }

  function init() {
    normalizeMemoriaLinks();
    ensureBetaExploreRows();
    ensureHomeBetaNav();
    buildContextNav();
    prepareMediaSlots();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
