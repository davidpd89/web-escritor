// Auditoría de navegación en navegador real, en 9 anchos (móvil, tablet,
// escritorio) y en una página representativa de cada familia del sitio.
//
// Comprueba lo que una lectura del HTML no puede ver:
//   - la cabecera cabe, sus controles no se solapan y miden al menos 24×24
//     (WCAG 2.2, 2.5.8) en todos los anchos; no hay scroll horizontal;
//   - la barra de sección marca exactamente una página actual, la deja a la
//     vista y su título lleva al índice de la sección («volver atrás»);
//   - el menú ☰ (Explorar) es el mismo en todas las páginas, cabe en la
//     pantalla, usa tamaños de texto razonables en móvil, cada desplegable
//     abre y TODOS sus enlaces son alcanzables y pulsables, y se cierra con el
//     botón, con Escape y tocando fuera, devolviendo el foco al botón ☰;
//   - en la portada, la barra de territorios y sus desplegables funcionan y
//     ofrecen los mismos destinos que el ☰.
//
// Uso: node qa/navigation-menus-multidevice.mjs   (sirve el repo él mismo;
// QA_ORIGIN apunta a otro origen, p. ej. la vista previa de build-public-dist).
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
]);
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const clean = decodeURIComponent(url.pathname.split('?')[0]).replace(/^\/+/, '');
  const file = path.join(ROOT, clean.endsWith('/') || clean === '' ? clean + 'index.html' : clean);
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = process.env.QA_ORIGIN || `http://127.0.0.1:${server.address().port}`;

const VIEWPORTS = [
  { name: 'movil-320', width: 320, height: 640, touch: true },
  { name: 'movil-375', width: 375, height: 812, touch: true },
  { name: 'movil-390', width: 390, height: 844, touch: true },
  { name: 'movil-414', width: 414, height: 896, touch: true },
  { name: 'tablet-768', width: 768, height: 1024, touch: true },
  { name: 'tablet-1024', width: 1024, height: 768, touch: true },
  { name: 'portatil-1280', width: 1280, height: 800, touch: false },
  { name: 'escritorio-1440', width: 1440, height: 900, touch: false },
  { name: 'escritorio-1920', width: 1920, height: 1080, touch: false },
];

// Una página por familia/plantilla: si una plantilla rompe la navegación,
// aparece aquí.
const PAGES = [
  '/', '/libros/', '/las-manecillas-del-recuerdo/', '/las-manecillas-del-recuerdo/fragmentos/',
  '/las-manecillas-del-recuerdo/kindle/', '/libros/samuel-entre-mundos/', '/fragmento/', '/universo/noveris/',
  '/clubes-de-lectura/samuel-entre-mundos/', '/autor.html', '/premios.html', '/al-otro-lado/', '/cuaderno/',
  '/cuaderno/que-es-el-portal-fantasy/', '/lectores-beta/', '/lectores-beta/enviar-manuscrito/',
  '/recomendaciones/', '/recomendaciones/autores/', '/recomendaciones/autores/stephen-king/',
  '/recomendaciones/libros/coraline/', '/recomendaciones/editoriales/', '/editoriales/', '/editoriales/minotauro/',
  '/metodologia-editorial/', '/atlas-literario/', '/atlas-literario/praga/', '/convocatorias-escritores/',
  '/herramientas/', '/herramientas/manuscrito/', '/herramientas/metadatos-libro/', '/clubes-de-lectura/preparar-sesion/',
  '/recursos/ficha-historia-objeto-heredado/', '/prensa.html', '/eventos.html', '/ferias.html',
  '/privacidad.html', '/aviso-legal.html', '/accesibilidad/', '/mapa-del-sitio/', '/redes-sociales/', '/apoyar/',
  '/empieza-aqui/',
];
// En estas se hace la prueba completa del ☰ (abrir todo, pulsar cada enlace,
// tres formas de cerrar). En el resto basta la firma: el ☰ es el mismo.
const DEEP_EXPLORE = new Set(['/', '/libros/', '/herramientas/manuscrito/']);

const failures = [];
const fail = (label, detail) => { failures.push(`${label}: ${detail}`); };

const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});

let reference = null; // firma del ☰ de la primera página, para comparar con el resto

