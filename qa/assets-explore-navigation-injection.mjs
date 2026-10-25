import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const source = fs.readFileSync('assets/v1-shell.js', 'utf8');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.setContent(`<button data-explore-open aria-expanded="false">Explorar</button><dialog data-explore-dialog><button data-explore-close>Cerrar</button><div class="explore-list"><div class="explore-item"><a class="explore-row" href="/obras/"><span class="explore-row__index">1</span><span>Obras</span></a></div><div class="explore-item"><a class="explore-row" href="/autor/"><span class="explore-row__index">2</span><span>Autor</span></a></div></div></dialog>`);
  await page.evaluate(source => { const script = document.createElement('script'); script.textContent = source; document.body.append(script); }, source);
  const result = await page.evaluate(() => {
    const dialog = document.querySelector('[data-explore-dialog]');
    const rows = [...dialog.querySelectorAll('.explore-row')];
    return {
      indices: [...dialog.querySelectorAll('.explore-row__index')].map(el => Number(el.textContent)),
      links: rows.map(el => el.getAttribute('href')),
      assistantCount: dialog.querySelectorAll('[data-assistant-menu-link]').length
    };
  });
  assert.ok(result.indices.length >= 3, 'No se incorporó el acceso dinámico');
  assert.deepEqual(result.indices, Array.from({ length: result.indices.length }, (_, i) => i + 1));
  assert.equal(result.assistantCount, 1);
  assert.equal(result.links.filter(link => link === '/asistente/').length, 1);
  for (const href of result.links) assert.match(href, /^\/(?!\/)[^?#]*\/?$/, `Destino no local: ${href}`);
  console.log('assets-explore-navigation-injection: OK');
} finally {
  await browser.close();
}
