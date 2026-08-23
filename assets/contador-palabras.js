(() => {
  'use strict';
  const form = document.querySelector('[data-wc-form]'); if (!form || !window.WordCounter) return;
  const input = form.querySelector('[data-wc-input]'), status = form.querySelector('[data-wc-status]'), sample = form.querySelector('[data-wc-sample]'), clear = form.querySelector('[data-wc-clear]');
  const results = document.querySelector('[data-wc-results]'), summary = document.querySelector('[data-wc-summary]');
  const fmt = n => new Intl.NumberFormat('es-ES').format(Math.round(n));
  const fmt1 = n => new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 }).format(n);

  function render() {
    const text = input.value;
    if (!text.trim()) { results.hidden = true; status.textContent = 'Introduce un texto y pulsa «Contar», o los recuentos se actualizan mientras escribes.'; return; }
    const r = window.WordCounter.count(text);
    summary.replaceChildren();
    [
      ['Palabras', fmt(r.wordCount)],
      ['Caracteres (con espacios)', fmt(r.charsWithSpaces)],
      ['Caracteres (sin espacios)', fmt(r.charsNoSpaces)],
      ['Frases', fmt(r.sentenceCount)],
      ['Párrafos', fmt(r.paragraphCount)],
      ['Palabras por frase (media)', fmt1(r.avgWordsPerSentence)],
      ['Palabras por párrafo (media)', fmt1(r.avgWordsPerParagraph)],
      ['Tiempo de lectura estimado', window.WordCounter.formatReadingTime(r.readingMinutes)],
    ].forEach(([label, value]) => {
      const box = document.createElement('div'), dt = document.createElement('span'), dd = document.createElement('strong');
      dt.textContent = label; dd.textContent = value; box.append(dt, dd); summary.appendChild(box);
    });
    results.hidden = false;
    status.textContent = `${fmt(r.wordCount)} palabras contadas. No se ha enviado ningún dato.`;
  }

  form.addEventListener('submit', e => { e.preventDefault(); render(); });
  input.addEventListener('input', render);
  sample.addEventListener('click', () => {
    input.value = 'Ana llevaba tres años escribiendo la misma novela. Cada mañana abría el cuaderno, releía las últimas páginas y añadía una frase, a veces dos.\n\nAquel martes, sin embargo, algo cambió. Encontró una nota que no recordaba haber escrito: "Termínala antes de que sea tarde."';
    render(); input.focus();
  });
  clear.addEventListener('click', () => { input.value = ''; render(); input.focus(); });
  render();
})();
