import {visibleSocialMetrics} from './gpt_social_reader.mjs';

const DATA_URL = '/redes-sociales/social-metrics.json';
const grid = document.getElementById('social-grid');
const totalEl = document.getElementById('social-total');
const number = new Intl.NumberFormat('es-ES');
const date = new Intl.DateTimeFormat('es-ES', {day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Madrid'});

function when(observed) {
  const stamp = /^\d{4}-\d{2}-\d{2}$/.test(observed) ? observed + 'T12:00:00Z' : observed;
  const parsed = new Date(stamp);
  return Number.isNaN(parsed.getTime()) ? null : date.format(parsed);
}

function render(view) {
  for (const net of view.networks) {
    const card = grid.querySelector(`[data-network="${net.id}"]`);
    if (!card) continue;
    const count = card.querySelector('[data-role="count"]');
    const meta = card.querySelector('[data-role="meta"]');
    if (net.followers === null) {
      count.textContent = 'Dato no disponible';
      meta.textContent = 'Sin medición vigente.';
      continue;
    }
    count.textContent = `${number.format(net.followers)} seguidores`;
    const label = net.observed_at && when(net.observed_at);
    meta.textContent = label ? `Actualizado: ${label}` : 'Medición vigente.';
  }
  const t = view.totals;
  if (t.follower_relationships === null) {
    totalEl.hidden = true;
    return;
  }
  totalEl.textContent = `${number.format(t.follower_relationships)} seguidores sumados en ${t.coverage} de ${t.eligible} redes con datos vigentes (no son personas únicas).`;
  totalEl.hidden = false;
}

fetch(DATA_URL, {cache: 'no-cache'})
  .then(r => (r.ok ? r.json() : null))
  .catch(() => null)
  .then(snapshot => render(visibleSocialMetrics(snapshot)));
