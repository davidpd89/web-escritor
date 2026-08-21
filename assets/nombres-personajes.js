(function () {
  'use strict';

  const root = document.querySelector('[data-character-name-checker]');
  if (!root || !window || !window.DPCharacterNames) return;

  const input = root.querySelector('[data-names-input]');
  const form = root.querySelector('form');
  const results = root.querySelector('[data-results]');
  const summary = root.querySelector('[data-summary]');
  const clear = root.querySelector('[data-clear]');

  const esc = value => String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));

  const parse = () => input.value
    .split(/[\n,;]+/)
    .map(value => value.trim())
    .filter(Boolean);

  function state(name) {
    root.dataset.state = name;
  }

  function clearResults() {
    results.innerHTML = '';
    results.hidden = true;
  }

  function resetResult(message) {
    clearResults();
    summary.textContent = message;
    input.setAttribute('aria-invalid', 'false');
    state('initial');
  }

  function render(data) {
    summary.textContent = `${data.counts.totalNames} nombres · ${data.counts.comparedPairs} parejas comparadas · ${data.counts.high} alertas altas · ${data.counts.medium} medias`;
    results.hidden = false;

    if (!data.flagged.length) {
      results.innerHTML = '<h2>Parejas potencialmente confusas</h2><p class="namecheck-empty">No aparecen parejas con señales fuertes de confusión. Esto no significa que los nombres sean perfectos: solo que este análisis no detecta similitud suficiente.</p>';
      state('result');
      return;
    }

    results.innerHTML = `<h2>Parejas potencialmente confusas</h2><ol class="namecheck-pairs">${data.flagged.map(pair => `
      <li class="namecheck-pair namecheck-pair--${pair.level}">
        <div class="namecheck-pair__head">
          <strong>${esc(pair.left)} ↔ ${esc(pair.right)}</strong>
          <span>${pair.level === 'high' ? 'Alta' : 'Media'} · ${Math.round(pair.score * 100)}%</span>
        </div>
        <p><strong>Motivo:</strong> ${esc(pair.reasons.slice(0, 4).join(' · '))}</p>
        <details>
          <summary>Ver métricas</summary>
          <ul>
            <li>Similitud ortográfica: ${Math.round(pair.metrics.edit * 100)}%</li>
            <li>Jaro-Winkler: ${Math.round(pair.metrics.jaroWinkler * 100)}%</li>
            <li>Patrón vocálico: ${Math.round(pair.metrics.vowels * 100)}%</li>
            <li>Silueta C/V: ${Math.round(pair.metrics.shape * 100)}%</li>
          </ul>
        </details>
      </li>`).join('')}</ol>`;
    state('result');
  }

  form.addEventListener('submit', event => {
    event.preventDefault();
    const names = parse();
    if (names.length < 2) {
      input.setAttribute('aria-invalid', 'true');
      summary.textContent = names.length
        ? 'Añade al menos un segundo nombre para poder comparar.'
        : 'Introduce al menos dos nombres.';
      clearResults();
      state('invalid');
      input.focus();
      return;
    }

    input.setAttribute('aria-invalid', 'false');
    render(window.DPCharacterNames.analyze(names));
  });

  input.addEventListener('input', () => {
    input.setAttribute('aria-invalid', 'false');
    clearResults();
    summary.textContent = input.value.trim()
      ? 'Lista modificada. Pulsa «Analizar» para comparar los nombres.'
      : 'Introduce al menos dos nombres para analizar.';
    state('initial');
  });

  clear.addEventListener('click', () => {
    input.value = '';
    resetResult('El análisis se ejecuta únicamente en tu navegador.');
    input.focus();
  });
})();
