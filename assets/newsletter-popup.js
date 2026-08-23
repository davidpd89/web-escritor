// Email capture popup -- EXTRAIDO de script.js (H.1, 2026-08-23).
// Solo se necesita en /cuaderno/*, /recomendaciones/*, /universo/noveris/*
// y /clubes-de-lectura/* (antes se descargaba/ejecutaba en TODAS las
// paginas y se autoexcluia via allowedPath() en runtime). Su CSS vive
// ahora en assets/newsletter-popup.css (enlazada desde el <head> de cada
// pagina que carga este script) en vez de inyectarse con
// style.textContent -- ver criterios de aceptacion de H.1.
//
// Triggers alineados con la spec del dossier (no reintroducir los
// antiguos): 70% de scroll (no 60%), sin temporizador de 30s, exit-intent
// solo en dispositivos con hover real + puntero fino.
//
// Depende de scheduleTask/postNewsletter/isValidNewsletterEmail/
// newsletterErrorMessage/IS_STAGING/STAGING_DISABLED_MESSAGE/_gcEvent, ya
// globales (definidos por script.js, cargado antes que este fichero).
(function () {
  const DISMISSED_KEY = "nl-popup-ts";
  const SUBSCRIBED_KEY = "nl-subscribed";
  const COOLDOWN = 7 * 24 * 60 * 60 * 1000;
  const path = window.location.pathname.replace(/\/index\.html$/, "/");

  if (localStorage.getItem(SUBSCRIBED_KEY) === "1") return;
  const ts = localStorage.getItem(DISMISSED_KEY);
  if (ts && Date.now() - Number(ts) < COOLDOWN) return;

  // Copy varies by context: the Noveris/Samuel-specific pitch only makes
  // sense on pages actually about that book. Elsewhere it stays generic.
  function popupCopy() {
    if (path.startsWith("/universo/noveris/") || path.startsWith("/clubes-de-lectura/")) {
      // BREVO AUTOMATION VERIFICATION REQUIRED (2026-08-20): no confirmed
      // Brevo automation in this repo actually emails a map/chapter PDF on
      // signup, so this copy no longer promises specific automatic content
      // delivery — only what a plain list subscription genuinely does.
      return {
        eyebrow: "Primeros lectores de Noveris",
        title: "Sigue el universo de Noveris.",
        body: "Novedades sobre el universo de Noveris y avisos de nuevas firmas o lecturas. Un email cuando haya algo que valga la pena.",
        cta: "Suscribirme",
        okTitle: "✓ ¡Apuntado!",
        okBody: "Recibirás las novedades de David Porto Díaz sobre el universo de Noveris.",
        dupeTitle: "✓ Ya estás suscrito.",
        dupeBody: "¡Gracias por seguir a David Porto Díaz!"
      };
    }
    return {
      eyebrow: "Novedades de David Porto Díaz",
      title: "Sigue los próximos libros y artículos.",
      body: "Nuevas publicaciones, artículos, firmas y recursos para lectores. Solo cuando haya algo que contar.",
      cta: "Suscribirme",
      okTitle: "✓ ¡Apuntado!",
      okBody: "Recibirás las novedades de David Porto Díaz.",
      dupeTitle: "✓ Ya estás suscrito.",
      dupeBody: "¡Gracias por seguir a David Porto Díaz!"
    };
  }

  let shown = false;

  function dismiss() {
    localStorage.setItem(DISMISSED_KEY, String(Date.now()));
    const el = document.getElementById("nl-popup-overlay");
    if (!el) return;
    el.style.transition = "opacity 0.25s ease";
    el.style.opacity = "0";
    setTimeout(() => { if (el.parentNode) el.parentNode.removeChild(el); }, 260);
  }

  function showPopup() {
    if (shown || document.getElementById("nl-popup-overlay")) return;
    shown = true;
    localStorage.setItem(DISMISSED_KEY, String(Date.now()));
    const copy = popupCopy();

    const overlay = document.createElement("div");
    overlay.id = "nl-popup-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-labelledby", "nl-popup-title");
    overlay.innerHTML =
      '<div id="nl-popup-panel">' +
      '<button id="nl-popup-close" type="button" aria-label="Cerrar">&times;</button>' +
      '<p class="eyebrow">' + copy.eyebrow + '</p>' +
      '<h2 id="nl-popup-title">' + copy.title + '</h2>' +
      '<p id="nl-popup-body">' + copy.body + '</p>' +
      '<form id="nl-popup-form" novalidate>' +
      '<input type="email" id="nl-popup-email" name="email" placeholder="tu@email.com" autocomplete="email" required />' +
      '<button type="submit" class="button primary" id="nl-popup-submit">' + copy.cta + '</button>' +
      '<label id="nl-popup-gdpr-row"><input type="checkbox" id="nl-popup-gdpr" required />Acepto recibir novedades del autor. <a href="/privacidad.html" target="_blank" rel="noopener">Privacidad</a>.</label>' +
      '<p id="nl-popup-status" role="status" aria-live="polite"></p>' +
      '</form>' +
      '<button id="nl-popup-skip" type="button">No, gracias</button>' +
      '</div>';
    document.body.appendChild(overlay);

    // Focus first field
    scheduleTask(() => { const f = document.getElementById("nl-popup-email"); if (f) f.focus(); }, "user-visible");

    // Close handlers
    document.getElementById("nl-popup-close").addEventListener("click", dismiss);
    document.getElementById("nl-popup-skip").addEventListener("click", dismiss);
    overlay.addEventListener("click", function (e) { if (e.target === overlay) dismiss(); });
    document.addEventListener("keydown", function escClose(e) {
      if (e.key === "Escape") { dismiss(); document.removeEventListener("keydown", escClose); }
    });

    // Form submit
    document.getElementById("nl-popup-form").addEventListener("submit", function (e) {
      e.preventDefault();
      scheduleTask(async function () {
        const emailEl = document.getElementById("nl-popup-email");
        const gdprEl = document.getElementById("nl-popup-gdpr");
        const statusEl = document.getElementById("nl-popup-status");
        const submitBtn = document.getElementById("nl-popup-submit");
        if (IS_STAGING) { statusEl.textContent = STAGING_DISABLED_MESSAGE; return; }
        if (!isValidNewsletterEmail(emailEl.value)) { statusEl.textContent = "Introduce un email válido."; return; }
        if (!gdprEl.checked) { statusEl.textContent = "Acepta la política de privacidad para continuar."; return; }
        statusEl.textContent = "";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
          const result = await postNewsletter({ email: emailEl.value.trim(), source: "popup" });
          if (result.ok && !result.duplicate) {
            localStorage.setItem(SUBSCRIBED_KEY, "1");
            const panel = document.getElementById("nl-popup-panel");
            panel.innerHTML = '<p class="nl-popup-result-title">' + copy.okTitle + '</p><p class="nl-popup-result-body">' + copy.okBody + '</p>';
            _gcEvent("newsletter-popup", "Newsletter: popup");
            setTimeout(dismiss, 3200);
          } else if (result.ok && result.duplicate) {
            localStorage.setItem(SUBSCRIBED_KEY, "1");
            const panel = document.getElementById("nl-popup-panel");
            panel.innerHTML = '<p class="nl-popup-result-title">' + copy.dupeTitle + '</p><p class="nl-popup-result-body">' + copy.dupeBody + '</p>';
            setTimeout(dismiss, 3200);
          } else {
            throw new Error(result.code || "request_failed");
          }
        } catch (err) {
          statusEl.textContent = newsletterErrorMessage(err.message);
          submitBtn.disabled = false;
          submitBtn.textContent = copy.cta;
        }
      }, "user-blocking");
    });
  }

  // Trigger 1: 70% scroll depth (alineado con la spec del dossier, no el
  // 60% legacy).
  window.addEventListener("scroll", function onScroll() {
    const ratio = window.scrollY / Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    if (ratio >= 0.7) { window.removeEventListener("scroll", onScroll); showPopup(); }
  }, { passive: true });

  // Trigger 2: exit-intent, solo en dispositivos con hover real + puntero
  // fino -- un scroll/touch que el navegador interprete como mouseleave en
  // movil no debe disparar el popup.
  if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    document.addEventListener("mouseleave", function onLeave(e) {
      if (e.clientY <= 0) { document.removeEventListener("mouseleave", onLeave); showPopup(); }
    });
  }

  // NO hay Trigger 3 (temporizador de 30s): retirado por spec, no
  // reintroducir.
})();
