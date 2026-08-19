(function () {
  'use strict';
  const root = document.querySelector('[data-character-name-checker]');
  if (!root || !window || !window.DPCharacterNames) return;
  const input = root.querySelector('[data-names-input]');
  const form = root.querySelector('form');
  const results = root.querySelector('[data-results]');
  const summary = root.querySelector('[data-summary]');
  const clear = root.querySelector('[data-clear]');

  const esc = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const parse = () => input.value.split(/[\n,;]+/).map(x => x.trim()).filter(Boolean);
  const bucket = (n) => n < 6 ? '1-5' : n < 11 ? '6-10' : n < 21 ? '11-20' : '21+';

  const render = (data) => {
    summary.textContent = `${data.counts.totalNames} nombres · ${data.counts.comparedPairs} parejas comparadas · ${data.counts.high} alertas altas · ${data.counts.medium} medias`;
    if (!data.flagged.length) {
      results.innerHTML = '<p class="namecheck-empty">No aparecen parejas con señales fuertes de confusión. Esto no significa que los nombres sean perfectos: solo que este análisis no detecta similitud suficiente.</p>';
      return;
    }
    results.innerHTML = data.flagged.map(p => `
      <article class="namecheck-pair namecheck-pair--${p.level}">
        <div class="namecheck-pair__head"><strong>${esc(p.left)} ↔ ${esc(p.right)}</strong><span>${p.level === 'high' ? 'Alta' : 'Media'} · ${Math.round(p.score * 100)}%</span></div>
        <p>${esc(p.reasons.slice(0, 4).join(' · '))}</p>
        <details><summary>Ver métricas</summary><ul>
          <li>Similitud ortográfica: ${Math.round(p.metrics.edit * 100)}%</li>
          <li>Jaro-Winkler: ${Math.round(p.metrics.jaroWinkler * 100)}%</li>
          <li>Patrón vocálico: ${Math.round(p.metrics.vowels * 100)}%</li>
          <li>Silueta C/V: ${Math.round(p.metrics.shape * 100)}%</li>
        </ul></details>
      </article>`).join('');
  };

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const names = parse();
    if (names.length < 2) {
      summary.textContent = 'Introduce al menos dos nombres.';
      results.innerHTML = '';
      return;
    }
    const data = window.DPCharacterNames.analyze(names);
    render(data);
    // Analytics disabled for privacy: do not dispatch events with text-derived data.
  });

  clear.addEventListener('click', () => {
    input.value = '';
    results.innerHTML = '';
    summary.textContent = 'El análisis se ejecuta únicamente en tu navegador.';
    input.focus();
  });
})();
