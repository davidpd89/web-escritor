import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.EVENTOS_BASE_URL || 'http://127.0.0.1:4173';
const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const page = await browser.newPage();
  try {
    const response = await page.goto(new URL('/eventos.html', BASE).href, { waitUntil: 'load' });
    assert.ok(response?.ok(), `eventos.html: HTTP ${response?.status()}`);
    const state = await page.evaluate(() => ({
      future: [...document.querySelectorAll('#proximos .event-entry')].map(entry => ({ id: entry.id, dates: [...entry.querySelectorAll('time[datetime]')].map(t => t.getAttribute('datetime')) })),
      archive: [...document.querySelectorAll('#pasados .event-entry')].map(entry => ({ id: entry.id, dates: [...entry.querySelectorAll('time[datetime]')].map(t => t.getAttribute('datetime')) })),
      empty: document.querySelector('#proximos .event-empty')?.textContent.trim() || ''
    }));
    assert.ok(state.archive.length > 0, 'eventos.html: no se encontraron entradas históricas para comprobar');
    for (const entry of state.future) {
      assert.ok(entry.dates.length > 0, `eventos.html#${entry.id}: convocatoria futura sin fecha verificable`);
      assert.ok(entry.dates.some(d => d.slice(0, 10) >= today), `eventos.html#${entry.id}: evento pasado presentado como futuro (${entry.dates.join(', ')}, hoy ${today})`);
    }
    for (const entry of state.archive) {
      if (!entry.dates.length) continue;
      assert.ok(entry.dates.some(d => d.slice(0, 10) <= today), `eventos.html#${entry.id}: entrada histórica fechada íntegramente en el futuro (${entry.dates.join(', ')})`);
    }
    if (state.future.length === 0) assert.ok(state.empty.length > 0, 'eventos.html#proximos: agenda sin eventos y sin explicación visible');
  } finally { await page.close(); }
} finally { await browser.close(); }
console.log('event historical future classification: OK');
