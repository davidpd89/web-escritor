import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const url = new URL('/gracias-suscripcion/', base).href;
  const response = await page.goto(url, { waitUntil: 'domcontentloaded' });
  assert.equal(response?.status(), 200, `${url}: la página de confirmación no responde 200`);
  const result = await page.evaluate(() => {
    const errors = [];
    for (const a of document.querySelectorAll('a[href]')) {
      const raw = a.getAttribute('href');
      const resolved = new URL(raw, location.href);
      const rel = new Set(a.rel.toLowerCase().split(/\s+/));
      if (a.target === '_blank' && !rel.has('noopener') && !rel.has('noreferrer')) {
        errors.push(`${raw}: target=_blank sin aislamiento explícito`);
      }
      if (resolved.protocol === 'http:' && resolved.hostname !== 'localhost' && resolved.hostname !== '127.0.0.1') {
        errors.push(`${raw}: enlace HTTP no seguro`);
      }
      if (raw.startsWith('#') && raw.length > 1) {
        const id = decodeURIComponent(raw.slice(1));
        if (!document.getElementById(id) && !document.getElementsByName(id).length) {
          errors.push(`${raw}: ancla inexistente`);
        }
      }
    }
    return errors;
  });
  assert.deepEqual(result, [], `${url}: enlaces inseguros o anclas inexistentes: ${result.join('; ')}`);
} finally {
  await browser.close();
}
