import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage();
  const response = await page.goto(`${ORIGIN}/`, { waitUntil: 'domcontentloaded' });
  assert.equal(response?.ok(), true, '/: la portada no responde correctamente');
  await page.locator('html[data-home-editorial-v3="true"]').waitFor();

  const links = await page.locator('main a[href]').evaluateAll(nodes => nodes.filter(a => a.getClientRects().length && a.href.startsWith(location.origin + '/') && !a.hasAttribute('download')).map(a => ({ href: a.href, text: a.textContent.trim() })));
  assert.ok(links.length > 0, '/: no se encontraron enlaces internos de la portada generada');

  const destinations = new Map();
  for (const link of links) {
    const url = new URL(link.href);
    const key = url.pathname + url.search;
    if (!destinations.has(key)) destinations.set(key, []);
    destinations.get(key).push({ ...link, fragment: url.hash });
  }

  for (const [path, references] of destinations) {
    const target = await browser.newPage();
    try {
      const result = await target.goto(ORIGIN + path, { waitUntil: 'domcontentloaded' });
      assert.equal(result?.ok(), true, `/: destino ${path} devuelve HTTP ${result?.status()}; enlaces: ${references.map(x => x.text).join(', ')}`);
      for (const ref of references) {
        if (!ref.fragment) continue;
        const fragment = decodeURIComponent(ref.fragment.slice(1));
        const exists = await target.evaluate(value => [...document.querySelectorAll('[id],a[name]')].some(el => el.id === value || el.getAttribute('name') === value), fragment);
        assert.ok(exists, `/: enlace ${ref.text} apunta a ${path}${ref.fragment}, pero el ancla no existe`);
      }
    } finally {
      await target.close();
    }
  }
  console.log(`PASS: ${links.length} enlaces internos y ${destinations.size} destinos de portada`);
} finally {
  await browser.close();
}
