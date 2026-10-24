import assert from 'node:assert/strict';
import fs from 'node:fs';

const standalone = fs.readFileSync(new URL('../asistente/index.html', import.meta.url), 'utf8');
const embedded = fs.readFileSync(new URL('../asistente/embed.html', import.meta.url), 'utf8');
const client = fs.readFileSync(new URL('../assets/assistant.js', import.meta.url), 'utf8');
function tag(html, selector) {
  const re = new RegExp(`<([a-z]+)\\b[^>]*${selector}[^>]*>`, 'i');
  const result = html.match(re)?.[0];
  assert.ok(result, `missing ${selector}`);
  return result;
}
function attribute(html, name) {
  return html.match(new RegExp(`\\b${name}=["']([^"']+)["']`, 'i'))?.[1] || null;
}
const selectors = ['data-assistant-form', 'data-assistant-query', 'data-assistant-submit', 'data-assistant-stop', 'data-assistant-status', 'data-assistant-turnstile'];
for (const selector of selectors) {
  const a = tag(standalone, selector);
  const b = tag(embedded, selector);
  assert.equal(a.match(/^<\w+/)?.[0], b.match(/^<\w+/)?.[0], `${selector}: tag mismatch`);
}
const a = tag(standalone, 'data-assistant-query');
const b = tag(embedded, 'data-assistant-query');
for (const attr of ['id', 'name', 'maxlength', 'autocomplete', 'placeholder']) assert.equal(attribute(a, attr), attribute(b, attr), `${attr}: composer mismatch`);
assert.ok(/\brequired\b/.test(a) && /\brequired\b/.test(b));
assert.equal(attribute(tag(standalone, 'data-assistant-submit'), 'aria-label'), attribute(tag(embedded, 'data-assistant-submit'), 'aria-label'));
assert.match(client, /textarea\.maxLength\s*=\s*QUERY_MAX_LENGTH/);
assert.match(client, /textarea\.required\s*=\s*true/);
console.log('PASS standalone/embed assistant form parity');
