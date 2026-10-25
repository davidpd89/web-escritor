import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';

const cases = [
  {
    route: '/libros/',
    file: 'libros/index.html',
    title: 'Las manecillas del recuerdo',
    purchaseSelector: '.books-stage-manecillas a[href="https://amzn.to/4zW6Yeu"]',
  },
  {
    route: '/libros/samuel-entre-mundos/',
    file: 'libros/samuel-entre-mundos/index.html',
    title: 'Samuel entre mundos',
    purchaseSelector: '.samuel-actions [data-buy-modal]',
  },
];

const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage();

  for (const entry of cases) {
    const html = fs.readFileSync(path.join(ROOT, entry.file), 'utf8');
    assert.match(html, /class="header-buy"/, `${entry.file}: falta la acción global de compra`);

    await page.goto(`${ORIGIN}${entry.route}`, { waitUntil: 'domcontentloaded' });

    const result = await page.evaluate(() => {
      const header = document.querySelector('.site-header .header-buy');
      const book = document.querySelector('main h1');
      return {
        header: header ? {
          href: header.href,
          text: header.textContent.trim(),
          label: header.getAttribute('aria-label') || '',
        } : null,
        heading: book?.textContent.trim() || '',
      };
    });

    assert.ok(result.header, `${entry.route}: falta Comprar en cabecera`);
    assert.ok(result.header.href, `${entry.route}: Comprar no tiene destino`);
    assert.match(result.header.label, new RegExp(entry.title, 'i'), `${entry.route}: la acción Comprar identifica una obra diferente de la ficha actual`);

    if (entry.title === 'Samuel entre mundos') {
      const purchase = page.locator(entry.purchaseSelector);
      assert.ok(await purchase.count(), 'Samuel: falta la opción de compra específica');
      assert.doesNotMatch(result.header.href, /^https:\/\/amzn\.to\/4zW6Yeu(?:[?#]|$)/, 'Samuel: Comprar conduce a Las manecillas del recuerdo');

      const samuelAmazon = await page.locator('main a[href*="amazon.es/dp/"]').evaluateAll(links => links.map(link => link.href));
      assert.ok(samuelAmazon.some(url => url.includes('B0GB6LGQFH')), 'Samuel: falta el enlace comercial específico');
      assert.ok(samuelAmazon.some(url => url.split('?')[0] === result.header.href.split('?')[0]) || result.header.href.includes('samuel-entre-mundos'), 'Samuel: el destino de Comprar no coincide con las opciones comerciales de la novela');
    }
  }

  console.log('OK: acciones de compra de cabecera coherentes con cada obra');
} finally {
  await browser.close();
}
