import { buildSession } from './club-session-engine.js';

const form = document.querySelector('[data-club-session-form]');
if (form) {
  const output = document.querySelector('[data-club-session-output]');
  const status = document.querySelector('[data-club-session-status]');
  const generateAlt = document.querySelector('[data-club-session-alt]');
  const copyBtn = document.querySelector('[data-club-session-copy]');
  const printBtn = document.querySelector('[data-club-session-print]');
  let variant = 0;
  let lastSession = null;

  const emit = (event, target = '') => document.dispatchEvent(new CustomEvent('dp:analytics', { detail: { event, target } }));

  const readConfig = () => Object.fromEntries(new FormData(form).entries());

  const makeList = (title, items) => {
    const section = document.createElement('section');
    section.className = 'club-session-block';
    const h = document.createElement('h3');
    h.textContent = title;
    const ol = document.createElement('ol');
    items.forEach(text => {
      const li = document.createElement('li');
      li.textContent = text;
      ol.append(li);
    });
    section.append(h, ol);
    return section;
  };

  const render = session => {
    output.replaceChildren();
    const heading = document.createElement('div');
    heading.className = 'club-session-result-head';
    const h2 = document.createElement('h2');
    h2.textContent = session.title ? `Sesión para «${session.title}»` : 'Tu sesión de club de lectura';
    const meta = document.createElement('p');
    meta.textContent = `${session.duration} min · ${session.kind === 'fiction' ? 'ficción' : 'no ficción'} · ${session.scope === 'partial' ? 'lectura parcial' : 'libro completo'}`;
    heading.append(h2, meta);
    output.append(heading);

    output.append(makeList(`Apertura · ${session.timing.opening} min`, session.opening));
    output.append(makeList(`Debate central · ${session.timing.core} min`, session.questions));
    if (session.activity) output.append(makeList('Actividad opcional', [session.activity]));
    output.append(makeList(`Cierre · ${session.timing.close} min`, session.closing));
    output.append(makeList('Recordatorios para moderar', session.facilitator));
    output.hidden = false;
  };

  const plainText = session => {
    const lines = [];
    lines.push(session.title ? `Sesión para «${session.title}»` : 'Sesión de club de lectura');
    if (session.author) lines.push(`Autor/a: ${session.author}`);
    lines.push(`${session.duration} minutos`,'');
    const block = (title, items) => { lines.push(title); items.forEach((x, i) => lines.push(`${i + 1}. ${x}`)); lines.push(''); };
    block('Apertura', session.opening);
    block('Debate central', session.questions);
    if (session.activity) block('Actividad opcional', [session.activity]);
    block('Cierre', session.closing);
    block('Recordatorios para moderar', session.facilitator);
    return lines.join('\n');
  };

  const generate = (increment = false) => {
    if (increment) variant += 1;
    const config = readConfig();
    lastSession = buildSession(config, variant);
    render(lastSession);
    status.textContent = 'Sesión preparada en este dispositivo. Ningún título, tema o nombre se ha enviado a un servidor.';
    emit('club_session_generate', `${lastSession.duration}-${lastSession.kind}-${lastSession.tone}`);
  };

  form.addEventListener('submit', event => { event.preventDefault(); variant = 0; generate(false); });
  generateAlt.addEventListener('click', () => generate(true));
  copyBtn.addEventListener('click', async () => {
    if (!lastSession) return;
    try {
      await navigator.clipboard.writeText(plainText(lastSession));
      status.textContent = 'Sesión copiada al portapapeles.';
      emit('club_session_copy', String(lastSession.duration));
    } catch {
      status.textContent = 'No se pudo copiar automáticamente. Puedes seleccionar el resultado y copiarlo manualmente.';
    }
  });
  printBtn.addEventListener('click', () => { if (lastSession) { emit('club_session_print', String(lastSession.duration)); window.print(); } });
}