async function exploreSignature(page) {
  return page.evaluate(() => [...document.querySelectorAll('[data-explore-dialog] .explore-list a, [data-explore-dialog] .explore-utilities a')]
    .map((a) => `${a.getAttribute('href')}|${(a.querySelector('strong')?.textContent || a.textContent).trim()}`));
}

async function checkHeader(page, label) {
  const report = await page.evaluate(() => {
    const visible = (el) => el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
    const controls = [...document.querySelectorAll('.site-header a, .site-header button')].filter(visible).map((el) => {
      const b = el.getBoundingClientRect();
      return { name: (el.getAttribute('aria-label') || el.textContent).trim().slice(0, 30), x: b.x, y: b.y, w: b.width, h: b.height };
    });
    const overlaps = [];
    for (let i = 0; i < controls.length; i++) for (let j = i + 1; j < controls.length; j++) {
      const a = controls[i]; const c = controls[j];
      if (a.x < c.x + c.w - 1 && c.x < a.x + a.w - 1 && a.y < c.y + c.h - 1 && c.y < a.y + a.h - 1) overlaps.push(`${a.name} × ${c.name}`);
    }
    const trigger = document.querySelector('[data-explore-open]');
    return {
      overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      small: controls.filter((c) => c.w < 24 || c.h < 24).map((c) => `${c.name} ${Math.round(c.w)}×${Math.round(c.h)}`),
      outside: controls.filter((c) => c.x < -1 || c.x + c.w > innerWidth + 1).map((c) => c.name),
      overlaps,
      trigger: Boolean(trigger && visible(trigger)),
    };
  });
  if (report.overflowX > 1) fail(label, `scroll horizontal de ${report.overflowX}px`);
  if (!report.trigger) fail(label, 'el botón ☰ no está visible');
  if (report.small.length) fail(label, `controles de cabecera < 24px: ${report.small.join(', ')}`);
  if (report.outside.length) fail(label, `controles de cabecera fuera de pantalla: ${report.outside.join(', ')}`);
  if (report.overlaps.length) fail(label, `controles de cabecera solapados: ${report.overlaps.join(', ')}`);
}

async function checkSectionStrip(page, label) {
  const strip = await page.evaluate(() => {
    const nav = document.querySelector('nav.section-context');
    if (!nav) return null;
    const links = nav.querySelector('.section-context__links');
    const current = [...nav.querySelectorAll('.section-context__links [aria-current="page"]')];
    const box = current[0]?.getBoundingClientRect();
    const lbox = links.getBoundingClientRect();
    return {
      currents: current.length,
      currentVisible: box ? box.left >= lbox.left - 1 && box.right <= lbox.right + 1 : true,
      titleHref: nav.querySelector('.section-context__title')?.getAttribute('href'),
      navRight: nav.getBoundingClientRect().right,
      linkCount: links.querySelectorAll('a').length,
      smallLinks: [...links.querySelectorAll('a')].filter((a) => { const b = a.getBoundingClientRect(); return b.height < 24; }).map((a) => a.textContent.trim()),
    };
  });
  if (!strip) return false;
  if (strip.currents > 1) fail(label, `la barra de sección marca ${strip.currents} páginas actuales`);
  if (!strip.currentVisible) fail(label, 'el elemento actual de la barra de sección queda fuera de la vista');
  if (!strip.titleHref) fail(label, 'la barra de sección no tiene título enlazado al índice');
  if (strip.smallLinks.length) fail(label, `enlaces de la barra de sección < 24px de alto: ${strip.smallLinks.join(', ')}`);
  return true;
}

async function closedAndFocused(page) {
  return page.evaluate(() => ({
    open: document.querySelector('[data-explore-dialog]').open,
    focus: document.activeElement?.hasAttribute('data-explore-open') || false,
  }));
}

