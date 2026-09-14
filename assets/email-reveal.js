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

    return link;
  };

  // One interaction, not two: a control that says "Contactar por email"
  // should open the mail client on the first click, not reveal-then-wait-
  // for-a-second-click. Navigating here, inside the same click/keydown
  // handler that reveal() ran in, still counts as the direct result of a
  // user gesture -- it is not a background redirect. The real <a href="
  // mailto:...">  stays in the DOM afterward exactly as before, so right-
  // click "copy email address", re-reading it, or a screen reader
  // revisiting the element all keep working.
  const revealAndOpen = (trigger) => {
    const link = reveal(trigger);
    if (link) window.location.href = link.href;
  };

  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-email-reveal]');
    if (!trigger) return;
    event.preventDefault();
    revealAndOpen(trigger);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const trigger = event.target.closest('[data-email-reveal]');
    if (!trigger) return;
    // Native anchors already fire click for Enter. Space does not, so support
    // it explicitly for link-shaped controls without creating a custom widget.
    if (event.key === ' ') {
      event.preventDefault();
      revealAndOpen(trigger);
    }
  });

  // Printing (e.g. a journalist keeping a paper copy of the press page) never
  // fires a click, so without this the printed page would show only the
  // trigger's label and never the address -- a real functional loss for the
  // legitimate use case this exists to protect, not just a scraper. A print
  // command is not something a bulk static-scraping bot issues, so revealing
  // here does not reopen the exposure this file exists to close.
  //
  // afterprint puts back the ORIGINAL trigger for exactly the elements this
  // pass revealed (each one cloned before reveal() ran), so cancelling the
  // print dialog does not leave the address sitting in the DOM indefinitely.
  // querySelectorAll('[data-email-reveal]') only ever matches un-revealed
  // triggers to begin with (reveal() replaces the element and the
  // replacement carries no data-email-reveal attribute), so a trigger a
  // visitor already revealed by clicking before printing is untouched here
  // and correctly stays revealed after the print dialog closes.
  let printRevealState = null;
  window.addEventListener('beforeprint', () => {
    printRevealState = [...document.querySelectorAll('[data-email-reveal]')].map((trigger) => {
      const original = trigger.cloneNode(true);
      const link = reveal(trigger);
      return link ? { original, link } : null;
    }).filter(Boolean);
  });
  window.addEventListener('afterprint', () => {
    if (!printRevealState) return;
    for (const { original, link } of printRevealState) {
      if (link.isConnected) link.replaceWith(original);
    }
    printRevealState = null;
  });
})();
