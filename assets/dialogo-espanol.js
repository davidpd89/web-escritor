const WORD_RE = /[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:['’\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)*/g;
const CHAPTER_RE = /^(?:#{1,3}\s+.+|cap[ií]tulo\s+(?:\d+|[ivxlcdm]+|.+)|chapter\s+(?:\d+|[ivxlcdm]+|.+))$/iu;
// A zero-width space/joiner or BOM landing inside a word (a real artifact
// from some PDF/OCR extraction pipelines) isn't in this character class
// either, so it still splits one word into two matches -- stripped before
// matching rather than added to the class, since it must never count as a
// word by itself.
const INVISIBLE_RE = /[\u200B-\u200D\uFEFF]/g;

function words(text) {
  return String(text || '').replace(INVISIBLE_RE, '').match(WORD_RE) || [];
}

function quotedSegments(text) {
  const specs = [
    { type: 'angle', re: /«([^»]+)»/g },
    { type: 'curly', re: /“([^”]+)”/g },
    { type: 'straight', re: /"([^"]+)"/g },
  ];
  const found = [];
  for (const spec of specs) {
    let m;
    while ((m = spec.re.exec(text)) !== null) {
      found.push({ type: spec.type, text: m[1], index: m.index });
    }
  }
  return found.sort((a, b) => a.index - b.index);
}

function parseDashParagraph(paragraph) {
  const trimmed = paragraph.trim();
  if (!trimmed.startsWith('—')) return null;

  const segments = trimmed.slice(1).split('—');
  let dialogueWords = 0;
  let narratorWords = 0;
  const dialogueSegments = [];
  const narratorSegments = [];

  segments.forEach((segment, index) => {
    const count = words(segment).length;
    if (index % 2 === 0) {
      dialogueWords += count;
      if (segment.trim()) dialogueSegments.push(segment.trim());
    } else {
      narratorWords += count;
      if (segment.trim()) narratorSegments.push(segment.trim());
    }
  });

  return { dialogueWords, narratorWords, dialogueSegments, narratorSegments };
}

function splitChapters(paragraphs) {
  const chapters = [];
  let current = { title: 'Texto completo', paragraphs: [] };
  let foundHeading = false;

  for (const paragraph of paragraphs) {
    if (CHAPTER_RE.test(paragraph.trim())) {
      if (current.paragraphs.length || foundHeading) chapters.push(current);
      current = { title: paragraph.replace(/^#{1,3}\s+/, '').trim(), paragraphs: [] };
      foundHeading = true;
    } else {
      current.paragraphs.push(paragraph);
    }
  }
  if (current.paragraphs.length || foundHeading) chapters.push(current);

  return foundHeading ? chapters.filter(ch => ch.paragraphs.length) : [{ title: 'Texto completo', paragraphs }];
}

function inspectParagraphs(paragraphs, mode) {
  let totalWords = 0;
  let dialogueWords = 0;
  let quotedWords = 0;
  let dialogueParagraphs = 0;
  let interventions = 0;
  let longestIntervention = 0;
  let currentNarrativeStreak = 0;
  let maxNarrativeStreak = 0;
  const conventions = { dash: 0, angle: 0, curly: 0, straight: 0 };

  const details = paragraphs.map((paragraph, idx) => {
    const paragraphWords = words(paragraph).length;
    totalWords += paragraphWords;

    const dash = parseDashParagraph(paragraph);
    const quotes = quotedSegments(paragraph);
    const quoteWordCount = quotes.reduce((sum, q) => {
      conventions[q.type] += 1;
      return sum + words(q.text).length;
    }, 0);
    quotedWords += quoteWordCount;

    let countedDialogue = 0;
    let paragraphInterventions = 0;
    let basis = 'narración';

    if (dash) {
      conventions.dash += 1;
      if (mode === 'dash') {
        countedDialogue = dash.dialogueWords;
        paragraphInterventions = countedDialogue > 0 ? 1 : 0;
        longestIntervention = Math.max(longestIntervention, countedDialogue);
        basis = 'raya';
      }
    } else if (mode === 'quotes' && quotes.length) {
      countedDialogue = quoteWordCount;
      paragraphInterventions = quotes.length;
      quotes.forEach(q => { longestIntervention = Math.max(longestIntervention, words(q.text).length); });
      basis = 'comillas';
    }

    const hasDialogue = countedDialogue > 0;
    if (hasDialogue) {
      dialogueParagraphs += 1;
      currentNarrativeStreak = 0;
    } else {
      currentNarrativeStreak += 1;
      maxNarrativeStreak = Math.max(maxNarrativeStreak, currentNarrativeStreak);
    }

    dialogueWords += countedDialogue;
    interventions += paragraphInterventions;

    return {
      number: idx + 1,
      totalWords: paragraphWords,
      dialogueWords: countedDialogue,
      quotedWords: quoteWordCount,
      hasDialogue,
      basis,
      preview: paragraph.slice(0, 170),
    };
  });

  return {
    totalWords,
    dialogueWords,
    quotedWords,
    dialogueParagraphs,
    narrativeParagraphs: Math.max(0, paragraphs.length - dialogueParagraphs),
    interventions,
    avgInterventionWords: interventions ? dialogueWords / interventions : 0,
    longestInterventionWords: longestIntervention,
    maxNarrativeStreak,
    conventions,
    details,
  };
}

export function analyzeDialogue(input) {
  const text = String(input || '').replace(/\r\n?/g, '\n').trim();
  const paragraphs = text ? text.split(/\n+/).map(p => p.trim()).filter(Boolean) : [];
  const contentParagraphs = paragraphs.filter(p => !CHAPTER_RE.test(p.trim()));
  const hasDashDialogue = contentParagraphs.some(p => p.trim().startsWith('—'));
  const hasQuotedText = contentParagraphs.some(p => quotedSegments(p).length > 0);
  const mode = hasDashDialogue ? 'dash' : hasQuotedText ? 'quotes' : 'none';

  const overall = inspectParagraphs(contentParagraphs, mode);
  const chapters = splitChapters(paragraphs).map(chapter => {
    const stats = inspectParagraphs(chapter.paragraphs, mode);
    return {
      title: chapter.title,
      totalWords: stats.totalWords,
      dialogueWords: stats.dialogueWords,
      dialoguePercentage: stats.totalWords ? (stats.dialogueWords / stats.totalWords) * 100 : 0,
      interventions: stats.interventions,
    };
  });

  return {
    ...overall,
    paragraphs: contentParagraphs.length,
    mode,
    modeLabel: mode === 'dash' ? 'raya de diálogo' : mode === 'quotes' ? 'texto entre comillas' : 'sin convención detectada',
    dialoguePercentage: overall.totalWords ? (overall.dialogueWords / overall.totalWords) * 100 : 0,
    chapters,
    caveats: [
      mode === 'dash'
        ? 'Se prioriza la raya porque aparece en el texto. Las acotaciones entre rayas se excluyen del recuento cuando siguen el patrón editorial habitual.'
        : mode === 'quotes'
          ? 'No se han detectado párrafos iniciados por raya. El porcentaje usa texto entre comillas, que puede incluir pensamientos, citas, rótulos o ironía además de habla.'
          : 'No se ha detectado una convención de diálogo reconocible.',
      'La detección es heurística: una puntuación poco convencional, una raya usada con otra función o comillas no dialogales pueden alterar el resultado.',
      'La cifra describe estructura; no puntúa la calidad del diálogo ni recomienda un porcentaje objetivo.',
    ],
  };
}

function fmt(n, digits = 0) {
  return Number(n || 0).toLocaleString('es-ES', { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
}

export function render(result, root) {
  root.hidden = false;
  root.querySelector('[data-dialogue-basis]').textContent = `Base de cálculo: ${result.modeLabel}.`;

  const metrics = root.querySelector('[data-dialogue-metrics]');
  metrics.innerHTML = [
    ['Palabras totales', fmt(result.totalWords)],
    ['Contadas como diálogo', fmt(result.dialogueWords)],
    ['Diálogo / texto', `${fmt(result.dialoguePercentage, 1)} %`],
    ['Intervenciones detectadas', fmt(result.interventions)],
    ['Media por intervención', `${fmt(result.avgInterventionWords, 1)} palabras`],
    ['Racha sin diálogo máxima', `${fmt(result.maxNarrativeStreak)} ${result.maxNarrativeStreak === 1 ? 'párrafo' : 'párrafos'}`],
  ].map(([label, value]) => `<div class="dialogue-metric"><dt>${label}</dt><dd>${value}</dd></div>`).join('');

  const conventionList = Object.entries(result.conventions)
    .filter(([, count]) => count > 0)
    .map(([key, count]) => `${({dash:'raya',angle:'«comillas españolas»',curly:'“comillas tipográficas”',straight:'"comillas rectas"'})[key]}: ${count}`)
    .join(' · ') || 'No se ha detectado una convención de diálogo.';
  root.querySelector('[data-dialogue-conventions]').textContent = conventionList;

  const rows = result.details.filter(d => d.hasDialogue).slice(0, 20);
  root.querySelector('[data-dialogue-detail]').innerHTML = rows.length
    ? rows.map(d => `<li><strong>Párrafo ${d.number}</strong> · ${d.dialogueWords}/${d.totalWords} palabras contadas como diálogo · ${escapeHtml(d.preview)}</li>`).join('')
    : '<li>No se han detectado bloques dialogados con la convención seleccionada automáticamente.</li>';

  const chapterRoot = root.querySelector('[data-dialogue-chapters]');
  const meaningfulChapters = result.chapters.length > 1 || result.chapters[0]?.title !== 'Texto completo';
  chapterRoot.innerHTML = meaningfulChapters
    ? result.chapters.map(ch => `<li><strong>${escapeHtml(ch.title)}</strong> · ${fmt(ch.dialoguePercentage, 1)} % · ${fmt(ch.dialogueWords)}/${fmt(ch.totalWords)} palabras · ${fmt(ch.interventions)} intervenciones</li>`).join('')
    : '<li>No se han detectado encabezados de capítulo. Prueba con líneas como «Capítulo 1», «Capítulo I» o encabezados Markdown.</li>';

  root.querySelector('[data-dialogue-caveat]').textContent = result.caveats[0];
  root.querySelector('[data-dialogue-caveat-extra]').textContent = result.caveats[1];
}

export function init() {
  const form = document.querySelector('[data-dialogue-tool]');
  if (!form) return;
  const textarea = form.querySelector('textarea');
  const root = document.querySelector('[data-dialogue-results]');
  const clear = form.querySelector('[data-dialogue-clear]');

  form.addEventListener('submit', event => {
    event.preventDefault();
    const result = analyzeDialogue(textarea.value);
    render(result, root);
    // Analytics disabled by default for privacy: no external events or payloads sent.
  });

  clear.addEventListener('click', () => {
    textarea.value = '';
    root.hidden = true;
    textarea.focus();
  });
}

if (typeof document !== 'undefined') init();
