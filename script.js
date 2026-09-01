// scheduler.postTask() shim — default to background work; opt into user-blocking only for critical UI.
function scheduleTask(fn, priority = "background") {
  if (typeof scheduler !== "undefined" && scheduler.postTask) {
    return scheduler.postTask(fn, { priority });
  }
  return Promise.resolve().then(fn);
}

// Client contract (2026-08-23): only { email, source, result?, website? } is ever
// sent to the Worker. `website` is a honeypot and is never forwarded by the Worker.
// listIds/attributes/templateId/redirectionUrl are never client-controlled —
// the Worker validates `source` against its own server-side whitelist and
// builds the Brevo attributes itself. See cloudflare-worker-subscribe.js.
// The `source` values used below (home, fragmento, manecillas, cuaderno,
// popup, quiz, lectores-beta) must match the Worker's SOURCE_MAP keys exactly.
const NEWSLETTER_CONFIG = {
  endpoint: "https://subscribe.davidpd89.workers.dev"
};
const NEWSLETTER_TIMEOUT_MS = 12000;

// Same shape as the Worker's server-side check (cloudflare-worker-subscribe.js)
// so obviously-invalid input never leaves the browser, not just the empty case.
const NEWSLETTER_EMAIL_RE = /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@]{2,}$/;
function isValidNewsletterEmail(value) {
  const normalized = String(value || "").trim();
  return normalized.length <= 254 && NEWSLETTER_EMAIL_RE.test(normalized);
}

function honeypotValue(form) {
  const field = form?.querySelector('input[name="website"]');
  return field ? String(field.value || "").trim() : "";
}

function installNewsletterHoneypot(form) {
  if (!form || form.querySelector('input[name="website"]')) return;
  const wrapper = document.createElement("div");
  wrapper.setAttribute("aria-hidden", "true");
  wrapper.setAttribute("inert", "");
  wrapper.style.cssText = "position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0;";
  const field = document.createElement("input");
  field.type = "text";
  field.name = "website";
  field.autocomplete = "off";
  field.tabIndex = -1;
  wrapper.appendChild(field);
  form.appendChild(wrapper);
}

function newsletterErrorMessage(code) {
  if (code === "offline") return "No hay conexión. Revisa tu red e inténtalo de nuevo.";
  if (code === "timeout") return "La solicitud está tardando demasiado. Inténtalo de nuevo en unos segundos.";
  if (code === "rate_limited") return "Has hecho demasiados intentos. Espera un minuto e inténtalo de nuevo.";
  return "Error al suscribirse. Escríbenos a davidportodiaz@gmail.com.";
}

async function postNewsletter(payload) {
  if (window.DPNewsletterGeneral?.postNewsletter) {
    return window.DPNewsletterGeneral.postNewsletter(payload);
  }
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    return { ok: false, code: "offline" };
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), NEWSLETTER_TIMEOUT_MS);
  try {
    const res = await fetch(NEWSLETTER_CONFIG.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal
    });

    if (res.ok) {
      const body = await res.json().catch(() => ({}));
      if (body && body.ok === true && body.state === "pending_confirmation") {
        return { ok: true, state: "pending_confirmation", code: "pending_confirmation" };
      }
      return { ok: false, code: "invalid_response" };
    }

    if (res.status === 400) return { ok: false, code: "invalid_request" };

    if (res.status === 429) return { ok: false, code: "rate_limited" };
    if (res.status >= 500) return { ok: false, code: "server_error" };
    return { ok: false, code: "request_failed" };
  } catch (err) {
    if (err && err.name === "AbortError") return { ok: false, code: "timeout" };
    return { ok: false, code: "network_error" };
  } finally {
    clearTimeout(timer);
  }
}

// Staging must never create real Brevo contacts. This is the Cloudflare
// Pages preview hostname for this project (confirmed working
// 2026-08-20) — production is davidportodiaz.com, which is never in
// this set. Point 23 of the 2026-08-20 corrective audit.
const STAGING_HOSTNAMES = new Set(["david-porto-preview.davidpd89.workers.dev"]);
const IS_STAGING = STAGING_HOSTNAMES.has(window.location.hostname);
const STAGING_DISABLED_MESSAGE = "Formulario desactivado en el entorno de pruebas.";
// Clarity analytics is intentionally disabled. Keep the project id out of runtime until it is useful again.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    scheduleTask(() => {
      navigator.serviceWorker.register("/service-worker.js").catch(() => {});
    }, "background");
  });
}

