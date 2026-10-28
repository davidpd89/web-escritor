import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:8000';

try {
  for (const width of [320, 375, 768, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const response = await page.goto(origin, { waitUntil: 'load' });
    assert.ok(response?.ok(), `Portada @${width}: HTTP ${response?.status()}`);
    await page.locator('html[data-home-editorial-v3="true"]').waitFor({ state: 'attached' });
    const result = await page.locator('.yale-lead__actions').evaluateAll(groups => groups.map(group => {
      const items = [...group.querySelectorAll('a,button')].filter(el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && s.visibility === 'visible' && s.display !== 'none';
      });
      const collisions = [];
      for (let i = 0; i < items.length; i++) {
        for (let j = i + 1; j < items.length; j++) {
          const a = items[i].getBoundingClientRect();
          const b = items[j].getBoundingClientRect();
          const overlap = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
          if (overlap > 4) collisions.push({ first: items[i].innerText, second: items[j].innerText, overlap });
        }
      }
      return { count: items.length, collisions };
    }));
    assert.ok(result.length > 0, `Portada @${width}: falta yale-lead__actions`);
    assert.ok(result.some(group => group.count > 0), `Portada @${width}: sin acciones visibles`);
    for (const group of result) assert.deepEqual(group.collisions, [], `Portada @${width}: acciones comerciales solapadas`);
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('conversion-home-action-overlap: OK');