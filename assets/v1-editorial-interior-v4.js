/* PR95 V4 — persistent local navigation + editorial media placeholders.
   Progressive enhancement: every destination remains a real static URL and
   the global Explore/footer continue to work if JavaScript is unavailable. */
(() => {
  'use strict';

  const root = document.documentElement;
  if (!root.classList.contains('v1')) return;

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
        ['/las-manecillas-del-recuerdo/', 'La novela'],
        ['/las-manecillas-del-recuerdo/fragmentos/', 'Fragmentos'],
        ['/prensa.html#ficha-manecillas', 'Ficha de prensa']
      ]
    },
    {
      key: 'samuel', label: 'Samuel entre mundos', home: '/libros/samuel-entre-mundos/',
      matches: (path) => path.startsWith('/libros/samuel-entre-mundos/') || path === '/fragmento/' || path.startsWith('/universo/noveris/') || path.startsWith('/clubes-de-lectura/samuel-entre-mundos/'),
      links: [
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
      matches: (path) => path === '/autor.html' || path === '/premios.html',
      links: [
        ['/autor.html', 'Autor'],
        ['/premios.html', 'Premios'],
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
    if (active) requestAnimationFrame(() => active.scrollIntoView({ block: 'nearest', inline: 'nearest' }));
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
    const isFinalBanner = path.startsWith('/assets/banners/');
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
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => observer.disconnect(), 6000);
  }

  function init() {
    buildContextNav();
    prepareMediaSlots();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
