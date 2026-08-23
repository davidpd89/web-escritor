import assert from 'node:assert/strict';
import {
  READING_CARD_LIMITS,
  READING_CARD_TOOL_URL,
  buildReadingCardOutputs,
  validateReadingCardInput,
} from '../assets/tarjeta-estoy-leyendo-core.js';

const base = { label: 'leyendo', title: 'La casa del reloj', author: 'Ana Ejemplo', includeReference: false };
assert.deepEqual(validateReadingCardInput(base), []);

const a = buildReadingCardOutputs(base);
const b = buildReadingCardOutputs({ ...base });
assert.deepEqual(a, b, 'same input must produce deterministic output');
assert.ok(a.html.includes('Estoy leyendo'));
assert.ok(a.html.includes('<cite>Ana Ejemplo</cite>'));
assert.ok(!a.html.includes(READING_CARD_TOOL_URL), 'backlink must be absent by default');
assert.ok(!a.markdown.includes(READING_CARD_TOOL_URL), 'Markdown backlink must be absent by default');

const withReference = buildReadingCardOutputs({ ...base, includeReference: true });
assert.ok(withReference.html.includes(READING_CARD_TOOL_URL));
assert.ok(withReference.html.includes('rel="nofollow noopener noreferrer"'));
assert.ok(withReference.markdown.includes(READING_CARD_TOOL_URL));

const hostile = buildReadingCardOutputs({
  ...base,
  title: '<script>globalThis.pwned=1</script><img src=x onerror=alert(1)>',
  author: 'javascript:alert(1) & "autor"',
});
assert.ok(hostile.html.includes('&lt;script&gt;'));
assert.ok(hostile.html.includes('&lt;img'));
assert.ok(hostile.html.includes('onerror=alert(1)'), 'hostile source text should be preserved as escaped text');
assert.ok(hostile.html.includes('&amp;'));
assert.ok(!hostile.html.includes('<script'));
assert.ok(!hostile.html.includes('<img'));
assert.ok(!hostile.html.includes('href="javascript:'));
assert.ok(!/<(?:script|iframe)\b/i.test(hostile.html));

for (const invalid of [
  { ...base, title: '' },
  { ...base, author: '' },
  { ...base, label: 'inventada' },
  { ...base, title: 'x'.repeat(READING_CARD_LIMITS.title + 1) },
  { ...base, author: 'x'.repeat(READING_CARD_LIMITS.author + 1) },
]) {
  assert.ok(validateReadingCardInput(invalid).length > 0, `expected invalid: ${JSON.stringify(invalid)}`);
  assert.throws(() => buildReadingCardOutputs(invalid));
}

const markdownHostile = buildReadingCardOutputs({ ...base, title: '[Título](javascript:alert(1))', author: '*Autor*' });
assert.ok(markdownHostile.markdown.includes('\\['));
assert.ok(markdownHostile.markdown.includes('\\*Autor\\*'));

console.log('tests/test-tarjeta-estoy-leyendo: OK');
