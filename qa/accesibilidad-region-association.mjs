import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  const state = await page.evaluate(() => {
    const main = document.querySelector('main[data-family="accesibilidad"]');
    const sections = [...main.querySelectorAll('section.v1-section')];
    const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
    return { mainCount: document.querySelectorAll('main').length, h1Count: main.querySelectorAll('h1').length, uniqueIds: new Set(ids).size === ids.length, sections: sections.map(s => { const id = s.getAttribute('aria-labelledby'); const matches = id ? document.querySelectorAll(`[id="${id}"]`) : []; const heading = matches.length === 1 ? matches[0] : null; return { id, valid: Boolean(heading && s.contains(heading) && heading.matches('h2') && heading.textContent.trim()) }; }) };
  });
  assert.equal(state.mainCount, 1);
  assert.equal(state.h1Count, 1);
  assert.equal(state.uniqueIds, true);
  assert.deepEqual(state.sections.map(s => s.id), ['estandar', 'alcance', 'limitaciones', 'contacto', 'fecha']);
  assert.ok(state.sections.every(s => s.valid));
  for (const label of ['Estándar aplicado', 'Alcance verificado', 'Limitaciones conocidas', 'Contacto', 'Vigencia']) {
    assert.ok((await page.locator('main').innerText()).includes(label), label);
  }
});
console.log('accesibilidad-region-association: PASS');
