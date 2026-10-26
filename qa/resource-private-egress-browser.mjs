import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const route = '/recursos/ficha-historia-objeto-heredado/';
const secret = 'FAMILIA_PRIVADA_QA_472891';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const requests = [];
  page.on('request', request => requests.push({ url: request.url(), body: request.postData() || '' }));
  await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
  await page.locator('[data-record-status]').waitFor();
  requests.length = 0;

  await page.locator('[data-object-field="title"]').fill(secret);
  await page.locator('[data-object-field="marks"]').fill(`Referencia privada: ${secret}`);
  await page.locator('[data-rows="owners"] [data-key="person"]').first().fill(secret);
  await page.locator('[data-open-questions]').fill(`¿Quién conserva ${secret}?`);

  const downloadPromise = page.waitForEvent('download');
  await page.locator('[data-record-export]').click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  const exported = JSON.parse(Buffer.concat(chunks).toString('utf8'));

  assert.equal(exported.object.title, secret, `${route}: la exportación no conserva el título`);
  assert.equal(exported.owners[0].person, secret, `${route}: la exportación no conserva el propietario`);
  const leaked = requests.filter(request => `${request.url} ${request.body}`.includes(secret));
  assert.deepEqual(leaked, [], `${route}: datos familiares presentes en solicitudes: ${JSON.stringify(leaked)}`);
  const external = requests.filter(request => !['blob:', new URL(BASE).origin].some(origin => request.url.startsWith(origin)));
  assert.deepEqual(external, [], `${route}: solicitudes externas durante la exportación: ${JSON.stringify(external)}`);
  console.log('PASS resource private data egress');
} finally {
  await browser.close();
}
