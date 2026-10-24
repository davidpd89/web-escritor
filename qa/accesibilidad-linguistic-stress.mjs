import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  for (const width of [320, 375, 768]) {
    await page.setViewportSize({ width, height: 850 });
    await page.evaluate(() => {
      document.querySelector('#estandar').textContent = 'Estándares de accesibilidad, comprensión lingüística y navegación internacionalizada';
      document.querySelector('.a11y-route-list li').textContent = 'Revisión de ' + 'hiperresponsabilizacióninterdisciplinaria'.repeat(8) + ' en navegadores móviles';
    });
    await page.addStyleTag({ content: 'main p, main li, main h2 { line-height: 1.7 !important; letter-spacing: .12em !important; word-spacing: .16em !important; } main p { margin-bottom: 2em !important; }' });
    const state = await page.evaluate(() => {
      const sections = [...document.querySelectorAll('main section.v1-section')];
      const rects = sections.map(el => el.getBoundingClientRect());
      return { overflow: document.documentElement.scrollWidth > innerWidth + 1, overlap: rects.some((r, i) => i && r.top < rects[i - 1].bottom - 1), headings: sections.every(section => section.querySelector('h2')?.id === section.getAttribute('aria-labelledby')) };
    });
    assert.equal(state.overflow, false, `${width}: desbordamiento textual`);
    assert.equal(state.overlap, false, `${width}: secciones solapadas`);
    assert.equal(state.headings, true);
    await page.reload({ waitUntil: 'load' });
  }
});
console.log('accesibilidad-linguistic-stress: PASS');
