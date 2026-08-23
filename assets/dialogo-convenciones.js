const OPENING_HYPHEN_RE = /^\s*-\s+\S/m;
const OPENING_DASH_RE = /^\s*—\s*\S/m;
const ANGLE_QUOTES_RE = /«[^»]*»/g;
const CURLY_QUOTES_RE = /“[^”]*”/g;
const STRAIGHT_QUOTES_RE = /"[^"]*"/g;
const NARRATION_COMMA_UPPER_RE = /—[^\n—]{2,},\s+[A-ZÁÉÍÓÚÑÜ]/g;

function matches(re, text) {
  return text.match(re) || [];
}

function findLineNumbers(text, re) {
  const numbers = [];
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length; i += 1) {
    if (re.test(lines[i])) {
      numbers.push(i + 1);
    }
    re.lastIndex = 0;
  }
  return numbers;
}

export function analyzeDialogueConventions(input) {
  const text = String(input || '').replace(/\r\n?/g, '\n');
  const issues = [];
  const warnings = [];

  const openingHyphenLines = findLineNumbers(text, /^\s*-\s+\S/);
  const openingDashCount = matches(OPENING_DASH_RE, text).length;
  if (openingHyphenLines.length > 0) {
    issues.push({
      code: 'hyphen-instead-of-dash',
      message: 'Se detectaron intervenciones de diálogo abiertas con guion (-) en lugar de raya (—).',
      count: openingHyphenLines.length,
      lines: openingHyphenLines,
    });
  }

  const quoteCounts = {
    angle: matches(ANGLE_QUOTES_RE, text).length,
    curly: matches(CURLY_QUOTES_RE, text).length,
    straight: matches(STRAIGHT_QUOTES_RE, text).length,
  };
  const activeStyles = Object.entries(quoteCounts).filter(([, count]) => count > 0);
  if (activeStyles.length > 1) {
    issues.push({
      code: 'mixed-quotes',
      message: 'Hay mezcla de estilos de comillas en el mismo texto.',
      count: activeStyles.length,
      details: activeStyles.map(([style, count]) => `${style}:${count}`),
    });
  }

  const suspiciousNarration = matches(NARRATION_COMMA_UPPER_RE, text);
  if (suspiciousNarration.length > 0) {
    warnings.push({
      code: 'punctuation-after-dialogue-tag',
      message: 'Posibles acotaciones con coma seguida de mayúscula (revisar puntuación tras inciso).',
      count: suspiciousNarration.length,
    });
  }

  if (openingDashCount === 0 && openingHyphenLines.length === 0) {
    warnings.push({
      code: 'no-dialogue-openers',
      message: 'No se detectaron aperturas de diálogo con raya o guion al inicio de línea.',
      count: 0,
    });
  }

  return {
    characters: text.length,
    issues,
    warnings,
    quoteCounts,
    hasProblems: issues.length > 0 || warnings.length > 0,
  };
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

function renderList(items, emptyMessage) {
  if (!items.length) {
    return `<li>${escapeHtml(emptyMessage)}</li>`;
  }
  return items
    .map((item) => {
      const where = item.lines && item.lines.length ? ` Líneas: ${item.lines.slice(0, 12).join(', ')}.` : '';
      const details = item.details && item.details.length ? ` (${item.details.join(' · ')})` : '';
      return `<li><strong>${escapeHtml(item.message)}</strong>${details} <span>(${item.count})</span>.${escapeHtml(where)}</li>`;
    })
    .join('');
}

export function renderDialogueConventions(result, root) {
  root.hidden = false;
  root.querySelector('[data-dialogue-conv-summary]').textContent =
    `Caracteres analizados: ${result.characters.toLocaleString('es-ES')}.`;

  root.querySelector('[data-dialogue-conv-issues]').innerHTML = renderList(
    result.issues,
    'No se han detectado incidencias de convención en las reglas comprobadas.'
  );

  root.querySelector('[data-dialogue-conv-warnings]').innerHTML = renderList(
    result.warnings,
    'No hay avisos adicionales con las heurísticas aplicadas.'
  );

  const quotes = result.quoteCounts;
  root.querySelector('[data-dialogue-conv-quotes]').textContent =
    `Comillas detectadas -> angulares: ${quotes.angle}, tipográficas: ${quotes.curly}, rectas: ${quotes.straight}.`;
}

export function initDialogueConventionsTool() {
  const form = document.querySelector('[data-dialogue-conv-tool]');
  if (!form) {
    return;
  }
  const textarea = form.querySelector('textarea');
  const clear = form.querySelector('[data-dialogue-conv-clear]');
  const output = document.querySelector('[data-dialogue-conv-results]');

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const result = analyzeDialogueConventions(textarea.value);
    renderDialogueConventions(result, output);
  });

  clear.addEventListener('click', () => {
    textarea.value = '';
    output.hidden = true;
    textarea.focus();
  });
}

if (typeof document !== 'undefined') {
  initDialogueConventionsTool();
}
