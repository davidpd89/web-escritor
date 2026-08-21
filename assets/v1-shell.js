// V1 editorial shell — Explorar <dialog>, header scroll state, cartography
// hover preview. Ported from lab/diseno-home-v1/js/lab.js (initHeader,
// initExplore, initMap only — the lab's demo-form/fixtures/share helpers
// are lab-only and not needed here: production newsletter submission stays
// in script.js's submitNewsletter(), bound by the same element IDs).
(() => {
  'use strict';
  document.documentElement.classList.add('has-js');
  const q = (s, c = document) => c.querySelector(s);
  const qa = (s, c = document) => [...c.querySelectorAll(s)];

  function initHeader() {
    const header = q('[data-header]');
    if (!header) return;
    let ticking = false;
    const update = () => {
      header.dataset.scrolled = window.scrollY > 18 ? 'true' : 'false';
      ticking = false;
    };
    addEventListener('scroll', () => {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
    update();
  }

  function initExplore() {
    const dialog = q('[data-explore-dialog]');
    const open = q('[data-explore-open]');
    const close = q('[data-explore-close]');
    if (!dialog || !open || !close || typeof dialog.showModal !== 'function') return;

    let opener = null;
    open.addEventListener('click', () => {
      opener = document.activeElement;
      open.setAttribute('aria-expanded', 'true');
      dialog.showModal();
      close.focus();
    });
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('close', () => {
      open.setAttribute('aria-expanded', 'false');
      if (opener instanceof HTMLElement) opener.focus({ preventScroll: true });
    });

    const preview = q('[data-explore-preview]', dialog);
    const label = q('[data-preview-label]', dialog);
    const copy = q('[data-preview-copy]', dialog);
    const media = q('[data-preview-media]', dialog);
    const content = {
      manecillas: ['Las manecillas del recuerdo', 'La obra actual y punto de entrada editorial.'],
      autor: ['Autor', 'Biografía, obra y trayectoria de David Porto Díaz.'],
      samuel: ['Samuel entre mundos', 'Primera novela publicada.'],
      cuaderno: ['Cuaderno', 'Artículos y piezas editoriales.'],
      herramientas: ['Herramientas', 'Utilidades gratuitas para problemas concretos de escritura y publicación.'],
      prensa: ['Prensa y eventos', 'Apariciones, materiales de prensa y agenda.']
    };
    const setPreview = (key) => {
      if (!preview || !content[key]) return;
      label.textContent = content[key][0];
      copy.textContent = content[key][1];
      media.dataset.preview = key;
    };
    qa('[data-preview]', dialog).forEach((link) => {
      link.addEventListener('mouseenter', () => setPreview(link.dataset.preview));
      link.addEventListener('focus', () => setPreview(link.dataset.preview));
    });
  }

  function initMap() {
    const map = q('[data-map]');
    if (!map) return;
    qa('[data-map-node]', map).forEach((node) => {
      const on = () => { map.dataset.active = node.dataset.mapNode; };
      const off = () => { delete map.dataset.active; };
      node.addEventListener('mouseenter', on);
      node.addEventListener('mouseleave', off);
      node.addEventListener('focus', on);
      node.addEventListener('blur', off);
    });
  }

  initHeader();
  initExplore();
  initMap();
})();
