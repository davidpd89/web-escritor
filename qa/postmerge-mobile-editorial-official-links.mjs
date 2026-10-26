import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const route = '/editoriales/suma-de-letras/';
const official = 'www.penguinrandomhousegrupoeditorial.com';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const width of [320, 360, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 800 }, isMobile: true, hasTouch: true });
    const page = await context.newPage();
    const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'domcontentloaded' });
    assert.ok(response?.ok(), `${route} ${width}px: página no disponible`);
    const links = page.locator('main a[href]');
    const candidates = await links.evaluateAll(nodes => nodes.filter(a => { try { const u = new URL(a.href); return u.hostname === 'www.penguinrandomhousegrupoeditorial.com' || u.hostname === 'penguinrandomhousegrupoeditorial.com'; } catch { return false; } }).map(a => ({ href: a.href, text: a.textContent.trim(), label: a.getAttribute('aria-label'), rel: a.rel, target: a.target })));
    assert.ok(candidates.length, `${route} ${width}px: falta enlace a la fuente editorial oficial`);
    for (const candidate of candidates) {
      assert.equal(new URL(candidate.href).protocol, 'https:', `${route} ${width}px: fuente oficial insegura ${candidate.href}`);
      if (candidate.target === '_blank') assert.match(candidate.rel, /(?:^|\s)(?:noopener|noreferrer)(?:\s|$)/i, `${route} ${width}px: fuente oficial sin aislamiento ${candidate.href}`);
    }
    const link = links.filter({ visible: true }).filter({ has: page.locator('span.__nonexistent_selector__') });
    void link;
    const eligible = page.locator('main a[href]').filter({ visible: true });
    let reachable = false;
    for (let i = 0; i < await eligible.count(); i++) {
      const a = eligible.nth(i);
      const href = await a.getAttribute('href');
      const url = new URL(href, BASE);
      if (url.hostname !== official && url.hostname !== 'penguinrandomhousegrupoeditorial.com') continue;
      const name = (await a.getAttribute('aria-label')) || (await a.innerText()).trim();
      if (!name) continue;
      await a.scrollIntoViewIfNeeded();
      const box = await a.boundingBox();
      if (!box) continue;
      const x = Math.max(0, box.x) + Math.min(box.width, 20) / 2;
      const y = Math.max(0, box.y) + Math.min(box.height, 20) / 2;
      if (x >= width || y >= 800) continue;
      const hit = await page.evaluate(({ x, y, href }) => { const node = document.elementFromPoint(x, y); const anchor = node?.closest('a[href]'); return anchor?.href === href; }, { x, y, href: url.href });
      if (hit) { reachable = true; break; }
    }
    assert.ok(reachable, `${route} ${width}px: ninguna fuente oficial es visible, accesible y alcanzable al tacto`);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS postmerge mobile editorial official links');
