import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

await withJaula(async ({ page }) => {
  await page.emulateMedia({ media: 'print' });
  const metrics = await page.locator('#capitulo-1').evaluate(section => {
    const prose = section.querySelector('.excerpt-field');
    const style = getComputedStyle(section);
    const proseStyle = getComputedStyle(prose);
    return { paragraphs: prose.querySelectorAll('p').length, height: section.getBoundingClientRect().height, breakInside: style.breakInside, pageBreakInside: style.pageBreakInside, display: style.display, proseDisplay: proseStyle.display, proseVisibility: proseStyle.visibility };
  });
  assert.equal(metrics.paragraphs, 133);
  assert.ok(metrics.height > 1000, 'La muestra debe abarcar más de una página de impresión');
  assert.notEqual(metrics.display, 'none');
  assert.notEqual(metrics.proseDisplay, 'none');
  assert.notEqual(metrics.proseVisibility, 'hidden');
  assert.notEqual(metrics.breakInside, 'avoid', 'La sección larga no debe impedir los saltos de página');
  assert.notEqual(metrics.pageBreakInside, 'avoid', 'La sección larga no debe impedir la fragmentación paginada');
});
console.log('jaula-print-fragmentation-browser: OK');
