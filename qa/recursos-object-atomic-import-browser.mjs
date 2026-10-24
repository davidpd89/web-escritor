import assert from 'node:assert/strict';
import { browserCase, OBJECT, exportedRecord } from './recursos-risk-harness.mjs';

const invalid = [
  { schema_version: 1, owners: [null] },
  { schema_version: 1, object: { title: { inesperado: true } } },
  { schema_version: 1, owners: [{ person: 'Ana', source_ids: 'F01' }] },
  { schema_version: 1, evidence: [{ id: ['F01'] }] },
];

await browserCase(OBJECT, async page => {
  await page.locator('[data-object-field="title"]').fill('Reloj original');
  await page.locator('[data-rows="owners"] [data-key="person"]').fill('María');
  const before = await exportedRecord(page);
  const semantic = ({ exported_at, ...rest }) => rest;

  for (let i = 0; i < invalid.length; i++) {
    await page.locator('[data-record-import]').setInputFiles({
      name: `invalid-${i}.json`,
      mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify(invalid[i])),
    });
    await page.waitForTimeout(50);
    const message = await page.locator('[data-record-status]').innerText();
    assert.match(message, /No se pudo abrir/i, `Caso ${i} admitido silenciosamente`);
    const after = await exportedRecord(page);
    assert.deepEqual(semantic(after), semantic(before), `La importación ${i} alteró datos previos`);
  }
  console.log('PASS recursos: importación atómica frente a tipos hostiles');
});
