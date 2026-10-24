import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const sentinel = 'CONSULTA_PRIVADA_QA_837294';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const leaks = [];
  const posts = [];
  page.on('request', request => {
    const url = request.url();
    if (url.includes(sentinel) || (request.postData() || '').includes(sentinel)) leaks.push(url);
    if (url.includes('/api/assistant') && request.method() === 'POST') posts.push(url);
  });
  await page.route('**/*', route => {
    if (new URL(route.request().url()).origin !== origin) return route.abort();
    return route.continue();
  });
  await page.route('**/pagefind/pagefind.js', route => route.abort());
  await page.goto(origin + '/asistente/');
  await page.locator('[data-assistant-query]').fill(sentinel);
  await page.locator('[data-assistant-submit]').click();
  await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
  assert.deepEqual(posts, [], 'El modo local realizó una petición remota');
  assert.deepEqual(leaks, [], 'La consulta se incluyó en una petición de red');
  const answer = page.locator('.assistant-message--assistant').last();
  assert((await answer.innerText()).trim().length > 20);
  const links = await answer.locator('.assistant-message__sources a').evaluateAll(els => els.map(x => x.getAttribute('href')));
  assert(links.length > 0, 'Sin rutas de orientación tras fallar Pagefind');
  assert(links.every(url => url.startsWith('/') && !url.startsWith('//')));
} finally { await browser.close(); }
console.log('assistant-pagefind-outage: OK');
