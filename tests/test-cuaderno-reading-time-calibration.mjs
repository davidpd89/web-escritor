import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const dirs = fs.readdirSync('cuaderno', { withFileTypes: true }).filter(d => d.isDirectory() && d.name !== 'temas');
let inspected = 0;
for (const dir of dirs) {
  const file = path.join('cuaderno', dir.name, 'index.html');
  const html = fs.readFileSync(file, 'utf8');
  if (!/"@type"\s*:\s*"Article"/.test(html)) continue;
  const opening = /<div\b(?=[^>]*\bclass="[^"]*\barticle-prose\b[^"]*")[^>]*>/i.exec(html);
  let body;
  if (opening) {
    const start = opening.index + opening[0].length;
    const tags = /<\/?div\b[^>]*>/gi;
    tags.lastIndex = start;
    let depth = 1;
    let tag;
    while ((tag = tags.exec(html)) !== null) {
      depth += /^<\/div\b/i.test(tag[0]) ? -1 : 1;
      if (depth === 0) {
        body = html.slice(start, tag.index);
        break;
      }
    }
  }
  assert.ok(body, `${file}: no se encuentra cuerpo editorial`);
  const article = html.match(/<article\b[\s\S]*?<\/article>/)?.[0] || '';
  const match = article.match(/(\d+)\s*min(?:utos)? de lectura/i);
  assert.ok(match, `${file}: falta tiempo de lectura visible`);
  const minutes = Number(match[1]);
  const text = body.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<[^>]+>/g, ' ').replace(/&[a-z]+;/gi, ' ').replace(/\s+/g, ' ');
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  assert.ok(words >= 100, `${file}: recuento anormalmente pequeño (${words})`);
  const speed = words / minutes;
  assert.ok(speed >= 100 && speed <= 350, `${file}: ${words} palabras en ${minutes} minutos (${speed.toFixed(1)} palabras/minuto)`);
  inspected++;
}
assert.ok(inspected >= 5, `Solo ${inspected} artículos verificados`);
console.log(`OK: tiempos de lectura evaluados en ${inspected} artículos`);
