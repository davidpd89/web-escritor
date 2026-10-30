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

// Donut segments: circumference 100 (r = 15.9155), first segment starts at 12 o'clock.
function drawDonut(rows, total) {
  let offset = 25;
  for (const r of rows) {
    const seg = document.querySelector(`.social-donut circle[data-network="${r.id}"]`);
    const legend = document.querySelector(`[data-legend="${r.id}"]`);
    const share = r.followers / total * 100;
    if (seg) {
      seg.setAttribute('stroke-dasharray', `${share.toFixed(2)} ${(100 - share).toFixed(2)}`);
      seg.setAttribute('stroke-dashoffset', offset.toFixed(2));
    }
    if (legend) legend.textContent = number.format(r.followers);
    offset -= share;
  }
}

// The HTML ships the last published figures; live JSON refines them. A value that is
// not fresh (expired JSON or the shipped figure) is still shown, marked approximate with its date.
// Cards marked data-static (networks outside the JSON) keep their printed, dated figure.
function render(fresh, known) {
  const rows = [];
  for (const card of grid.querySelectorAll('.social-card[data-network]')) {
    const id = card.dataset.network;
    const value = card.querySelector('[data-role="value"]');
    const shipped = {followers: Number(value.dataset.followers), observed_at: value.dataset.observed || null};
    if (value.dataset.static) {
      rows.push({id, card, value, followers: shipped.followers, approx: false, observed: shipped.observed_at});
      continue;
    }
    const live = fresh.networks.find(n => n.id === id);
    const last = known.networks.find(n => n.id === id);
    // An expired JSON value never replaces a newer figure already printed in the page.
    const older = last && shipped.observed_at && String(last.observed_at).slice(0, 10) < shipped.observed_at;
    const pick = live?.followers != null ? live : last?.followers != null && !older ? last : shipped;
    rows.push({id, card, value, followers: pick.followers, approx: pick !== live, observed: pick.observed_at});
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
  drawDonut(rows, total);
  const approx = rows.some(r => r.approx && !r.value.dataset.static);
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

// Per-day tooltip + crosshair, built here so the static HTML keeps a single <title> and no inline JS.
// data-tip format: "29 oct · Total 10.157 · Bluesky 5.105 · ..."
const area = document.querySelector('.social-chart__area');
const tip = area?.querySelector('.social-chart__tip');
const cross = area?.querySelector('.social-chart__cross');
if (area && tip && cross) {
  const colors = {};
  for (const band of document.querySelectorAll('.social-chart__legend li')) {
    const swatch = band.querySelector('.social-swatch');
    if (swatch) colors[band.textContent.trim()] = swatch.style.background;
  }
  const show = hit => {
    const [day, ...parts] = hit.dataset.tip.split(' · ');
    tip.replaceChildren();
    const head = document.createElement('strong');
    head.textContent = day;
    tip.append(head);
    for (const part of parts) {
      const cut = part.lastIndexOf(' ');
      const name = part.slice(0, cut);
      const row = document.createElement('span');
      if (name === 'Total') row.className = 'is-total';
      else {
        const dot = document.createElement('i');
        dot.style.setProperty('--net', colors[name] || 'currentColor');
        row.append(dot);
      }
      const b = document.createElement('b');
      b.textContent = part.slice(cut + 1);
      row.append(name, b);
      tip.append(row);
    }
    const x = Number(hit.getAttribute('x')) + Number(hit.getAttribute('width')) / 2;
    cross.setAttribute('d', `M${x.toFixed(1)} 0V1000`);
    cross.classList.add('is-on');
    tip.hidden = false;
    const ratio = x / 1000;
    tip.style.left = ratio > 0.55 ? '' : `calc(${(ratio * 100).toFixed(1)}% + 12px)`;
    tip.style.right = ratio > 0.55 ? `calc(${((1 - ratio) * 100).toFixed(1)}% + 12px)` : '';
  };
  const hide = () => {
    tip.hidden = true;
    cross.classList.remove('is-on');
  };
  area.addEventListener('pointermove', event => {
    const hit = event.target.closest?.('rect[data-tip]');
    if (hit) show(hit);
  });
  area.addEventListener('pointerleave', hide);
  area.addEventListener('pointerdown', event => {
    const hit = event.target.closest?.('rect[data-tip]');
    if (hit) show(hit);
  });
}
