/* PR95 V4 — persistent local navigation + editorial media placeholders.
   Progressive enhancement: every destination remains a real static URL and
   the global Explore/footer continue to work if JavaScript is unavailable. */
(() => {
  'use strict';

  const root = document.documentElement;
  if (!root.classList.contains('v1')) return;

  const MEMORIA_EXTERNAL_URL = 'https://www.diversidadliteraria.com/la-memoria-de-las-tierras-del-norte';
  const MEMORIA_INTERNAL_URL = '/libros/#memoria-tierras-norte';

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
        ['/las-manecillas-del-recuerdo/kindle/', 'Kindle'],
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
        ['/libros/samuel-entre-mundos/', 'Samuel entre mundos'],
        ['/libros/#memoria-tierras-norte', 'La memoria de las tierras del norte']
      ]
    },
    {
      key: 'cuaderno', label: 'Cuaderno', home: '/cuaderno/',
      matches: (path) => path.startsWith('/cuaderno/'),
      links: [
        ['/autor.html', '← Autor'],
        ['/cuaderno/', 'Archivo']
      ]
    },
    /* `key` es el id del sistema visual (CSS data-editorial-context), no la
       sección del menú: «Libros recomendados» conserva el de cuaderno y el
       directorio editorial/concursos el de herramientas para no perder estilos. */
    {
      key: 'cuaderno', label: 'Libros recomendados', home: '/recomendaciones/',
      matches: (path) => path.startsWith('/recomendaciones/') || path.startsWith('/atlas-literario/'),
      links: [
        ['/recomendaciones/', 'Catálogo'],
        ['/recomendaciones/autores/', 'Autores'],
        ['/editoriales/', 'Editoriales'],
        ['/atlas-literario/', 'Atlas literario'],
        ['/convocatorias-escritores/', 'Concursos']
      ]
    },
    {
      key: 'herramientas', label: 'Libros recomendados', home: '/recomendaciones/',
      matches: (path) => path.startsWith('/editoriales/') || path.startsWith('/convocatorias-escritores/'),
      links: [
        ['/recomendaciones/', 'Catálogo'],
        ['/recomendaciones/autores/', 'Autores'],
        ['/editoriales/', 'Editoriales'],
        ['/atlas-literario/', 'Atlas literario'],
        ['/convocatorias-escritores/', 'Concursos']
      ]
    },
    {
      key: 'herramientas', label: 'Herramientas', home: '/herramientas/',
      matches: (path) => path.startsWith('/herramientas/') || path === '/clubes-de-lectura/preparar-sesion/' || path === '/recursos/ficha-historia-objeto-heredado/',
      links: [
        ['/herramientas/', 'Todas las herramientas'],
        ['/herramientas/manuscrito/', 'Manuscrito'],
        ['/herramientas/dialogo/', 'Diálogo'],
        ['/herramientas/repeticiones/', 'Repeticiones'],
        ['/herramientas/metadatos-libro/', 'Publicar y promocionar']
      ]
    },
    {
      key: 'herramientas', label: 'Editoriales', home: '/editoriales/',
      matches: (path) => path.startsWith('/metodologia-editorial/'),
      links: [
        ['/editoriales/', 'Editoriales'],
        ['/metodologia-editorial/', 'Metodología']
      ]
    },
    {
      key: 'autor', label: 'Autor', home: '/autor.html',
      matches: (path) => path === '/autor.html' || path === '/premios.html' || path === '/al-otro-lado/' || path.startsWith('/lectores-beta/'),
      links: [
        ['/autor.html', 'Autor'],
        ['/premios.html', 'Premios'],
        ['/eventos.html', 'Eventos'],
        ['/cuaderno/', 'Cuaderno'],
        ['/lectores-beta/', 'Lectores beta']
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
    if (root.dataset.lrbHome === 'true') return;
    const existing = document.querySelector('.section-context');
    if (existing) {
      revealActiveContextLink(existing.querySelector('.section-context__links'));
      return;
    }
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
    // At most one link is ever "current": an exact match always wins over a
    // family/prefix match, and among family matches only the longest (most
    // specific) prefix qualifies. Scoring every link independently used to
    // let an exact match ("El libro") and its own ancestor family link
    // ("← Obras") both claim aria-current="page" on the same page.
    // Mirrors FAMILY_ALIASES in scripts/build-section-context-nav.py: las
    // fichas de sellos del catálogo marcan «Editoriales» aunque el enlace
    // lleve al directorio general.
    const familyAliases = { '/editoriales/': ['/recomendaciones/editoriales/'] };
    const scored = context.links.map(([href, label]) => {
      const linkPath = normalise(href);
      const exact = currentPath === linkPath;
      const matched = [linkPath, ...(familyAliases[linkPath] || [])]
        .filter((prefix) => prefix.endsWith('/') && prefix !== '/' && currentPath.startsWith(prefix));
      const familyMatch = !exact && matched.length > 0;
      const depth = matched.length ? Math.max(...matched.map((prefix) => prefix.length)) : linkPath.length;
      return { href, label, linkPath, exact, familyMatch, depth };
    });
    const exactMatch = scored.find((item) => item.exact);
    const bestFamilyMatch = !exactMatch && scored
      .filter((item) => item.familyMatch)
      .sort((a, b) => b.depth - a.depth)[0];
    const currentItem = exactMatch || bestFamilyMatch || null;
    scored.forEach((item) => {
      const link = document.createElement('a');
      link.href = item.href;
      link.textContent = item.label;
      if (item === currentItem) link.setAttribute('aria-current', 'page');
      links.append(link);
    });

    inner.append(title, links);
    nav.append(inner);
    header.insertAdjacentElement('afterend', nav);

    revealActiveContextLink(links);
  }

  // Deja a la vista el enlace actual dentro de la fila desplazable de la barra
  // de sección. Antes solo se hacía cuando el JS creaba la barra; las ~440
  // páginas con la barra pre-renderizada (build-section-context-nav.py) nunca
  // lo hacían, y en tablet/móvil el elemento actual podía quedar fuera.
  function revealActiveContextLink(links) {
    const active = links?.querySelector('[aria-current="page"]');
    if (!active) return;
    requestAnimationFrame(() => {
      // Element.scrollIntoView() here (even with block/inline:'nearest') was
      // shifting Chromium's sequential focus-navigation starting point to
      // this link on page load, so the very first real Tab press landed on
      // it instead of the skip-link -- a serious a11y regression. Adjusting
      // the strip's own scrollLeft directly reveals the active item in its
      // horizontally-scrollable row without touching document-level scroll
      // or focus navigation at all.
      if (links.scrollWidth <= links.clientWidth) return;
      const box = active.getBoundingClientRect();
      const view = links.getBoundingClientRect();
      if (box.left < view.left) links.scrollLeft -= view.left - box.left;
      else if (box.right > view.right) links.scrollLeft += box.right - view.right;
    });
  }

  /* Lectores beta ya no se inyecta aquí: Explorar y la barra de la home lo
     reciben estático desde data/navigation.json (exploreExtras) vía
     scripts/build-site-shell.py, con la misma forma que los demás territorios
     y también sin JavaScript. */

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

  function prepareMediaSlots() {
    if (root.dataset.lrbHome !== 'true') return;
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
          if (!(node instanceof Element)) continue;
          normalizeMemoriaLinks(node);
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => observer.disconnect(), 6000);
  }

  /* Pie «Anterior · Índice · Siguiente» al final de las fichas hermanas
     (editoriales, libros, autores, herramientas, Cuaderno, Atlas). El orden
     sale de assets/page-order.generated.js (scripts/build-page-order.py); si la
     ficha aún no figura allí o el script falla, simplemente no se pinta. Va al
     final de <main>, fuera de la primera pantalla, así que no mueve el diseño. */
  function buildSiblingPager() {
    const main = document.querySelector('main');
    if (!main || root.dataset.lrbHome === 'true' || main.querySelector('.sibling-pager')) return;
    const here = currentPath;
    if (!/^\/(editoriales|recomendaciones|herramientas|cuaderno|atlas-literario)\/./.test(here)) return;
    const render = () => {
      const data = window.DP_PAGE_ORDER;
      if (!data || !Array.isArray(data.families) || main.querySelector('.sibling-pager')) return;
      const family = data.families.find((item) => here.startsWith(item.prefix));
      if (!family) return;
      const position = family.items.findIndex((item) => item[0] === here);
      if (position === -1) return;
      const total = family.items.length;
      const nav = document.createElement('nav');
      nav.className = 'sibling-pager';
      nav.setAttribute('aria-label', `Seguir navegando: ${family.hub.label}`);
      const cell = (neighbour, rel, caption) => {
        const holder = document.createElement(neighbour ? 'a' : 'span');
        holder.className = `sibling-pager__link sibling-pager__link--${rel}`;
        if (!neighbour) return holder;
        holder.href = neighbour[0];
        holder.rel = rel;
        const small = document.createElement('small');
        small.textContent = caption;
        const strong = document.createElement('strong');
        strong.textContent = neighbour[1];
        holder.append(small, strong);
        return holder;
      };
      const hub = document.createElement('a');
      hub.className = 'sibling-pager__hub';
      hub.href = family.hub.href;
      const hubLabel = document.createElement('strong');
      hubLabel.textContent = family.hub.label;
      const count = document.createElement('small');
      count.textContent = `${position + 1} de ${total}`;
      hub.append(hubLabel, count);
      nav.append(
        cell(family.items[position - 1], 'prev', '← Anterior'),
        hub,
        cell(family.items[position + 1], 'next', 'Siguiente →')
      );
      main.append(nav);
    };
    if (window.DP_PAGE_ORDER) return render();
    const script = document.createElement('script');
    script.src = '/assets/page-order.generated.js';
    script.async = true;
    script.addEventListener('load', render, { once: true });
    document.head.append(script);
  }

  function init() {
    normalizeMemoriaLinks();
    buildContextNav();
    buildSiblingPager();
    prepareMediaSlots();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
