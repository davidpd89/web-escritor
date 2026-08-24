// Browser contract for the five stable Explorar territories and effective
// findability of both published works. Books are children of Obras, not
// top-level territories, but remain direct static links in the global footer
// and in /libros/ so JS is not required to discover or navigate to them.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
]);
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const clean = decodeURIComponent(url.pathname.split('?')[0]).replace(/^\/+/, '');
  const file = path.join(ROOT, clean.endsWith('/') || clean === '' ? clean + 'index.html' : clean);
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});

const TOP_LEVEL = [
  ['/libros/', 'Obras'],
  ['/autor.html', 'Autor'],
  ['/cuaderno/', 'Cuaderno'],
  ['/herramientas/', 'Herramientas'],
  ['/prensa.html', 'Prensa'],
];
const WORKS = [
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
];

async function assertVisibleDirectWorkLinks(page, scope) {
  for (const href of WORKS) {
    const link = page.locator(`${scope} a[href="${href}"]`).first();
    assert(await link.count() > 0, `${scope}: falta enlace directo ${href}`);
    assert(await link.isVisible(), `${scope}: el enlace ${href} no es visible`);
  }
}

try {
  // Mobile + keyboard contract.
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, hasTouch: true });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });

    // Direct one-click fallback is static and visible even outside Explorar.
    await assertVisibleDirectWorkLinks(page, 'footer.site-footer nav[aria-label="Obra"]');

    const trigger = page.locator('[data-explore-open]');
    await trigger.focus();
    await trigger.click();
    await page.waitForTimeout(80);

    const dialog = page.locator('[data-explore-dialog]');
    assert(await dialog.evaluate((el) => el.open), 'Explorar debe abrirse tras el clic');
    assert.equal(await page.locator('.explore-list').getAttribute('aria-label'), 'Destinos de la web', 'Explorar debe conservar nombre accesible');

    const rows = page.locator('.explore-list > a');
    // Fila 0: el menú lateral sustituyó al enlace de marca en la cabecera
    // (ya no hay logo/nombre clicable fuera del menú), así que "Inicio" es
    // ahora la primera fila, antes de los territorios estables.
    const first = {
      href: await rows.nth(0).getAttribute('href'),
      label: (await rows.nth(0).locator('strong').textContent())?.trim(),
    };
    assert.deepEqual(first, { href: '/', label: 'Inicio' }, `la primera fila debe ser Inicio: ${JSON.stringify(first)}`);
    const firstFive = [];
    for (let i = 0; i < TOP_LEVEL.length; i++) {
      firstFive.push({
        href: await rows.nth(i + 1).getAttribute('href'),
        label: (await rows.nth(i + 1).locator('strong').textContent())?.trim(),
      });
    }
    assert.deepEqual(
      firstFive,
      TOP_LEVEL.map(([href, label]) => ({ href, label })),
      `los territorios estables deben seguir a Inicio: ${JSON.stringify(firstFive)}`,
    );
    assert(!firstFive.some(({ href }) => WORKS.includes(href)), 'ningún libro individual puede ser territorio top-level');

    // Focus remains trapped in the modal; Escape closes and restores opener.
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press('Tab');
      const inside = await page.evaluate(() => {
        const dialogNode = document.querySelector('[data-explore-dialog]');
        return Boolean(dialogNode && (dialogNode === document.activeElement || dialogNode.contains(document.activeElement)));
      });
      assert(inside, `el foco salió de Explorar en Tab ${i + 1}`);
    }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(60);
    assert(!(await dialog.evaluate((el) => el.open)), 'Escape debe cerrar el diálogo');
    assert.equal(
      await page.evaluate(() => document.activeElement?.hasAttribute?.('data-explore-open')),
      true,
      'el foco debe volver al trigger tras Escape',
    );

    // Obras is the stable territory entry; one tap reaches its hub.
    await trigger.click();
    await page.locator('.explore-list > a[href="/libros/"]').click();
    await page.waitForLoadState('load');
    assert.equal(new URL(page.url()).pathname, '/libros/', 'Obras debe navegar a /libros/ con un toque');
    await assertVisibleDirectWorkLinks(page, 'main');

    // Each canonical work is navigable from the Obras hub with a real anchor.
    for (const href of WORKS) {
      await page.goto(`${ORIGIN}/libros/`, { waitUntil: 'load' });
      const link = page.locator(`main a[href="${href}"]`).first();
      await link.click();
      await page.waitForLoadState('load');
      assert.equal(new URL(page.url()).pathname, href, `Obras no navegó correctamente a ${href}`);
    }
    await context.close();
  }

  // No-JS: Explorar itself is progressive enhancement, but both works must
  // still have visible one-click navigation and the Obras hub must expose them.
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
    await assertVisibleDirectWorkLinks(page, 'footer.site-footer nav[aria-label="Obra"]');
    await page.goto(`${ORIGIN}/libros/`, { waitUntil: 'load' });
    await assertVisibleDirectWorkLinks(page, 'main');
    await context.close();
  }

  // 320px + 200% text zoom: opening Explorar must not create horizontal
  // overflow and its top-level Obras destination remains reachable.
  {
    const context = await browser.newContext({ viewport: { width: 320, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
    await page.locator('[data-explore-open]').click();
    await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
    await page.waitForTimeout(80);
    const dimensions = await page.evaluate(() => ({
      documentScroll: document.documentElement.scrollWidth,
      documentClient: document.documentElement.clientWidth,
      dialogScroll: document.querySelector('[data-explore-dialog]')?.scrollWidth ?? 0,
      dialogClient: document.querySelector('[data-explore-dialog]')?.clientWidth ?? 0,
    }));
    assert(dimensions.documentScroll <= dimensions.documentClient + 1, `320px/200%: overflow documento ${JSON.stringify(dimensions)}`);
    assert(dimensions.dialogScroll <= dimensions.dialogClient + 1, `320px/200%: overflow diálogo ${JSON.stringify(dimensions)}`);
    assert(await page.locator('.explore-list > a[href="/libros/"]').isVisible(), '320px/200%: Obras debe seguir visible en Explorar');
    await page.keyboard.press('Escape');
    await context.close();
  }

  console.log('explore-territories-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
