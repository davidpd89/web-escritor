import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const route of ['/eventos.html', '/ferias.html']) {
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, serviceWorkers: 'allow', reducedMotion: 'reduce' });
      const page = await context.newPage();
      try {
        const initial = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
        assert.ok(initial?.ok(), `${route} ${width}px: carga inicial fallida`);
        const workerResponse = await context.request.get(`${ORIGIN}/service-worker.js`);
        assert.ok(workerResponse.ok(), `${route}: service worker no disponible`);
        await page.evaluate(async () => {
          const registration = await navigator.serviceWorker.register('/service-worker.js');
          await navigator.serviceWorker.ready;
          if (!navigator.serviceWorker.controller) {
            await new Promise((resolve, reject) => {
              const timer = setTimeout(() => reject(new Error('service worker sin control')), 10000);
              navigator.serviceWorker.addEventListener('controllerchange', () => { clearTimeout(timer); resolve(); }, { once: true });
              if (navigator.serviceWorker.controller) { clearTimeout(timer); resolve(); }
            });
          }
          if (!registration.active) throw new Error('service worker no activo');
        });
        await context.setOffline(true);
        const offline = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'domcontentloaded' });
        assert.ok(offline, `${route} ${width}px: navegación offline sin respuesta`);
        const state = await page.evaluate(() => {
          const main = document.querySelector('main') || document.body;
          const style = getComputedStyle(main);
          const rect = main.getBoundingClientRect();
          return { title: document.title, text: main.innerText.trim(), display: style.display, width: rect.width, height: rect.height, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth, contentType: document.contentType };
        });
        assert.equal(state.contentType, 'text/html', `${route} ${width}px: fallback no es HTML (${state.contentType})`);
        assert.ok(state.text.length > 30, `${route} ${width}px: respaldo sin contenido legible`);
        assert.notEqual(state.display, 'none', `${route} ${width}px: contenido offline oculto`);
        assert.ok(state.width > 0 && state.height > 0, `${route} ${width}px: caja offline inválida ${JSON.stringify(state)}`);
        assert.ok(state.overflow <= 1, `${route} ${width}px: overflow offline ${state.overflow}px`);
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
console.log('OK: navegación y presentación offline de Eventos y Ferias');
