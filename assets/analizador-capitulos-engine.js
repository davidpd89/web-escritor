const WORD_RE = /[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:['’\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)*/g;
const SCENE_BREAK_RE = /^\s*(?:\*\s*\*\s*\*|\*{3,}|-{3,}|—\s*—\s*—|#{3,})\s*$/;
// A zero-width space/joiner or BOM landing inside a word (a real artifact
// from some PDF/OCR extraction pipelines) isn't in this character class
// either, so it still splits one word into two matches -- stripped before
// matching, since it must never count as a word boundary by itself.
const INVISIBLE_RE = /[\u200B-\u200D\uFEFF]/g;

export function words(text) {
  return String(text || '').replace(INVISIBLE_RE, '').match(WORD_RE) || [];
}

export function splitParagraphs(text) {
  return String(text || '').replace(/\r\n?/g, '\n').split(/\n\s*\n+/).map(v => v.trim()).filter(Boolean).filter(v => !SCENE_BREAK_RE.test(v));
}

export function median(values) {
  const nums = values.filter(Number.isFinite).slice().sort((a,b) => a-b);
  if (!nums.length) return 0;
  const mid = Math.floor(nums.length / 2);
  return nums.length % 2 ? nums[mid] : (nums[mid-1] + nums[mid]) / 2;
}

export function standardDeviation(values) {
  const nums = values.filter(Number.isFinite);
  if (nums.length < 2) return 0;
  const avg = nums.reduce((a,b)=>a+b,0) / nums.length;
  const variance = nums.reduce((sum,n)=>sum + (n-avg) ** 2,0) / nums.length;
  return Math.sqrt(variance);
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function countMentions(text, names) {
  const result = {};
  for (const raw of names) {
    const name = raw.trim();
    if (!name) continue;
    const pattern = name.split(/\s+/).map(escapeRegExp).join('\\s+');
    const re = new RegExp(`(^|[^\\p{L}\\p{N}_])(${pattern})(?=$|[^\\p{L}\\p{N}_])`, 'giu');
    let count = 0;
    while (re.exec(text)) count += 1;
    result[name] = count;
  }
  return result;
}

function countExplicitSceneBreaks(text) {
  const lines = String(text || '').replace(/\r\n?/g, '\n').split('\n');
  let count = 0;
  for (let i = 1; i < lines.length - 1; i += 1) {
    if (SCENE_BREAK_RE.test(lines[i]) && lines.slice(0, i).some(l => l.trim()) && lines.slice(i + 1).some(l => l.trim())) count += 1;
  }
  return count;
}

function quotedSegments(text) {
  const specs = [/«([^»]+)»/g, /“([^”]+)”/g, /"([^\"]+)"/g];
  const found = [];
  for (const re of specs) {
    let m;
    while ((m = re.exec(text)) !== null) found.push({text:m[1], index:m.index});
  }
  return found.sort((a,b)=>a.index-b.index);
}

export function approximateDialogue(text) {
  const paragraphs = String(text || '').replace(/\r\n?/g, '\n').split(/\n+/).map(v=>v.trim()).filter(Boolean);
  const totalWords = words(text).length;
  let dialogueWords = 0;
  let dialogueParagraphs = 0;
  for (const p of paragraphs) {
    let current = 0;
    if (p.startsWith('—')) current = words(p).length;
    else current = quotedSegments(p).reduce((sum, q)=>sum + words(q.text).length, 0);
    if (current > 0) dialogueParagraphs += 1;
    dialogueWords += current;
  }
  return {
    dialogueWords,
    dialoguePercentage: totalWords ? (dialogueWords / totalWords) * 100 : 0,
    dialogueParagraphs,
  };
}

export function analyzeChapter(chapter, names = []) {
  const text = String(chapter.text || '');
  const totalWords = words(text).length;
  const paragraphs = splitParagraphs(text);
  const paragraphWordCounts = paragraphs.map(p => words(p).length).filter(Boolean);
  const dialogue = approximateDialogue(text);
  const sceneBreaks = countExplicitSceneBreaks(text);
  return {
    id: chapter.id,
    title: chapter.title || chapter.name || 'Capítulo',
    sourceName: chapter.sourceName || '',
    words: totalWords,
    paragraphs: paragraphs.length,
    avgParagraphWords: paragraphWordCounts.length ? paragraphWordCounts.reduce((a,b)=>a+b,0) / paragraphWordCounts.length : 0,
    medianParagraphWords: median(paragraphWordCounts),
    longestParagraphWords: paragraphWordCounts.length ? Math.max(...paragraphWordCounts) : 0,
    dialoguePercentage: dialogue.dialoguePercentage,
    dialogueWords: dialogue.dialogueWords,
    explicitSceneBreaks: sceneBreaks,
    sceneBreaksPer10k: totalWords ? sceneBreaks / totalWords * 10000 : 0,
    mentions: countMentions(text, names),
  };
}

export function summarizeChapters(rows) {
  const counts = rows.map(r => r.words);
  const totalWords = counts.reduce((a,b)=>a+b,0);
  const meanWords = rows.length ? totalWords / rows.length : 0;
  const medianWords = median(counts);
  const sdWords = standardDeviation(counts);
  let cumulative = 0;
  const chapters = rows.map((row, index) => {
    cumulative += row.words;
    return {
      ...row,
      index: index + 1,
      cumulativeWords: cumulative,
      cumulativePercentage: totalWords ? cumulative / totalWords * 100 : 0,
      deviationFromMedianPct: medianWords ? (row.words - medianWords) / medianWords * 100 : 0,
    };
  });
  return {
    chapters,
    chapterCount: rows.length,
    totalWords,
    meanWords,
    medianWords,
    sdWords,
    coefficientVariationPct: meanWords ? sdWords / meanWords * 100 : 0,
    minWords: counts.length ? Math.min(...counts) : 0,
    maxWords: counts.length ? Math.max(...counts) : 0,
  };
}

export function analyzeChapterBatch(chapters, names = []) {
  return summarizeChapters(chapters.map(c => analyzeChapter(c, names)));
}
