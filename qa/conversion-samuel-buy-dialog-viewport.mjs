import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:8000';
const route = '/libros/samuel-entre-mundos/';

try {
  for (const width of [320, 375, 768, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 800 } });
    const response = await page.goto(new URL(route, origin).href, { waitUntil: 'load' });
    assert.ok(response?.ok(), `${route} @${width}: HTTP ${response?.status()}`);
    const trigger = page.locator('[data-buy-modal]').first();
    await trigger.waitFor({ state: 'visible' });
    await trigger.click();
    await page.waitForFunction(() => [...document.querySelectorAll('dialog,[role="dialog"]')].some(el => {
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && s.visibility === 'visible' && s.display !== 'none';
    }));
    const result = await page.evaluate(() => {
      const dialogs = [...document.querySelectorAll('dialog,[role="dialog"]')];
      const el = dialogs.find(node => { const r = node.getBoundingClientRect(); const s = getComputedStyle(node); return r.width > 0 && r.height > 0 && s.visibility === 'visible' && s.display !== 'none'; });
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      const scrollable = [el, ...el.querySelectorAll('*')].some(node => { const cs = getComputedStyle(node); return node.scrollHeight > node.clientHeight + 2 && /auto|scroll/.test(cs.overflowY); });
      return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, height: r.height, overflowY: s.overflowY, scrollable, text: el.innerText.trim().length };
    });
    assert.ok(result, `${route} @${width}: diálogo no visible`);
    assert.ok(result.left >= -1 && result.right <= width + 1, `${route} @${width}: diálogo recortado horizontalmente ${JSON.stringify(result)}`);
    assert.ok(result.top < 800 && result.bottom > 0, `${route} @${width}: diálogo fuera de pantalla ${JSON.stringify(result)}`);
    assert.ok(result.text > 0, `${route} @${width}: diálogo comercial vacío`);
    assert.ok(result.bottom <= 801 || result.scrollable, `${route} @${width}: contenido comercial fuera de pantalla sin desplazamiento ${JSON.stringify(result)}`);
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('conversion-samuel-buy-dialog-viewport: OK');