import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const questions = [
  '¿Qué es Noveris?', '¿De qué trata Samuel entre mundos?',
  '¿De qué trata Las manecillas del recuerdo?', '¿Qué libros hay?',
  '¿Qué herramientas gratuitas hay?', '¿Dónde mando un manuscrito?',
  '¿Qué concursos para escritores hay?', '¿Cómo contacto con David?'
];
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1024, height: 900 } });
  await page.route('**/*', r => new URL(r.request().url()).origin === O ? r.continue() : r.abort());
  await page.goto(`${O}/asistente/`, { waitUntil: 'load' });
  for (const question of questions) {
    await page.locator('[data-assistant-query]').fill(question);
    await page.locator('[data-assistant-submit]').click();
    await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
  }
  await page.emulateMedia({ media: 'print' });
  const state = await page.locator('.assistant-chat').evaluate(e => {
    const css = getComputedStyle(e);
    return { overflow: css.overflowY, scrollHeight: e.scrollHeight, clientHeight: e.clientHeight };
  });
  assert.ok(!(state.overflow === 'hidden' && state.scrollHeight > state.clientHeight + 2), `print clipping: ${JSON.stringify(state)}`);
  const transcript = await page.locator('[data-assistant-log]').innerText();
  for (const question of questions) assert.ok(transcript.includes(question), `lost printed question: ${question}`);
} finally {
  await browser.close();
}
console.log('PASS assistant print transcript containment');
