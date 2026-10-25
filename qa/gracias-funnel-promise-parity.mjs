import assert from 'node:assert/strict';
import fs from 'node:fs';

const thanks = fs.readFileSync('gracias-suscripcion/index.html', 'utf8');
const routes = [
  ['index.html', 'newsletter-form-home'],
  ['cuaderno/index.html', 'newsletter-form-cuaderno'],
  ['fragmento/index.html', 'newsletter-form-fragmento'],
  ['las-manecillas-del-recuerdo/index.html', 'newsletter-form-manecillas'],
  ['gracias-suscripcion/index.html', 'newsletter-form-explore']
];
const unspecified = [];
for (const [file, id] of routes) {
  const html = fs.readFileSync(file, 'utf8');
  const at = html.indexOf(`id="${id}"`);
  assert(at >= 0, `${file}: ${id} missing`);
  const proposition = html.slice(Math.max(0, at - 1100), at).replace(/<[^>]+>/g, ' ');
  if (!/Samuel/i.test(proposition) || !/capítulo|fragmento/i.test(proposition)) unspecified.push(file);
}
assert(!/tal y como prometía el formulario/i.test(thanks) || unspecified.length === 0,
  `One shared DOI landing asserts a chapter was promised, but these funnels do not: ${unspecified.join(', ')}`);
console.log('PASS shared landing promise parity');
