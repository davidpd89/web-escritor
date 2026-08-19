(() => {
  const buttons = [...document.querySelectorAll('[data-filter]')];
  const cards = [...document.querySelectorAll('[data-tool]')];
  const count = document.querySelector('[data-tool-count]');
  if (!buttons.length || !cards.length) return;
  const groups = {
    revisar: new Set(['revisar-texto','revisar-manuscrito']),
    estructura: new Set(['personajes-estructura']),
    publicar: new Set(['publicar-web','publicar-promocionar','lectura-eventos']),
    investigar: new Set(['investigar-recordar'])
  };
  function matches(card, filter) {
    if (filter === 'all') return true;
    if (filter === 'local') return card.dataset.privacy === 'local';
    return groups[filter]?.has(card.dataset.category) || false;
  }
  function apply(filter) {
    let visible = 0;
    cards.forEach(card => { const show = matches(card, filter); card.hidden = !show; if (show) visible++; });
    document.querySelectorAll('[data-tool-section]').forEach(section => { section.hidden = !section.querySelector('[data-tool]:not([hidden])'); });
    buttons.forEach(btn => btn.setAttribute('aria-pressed', String(btn.dataset.filter === filter)));
    if (count) count.textContent = `${visible} ${visible === 1 ? 'herramienta' : 'herramientas'}`;
  }
  buttons.forEach(btn => btn.addEventListener('click', () => apply(btn.dataset.filter)));
})();
