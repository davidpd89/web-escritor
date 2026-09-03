(() => {
  'use strict';
  const app = document.querySelector('[data-pov-app]'); if (!app || !window.PovDistribution) return;
  const form = app.querySelector('[data-pov-form]'), input = app.querySelector('[data-pov-input]'), inputTotals = app.querySelector('[data-pov-input-totals]'), formatMode = app.querySelector('[data-pov-format-mode]'), fieldScenes = app.querySelector('[data-pov-field-scenes]'), fieldTotals = app.querySelector('[data-pov-field-totals]'), sample = app.querySelector('[data-pov-sample]'), clear = app.querySelector('[data-pov-clear]'), status = app.querySelector('[data-pov-status]'), results = app.querySelector('[data-pov-results]'), metrics = app.querySelector('[data-pov-metrics]'), sequenceBlock = app.querySelector('[data-pov-sequence-block]'), lanesBlock = app.querySelector('[data-pov-lanes-block]'), sequence = app.querySelector('[data-pov-sequence]'), lanes = app.querySelector('[data-pov-lanes]'), summary = app.querySelector('[data-pov-summary]'), summaryHead = app.querySelector('[data-pov-summary-head]'), noteScenes = app.querySelector('[data-pov-note-scenes]'), noteTotals = app.querySelector('[data-pov-note-totals]');
  const SCENES_HEAD = '<tr><th scope="col">POV</th><th scope="col">Escenas</th><th scope="col">% escenas</th><th scope="col">Palabras</th><th scope="col">% palabras</th><th scope="col">Racha máx.</th><th scope="col">Hueco interno máx.</th></tr>';
  const TOTALS_HEAD = '<tr><th scope="col">POV</th><th scope="col">Palabras</th><th scope="col">% palabras</th></tr>';
  function activeInput() { return formatMode.value === 'totals' ? inputTotals : input; }
  function syncFormatUI() {
    const isTotals = formatMode.value === 'totals';
    fieldScenes.hidden = isTotals; fieldTotals.hidden = !isTotals;
  }
  formatMode?.addEventListener('change', () => { syncFormatUI(); invalidateResult(activeInput().value.trim() ? 'Entrada modificada. Pulsa «Analizar distribución» para actualizar la vista.' : 'Introduce datos y pulsa «Analizar distribución».'); });
  syncFormatUI();
  const paletteClasses = Array.from({ length: 10 }, (_, i) => `pov-tone-${i + 1}`);
  const pct = value => `${(value * 100).toFixed(value < 0.1 ? 1 : 0)} %`; const fmt = n => new Intl.NumberFormat('es-ES').format(n); const tone = order => paletteClasses[order % paletteClasses.length];
  function setStatus(message, isError = false) { status.textContent = message; status.classList.toggle('is-error', isError); app.dataset.state = isError ? 'invalid' : app.dataset.state; }
  function invalidateResult(message) { results.hidden = true; const field = activeInput(); field.setAttribute('aria-invalid', 'false'); app.dataset.state = field.value.trim() ? 'valid' : 'initial'; setStatus(message); }
  function renderScenes(data) {
    summaryHead.innerHTML = SCENES_HEAD;
    sequenceBlock.hidden = false; lanesBlock.hidden = false; noteScenes.hidden = false; noteTotals.hidden = true;
    metrics.replaceChildren(); [['Escenas',fmt(data.totalScenes)],['POV',fmt(data.totalPovs)],['Palabras',data.completeWords?fmt(data.totalWords):'Opcionales'],['Medición',data.completeWords?'escenas + palabras':'por escenas']].forEach(([label,value]) => { const box=document.createElement('div'),dt=document.createElement('span'),dd=document.createElement('strong'); dt.textContent=label; dd.textContent=value; box.append(dt,dd); metrics.appendChild(box); });
    sequence.replaceChildren(); data.scenes.forEach(scene => { const item=document.createElement('div'); item.className=`pov-scene ${tone(scene.povOrder)}`; item.title=`${scene.label} · ${scene.pov}${scene.words?` · ${fmt(scene.words)} palabras`:''}`; const label=document.createElement('span'),who=document.createElement('strong'); label.textContent=scene.label; who.textContent=scene.pov; item.append(label,who); sequence.appendChild(item); });
    lanes.replaceChildren(); const grid=document.createElement('div'); grid.className='pov-lane-grid'; grid.style.setProperty('--scene-count',String(data.totalScenes)); data.povs.forEach(pov => { const row=document.createElement('div'); row.className='pov-lane-row'; const name=document.createElement('div'); name.className=`pov-lane-name ${tone(pov.order)}`; name.textContent=pov.pov; const track=document.createElement('div'); track.className='pov-lane-track'; track.style.gridTemplateColumns=`repeat(${data.totalScenes}, minmax(20px, 1fr))`; data.scenes.forEach(scene => { const cell=document.createElement('span'); cell.className='pov-lane-cell'; if(scene.pov===pov.pov){cell.classList.add('is-active',tone(pov.order));cell.textContent='●';cell.title=`${scene.label}: ${pov.pov}`;cell.setAttribute('aria-label',`${scene.label}: ${pov.pov}`);}else cell.setAttribute('aria-hidden','true'); track.appendChild(cell); }); row.append(name,track); grid.appendChild(row); }); lanes.appendChild(grid);
    summary.replaceChildren(); data.povs.forEach(pov => { const tr=document.createElement('tr'); [pov.pov,fmt(pov.sceneCount),pct(pov.sceneShare),data.completeWords?fmt(pov.wordCount):'—',data.completeWords?pct(pov.wordShare):'—',fmt(pov.longestRun),fmt(pov.maxInternalGap)].forEach((value,i)=>{const cell=document.createElement(i===0?'th':'td');if(i===0)cell.scope='row';cell.textContent=value;if(i===0)cell.classList.add(tone(pov.order));tr.appendChild(cell);}); summary.appendChild(tr); });
    results.hidden=false; app.dataset.state='result'; setStatus(`Vista creada con ${data.totalScenes} escenas. No se ha enviado ningún dato.`);
  }
  function renderTotals(data) {
    summaryHead.innerHTML = TOTALS_HEAD;
    sequenceBlock.hidden = true; lanesBlock.hidden = true; noteScenes.hidden = true; noteTotals.hidden = false;
    metrics.replaceChildren(); [['POV',fmt(data.totalPovs)],['Palabras',fmt(data.totalWords)],['Medición','totales por POV']].forEach(([label,value]) => { const box=document.createElement('div'),dt=document.createElement('span'),dd=document.createElement('strong'); dt.textContent=label; dd.textContent=value; box.append(dt,dd); metrics.appendChild(box); });
    sequence.replaceChildren(); lanes.replaceChildren();
    summary.replaceChildren(); data.povs.forEach(pov => { const tr=document.createElement('tr'); [pov.pov,fmt(pov.wordCount),pct(pov.wordShare)].forEach((value,i)=>{const cell=document.createElement(i===0?'th':'td');if(i===0)cell.scope='row';cell.textContent=value;if(i===0)cell.classList.add(tone(pov.order));tr.appendChild(cell);}); summary.appendChild(tr); });
    results.hidden=false; app.dataset.state='result'; setStatus(`Vista creada con ${data.totalPovs} POV. No se ha enviado ningún dato.`);
  }
  function run() {
    const isTotals = formatMode.value === 'totals';
    const field = activeInput();
    if (isTotals) {
      const parsed = window.PovDistribution.parseTotals(field.value);
      if (parsed.errors.length) { results.hidden=true; field.setAttribute('aria-invalid','true'); app.dataset.state='invalid'; setStatus(parsed.errors.slice(0,4).join(' '),true); field.focus(); return; }
      field.setAttribute('aria-invalid','false');
      renderTotals(window.PovDistribution.analyzeTotals(parsed.totals));
    } else {
      const parsed = window.PovDistribution.parse(field.value);
      if (parsed.errors.length) { results.hidden=true; field.setAttribute('aria-invalid','true'); app.dataset.state='invalid'; setStatus(parsed.errors.slice(0,4).join(' '),true); field.focus(); return; }
      field.setAttribute('aria-invalid','false');
      renderScenes(window.PovDistribution.analyze(parsed.scenes));
    }
  }
  form.addEventListener('submit', e => { e.preventDefault(); run(); });
  input.addEventListener('input', () => invalidateResult(input.value.trim() ? 'Entrada modificada. Pulsa «Analizar distribución» para actualizar la vista.' : 'Introduce al menos una escena y pulsa «Analizar distribución».'));
  inputTotals.addEventListener('input', () => invalidateResult(inputTotals.value.trim() ? 'Entrada modificada. Pulsa «Analizar distribución» para actualizar la vista.' : 'Introduce al menos un POV con sus palabras y pulsa «Analizar distribución».'));
  sample.addEventListener('click', () => {
    if (formatMode.value === 'totals') { inputTotals.value=['Ana | 24500','Bruno | 18200','Clara | 9100'].join('\n'); invalidateResult('Ejemplo cargado. Pulsa «Analizar distribución» para crear la vista.'); inputTotals.focus(); return; }
    input.value=['1.1 | Ana | 1420','1.2 | Ana | 980','2.1 | Bruno | 1310','2.2 | Clara | 1200','3.1 | Ana | 1550','3.2 | Bruno | 1180','4.1 | Bruno | 990','5.1 | Clara | 1300'].join('\n'); invalidateResult('Ejemplo cargado. Pulsa «Analizar distribución» para crear la vista.'); input.focus();
  });
  clear.addEventListener('click', () => { input.value=''; inputTotals.value=''; invalidateResult('Datos borrados de esta página.'); activeInput().focus(); });
})();
