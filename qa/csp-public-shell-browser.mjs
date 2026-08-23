// Verifica en un navegador real que el CSP publico inyectado por
// scripts/build-site-shell.py (apply_public_csp) no bloquea nada que la
// propia pagina necesita: GoatCounter, Metricool, el Worker de newsletter,
// los bloques inline (speculationrules, config de GoatCounter) y las
// herramientas de manuscrito con su CSP propio mas estricto.
//
// Nacio de un hallazgo real: una lectura manual de script.js no detecto ni
// el pixel de Metricool ni que gc.zgo.at se carga por protocolo relativo
// (`//gc.zgo.at/...`) -- solo un navegador real, cargando las paginas de
// verdad, lo dejo ver. Por eso este test carga paginas reales en vez de
// solo re-analizar el HTML generado.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'], ['.xml', 'application/xml; charset=utf-8'],
  ['.txt', 'text/plain; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.jpeg', 'image/jpeg'], ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
]);

function resolvePath(pathname) {
  const clean = decodeURIComponent(pathname.split('?')[0]).replace(/^\/+/, '');
  if (!clean) return path.join(ROOT, 'index.html');
  const candidate = pathname.endsWith('/') ? path.join(ROOT, clean, 'index.html') : path.join(ROOT, clean);
  const normalized = path.resolve(candidate);
  return normalized.startsWith(ROOT) ? normalized : null;
}

const page404 = fs.readFileSync(path.join(ROOT, '404.html'));
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const file = resolvePath(url.pathname);
  if (!file || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(page404);
    return;
  }
  const type = MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(fs.readFileSync(file));
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;

// Paginas con CSP publico (index, con speculationrules, con GoatCounter
// inline) + al menos una herramienta de manuscrito con su CSP propio mas
// estricto, para confirmar que este test tambien la deja intacta.
const PAGES = [
  '/', '/autor.html', '/las-manecillas-del-recuerdo/', '/herramientas/',
  '/herramientas/legibilidad/', '/eventos.html', '/ferias.html',
  '/libros/samuel-entre-mundos/', '/premios.html', '/prensa.html',
  '/universo/noveris/', '/cuaderno/', '/recomendaciones/',
  '/mapa-del-sitio/', '/privacidad.html',
];

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  const context = await browser.newContext();
  const page = await context.newPage();
  const violations = [];
  page.on('console', (msg) => {
    const text = msg.text();
    if (/Content Security Policy|Refused to (load|execute|apply)/i.test(text)) {
      violations.push(`${page.url()} :: ${text}`);
    }
  });

  for (const route of PAGES) {
    const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'networkidle' });
    assert(response && response.status() < 400, `${route}: HTTP ${response?.status()}`);
    await page.waitForTimeout(300);
  }

  assert.equal(violations.length, 0, `CSP violations found:\n${violations.join('\n')}`);
  console.log(`csp-public-shell-browser: PASS (${PAGES.length} páginas, 0 violaciones de CSP)`);
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
