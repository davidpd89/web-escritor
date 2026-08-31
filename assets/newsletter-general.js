(() => {
  'use strict';
  if (window.DPNewsletterGeneral) return;

  const ENDPOINT = 'https://subscribe.davidpd89.workers.dev';
  const TIMEOUT_MS = 12000;
  const EMAIL_RE = /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@]{2,}$/;
  const STAGING_HOSTNAMES = new Set(['david-porto-preview.davidpd89.workers.dev']);
  const STAGING_MESSAGE = 'Formulario desactivado en el entorno de pruebas.';
  const PENDING_COPY = {
    home: 'Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.',
    fragmento: 'Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.',
    manecillas: 'Revisa tu correo y confirma la suscripción. Después te avisaré cuando Las manecillas del recuerdo esté disponible.',
    cuaderno: 'Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.',
    explore: 'Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.'
  };

  function isValidEmail(value) {
    const normalized = String(value || '').trim();
    return normalized.length <= 254 && EMAIL_RE.test(normalized);
  }

  function honeypotValue(form) {
    const field = form?.querySelector('input[name="website"]');
    return field ? String(field.value || '').trim() : '';
  }

  function installHoneypot(form) {
    if (!form || form.querySelector('input[name="website"]')) return;
    const wrapper = document.createElement('div');
    wrapper.setAttribute('aria-hidden', 'true');
    wrapper.setAttribute('inert', '');
    wrapper.style.cssText = 'position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0;';
    const field = document.createElement('input');
    field.type = 'text';
    field.name = 'website';
    field.autocomplete = 'off';
    field.tabIndex = -1;
    wrapper.appendChild(field);
    form.appendChild(wrapper);
  }

  function errorMessage(code) {
    if (code === 'offline') return 'No hay conexión. Revisa tu red e inténtalo de nuevo.';
    if (code === 'timeout') return 'La solicitud está tardando demasiado. Inténtalo de nuevo en unos segundos.';
    if (code === 'rate_limited') return 'Has hecho demasiados intentos. Espera un minuto e inténtalo de nuevo.';
    return 'Error al suscribirse. Escríbenos a davidportodiaz@gmail.com.';
  }

  async function postNewsletter(payload) {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      return { ok: false, code: 'offline' };
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const response = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal
      });
      if (response.ok) {
        const body = await response.json().catch(() => ({}));
        if (body && body.ok === true && body.state === 'pending_confirmation') {
          return { ok: true, state: 'pending_confirmation', code: 'pending_confirmation' };
        }
        return { ok: false, code: 'invalid_response' };
      }
      if (response.status === 400) return { ok: false, code: 'invalid_request' };
      if (response.status === 429) return { ok: false, code: 'rate_limited' };
      if (response.status >= 500) return { ok: false, code: 'server_error' };
      return { ok: false, code: 'request_failed' };
    } catch (error) {
      if (error && error.name === 'AbortError') return { ok: false, code: 'timeout' };
      return { ok: false, code: 'network_error' };
    } finally {
      clearTimeout(timer);
    }
  }

  function schedule(fn) {
    if (typeof scheduler !== 'undefined' && scheduler.postTask) {
      return scheduler.postTask(fn, { priority: 'user-blocking' });
    }
    return Promise.resolve().then(fn);
  }

  function bindForm(form) {
    if (!form || form.dataset.newsletterBound === 'true') return;
    const source = String(form.dataset.newsletterSource || '');
    if (!Object.hasOwn(PENDING_COPY, source)) return;
    form.dataset.newsletterBound = 'true';
    installHoneypot(form);

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      schedule(async () => {
        const email = form.querySelector('input[type="email"]');
        const consent = form.querySelector('input[name="consent"]');
        const status = form.querySelector('[role="status"]');
        const submit = form.querySelector('[type="submit"]');
        if (!submit || submit.dataset.submitting === 'true') return;
        if (STAGING_HOSTNAMES.has(window.location.hostname)) {
          if (status) status.textContent = STAGING_MESSAGE;
          return;
        }
        if (!email || !isValidEmail(email.value)) {
          if (status) status.textContent = 'Introduce un email válido.';
          email?.focus({ preventScroll: true });
          return;
        }
        if (!consent || !consent.checked) {
          if (status) status.textContent = 'Acepta la política de privacidad para continuar.';
          consent?.focus({ preventScroll: true });
          return;
        }

        if (status) status.textContent = '';
        const originalText = submit.textContent;
        submit.dataset.submitting = 'true';
        submit.disabled = true;
        submit.textContent = 'Enviando…';
        try {
          const result = await postNewsletter({
            email: email.value.trim(),
            source,
            website: honeypotValue(form)
          });
          if (!result.ok || result.state !== 'pending_confirmation') {
            throw new Error(result.code || 'request_failed');
          }
          form.innerHTML = '<p class="quiz-subscribe-ok">✓ ' + PENDING_COPY[source] + '</p>';
          if (typeof window._gcEvent === 'function') {
            window._gcEvent('newsletter-pending-' + source, 'Newsletter DOI pendiente: ' + source);
          }
        } catch (error) {
          if (status) status.textContent = errorMessage(error.message);
          delete submit.dataset.submitting;
          submit.disabled = false;
          submit.textContent = originalText;
        }
      });
    });
  }

  function init() {
    document.querySelectorAll('form[data-newsletter-source]').forEach(bindForm);
  }

  window.DPNewsletterGeneral = Object.freeze({
    bindForm,
    errorMessage,
    honeypotValue,
    installHoneypot,
    isValidEmail,
    postNewsletter
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
