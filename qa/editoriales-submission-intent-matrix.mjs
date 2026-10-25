import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const records = JSON.parse(fs.readFileSync('editoriales/editoriales-data.json', 'utf8')).publishers;
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const errors = [];
try {
  const context = await browser.newContext({viewport:{width:390,height:844}});
  await context.route(/^https?:\/\/(?!127\.0\.0\.1(?::4173)?(?:\/|$)|localhost(?::4173)?(?:\/|$))/, route => route.abort());
  const page = await context.newPage();
  for (const record of records) {
    try {
      const url = `/editoriales/${record.slug}/`;
      const response = await page.goto(BASE + url,{waitUntil:'domcontentloaded'});
      assert.ok(response?.ok(),`${url}: ficha inaccesible`);
      const heading = (await page.locator('main h1').first().innerText()).trim();
      assert.equal(heading,record.name,`${url}: identidad incorrecta`);
      const links = await page.locator('main a[href]').evaluateAll(nodes => nodes.map(a=>({href:a.getAttribute('href')||'',text:(a.innerText||a.getAttribute('aria-label')||'').trim()})));
      assert.ok(links.length>0,`${url}: no hay enlaces utilizables`);
      const direct = record.status === 'open' && record.direct_submission === true;
      if (!direct) {
        const mail = links.filter(a=>a.href.toLowerCase().startsWith('mailto:'));
        assert.deepEqual(mail,[],`${url}: correo de envío ofrecido sin recepción directa confirmada`);
        const misleading = links.filter(a=>/^(enviar|envía|presentar) (mi |tu |un |el )?(manuscrito|original|proyecto)/i.test(a.text));
        assert.deepEqual(misleading,[],`${url}: acción de envío presentada como disponible`);
      } else {
        assert.ok(links.some(a=>/^https:\/\//.test(a.href)||a.href.startsWith('mailto:')),`${url}: falta vía de consulta o contacto`);
      }
      assert.ok(await page.locator('.tool-source-list a[href]').count()>0,`${url}: falta fuente oficial`);
    } catch(e) {errors.push(`${record.slug}: ${e.message}`);}
  }
  await context.close();
} finally {await browser.close();}
assert.deepEqual(errors,[],errors.join('\n'));
console.log(`PASS ${records.length} recorridos de intención editorial`);
