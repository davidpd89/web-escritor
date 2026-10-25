/** Public-facing selector for the static v1 social JSON. No network or DOM.
 *
 * The writer preserves last-good JSON if all collectors fail, so a page must
 * not trust stored `status: ok` or an old `totals.follower_relationships`.
 * Use only the publisher's explicit UTC expiration for each metric.
 */
const NETWORKS = ['bluesky', 'mastodon', 'threads', 'instagram', 'tiktok', 'pinterest'];
const SOURCES = {
  bluesky: 'bluesky-public-appview',
  mastodon: 'mastodon-public-search',
  threads: 'metricool-mcp-export',
  instagram: 'metricool-mcp-export',
  tiktok: 'metricool-mcp-export',
  pinterest: 'metricool-mcp-export',
};
const ISO_UTC = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
const MAX_SNAPSHOT_AGE_MS = 48 * 60 * 60 * 1000; // Same limit as Python publisher.

function instant(value) {
  if (typeof value !== 'string' || !ISO_UTC.test(value)) return null;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) && new Date(parsed).toISOString().slice(0, 19) + 'Z' === value ? parsed : null;
}

/** Return only fresh numbers; never surface profile URLs supplied in JSON. */
export function visibleSocialMetrics(snapshot, nowMs = Date.now()) {
  const absent = {
    networks: NETWORKS.map(id => ({id, followers: null, observed_at: null, status: 'pending'})),
    totals: {follower_relationships: null, coverage: 0, eligible: NETWORKS.length},
  };
  if (!Number.isFinite(nowMs) || !snapshot || typeof snapshot !== 'object' ||
      Array.isArray(snapshot) || snapshot.schema_version !== 1 ||
      !Array.isArray(snapshot.networks)) return absent;

  const generated = instant(snapshot.generated_at);
  if (generated === null || generated > nowMs ||
      nowMs - generated > MAX_SNAPSHOT_AGE_MS) return absent;
  // Never treat a duplicate as two distinct accounts, even in corrupted JSON.
  const seen = new Set();
  const found = new Map();
  for (const row of snapshot.networks) {
    if (!row || typeof row !== 'object' || Array.isArray(row) ||
        !NETWORKS.includes(row.id) || seen.has(row.id)) return absent;
    seen.add(row.id);
    const expires = instant(row.valid_until);
    const observationValue = row.observed_at;
    const isDateOnly = typeof observationValue === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(observationValue);
    const observedMs = isDateOnly
        ? instant(`${observationValue}T00:00:00Z`)
        : instant(observationValue);
    const observed = observedMs !== null ? observationValue : null;
    const usable = row.status === 'ok' && row.source === SOURCES[row.id] &&
        Number.isSafeInteger(row.followers) && row.followers >= 0 &&
        observedMs !== null && observedMs <= generated && observedMs <= nowMs &&
        expires !== null && expires >= nowMs &&
        expires <= generated + MAX_SNAPSHOT_AGE_MS;
    found.set(row.id, {id: row.id, followers: usable ? row.followers : null,
                       observed_at: usable ? observed : null,
                       status: usable ? 'ok' : 'unavailable'});
  }
  const networks = NETWORKS.map(id => found.get(id) ?? {id, followers: null, observed_at: null, status: 'pending'});
  const fresh = networks.filter(row => row.followers !== null);
  const total = fresh.reduce((sum, row) => sum + row.followers, 0);
  return {
    networks,
    totals: {follower_relationships: fresh.length && Number.isSafeInteger(total) ? total : null,
             coverage: fresh.length, eligible: NETWORKS.length},
  };
}
