import assert from 'node:assert/strict';
import {withPage} from './microstory-offline-harness.mjs';

for (const width of [375,1280]) {
  await withPage(async ({page}) => {
    for (const id of ['texto','evidencia']) {
      const action = page.locator('.v1-masthead__actions a[href="#'+id+'"]');
      assert.equal(await action.count(),1);
      await action.click();
      assert.equal(new URL(page.url()).hash,'#'+id);
      const section = page.locator('#'+id);
      assert.equal(await section.count(),1);
      const heading = section.locator('h2');
      assert.ok((await heading.innerText()).trim().length>5);
      await page.waitForTimeout(180);
      const rect = await section.boundingBox();
      assert.ok(rect && rect.y<900,`${width}: #${id} not brought into view`);
      await page.goBack({waitUntil:'domcontentloaded'}).catch(async () => page.evaluate(() => history.back()));
      await page.waitForFunction(() => location.hash==='');
    }
    assert.ok((await page.locator('.microstory-text p').innerText()).includes('Nos hablamos'));
  },width);
}
console.log('PASS microstory anchor navigation');
