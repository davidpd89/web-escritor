import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
const page = await context.newPage();
const club = '/clubes-de-lectura/samuel-entre-mundos/';
const guide = `${club}guia-imprimible/`;

async function expectPath(path) {
  assert.equal(new URL(page.url()).pathname, path);
  assert.equal(await page.locator('main h1').count(), 1);
}

try {
  await page.goto(`${origin}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'load' });
  await page.locator('.tool-caveat a[href="/clubes-de-lectura/samuel-entre-mundos/"]').click();
  await expectPath(club);
  await page.locator('.tool-hero a[href="/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/"]').click();
  await expectPath(guide);
  await page.locator('.topbar a[href="/clubes-de-lectura/samuel-entre-mundos/"]').click();
  await expectPath(club);
  await page.locator('#ficha a[href="/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/"]').click();
  await expectPath(guide);
  await page.locator('.actions a[href="/libros/samuel-entre-mundos/"]').click();
  await expectPath('/libros/samuel-entre-mundos/');
  await page.goBack();
  await expectPath(guide);
} finally {
  await browser.close();
}
console.log('club-multi-route-journey: OK');