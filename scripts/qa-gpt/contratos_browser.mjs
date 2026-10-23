// Via A (navegador): contratos de UX/diseno sobre una lista de URLs reales. Uso: node contratos_browser.mjs <base> <lista.json> <salida.json>
import fs from 'node:fs';
import { createRequire } from 'node:module';
const { chromium } = createRequire((process.env.QA_NODE_MODULES || 'node_modules') + '/_.js')('playwright');
const [base, listaF, salida] = process.argv.slice(2);
const urls = JSON.parse(fs.readFileSync(listaF, 'utf8'));
const VIEWS = [['movil', 375, 720], ['tablet', 820, 1100], ['escritorio', 1366, 800]];
const hallazgos = [];   // {url, vista, contrato, causa, detalle}
const add = (url, vista, contrato, causa, detalle = '') => hallazgos.push({ url, vista, contrato, causa, detalle: String(detalle).slice(0, 140) });
const t0 = Date.now(); let aserciones = 0, cargas = 0;
const browser = await chromium.launch();
for (const [vista, w, h] of VIEWS) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, hasTouch: vista !== 'escritorio' });
  for (const u of urls) {
    const page = await ctx.newPage(); const consola = [], fallos = [];
    page.on('console', m => { if (m.type() === 'error') consola.push(m.text()); });
    page.on('pageerror', e => consola.push('pageerror: ' + e.message));
    page.on('requestfailed', r => fallos.push(r.url()));
    page.on('response', r => { if (r.status() >= 400) fallos.push(r.status() + ' ' + r.url()); });
    try {
      const resp = await page.goto(base + u, { waitUntil: 'load', timeout: 20000 }); cargas++;
      await page.evaluate(() => document.fonts && document.fonts.ready);
      aserciones++; if (!resp || resp.status() >= 400) add(u, vista, 'smoke-carga', 'la pagina no responde 2xx', resp && resp.status());
      const r = await page.evaluate(() => {
        const de = document.documentElement, ancho = de.clientWidth;
        const desbordan = [...document.querySelectorAll('body *')].filter(e => { const b = e.getBoundingClientRect(); return b.width > 0 && b.right > ancho + 1 && getComputedStyle(e).position !== 'fixed' && !e.closest('[style*="overflow"]'); }).slice(0, 3).map(e => e.tagName + '.' + (e.className || '').toString().slice(0, 30));
        const peq = [...document.querySelectorAll('a[href],button,input,select,textarea,summary')].filter(e => { const b = e.getBoundingClientRect(); const cs = getComputedStyle(e); return b.width > 0 && b.height > 0 && cs.visibility !== 'hidden' && (b.width < 24 || b.height < 24) && !(e.tagName === 'A' && e.closest('p,li,span,td') && cs.display === 'inline'); }).length;
        const rotas = [...document.images].filter(i => i.complete && i.naturalWidth === 0 && i.currentSrc).map(i => i.currentSrc.slice(-60));
        const sinNombre = [...document.querySelectorAll('a[href],button')].filter(e => !(e.textContent.trim() || e.getAttribute('aria-label') || e.getAttribute('title') || e.querySelector('img[alt]:not([alt=""])'))).length;
        const body = getComputedStyle(document.body); const h1 = document.querySelector('h1');
        return { desborda: de.scrollWidth > ancho + 1, desbordan, peq, rotas, sinNombre, fuente: body.fontFamily.split(',')[0].replace(/["']/g, ''), tam: parseFloat(body.fontSize), h1fuente: h1 ? getComputedStyle(h1).fontFamily.split(',')[0].replace(/["']/g, '') : null, h1vis: h1 ? h1.getBoundingClientRect().height > 0 : false, focoVisible: null };
      });
      aserciones += 6;
      if (r.desborda) add(u, vista, 'responsive-overflow', 'desborde horizontal de la pagina', r.desbordan.join(' '));
      if (vista !== 'escritorio' && r.peq > 0) add(u, vista, 'ux-objetivos-tactiles', 'objetivos tactiles < 24px', r.peq + ' elementos');
      if (r.rotas.length) add(u, vista, 'smoke-imagenes', 'imagen rota', r.rotas[0]);
      if (r.sinNombre) add(u, vista, 'a11y-nombre-accesible', 'enlace/boton sin nombre accesible', r.sinNombre + ' elementos');
      if (r.tam < 15) add(u, vista, 'tipografia-tamano', 'cuerpo de texto menor de 15px', r.tam);
      if (!r.h1vis) add(u, vista, 'estructura-h1-visible', 'h1 ausente u oculto');
      aserciones++; if (consola.length) add(u, vista, 'smoke-consola', 'errores de consola/JS', consola[0]);
      aserciones++; if (fallos.length) add(u, vista, 'smoke-red', 'peticiones fallidas o 4xx/5xx', fallos[0]);
      if (vista === 'escritorio') {  // teclado: el primer Tab debe llegar a un elemento visible (skip-link o enlace)
        aserciones++; await page.keyboard.press('Tab');
        const f = await page.evaluate(() => { const e = document.activeElement; if (!e || e === document.body) return null; const b = e.getBoundingClientRect(); const cs = getComputedStyle(e); return { ok: true, outline: cs.outlineStyle !== 'none' || cs.boxShadow !== 'none' }; });
        if (!f) add(u, vista, 'a11y-teclado', 'Tab no mueve el foco a ningun elemento'); else if (!f.outline) add(u, vista, 'a11y-foco-visible', 'el primer elemento enfocable no muestra foco');
      }
    } catch (e) { add(u, vista, 'smoke-carga', 'error al cargar/inspeccionar', e.message.split('\n')[0]); }
    await page.close();
  }
  await ctx.close();
}
await browser.close();
fs.writeFileSync(salida, JSON.stringify({ segundos: Math.round((Date.now() - t0) / 100) / 10, cargas, aserciones, paginas: urls.length, hallazgos }, null, 1));
console.log(`navegador: ${urls.length} paginas x ${VIEWS.length} vistas = ${cargas} cargas, ${aserciones} aserciones, ${hallazgos.length} fallos brutos en ${(Date.now() - t0) / 1000}s`);
