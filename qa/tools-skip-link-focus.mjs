import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/herramientas/contador-palabras/', '/herramientas/dialogo/', '/herramientas/repeticiones/', '/herramientas/limpiador-manuscritos/'];
const browser = await chromium.launch();
try {
  for (const route of routes) {
    const page = await browser.newPage();
    try {
      const response = await page.goto(new URL(route, origin).href);
      assert.equal(response.status(), 200, `${route}: HTTP`);
      await page.keyboard.press('Tab');
      const first = await page.evaluate(() => ({ tag: document.activeElement.tagName, href: document.activeElement.getAttribute('href'), name: document.activeElement.textContent.trim() }));
      assert.equal(first.tag, 'A', `${route}: el primer elemento no es un enlace`);
      assert(first.href?.startsWith('#'), `${route}: primer enlace sin destino interno`);
      assert(first.name.length > 0, `${route}: enlace de salto sin nombre`);
      await page.keyboard.press('Enter');
      const result = await page.evaluate(() => {
        const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
        const active = document.activeElement;
        const rect = target?.getBoundingClientRect();
        return { exists: !!target, semantic: !!target?.closest('main, [role="main"]') || target?.matches('main, [role="main"]'), focused: !!target && (target === active || target.contains(active)), visible: !!rect && rect.bottom > 0 && rect.top < innerHeight };
      });
      assert(result.exists, `${route}: destino inexistente ${first.href}`);
      assert(result.semantic, `${route}: destino fuera del contenido principal`);
      assert(result.focused, `${route}: el foco no llega al contenido`);
      assert(result.visible, `${route}: destino fuera de la ventana visible`);
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