// Email obfuscation — build mailto: links from data-n + data-d at runtime.
// Bots that don't execute JS see href="#" and no email in the href.
document.querySelectorAll('[data-n][data-d]').forEach(el => {
  const addr = el.dataset.n + '@' + el.dataset.d;
  let href = 'mailto:' + addr;
  if (el.dataset.s) href += '?subject=' + encodeURIComponent(el.dataset.s);
  el.href = href;
  el.removeAttribute('target');
  el.removeAttribute('rel');
});

function syncHashScroll() {
  if (!window.location.hash || window.location.hash === "#") return;
  // decodeURIComponent lanza URIError con un % mal formado en la URL
  // (#%E0%A4%A, por ejemplo). Es una URL que cualquiera puede teclear o que
  // llega desde un enlace roto, y hasta ahora tiraba un error no capturado en
  // *todas* las paginas que cargan este script, no solo aqui. Un hash que no
  // se puede decodificar simplemente no apunta a nada: no hay a donde
  // desplazarse, asi que salir es la respuesta correcta.
  let targetId;
  try {
    targetId = decodeURIComponent(window.location.hash.slice(1));
  } catch {
    return;
  }
  const target = document.getElementById(targetId);
  if (!target) return;
  target.scrollIntoView({ block: "start" });
}

window.addEventListener("load", () => {
  scheduleTask(() => {
    syncHashScroll();
    window.setTimeout(syncHashScroll, 450);
  }, "user-visible");
});

// Thumb-friendly mobile navigation. Injected once so every page gets the same bottom actions.
// Scoped off legal/policy pages: a promotional "Novedad" shortcut doesn't
// belong on a privacy policy or legal notice page (reviewed 2026-08-20).
(function () {
  if (document.querySelector(".mobile-bottom-nav")) return;
  // V1 editorial shell pages reach every primary route via direct header
  // links + Explorar; MIGRATION-MATRIX.md marks the legacy bottom nav
  // "FUERA DE HOME" for those pages, not just excluded by path.
  if (document.documentElement.classList.contains("v1")) return;
  const NO_BOTTOM_NAV_PATHS = new Set(["/privacidad.html", "/aviso-legal.html"]);
  if (NO_BOTTOM_NAV_PATHS.has(window.location.pathname)) return;

  const items = [
    { href: "/", label: "Inicio", icon: "⌂" },
    { href: "/las-manecillas-del-recuerdo/", label: "Novedad", icon: "◷" },
    { href: "/libros/", label: "Libros", icon: "◇" },
    { href: "/cuaderno/", label: "Cuaderno", icon: "✎" },
    { href: "/#contacto", label: "Contacto", icon: "@" }
  ];

  const currentPath = window.location.pathname.replace(/\/index\.html$/, "/");
  const nav = document.createElement("nav");
  nav.className = "mobile-bottom-nav";
  nav.setAttribute("aria-label", "Navegación móvil principal");

  items.forEach((item) => {
    const link = document.createElement("a");
    link.href = item.href;
    link.innerHTML = `<span aria-hidden="true">${item.icon}</span><small>${item.label}</small>`;
    const itemPath = new URL(item.href, window.location.origin).pathname;
    if (currentPath === itemPath || (itemPath !== "/" && currentPath.startsWith(itemPath))) {
      link.setAttribute("aria-current", "page");
    }
    nav.appendChild(link);
  });

  document.body.appendChild(nav);
})();

