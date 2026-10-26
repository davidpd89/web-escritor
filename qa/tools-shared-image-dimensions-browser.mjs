import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/herramientas/eventos-ics/', '/herramientas/tiempo-lectura-voz-alta/', '/clubes-de-lectura/preparar-sesion/', '/herramientas/entrevista-familiar/', '/recursos/ficha-historia-objeto-heredado/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const route of routes) {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200, `${route}: HTTP ${response.status()}`);
    const images = await page.locator('img').evaluateAll(els => els.filter(img => {
      const css = getComputedStyle(img);
      return css.display !== 'none' && css.visibility !== 'hidden' && img.getClientRects().length > 0;
    }).map(img => {
      const css = getComputedStyle(img);
      const width = Number(img.getAttribute('width'));
      const height = Number(img.getAttribute('height'));
      const htmlSize = width > 0 && height > 0;
      const ratio = css.aspectRatio;
      const cssRatio = ratio !== 'auto' && ratio !== 'auto 0 / 0' && ratio !== 'normal';
      return { src: img.currentSrc || img.src, reserved: htmlSize || cssRatio };
    }));
    for (const img of images) assert.ok(img.reserved, `${route}: imagen sin dimensiones reservadas: ${img.src}`);
    await page.close();
  }
} finally { await browser.close(); }
console.log('OK: imágenes con espacio reservado');