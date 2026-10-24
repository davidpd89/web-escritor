import assert from 'node:assert/strict';
import { browserCase, OBJECT, exportedRecord } from './recursos-risk-harness.mjs';

const fixture = {
  schema_version: 1,
  object: { title: 'Reloj de familia' },
  photos: [{ filename: 'original.jpg', view: 'Frente' }],
  open_questions: ['¿Quién lo fabricó?'],
};

await browserCase(OBJECT, async page => {
  const input = page.locator('[data-record-import]');
  const upload = async () => {
    await input.setInputFiles({ name: 'misma-ficha.json', mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify(fixture)) });
    await page.waitForFunction(() => document.querySelector('[data-object-field="title"]')?.value === 'Reloj de familia');
  };
  await upload();
  assert.equal((await exportedRecord(page)).photos[0].filename, 'original.jpg');

  await page.locator('[data-object-field="title"]').fill('Cambio que debe desaparecer');
  await page.locator('[data-add-row="photos"]').click();
  await page.locator('[data-rows="photos"] [data-row]').last()
    .locator('[data-key="filename"]').fill('intruso.jpg');
  assert.equal((await exportedRecord(page)).photos.length, 2);

  await upload();
  const restored = await exportedRecord(page);
  assert.equal(restored.object.title, 'Reloj de familia');
  assert.deepEqual(restored.photos.map(photo => photo.filename), ['original.jpg']);
  assert.deepEqual(restored.open_questions, ['¿Quién lo fabricó?']);
  assert.equal(await input.inputValue(), '');
  console.log('PASS recursos: reimportación con nombre idéntico');
});