// Back-to-top button — opt-in only (data-back-to-top on <body>), not
// injected on every page. Long-form reading pages opt in explicitly, same
// contract as data-reading-progress; utility/tool/legal pages don't need it.
(function () {
  if (!document.body.hasAttribute("data-back-to-top")) return;
  const btn = document.createElement("button");
  btn.className = "back-to-top";
  btn.setAttribute("aria-label", "Volver al inicio de la página");
  btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true"><path d="M9 14V4M4 9l5-5 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  document.body.appendChild(btn);

  // Show/hide with passive scroll listener (better INP on mobile)
  let scheduled = false;
  window.addEventListener("scroll", () => {
    if (scheduled) return;
    scheduled = true;
    scheduleTask(() => {
      btn.classList.toggle("is-visible", window.scrollY > 500);
      scheduled = false;
    }, "background");
  }, { passive: true });

  btn.addEventListener("click", () => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
  });
})();

// Copy to clipboard (press kit bios)
document.querySelectorAll(".copy-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    scheduleTask(() => {
      const targetEl = document.getElementById(btn.dataset.copyTarget);
      if (!targetEl) return;
      const text = targetEl.textContent.trim();
      const original = btn.textContent;

      const finish = () => {
        btn.textContent = "✓ Copiado";
        setTimeout(() => { btn.textContent = original; }, 2200);
      };

      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(text).then(finish).catch(() => fallbackCopy(text, finish));
      } else {
        fallbackCopy(text, finish);
      }
    }, "user-visible");
  });
});

function fallbackCopy(text, done) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.cssText = "position:fixed;top:0;left:0;opacity:0";
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand("copy"); done(); } catch (_) {}
  document.body.removeChild(ta);
}

// Reading progress bar — opt-in only (data-reading-progress on <body>),
// not injected on every page. Long-form reading pages (articles,
// fragments) opt in explicitly; utility/tool/legal pages don't need it.
(function () {
  if (!document.body.hasAttribute("data-reading-progress")) return;
  const bar = document.createElement("div");
  bar.className = "reading-progress";
  bar.setAttribute("role", "progressbar");
  bar.setAttribute("aria-hidden", "true");
  document.body.prepend(bar);

  let scheduled = false;
  window.addEventListener("scroll", () => {
    if (scheduled) return;
    scheduled = true;
    scheduleTask(() => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = docHeight > 0 ? (scrollTop / docHeight * 100) + "%" : "0%";
      scheduled = false;
    }, "background");
  }, { passive: true });
})();

// Quiz "¿Qué habitante de Noveris serías?" -- ELIMINADO (H.1, 2026-08-23):
// id="quiz-noveris-app" no aparecia en ningun HTML real del repo (grep
// completo del sitio), y tests/test-samuel-ecosystem-parity.py:89 prohibe
// explicitamente ese id porque el quiz real vigente es otro: id=
// "samuel-quiz-app" + assets/samuel-quiz.js, cargado solo en
// libros/samuel-entre-mundos/index.html. Este bloque (~220 lineas) nunca
// se ejecutaba en produccion. PR55 lo habia actualizado al patron DOI
// (installNewsletterHoneypot + pending_confirmation) antes de saberlo
// muerto; si "quiz-noveris-app" vuelve a activarse alguna vez, replicar
// ese patron DOI, no el _SUCCESS_COPY antiguo.

