/*
 * Private tools shell — davidportodiaz.com
 * Deliberately network-free and storage-free.
 * Used on manuscript tools instead of /script.js so third-party analytics,
 * newsletter code and service-worker registration are not present in the page.
 */
(() => {
  'use strict';

  const navToggle = document.querySelector('.nav-toggle');
  const siteNav = document.querySelector('.site-nav');

  if (navToggle && siteNav) {
    const closeNav = (returnFocus = false) => {
      siteNav.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
      if (returnFocus) navToggle.focus();
    };

    navToggle.addEventListener('click', () => {
      const isOpen = siteNav.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', String(isOpen));
    });

    siteNav.addEventListener('click', (event) => {
      if (event.target.closest('a')) closeNav(false);
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && siteNav.classList.contains('is-open')) {
        closeNav(true);
      }
    });
  }

  document.querySelectorAll('[data-private-tools-backtop]').forEach((button) => {
    button.addEventListener('click', () => {
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });
    });
  });
})();
