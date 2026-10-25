import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.goto(base + '/recomendaciones/');
  const inspect = async () => page.locator('input[data-facet]').evaluateAll(nodes => nodes.map(el => ({
    value: el.value,
    facet: el.dataset.facet,
    disabled: el.disabled,
    checked: el.checked,
    visible: !!el.getClientRects().length,
    label: el.labels ? [...el.labels].map(x => x.textContent.trim()).join(' ') : ''
  })));
  const initial = await inspect();
  assert(initial.length > 0);
  for (const item of initial.filter(x => x.visible)) {
    assert(item.label.length > 0, `Etiqueta ausente: ${item.facet}/${item.value}`);
    assert(!(item.disabled && item.checked), `Opción imposible marcada: ${item.value}`);
  }
  const disabled = page.locator('input[data-facet]:disabled').first();
  if (await disabled.count()) {
    await disabled.evaluate(el => { el.focus(); });
    await page.keyboard.press('Space');
    assert.equal(await disabled.isChecked(), false);
  }
  const enabled = page.locator('input[data-facet]:not(:disabled)').first();
  assert(await enabled.count());
  await enabled.check({ force: true });
  const after = await inspect();
  assert(after.some(x => x.checked));
  for (const item of after.filter(x => x.visible)) {
    assert(item.label.length > 0, `Etiqueta perdida: ${item.facet}/${item.value}`);
    assert(!(item.disabled && item.checked), `Selección deshabilitada: ${item.value}`);
  }
} finally {
  await browser.close();
}