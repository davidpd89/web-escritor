import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

await browserCase(DIRECTORY, async page => {
  const cards = await page.locator('.wt-card').evaluateAll(nodes => nodes.map(node => ({
    name: node.dataset.name,
    text: node.textContent.toLocaleLowerCase('es'),
    stages: node.dataset.stages.split(' '),
    price: node.dataset.price,
    account: node.dataset.account,
    local: node.dataset.local,
    spanish: node.dataset.spanish,
  })));
  assert.equal(cards.length, 8);

  for (const q of ['', 'scrivener', 'epub']) {
    for (const stage of ['', 'escritura', 'maquetacion']) {
      for (const price of ['', 'pago-unico', 'gratis-open-source']) {
        for (let flags = 0; flags < 8; flags++) {
          await page.evaluate(({ q, stage, price, flags }) => {
            document.querySelector('[data-wt-search]').value = q;
            document.querySelector('[data-wt-stage]').value = stage;
            document.querySelector('[data-wt-price]').value = price;
            document.querySelector('[data-wt-no-account]').checked = Boolean(flags & 1);
            document.querySelector('[data-wt-local]').checked = Boolean(flags & 2);
            document.querySelector('[data-wt-spanish]').checked = Boolean(flags & 4);
            document.querySelector('[data-wt-filters]').dispatchEvent(new Event('input', { bubbles: true }));
          }, { q, stage, price, flags });

          const expected = cards.filter(card =>
            (!q || (card.name + ' ' + card.text).toLowerCase().includes(q)) &&
            (!stage || card.stages.includes(stage)) &&
            (!price || card.price === price) &&
            (!(flags & 1) || card.account === '0') &&
            (!(flags & 2) || card.local === '1') &&
            (!(flags & 4) || card.spanish === '1')
          ).map(card => card.name).sort();
          const actual = (await page.locator('.wt-card:visible').evaluateAll(nodes =>
            nodes.map(node => node.dataset.name))).sort();
          const label = JSON.stringify({ q, stage, price, flags });
          assert.deepEqual(actual, expected, label);
          assert.equal((await page.locator('[data-wt-count]').innerText()).trim(),
            `${expected.length} ${expected.length === 1 ? 'herramienta' : 'herramientas'}`, label);
          assert.equal(await page.locator('[data-wt-empty]').isVisible(), expected.length === 0, label);
        }
      }
    }
  }
  console.log('PASS recursos: 216 combinaciones de filtros');
});
