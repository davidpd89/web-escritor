import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

export async function runMobileAudit(check) {
  const root = process.cwd();
  const mime = new Map([['.html','text/html; charset=utf-8'],['.css','text/css; charset=utf-8'],['.js','text/javascript; charset=utf-8'],['.json','application/json; charset=utf-8'],['.svg','image/svg+xml'],['.webp','image/webp'],['.avif','image/avif'],['.woff2','font/woff2']]);
  const server = createServer((req,res) => {
    let pathname;
    try { pathname = decodeURIComponent(new URL(req.url,'http://localhost').pathname); }
    catch { res.writeHead(400); res.end(); return; }
    const relative = pathname.replace(/^\/+/, '');
    const file = path.resolve(root, relative.endsWith('/') || !relative ? path.join(relative,'index.html') : relative);
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200,{'Content-Type':mime.get(path.extname(file)) || 'application/octet-stream'});
    res.end(fs.readFileSync(file));
  });
  let browser;
  try {
    await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
    const origin = process.env.QA_ORIGIN || `http://127.0.0.1:${server.address().port}`;
    browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
    for (const width of [320,360,390]) {
      const context = await browser.newContext({viewport:{width,height:844},hasTouch:true,isMobile:true,reducedMotion:'reduce'});
      try {
        const page = await context.newPage();
        const response = await page.goto(`${origin}/al-otro-lado/`,{waitUntil:'load'});
        assert(response && response.status() === 200,`/al-otro-lado/ ${width}px: HTTP ${response?.status()}`);
        await page.locator('main[data-page="microstory"] .microstory-text p').waitFor({state:'visible'});
        await check(page,width,origin);
      } finally { await context.close(); }
    }
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
