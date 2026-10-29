import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// MW-0103: en modo de contraste forzado los separadores de la columna lateral de la portada siguen visibles.
const origin = process.env.SITE_ORIGIN;
assert.ok(origin, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');

const browser = await chromium.launch({ headless: true });
try {
  async function medir(forcedColors) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, forcedColors, reducedMotion: 'reduce' });
    await page.addInitScript(() => { try { sessionStorage.setItem('dp-intro-seen', '1'); localStorage.setItem('nl-subscribed', '1'); } catch (e) {} });
    await page.goto(`${origin.replace(/\/$/, '')}/`, { waitUntil: 'load', timeout: 20000 });
    await page.locator('.yale-rail').first().waitFor({ state: 'attached', timeout: 10000 });
    const r = await page.evaluate(() => {
      const rail = document.querySelector('.yale-rail');
      const cards = [...rail.querySelectorAll('.yale-rail-card')];
      return { cards: cards.length, railLeft: parseFloat(getComputedStyle(rail).borderLeftWidth), between: cards.slice(0, -1).map(c => parseFloat(getComputedStyle(c).borderBottomWidth)) };
    });
    await page.close();
    return r;
  }
  const normal = await medir('none');
  assert.equal(normal.railLeft, 0, 'en modo normal no se añaden bordes (los separadores son los degradados)');
  assert.ok(normal.cards >= 2, 'la columna tiene varias tarjetas');
  const forzado = await medir('active');
  assert.ok(forzado.railLeft >= 2, `contraste forzado: borde lateral visible (${forzado.railLeft}px)`);
  assert.ok(forzado.between.every(w => w >= 1), `contraste forzado: separador entre tarjetas (${forzado.between})`);
  console.log('PASS MW-0103: separadores de la columna lateral visibles en contraste forzado, sin cambios en modo normal');
} finally {
  await browser.close();
}
