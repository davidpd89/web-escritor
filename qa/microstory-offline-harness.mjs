import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

export async function withPage(check, width = 390, height = 844) {
  const root = process.cwd();
  const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.woff2':'font/woff2','.webp':'image/webp','.avif':'image/avif','.jpg':'image/jpeg','.png':'image/png','.ico':'image/x-icon'};
  const server = createServer((req,res) => {
    try {
      const pathname = decodeURIComponent(new URL(req.url,'http://localhost').pathname);
      let file = path.resolve(root,'.' + pathname);
      if (file !== root && !file.startsWith(root + path.sep)) throw Error('Invalid path');
      if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file,'index.html');
      if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {res.writeHead(404);res.end('Not found');return;}
      res.writeHead(200,{'Content-Type':mime[path.extname(file)] || 'application/octet-stream'});
      res.end(fs.readFileSync(file));
    } catch {res.writeHead(400);res.end('Bad request');}
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  let browser;
  try {
    browser = await chromium.launch({headless:true});
    const context = await browser.newContext({viewport:{width,height},reducedMotion:'reduce',serviceWorkers:'block'});
    await context.route('**/*',route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
    await context.addInitScript(() => {
      try {sessionStorage.setItem('dp-intro-seen','1');localStorage.setItem('nl-popup-ts',String(Date.now()));} catch {}
    });
    const page = await context.newPage();
    page.setDefaultTimeout(5000);
    const errors = [];
    page.on('pageerror',e => errors.push(String(e)));
    const response = await page.goto(origin + '/al-otro-lado/',{waitUntil:'load'});
    assert.equal(response.status(),200);
    assert.equal(await page.locator('main[data-page=microstory]').count(),1);
    await check({page,origin,context});
    assert.deepEqual(errors,[],errors.join('\n'));
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
