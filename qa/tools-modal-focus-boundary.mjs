import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/herramientas/dialogo/', '/herramientas/repeticiones/', '/herramientas/contador-palabras/'];
const browser = await chromium.launch({ headless: true });
try {
  for (const route of routes) {
    const page = await browser.newPage();
    try {
      const response = await page.goto(new URL(route, origin).href);
      assert.equal(response.status(), 200, `${route}: respuesta HTTP`);
      const trigger = page.locator('[data-explore-open]');
      await trigger.focus();
      await page.keyboard.press('Enter');
      const dialog = page.locator('[data-explore-dialog]');
      await dialog.waitFor({ state: 'visible' });
      assert.equal(await dialog.evaluate(el => el.matches(':modal')), true, `${route}: el menú debe ser modal`);
      for (const key of ['Tab', 'Tab', 'Tab', 'Shift+Tab', 'Shift+Tab']) {
        await page.keyboard.press(key);
        const inside = await dialog.evaluate(el => el.contains(document.activeElement));
        assert(inside, `${route}: ${key} desplaza el foco fuera del diálogo`);
      }
      await page.keyboard.press('Escape');
      await dialog.waitFor({ state: 'hidden' });
      assert.equal(await trigger.evaluate(el => el === document.activeElement), true, `${route}: Escape no restaura el foco`);
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
