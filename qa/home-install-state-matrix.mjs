import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { localPage, readyHome } from './home-family-local-fixture.mjs';

const browser = await chromium.launch({ headless: true });

try {
  for (const outcome of ['accepted', 'dismissed']) {
    const { context, page } = await localPage(browser);
    await readyHome(page);

    await page.evaluate(outcome => {
      window.__installCalls = 0;
      const event = new Event('beforeinstallprompt', { cancelable: true });
      event.prompt = () => { window.__installCalls++; };
      event.userChoice = Promise.resolve({ outcome });
      window.dispatchEvent(event);
    }, outcome);

    const button = page.locator('[data-install-web]');
    const status = page.locator('.install-web__status');
    await button.click();
    await page.waitForFunction(() =>
      document.querySelector('.install-web__status')?.textContent.length > 0
    );

    assert.equal(await page.evaluate(() => window.__installCalls), 1);
    assert.match(
      await status.innerText(),
      outcome === 'accepted' ? /iniciada/i : /cancelada/i
    );

    await button.click();
    assert.equal(await page.evaluate(() => window.__installCalls), 1,
      'Una solicitud consumida no puede solicitarse otra vez');
    assert((await status.innerText()).trim().length > 15);

    await page.evaluate(() => window.dispatchEvent(new Event('appinstalled')));
    assert.equal(await button.isDisabled(), true);
    assert.match(await status.innerText(), /completada/i);
    await context.close();
  }

  for (const device of [
    { name: 'ios', ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)' },
    { name: 'android', ua: 'Mozilla/5.0 (Linux; Android 14; Mobile)' },
    { name: 'desktop', ua: 'Mozilla/5.0 (X11; Linux x86_64) Chrome/125.0' }
  ]) {
    const { context, page } = await localPage(browser, { userAgent: device.ua });
    await readyHome(page);
    await page.locator('[data-install-web]').click();
    const message = await page.locator('.install-web__status').innerText();
    assert(message.length > 20, `${device.name}: falta ayuda`);
    assert.equal(await page.locator('[data-install-web]').isDisabled(), false);
    await context.close();
  }

  console.log('PASS home-install-state-matrix');
} finally {
  await browser.close();
}