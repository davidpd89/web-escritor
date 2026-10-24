import assert from 'node:assert/strict';
import { startSite, launch } from '../qa/errores-progresivo-browser-fixture.mjs';
const site = await startSite();
const browser = await launch();
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto(site.origin + '/offline.html');
  await page.evaluate(() => { document.documentElement.style.zoom = '4'; });
  const state = await page.evaluate(() => ({
    width: innerWidth, scroll: document.documentElement.scrollWidth,
    card: (() => { const r = document.querySelector('.offline-card').getBoundingClientRect(); return { left: r.left, right: r.right }; })(),
    buttons: [...document.querySelectorAll('.actions button:not([hidden])')].map(node => {
      const rect = node.getBoundingClientRect(); return { width: rect.width, height: rect.height };
    }),
  }));
  assert(state.scroll <= state.width + 2, `400% zoom produced horizontal overflow ${JSON.stringify(state)}`);
  assert(state.card.left >= -1 && state.card.right <= state.width + 2,
    'Recovery card clipped at 400% zoom');
  assert(state.buttons.length >= 1 && state.buttons.every(x => x.width >= 44 && x.height >= 44),
    'Offline recovery target too small at 400% zoom');
} finally { await browser.close(); await site.close(); }
console.log('PASS offline 400% reflow and controls');
