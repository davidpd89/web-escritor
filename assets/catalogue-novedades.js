// Novedades: el HTML lleva la fecha absoluta de cada día; aquí se antepone «Hoy», «Mañana» o «Pasado mañana»
// según el día civil de Madrid (no el del navegador), también en el cambio de hora.
(() => {
  'use strict';
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
  const today = Date.parse(parts + 'T00:00:00Z');
  const names = ['Hoy', 'Mañana', 'Pasado mañana'];
  for (const section of document.querySelectorAll('[data-novelty-day]')) {
    const offset = Math.round((Date.parse(section.dataset.noveltyDay + 'T00:00:00Z') - today) / 86400000);
    const label = section.querySelector('[data-novelty-relative]');
    if (!label || !names[offset]) continue;
    label.textContent = names[offset] + ' ·';
    label.hidden = false;
  }
})();
