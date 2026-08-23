export const READING_CARD_LABELS = Object.freeze({
  leyendo: 'Estoy leyendo',
  releyendo: 'Estoy releyendo',
  recomiendo: 'Recomiendo',
});

export const READING_CARD_LIMITS = Object.freeze({ title: 160, author: 120 });
export const READING_CARD_TOOL_URL = 'https://davidportodiaz.com/herramientas/tarjeta-estoy-leyendo/';

function clean(value) {
  return String(value ?? '').trim().replace(/\s+/g, ' ');
}

export function validateReadingCardInput(input = {}) {
  const title = clean(input.title);
  const author = clean(input.author);
  const label = String(input.label || 'leyendo');
  const errors = [];

  if (!title) errors.push('Escribe el título del libro.');
  if (title.length > READING_CARD_LIMITS.title) errors.push(`El título no puede superar ${READING_CARD_LIMITS.title} caracteres.`);
  if (!author) errors.push('Escribe el nombre del autor o autora.');
  if (author.length > READING_CARD_LIMITS.author) errors.push(`La autoría no puede superar ${READING_CARD_LIMITS.author} caracteres.`);
  if (!Object.hasOwn(READING_CARD_LABELS, label)) errors.push('Elige una etiqueta válida.');

  return errors;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function escapeMarkdown(value) {
  return String(value).replace(/([\\`*_{}\[\]()#+\-.!|>])/g, '\\$1');
}

export function normalizeReadingCardInput(input = {}) {
  const errors = validateReadingCardInput(input);
  if (errors.length) {
    const error = new Error(errors[0]);
    error.code = 'invalid-reading-card';
    error.errors = errors;
    throw error;
  }
  const labelKey = String(input.label || 'leyendo');
  return {
    title: clean(input.title),
    author: clean(input.author),
    labelKey,
    label: READING_CARD_LABELS[labelKey],
    includeReference: input.includeReference === true,
  };
}

export function buildReadingCardOutputs(input = {}) {
  const model = normalizeReadingCardInput(input);
  const title = escapeHtml(model.title);
  const author = escapeHtml(model.author);
  const label = escapeHtml(model.label);
  const reference = model.includeReference
    ? `<p style="margin:.75rem 0 0;font-size:.72rem;line-height:1.45"><a href="${READING_CARD_TOOL_URL}" rel="nofollow noopener noreferrer">Creada con Tarjeta «Estoy leyendo»</a></p>`
    : '';

  const html = [
    '<figure aria-label="Tarjeta de lectura" style="box-sizing:border-box;max-width:34rem;margin:1rem 0;padding:1rem 1.25rem;border:1px solid #b8b8b8;border-radius:.5rem;background:#fff;color:#1b1b1b;font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">',
    `<p style="margin:0 0 .35rem;font-size:.78rem;line-height:1.4;letter-spacing:.06em;text-transform:uppercase">${label}</p>`,
    `<p style="margin:0;font-size:1.25rem;line-height:1.35"><strong>${title}</strong></p>`,
    `<figcaption style="margin:.4rem 0 0;font-size:.92rem;line-height:1.5">de <cite>${author}</cite></figcaption>`,
    reference,
    '</figure>',
  ].filter(Boolean).join('');

  const markdownReference = model.includeReference
    ? `\n\n[Creada con Tarjeta «Estoy leyendo»](${READING_CARD_TOOL_URL})`
    : '';
  const markdown = `**${escapeMarkdown(model.label)}**\n\n***${escapeMarkdown(model.title)}*** — ${escapeMarkdown(model.author)}${markdownReference}`;

  return { model, html, markdown };
}
