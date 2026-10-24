import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const files = ['cuaderno/index.html', ...fs.readdirSync('cuaderno', { withFileTypes: true }).filter(d => d.isDirectory()).flatMap(d => {
  const base = path.join('cuaderno', d.name);
  if (d.name === 'temas') return [];
  return [path.join(base, 'index.html')];
})];
const feed = 'https://davidportodiaz.com/cuaderno/feed.xml';
assert.ok(fs.statSync('cuaderno/feed.xml').size > 100);
for (const file of files) {
  const html = fs.readFileSync(file, 'utf8');
  const head = html.split('</head>')[0];
  const links = [...head.matchAll(/<link\b[^>]*>/g)].map(m => m[0]);
  const rss = links.filter(tag => /type="application\/rss\+xml"/.test(tag));
  assert.equal(rss.length, 1, `${file}: debe anunciar un único RSS`);
  assert.ok(rss[0].includes(`href="${feed}"`), `${file}: RSS no canónico`);
}
console.log(`OK: RSS discoverable en ${files.length} páginas`);
