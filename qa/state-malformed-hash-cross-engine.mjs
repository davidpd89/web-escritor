import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';

const O = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const hashes = ['#%E0%A4%A', '#%ZZ', '#%C3%28', '#no-existe-qa'];

for (const [name, launcher] of Object.entries({ chromium, firefox, webkit })) {
  const browser = await launcher.launch({ headless: true });
  try {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    await context.route(/^https?:\/\//, r => r.request().url().startsWith(O) ? r.continue() : r.abort());
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    for (const hash of hashes) {
      const response = await page.goto(`${O}/fragmento/${hash}`, { waitUntil: 'load' });
      if (response !== null) {
      assert.equal(response.status(), 200, `${name}: HTTP con ${hash}`);
    }
    assert.equal(new URL(page.url()).hash, hash, `${name}: fragmento no conservado`);
      await page.waitForTimeout(550);
      assert.ok((await page.locator('main').innerText()).trim().length > 100, `${name}: contenido perdido`);
      assert.deepEqual(errors, [], `${name}: excepción con ${hash}`);
    }
    await page.goto(`${O}/fragmento/#article-title`, { waitUntil: 'load' });
    await page.waitForTimeout(550);
    assert.equal(await page.locator('#article-title').count(), 1);
    const rect = await page.locator('#article-title').boundingBox();
    assert.ok(rect && rect.y >= -150 && rect.y < 844, `${name}: ancla válida fuera de vista`);
    assert.deepEqual(errors, []);
    await context.close();
    console.log(`PASS ${name}: hash boundaries`);
  } finally {
    await browser.close();
  }
}
