import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/herramientas/', '/herramientas/dialogo/', '/herramientas/limpiador-manuscritos/'];
const browser = await chromium.launch();
try {
  for (const route of routes) {
    const page = await browser.newPage();
    try {
      const response = await page.goto(new URL(route, origin).href);
      assert.equal(response.status(), 200, `${route}: HTTP`);
      const links = await page.locator('a[href][target="_blank"]').evaluateAll(nodes => nodes.filter(a => {
        const style = getComputedStyle(a);
        return a.getClientRects().length && style.visibility !== 'hidden' && style.display !== 'none' && !a.closest('[inert]');
      }).map(a => ({
        href: a.href,
        rel: a.rel,
        name: (a.getAttribute('aria-label') || a.getAttribute('aria-labelledby')?.split(/\s+/).map(id => document.getElementById(id)?.textContent || '').join(' ') || a.innerText || a.querySelector('img[alt]')?.getAttribute('alt') || '').trim(),
        external: a.origin !== location.origin
      })));
      for (const link of links.filter(item => item.external)) {
        assert(link.name.length > 0, `${route}: enlace ${link.href} sin nombre accesible`);
        assert(/\b(noopener|noreferrer)\b/i.test(link.rel), `${route}: enlace ${link.href} sin aislamiento de opener`);
      }
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
