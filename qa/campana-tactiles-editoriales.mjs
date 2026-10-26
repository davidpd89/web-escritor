// Campana determinista (Via A): objetivos tactiles de al menos 24x24 px en movil (WCAG 2.2, 2.5.8). Familia: editoriales.
import { chromium } from 'playwright';
const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:8080';
const URLS = ["/editoriales/editorial-planeta/", "/editoriales/editorial-runaris/", "/editoriales/editorial-transito/", "/editoriales/foem-ceape/"];
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 375, height: 720 }, hasTouch: true });
const fallos = [];
for (const u of URLS) {
  const page = await ctx.newPage();
  await page.goto(ORIGIN + u, { waitUntil: 'load', timeout: 30000 });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  const peq = await page.evaluate(() => [...document.querySelectorAll('a[href],button,input,select,textarea,summary')].filter(e => {
    const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return b.width > 1 && b.height > 1 && cs.visibility !== 'hidden' && cs.opacity !== '0' && e.tabIndex >= 0 && !e.closest('[aria-hidden="true"],[hidden],[inert]') && b.right > 0 && b.bottom > 0 && b.left < innerWidth && (b.width < 24 || b.height < 24) && !(e.tagName === 'A' && e.closest('p,li,span,td') && cs.display === 'inline');
  }).slice(0, 5).map(e => { const b = e.getBoundingClientRect(); return `${e.tagName.toLowerCase()}.${String(e.className).slice(0, 30)} "${(e.textContent || e.getAttribute('aria-label') || '').trim().slice(0, 25)}" ${Math.round(b.width)}x${Math.round(b.height)}`; }));
  if (peq.length) fallos.push(`${u}: ${peq.join('; ')}`);
  await page.close();
}
await browser.close();
if (fallos.length) { console.error('FAIL objetivos tactiles < 24px en movil (WCAG 2.5.8):\n' + fallos.join('\n')); process.exit(1); }
console.log(`PASS: ${URLS.length} paginas sin objetivos tactiles < 24px`);
