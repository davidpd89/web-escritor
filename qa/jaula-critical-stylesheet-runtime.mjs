import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTE = '/donde-empieza-la-jaula/';
const browser = await chromium.launch({ headless: true });

try {
  for (const width of [360, 390, 768, 1199, 1440]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const failures = [];
    const styles = [];

    page.on('requestfailed', request => {
      if (request.url().startsWith(ORIGIN)) failures.push(`${request.url()}: ${request.failure()?.errorText}`);
    });
    page.on('response', response => {
      const request = response.request();
      if (request.resourceType() === 'stylesheet' && response.url().startsWith(ORIGIN)) {
        styles.push({ url: response.url(), status: response.status() });
      }
    });

    const response = await page.goto(`${ORIGIN}${ROUTE}`, { waitUntil: 'networkidle' });
    assert.equal(response?.status(), 200, `${ROUTE} ${width}px: documento HTTP incorrecto`);
    await page.locator('.excerpt-field p').first().waitFor({ state: 'visible' });

    assert.ok(styles.length > 0, `${ROUTE} ${width}px: ninguna hoja CSS local solicitada`);
    assert.deepEqual(styles.filter(item => item.status < 200 || item.status >= 400), [], `${ROUTE} ${width}px: CSS con respuesta HTTP fallida`);
    assert.deepEqual(failures, [], `${ROUTE} ${width}px: recursos locales fallidos`);

    const geometry = await page.locator('.excerpt-field').evaluate(element => {
      const rect = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return { left: rect.left, right: rect.right, width: rect.width, fontSize: parseFloat(style.fontSize), lineHeight: parseFloat(style.lineHeight), viewport: document.documentElement.clientWidth };
    });

    assert.ok(geometry.width > 0 && geometry.fontSize >= 16 && geometry.lineHeight > geometry.fontSize, `${ROUTE} ${width}px: geometría tipográfica inválida ${JSON.stringify(geometry)}`);
    assert.ok(geometry.left >= -1 && geometry.right <= geometry.viewport + 1, `${ROUTE} ${width}px: capítulo fuera del viewport ${JSON.stringify(geometry)}`);
    await page.close();
  }
} finally {
  await browser.close();
}

console.log('OK: recursos CSS y geometría de lectura de Jaula');