import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.FERIAS_BASE_URL || 'http://127.0.0.1:4173';
const ids = ['feria-libro-aranjuez-2026', 'feria-libro-madrid-2026'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const results = new Map();
try {
  for (const route of ['/eventos.html', '/ferias.html']) {
    const page = await browser.newPage();
    try {
      const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
      assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);
      const records = await page.evaluate(ids => ids.map(id => {
        const entry = document.getElementById(id);
        return { id, exists: Boolean(entry), times: entry ? [...entry.querySelectorAll('time[datetime]')].map(t => ({ datetime: t.getAttribute('datetime'), label: t.textContent.trim() })) : [] };
      }), ids);
      results.set(route, records);
    } finally { await page.close(); }
  }
  for (const id of ids) {
    const dates = [];
    for (const route of ['/eventos.html', '/ferias.html']) {
      const record = results.get(route).find(r => r.id === id);
      assert.ok(record.exists, `${route}#${id}: falta el registro documental`);
      const calendarDates = record.times.filter(t => /^\d{4}-\d{2}-\d{2}(?:T|$)/.test(t.datetime));
      assert.ok(calendarDates.length > 0, `${route}#${id}: falta fecha calendario en time[datetime]`);
      for (const time of calendarDates) {
        assert.ok(time.label.length > 0, `${route}#${id}: fecha ${time.datetime} sin texto visible`);
        const iso = time.datetime.slice(0, 10);
        const date = new Date(`${iso}T12:00:00Z`);
        assert.ok(!Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === iso, `${route}#${id}: fecha inválida ${time.datetime}`);
      }
      dates.push(new Set(calendarDates.map(t => t.datetime.slice(0, 10))));
    }
    assert.ok([...dates[0]].some(date => dates[1].has(date)), `${id}: fechas contradictorias entre eventos.html (${[...dates[0]]}) y ferias.html (${[...dates[1]]})`);
  }
} finally { await browser.close(); }
console.log('fairs visible date parity: OK');
