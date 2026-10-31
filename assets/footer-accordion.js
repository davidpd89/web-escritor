/* Pie de pagina: las columnas son <details open> (sin JS se ven todas).
 * En movil se pliegan como desplegables; en escritorio quedan siempre
 * abiertas y el resumen no se puede cerrar. */
(() => {
  'use strict';

  const groups = document.querySelectorAll('.site-footer .footer-group');
  if (!groups.length || !window.matchMedia) return;

  const mobile = window.matchMedia('(max-width: 767px)');
  let syncing = false;

  const sync = () => {
    syncing = true;
    groups.forEach((group) => {
      group.open = !mobile.matches;
    });
    requestAnimationFrame(() => { syncing = false; });
  };

  groups.forEach((group) => {
    group.addEventListener('toggle', () => {
      if (syncing || mobile.matches || group.open) return;
      group.open = true;
    });
  });

  sync();
  mobile.addEventListener('change', sync);
})();
