import { buildReadingCardOutputs, validateReadingCardInput } from './tarjeta-estoy-leyendo-core.js';

const form = document.querySelector('[data-reading-card-form]');
const results = document.querySelector('[data-reading-card-results]');
const preview = document.querySelector('[data-reading-card-preview]');
const htmlOutput = document.querySelector('[data-reading-card-html]');
const markdownOutput = document.querySelector('[data-reading-card-markdown]');
const status = document.querySelector('[data-reading-card-status]');

function values() {
  return {
    label: form.elements.label.value,
    title: form.elements.title.value,
    author: form.elements.author.value,
    includeReference: form.elements.includeReference.checked,
  };
}

function renderPreview(model) {
  preview.replaceChildren();
  const eyebrow = document.createElement('p');
  eyebrow.className = 'eyebrow';
  eyebrow.textContent = model.label;
  const title = document.createElement('p');
  const strong = document.createElement('strong');
  strong.textContent = model.title;
  title.append(strong);
  const byline = document.createElement('p');
  const cite = document.createElement('cite');
  cite.textContent = model.author;
  byline.append('de ', cite);
  preview.append(eyebrow, title, byline);

  if (model.includeReference) {
    const ref = document.createElement('p');
    const link = document.createElement('a');
    link.href = '/herramientas/tarjeta-estoy-leyendo/';
    link.rel = 'nofollow';
    link.textContent = 'Creada con Tarjeta «Estoy leyendo»';
    ref.append(link);
    preview.append(ref);
  }
}

function generate(event) {
  event.preventDefault();
  const input = values();
  const errors = validateReadingCardInput(input);
  if (errors.length) {
    status.textContent = errors[0];
    results.hidden = true;
    return;
  }

  const output = buildReadingCardOutputs(input);
  renderPreview(output.model);
  htmlOutput.value = output.html;
  markdownOutput.value = output.markdown;
  results.hidden = false;
  status.textContent = 'Tarjeta generada en este navegador. No se ha enviado ni guardado ningún dato.';
  results.scrollIntoView({
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
    block: 'start',
  });
}

async function copyOutput(button) {
  const selector = button.getAttribute('data-copy-target');
  const target = document.querySelector(selector);
  if (!target) return;
  const text = target.value;

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      status.textContent = 'Código copiado al portapapeles.';
      return;
    }
  } catch {
    // Sigue con el fallback seleccionable; no hay red ni persistencia.
  }

  target.focus();
  target.select();
  let copied = false;
  try {
    copied = typeof document.execCommand === 'function' && document.execCommand('copy');
  } catch {
    copied = false;
  }
  status.textContent = copied
    ? 'Código copiado al portapapeles.'
    : 'No se pudo copiar automáticamente. El código queda seleccionado para copiarlo manualmente.';
}

form?.addEventListener('submit', generate);
document.querySelectorAll('[data-copy-target]').forEach((button) => {
  button.addEventListener('click', () => copyOutput(button));
});
