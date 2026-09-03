// Email capture popup -- EXTRAIDO de script.js (H.1, 2026-08-23).
// Solo se necesita en /cuaderno/*, /recomendaciones/*, /universo/noveris/*
// y /clubes-de-lectura/*. Usa <dialog> nativo: el navegador gestiona la
// modalidad y el ciclo de Tab; este módulo solo decide apertura/cierre y
// devuelve el foco al elemento que lo tenía antes de abrir cuando procede.
//
// Triggers de producto: 70% de scroll, SIN temporizador de 30 s y exit-intent
// solo con (hover: hover) and (pointer: fine).
//
// Depende de scheduleTask/postNewsletter/isValidNewsletterEmail/
// installNewsletterHoneypot/honeypotValue/newsletterErrorMessage/IS_STAGING/
// STAGING_DISABLED_MESSAGE/_gcEvent, ya definidos por script.js, que se
// carga antes que este fichero.
(function () {
  const DISMISSED_KEY = "nl-popup-ts";
  const SUBSCRIBED_KEY = "nl-subscribed";
  const COOLDOWN = 7 * 24 * 60 * 60 * 1000;
  const path = window.location.pathname.replace(/\/index\.html$/, "/");

  // localStorage access throws (SecurityError) with storage blocked entirely
  // -- some privacy settings, some enterprise policies -- unlike every other
  // localStorage/sessionStorage call site in this codebase (assistant.js,
  // assistant-widget.js, surprise-me.js, v1-shell.js), this one wasn't
  // guarded: confirmed live, it threw an uncaught page error and silently
  // disabled the popup for the rest of the session. Same fix as those.
  function safeGet(key) { try { return localStorage.getItem(key); } catch { return null; } }
  function safeSet(key, value) { try { localStorage.setItem(key, value); } catch {} }

  if (safeGet(SUBSCRIBED_KEY) === "1") return;
  const ts = safeGet(DISMISSED_KEY);
  if (ts && Date.now() - Number(ts) < COOLDOWN) return;

  function popupCopy() {
    if (path.startsWith("/universo/noveris/") || path.startsWith("/clubes-de-lectura/")) {
      return {
        eyebrow: "Primeros lectores de Noveris",
        title: "Sigue el universo de Noveris.",
        body: "Novedades sobre el universo de Noveris y avisos de nuevas firmas o lecturas. Un email cuando haya algo que valga la pena.",
        cta: "Suscribirme",
        okTitle: "Revisa tu correo",
        okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción."
      };
    }
    return {
      eyebrow: "Novedades de David Porto Díaz",
      title: "Sigue los próximos libros y artículos.",
      body: "Nuevas publicaciones, artículos, firmas y recursos para lectores. Solo cuando haya algo que contar.",
      cta: "Suscribirme",
      okTitle: "Revisa tu correo",
      okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción."
    };
  }

  let shown = false;
  let dialog = null;
  let returnFocus = null;

  function restoreFocus() {
    const target = returnFocus;
    returnFocus = null;
    if (target instanceof HTMLElement && target.isConnected) {
      target.focus({ preventScroll: true });
    }
  }

  function dismiss() {
    safeSet(DISMISSED_KEY, String(Date.now()));
    if (dialog?.open) dialog.close();
  }

  // El <dialog> nativo hace inerte el resto del documento, pero no garantiza
  // el ciclo de Tab en todos los motores: tras el último elemento, un Tab
  // puede mandar el foco a <body> antes de reciclar al primero. Trap manual.
  function trapTabCycle(d) {
    d.addEventListener("keydown", (event) => {
      if (event.key !== "Tab") return;
      const focusable = Array.from(
        d.querySelectorAll('a[href], button:not([disabled]), input:not([disabled])')
      ).filter((el) => el.offsetParent !== null);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });
  }

  function buildDialog(copy) {
    const d = document.createElement("dialog");
    d.id = "nl-popup-dialog";
    d.setAttribute("aria-labelledby", "nl-popup-title");
    d.setAttribute("aria-describedby", "nl-popup-body");
    d.innerHTML =
      '<div id="nl-popup-panel">' +
      '<button id="nl-popup-close" type="button" aria-label="Cerrar">&times;</button>' +
      '<p class="eyebrow">' + copy.eyebrow + '</p>' +
      '<h2 id="nl-popup-title">' + copy.title + '</h2>' +
      '<p id="nl-popup-body">' + copy.body + '</p>' +
      '<form id="nl-popup-form" novalidate>' +
      '<label class="sr-only" for="nl-popup-email">Correo electrónico</label>' +
      '<input type="email" id="nl-popup-email" name="email" placeholder="tu@email.com" autocomplete="email" required />' +
      '<p class="nl-popup-consent">Al enviar tu email, aceptas la <a href="/privacidad.html">política de privacidad</a>.</p>' +
      '<button type="submit" class="button primary" id="nl-popup-submit">' + copy.cta + '</button>' +
      '<div aria-hidden="true" inert style="position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0;"><input type="text" name="website" autocomplete="off" tabindex="-1" /></div>' +
      '<p id="nl-popup-status" role="status" aria-live="polite"></p>' +
      '</form>' +
      '<button id="nl-popup-skip" type="button">No, gracias</button>' +
      '</div>';

    d.querySelector("#nl-popup-close").addEventListener("click", dismiss);
    d.querySelector("#nl-popup-skip").addEventListener("click", dismiss);
    d.addEventListener("click", (event) => {
      if (event.target === d) dismiss();
    });
    d.addEventListener("cancel", (event) => {
      event.preventDefault();
      dismiss();
    });
    d.addEventListener("close", () => {
      restoreFocus();
      d.remove();
      if (dialog === d) dialog = null;
    }, { once: true });

    installNewsletterHoneypot(d.querySelector("#nl-popup-form"));
    d.querySelector("#nl-popup-form").addEventListener("submit", function (event) {
      event.preventDefault();
      scheduleTask(async function () {
        const emailEl = d.querySelector("#nl-popup-email");
        const statusEl = d.querySelector("#nl-popup-status");
        const submitBtn = d.querySelector("#nl-popup-submit");
        if (!emailEl || !statusEl || !submitBtn) return;
        if (submitBtn.dataset.submitting === "true") return;
        if (IS_STAGING) { statusEl.textContent = STAGING_DISABLED_MESSAGE; return; }
        if (!isValidNewsletterEmail(emailEl.value)) { statusEl.textContent = "Introduce un email válido."; return; }
        statusEl.textContent = "";
        submitBtn.dataset.submitting = "true";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
          const result = await postNewsletter({
            email: emailEl.value.trim(),
            source: "popup",
            website: honeypotValue(d.querySelector("#nl-popup-form"))
          });
          const panel = d.querySelector("#nl-popup-panel");
          if (result.ok && result.state === "pending_confirmation") {
            panel.innerHTML = '<p class="nl-popup-result-title">' + copy.okTitle + '</p><p class="nl-popup-result-body">' + copy.okBody + '</p>';
            panel.tabIndex = -1;
            panel.focus({ preventScroll: true });
            _gcEvent("newsletter-pending-popup", "Newsletter DOI pendiente: popup");
            setTimeout(dismiss, 5000);
          } else {
            throw new Error(result.code || "request_failed");
          }
        } catch (err) {
          statusEl.textContent = newsletterErrorMessage(err.message);
          delete submitBtn.dataset.submitting;
          submitBtn.disabled = false;
          submitBtn.textContent = copy.cta;
        }
      }, "user-blocking");
    });

    trapTabCycle(d);
    return d;
  }

  function showPopup() {
    if (shown || dialog?.open) return false;
    // No apilar un segundo modal sobre Explorar, compra u otro <dialog> nativo.
    if (document.querySelector("dialog[open]")) return false;

    const active = document.activeElement;
    returnFocus = active instanceof HTMLElement && active !== document.body && active !== document.documentElement
      ? active
      : null;

    const copy = popupCopy();
    dialog = buildDialog(copy);
    document.body.appendChild(dialog);
    try {
      dialog.showModal();
    } catch {
      dialog.remove();
      dialog = null;
      returnFocus = null;
      return false;
    }

    shown = true;
    safeSet(DISMISSED_KEY, String(Date.now()));
    dialog.querySelector("#nl-popup-email")?.focus({ preventScroll: true });
    return true;
  }

  function onScroll() {
    const ratio = window.scrollY / Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    if (ratio >= 0.7 && showPopup()) window.removeEventListener("scroll", onScroll);
  }
  window.addEventListener("scroll", onScroll, { passive: true });

  if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    function onLeave(event) {
      if (event.clientY <= 0 && showPopup()) document.removeEventListener("mouseleave", onLeave);
    }
    document.addEventListener("mouseleave", onLeave);
  }

  // Deliberadamente no hay trigger temporal de 30 s.
})();
