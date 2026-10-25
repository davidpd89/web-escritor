import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const ROUTE = '/recursos/ficha-historia-objeto-heredado/';
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});

async function open() {
  const context = await browser.newContext({acceptDownloads:true,locale:'es-ES'});
  const page = await context.newPage();
  const response = await page.goto(`${BASE}${ROUTE}`,{waitUntil:'domcontentloaded'});
  assert.ok(response?.ok(),`${ROUTE}: HTTP ${response?.status()}`);
  await page.locator('[data-rows="owners"] [data-row]').first().waitFor();
  return {context,page};
}

async function exportJson(page) {
  const pending = page.waitForEvent('download');
  await page.locator('[data-record-export]').click();
  const download = await pending;
  const stream = await download.createReadStream();
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

async function importJson(page,data,name='ficha.json') {
  await page.locator('[data-record-import]').setInputFiles({name,mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});
  await assert.doesNotReject(()=>page.locator('[data-record-status]').getByText(/cargado/i).waitFor({timeout:5000}),`${ROUTE}: no se confirma la importación de ${name}`);
}

async function testRepeatedImport() {
  const {context,page} = await open();
  try {
    await page.locator('[data-object-field="title"]').fill('Reloj familiar');
    await page.locator('[data-rows="owners"] [data-key="person"]').first().fill('María');
    await page.locator('[data-rows="evidence"] [data-key="id"]').first().fill('F01');
    const original = await exportJson(page);
    await importJson(page,original);
    const first = await exportJson(page);
    await importJson(page,original);
    const second = await exportJson(page);
    delete first.exported_at;
    delete second.exported_at;
    assert.deepEqual(second,first,`${ROUTE}: importar dos veces duplica o altera el registro`);
    assert.equal(await page.locator('[data-rows="owners"] [data-row]').count(),1,`${ROUTE}: propietarios duplicados`);
    assert.equal(await page.locator('[data-rows="evidence"] [data-row]').count(),1,`${ROUTE}: fuentes duplicadas`);
  } finally {await context.close();}
}

async function testDeletedRows() {
  const {context,page} = await open();
  try {
    await page.locator('[data-rows="photos"] [data-key="filename"]').first().fill('frente.jpg');
    await page.locator('[data-add-row="photos"]').click();
    await page.locator('[data-rows="photos"] [data-key="filename"]').last().fill('reverso.jpg');
    await page.locator('[data-rows="photos"] [data-row]').first().locator('[data-remove]').click();
    const exported = await exportJson(page);
    assert.deepEqual(exported.photos.map(x=>x.filename),['reverso.jpg'],`${ROUTE}: la exportación conserva fotografías eliminadas o pierde las restantes`);
    await importJson(page,exported);
    assert.equal(await page.locator('[data-rows="photos"] [data-row]').count(),1,`${ROUTE}: la importación restaura filas eliminadas`);
    assert.equal(await page.locator('[data-rows="photos"] [data-key="filename"]').inputValue(),'reverso.jpg',`${ROUTE}: fotografía incorrecta después de importar`);
  } finally {await context.close();}
}

async function testReload() {
  const {context,page} = await open();
  try {
    await page.locator('[data-object-field="title"]').fill('Reloj sin guardar');
    await page.locator('[data-open-questions]').fill('¿De quién era?');
    await page.reload({waitUntil:'domcontentloaded'});
    await page.locator('[data-rows="owners"] [data-row]').first().waitFor();
    assert.equal(await page.locator('[data-object-field="title"]').inputValue(),'',`${ROUTE}: la recarga conserva un borrador que se anuncia como temporal`);
    assert.equal(await page.locator('[data-open-questions]').inputValue(),'',`${ROUTE}: preguntas temporales conservadas después de recargar`);
    assert.match(await page.locator('[data-record-status]').innerText(),/descarga|JSON|recargues/i,`${ROUTE}: falta aviso sobre conservación del trabajo`);
  } finally {await context.close();}
}

async function testEmptyQuestions() {
  const {context,page} = await open();
  try {
    await page.locator('[data-open-questions]').fill('  ¿Quién lo compró?  \n\n  ¿Cuándo llegó?  \n   ');
    const exported = await exportJson(page);
    assert.deepEqual(exported.open_questions,['¿Quién lo compró?','¿Cuándo llegó?'],`${ROUTE}: preguntas vacías o espacios adicionales en JSON`);
    await importJson(page,exported);
    assert.equal(await page.locator('[data-open-questions]').inputValue(),'¿Quién lo compró?\n¿Cuándo llegó?',`${ROUTE}: las preguntas no se restauran correctamente`);
  } finally {await context.close();}
}

try {
  await testRepeatedImport();
  await testDeletedRows();
  await testReload();
  await testEmptyQuestions();
  console.log('qa/recursos-stateful-regression-browser: OK');
} finally {await browser.close();}
