/* Progressive enhancement only. All book text, covers and links are static HTML. */
(() => {
  'use strict';
  const root = document.querySelector('[data-reading-catalogue]');
  if (!root) return;
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').trim();
  const form = root.querySelector('[data-catalogue-filters]');
  if (form) {
    const cards = [...root.querySelectorAll('[data-catalogue-book]')];
    const fields = [...form.querySelectorAll('[data-filter]')];
    const count = root.querySelector('[data-catalogue-count]');
    const empty = root.querySelector('[data-catalogue-empty]');
    const today = () => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
    const isNew = published => {
      if (!published) return false;
      const days = (Date.parse(`${today()}T00:00:00Z`) - Date.parse(`${published}T00:00:00Z`)) / 86400000;
      return days >= 0 && days <= 180;
    };
    const apply = (save = true) => {
      const values = Object.fromEntries(fields.map(field => [field.dataset.filter, field.value]));
      let visible = 0;
      for (const card of cards) {
        const categories = card.dataset.categories.split(' ');
        const match = normalize(card.dataset.search).includes(normalize(values.q || '')) && fields.every(field => {
          const key = field.dataset.filter;
          return !field.value || key === 'q' || (key === 'novedad' ? isNew(card.dataset.published) : categories.includes(field.value));
        });
        card.hidden = !match;
        if (match) visible++;
      }
      count.textContent = `${visible} ${visible === 1 ? 'libro' : 'libros'}`;
      empty.hidden = visible !== 0;
      if (save) {
        const hash = new URLSearchParams(Object.entries(values).filter(([, value]) => value));
        history.replaceState(null, '', `${location.pathname}${hash.size ? `#${hash}` : ''}`);
      }
    };
    const restore = () => {
      const params = new URLSearchParams(location.hash.slice(1));
      for (const field of fields) {
        const value = params.get(field.dataset.filter) || '';
        field.value = field.tagName === 'SELECT' && ![...field.options].some(option => option.value === value) ? '' : value;
      }
      apply(false);
    };
    form.querySelector('fieldset').disabled = false;
    form.querySelector('button[type="reset"]').disabled = false;
    form.addEventListener('input', () => apply());
    form.addEventListener('submit', event => { event.preventDefault(); apply(); });
    form.addEventListener('reset', () => { queueMicrotask(() => apply()); });
    window.addEventListener('hashchange', restore);
    window.addEventListener('pageshow', () => apply(false));
    document.addEventListener('visibilitychange', () => { if (!document.hidden) apply(false); });
    restore();
  }
  const speak = root.querySelector('[data-catalogue-speak]');
  if (speak && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window) {
    const stop = root.querySelector('[data-catalogue-stop]');
    const status = root.querySelector('[data-catalogue-speech-status]');
    speak.parentElement.hidden = false;
    const finish = message => { speak.disabled = false; stop.disabled = true; status.textContent = message; };
    speak.addEventListener('click', () => {
      speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(root.querySelector('[data-catalogue-description]').textContent);
      utterance.lang = 'es-ES';
      utterance.onend = () => finish('Lectura terminada.');
      utterance.onerror = () => finish('No se ha podido continuar la lectura. Puedes volver a intentarlo.');
      speak.disabled = true;
      stop.disabled = false;
      status.textContent = 'Leyendo la descripción.';
      speechSynthesis.speak(utterance);
    });
    const cancel = () => { speechSynthesis.cancel(); finish('Lectura detenida.'); };
    stop.addEventListener('click', cancel);
    window.addEventListener('pagehide', cancel);
  }
})();
