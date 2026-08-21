(() => {
  'use strict';
  const fixture = document.documentElement.dataset.fixture || 'normal';
  const q = (s) => document.querySelector(s);
  const qa = (s) => [...document.querySelectorAll(s)];

  const hideMeta = (...names) => names.forEach((name) => {
    const row = q(`[data-book-meta="${name}"]`);
    if (row) row.hidden = true;
  });

  switch (fixture) {
    case 'partial-meta':
      hideMeta('pvp', 'paginas');
      break;
    case 'sparse-meta':
      hideMeta('pvp', 'paginas', 'isbn');
      break;
    case 'related-none': {
      const related = q('[data-book-related]');
      if (related) related.hidden = true;
      break;
    }
    case 'related-one': {
      const secondary = q('[data-related-secondary]');
      if (secondary) secondary.hidden = true;
      break;
    }
    case 'no-context': {
      const context = q('[data-book-context]');
      if (context) context.hidden = true;
      break;
    }
    case 'long-title': {
      const title = q('[data-book-title]');
      if (title) title.textContent = 'Las manecillas del recuerdo — una edición de prueba con un título deliberadamente largo';
      break;
    }
    case 'empty-related-secondary':
      qa('[data-related-secondary] a').forEach((link) => link.hidden = true);
      break;
    default:
      break;
  }
})();
