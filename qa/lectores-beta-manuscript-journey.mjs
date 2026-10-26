import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const root = process.cwd();
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.woff2':'font/woff2'};
const server = createServer((req,res) => {
  const pathname = new URL(req.url,'http://127.0.0.1').pathname;
  const rel = decodeURIComponent(pathname).replace(/^\/+/, '');
  const file = path.resolve(root, rel.endsWith('/') || !rel ? `${rel}index.html` : rel);
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {res.writeHead(404).end();return;}
  res.writeHead(200,{'Content-Type':mime[path.extname(file)] || 'application/octet-stream'});
  res.end(fs.readFileSync(file));
});
await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
async function visit(route,options={}) {
  const context = await browser.newContext({serviceWorkers:'block',...options});
  await context.route('**/*', r => new URL(r.request().url()).origin === base ? r.continue() : r.abort());
  const page = await context.newPage();
  await page.goto(base + route, {waitUntil:'load'});
  return {context,page};
}
try {
  // 1. El CTA prepara asunto y destinatario con ratón, Enter y Espacio.
  for (const mode of ['click','Enter','Space']) {
    const {context,page} = await visit('/lectores-beta/enviar-manuscrito/');
    const cta = page.locator('main a[data-email-subject]');
    assert.equal(await cta.count(),1,`${mode}: CTA principal ausente`);
    if (mode === 'click') await cta.click();
    else {await cta.focus();await page.keyboard.press(mode);}
    const revealed = page.locator('main a[data-email-revealed="true"]');
    await revealed.waitFor({state:'attached'});
    const url = new URL(await revealed.getAttribute('href'));
    assert.equal(url.protocol,'mailto:');
    assert.match(url.pathname,/^[^@\s]+@[^@\s]+\.[^@\s]+$/);
    assert.equal(url.searchParams.get('subject'),'Envío de manuscrito para valoración beta');
    assert.equal(await page.locator('main a[data-email-subject]').count(),0);
    await context.close();
  }
  // 2. Imprimir revela el contacto, pero cancelar no lo deja en el DOM.
  {
    const {context,page} = await visit('/lectores-beta/enviar-manuscrito/');
    const cta = 'main a[data-email-subject]';
    await page.evaluate(() => dispatchEvent(new Event('beforeprint')));
    assert.equal(await page.locator(cta).count(),0);
    assert.match(await page.locator('main a[data-email-revealed]').first().getAttribute('href'),/^mailto:.*subject=/);
    await page.evaluate(() => dispatchEvent(new Event('afterprint')));
    assert.equal(await page.locator(cta).count(),1);
    assert.equal(await page.locator('main a[data-email-revealed]').count(),0);
    await context.close();
  }
  // 3. Sin JS, el CTA llega a un contacto alternativo visible.
  {
    const {context,page} = await visit('/lectores-beta/enviar-manuscrito/',{javaScriptEnabled:false});
    await page.locator('main a.primary-action[href="/prensa.html#contacto"]').click();
    await page.waitForURL('**/prensa.html#contacto');
    assert.equal(await page.locator('#contacto').count(),1);
    assert.match(await page.locator('#contacto noscript').innerText(),/Instagram|LinkedIn/);
    for (const name of ['Instagram','LinkedIn'])
      assert.equal(await page.locator(`#contacto a[aria-label="${name}"]`).count(),1);
    await context.close();
  }
  // 4. Los dos recorridos no se confunden: autores -> lectores -> autores.
  {
    const {context,page} = await visit('/lectores-beta/enviar-manuscrito/');
    await page.locator('main a.text-action[href="/lectores-beta/"]').click();
    await page.waitForURL('**/lectores-beta/');
    assert.equal(await page.locator('#lectores-beta-form').count(),1);
    await page.locator('main a[href="/lectores-beta/enviar-manuscrito/"]').click();
    await page.waitForURL('**/lectores-beta/enviar-manuscrito/');
    assert.equal(await page.locator('main #lectores-beta-form').count(),0);
    assert.equal(await page.locator('main a[data-email-subject]').count(),1);
    await context.close();
  }
} finally {await browser.close();await new Promise(resolve => server.close(resolve));}
console.log('PASS beta manuscript: modalities, print, no-JS alternative, roundtrip');
