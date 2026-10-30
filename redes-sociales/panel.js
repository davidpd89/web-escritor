import {lastKnownSocialMetrics, visibleSocialMetrics} from './gpt_social_reader.mjs';

const DATA_URL = '/redes-sociales/social-metrics.json';
const grid = document.getElementById('social-grid');
const totalEl = document.getElementById('social-total');
const updatedEl = document.getElementById('social-updated');
const number = new Intl.NumberFormat('es-ES', {useGrouping: 'always'});
const date = new Intl.DateTimeFormat('es-ES', {day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Madrid'});

function when(observed) {
  const stamp = /^\d{4}-\d{2}-\d{2}$/.test(observed) ? observed + 'T12:00:00Z' : observed;
  const parsed = new Date(stamp);
  return Number.isNaN(parsed.getTime()) ? null : date.format(parsed);
}

// The HTML ships the last published figures; live JSON refines them. A value that is
// not fresh (expired JSON or the shipped figure) is still shown, marked approximate with its date.
function render(fresh, known) {
  const rows = [];
  for (const card of grid.querySelectorAll('.social-card[data-network]')) {
    const id = card.dataset.network;
    const value = card.querySelector('[data-role="value"]');
    const live = fresh.networks.find(n => n.id === id);
    const last = known.networks.find(n => n.id === id);
    const shipped = {followers: Number(value.dataset.followers), observed_at: value.dataset.observed || null};
    // An expired JSON value never replaces a newer figure already printed in the page.
    const older = last && shipped.observed_at && String(last.observed_at).slice(0, 10) < shipped.observed_at;
    const pick = live?.followers != null ? live : last?.followers != null && !older ? last : shipped;
    rows.push({card, value, followers: pick.followers, approx: pick !== live, observed: pick.observed_at});
  }
  const total = rows.reduce((sum, r) => sum + (Number.isSafeInteger(r.followers) ? r.followers : 0), 0);
  if (!total) return;
  for (const r of rows) {
    r.value.textContent = (r.approx ? '≈ ' : '') + number.format(r.followers);
    const share = r.followers / total * 100;
    r.card.querySelector('[data-role="bar"]').style.width = Math.max(share, 1.5).toFixed(1) + '%';
    const label = r.observed && when(r.observed);
    const meta = r.card.querySelector('[data-role="meta"]');
    if (label) meta.textContent = `${share < 1 ? '<1' : Math.round(share)} % del total · ${r.approx ? 'Último dato' : 'Dato'} del ${label}`;
  }
  const approx = rows.some(r => r.approx);
  totalEl.textContent = (approx ? '≈ ' : '') + number.format(total);
  if (fresh.totals.coverage === fresh.totals.eligible) {
    updatedEl.textContent = 'Cifras de los perfiles oficiales, actualizadas automáticamente cada día.';
  } else if (approx) {
    updatedEl.textContent = 'Algunas cifras son aproximadas: muestran el último dato disponible de cada red.';
  }
}

fetch(DATA_URL, {cache: 'no-cache'})
  .then(r => (r.ok ? r.json() : null))
  .catch(() => null)
  .then(snapshot => render(visibleSocialMetrics(snapshot), lastKnownSocialMetrics(snapshot)));

// Native per-day tooltips, built here so the static HTML keeps a single <title>.
for (const hit of document.querySelectorAll('.social-chart rect[data-tip]')) {
  const tip = document.createElementNS('http://www.w3.org/2000/svg', 'title');
  tip.textContent = hit.dataset.tip;
  hit.append(tip);
}
