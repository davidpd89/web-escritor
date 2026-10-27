import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const routes = ['/fragmento/', '/cuaderno/', '/editoriales/', '/herramientas/', '/libros/samuel-entre-mundos/'];
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext();
  const snapshots = await Promise.all(Array.from({ length: 3 }, (_, round) => Promise.all(routes.map(async route => {
    const page = await context.newPage();
    try {
      const response = await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
      assert.equal(response?.status(), 200, `${route} ronda ${round}: HTTP ${response?.status()}`);
      const data = await page.evaluate(() => {
        const footer = document.querySelector('footer.site-footer');
        const links = [...(footer?.querySelectorAll('a[href]') || [])];
        return {
          exists: Boolean(footer),
          text: footer?.innerText.trim().length || 0,
          links: links.map(a => ({ href: a.getAttribute('href'), label: a.textContent.trim() || a.getAttribute('aria-label') || '' }))
        };
      });
      assert.ok(data.exists && data.text > 50, `${route}: pie editorial ausente o vacío`);
      for (const href of ['/autor.html', '/prensa.html', '/privacidad.html', '/aviso-legal.html']) {
        assert.ok(data.links.some(a => a.href === href && a.label), `${route}: falta enlace informativo ${href}`);
      }
      return { route, destinations: data.links.filter(a => a.href?.startsWith('/')).map(a => a.href).sort() };
    } finally {
      await page.close();
    }
  }))));
  const familyLinks = new Set(['/cuaderno/feed.xml']);
  const shared = destinations => destinations.filter(href => !familyLinks.has(href));
  const baseline = shared(snapshots[0][0].destinations);
  for (const entry of snapshots.flat()) {
    assert.deepEqual(shared(entry.destinations), baseline, `${entry.route}: destinos compartidos del pie inconsistentes`);
    if (entry.route === '/cuaderno/') {
      assert.ok(entry.destinations.includes('/cuaderno/feed.xml'), `${entry.route}: falta el RSS del Cuaderno`);
    }
  }
  const feed = await context.request.get(BASE + '/cuaderno/feed.xml');
  assert.equal(feed.status(), 200, 'RSS del Cuaderno inaccesible');
  assert.ok((await feed.text()).trim().length > 100, 'RSS del Cuaderno vacío');
  for (const href of ['/autor.html', '/prensa.html', '/privacidad.html', '/aviso-legal.html']) {
    const response = await context.request.get(BASE + href);
    assert.equal(response.status(), 200, `${href}: destino informativo inaccesible`);
    assert.ok((await response.text()).length > 100, `${href}: respuesta vacía`);
  }
} finally {
  await browser.close();
}
console.log('shared-footer-concurrent-parity: OK');