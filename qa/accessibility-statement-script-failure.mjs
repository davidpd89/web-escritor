import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });

async function inspect(context, label) {
  const page = await context.newPage();
  try {
    const response = await page.goto(`${ORIGIN}/accesibilidad/`, { waitUntil: 'domcontentloaded' });
    assert.equal(response?.status(), 200, `${label}: HTTP ${response?.status()}`);
    const state = await page.evaluate(() => {
      const main = document.querySelector('main');
      const heading = main?.querySelector('h1')?.textContent?.trim() || '';
      const text = main?.textContent?.trim() || '';
      const links = [...document.querySelectorAll('a[href]')].filter(a => a.getAttribute('href') && !a.getAttribute('href').startsWith('javascript:'));
      const skip = [...document.querySelectorAll('a[href^="#"]')].some(a => {
        const target = document.getElementById(a.getAttribute('href').slice(1));
        return target && (target === main || main?.contains(target));
      });
      return { heading, length: text.length, links: links.length, skip };
    });
    assert.match(state.heading, /accesibilidad/i, `${label}: H1 inesperado: ${state.heading}`);
    assert.ok(state.length > 300, `${label}: contenido insuficiente: ${state.length}`);
    assert.ok(state.links > 0, `${label}: no quedan enlaces navegables`);
    assert.ok(state.skip, `${label}: salto al contenido no operativo`);
    return state;
  } finally {
    await page.close();
  }
}

try {
  const nojs = await browser.newContext({ javaScriptEnabled: false });
  const blocked = await browser.newContext({ javaScriptEnabled: true });
  await blocked.route('**/*.js*', async route => {
    if (new URL(route.request().url()).origin === ORIGIN) await route.abort('failed');
    else await route.abort('blockedbyclient');
  });
  const [a, b, c, d] = await Promise.all([
    inspect(nojs, 'sin JS primera carga'),
    inspect(nojs, 'sin JS segunda carga'),
    inspect(blocked, 'scripts fallidos primera carga'),
    inspect(blocked, 'scripts fallidos segunda carga')
  ]);
  assert.equal(a.heading, c.heading, 'accesibilidad: H1 distinto al fallar scripts');
  assert.equal(a.length, c.length, 'accesibilidad: contenido principal alterado por scripts fallidos');
  assert.equal(b.heading, d.heading, 'accesibilidad: H1 inconsistente entre cargas');
  await nojs.close();
  await blocked.close();
  console.log('PASS accessibility statement script failure resilience');
} finally {
  await browser.close();
}