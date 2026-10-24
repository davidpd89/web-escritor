import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

const families = [
  ['maquetación', 'maquetacion', 'MAQUETACIÓN', 'maquetación'.normalize('NFD')],
  ['planificación', 'planificacion', 'PLANIFICACIÓN', 'planificación'.normalize('NFD')],
  ['revisión', 'revision', 'REVISIÓN', 'revisión'.normalize('NFD')],
  ['español', 'ESPANOL', 'español', 'español'.normalize('NFD')],
];

await browserCase(DIRECTORY, async page => {
  for (const family of families) {
    const results = [];
    for (const query of family) {
      await page.locator('[data-wt-search]').fill(query);
      results.push((await page.locator('.wt-card:visible').evaluateAll(nodes =>
        nodes.map(node => node.dataset.name))).sort());
    }
    assert.ok(results[0].length > 0, `La fixture debe producir coincidencias: ${family[0]}`);
    for (const result of results.slice(1)) {
      assert.deepEqual(result, results[0], `Deriva lingüística: ${family.join(' / ')}`);
    }
  }
  console.log('PASS recursos: búsquedas lingüísticas equivalentes');
});
