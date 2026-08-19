import { analyzeChapterBatch } from './analizador-capitulos-engine.js';

self.onmessage = event => {
  try {
    const { chapters = [], names = [] } = event.data || {};
    const result = analyzeChapterBatch(chapters, names);
    self.postMessage({ ok: true, result });
  } catch (error) {
    self.postMessage({ ok: false, error: error instanceof Error ? error.message : String(error) });
  }
};
