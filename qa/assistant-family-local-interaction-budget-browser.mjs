import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { chromium } from 'playwright';

const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const queries = [
  '¿De qué trata Las manecillas del recuerdo?',
  '¿Qué es Noveris?',
  '¿Qué libros ha publicado David?',
  '¿Qué herramientas gratuitas hay?',
  '¿Dónde puedo enviar mi manuscrito a una editorial?',
  '¿Qué concursos para escritores hay?',
  '¿Cómo puedo contactar con David?',
  '¿Hay eventos o firmas?',
  '¿Qué premios tiene?',
  '¿Qué puedo encontrar en esta web?'
];
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  let posts = 0;
  await page.route('**/*', r => {
    if (r.request().method() === 'POST' && r.request().url().includes('/api/assistant')) posts++;
    return new URL(r.request().url()).origin === O ? r.continue() : r.abort();
  });
  await page.goto(`${O}/asistente/`, { waitUntil: 'load' });
  const timings = [];
  for (const query of queries) {
    const before = await page.locator('.assistant-message--assistant').count();
    await page.locator('[data-assistant-query]').fill(query);
    const start = performance.now();
    await page.locator('[data-assistant-submit]').click();
    await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
    timings.push(performance.now() - start);
    assert.equal(await page.locator('.assistant-message--assistant').count(), before + 1, query);
  }
  assert.equal(posts, 0, 'local questions triggered remote requests');
  const ordered = timings.toSorted((a, b) => a - b);
  const p95 = ordered[Math.ceil(ordered.length * 0.95) - 1];
  assert.ok(p95 < 2500, `local interaction p95 ${p95.toFixed(1)}ms > 2500ms`);
} finally {
  await browser.close();
}
console.log('PASS assistant local interaction budget');
