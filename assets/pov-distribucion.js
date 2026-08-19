(() => {
  'use strict';
  const app = document.querySelector('[data-pov-app]');
  if (!app || !window.PovDistribution) return;

  const input = app.querySelector('[data-pov-input]');
  const sample = app.querySelector('[data-pov-sample]');
  const clear = app.querySelector('[data-pov-clear]');
  const status = app.querySelector('[data-pov-status]');
  const results = app.querySelector('[data-pov-results]');
  const metrics = app.querySelector('[data-pov-metrics]');
  const sequence = app.querySelector('[data-pov-sequence]');
  const lanes = app.querySelector('[data-pov-lanes]');
  const summary = app.querySelector('[data-pov-summary]');

  const paletteClasses = Array.from({ length: 10 }, (_, i) => `pov-tone-${i + 1}`);

  function pct(value) { return `${(value * 100).toFixed(value < 0.1 ? 1 : 0)} %`; }
  function fmt(n) { return new Intl.NumberFormat('es-ES').format(n); }
  function tone(order) { return paletteClasses[order % paletteClasses.length]; }

  function setStatus(message, isError = false) {
    status.textContent = message;
    status.classList.toggle('is-error', isError);
  }

  function render(data) {
    metrics.replaceChildren();
    const metricData = [
      ['Escenas', fmt(data.totalScenes)],
      ['POV', fmt(data.totalPovs)],
      ['Palabras', data.completeWords ? fmt(data.totalWords) : 'Opcionales'],
      ['Medición', data.completeWords ? 'escenas + palabras' : 'por escenas']
    ];
    metricData.forEach(([label, value]) => {
      const box = document.createElement('div');
      const dt = document.createElement('span'); dt.textContent = label;
      const dd = document.createElement('strong'); dd.textContent = value;
      box.append(dt, dd); metrics.appendChild(box);
    });

    sequence.replaceChildren();
    data.scenes.forEach(scene => {
      const item = document.createElement('div');
      item.className = `pov-scene ${tone(scene.povOrder)}`;
      item.title = `${scene.label} · ${scene.pov}${scene.words ? ` · ${fmt(scene.words)} palabras` : ''}`;
      const label = document.createElement('span'); label.textContent = scene.label;
      const who = document.createElement('strong'); who.textContent = scene.pov;
      item.append(label, who); sequence.appendChild(item);
    });

    lanes.replaceChildren();
    const grid = document.createElement('div');
    grid.className = 'pov-lane-grid';
    grid.style.setProperty('--scene-count', String(data.totalScenes));
    data.povs.forEach(pov => {
      const row = document.createElement('div'); row.className = 'pov-lane-row';
      const name = document.createElement('div'); name.className = `pov-lane-name ${tone(pov.order)}`; name.textContent = pov.pov;
      const track = document.createElement('div'); track.className = 'pov-lane-track';
      track.style.gridTemplateColumns = `repeat(${data.totalScenes}, minmax(18px, 1fr))`;
      data.scenes.forEach(scene => {
        const cell = document.createElement('span');
        cell.className = 'pov-lane-cell';
        if (scene.pov === pov.pov) {
          cell.classList.add('is-active', tone(pov.order));
          cell.textContent = '●';
          cell.title = `${scene.label}: ${pov.pov}`;
        } else {
          cell.setAttribute('aria-hidden', 'true');
        }
        track.appendChild(cell);
      });
      row.append(name, track); grid.appendChild(row);
    });
    lanes.appendChild(grid);

    summary.replaceChildren();
    data.povs.forEach(pov => {
      const tr = document.createElement('tr');
      const values = [
        pov.pov,
        fmt(pov.sceneCount),
        pct(pov.sceneShare),
        data.completeWords ? fmt(pov.wordCount) : '—',
        data.completeWords ? pct(pov.wordShare) : '—',
        fmt(pov.longestRun),
        fmt(pov.maxInternalGap)
      ];
      values.forEach((value, i) => {
        const cell = document.createElement(i === 0 ? 'th' : 'td');
        if (i === 0) cell.scope = 'row';
        cell.textContent = value;
        if (i === 0) cell.classList.add(tone(pov.order));
        tr.appendChild(cell);
      });
      summary.appendChild(tr);
    });

    results.hidden = false;
    setStatus(`Vista creada con ${data.totalScenes} escenas. No se ha enviado ningún dato.`);
  }

  function run() {
    const parsed = window.PovDistribution.parse(input.value);
    if (parsed.errors.length) {
      results.hidden = true;
      setStatus(parsed.errors.slice(0, 4).join(' '), true);
      return;
    }
    render(window.PovDistribution.analyze(parsed.scenes));
  }

  input.addEventListener('input', () => {
    if (!input.value.trim()) { results.hidden = true; setStatus(''); return; }
    run();
  });

  sample.addEventListener('click', () => {
    input.value = [
      '1.1 | Ana | 1420',
      '1.2 | Ana | 980',
      '2.1 | Bruno | 1310',
      '2.2 | Ana | 1560',
      '3.1 | Clara | 1120',
      '3.2 | Bruno | 1250',
      '4.1 | Ana | 1680',
      '4.2 | Clara | 1040'
    ].join('\n');
    run(); input.focus();
  });

  clear.addEventListener('click', () => {
    input.value = ''; results.hidden = true; setStatus('Datos borrados de esta página.'); input.focus();
  });
})();