// Generic newsletter forms (home, fragmento, manecillas pages)
(function () {
  // Contextual success copy per source. BREVO AUTOMATION VERIFICATION
  // REQUIRED: there is no confirmed Brevo automation in this repo that
  // actually emails the Samuel entre mundos chapter (or any other content)
  // on signup — subscribing only adds the contact to a list with a SOURCE
  // attribute. Until such an automation is verified and documented, copy
  // must not promise specific automatic content delivery (2026-08-20).
  // Manecillas keeps its own promise because that one is just "I'll notify
  // you" (a real, simple thing this list can do), not a content delivery.
  const NEWSLETTER_PENDING_COPY = {
    home: "Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.",
    fragmento: "Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.",
    manecillas: "Revisa tu correo y confirma la suscripción. Después te avisaré cuando Las manecillas del recuerdo esté disponible.",
    cuaderno: "Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.",
    explore: "Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz."
  };

  async function submitNewsletter(formId, emailId, gdprId, statusId, sourceLabel) {
    const form = document.getElementById(formId);
    if (!form) return;
    if (form.dataset.newsletterBound === "true") return;
    form.dataset.newsletterBound = "true";
    installNewsletterHoneypot(form);
    const pendingBody = NEWSLETTER_PENDING_COPY[sourceLabel] || "Revisa tu correo y confirma la suscripción para completarla.";
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      scheduleTask(async () => {
        const emailEl = document.getElementById(emailId);
        const gdprEl = document.getElementById(gdprId);
        const statusEl = document.getElementById(statusId);
        const submitBtn = form.querySelector("[type=submit]");
        if (submitBtn.dataset.submitting === "true") return;
        if (IS_STAGING) {
          if (statusEl) statusEl.textContent = STAGING_DISABLED_MESSAGE;
          return;
        }
        if (!emailEl || !isValidNewsletterEmail(emailEl.value)) {
          if (statusEl) statusEl.textContent = "Introduce un email válido.";
          return;
        }
        if (!gdprEl || !gdprEl.checked) {
          if (statusEl) statusEl.textContent = "Acepta la política de privacidad para continuar.";
          gdprEl?.focus({ preventScroll: true });
          return;
        }
        if (statusEl) statusEl.textContent = "";
        submitBtn.dataset.submitting = "true";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
          const result = await postNewsletter({
            email: emailEl.value.trim(),
            source: sourceLabel,
            website: honeypotValue(form)
          });
          if (result.ok && result.state === "pending_confirmation") {
            form.innerHTML = '<p class="quiz-subscribe-ok">✓ ' + pendingBody + '</p>';
            _gcEvent("newsletter-pending-" + sourceLabel, "Newsletter DOI pendiente: " + sourceLabel);
          } else {
            throw new Error(result.code || "request_failed");
          }
        } catch (err) {
          if (statusEl) statusEl.textContent = newsletterErrorMessage(err.message);
          delete submitBtn.dataset.submitting;
          submitBtn.disabled = false;
          submitBtn.textContent = "Suscribirme";
        }
      }, "user-blocking");
    });
  }
  submitNewsletter("newsletter-form-home",       "nl-email-home",       "nl-gdpr-home",       "nl-status-home",       "home");
  submitNewsletter("newsletter-form-fragmento",  "nl-email-fragmento",  "nl-gdpr-fragmento",  "nl-status-fragmento",  "fragmento");
  submitNewsletter("newsletter-form-manecillas", "nl-email-manecillas", "nl-gdpr-manecillas", "nl-status-manecillas", "manecillas");
  submitNewsletter("newsletter-form-home-manecillas-card", "home-manecillas-card-email", "home-manecillas-card-gdpr", "home-manecillas-card-status", "manecillas");
  document.addEventListener("dp:home-editorial-ready", () => {
    submitNewsletter("newsletter-form-home-manecillas-card", "home-manecillas-card-email", "home-manecillas-card-gdpr", "home-manecillas-card-status", "manecillas");
  }, { once: true });
  submitNewsletter("newsletter-form-cuaderno",   "nl-email-cuaderno",   "nl-gdpr-cuaderno",   "nl-status-cuaderno",   "cuaderno");
  submitNewsletter("newsletter-form-explore",    "nl-email-explore",    "nl-gdpr-explore",    "nl-status-explore",    "explore");
  // Lectores beta (N.1, 2026-08-23): mismo mecanismo de envio, pero fuente,
  // lista de Brevo y consentimiento propios -- ver /lectores-beta/ y
  // cloudflare-worker-subscribe.js (BREVO_BETA_LIST_ID). El copy de exito no
  // reutiliza NEWSLETTER_SUCCESS_COPY porque no es "recibir novedades del
  // autor", es la confirmacion del programa de lectores beta.
  (function () {
    const form = document.getElementById("lectores-beta-form");
    if (!form) return;
    installNewsletterHoneypot(form);
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      scheduleTask(async () => {
        const emailEl = document.getElementById("lectores-beta-email");
        const gdprEl = document.getElementById("lectores-beta-gdpr");
        const statusEl = document.getElementById("lectores-beta-status");
        const submitBtn = form.querySelector("[type=submit]");
        if (submitBtn.dataset.submitting === "true") return;
        if (IS_STAGING) {
          if (statusEl) statusEl.textContent = STAGING_DISABLED_MESSAGE;
          return;
        }
        if (!emailEl || !isValidNewsletterEmail(emailEl.value) || !gdprEl || !gdprEl.checked) {
          if (statusEl) statusEl.textContent = gdprEl && !gdprEl.checked
            ? "Acepta el consentimiento del programa de lectores beta para continuar."
            : "Introduce un email válido.";
          return;
        }
        if (statusEl) statusEl.textContent = "";
        submitBtn.dataset.submitting = "true";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
          const result = await postNewsletter({
            email: emailEl.value.trim(),
            source: "lectores-beta",
            website: honeypotValue(form)
          });
          if (result.ok && result.state === "pending_confirmation") {
            form.innerHTML = '<p class="quiz-subscribe-ok">✓ Revisa tu correo y confirma la suscripción. Te escribiré cuando tenga material listo para lectores beta.</p>';
            _gcEvent("newsletter-pending-lectores-beta", "Newsletter DOI pendiente: lectores beta");
          } else {
            throw new Error(result.code || "request_failed");
          }
        } catch (err) {
          if (statusEl) statusEl.textContent = newsletterErrorMessage(err.message);
          delete submitBtn.dataset.submitting;
          submitBtn.disabled = false;
          submitBtn.textContent = "Quiero apuntarme";
        }
      }, "user-blocking");
    });
  })();
})();

