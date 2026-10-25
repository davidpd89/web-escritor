import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

export async function withSite(run) {
  const root = path.resolve(process.cwd());
  const mime = {'.html':'text/html', '.css':'text/css', '.js':'text/javascript', '.mjs':'text/javascript', '.json':'application/json', '.svg':'image/svg+xml', '.png':'image/png', '.webp':'image/webp', '.avif':'image/avif', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.woff2':'font/woff2'};
  const server = createServer((req,res) => {
    let target;
    try {
      const pathname = decodeURIComponent(new URL(req.url,'http://localhost').pathname);
      target = path.resolve(root,'.' + pathname);
      if (target !== root && !target.startsWith(root + path.sep)) throw Error('Traversal');
      if (pathname.endsWith('/')) target = path.join(target,'index.html');
      if (!fs.existsSync(target) || !fs.statSync(target).isFile()) throw Error('Missing');
      res.writeHead(200,{'Content-Type':(mime[path.extname(target)] || 'application/octet-stream')});
      res.end(fs.readFileSync(target));
    } catch { res.writeHead(404);res.end(); }
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  let browser;
  const contexts = [];
  try {
    browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
    async function visit(route,opts={}) {
      const context = await browser.newContext({viewport:opts.viewport || {width:390,height:700},reducedMotion:'reduce',serviceWorkers:'block',forcedColors:opts.forcedColors || 'none'});
      contexts.push(context);
      await context.route('**/*',r => new URL(r.request().url()).origin === origin ? r.continue() : r.abort());
      if (!opts.intro) await context.addInitScript(() => sessionStorage.setItem('dp-intro-seen','1'));
      if (opts.initScript) await context.addInitScript(opts.initScript);
      const page = await context.newPage();
      const response = await page.goto(origin + route,{waitUntil:'load',timeout:20000});
      assert.equal(response?.status(),200,`${route}: HTTP ${response?.status()}`);
      return page;
    }
    await run({visit,origin,browser});
  } finally {
    await Promise.all(contexts.map(c=>c.close().catch(()=>{})));
    if (browser) await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
}
