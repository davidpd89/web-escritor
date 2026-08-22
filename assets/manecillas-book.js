(() => {
  'use strict';

  const button = document.querySelector('[data-book-share]');
  if (!button) return;

  const status = document.getElementById(button.getAttribute('aria-describedby') || '');
  const url = button.dataset.shareUrl || location.href.split('#')[0];
  const title = button.dataset.shareTitle || document.title;

  const announce = (message) => {
    if (status) status.textContent = message;
  };

  const copyLink = async () => {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url);
      announce('Enlace copiado.');
      return;
    }

    const field = document.createElement('textarea');
    field.value = url;
    field.setAttribute('readonly', '');
    field.style.position = 'fixed';
    field.style.opacity = '0';
    document.body.appendChild(field);
    field.select();
    const copied = document.execCommand('copy');
    field.remove();
    announce(copied ? 'Enlace copiado.' : 'No se pudo copiar el enlace.');
  };

  button.hidden = false;
  button.addEventListener('click', async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title, url });
        announce('Compartido.');
        return;
      } catch (error) {
        if (error?.name === 'AbortError') return;
      }
    }

    try {
      await copyLink();
    } catch {
      announce('No se pudo copiar el enlace.');
    }
  });
})();
