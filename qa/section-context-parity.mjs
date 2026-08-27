// Parity guard for the pre-rendered .section-context nav (post-#129 audit).
//
// libros/samuel-entre-mundos/index.html and the two recomendaciones/* pages
// now hand-copy buildContextNav()'s output into static HTML so it paints on
// first frame instead of being inserted by JS after load (the CLS fix).
// That is a second, manually-maintained copy of what the JS would generate --
// exactly the kind of duplication that drifts silently. This test derives
// the JS-generated version fresh (by stripping the pre-rendered <nav> and
// letting v1-editorial-interior-v4.js build it from scratch, same as any
// page without one) and diffs it against the committed markup link-by-link.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const PAGES = [
  'libros/samuel-entre-mundos/index.html',
  'recomendaciones/magia-con-coste/index.html',
  'recomendaciones/portal-fantasy-espanol/index.html',
  'universo/noveris/index.html',
  'clubes-de-lectura/samuel-entre-mundos/index.html',
];

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.jpeg', 'image/jpeg'], ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'],
  ['.ico', 'image/x-icon'],
]);

const NAV_RE = /<nav class="section-context"[\s\S]*?<\/nav>\s*/;

function extractLinks(html) {
  const linksBlockMatch = html.match(/<div class="section-context__links">([\s\S]*?)<\/div>/);
  assert.ok(linksBlockMatch, 'no .section-context__links block found');
  const anchors = [...linksBlockMatch[1].matchAll(/<a href="([^"]+)"(\s+aria-current="page")?>([^<]+)<\/a>/g)];
  assert.ok(anchors.length > 0, 'no <a> links parsed from .section-context__links');
  return anchors.map(m => ({ href: m[1], current: !!m[2], label: m[3] }));
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const clean = decodeURIComponent(url.pathname.split('?')[0]).replace(/^\/+/, '');
  let file = clean === '' ? 'index.html' : clean;
  let full = path.join(ROOT, file);
  if (fs.existsSync(full) && fs.statSync(full).isDirectory()) full = path.join(full, 'index.html');
  if (!fs.existsSync(full) || !fs.statSync(full).isFile()) {
    res.writeHead(404); res.end('not found'); return;
  }
  const type = MIME.get(path.extname(full).toLowerCase()) || 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(fs.readFileSync(full));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

for (const rel of PAGES) {
  const original = fs.readFileSync(path.join(ROOT, rel), 'utf8');
  const committedNavMatch = original.match(NAV_RE);
  assert.ok(committedNavMatch, `${rel}: no pre-rendered <nav class="section-context"> found`);
  const committedLinks = extractLinks(committedNavMatch[0]);

  // Strip the pre-rendered nav so the page looks like one that never had
  // it -- exactly the condition buildContextNav()'s own guard checks for.
  const stripped = original.replace(NAV_RE, '');
  const tmpRel = rel.replace(/index\.html$/, '__parity-check.html');
  const tmpAbs = path.join(ROOT, tmpRel);
  fs.writeFileSync(tmpAbs, stripped, 'utf8');

  try {
    const page = await browser.newPage();
    await page.goto(`${ORIGIN}/${tmpRel}`, { waitUntil: 'networkidle' });
    const generatedOuter = await page.locator('.section-context').first().evaluate(el => el.outerHTML).catch(() => null);
    assert.ok(generatedOuter, `${rel}: v1-editorial-interior-v4.js did not generate a .section-context when none was pre-rendered`);
    const generatedLinks = extractLinks(generatedOuter);

    assert.deepEqual(
      generatedLinks, committedLinks,
      `${rel}: pre-rendered .section-context__links drifted from what buildContextNav() generates.\n` +
      `committed: ${JSON.stringify(committedLinks)}\ngenerated: ${JSON.stringify(generatedLinks)}`
    );
    await page.close();
  } finally {
    fs.unlinkSync(tmpAbs);
  }
}

await browser.close();
server.close();
console.log(`PASS section-context parity (${PAGES.length} pre-rendered pages match buildContextNav() output)`);
