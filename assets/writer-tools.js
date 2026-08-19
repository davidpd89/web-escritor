(() => {
  const root = document.querySelector("[data-wt-grid]");
  const form = document.querySelector("[data-wt-filters]");
  if (!root || !form) return;
  const cards = [...root.querySelectorAll(".wt-card")];
  const search = form.querySelector("[data-wt-search]");
  const stage = form.querySelector("[data-wt-stage]");
  const price = form.querySelector("[data-wt-price]");
  const noAccount = form.querySelector("[data-wt-no-account]");
  const local = form.querySelector("[data-wt-local]");
  const spanish = form.querySelector("[data-wt-spanish]");
  const count = form.querySelector("[data-wt-count]");
  const empty = document.querySelector("[data-wt-empty]");
  const norm = (v) => (v || "").toLocaleLowerCase("es").normalize("NFD").replace(/\p{Diacritic}/gu, "");
  function apply() {
    const q = norm(search.value); let visible = 0;
    cards.forEach((card) => {
      const ok = (!q || norm(card.dataset.name + " " + card.textContent).includes(q))
        && (!stage.value || card.dataset.stages.split(" ").includes(stage.value))
        && (!price.value || card.dataset.price === price.value)
        && (!noAccount.checked || card.dataset.account === "0")
        && (!local.checked || card.dataset.local === "1")
        && (!spanish.checked || card.dataset.spanish === "1");
      card.hidden = !ok; if (ok) visible += 1;
    });
    count.textContent = `${visible} ${visible === 1 ? "herramienta" : "herramientas"}`;
    empty.hidden = visible !== 0;
  }
  form.addEventListener("input", apply);
  form.querySelector("[data-wt-clear]").addEventListener("click", () => { form.reset(); apply(); search.focus(); });
  apply();
})();