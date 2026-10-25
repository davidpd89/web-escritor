import fs from 'node:fs';
import path from 'node:path';
import { createServer } from 'node:http';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const MIME = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.woff2':'font/woff2','.webp':'image/webp','.avif':'image/avif','.png':'image/png','.jpg':'image/jpeg','.ico':'image/x-icon','.xml':'application/xml'};
export const ROUTES = ['/', '/recomendaciones/', '/recomendaciones/autores/', '/editoriales/', '/editoriales/editorial-espasa/', '/convocatorias-escritores/', '/eventos.html', '/ferias.html', '/premios.html', '/cuaderno/', '/herramientas/', '/mapa-del-sitio/'];

export async function withSite(run) {
  const server = createServer((req,res) => {
    try {
      const pathname = decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
      let file = path.resolve(ROOT,'.' + pathname);
      if (file !== ROOT && !file.startsWith(ROOT + path.sep)) throw Error('Traversal');
      if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file,'index.html');
      if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {res.writeHead(404);res.end('Not found');return;}
      res.writeHead(200,{'Content-Type':MIME[path.extname(file).toLowerCase()] || 'application/octet-stream'});
      res.end(fs.readFileSync(file));
    } catch {res.writeHead(400);res.end('Bad request');}
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
    return await run({browser,origin});
  } finally {
    await browser?.close();
    await new Promise(resolve => server.close(resolve));
  }
}

export async function visit(browser,origin,route,{width=390,height=850,touch=false,js=true,blockShell=false}={}) {
  const context = await browser.newContext({viewport:{width,height},isMobile:touch,hasTouch:touch,javaScriptEnabled:js,reducedMotion:'reduce',serviceWorkers:'block'});
  await context.route('**/*',r => {
    const url = r.request().url();
    if (url.startsWith(origin + '/') && !(blockShell && /\/assets\/v1-shell\.js(?:\?|$)/.test(url))) return r.continue();
    return r.abort();
  });
  if (js) await context.addInitScript(() => {
    try {sessionStorage.setItem('dp-intro-seen','1');localStorage.setItem('nl-popup-ts',String(Date.now()));} catch {}
  });
  const page = await context.newPage();
  page.setDefaultTimeout(5000);
  const response = await page.goto(origin + route,{waitUntil:'domcontentloaded',timeout:20000});
  assert.equal(response?.status(),200,`${route}: document HTTP`);
  const intro = page.locator('[data-intro-enter]');
  if (js && await intro.count() && await intro.isVisible().catch(() => false)) await intro.click();
  return {page,context};
}
