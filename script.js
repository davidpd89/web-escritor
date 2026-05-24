// scheduler.postTask() shim — default to background work; opt into user-blocking only for critical UI.
function scheduleTask(fn, priority = "background") {
  if (typeof scheduler !== "undefined" && scheduler.postTask) {
    return scheduler.postTask(fn, { priority });
  }
  return Promise.resolve().then(fn);
}

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

// Mobile nav
const navToggle = document.querySelector(".nav-toggle");
const siteNav = document.querySelector(".site-nav");

if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    scheduleTask(() => {
      const isOpen = siteNav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
    }, "user-blocking");
  });

  siteNav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      scheduleTask(() => {
        siteNav.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      }, "user-blocking");
    });
  });
}

function syncHashScroll() {
  if (!window.location.hash || window.location.hash === "#") return;
  const targetId = decodeURIComponent(window.location.hash.slice(1));
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
(function () {
  if (document.querySelector(".mobile-bottom-nav")) return;

  const items = [
    { href: "/", label: "Inicio", icon: "⌂" },
    { href: "/libros/samuel-entre-mundos/", label: "Libro", icon: "◇" },
    { href: "/fragmento/", label: "Leer", icon: "Ⅰ" },
    { href: "/universo/noveris/", label: "Noveris", icon: "✦" },
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

// Back-to-top button — create, inject, and wire up
(function () {
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
    scheduleTask(() => {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
    }, "user-visible");
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

// Reading progress bar
(function () {
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

// Quiz "¿Qué habitante de Noveris serías?"
(function () {
  const app = document.getElementById("quiz-noveris-app");
  if (!app) return;

  const QUESTIONS = [
    {
      text: "Encuentras una puerta que no debería existir. ¿Qué haces?",
      options: [
        { text: "La cruzo. Tengo que saber qué hay al otro lado.", key: "mensajero" },
        { text: "Estudio sus mecanismos antes de decidir nada.", key: "sabio" },
        { text: "Me aseguro de que nadie más la cruce.", key: "silenciadora" },
        { text: "La protejo. Hay puertas que existen por algo.", key: "guardian" }
      ]
    },
    {
      text: "¿Cuál es tu mayor defecto?",
      options: [
        { text: "No sé cuándo parar de buscar.", key: "mensajero" },
        { text: "Analizo tanto que a veces no actúo.", key: "sabio" },
        { text: "Soy demasiado estricto/a, conmigo y con los demás.", key: "silenciadora" },
        { text: "Me cuesta soltar lo que protejo.", key: "guardian" }
      ]
    },
    {
      text: "La magia que siempre tiene un precio representa para ti…",
      options: [
        { text: "Una aventura con consecuencias reales.", key: "mensajero" },
        { text: "Un sistema que hay que comprender antes de usar.", key: "sabio" },
        { text: "Una responsabilidad que la mayoría ignora.", key: "silenciadora" },
        { text: "Una razón para ser cauteloso con el poder.", key: "guardian" }
      ]
    },
    {
      text: "Una verdad que podría destruirte: ¿preferirías conocerla o ignorarla?",
      options: [
        { text: "Conocerla siempre. La incertidumbre es peor.", key: "mensajero" },
        { text: "Conocerla, pero en el momento justo.", key: "sabio" },
        { text: "Conocerla, para poder actuar en consecuencia.", key: "silenciadora" },
        { text: "Depende de cuántas personas proteja esa verdad.", key: "guardian" }
      ]
    },
    {
      text: "¿Qué te llevarías a Noveris?",
      options: [
        { text: "Nada. Las manos vacías son más honestas.", key: "mensajero" },
        { text: "Un cuaderno donde anotar todo lo que descubra.", key: "sabio" },
        { text: "Algo que me recuerde las normas del mundo al que vuelvo.", key: "silenciadora" },
        { text: "Algo que pertenezca a alguien que quiero proteger.", key: "guardian" }
      ]
    }
  ];

  const RESULTS = {
    mensajero: {
      name: "El Mensajero",
      desc: "Eres el tipo de habitante que Noveris no esperaba. Curioso hasta el riesgo, incapaz de dejar una pregunta sin responder, cruzarías la barrera aunque todo te dijera que no. Como Samuel, tu fuerza no es la fuerza: es la necesidad de saber. Noveris te necesita aunque no lo sepa todavía.",
      share: "Soy El Mensajero en el mundo de Samuel entre mundos ✨ Mi curiosidad cruzaría cualquier barrera. ¿Y tú, qué habitante de Noveris serías? → davidportodiaz.com"
    },
    sabio: {
      name: "El Sabio del Espejo",
      desc: "Observas más de lo que hablas. El Espejo Ancestral no revela lo que ves: revela lo que eres, y tú llevas tiempo mirándote. En Noveris guardarías el conocimiento como se guarda el fuego — con cuidado, para que no queme lo que no debe. La paciencia es tu poder más subestimado.",
      share: "Soy El Sabio del Espejo en el mundo de Samuel entre mundos ✨ El conocimiento como poder y responsabilidad. ¿Y tú, qué habitante de Noveris serías? → davidportodiaz.com"
    },
    silenciadora: {
      name: "La Silenciadora",
      desc: "Disciplina absoluta. Conoces los costes de la magia mejor que nadie — y te aseguras de que nadie los olvide. En Noveris no eres el villano: eres la consecuencia necesaria. Lo que otros llaman frialdad, tú lo llamas honestidad. Noveris funciona porque hay gente como tú dispuesta a mantener el precio real.",
      share: "Soy La Silenciadora en el mundo de Samuel entre mundos ✨ La disciplina que mantiene el equilibrio. ¿Y tú, qué habitante de Noveris serías? → davidportodiaz.com"
    },
    guardian: {
      name: "El Guardián",
      desc: "Firme, leal, con el peso de lo que cuidas grabado en cada decisión. En Noveris entenderías que la barrera existe por algo y que no todo lo que está al otro lado merece cruzar. Tu fortaleza no está en atacar: está en lo que decides no soltar nunca, cueste lo que cueste.",
      share: "Soy El Guardián en el mundo de Samuel entre mundos ✨ La lealtad que sostiene el mundo. ¿Y tú, qué habitante de Noveris serías? → davidportodiaz.com"
    }
  };

  let current = 0;
  const scores = { mensajero: 0, sabio: 0, silenciadora: 0, guardian: 0 };

  const stage = document.getElementById("quiz-stage");
  const stepLabel = document.getElementById("quiz-step-label");
  const questionText = document.getElementById("quiz-question-text");
  const optionsEl = document.getElementById("quiz-options");
  const resultEl = document.getElementById("quiz-result");
  const resultName = document.getElementById("quiz-result-name");
  const resultDesc = document.getElementById("quiz-result-desc");
  const progressBar = document.getElementById("quiz-progress-bar");
  const shareBtn = document.getElementById("quiz-share-btn");
  const restartBtn = document.getElementById("quiz-restart-btn");
  const subscribeForm = document.getElementById("quiz-subscribe-form");
  const resultActions = resultEl.querySelector(".quiz-result-actions");

  function shuffle(arr) {
    return arr.slice().sort(() => Math.random() - 0.5);
  }

  function showQuestion(idx) {
    const q = QUESTIONS[idx];
    stepLabel.textContent = `Pregunta ${idx + 1} de ${QUESTIONS.length}`;
    questionText.textContent = q.text;
    progressBar.style.width = (idx / QUESTIONS.length * 100) + "%";
    optionsEl.innerHTML = "";
    shuffle(q.options).forEach(opt => {
      const btn = document.createElement("button");
      btn.className = "quiz-option";
      btn.type = "button";
      btn.textContent = opt.text;
      btn.addEventListener("click", () => choose(opt.key));
      optionsEl.appendChild(btn);
    });
  }

  function choose(key) {
    scheduleTask(() => {
      scores[key]++;
      current++;
      if (current < QUESTIONS.length) {
        showQuestion(current);
      } else {
        showResult();
      }
    }, "user-visible");
  }

  function showResult() {
    progressBar.style.width = "100%";
    stage.hidden = true;
    resultEl.hidden = false;
    const winner = Object.entries(scores).reduce((a, b) => b[1] > a[1] ? b : a)[0];
    const res = RESULTS[winner];
    resultName.textContent = res.name;
    resultDesc.textContent = res.desc;
    resultEl._shareText = res.share;
    resultEl._resultKey = winner;
    setResultLocked(Boolean(subscribeForm && subscribeForm.dataset.done !== "true"));
    resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function setResultLocked(isLocked) {
    resultEl.classList.toggle("is-locked", isLocked);
    resultName.hidden = isLocked;
    resultDesc.hidden = isLocked;
    if (resultActions) resultActions.hidden = isLocked;
  }

  shareBtn.addEventListener("click", () => {
    const text = resultEl._shareText || "";
    if (navigator.share) {
      navigator.share({ text }).catch(() => {});
    } else if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        const orig = shareBtn.textContent;
        shareBtn.textContent = "✓ Texto copiado";
        setTimeout(() => { shareBtn.textContent = orig; }, 2200);
      });
    }
  });

  // Brevo email subscription
  if (subscribeForm) {
    subscribeForm.addEventListener("submit", (e) => {
      e.preventDefault();
      scheduleTask(async () => {
        const emailEl = document.getElementById("quiz-email");
        const gdprEl = document.getElementById("quiz-gdpr");
        const statusEl = document.getElementById("quiz-subscribe-status");
        const submitBtn = subscribeForm.querySelector("[type=submit]");
        if (!emailEl.value.trim() || !gdprEl.checked) {
          statusEl.textContent = gdprEl.checked ? "Introduce un email válido." : "Acepta la política de privacidad para continuar.";
          return;
        }
        statusEl.textContent = "";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        // Worker URL: update with your Cloudflare Worker URL after deploying cloudflare-worker-subscribe.js
        const WORKER_URL = "https://subscribe.davidpd89.workers.dev";
        try {
          const res = await fetch(WORKER_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: emailEl.value.trim(),
              listIds: [3],
              updateEnabled: true,
              attributes: { NOVERIS: resultEl._resultKey || "" }
            })
          });
          if (res.ok || res.status === 204 || res.status === 400) {
            subscribeForm.dataset.done = "true";
            subscribeForm.innerHTML = "<p class=\"quiz-subscribe-ok\">✓ ¡Apuntado! Recibirás novedades de David Porto Díaz antes que nadie.</p>";
            _gcEvent("newsletter-quiz", "Newsletter: quiz Noveris");
            setResultLocked(false);
          } else {
            throw new Error(res.status);
          }
        } catch {
          statusEl.textContent = "Error al suscribirse. Escríbenos a samuelentremundos@gmail.com.";
          submitBtn.disabled = false;
          submitBtn.textContent = "Suscribirme";
        }
      }, "user-blocking");
    });
  }

  restartBtn.addEventListener("click", () => {
    current = 0;
    Object.keys(scores).forEach(k => { scores[k] = 0; });
    resultEl.hidden = true;
    stage.hidden = false;
    setResultLocked(false);
    showQuestion(0);
  });

  showQuestion(0);
})();

// Generic newsletter forms (home, fragmento, manecillas pages)
(function () {
  async function submitNewsletter(formId, emailId, gdprId, statusId, sourceLabel) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      scheduleTask(async () => {
        const emailEl = document.getElementById(emailId);
        const gdprEl = document.getElementById(gdprId);
        const statusEl = document.getElementById(statusId);
        const submitBtn = form.querySelector("[type=submit]");
        if (!emailEl || !emailEl.value.trim() || !gdprEl || !gdprEl.checked) {
          if (statusEl) statusEl.textContent = gdprEl && !gdprEl.checked
            ? "Acepta la política de privacidad para continuar."
            : "Introduce un email válido.";
          return;
        }
        if (statusEl) statusEl.textContent = "";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        // Worker URL: update with your Cloudflare Worker URL after deploying cloudflare-worker-subscribe.js
        const WORKER_URL = "https://subscribe.davidpd89.workers.dev";
        try {
          const res = await fetch(WORKER_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: emailEl.value.trim(),
              listIds: [3],
              updateEnabled: true,
              attributes: { SOURCE: sourceLabel }
            })
          });
          if (res.ok || res.status === 204 || res.status === 400) {
            form.innerHTML = "<p class=\"quiz-subscribe-ok\">✓ ¡Apuntado! Recibirás el capítulo y novedades de David Porto Díaz.</p>";
            _gcEvent("newsletter-" + sourceLabel, "Newsletter: " + sourceLabel);
          } else {
            throw new Error(res.status);
          }
        } catch {
          if (statusEl) statusEl.textContent = "Error al suscribirse. Escríbenos a samuelentremundos@gmail.com.";
          submitBtn.disabled = false;
          submitBtn.textContent = "Suscribirme";
        }
      }, "user-blocking");
    });
  }
  submitNewsletter("newsletter-form-home",       "nl-email-home",       "nl-gdpr-home",       "nl-status-home",       "home");
  submitNewsletter("newsletter-form-fragmento",  "nl-email-fragmento",  "nl-gdpr-fragmento",  "nl-status-fragmento",  "fragmento");
  submitNewsletter("newsletter-form-manecillas", "nl-email-manecillas", "nl-gdpr-manecillas", "nl-status-manecillas", "manecillas");
})();

