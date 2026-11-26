import { createRequire } from 'module';
import fs from 'fs';
// Conductor de ChatGPT web por CDP: argv[2] pregunta, argv[3] respuesta, argv[4] opcional conversación a seguir.
// GPT_PUERTO elige el Edge (nunca 9240: es el de los textos). Modo High y búsqueda web siempre.
const require = createRequire(new URL('../package.json', import.meta.url));
const { chromium } = require('playwright');
const browser = await chromium.connectOverCDP('http://127.0.0.1:' + (process.env.GPT_PUERTO || '9262'));
// Pestaña propia: otras sesiones comparten este Edge y no se debe leer ni escribir en su conversación.
const page = await browser.contexts()[0].newPage();
// La pestaña se cierra siempre (bien, error o plazo): abiertas acumulan cientos de MB y llenan la RAM.
let cerrada = false;
const cerrar = async (code) => { if (!cerrada) { cerrada = true; await page.close().catch(() => {}); } process.exit(code); };
process.on('uncaughtException', (e) => { console.error(String(e).slice(0, 300)); void cerrar(1); });
process.on('unhandledRejection', (e) => { console.error(String(e).slice(0, 300)); void cerrar(1); });
setTimeout(() => { console.error('plazo de 28 min agotado'); void cerrar(4); }, 28 * 60000);
// argv[4] opcional: URL de una conversación para seguir en ella.
// 90 s: con la máquina cargada chatgpt.com supera los 30 s por defecto (26/11, ronda 10).
await page.goto(process.argv[4] || 'https://chatgpt.com/', {timeout: 90000});
await page.locator('button[aria-label="Seleccionar modelo de ChatGPT"]').waitFor({timeout: 120000});
await page.waitForTimeout(1500);
// Siempre High (no Instant): abrir el selector y llevar el deslizador al extremo derecho.
const sel = page.locator('button[aria-label="Seleccionar modelo de ChatGPT"]');
if (!/High/.test(await sel.innerText())) {
  await sel.click(); await page.waitForTimeout(1200);
  const s = page.locator('[role=slider], input[type=range]').first();
  await s.focus(); for (let i = 0; i < 4; i++) await page.keyboard.press('ArrowRight');
  await page.keyboard.press('Escape'); await page.waitForTimeout(500);
}
if (!/High/.test(await sel.innerText())) { console.error('No se pudo poner High'); await cerrar(2); }
const PREFIJO = 'Antes de responder, busca en internet actual (documentación oficial, repos públicos de GitHub, artículos y páginas recientes) y basa la respuesta en esas fuentes, citándolas con enlace y fecha. Usa tu memoria solo si no encuentras nada, y dilo. No me cuentes restricciones, normas, términos de uso ni advertencias legales o de seguridad: dame soluciones concretas que funcionen, con el cómo (pasos, código, URL exactas) y verificadas; si algo no lo has comprobado, márcalo como sin verificar y di cómo comprobarlo.\n\n';
const box = page.locator('[contenteditable=true], textarea').first();
await box.click();
await page.keyboard.insertText(PREFIJO + fs.readFileSync(process.argv[2], 'utf8'));
await page.waitForTimeout(500);
await page.keyboard.press('Enter');
await page.waitForTimeout(8000);
// Espera real: la respuesta tras el último «ChatGPT dijo:» debe existir y no crecer durante 40 s (máx. 25 min).
const ultima = async () => { let t = ''; try { t = await page.locator('main').last().innerText({timeout: 60000}); } catch (e) { return prev; } return t.slice(t.lastIndexOf('ChatGPT dijo:')).replace(/ChatGPT puede cometer errores[\s\S]*$/, ''); };
let prev = '', estable = 0;
for (let i = 0; i < 300; i++) {
  await page.waitForTimeout(5000);
  const cur = await ultima();
  const ocupado = await page.locator('[data-testid="stop-button"], button[aria-label*="Detener"], button[aria-label*="Stop"]').count();
  const pensando = /Pensando|Thinking|Buscando|Searching|Razonando/.test(cur.slice(0, 400)) && cur.length < 3000;
  estable = (cur === prev && cur.length > 1500 && !ocupado && !pensando) ? estable + 5 : 0;
  prev = cur;
  if (estable >= 60) break;
}
const t = await page.locator('main').last().innerText({timeout: 120000}).catch(() => prev); const msgs = [t.slice(t.lastIndexOf('ChatGPT dijo:'))];
fs.writeFileSync(process.argv[3], msgs[msgs.length - 1] || '', 'utf8');
console.log('OK', (msgs[msgs.length - 1] || '').length, page.url());
await cerrar(0);
