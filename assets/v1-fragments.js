(() => {
  const index = document.querySelector('[data-fragment-index]');
  if (!index) return;

  const links = [...index.querySelectorAll('[data-fragment-link]')];
  const sections = links
    .map(link => document.getElementById(link.dataset.fragmentLink))
    .filter(Boolean);

  const setCurrent = id => {
    links.forEach(link => {
      const active = link.dataset.fragmentLink === id;
      if (active) link.dataset.current = 'true';
      else delete link.dataset.current;
      const label = link.querySelector('[data-current-label]');
      if (label) label.textContent = active ? ' Fragmento actual.' : '';
    });
  };

  const idFromHash = () => {
    const id = decodeURIComponent(location.hash.slice(1));
    return sections.some(section => section.id === id) ? id : null;
  };

  const initial = idFromHash();
  if (initial) setCurrent(initial);

  addEventListener('hashchange', () => {
    const id = idFromHash();
    if (id) setCurrent(id);
  });

  if (!('IntersectionObserver' in window)) return;

  const ratios = new Map(sections.map(section => [section.id, 0]));
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => ratios.set(entry.target.id, entry.isIntersecting ? entry.intersectionRatio : 0));
    const current = [...ratios.entries()].sort((a, b) => b[1] - a[1])[0];
    if (current && current[1] > 0) setCurrent(current[0]);
  }, {
    rootMargin: '-18% 0px -55% 0px',
    threshold: [0, .15, .35, .6, .85]
  });

  sections.forEach(section => observer.observe(section));
})();
