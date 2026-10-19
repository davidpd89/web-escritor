import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

// Real radar HTML/runtime with one controlled deadline. This remains useful
// after the current contests have expired and covers both Madrid DST changes.
export async function assertRadarLiveClock(browser, origin) {
  const html = await fs.readFile('convocatorias-escritores/index.html', 'utf8');
  for (const [day, instant] of [
    ['2026-10-19', '2026-10-19T21:59:30Z'],
    ['2026-01-15', '2026-01-15T22:59:30Z'],
    ['2026-03-29', '2026-03-29T21:59:30Z'],
    ['2026-10-25', '2026-10-25T22:59:30Z'],
  ]) {
    for (const wake of ['timer', 'visibilitychange', 'pageshow']) {
      const context = await browser.newContext({ timezoneId: 'America/Los_Angeles', reducedMotion: 'reduce' });
      const page = await context.newPage();
      await page.clock.install({ time: new Date(instant) });
      await page.route('**/convocatorias-escritores/', route => route.fulfill({
        contentType: 'text/html; charset=utf-8',
        body: html.replace(/<article\b[^>]*data-radar-item[^>]*>/, tag => tag
          .replace(/data-deadline="[^"]*"/, `data-deadline="${day}"`)
          .replace(/data-verified-at="[^"]*"/, `data-verified-at="${day}"`)),
      }));
      await page.goto(`${origin}/convocatorias-escritores/`);
      const card = page.locator('[data-radar-item]').first();
      assert(await card.isVisible(), `${day}/${wake}: open on deadline day`);
      assert.equal(await card.locator('[data-radar-status]').textContent(), 'Cierra hoy');
      const title = await card.getAttribute('data-title');
      await page.locator('[data-radar-search]').fill(title);
      if (wake === 'timer') await page.clock.runFor(60000);
      else {
        await page.clock.setSystemTime(new Date(Date.parse(instant) + 60000));
        await page.evaluate(event => {
          (event === 'pageshow' ? window : document).dispatchEvent(new Event(event));
        }, wake);
      }
      assert(await card.isHidden(), `${day}/${wake}: closed after Madrid midnight without reloading`);
      assert.equal(await card.locator('[data-radar-status]').textContent(), 'Plazo finalizado');
      assert.equal(await page.locator('[data-radar-search]').inputValue(), title, 'clock refresh must retain filters');
      assert(await page.locator('[data-radar-filter-empty]').isVisible());
      await context.close();
    }
  }
  console.log('radar-live-clock: PASS (12 midnight/suspended-tab cases, CET/CEST and DST boundaries)');
}
