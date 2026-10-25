import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const html=await fs.readFile(new URL('../gracias-suscripcion/index.html',import.meta.url),'utf8');
const csp=html.match(/<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"/i)?.[1];
assert.ok(csp,'Falta CSP');
const scriptSrc=csp.split(';').map(s=>s.trim()).find(s=>s.startsWith('script-src '));
assert.ok(scriptSrc,'Falta script-src');
const scripts=[...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].filter(m=>!/(?:type\s*=\s*["']application\/ld\+json["'])/i.test(m[1])&&!/\bsrc\s*=/i.test(m[1]));
assert.ok(scripts.length>0,'Debe existir el script de confirmación');
for(const [,attrs,code] of scripts){
  const hash=createHash('sha256').update(code,'utf8').digest('base64');
  assert.ok(scriptSrc.includes(`'sha256-${hash}'`),`La CSP no autoriza el hash ${hash}`);
}
console.log('newsletter confirmation CSP hash: OK');