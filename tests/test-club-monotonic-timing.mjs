import assert from 'node:assert/strict';
import { buildSession } from '../assets/club-session-engine.js';

for (const kind of ['fiction', 'nonfiction']) {
  for (const tone of ['social', 'balanced', 'deep']) {
    for (const scope of ['complete', 'partial']) {
      const config = { kind, tone, scope, genre: 'general' };
      const rows = [30, 60, 90].map(duration => buildSession({ ...config, duration }));
      for (const row of rows) {
        assert.equal(row.timing.opening + row.timing.core + row.timing.close, row.duration);
        assert.equal(row.questions.length, row.timing.questions);
      }
      for (let i = 1; i < rows.length; i++) {
        const previous = rows[i - 1];
        const current = rows[i];
        for (const field of ['opening', 'core', 'close', 'questions']) {
          assert.ok(current.timing[field] >= previous.timing[field], `${kind}/${tone}/${scope}: ${field} retrocede`);
        }
      }
      assert.equal(rows[0].activity, null);
      assert.ok(rows[2].activity);
    }
  }
}
console.log('test-club-monotonic-timing: OK');