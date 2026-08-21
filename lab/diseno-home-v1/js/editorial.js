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
    addEventListener('scroll', updateProgress, {passive:true});
    addEventListener('resize', updateProgress, {passive:true});
  }

  if (tocLinks.length && 'IntersectionObserver' in window) {
    const sections = tocLinks.map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
    const byId = new Map(tocLinks.map(a => [a.getAttribute('href').slice(1), a]));
    const observer = new IntersectionObserver(entries => {
      const visible = entries.filter(e => e.isIntersecting).sort((a,b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!visible) return;
      tocLinks.forEach(a => a.removeAttribute('aria-current'));
      byId.get(visible.target.id)?.setAttribute('aria-current','location');
    }, {rootMargin:'-18% 0px -68% 0px', threshold:0});
    sections.forEach(section => observer.observe(section));
  }

  document.querySelectorAll('[data-print]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', () => window.print());
  });
})();
