// Modal «¿Dónde comprar?» de Samuel entre mundos.
// Runtime deliberadamente fail-closed: aunque este asset se cargase por error
// en otra URL, no registra listeners, no carga CSS y no expone retailers si no
// existe la identidad exacta de la página Samuel.
(function () {
  const EXPECTED_PATH = "/libros/samuel-entre-mundos/";
  const path = window.location.pathname.replace(/\/index\.html$/, "/");
  const pageRoot = document.querySelector('main[data-family="book-samuel"]');
  if (path !== EXPECTED_PATH || !pageRoot) return;

  const STYLE_HREF = "/assets/samuel-buy-modal.css";
  const AMAZON_URL = "https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21";
  const CASADELLIBRO_URL = "https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776/17856720";

  if (!document.querySelector('link[data-samuel-buy-modal-style]')) {
    const style = document.createElement("link");
    style.rel = "stylesheet";
    style.href = STYLE_HREF;
    style.dataset.samuelBuyModalStyle = "true";
    document.head.appendChild(style);
  }

  let dialog = null;
  let lastBuyTrigger = null;

  function restoreFocus() {
    const target = lastBuyTrigger;
    lastBuyTrigger = null;
    if (target instanceof HTMLElement && target.isConnected) {
      target.focus({ preventScroll: true });
    }
  }

  function buildDialog() {
    const d = document.createElement("dialog");
    d.id = "buy-dialog";
    d.setAttribute("aria-labelledby", "buy-dialog-title");
    d.innerHTML = `
      <div class="buy-dialog-inner">
        <button class="buy-dialog-close" id="buy-dialog-close" type="button" aria-label="Cerrar">✕</button>
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

    d.querySelector("#buy-dialog-close").addEventListener("click", () => d.close());
    d.addEventListener("click", (event) => {
      if (event.target === d) d.close();
    });
    // No hay focus trap manual: showModal() hace modal el resto del documento
    // y el navegador mantiene el ciclo de teclado dentro del <dialog>.
    d.addEventListener("close", () => {
      document.documentElement.classList.remove("modal-open");
      restoreFocus();
    });

    d.querySelectorAll("[data-gc]").forEach((element) => {
      element.addEventListener("click", () => _gcEvent(element.dataset.gc, "Clic: " + element.dataset.gc));
    });
    return d;
  }

  function openBuyDialog(trigger) {
    if (!(trigger instanceof HTMLElement) || !pageRoot.contains(trigger)) return false;
    if (dialog?.open || document.querySelector("dialog[open]")) return false;

    if (!dialog) dialog = buildDialog();
    lastBuyTrigger = trigger;

    // #63 es owner de la taxonomía analítica global: se conserva el nombre
    // existente y solo se mantiene la identidad Samuel en la etiqueta.
    _gcEvent("abrir-modal-comprar", "Modal: abrir dónde comprar (book=samuel)");
    document.documentElement.classList.add("modal-open");
    history.pushState({ buyModal: true }, "", "#comprar");
    dialog.showModal();
    (dialog.querySelector(".buy-option--primary") || dialog.querySelector("a, button"))?.focus({ preventScroll: true });
    return true;
  }

  pageRoot.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const trigger = event.target.closest("[data-buy-modal]");
    if (!trigger || !pageRoot.contains(trigger)) return;
    event.preventDefault();
    openBuyDialog(trigger);
  });

  window.addEventListener("popstate", () => {
    if (dialog?.open) dialog.close();
  });
})();
