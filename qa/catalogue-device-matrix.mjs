import assert from 'node:assert/strict';
import { chromium, devices } from 'playwright';

// Matriz de dispositivos del catálogo /recomendaciones/: móvil estrecho, móviles reales, tabletas
// (vertical y apaisada) y escritorio hasta 1920 px. En cada perfil, la cuadrícula y una ficha
// cargan sin scroll horizontal ni errores de consola, la tarjeta solo enseña etiquetas que
// informan (la edad queda para filtros y ficha) y el layout no salta (CLS) al pintar el mercado.
const origin = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const profiles = [
  ['320 estrecho', { viewport: { width: 320, height: 640 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 }],
  ['iPhone SE', devices['iPhone SE']],
  ['iPhone 13', devices['iPhone 13']],
  ['iPhone 13 apaisado', devices['iPhone 13 landscape']],
  ['Pixel 7', devices['Pixel 7']],
  ['Galaxy S9+', devices['Galaxy S9+']],
  ['iPad Mini', devices['iPad Mini']],
  ['iPad Pro 11 apaisado', devices['iPad Pro 11 landscape']],
  ['Escritorio 1280', { viewport: { width: 1280, height: 800 } }],
  ['Escritorio 1440', { viewport: { width: 1440, height: 900 } }],
  ['Escritorio 1920', { viewport: { width: 1920, height: 1080 } }],
];
const budget = { cls: 0.1, domContentLoadedMs: 4000 };
const browser = await chromium.launch({ headless: true });
const failures = [];
const report = [];

async function open(profile, path) {
  const context = await browser.newContext({ ...profile, reducedMotion: 'reduce' });
  await context.addInitScript(() => {
    try { sessionStorage.setItem('dp-intro-seen', '1'); localStorage.setItem('nl-subscribed', '1'); } catch (e) {}
    window.__cls = 0;
    new PerformanceObserver(list => { for (const e of list.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; }).observe({ type: 'layout-shift', buffered: true });
  });
  await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  const page = await context.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error' && !/net::ERR_FAILED|ERR_BLOCKED/.test(m.text())) errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(origin + path, { waitUntil: 'load', timeout: 30000 });
  await page.waitForTimeout(600);
  return { context, page, errors };
}

const overflow = page => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
const perf = page => page.evaluate(() => { const n = performance.getEntriesByType('navigation')[0]; return { cls: Math.round(window.__cls * 1000) / 1000, dcl: Math.round(n.domContentLoadedEventEnd - n.startTime) }; });

try {
  let fichaPath = '';
  for (const [name, profile] of profiles) {
    const check = (ok, msg) => { if (!ok) failures.push(`${name}: ${msg}`); };
    const { context, page, errors } = await open(profile, '/recomendaciones/');
    const cards = page.locator('.catalogue-card:visible');
    check(await cards.count() >= 6, 'menos de 6 tarjetas visibles');
    check(await overflow(page) <= 0, `scroll horizontal en el catálogo (${await overflow(page)} px)`);
    const state = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('.catalogue-card')];
      const facts = document.querySelector('.catalogue-card .catalogue-byline');
      const first = cards.find(c => c.offsetParent);
      const small = cards.slice(0, 6).flatMap(c => [...c.querySelectorAll('a')].filter(a => a.offsetParent).map(a => a.getBoundingClientRect()).filter(r => r.height < 24 || r.width < 24));
      return {
        ageTags: cards.reduce((n, c) => n + c.querySelectorAll('.catalogue-tags a[href*="#edad="]').length, 0),
        maxTags: Math.max(0, ...cards.map(c => c.querySelectorAll('.catalogue-tags li').length)),
        factsBackground: facts ? getComputedStyle(facts).backgroundColor : '',
        emptyRatings: cards.filter(c => { const b = c.querySelector('[data-rating-book]'); return b && !b.hidden && !b.textContent.trim(); }).length,
        firstTop: first ? Math.round(first.getBoundingClientRect().top + scrollY) : -1,
        smallTargets: small.length,
        bookNodes: [...document.querySelectorAll('script[type="application/ld+json"]')].reduce((n, s) => n + (s.textContent.match(/"@type":\s*"Book"/g) || []).length, 0),
        firstHref: first?.querySelector('h3 a')?.getAttribute('href') || '',
      };
    });
    check(state.ageTags === 0, `${state.ageTags} etiquetas de edad en tarjetas`);
    check(state.maxTags <= 3, `una tarjeta lleva ${state.maxTags} etiquetas`);
    check(['rgba(0, 0, 0, 0)', 'transparent'].includes(state.factsBackground), `la línea editorial conserva fondo ${state.factsBackground}`);
    check(state.emptyRatings === 0, `${state.emptyRatings} cajas de valoración vacías reservan altura`);
    check(state.smallTargets === 0, `${state.smallTargets} enlaces de menos de 24 px en las primeras tarjetas`);
    check(state.bookNodes >= 6, 'el ItemList no publica nodos Book');
    const hub = await perf(page);
    check(hub.cls <= budget.cls, `CLS del catálogo ${hub.cls}`);
    check(hub.dcl <= budget.domContentLoadedMs, `DOMContentLoaded del catálogo ${hub.dcl} ms`);
    check(errors.length === 0, `errores de consola en el catálogo: ${errors.slice(0, 2).join(' | ')}`);
    fichaPath ||= state.firstHref;
    await context.close();

    const ficha = await open(profile, fichaPath);
    check(await ficha.page.locator('h1').isVisible(), 'la ficha no muestra el título');
    check(await overflow(ficha.page) <= 0, `scroll horizontal en la ficha (${await overflow(ficha.page)} px)`);
    const book = await ficha.page.evaluate(() => [...document.querySelectorAll('script[type="application/ld+json"]')].flatMap(s => JSON.parse(s.textContent)['@graph'] || []).find(n => n['@type'] === 'Book') || null);
    check(book && /^97[89]\d{10}$/.test(book.isbn || '') && book.name && book.author?.length, 'la ficha no publica un Book con ISBN, título y autoría');
    const detail = await perf(ficha.page);
    check(detail.cls <= budget.cls, `CLS de la ficha ${detail.cls}`);
    check(ficha.errors.length === 0, `errores de consola en la ficha: ${ficha.errors.slice(0, 2).join(' | ')}`);
    await ficha.context.close();
    report.push(`${name.padEnd(22)} catálogo CLS ${hub.cls} DCL ${hub.dcl} ms · ficha CLS ${detail.cls} DCL ${detail.dcl} ms · 1.ª tarjeta a ${state.firstTop} px`);
  }
} finally {
  await browser.close();
}
console.log(report.join('\n'));
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`PASS catalogue-device-matrix: ${profiles.length} perfiles, catálogo y ficha`);
