// ── MODAL "¿DÓNDE COMPRAR?" (Samuel entre mundos) ──────────────────────────
// Extraido de script.js (H.1, 2026-08-23): solo se cargaba y ejecutaba
// realmente en libros/samuel-entre-mundos/index.html (unico HTML del repo
// con data-buy-modal), pero antes se descargaba/ejecutaba en TODAS las
// paginas via script.js. Depende de scheduleTask/_gcEvent, ya globales
// (definidos por script.js, cargado antes que este fichero).
//
// Crea el <dialog> una sola vez y lo abre cuando se pulsa cualquier
// botón/enlace con el atributo data-buy-modal. Funciona en Android,
// iOS (Safari 15.4+) y escritorio. ESC y clic fuera cierran el modal.
(function () {
  const AMAZON_URL = "https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21";
  const CASADELLIBRO_URL = "https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776/17856720";

  function buildDialog() {
    const d = document.createElement("dialog");
    d.id = "buy-dialog";
    d.setAttribute("aria-modal", "true");
    d.setAttribute("aria-labelledby", "buy-dialog-title");
    d.innerHTML = `
      <div class="buy-dialog-inner">
        <button class="buy-dialog-close" id="buy-dialog-close" aria-label="Cerrar">✕</button>
        <p class="buy-dialog-eyebrow">Samuel entre mundos · David Porto Díaz</p>
        <h2 id="buy-dialog-title" class="buy-dialog-title">¿Dónde quieres leerlo?</h2>
        <div class="buy-dialog-options">
          <a class="buy-option buy-option--primary" href="${AMAZON_URL}" target="_blank" rel="sponsored nofollow noopener noreferrer" data-gc="comprar-amazon-papel">
            <span class="buy-option-vendor">Amazon España</span>
            <span class="buy-option-format">Tapa blanda</span>
            <span class="buy-option-cta">Comprar →</span>
          </a>
          <a class="buy-option" href="${CASADELLIBRO_URL}" target="_blank" rel="noopener noreferrer" data-gc="comprar-casadellibro">
            <span class="buy-option-vendor">Casa del Libro</span>
            <span class="buy-option-format">Papel</span>
            <span class="buy-option-cta">Comprar →</span>
          </a>
        </div>
        <p class="buy-dialog-note">Amazon ofrece 30 días de devolución en papel. ¿Prefieres probarlo antes? <a href="/fragmento/" class="text-link" data-gc="fragmento-desde-modal">Lee el capítulo 1 gratis →</a></p>
        <p class="buy-dialog-affiliate-note">Algunos enlaces son de afiliado; no cambian el precio.</p>
      </div>`;
    document.body.appendChild(d);

    // Cerrar con el botón X
    d.querySelector("#buy-dialog-close").addEventListener("click", () => d.close());

    // Cerrar al clicar el backdrop (fuera del inner)
    d.addEventListener("click", e => {
      if (e.target === d) d.close();
    });

    // Focus trap: Tab dentro del diálogo
    d.addEventListener("keydown", e => {
      if (e.key !== "Tab") return;
      const focusable = Array.from(d.querySelectorAll("a, button")).filter(el => !el.disabled);
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey ? document.activeElement === first : document.activeElement === last) {
        e.preventDefault();
        (e.shiftKey ? last : first).focus();
      }
    });

    // GoatCounter por opción
    d.querySelectorAll("[data-gc]").forEach(el => {
      el.addEventListener("click", () => _gcEvent(el.dataset.gc, "Clic: " + el.dataset.gc));
    });

    return d;
  }

  let _dialog = null;
  let _lastBuyTrigger = null;

  function openBuyDialog(trigger) {
    _lastBuyTrigger = trigger || document.activeElement;
    if (!_dialog) {
      _dialog = buildDialog();
      _dialog.setAttribute("role", "dialog");
      // Restaurar foco al cerrar
      _dialog.addEventListener("close", () => {
        document.documentElement.classList.remove("modal-open");
        _lastBuyTrigger?.focus?.();
      });
    }
    // book=samuel (H.2): identidad de libro explicita para no mezclar este
    // funnel con el de Manecillas bajo el mismo nombre de evento generico.
    _gcEvent("abrir-modal-comprar", "Modal: abrir dónde comprar (book=samuel)");
    document.documentElement.classList.add("modal-open");
    // Back button support: push state so Back closes modal instead of leaving page
    history.pushState({ buyModal: true }, "", "#comprar");
    _dialog.showModal();
    // Enfocar la opción principal de compra
    setTimeout(() => (_dialog.querySelector(".buy-option--primary") || _dialog.querySelector("a, button"))?.focus(), 50);
  }

  // Activar en todos los elementos con data-buy-modal
  document.addEventListener("click", e => {
    const trigger = e.target.closest("[data-buy-modal]");
    if (trigger) {
      e.preventDefault();
      openBuyDialog(trigger);
    }
  });

  // Cerrar modal con el botón Atrás del navegador
  window.addEventListener("popstate", () => {
    if (_dialog && _dialog.open) _dialog.close();
  });
})();
