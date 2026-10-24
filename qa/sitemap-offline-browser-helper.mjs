import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createServer} from 'node:http';
import {chromium} from 'playwright';

export async function withSitemapBrowser(test) {
  const root = process.cwd();
  const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.woff2':'font/woff2','.ico':'image/x-icon'};
  const server = createServer((req,res) => {
    let pathname;
    try { pathname = decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname); }
    catch { res.writeHead(400); res.end(); return; }
    const rel = pathname.replace(/^\/+/, '');
    const file = path.resolve(root,!rel || rel.endsWith('/') ? path.join(rel,'index.html') : rel);
    if (!file.startsWith(root + path.sep)) { res.writeHead(403); res.end(); return; }
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200,{'Content-Type':mime[path.extname(file).toLowerCase()] || 'application/octet-stream','Cache-Control':'no-store'});
    res.end(fs.readFileSync(file));
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
    async function newPage(options = {}) {
      const context = await browser.newContext(options);
      await context.route('**/*',route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
      const page = await context.newPage();
      const response = await page.goto(`${origin}/mapa-del-sitio/`,{waitUntil:'load'});
      assert.equal(response?.status(),200);
      return {context,page};
    }
    await test({newPage,origin,browser});
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
