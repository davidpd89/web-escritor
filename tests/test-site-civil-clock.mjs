import assert from 'node:assert/strict';
import { SITE_TIME_ZONE, siteCivilDate } from '../qa/site-civil-clock.mjs';

assert.equal(SITE_TIME_ZONE,'Europe/Madrid');
assert.equal(siteCivilDate('2026-01-01T23:30:00Z'),'2026-01-02','CET boundary');
assert.equal(siteCivilDate('2026-07-01T22:30:00Z'),'2026-07-02','CEST boundary');
assert.equal(siteCivilDate('2026-07-01T21:30:00Z'),'2026-07-01','CEST pre-boundary');
assert.equal(siteCivilDate('2026-03-29T00:30:00Z'),'2026-03-29','DST spring day remains stable');
assert.equal(siteCivilDate('2026-10-25T00:30:00Z'),'2026-10-25','DST autumn day remains stable');
assert.equal(siteCivilDate('not-a-date'),null,'invalid instant');
console.log('PASS JS site civil clock: Europe/Madrid across CET/CEST and DST boundaries');
