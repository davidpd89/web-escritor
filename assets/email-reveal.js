/* Accessible, local-only email reveal for public contact surfaces.
 *
 * Goal: keep the contact address easy for a real person to reach while
 * removing the literal address and mailto: target from static HTML, where
 * low-effort harvesters can collect it without executing/using the page.
 *
 * This is intentionally NOT presented as bot-proof security. A determined
 * browser-automation bot or a person can still reveal the address. The layer
 * raises the cost of bulk static scraping without CAPTCHA, cookies, tracking,
 * network calls or a third-party dependency.
 */
(() => {
  'use strict';

  // Do not replace this with a plaintext address in HTML/data attributes.
  // Keeping the address out of the document source is the useful part of the
  // protection. The character-code representation is obfuscation, not a secret.
  const AUTHOR_EMAIL_CODES = [
    100, 97, 118, 105, 100, 112, 111, 114, 116, 111, 100, 105, 97, 122,
    64, 103, 109, 97, 105, 108, 46, 99, 111, 109,
  ];

  const emailAddress = () => String.fromCharCode(...AUTHOR_EMAIL_CODES);

  const buildMailto = (trigger) => {
    const params = new URLSearchParams();
    const subject = trigger.dataset.emailSubject?.trim();
    const body = trigger.dataset.emailBody?.trim();
    if (subject) params.set('subject', subject);
    if (body) params.set('body', body);
    const query = params.toString();
    return `mailto:${emailAddress()}${query ? `?${query}` : ''}`;
  };

  const reveal = (trigger) => {
    if (trigger.dataset.emailRevealed === 'true') return;

    const link = document.createElement('a');
    link.className = trigger.className;
    link.href = buildMailto(trigger);
    link.dataset.emailRevealed = 'true';

    const after = trigger.dataset.emailLabelAfter?.trim();
    link.textContent = after || emailAddress();

    // Keep a useful accessible name even when the visual label is an action.
    link.setAttribute(
      'aria-label',
      after ? `${after}: ${emailAddress()}` : `Enviar correo a ${emailAddress()}`,
    );

    // Preserve ids used as styling/anchor hooks, but do not copy arbitrary
    // attributes that could accidentally reintroduce data into the mailto.
    if (trigger.id) link.id = trigger.id;

    trigger.replaceWith(link);
    link.focus({ preventScroll: true });

    const statusId = trigger.dataset.emailStatus;
    if (statusId) {
      const status = document.getElementById(statusId);
      if (status) status.textContent = `Correo mostrado: ${emailAddress()}`;
    }
  };

  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-email-reveal]');
    if (!trigger) return;
    event.preventDefault();
    reveal(trigger);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const trigger = event.target.closest('[data-email-reveal]');
    if (!trigger) return;
    // Native anchors already fire click for Enter. Space does not, so support
    // it explicitly for link-shaped controls without creating a custom widget.
    if (event.key === ' ') {
      event.preventDefault();
      reveal(trigger);
    }
  });
})();
