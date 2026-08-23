// Verifica en un navegador real que el dialogo Explorar representa
// exactamente los 5 territorios estables (M.1, 2026-08-23), que Obras
// enlaza a /libros/, que Manecillas y Samuel siguen siendo alcanzables, y
// que el comportamiento de teclado/foco/Escape sigue intacto.
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
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });

  const trigger = page.locator('[data-explore-open]');
  await trigger.click();
  await page.waitForTimeout(150);

  const dialog = page.locator('[data-explore-dialog]');
  assert(await dialog.evaluate((el) => el.open), 'Explorar debe abrirse tras el clic');

  // 1) Exactamente 5 territorios, en el orden y con los hrefs correctos.
  const territoryLinks = page.locator('.explore-list > a').locator('nth=0, nth=1, nth=2, nth=3, nth=4');
  const rows = page.locator('.explore-list > a');
  const firstFive = [];
  for (let i = 0; i < 5; i++) {
    const href = await rows.nth(i).getAttribute('href');
    const label = (await rows.nth(i).locator('strong').textContent())?.trim();
    firstFive.push({ href, label });
  }
  assert.deepEqual(
    firstFive.map((r) => r.href),
    ['/libros/', '/autor.html', '/cuaderno/', '/herramientas/', '/prensa.html'],
    `los primeros 5 destinos deben ser los territorios estables en orden, obtenido: ${JSON.stringify(firstFive)}`,
  );
  assert.equal(firstFive[0].label, 'Obras', 'el primer territorio debe etiquetarse "Obras"');

  // 2) Manecillas ya no es un territorio de primer nivel, pero sigue
  //    siendo alcanzable (atajo "Leer un fragmento").
  const allHrefs = await rows.evaluateAll((els) => els.map((el) => el.getAttribute('href')));
  assert(!allHrefs.slice(0, 5).includes('/las-manecillas-del-recuerdo/'), 'Manecillas no debe ser un territorio de primer nivel');
  assert(allHrefs.includes('/las-manecillas-del-recuerdo/fragmentos/'), 'Manecillas debe seguir siendo alcanzable vía el atajo de fragmento');

  // 3) Foco: al abrir, el foco entra en el diálogo.
  const focusedInDialog = await page.evaluate(() => document.activeElement?.closest('[data-explore-dialog]') != null);
  assert(focusedInDialog, 'el foco debe entrar en el diálogo al abrirlo');

  // 4) Escape cierra y devuelve el foco al trigger.
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  assert(!(await dialog.evaluate((el) => el.open)), 'Escape debe cerrar el diálogo');
  const focusReturned = await page.evaluate(() => document.activeElement?.hasAttribute?.('data-explore-open'));
  assert(focusReturned, 'el foco debe volver al trigger tras cerrar con Escape');

  await context.close();
  console.log('explore-territories-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
