/* V1 Cuaderno/Artículo enhancements. Ported from lab/diseno-home-v1/js/editorial.js
   plus the lab's share handler. Progressive enhancement only: the article is
   complete and readable with this file absent or JavaScript disabled. */
(() => {
  'use strict';
  const root = document.documentElement;
  const body = document.querySelector('[data-article-body]');
  const meter = document.querySelector('[data-reading-progress-meter]');
  const tocLinks = [...document.querySelectorAll('[data-article-toc] a[href^="#"]')];

  if (body && meter) {
    const updateProgress = () => {
      const rect = body.getBoundingClientRect();
      const start = window.scrollY + rect.top;
      const end = start + body.offsetHeight - window.innerHeight;
      const value = end <= start ? 1 : Math.min(1, Math.max(0, (window.scrollY - start) / (end - start)));
      root.style.setProperty('--reading-progress', value.toFixed(4));
    };
    updateProgress();
    addEventListener('scroll', updateProgress, { passive: true });
    addEventListener('resize', updateProgress, { passive: true });
  }

  if (tocLinks.length && 'IntersectionObserver' in window) {
    const sections = tocLinks.map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
    const byId = new Map(tocLinks.map(a => [a.getAttribute('href').slice(1), a]));
    const observer = new IntersectionObserver(entries => {
      const visible = entries.filter(e => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!visible) return;
      tocLinks.forEach(a => a.removeAttribute('aria-current'));
      byId.get(visible.target.id)?.setAttribute('aria-current', 'location');
    }, { rootMargin: '-18% 0px -68% 0px', threshold: 0 });
    sections.forEach(section => observer.observe(section));
  }

  const ensurePrintSource = () => {
    const article = document.querySelector('.article-page article');
    if (!article || article.querySelector('.article-print-source')) return;
    const canonical = document.querySelector('link[rel="canonical"]')?.href || location.href;
    const title = article.querySelector('h1')?.textContent?.trim() || document.title;
    const source = document.createElement('p');
    source.className = 'article-print-source';
    source.setAttribute('aria-hidden', 'true');
    source.textContent = `${title} — ${canonical}`;
    article.appendChild(source);
  };

  document.querySelectorAll('[data-print]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', () => {
      ensurePrintSource();
      window.print();
    });
  });

  document.querySelectorAll('[data-share-url]').forEach(button => {
    button.hidden = false;
    const statusId = button.getAttribute('aria-describedby');
    const status = statusId ? document.getElementById(statusId) : null;
    button.addEventListener('click', async () => {
      const url = button.dataset.shareUrl;
      const title = button.dataset.shareTitle || document.title;
      if (!url) return;
      if (navigator.share) {
        try {
          await navigator.share({ title, url });
          if (status) status.textContent = 'Compartido.';
          return;
        } catch (error) {
          if (error?.name === 'AbortError') return;
        }
      }
      try {
        await navigator.clipboard.writeText(url);
        if (status) status.textContent = 'Enlace copiado.';
      } catch {
        if (status) status.textContent = 'No se pudo copiar el enlace.';
      }
    });
  });
})();
