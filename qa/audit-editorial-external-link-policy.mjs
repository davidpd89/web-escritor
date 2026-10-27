import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = [
  '/cuaderno/', '/cuaderno/que-es-el-portal-fantasy/',
  '/cuaderno/temas/', '/universo/noveris/',
  '/ferias.html', '/fragmento/',
  '/las-manecillas-del-recuerdo/', '/las-manecillas-del-recuerdo/fragmentos/'
];
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext();
  await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
  const page = await context.newPage();
  for (const route of routes) {
    await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
    const links = await page.locator('a[href]').evaluateAll(anchors => anchors.map(a => ({
      href: a.href,
      target: a.target,
      rel: a.rel.toLowerCase().split(/\s+/).filter(Boolean),
      label: a.getAttribute('aria-label') || a.textContent.trim(),
      authorFollow: a.classList.contains('amazon-author-follow-link')
    })).filter(a => /^https?:/.test(a.href)));
    assert.ok(links.length >= 1, `${route}: inventario de enlaces sospechosamente vacío`);
    for (const link of links) {
      const url = new URL(link.href);
      if (url.origin === 'https://davidportodiaz.com') continue;
      if (link.target === '_blank') {
        assert.ok(link.rel.includes('noopener'), `${route}: falta noopener en ${link.href}`);
        assert.ok(link.label.length >= 2, `${route}: enlace sin nombre accesible ${link.href}`);
      }
      // Afiliado = evidencia en el propio enlace (amzn.to o parametro tag=).
      // "Seguir al autor" apunta al perfil de autor y no es afiliado.
      const isAmazon = /^(amzn\.to|www\.amazon\.[a-z.]+|amazon\.[a-z.]+)$/.test(url.hostname);
      if (isAmazon && !link.authorFollow && (url.hostname === 'amzn.to' || url.searchParams.has('tag'))) {
        assert.ok(link.rel.includes('sponsored'), `${route}: falta sponsored en ${link.href}`);
        assert.ok(link.rel.includes('nofollow'), `${route}: falta nofollow en ${link.href}`);
      }
    }
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('PASS: política de enlaces externos');
