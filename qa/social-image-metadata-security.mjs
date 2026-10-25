import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const cases = [
  {route:'/', expected:/david porto díaz/i},
  {route:'/las-manecillas-del-recuerdo/', expected:/las manecillas del recuerdo/i}
];
const browser = await chromium.launch({headless:true});
try {
  const page = await browser.newPage();
  for (const item of cases) {
    const response = await page.goto(BASE + item.route, {waitUntil:'domcontentloaded'});
    assert.equal(response?.status(), 200, `${item.route}: HTTP ${response?.status()}`);
    const metadata = await page.evaluate(() => ({
      image:document.querySelector('meta[property="og:image"]')?.content || '',
      alt:document.querySelector('meta[property="og:image:alt"]')?.content || ''
    }));
    assert.ok(metadata.image, `${item.route}: falta og:image`);
    const url = new URL(metadata.image);
    assert.equal(url.protocol, 'https:', `${item.route}: og:image insegura: ${metadata.image}`);
    assert.equal(url.hostname, 'davidportodiaz.com', `${item.route}: og:image apunta a dominio inesperado: ${metadata.image}`);
    assert.equal(url.username, '', `${item.route}: og:image contiene credenciales`);
    assert.equal(url.password, '', `${item.route}: og:image contiene contraseña`);
    assert.equal(url.port, '', `${item.route}: og:image contiene puerto inesperado`);
    assert.match(metadata.alt, item.expected, `${item.route}: descripción social incoherente: ${metadata.alt}`);
    assert.doesNotMatch(metadata.alt, /lorem ipsum|placeholder|pendiente|próximamente|texto de prueba/i, `${item.route}: descripción social provisional: ${metadata.alt}`);
  }
} finally {
  await browser.close();
}
console.log('PASS social image metadata security');