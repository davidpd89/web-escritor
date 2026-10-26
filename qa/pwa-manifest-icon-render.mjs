import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const response = await page.goto(`${base}/`, { waitUntil: 'domcontentloaded' });
  assert.equal(response?.status(), 200, '/: error al cargar la página de referencia');
  const manifestResponse = await page.request.get(`${base}/manifest.json`);
  assert.equal(manifestResponse.status(), 200, '/manifest.json: HTTP inesperado');
  const manifest = await manifestResponse.json();
  assert.ok(Array.isArray(manifest.icons) && manifest.icons.length >= 2, '/manifest.json: faltan iconos PWA');
  for (const purpose of ['any', 'maskable']) {
    const icon = manifest.icons.find(x => String(x.purpose || 'any').split(/\s+/).includes(purpose));
    assert.ok(icon, `/manifest.json: falta icono ${purpose}`);
    const url = new URL(icon.src, base);
    assert.equal(url.origin, new URL(base).origin, `/manifest.json: icono ${purpose} fuera del origen`);
    const iconResponse = await page.request.get(url.href);
    assert.equal(iconResponse.status(), 200, `${url.pathname}: icono ${purpose} inaccesible`);
    for (const size of [48, 96, 192]) {
      const result = await page.evaluate(async ({ src, size }) => {
        const image = new Image();
        image.src = src;
        await image.decode();
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const context = canvas.getContext('2d');
        context.drawImage(image, 0, 0, size, size);
        const pixels = context.getImageData(0, 0, size, size).data;
        let visible = 0;
        for (let i = 3; i < pixels.length; i += 4) if (pixels[i] > 16) visible++;
        return { naturalWidth: image.naturalWidth, naturalHeight: image.naturalHeight, visible, total: size * size };
      }, { src: url.href, size });
      assert.equal(result.naturalWidth, 512, `${url.pathname}: ancho natural ${result.naturalWidth}, esperado 512`);
      assert.equal(result.naturalHeight, 512, `${url.pathname}: alto natural ${result.naturalHeight}, esperado 512`);
      assert.ok(result.visible > result.total * 0.05, `${url.pathname}: icono ${purpose} a ${size}px prácticamente invisible (${result.visible}/${result.total})`);
    }
  }
} finally {
  await browser.close();
}
console.log('PASS manifest PWA icon render');