// Modo lectura desactivado temporalmente: limpia estados antiguos guardados en el navegador.
(function () {
  document.documentElement.classList.remove("modo-samuel");
  try { localStorage.removeItem("modo-samuel"); } catch {}
})();

// FAQ accordion — closes siblings when one opens
document.querySelectorAll(".faq-question").forEach((btn) => {
  if (btn.closest("details")) return;
  btn.addEventListener("click", () => {
    scheduleTask(() => {
      const item = btn.closest(".faq-item");
      if (!item) return;
      const answer = item.querySelector(".faq-answer");
      if (!answer) return;
      const isOpening = !item.classList.contains("is-open");
      const list = item.closest(".faq-list") || item.parentElement;
      list.querySelectorAll(".faq-item.is-open").forEach(other => {
        if (other === item) return;
        other.classList.remove("is-open");
        const ob = other.querySelector(".faq-question");
        const oa = other.querySelector(".faq-answer");
        if (ob) ob.setAttribute("aria-expanded", "false");
        if (oa) oa.hidden = true;
      });
      item.classList.toggle("is-open", isOpening);
      btn.setAttribute("aria-expanded", String(isOpening));
      answer.hidden = !isOpening;
    }, "user-visible");
  });
});

(function () {
  // Guard against double-loading: some pages still carry a legacy direct
  // <script data-goatcounter> tag alongside this global loader, which would
  // otherwise fetch count.js twice and double-count the same pageview.
  if (document.querySelector('script[data-goatcounter]')) return;

  const gc = document.createElement("script");
  gc.dataset.goatcounter = "https://davidportodiaz.goatcounter.com/count";
  gc.src = "https://gc.zgo.at/count.js";
  gc.async = true;
  document.head.appendChild(gc);
})();

// Metricool web analytics
(function () {
  function loadScript(a) {
    var b = document.getElementsByTagName("head")[0],
      c = document.createElement("script");
    c.type = "text/javascript";
    c.src = "https://tracker.metricool.com/resources/be.js";
    c.onreadystatechange = a;
    c.onload = a;
    b.appendChild(c);
  }
  loadScript(function () {
    beTracker.t({ hash: "45cbe9cb61a4afede1c287f1f545a629" });
  });
})();

// GoatCounter custom event tracking: send immediately when GC is ready so
// navigation clicks are not lost; fall back to a background retry otherwise.
function _gcEvent(path, title) {
  const payload = { path, title, event: true };
  if (window.goatcounter && window.goatcounter.count) {
    window.goatcounter.count(payload);
    return;
  }
  scheduleTask(() => {
    if (window.goatcounter && window.goatcounter.count) {
      window.goatcounter.count(payload);
    }
  }, "background");
}

