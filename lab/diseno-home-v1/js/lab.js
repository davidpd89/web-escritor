(() => {
  'use strict';

  const root = document.documentElement;
  root.classList.add('js');

  const fixture = window.LAB_FIXTURES?.[root.dataset.fixture] || {};
  const q = (s, c = document) => c.querySelector(s);
  const qa = (s, c = document) => [...c.querySelectorAll(s)];

  function applyFixture() {
    if (fixture.heroTitle) q('[data-fixture-target="hero-title"]').textContent = fixture.heroTitle;
    if (fixture.bookTitle) q('[data-fixture-target="book-title"]').textContent = fixture.bookTitle;
    if (fixture.date) q('[data-fixture-target="date"]').textContent = fixture.date;
    if (fixture.hideMedia) root.dataset.fixture = 'no-media';
    if (fixture.riverSignals) {
      qa('[data-signal]').forEach((el, i) => { if (i >= fixture.riverSignals) el.hidden = true; });
    }
    if (fixture.fontFallback) root.classList.add('force-font-fallback');
  }

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
      manecillas:['Las manecillas del recuerdo','La obra actual y punto de entrada editorial.'],
      autor:['Autor','Biografía, obra y trayectoria de David Porto Díaz.'],
      samuel:['Samuel entre mundos','Primera novela publicada.'],
      jaula:['Dónde empieza la jaula','Proyecto en desarrollo con información pública limitada.'],
      cuaderno:['Cuaderno','Artículos y piezas editoriales.'],
      herramientas:['Herramientas','Utilidades gratuitas para problemas concretos de escritura y publicación.'],
      prensa:['Prensa y eventos','Apariciones, materiales de prensa y agenda.']
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

  function initMediaFallbacks() {
    qa('[data-media-img]').forEach((img) => {
      img.addEventListener('error', () => {
        const object = img.closest('[data-media]');
        if (object) object.hidden = true;
        const shell = img.closest('[data-hero-media]');
        const fallback = shell?.querySelector('[data-media-fallback]');
        if (fallback && !shell.querySelector('[data-media]:not([hidden])')) fallback.hidden = false;
      }, { once: true });
    });
  }

  function initMap() {
    const map = q('[data-map]');
    if (!map) return;
    qa('[data-map-node]', map).forEach((node) => {
      const on = () => map.dataset.active = node.dataset.mapNode;
      const off = () => delete map.dataset.active;
      node.addEventListener('mouseenter', on);
      node.addEventListener('mouseleave', off);
      node.addEventListener('focus', on);
      node.addEventListener('blur', off);
    });
  }

  function initDemoForm() {
    const form = q('[data-demo-form]');
    if (!form) return;
    const email = q('input[type="email"]', form);
    const consent = q('input[type="checkbox"][required]', form);
    const status = q('[role="status"]', form);
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      status.textContent = '';
      email?.removeAttribute('aria-invalid');
      consent?.removeAttribute('aria-invalid');

      if (!email || !email.validity.valid) {
        email?.setAttribute('aria-invalid', 'true');
        status.textContent = 'Introduce una dirección de correo válida.';
        email?.focus();
        return;
      }
      if (!consent || !consent.checked) {
        consent?.setAttribute('aria-invalid', 'true');
        status.textContent = 'Acepta la política de privacidad para continuar.';
        consent?.focus();
        return;
      }

      status.textContent = 'Estado de laboratorio: validación completa; no se envían datos.';
    });
  }

  async function copyShareUrl(url) {
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(url);
        return true;
      } catch (_) {}
    }
    const field = document.createElement('textarea');
    field.value = url;
    field.setAttribute('readonly', '');
    field.style.position = 'fixed';
    field.style.opacity = '0';
    document.body.append(field);
    field.select();
    let copied = false;
    try { copied = document.execCommand('copy'); } catch (_) {}
    field.remove();
    return copied;
  }

  function initShare() {
    qa('[data-share-url]').forEach((button) => {
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
        const copied = await copyShareUrl(url);
        if (status) status.textContent = copied ? 'Enlace copiado.' : 'No se pudo copiar el enlace.';
      });
    });
  }

  applyFixture();
  initHeader();
  initExplore();
  initMediaFallbacks();
  initMap();
  initDemoForm();
  initShare();
})();
