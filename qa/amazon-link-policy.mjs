// Clasificación de enlaces a Amazon para auditorías: comercial (afiliado, exige
// sponsored/nofollow) frente a navegación legítima sin compra. Se decide por datos
// reales del enlace (amzn.to, parámetro tag=, fragmento customerReviews, tienda de
// autor), nunca solo por el dominio. Un enlace de compra sin tag sigue exigiendo rel.
const AMAZON_HOST = /(^|\.)amazon\.[a-z]{2,3}(\.[a-z]{2})?$/i;

export function isAmazonHref(href) {
  try {
    const u = new URL(href, 'https://davidportodiaz.com/');
    return u.hostname === 'amzn.to' || AMAZON_HOST.test(u.hostname);
  } catch { return false; }
}

// link: { href, className?, readerReview? }
export function amazonLinkKind(link) {
  if (!isAmazonHref(link.href)) return 'other';
  const u = new URL(link.href, 'https://davidportodiaz.com/');
  if (u.hostname === 'amzn.to') return 'affiliate';
  if ((link.className || '').split(/\s+/).includes('amazon-author-follow-link')) return 'author-follow';
  if (u.searchParams.has('tag')) return 'affiliate';
  if (link.readerReview && u.hash.toLowerCase() === '#customerreviews') return 'reviews';
  return 'unmarked-commercial';
}

// Devuelve true si el enlace incumple la política rel (sponsored o nofollow ausente).
export function amazonLinkViolatesRel(link) {
  const kind = amazonLinkKind(link);
  if (kind === 'other' || kind === 'author-follow' || kind === 'reviews') return false;
  const rel = new Set((link.rel || '').toLowerCase().split(/\s+/));
  return !rel.has('sponsored') && !rel.has('nofollow');
}
