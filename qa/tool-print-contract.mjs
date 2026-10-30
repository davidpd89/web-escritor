import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// Contrato de impresión de v1-tools.css: un .tool-panel marcado con
// data-tool-print-panel se imprime (resultado o ficha), sin formulario de
// entrada, estado ni botones. En main el panel entero quedaba en display:none
// y el botón «Imprimir» sacaba una página sin la sesión ni la ficha.
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
const page = await context.newPage();

const visible = selector => page.locator(selector).first().isVisible();
const pdfPages = buffer => (buffer.toString('latin1').match(/\/Type\s*\/Page(?![s\w])/g) || []).length;
const longTokens = 'memoria familiar heredada a lo largo de varias generaciones, Elena Ballesteros-Villanueva de los Ríos, el reloj de bolsillo que nadie se atreve a abrir, silencios';

try {
  await page.goto(`${origin}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'load' });

  // Antes de generar no hay nada que imprimir del panel: ni formulario ni resultado vacío.
  await page.emulateMedia({ media: 'print' });
  assert.equal(await visible('[data-club-session-form]'), false, 'club: el formulario se imprime antes de generar');
  assert.equal(await visible('[data-club-session-output]'), false, 'club: se imprime un resultado vacío');
  const emptyPdf = await page.pdf({ format: 'A4' });
  await page.emulateMedia({ media: 'screen' });

  for (const duration of ['30', '60', '90']) {
    const title = `Libro sintético QA-1000 de ${duration} minutos con un título deliberadamente largo para forzar varias líneas`;
    await page.fill('#club-title', title);
    await page.fill('#club-tokens', longTokens);
    await page.selectOption('#club-duration', duration);
    await page.click('[data-club-session-form] button[type=submit]');
    await page.locator('[data-club-session-output] .club-session-block').first().waitFor();

    await page.emulateMedia({ media: 'print' });
    assert.equal(await visible('[data-club-session-output]'), true, `club ${duration}: la sesión generada no se imprime`);
    const heading = page.locator('[data-club-session-output] h2');
    assert.equal(await heading.isVisible(), true, `club ${duration}: falta el título impreso`);
    assert.match(await heading.innerText(), /QA-1000/, `club ${duration}: el título impreso no es el de la sesión`);
    const questions = page.locator('[data-club-session-output] .club-session-block li');
    assert.ok(await questions.count() >= 3, `club ${duration}: faltan preguntas`);
    assert.equal(await questions.first().isVisible(), true, `club ${duration}: las preguntas no se imprimen`);
    assert.match(await page.locator('[data-club-session-output] .club-session-result-head p').innerText(), new RegExp(`${duration} min`), `club ${duration}: duración impresa incorrecta`);
    for (const selector of ['[data-club-session-form]', '[data-club-session-status]', '[data-club-session-print]', '[data-club-session-copy]', '.tool-actions']) {
      assert.equal(await visible(selector), false, `club ${duration}: ${selector} se imprime`);
    }
    const width = await page.locator('[data-club-session-output]').evaluate(e => e.getBoundingClientRect().width);
    assert.ok(width > 400, `club ${duration}: el resultado se imprime en una columna estrecha (${Math.round(width)} px)`);

    const pdf = await page.pdf({ format: 'A4', printBackground: false });
    assert.ok(pdfPages(pdf) >= 1, `club ${duration}: el PDF no tiene páginas`);
    // Sin librería de PDF en CI: la sesión impresa debe añadir contenido real al PDF vacío.
    assert.ok(pdf.length > emptyPdf.length * 1.2, `club ${duration}: el PDF (${pdf.length} B) apenas difiere del vacío (${emptyPdf.length} B)`);
    console.log(`club ${duration}: PDF ${pdfPages(pdf)} pág., ${pdf.length} B (vacío ${emptyPdf.length} B)`);
    await page.emulateMedia({ media: 'screen' });
  }

  // La ficha del objeto heredado: el formulario ES el documento y se imprime con sus campos.
  await page.goto(`${origin}/recursos/ficha-historia-objeto-heredado/`, { waitUntil: 'load' });
  await page.fill('#object-title', 'Reloj sintético QA-1000');
  await page.emulateMedia({ media: 'print' });
  assert.equal(await visible('[data-object-record] form'), true, 'ficha: el formulario de la ficha no se imprime');
  assert.equal(await visible('#object-title'), true, 'ficha: el campo del objeto no se imprime');
  assert.equal(await page.inputValue('#object-title'), 'Reloj sintético QA-1000');
  for (const selector of ['[data-record-print]', '[data-record-status]', '[data-object-record] .tool-actions']) {
    assert.equal(await visible(selector), false, `ficha: ${selector} se imprime`);
  }
  const pdf = await page.pdf({ format: 'A4' });
  assert.ok(pdfPages(pdf) >= 1, 'ficha: el PDF no tiene páginas');
} finally {
  await browser.close();
}
console.log('PASS tool print contract');
