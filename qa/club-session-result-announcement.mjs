import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
const page = await context.newPage();

try {
  await page.goto(`${origin}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'load' });
  await page.fill('#club-title', 'Libro para accesibilidad');
  await page.locator('[data-club-session-form] button[type=submit]').click();
  const state = await page.evaluate(() => {
    const result = document.querySelector('[data-club-session-output]');
    const status = document.querySelector('[data-club-session-status]');
    const heading = result.querySelector('h2');
    return {
      visible: !result.hidden,
      heading: heading?.textContent || '',
      live: result.getAttribute('aria-live'),
      role: result.getAttribute('role'),
      focusInside: result.contains(document.activeElement),
      status: status?.textContent || ''
    };
  });
  assert.equal(state.visible, true);
  assert.match(state.heading, /Libro para accesibilidad/);
  const announced = state.live === 'polite' || state.live === 'assertive' || state.role === 'status' || state.focusInside || /Libro para accesibilidad|sesión generada|resultado disponible|consulta la sesión/i.test(state.status);
  assert.ok(announced, 'El estado genérico no identifica ni localiza la nueva sesión para tecnología asistiva');
} finally {
  await browser.close();
}
console.log('club-session-result-announcement: OK');