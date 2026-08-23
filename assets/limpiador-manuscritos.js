(() => {
  'use strict';
  const form = document.querySelector('[data-mc-form]'); if (!form || !window.ManuscriptCleaner) return;
  const input = form.querySelector('[data-mc-input]'), status = form.querySelector('[data-mc-status]'), sample = form.querySelector('[data-mc-sample]'), clear = form.querySelector('[data-mc-clear]'), rulesBox = form.querySelector('[data-mc-rules]');
  const results = document.querySelector('[data-mc-results]'), summary = document.querySelector('[data-mc-summary]'), output = document.querySelector('[data-mc-output]'), copyBtn = document.querySelector('[data-mc-copy]'), downloadBtn = document.querySelector('[data-mc-download]');
  const fmt = n => new Intl.NumberFormat('es-ES').format(n);

  window.ManuscriptCleaner.RULES.forEach(rule => {
    const label = document.createElement('label'); label.className = 'tool-check';
    const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.checked = true; checkbox.dataset.mcRule = rule.id;
    label.append(checkbox, document.createTextNode(' ' + rule.label));
    rulesBox.appendChild(label);
  });

  function enabledRuleIds() {
    return Array.from(rulesBox.querySelectorAll('input[data-mc-rule]')).filter(c => c.checked).map(c => c.dataset.mcRule);
  }

  function run() {
    const text = input.value;
    if (!text.trim()) { results.hidden = true; status.textContent = 'Introduce un texto, elige las correcciones y pulsa «Limpiar texto».'; return; }
    const enabled = enabledRuleIds();
    if (!enabled.length) { results.hidden = true; status.textContent = 'Selecciona al menos una corrección para aplicar.'; return; }
    const r = window.ManuscriptCleaner.clean(text, enabled);
    output.value = r.text;
    summary.replaceChildren();
    r.applied.filter(a => enabled.includes(a.id)).forEach(a => {
      const box = document.createElement('div'), dt = document.createElement('span'), dd = document.createElement('strong');
      dt.textContent = a.label; dd.textContent = a.count ? `${fmt(a.count)} cambio(s)` : 'sin cambios'; box.append(dt, dd); summary.appendChild(box);
    });
    results.hidden = false;
    status.textContent = r.totalChanges ? `${fmt(r.totalChanges)} corrección(es) aplicadas. No se ha enviado ningún dato.` : 'No se encontró nada que corregir con las opciones seleccionadas.';
  }

  form.addEventListener('submit', e => { e.preventDefault(); run(); });
  sample.addEventListener('click', () => {
    input.value = 'Ana  se detuvo  frente a la puerta.\t Respiró hondo.\n\n\n\n"No puedo hacer esto" , pensó.\n- Vamos, tú puedes - se dijo a sí misma....';
    input.focus();
  });
  clear.addEventListener('click', () => { input.value = ''; output.value = ''; results.hidden = true; status.textContent = 'Introduce un texto, elige las correcciones y pulsa «Limpiar texto».'; input.focus(); });
  rulesBox.addEventListener('change', () => { if (!results.hidden) run(); });

  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(output.value);
      status.textContent = 'Resultado copiado al portapapeles.';
    } catch {
      output.select();
      status.textContent = 'No se pudo copiar automáticamente; el texto está seleccionado para copiar manualmente.';
    }
  });
  downloadBtn.addEventListener('click', () => {
    const blob = new Blob([output.value], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'manuscrito-limpio.txt';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  });
})();
