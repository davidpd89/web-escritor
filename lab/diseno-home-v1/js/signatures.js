/** Optional route-spine progress. Decorative only; navigation never depends on it. */
(() => {
  'use strict';
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const items = [...document.querySelectorAll('[data-route-step]')];
  if (!items.length || !('IntersectionObserver' in window)) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.dataset.routeActive = 'true';
    });
  }, { rootMargin: '-20% 0px -55% 0px', threshold: 0.01 });
  items.forEach((item) => observer.observe(item));
})();
