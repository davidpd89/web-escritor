import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const source = fs.readFileSync('assets/v1-shell.js', 'utf8');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.setContent(`<button data-explore-open aria-expanded="false">Abrir</button><dialog data-explore-dialog><button data-explore-close>Cerrar</button><div class="explore-list"><a href="/obras/">Obras</a></div><div hidden><button id="hidden-control">Oculto</button></div><div inert><button id="inert-control">Inerte</button></div><div aria-hidden="true"><button id="aria-hidden-control">Aria oculto</button></div><button id="last-control">Último</button></dialog>`);
  await page.evaluate(source => { const script = document.createElement('script'); script.textContent = source; document.body.append(script); }, source);
  await page.locator('[data-explore-open]').click();
  const forbidden = new Set(['hidden-control', 'inert-control', 'aria-hidden-control']);
  const visited = new Set();
  for (const direction of ['Tab', 'Shift+Tab']) {
    for (let i = 0; i < 30; i++) {
      await page.keyboard.press(direction);
      const current = await page.evaluate(() => ({ id: document.activeElement?.id || '', inside: document.querySelector('[data-explore-dialog]').contains(document.activeElement) }));
      assert.ok(current.inside, `El foco escapó del diálogo con ${direction}`);
      assert.ok(!forbidden.has(current.id), `Control oculto recibió foco: ${current.id}`);
      visited.add(current.id);
    }
  }
  assert.ok(visited.has('last-control'), 'El último control visible no fue alcanzable');
  console.log('assets-explore-hidden-focus-stress: OK');
} finally {
  await browser.close();
}
