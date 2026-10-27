import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import fs from 'node:fs';
const browser = await chromium.launch({ headless: true });
const html = fs.readFileSync('lecturas/index.html', 'utf8').replace(/<link[^>]*rel="stylesheet"[^>]*>/g, '');
const css = fs.readFileSync('styles.css', 'utf8') + '\n' + fs.readFileSync('assets/reading-list.css', 'utf8');
const cases = [
  { name: 'unbroken', title: 'PalabraExtremadamenteLarga'.repeat(12), author: 'AutoraSinEspacios'.repeat(10), note: 'TextoSinSeparadores'.repeat(35) },
  { name: 'unicode', title: '星海物語'.repeat(35), author: 'Álvarez Núñez Fernández'.repeat(8), note: 'Memoria, tiempo y ficción. '.repeat(70) },
  { name: 'emoji', title: '📖'.repeat(55), author: 'Nombre con acentos y diéresis '.repeat(9), note: 'Una descripción extensa. '.repeat(90) }
];
try {
  for (const width of [320, 390, 768]) {
    const page = await browser.newPage({ viewport: { width, height: 850 } });
    try {
      await page.setContent(html);
      await page.addStyleTag({ content: css });
      for (const item of cases) {
        const result = await page.evaluate(data => {
          document.querySelector('.reading-card h3').textContent = data.title;
          document.querySelector('.reading-author').textContent = data.author;
          const paragraphs = document.querySelectorAll('.reading-card > p');
          paragraphs[2].textContent = data.note;
          const card = document.querySelector('.reading-card');
          const offenders = [...card.querySelectorAll('*')].filter(el => el.scrollWidth > el.clientWidth + 1).map(el => el.tagName + '.' + el.className);
          const rect = card.getBoundingClientRect();
          return { offenders, cardRight: rect.right, width: innerWidth };
        }, item);
        assert.deepEqual(result.offenders, [], `${item.name} ${width}px`);
        assert(result.cardRight <= result.width + 1, `${item.name}: card outside viewport`);
      }
    } finally { await page.close(); }
  }
} finally { await browser.close(); }
