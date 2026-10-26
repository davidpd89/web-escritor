import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const pages = ['index.html','autor.html','prensa.html','eventos.html','recomendaciones/index.html'];
const origin = 'https://davidportodiaz.com';

for (const page of pages) {
  const html = fs.readFileSync(path.join(root,page),'utf8');
  const metas = [...html.matchAll(/<meta\b[^>]*>/gi)].map(m=>m[0]);
  for (const property of ['og:image','twitter:image']) {
    const tag = metas.find(t=>new RegExp('(?:property|name)=["\\\']'+property+'["\\\']','i').test(t));
    assert.ok(tag,`${page}: falta ${property}`);
    const value = tag.match(/content=["']([^"']+)["']/i)?.[1];
    assert.ok(value,`${page}: ${property} sin URL`);
    const url = new URL(value,origin);
    assert.equal(url.origin,origin,`${page}: ${property} apunta a otro origen`);
    const pathname = decodeURIComponent(url.pathname);
    assert.match(pathname,/\.(?:png|jpe?g|webp|avif)$/i,`${page}: ${property} no identifica una imagen`);
    const asset = path.resolve(root,'.'+pathname);
    assert.ok(asset.startsWith(root+path.sep),`${page}: ruta de imagen fuera del repositorio`);
    assert.ok(fs.existsSync(asset),`${page}: ${property} apunta a ${pathname}, que no existe`);
    assert.ok(fs.statSync(asset).size>0,`${page}: ${pathname} está vacío`);
  }
}
console.log('PASS: recursos de imágenes sociales presentes');