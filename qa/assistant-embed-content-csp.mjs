import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const page = await browser.newPage();
  const response = await page.goto(`${origin}/asistente/embed.html`, {waitUntil:'domcontentloaded'});
  assert.equal(response.status(),200,'/asistente/embed.html: respuesta HTTP');
  const header = response.headers()['content-security-policy'] || '';
  const meta = await page.locator('meta[http-equiv="Content-Security-Policy" i]').allTextContents();
  const metaPolicies = await page.locator('meta[http-equiv="Content-Security-Policy" i]').evaluateAll(nodes=>nodes.map(n=>n.content));
  const policies = [header,...metaPolicies].filter(Boolean);
  assert(policies.length>0,'/asistente/embed.html: falta CSP efectiva');
  const directives = new Map();
  for(const policy of policies) for(const part of policy.split(';')) {
    const tokens=part.trim().split(/\s+/);
    if(tokens[0] && !directives.has(tokens[0])) directives.set(tokens[0],tokens.slice(1));
  }
  const scripts=directives.get('script-src') || directives.get('default-src') || [];
  assert(scripts.includes("'self'"),'/asistente/embed.html: scripts sin origen propio autorizado');
  assert(!scripts.includes("'unsafe-inline'") && !scripts.includes('*'),'/asistente/embed.html: política de scripts demasiado permisiva');
  assert((directives.get('object-src')||[]).includes("'none'"),'/asistente/embed.html: object-src debe prohibirse');
  assert(directives.has('base-uri'),'/asistente/embed.html: base-uri sin restricción');
  assert(!((directives.get('base-uri')||[]).includes('*')),'/asistente/embed.html: base-uri universal');
  console.log('assistant-embed-content-csp: OK');
} finally { await browser.close(); }
