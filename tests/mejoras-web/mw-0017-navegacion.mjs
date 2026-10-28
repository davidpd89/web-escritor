import assert from 'node:assert/strict';
import { chromium } from 'playwright';

assert.ok(process.env.SITE_ORIGIN, 'SITE_ORIGIN es obligatorio');
const url = new URL('/', process.env.SITE_ORIGIN).href;
const siteOrigin = new URL(url).origin;
const browser = await chromium.launch({ headless: true });

try {
  for (const mode of ['no-preference', 'reduce']) {
    const context = await browser.newContext({
      reducedMotion: mode,
      serviceWorkers: 'block'
    });

    try {
      await context.route('**/*', (route) => {
        const requestOrigin = new URL(route.request().url()).origin;
        return requestOrigin === siteOrigin ? route.continue() : route.abort();
      });

      await context.addInitScript(() => {
        try { sessionStorage.setItem('dp-intro-seen', '1'); } catch {}
      });

      const page = await context.newPage();
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      await page.waitForFunction(() => document.documentElement.dataset.homeEditorialV3 === 'true');

      // Cada escenario empieza con el desplazamiento reiniciado explícitamente.
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      await page.evaluate(() => {
        const maximum = document.documentElement.scrollHeight - innerHeight;
        window.scrollTo({ top: Math.min(2200, maximum), behavior: 'instant' });
      });

      await page.waitForFunction(() => window.scrollY > 720 && document.querySelector('.back-to-top.is-visible'));

      await page.evaluate(() => {
        window.__mw0017ScrollCalls = [];
        window.__mw0017Analytics = 0;
        const originalScrollTo = window.scrollTo.bind(window);
        window.scrollTo = (...args) => {
          window.__mw0017ScrollCalls.push(args);
          return originalScrollTo(...args);
        };
        document.addEventListener('dp:analytics', (event) => {
          if (event.detail?.event === 'home_back_to_top') window.__mw0017Analytics++;
        });
      });

      const button = page.locator('button.back-to-top');
      await button.focus();
      await page.keyboard.press('Enter');

      const result = await page.evaluate(() => {
        const main = document.getElementById('contenido');
        const outline = getComputedStyle(main);
        return {
          focused: document.activeElement === main,
          calls: window.__mw0017ScrollCalls,
          analytics: window.__mw0017Analytics,
          outlineWidth: parseFloat(outline.outlineWidth)
        };
      });

      assert.equal(result.focused, true, `Foco incorrecto con ${mode}`);
      assert.equal(result.analytics, 1, `Analítica incorrecta con ${mode}`);

      const call = result.calls.find((args) => args[0] && args[0].top === 0);
      assert.ok(call, `Falta scrollTo({ top: 0 }) con ${mode}`);
      assert.equal(call[0].behavior, mode === 'reduce' ? 'auto' : 'smooth');
      assert.ok(result.outlineWidth <= 2, 'El foco ha generado un contorno excesivo en main');

      await page.waitForFunction(() => window.scrollY <= 5, { timeout: 10000 });
      await page.keyboard.press('Tab');

      const continued = await page.evaluate(() => {
        const main = document.getElementById('contenido');
        const active = document.activeElement;
        return active !== main && main.contains(active) &&
          active.matches('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])');
      });

      assert.equal(continued, true, `Tab no continúa dentro de main con ${mode}`);
      console.log(`PASS MW-0017 navegación: ${mode}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
