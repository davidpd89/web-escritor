import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.QA_BASE_URL || process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
try {
  const context = await browser.newContext({viewport:{width:390,height:844}});
  await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin ? route.continue() : route.abort());
  const page = await context.newPage();
  const transfers = new Map();
  page.on('requestfinished', async request => {
    const url = new URL(request.url());
    if (url.origin !== new URL(base).origin || !/\.(?:css|js|webp|png|jpe?g|woff2)$/.test(url.pathname)) return;
    const response = await request.response();
    if (!response || response.status() !== 200) return;
    const headers = await response.allHeaders();
    const size = Number(headers['content-length'] || 0);
    const entry = transfers.get(url.href) || {count:0,bytes:0};
    entry.count++;
    entry.bytes += size;
    transfers.set(url.href,entry);
  });
  for (const path of ['/recomendaciones/','/recomendaciones/libros/coraline/','/recomendaciones/']) {
    const response = await page.goto(base + path,{waitUntil:'load'});
    assert.equal(response.status(),200,`${path}: HTTP`);
  }
  const repeated = [...transfers].filter(([url,v]) => v.count > 1 && v.bytes > 65536);
  assert.deepEqual(repeated,[],`/recomendaciones/: recursos estáticos repetidos con transferencia significativa: ${JSON.stringify(repeated)}`);
  await context.close();
} finally { await browser.close(); }