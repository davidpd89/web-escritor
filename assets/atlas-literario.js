(() => {
  const root = document.querySelector('[data-atlas-index]');
  if (!root) return;
  const search = root.querySelector('[data-atlas-search]');
  const category = root.querySelector('[data-atlas-category]');
  const cards = [...root.querySelectorAll('[data-atlas-card]')];
  const count = root.querySelector('[data-atlas-count]');
  const normalize = (s='') => s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const apply = () => {
    const q = normalize(search?.value || '');
    const c = category?.value || '';
    let visible = 0;
    cards.forEach(card => {
      const hay = normalize(card.dataset.search || card.textContent || '');
      const ok = (!q || hay.includes(q)) && (!c || card.dataset.category === c);
      card.hidden = !ok;
      if (ok) visible++;
    });
    if (count) count.textContent = `${visible} ${visible === 1 ? 'artículo' : 'artículos'}`;
  };
  search?.addEventListener('input', apply);
  category?.addEventListener('change', apply);
  apply();
})();
