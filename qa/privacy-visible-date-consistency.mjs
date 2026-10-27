import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const route = '/privacidad.html';
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage();
  const response = await page.goto(ORIGIN + route, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);

  const dates = await page.evaluate(() => {
    const meta = [...document.querySelectorAll('.legal-meta li')]
      .find(el => /Actualizada/i.test(el.querySelector('strong')?.textContent || ''));
    const updated = document.querySelector('.legal-updated');
    return {
      header: meta?.querySelector('span')?.textContent?.trim() || '',
      history: updated?.textContent?.match(/Última actualización:\s*([^()]+?\d{4})/i)?.[1]?.trim() || ''
    };
  });

  assert.ok(dates.header, `${route}: falta la fecha visible de cabecera`);
  assert.ok(dates.history, `${route}: falta la fecha principal de última actualización`);

  const normalize = value => value.toLocaleLowerCase('es-ES').replace(/\s+/g, ' ').trim();
  assert.equal(normalize(dates.header), normalize(dates.history),
    `${route}: cabecera (${dates.header}) y última actualización (${dates.history}) no coinciden`);

  console.log('PASS: fechas legales visibles coherentes');
} finally {
  await browser.close();
}
