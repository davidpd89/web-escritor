import { THEMES, buildInterviewPlan } from './entrevista-familiar-core.js';

const form = document.querySelector('[data-family-interview-form]');
const results = document.querySelector('[data-family-interview-results]');
const questionsList = document.querySelector('[data-family-questions]');
const followList = document.querySelector('[data-family-followups]');
const meta = document.querySelector('[data-family-meta]');
const note = document.querySelector('[data-family-sensitive-note]');
const status = document.querySelector('[data-family-status]');
const nameInput = document.querySelector('[data-family-name]');
const relationInput = document.querySelector('[data-family-relation]');

function emit(event, detail = {}) {
  document.dispatchEvent(new CustomEvent('dp:analytics', { detail: { event, ...detail } }));
}

function checkedThemes() {
  return [...form.querySelectorAll('input[name="theme"]:checked')].map((el) => el.value);
}

function safeText(value) {
  return String(value || '').trim();
}

function render(plan) {
  const person = safeText(nameInput.value);
  const relation = safeText(relationInput.value);
  const label = person ? `Entrevista a ${person}` : 'Tu entrevista familiar';
  const relationPart = relation ? ` · ${relation}` : '';
  meta.textContent = `${label}${relationPart} · sesión orientativa de ${plan.duration} min · ${plan.questions.length} preguntas`;

  questionsList.replaceChildren();
  plan.questions.forEach((item, index) => {
    const li = document.createElement('li');
    const badge = document.createElement('span');
    badge.className = 'family-question__theme';
    badge.textContent = item.theme;
    const p = document.createElement('p');
    p.textContent = item.text;
    li.append(badge, p);
    li.dataset.questionIndex = String(index + 1);
    questionsList.append(li);
  });

  followList.replaceChildren();
  plan.followUps.forEach((text) => {
    const li = document.createElement('li');
    li.textContent = text;
    followList.append(li);
  });

  note.hidden = !plan.hasSensitiveTheme;
  results.hidden = false;
  status.textContent = 'Guion preparado. No se ha guardado ni enviado ningún dato.';
  results.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
}

form?.addEventListener('submit', (event) => {
  event.preventDefault();
  const themes = checkedThemes();
  const duration = Number(form.elements.duration.value);
  const objectMode = Boolean(form.elements.objectMode.checked);
  const plan = buildInterviewPlan({ duration, themes, objectMode });
  render(plan);
  emit('family_interview_generate', { duration, theme_count: themes.length, object_mode: objectMode });
});

document.querySelector('[data-family-print]')?.addEventListener('click', () => {
  emit('family_interview_print');
  window.print();
});

document.querySelector('[data-family-reset]')?.addEventListener('click', () => {
  form.reset();
  results.hidden = true;
  questionsList.replaceChildren();
  followList.replaceChildren();
  status.textContent = 'No se guarda ningún nombre ni selección.';
  nameInput.focus();
});

// Progressive enhancement: labels are present in HTML even if JS fails.
Object.entries(THEMES).forEach(([key, theme]) => {
  const checkbox = form?.querySelector(`input[name="theme"][value="${CSS.escape(key)}"]`);
  if (checkbox && theme.sensitive) checkbox.dataset.sensitive = 'true';
});
