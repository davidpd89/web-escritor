import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTES = ['/accesibilidad/', '/herramientas/', '/recomendaciones/', '/mapa-del-sitio/'];
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 700 } });
  await Promise.all(ROUTES.map(async route => {
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'domcontentloaded' });
      assert.equal(response?.status(), 200, `${route}: documento no disponible`);
      const state = await page.evaluate(() => {
        const main = document.querySelector('main');
        const skips = [...document.querySelectorAll('a[href^="#"]')].filter(a => /saltar al contenido/i.test(a.textContent || a.getAttribute('aria-label') || ''));
        const validSkips = skips.filter(a => {
          const id = decodeURIComponent(a.getAttribute('href').slice(1));
          const target = document.getElementById(id);
          return target && (target === main || main?.contains(target));
        });
        const navigation = [...document.querySelectorAll('nav a[href]')].filter(a => {
          const href = a.getAttribute('href');
          return href && !href.startsWith('#') && !href.startsWith('javascript:');
        });
        return { mainLength: main?.textContent?.trim().length || 0, skips: skips.length, validSkips: validSkips.length, navigation: navigation.length };
      });
      assert.ok(state.mainLength > 80, `${route}: contenido principal insuficiente: ${state.mainLength}`);
      assert.ok(state.validSkips > 0, `${route}: ${state.skips} enlaces de salto, ninguno alcanza el contenido principal`);
      assert.ok(state.navigation > 0, `${route}: ninguna navegación HTML disponible sin JavaScript`);
      await page.keyboard.press('Tab');
      const focused = await page.evaluate(() => ({ tag: document.activeElement?.tagName, href: document.activeElement?.getAttribute('href') }));
      assert.equal(focused.tag, 'A', `${route}: primer Tab no enfoca un enlace (${focused.tag})`);
      assert.ok(focused.href?.startsWith('#'), `${route}: primer enlace enfocado no permite saltar al contenido (${focused.href})`);
    } finally {
      await page.close();
    }
  }));
  await context.close();
  console.log('PASS parallel no-JS navigation');
} finally {
  await browser.close();
}