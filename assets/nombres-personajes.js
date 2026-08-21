(function () {
  'use strict';
  const root = document.querySelector('[data-character-name-checker]');
  if (!root || !window || !window.DPCharacterNames) return;
  const input = root.querySelector('[data-names-input]'); const form = root.querySelector('form'); const results = root.querySelector('[data-results]'); const summary = root.querySelector('[data-summary]'); const clear = root.querySelector('[data-clear]');
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const parse = () => input.value.split(/[\n,;]+/).map(x => x.trim()).filter(Boolean);
  function state(name) { root.dataset.state = name; }
  function resetResult(message) { results.innerHTML = ''; summary.textContent = message; input.setAttribute('aria-invalid', 'false'); state('initial'); }
  const render = data => {
    summary.textContent = `${data.counts.totalNames} nombres · ${data.counts.comparedPairs} parejas comparadas · ${data.counts.high} alertas altas · ${data.counts.medium} medias`;
    if (!data.flagged.length) { results.innerHTML = '<h2>Parejas potencialmente confusas</h2><p class="namecheck-empty">No aparecen parejas con señales fuertes de confusión. Esto no significa que los nombres sean perfectos: solo que este análisis no detecta similitud suficiente.</p>'; state('result'); return; }
    results.innerHTML = `<h2>Parejas potencialmente confusas</h2><ol class="namecheck-pairs">${data.flagged.map(p => `<li class="namecheck-pair namecheck-pair--${p.level}"><div class="namecheck-pair__head"><strong>${esc(p.left)} ↔ ${esc(p.right)}</strong><span>${p.level === 'high' ? 'Alta' : 'Media'} · ${Math.round(p.score * 100)}%</span></div><p><strong>Motivo:</strong> ${esc(p.reasons.slice(0, 4).join(' · '))}</p><details><summary>Ver métricas</summary><ul><li>Similitud ortográfica: ${Math.round(p.metrics.edit * 100)}%</li><li>Jaro-Winkler: ${Math.round(p.metrics.jaroWinkler * 100)}%</li><li>Patrón vocálico: ${Math.round(p.metrics.vowels * 100)}%</li><li>Silueta C/V: ${Math.round(p.metrics.shape * 100)}%</li></ul></details></li>`).join('')}</ol>`;
    state('result');
  };
  form.addEventListener('submit', e => {
    e.preventDefault(); const names = parse();
    if (names.length < 2) { input.setAttribute('aria-invalid', 'true'); summary.textContent = names.length ? 'Añade al menos un segundo nombre para poder comparar.' : 'Introduce al menos dos nombres.'; results.innerHTML = ''; state('invalid'); input.focus(); return; }
    input.setAttribute('aria-invalid', 'false'); render(window.DPCharacterNames.analyze(names));
  });
  input.addEventListener('input', () => { input.setAttribute('aria-invalid', 'false'); results.innerHTML = ''; summary.textContent = input.value.trim() ? 'Lista modificada. Pulsa «Analizar» para comparar los nombres.' : 'Introduce al menos dos nombres para analizar.'; state('initial'); });
  clear.addEventListener('click', () => { input.value = ''; resetResult('El análisis se ejecuta únicamente en tu navegador.'); input.focus(); });
})();
