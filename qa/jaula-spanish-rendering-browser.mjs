import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

for (const width of [390, 1440]) {
  await withJaula(async ({ page }) => {
    const result = await page.evaluate(() => {
      const paragraphs = [...document.querySelectorAll('.excerpt-field p')].map(p => p.textContent);
      const chapter = paragraphs.join('\n');
      return { charset: document.characterSet, language: document.documentElement.lang, paragraphs: paragraphs.length, hasDash: chapter.includes('—'), hasSpanishQuotes: chapter.includes('«') && chapter.includes('»'), hasReplacement: chapter.includes('\uFFFD'), hasEscapedUnicode: chapter.includes('\\u00'), heading: document.querySelector('h1')?.textContent.trim() };
    });
    assert.equal(result.charset.toUpperCase(), 'UTF-8');
    assert.equal(result.language, 'es');
    assert.equal(result.paragraphs, 133);
    assert.equal(result.heading, 'Dónde empieza la jaula');
    assert.ok(result.hasDash && result.hasSpanishQuotes, 'Se perdieron signos de la prosa española');
    assert.equal(result.hasReplacement, false, 'Caracteres de sustitución en el capítulo');
    assert.equal(result.hasEscapedUnicode, false, 'Secuencias Unicode visibles como texto');
  }, { width });
}
console.log('jaula-spanish-rendering-browser: OK');
