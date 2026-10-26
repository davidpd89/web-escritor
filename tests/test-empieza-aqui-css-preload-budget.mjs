import assert from 'node:assert/strict';
import fs from 'node:fs';

const file='empieza-aqui/index.html';
const html=fs.readFileSync(file,'utf8');
const links=[...html.matchAll(/<link\b[^>]*>/gi)].map(m=>m[0]);
const attr=(tag,key)=>tag.match(new RegExp(`\\b${key}\\s*=\\s*['\"]([^'\"]+)['\"]`,'i'))?.[1]||'';
const preloads=links.filter(tag=>attr(tag,'rel').split(/\s+/).includes('preload')&&attr(tag,'as')==='style');
const styles=links.filter(tag=>attr(tag,'rel').split(/\s+/).includes('stylesheet'));
assert(styles.length>0,`${file}: no hay hojas CSS publicadas`);
assert(preloads.length<=6,`${file}: ${preloads.length} precargas CSS; máximo 6. Recursos: ${preloads.map(t=>attr(t,'href')).join(', ')}`);
assert.match(html,/<main\b[^>]*id=['\"]contenido['\"]/i,`${file}: falta el contenido principal`);
console.log('Empieza aquí: presupuesto de precargas CSS correcto');