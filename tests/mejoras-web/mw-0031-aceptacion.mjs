import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// MW-0031: la portada 3D de Samuel en la portada se sirve en AVIF con el WebP como alternativa.
const origin = process.env.SITE_ORIGIN;
assert.ok(origin, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.addInitScript(() => { try { localStorage.setItem('nl-subscribed', '1'); sessionStorage.setItem('dp-intro-seen', '1'); } catch (e) {} });
  const pedidos = [];
  page.on('request', r => { if (/samuel_entre_mundos_3d\.(avif|webp)/.test(r.url())) pedidos.push(r.url().split('/').pop()); });
  await page.goto(`${origin.replace(/\/$/, '')}/`, { waitUntil: 'load', timeout: 20000 });
  const imgs = page.locator('img[src$="samuel_entre_mundos_3d.webp"]');
  await imgs.first().waitFor({ state: 'attached', timeout: 10000 });
  const total = await imgs.count();
  assert.ok(total >= 1, 'hay imágenes de la portada de Samuel');
  for (let i = 0; i < total; i++) {
    await imgs.nth(i).scrollIntoViewIfNeeded();
    const info = await imgs.nth(i).evaluate(el => ({
      picture: el.parentElement.tagName,
      source: el.parentElement.querySelector('source')?.getAttribute('type') + ' ' + el.parentElement.querySelector('source')?.getAttribute('srcset'),
      width: el.getAttribute('width'), height: el.getAttribute('height'), alt: el.alt,
    }));
    assert.equal(info.picture, 'PICTURE', 'la imagen va dentro de <picture>');
    assert.equal(info.source, 'image/avif /assets/samuel_entre_mundos_3d.avif', 'el <source> AVIF precede al WebP');
    assert.ok(info.width && info.height && info.alt, 'se conservan dimensiones y texto alternativo');
  }
  await page.waitForFunction(() => [...document.images].filter(i => /samuel_entre_mundos_3d/.test(i.currentSrc)).every(i => i.complete));
  const actuales = await page.evaluate(() => [...document.images].filter(i => /samuel_entre_mundos_3d/.test(i.currentSrc)).map(i => i.currentSrc.split('/').pop()));
  assert.ok(actuales.length >= 1 && actuales.every(n => n === 'samuel_entre_mundos_3d.avif'), `Chromium usa el AVIF (${actuales})`);
  assert.equal(pedidos.some(n => n.endsWith('.webp')), false, 'no se descarga el WebP cuando el AVIF se admite');
  console.log('PASS MW-0031: portada de Samuel en AVIF con WebP de reserva, sin descargar ambos');
} finally {
  await browser.close();
}
