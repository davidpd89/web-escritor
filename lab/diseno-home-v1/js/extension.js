/** V1 family lab enhancement. Static HTML remains complete without this file. */
(() => {
  'use strict';

  document.documentElement.classList.add('has-v1-js');

  document.querySelectorAll('[data-copy-target]').forEach((button) => {
    button.addEventListener('click', async () => {
      const target = document.getElementById(button.dataset.copyTarget || '');
      if (!target) return;
      const text = target.innerText.trim();
      try {
        await navigator.clipboard.writeText(text);
        const previous = button.textContent;
        button.textContent = 'Copiado';
        window.setTimeout(() => { button.textContent = previous; }, 1600);
      } catch {
        target.setAttribute('tabindex', '-1');
        target.focus();
      }
    });
  });

  const search = document.querySelector('[data-tool-search]');
  const rows = [...document.querySelectorAll('[data-tool-row]')];
  const count = document.querySelector('[data-tool-count]');
  if (search && rows.length) {
    const filter = () => {
      const query = search.value.trim().toLocaleLowerCase('es');
      let visible = 0;
      rows.forEach((row) => {
        const haystack = (row.dataset.search || row.textContent).toLocaleLowerCase('es');
        const match = !query || haystack.includes(query);
        row.hidden = !match;
        if (match) visible += 1;
      });
      if (count) count.textContent = `${visible} ${visible === 1 ? 'herramienta' : 'herramientas'}`;
    };
    search.addEventListener('input', filter);
  }

  const previews = document.querySelectorAll('[data-preview-source]');
  const previewTitle = document.querySelector('[data-preview-title]');
  const previewText = document.querySelector('[data-preview-text]');
  if (previews.length && previewTitle && previewText && matchMedia('(hover:hover) and (pointer:fine)').matches) {
    previews.forEach((link) => {
      link.addEventListener('mouseenter', () => {
        previewTitle.textContent = link.dataset.previewTitle || '';
        previewText.textContent = link.dataset.previewText || '';
      });
      link.addEventListener('focus', () => {
        previewTitle.textContent = link.dataset.previewTitle || '';
        previewText.textContent = link.dataset.previewText || '';
      });
    });
  }
})();