// Bridge for opt-in modules (Article Tools, herramientas/*) that dispatch a
// local "dp:analytics" CustomEvent instead of calling _gcEvent() directly —
// keeps those modules decoupled from GoatCounter and from each other.
// Manuscript-processing tools deliberately do NOT dispatch this event.
// Different modules dispatch on window or on document depending on when
// they were written, so this listens on both; a given event only ever
// fires on the target it was dispatched to, so there is no double-count.
function _dpAnalyticsBridge(event) {
  const detail = event.detail || {};
  const name = String(detail.event || '');
  if (!/^[a-z0-9_-]{1,64}$/i.test(name)) return;

  const safeTarget = String(detail.target || '')
    .replace(/[^a-zA-Z0-9/_.-]/g, '')
    .slice(0, 96);

  _gcEvent(
    `article-${name}`,
    safeTarget ? `Artículo: ${name} · ${safeTarget}` : `Artículo: ${name}`
  );
}
window.addEventListener('dp:analytics', _dpAnalyticsBridge);
document.addEventListener('dp:analytics', _dpAnalyticsBridge);

// Popup de newsletter -- EXTRAIDO (H.1, 2026-08-23) a
// assets/newsletter-popup.js + assets/newsletter-popup.css: solo se
// necesitaba en /cuaderno/*, /recomendaciones/*, /universo/noveris/* y
// /clubes-de-lectura/* (verificado con grep en todo el sitio), pero este
// bloque se descargaba/ejecutaba en TODAS las paginas y se auto-excluia
// en runtime via allowedPath(). Esas 13 paginas ahora cargan
// assets/newsletter-popup.js + assets/newsletter-popup.css directamente.
// Triggers actualizados a la vez (no reintroducir los antiguos): 70% de
// scroll, sin temporizador de 30s, exit-intent solo con hover real.

// Modal "¿DÓNDE COMPRAR?" (Samuel entre mundos) -- EXTRAIDO (H.1,
// 2026-08-23) a assets/samuel-buy-modal.js: data-buy-modal solo existe en
// libros/samuel-entre-mundos/index.html (verificado con grep en todo el
// sitio), pero este bloque se descargaba y ejecutaba en TODAS las paginas.
// Esa pagina ahora carga assets/samuel-buy-modal.js directamente.


document.querySelectorAll('a[href*="amazon.es"]:not(#buy-dialog a)').forEach(link => {
  link.addEventListener("click", () => _gcEvent("comprar-amazon", "Clic: Comprar Amazon"));
});

// Leer fragmento gratis -- eventos separados por libro (H.2, 2026-08-23):
// antes un unico tracker con el patron `/fragmento/` (singular) mezclaba
// implicitamente todo bajo "leer-fragmento" sin identidad de libro, y
// ademas ese patron nunca coincidia con la ruta real de Manecillas
// (`/las-manecillas-del-recuerdo/fragmentos/`, en plural) por lo que esos
// clics no se contaban en absoluto.
document.addEventListener("click", (event) => {
  const link = event.target && event.target.closest ? event.target.closest('a[href]') : null;
  if (!link) return;
  const href = link.getAttribute("href") || "";
  if (href.includes("/las-manecillas-del-recuerdo/fragmentos/")) {
    _gcEvent("leer-fragmento-manecillas", "Clic: Leer fragmento (Las manecillas del recuerdo)");
  } else if (href.includes("/fragmento/")) {
    _gcEvent("leer-fragmento-samuel", "Clic: Leer fragmento (Samuel entre mundos)");
  }
});

// Explorar Noveris
document.querySelectorAll('a[href*="/universo/noveris/"]').forEach(link => {
  link.addEventListener("click", () => _gcEvent("explorar-noveris", "Clic: Explorar Noveris"));
});

// Ver página de prensa / press kit
document.querySelectorAll('a[href*="/prensa"]').forEach(link => {
  link.addEventListener("click", () => _gcEvent("ver-prensa", "Clic: Prensa"));
});

// Press kit JSON download
document.querySelectorAll('a[href*="/press-kit/"]').forEach(link => {
  link.addEventListener("click", () => _gcEvent("download-press-kit", "Descarga: press kit JSON"));
});