// Modo Samuel — accesibilidad cognitiva y foco lector
(function () {
  const STORAGE_KEY = "modo-samuel";
  const root = document.documentElement;

  function applyMode(active) {
    root.classList.toggle("modo-samuel", active);
    document.querySelectorAll(".modo-samuel-btn").forEach(btn => {
      btn.setAttribute("aria-pressed", String(active));
      btn.title = active ? "Desactivar modo de lectura" : "Activar modo de lectura enfocado";
    });
  }

  const saved = localStorage.getItem(STORAGE_KEY) === "1";
  applyMode(saved);

  document.querySelectorAll(".modo-samuel-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      scheduleTask(() => {
        const next = !root.classList.contains("modo-samuel");
        localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
        applyMode(next);
      }, "user-blocking");
    });
  });
})();

// FAQ accordion
document.querySelectorAll(".faq-question").forEach((btn) => {
  btn.addEventListener("click", () => {
    scheduleTask(() => {
      const item = btn.closest(".faq-item");
      const answer = item.querySelector(".faq-answer");
      const isOpen = item.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", String(isOpen));
      answer.hidden = !isOpen;
    }, "user-visible");
  });
});

// GoatCounter analytics — privacy-friendly, no cookies
(function () {
  const gc = document.createElement("script");
  gc.dataset.goatcounter = "https://davidportodiaz.goatcounter.com/count";
  gc.src = "//gc.zgo.at/count.js";
  gc.async = true;
  document.head.appendChild(gc);
})();

// GoatCounter custom event tracking — fire-and-forget, safe if GC not yet loaded
function _gcEvent(path, title) {
  scheduleTask(() => {
    if (window.goatcounter && window.goatcounter.count) {
      window.goatcounter.count({ path, title, event: true });
    }
  }, "background");
}

// Comprar en Amazon
document.querySelectorAll('a[href*="amazon.es"]').forEach(link => {
  link.addEventListener("click", () => _gcEvent("comprar-amazon", "Clic: Comprar Amazon"));
});

// Leer fragmento gratis
document.querySelectorAll('a[href*="/fragmento/"]').forEach(link => {
  link.addEventListener("click", () => _gcEvent("leer-fragmento", "Clic: Leer fragmento"));
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
