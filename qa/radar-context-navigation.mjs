import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const page = await browser.newPage();
  const response = await page.goto(`${ORIGIN}/convocatorias-escritores/`, {waitUntil:'domcontentloaded'});
  assert.ok(response?.ok(), '/convocatorias-escritores/: HTTP incorrecto');
  const nav = page.locator('nav.section-context');
  assert.equal(await nav.count(), 1, '/convocatorias-escritores/: navegación contextual ausente o duplicada');
  const info = await nav.evaluate(el => ({
    name: el.getAttribute('aria-label') || (document.getElementById(el.getAttribute('aria-labelledby') || '')?.textContent || ''),
    current: [...el.querySelectorAll('a[aria-current="page"]')].map(a => ({href:a.getAttribute('href'), text:a.textContent.trim()}))
  }));
  assert.match(info.name, /herramientas|convocatorias|concursos/i, `/convocatorias-escritores/: landmark contextual identificado incorrectamente: ${info.name}`);
  assert.equal(info.current.length, 1, '/convocatorias-escritores/: debe existir un único enlace contextual actual');
  assert.equal(new URL(info.current[0].href, ORIGIN).pathname, '/convocatorias-escritores/', '/convocatorias-escritores/: aria-current señala otra página');
  assert.ok(info.current[0].text, '/convocatorias-escritores/: enlace actual sin nombre');
} finally { await browser.close(); }