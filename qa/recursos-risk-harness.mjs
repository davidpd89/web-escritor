import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

export const BASE = 'http://127.0.0.1:4173';
export const DIRECTORY = '/recursos/herramientas-para-escritores/';
export const OBJECT = '/recursos/ficha-historia-objeto-heredado/';
const ROOT = fileURLToPath(new URL('../', import.meta.url));
let server = null;

async function ensureLocalServer() {
  try {
    const response = await fetch(BASE + '/');
    if (response.ok) return;
  } catch {}
  server = spawn('python3', ['-m', 'http.server', '4173', '--bind', '127.0.0.1'], {
    cwd: ROOT,
    stdio: 'ignore',
  });
  for (let attempt = 0; attempt < 50; attempt++) {
    try {
      if ((await fetch(BASE + '/')).ok) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error('No se pudo iniciar el servidor HTTP local');
}

export async function browserCase(route, callback, options = {}) {
  let browser;
  try {
    await ensureLocalServer();
    browser = await chromium.launch({
      headless: true,
      ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {
        executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH,
      } : {}),
    });
    const context = await browser.newContext({
      locale: 'es-ES',
      acceptDownloads: true,
      javaScriptEnabled: options.javaScriptEnabled ?? true,
      viewport: options.viewport ?? { width: 390, height: 844 },
    });
    await context.route('**/*', route => {
      const url = new URL(route.request().url());
      return url.origin === new URL(BASE).origin ? route.continue() : route.abort();
    });
    const page = await context.newPage();
    const response = await page.goto(BASE + route, { waitUntil: 'load' });
    assert.equal(response?.status(), 200, `HTTP de ${route}`);
    await callback(page);
  } finally {
    if (browser) await browser.close();
    if (server) {
      server.kill();
      server = null;
    }
  }
}

export async function exportedRecord(page) {
  const pending = page.waitForEvent('download');
  await page.locator('[data-record-export]').click();
  const download = await pending;
  return JSON.parse(await readFile(await download.path(), 'utf8'));
}
