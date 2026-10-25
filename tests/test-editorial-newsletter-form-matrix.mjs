import assert from 'node:assert/strict';
import fs from 'node:fs';

const routes = [
  ['cuaderno/index.html', 'cuaderno'],
  ['cuaderno/que-es-el-portal-fantasy/index.html', 'cuaderno'],
  ['fragmento/index.html', 'fragmento'],
  ['las-manecillas-del-recuerdo/index.html', 'manecillas'],
];
for (const [file, source] of routes) {
  const html = fs.readFileSync(file, 'utf8');
  const forms = [...html.matchAll(/<form\b[^>]*data-newsletter-source="([^"]+)"[^>]*>[\s\S]*?<\/form>/g)];
  const form = forms.find(m => m[1] === source)?.[0];
  assert.ok(form, `${file}: falta formulario con source=${source}`);
  const input = form.match(/<input\b[^>]*type="email"[^>]*>/)?.[0];
  assert.ok(input, `${file}: falta campo email`);
  assert.ok(/\brequired\b/.test(input), `${file}: campo email no obligatorio`);
  const id = input.match(/\bid="([^"]+)"/)?.[1];
  const status = input.match(/aria-describedby="([^"]+)"/)?.[1];
  assert.ok(id && status, `${file}: falta id o asociación de estado`);
  assert.ok(form.includes(`for="${id}"`), `${file}: label sin asociación`);
  assert.ok(form.includes(`id="${status}"`), `${file}: estado inexistente`);
  assert.match(form, /aria-live="polite"/);
  assert.match(form, /type="submit"/);
  assert.ok(form.includes('/privacidad.html'), `${file}: falta enlace a privacidad`);
}
console.log('OK: procedencia y accesibilidad de formularios editoriales');
