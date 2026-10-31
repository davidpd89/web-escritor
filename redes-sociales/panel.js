import {lastKnownSocialMetrics, visibleSocialMetrics} from './gpt_social_reader.mjs';

const DATA_URL = '/redes-sociales/social-metrics.json';
const grid = document.getElementById('social-grid');
const totalEl = document.getElementById('social-total');
const updatedEl = document.getElementById('social-updated');
const number = new Intl.NumberFormat('es-ES', {useGrouping: 'always'});

// The HTML ships the last published figures; live JSON refines them. A value that is
// not fresh (expired JSON or the shipped figure) is still shown, marked approximate.
// Cards marked data-static (networks outside the JSON) keep their printed figure.
// Pinterest's card leads with views, so only the total includes its followers.
function render(fresh, known) {
  const pickOf = (id, shipped) => {
    const live = fresh.networks.find(n => n.id === id);
    const last = known.networks.find(n => n.id === id);
    // An expired JSON value never replaces a newer figure already printed in the page.
    const older = last && shipped.observed_at && String(last.observed_at).slice(0, 10) < shipped.observed_at;
    const pick = live?.followers != null ? live : last?.followers != null && !older ? last : shipped;
    return {followers: pick.followers, approx: pick !== live};
  };
  const rows = [];
  for (const value of grid.querySelectorAll('[data-followers-of][data-value]')) {
    const id = value.dataset.followersOf;
    const shipped = {followers: Number(value.dataset.value), observed_at: value.dataset.observed || null};
    const pick = value.dataset.static ? {followers: shipped.followers, approx: false} : pickOf(id, shipped);
    rows.push({id, ...pick});
  }
  const pinterest = pickOf('pinterest', {followers: Number(totalEl.dataset.pinterest), observed_at: null});
  rows.push({id: 'pinterest', ...pinterest, approx: false, hidden: true});
  const total = rows.reduce((sum, r) => sum + (Number.isSafeInteger(r.followers) ? r.followers : 0), 0);
  if (!total) return;
  for (const r of rows) {
    if (r.hidden || !Number.isSafeInteger(r.followers)) continue;
    const text = (r.approx ? '≈ ' : '') + number.format(r.followers);
    // Bubbles are sized for the bare number; the card keeps the approximate mark.
    for (const el of document.querySelectorAll(`[data-followers-of="${r.id}"]`)) el.textContent = el.closest('.social-bubble') ? number.format(r.followers) : text;
    const bubble = document.querySelector(`.social-bubble [data-followers-of="${r.id}"]`)?.parentElement;
    if (bubble) bubble.setAttribute('aria-label', `${bubble.dataset.name}: ${text} seguidores (se abre en una pestaña nueva)`);
  }
  const approx = rows.some(r => r.approx);
  totalEl.textContent = (approx ? '≈ ' : '') + number.format(total);
  // The stamp follows the newest live reading; the printed date stays if none is newer.
  const newest = fresh.networks.map(n => String(n.observed_at || '').slice(0, 10)).filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort().pop();
  if (updatedEl && newest && newest > updatedEl.dateTime) {
    updatedEl.dateTime = newest;
    updatedEl.textContent = new Intl.DateTimeFormat('es-ES', {day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC'}).format(new Date(newest + 'T12:00:00Z'));
  }
}

fetch(DATA_URL, {cache: 'no-cache'})
  .then(r => (r.ok ? r.json() : null))
  .catch(() => null)
  .then(snapshot => render(visibleSocialMetrics(snapshot), lastKnownSocialMetrics(snapshot)));
