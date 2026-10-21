/* Atlas global search example using the EXISTING Pagefind v1.5.2 index.
 * It does not add an engine, a dependency or a new indexed URL.
 * Do not attach before generated Atlas HTML has data-pagefind-filter
 * and the current build-pagefind-index.py includes the new pages.
 *
 * For illustration on an atlas search panel: call searchAtlas(query, filters)
 * from a user-triggered action, never on every keypress at page load.
 */
let pagefindModulePromise;

export async function searchAtlas(query, {
  country = '',
  city = '',
  workId = '',
  authorId = '',
  relation = '',
  entity = 'place'
} = {}) {
  const text = String(query || '').trim().slice(0, 180);
  if (!text && !country && !city && !workId && !authorId && !relation) {
    return { results: [], unfilteredResultCount: 0 };
  }

  // Shared search corpus. Avoid initializing Pagefind on base page render.
  pagefindModulePromise ||= import('/pagefind/pagefind.js')
    .catch(err => { pagefindModulePromise = null; throw err; });
  const pagefind = await pagefindModulePromise;

  const filters = { atlas_entity: entity };
  if (country) filters.atlas_country = country;
  if (city) filters.atlas_city = city;
  if (workId) filters.atlas_work = workId;
  if (authorId) filters.atlas_author = authorId;
  if (relation) filters.atlas_relation = relation;

  const response = await pagefind.search(text || null, { filters });
  // Deliberately do NOT fetch every result.data() immediately. UI paginates.
  return response;
}

export async function loadAtlasResults(response, first = 0, pageSize = 20) {
  const slice = (response?.results || []).slice(first, first + pageSize);
  const resolved = await Promise.all(slice.map(item => item.data()));
  return resolved.map(item => ({
    title: item.meta?.title || '',
    excerpt: item.excerpt || '',
    url: item.url,
    location: item.meta?.atlas_location || ''
  }));
}

// IMPORTANT: render title/excerpt with a vetted Pagefind-safe renderer. Excerpts
// can include highlight markup; NEVER interpolate provider data into innerHTML.
// This file intentionally returns objects rather than handling DOM or URLs.
