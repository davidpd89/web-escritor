import assert from 'node:assert/strict';
import { browserCase, OBJECT, exportedRecord } from './recursos-risk-harness.mjs';

const cases = [
  ['photos', 'filename'],
  ['owners', 'person'],
  ['evidence', 'id'],
  ['oral_history', 'speaker'],
  ['timeline', 'event'],
];

await browserCase(OBJECT, async page => {
  for (const [kind, field] of cases) {
    for (let i = 1; i < 3; i++) await page.locator(`[data-add-row="${kind}"]`).click();
    const rows = page.locator(`[data-rows="${kind}"] [data-row]`);
    assert.equal(await rows.count(), 3);
    for (let i = 0; i < 3; i++) {
      await rows.nth(i).locator(`[data-key="${field}"]`).fill(`${kind}-QA-${i}`);
    }
  }

  for (const [kind] of cases) {
    await page.locator(`[data-rows="${kind}"] [data-row]`).nth(1).locator('[data-remove]').click();
    assert.equal(await page.locator(`[data-rows="${kind}"] [data-row]`).count(), 2);
  }

  const record = await exportedRecord(page);
  for (const [kind, field] of cases) {
    assert.deepEqual(record[kind].map(row => row[field]),
      [`${kind}-QA-0`, `${kind}-QA-2`], `Pérdida de identidad en ${kind}`);
  }
  console.log('PASS recursos: identidad y orden de filas');
});