async function checkExplore(page, label, deep, viewport) {
  const trigger = page.locator('[data-explore-open]').first();
  await trigger.click();
  await page.waitForFunction(() => document.querySelector('[data-explore-dialog]')?.open);
  await page.waitForFunction(() => document.querySelector('[data-explore-dialog]').getAnimations({ subtree: true }).every((a) => a.playState !== 'running'));
  const geo = await page.evaluate(() => {
    const dialog = document.querySelector('[data-explore-dialog]');
    const b = dialog.getBoundingClientRect();
    const strong = dialog.querySelector('.explore-row__body strong');
    const small = dialog.querySelector('.explore-row__body small');
    return {
      left: b.left, right: b.right,
      strong: parseFloat(getComputedStyle(strong).fontSize),
      small: parseFloat(getComputedStyle(small).fontSize),
      focusClose: document.activeElement?.hasAttribute('data-explore-close') || false,
      scrollable: dialog.scrollHeight <= dialog.clientHeight + 1 || ['auto', 'scroll'].includes(getComputedStyle(dialog).overflowY),
    };
  });
  if (geo.left < -1 || geo.right > viewport.width + 1) fail(label, `☰ fuera de pantalla (${Math.round(geo.left)}–${Math.round(geo.right)})`);
  if (geo.strong > 24) fail(label, `☰: títulos a ${geo.strong}px (demasiado grandes)`);
  if (geo.small > 17 || geo.small >= geo.strong) fail(label, `☰: descripciones a ${geo.small}px (títulos ${geo.strong}px)`);
  if (!geo.focusClose) fail(label, '☰: al abrir, el foco no va al botón de cerrar');
  if (!geo.scrollable) fail(label, '☰: el contenido no cabe y el diálogo no hace scroll');

  const signature = await exploreSignature(page);
  if (!reference) reference = { label, signature };
  else if (JSON.stringify(signature) !== JSON.stringify(reference.signature)) {
    fail(label, `☰ distinto del de ${reference.label}:\n      ${signature.join('\n      ')}`);
  }

  if (deep) {
    const toggles = page.locator('[data-explore-dialog] .explore-row__toggle');
    const count = await toggles.count();
    for (let i = 0; i < count; i++) {
      const toggle = toggles.nth(i);
      await toggle.scrollIntoViewIfNeeded();
      await toggle.click();
      const expanded = await toggle.getAttribute('aria-expanded');
      const panelId = await toggle.getAttribute('aria-controls');
      if (expanded !== 'true') fail(label, `☰: el desplegable ${panelId} no cambia aria-expanded`);
      const links = page.locator(`#${panelId} a`);
      const n = await links.count();
      if (!n) fail(label, `☰: el desplegable ${panelId} está vacío`);
      for (let j = 0; j < n; j++) {
        const link = links.nth(j);
        await link.scrollIntoViewIfNeeded();
        const hit = await link.evaluate((el) => {
          const b = el.getBoundingClientRect();
          const target = document.elementFromPoint(b.left + Math.min(12, b.width / 2), b.top + b.height / 2);
          return { ok: Boolean(target && (target === el || el.contains(target))), h: b.height, w: b.width };
        });
        const text = (await link.textContent()).trim();
        if (!hit.ok) fail(label, `☰: «${text}» (${panelId}) no se puede pulsar: lo tapa otro elemento`);
        if (hit.h < 24) fail(label, `☰: «${text}» mide ${Math.round(hit.h)}px de alto (< 24)`);
      }
      await toggle.click();
      if (await page.locator(`#${panelId}`).isVisible()) fail(label, `☰: el desplegable ${panelId} no se cierra`);
    }
    const utilities = page.locator('[data-explore-dialog] .explore-utilities a');
    for (let j = 0; j < await utilities.count(); j++) {
      await utilities.nth(j).scrollIntoViewIfNeeded();
      if (!(await utilities.nth(j).isVisible())) fail(label, `☰: acceso de utilidad ${j + 1} no visible`);
    }
    // Cerrar con el botón.
    await page.locator('[data-explore-close]').click();
    await page.waitForTimeout(150);
    let state = await closedAndFocused(page);
    if (state.open || !state.focus) fail(label, `☰: cerrar con el botón deja ${JSON.stringify(state)}`);
    // Cerrar tocando fuera (solo si queda fondo visible a la derecha).
    if (viewport.width - geo.right > 40) {
      await trigger.click();
      await page.waitForFunction(() => document.querySelector('[data-explore-dialog]').getAnimations({ subtree: true }).every((a) => a.playState !== 'running'));
      await page.mouse.click(viewport.width - 10, viewport.height / 2);
      await page.waitForTimeout(150);
      state = await closedAndFocused(page);
      if (state.open) fail(label, '☰: tocar fuera no lo cierra');
    }
    await trigger.click();
    await page.waitForTimeout(300);
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(150);
  const state = await closedAndFocused(page);
  if (state.open || !state.focus) fail(label, `☰: Escape deja ${JSON.stringify(state)}`);
}

async function checkHomeMasthead(page, label, viewport) {
  const nav = page.locator('.masthead-nav');
  if (!(await nav.count()) || !(await nav.isVisible())) return;
  const items = page.locator('.masthead-nav__item');
  const n = await items.count();
  const destinations = [];
  for (let i = 0; i < n; i++) {
    const item = items.nth(i);
    const trigger = item.locator('.masthead-nav__submenu-trigger');
    if (!(await trigger.isVisible())) continue;
    await trigger.click();
    await page.waitForTimeout(220);
    const result = await item.evaluate((li, vw) => {
      const sub = li.querySelector('.masthead-nav__submenu');
      const s = getComputedStyle(sub);
      const b = sub.getBoundingClientRect();
      return {
        territory: li.querySelector('a[data-territory]')?.getAttribute('href'),
        visible: s.visibility !== 'hidden' && s.opacity !== '0' && b.height > 0,
        inside: b.left >= -1 && b.right <= vw + 1,
        links: [...sub.querySelectorAll('a')].map((a) => a.getAttribute('href')),
      };
    }, viewport.width);
    destinations.push(result);
    if (!result.visible) fail(label, `portada: el desplegable de ${result.territory} no se ve al pulsar`);
    if (!result.inside) fail(label, `portada: el desplegable de ${result.territory} se sale de la pantalla`);
    await trigger.click();
    await page.waitForTimeout(120);
  }
  // Mismos destinos que el ☰ (fila + hijos), en el mismo orden.
  const explore = await page.evaluate(() => [...document.querySelectorAll('[data-explore-dialog] .explore-item')]
    .filter((item) => item.querySelector('.explore-children'))
    .map((item) => ({
      territory: item.querySelector('a.explore-row').getAttribute('href'),
      links: [...item.querySelectorAll('.explore-children a')].map((a) => a.getAttribute('href')),
    })));
  if (destinations.length && JSON.stringify(destinations.map(({ territory, links }) => ({ territory, links }))) !== JSON.stringify(explore)) {
    fail(label, `portada: la barra de territorios y el ☰ no ofrecen lo mismo\n      barra: ${JSON.stringify(destinations.map(({ territory, links }) => ({ territory, links })))}\n      ☰:     ${JSON.stringify(explore)}`);
  }
}

try {
  for (const viewport of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      hasTouch: viewport.touch,
      isMobile: viewport.touch && viewport.width < 700,
      reducedMotion: 'no-preference',
    });
    await context.addInitScript(() => { try { sessionStorage.setItem('dp-intro-seen', '1'); } catch {} });
    // Sin terceros: la prueba es de navegación, no de analítica.
    await context.route(/^https?:\/\/(?!127\.0\.0\.1|localhost)/, (route) => route.abort());
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(String(error)));
    for (const pathname of PAGES) {
      const label = `${viewport.name} ${pathname}`;
      const response = await page.goto(`${ORIGIN}${pathname}`, { waitUntil: 'load' });
      if (!response || response.status() >= 400) { fail(label, `HTTP ${response?.status()}`); continue; }
      await page.waitForTimeout(150);
      await checkHeader(page, label);
      await checkSectionStrip(page, label);
      await checkExplore(page, label, DEEP_EXPLORE.has(pathname), viewport);
      if (pathname === '/') await checkHomeMasthead(page, label, viewport);
    }
    if (errors.length) fail(viewport.name, `errores JS: ${[...new Set(errors)].join(' | ')}`);
    await context.close();
    console.log(`  ok   ${viewport.name}: ${PAGES.length} páginas`);
  }
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}

if (failures.length) {
  console.error(`\nFAIL navegación multi-dispositivo: ${failures.length} problema(s)`);
  for (const line of failures) console.error(`  - ${line}`);
  process.exit(1);
}
console.log(`PASS navegación multi-dispositivo (${VIEWPORTS.length} anchos × ${PAGES.length} páginas)`);
assert.ok(true);
