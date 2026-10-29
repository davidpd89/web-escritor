import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// MW-0072: el vídeo de la introducción no se descarga con el ahorro de datos activado ni en conexiones 2G; en el resto sigue cargando.
const origin = process.env.SITE_ORIGIN;
assert.ok(origin, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');

const browser = await chromium.launch({ headless: true });
try {
  async function fuente(connection) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await page.addInitScript(c => {
      try { localStorage.setItem('nl-subscribed', '1'); } catch (e) {}
      if (c) Object.defineProperty(navigator, 'connection', { value: c, configurable: true });
    }, connection);
    const pedidos = [];
    page.on('request', r => { if (/hero-tinta-david-porto\.mp4/.test(r.url())) pedidos.push(r.url()); });
    await page.goto(`${origin.replace(/\/$/, '')}/`, { waitUntil: 'load', timeout: 20000 });
    await page.waitForTimeout(1200);
    const src = await page.evaluate(() => document.querySelector('[data-hero-video] source')?.getAttribute('src') || '');
    await page.close();
    return { src, pedidos: pedidos.length };
  }
  const normal = await fuente(null);
  assert.match(normal.src, /hero-tinta-david-porto\.mp4/, 'sin restricciones el vídeo se carga');
  const ahorro = await fuente({ saveData: true, effectiveType: '4g' });
  assert.equal(ahorro.src, '', 'con ahorro de datos el vídeo no recibe src');
  assert.equal(ahorro.pedidos, 0, 'con ahorro de datos no se solicita el vídeo');
  const lento = await fuente({ saveData: false, effectiveType: '2g' });
  assert.equal(lento.src, '', 'en 2G el vídeo no recibe src');
  const slow2g = await fuente({ saveData: false, effectiveType: 'slow-2g' });
  assert.equal(slow2g.src, '', 'en slow-2g el vídeo no recibe src');
  const rapido = await fuente({ saveData: false, effectiveType: '4g' });
  assert.match(rapido.src, /hero-tinta-david-porto\.mp4/, 'en 4g sin ahorro de datos sigue cargando');
  console.log('PASS MW-0072: sin vídeo con ahorro de datos o 2G; con conexión normal sigue cargando');
} finally {
  await browser.close();
}
