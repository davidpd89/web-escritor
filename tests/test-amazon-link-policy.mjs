import assert from 'node:assert/strict';
import test from 'node:test';
import { amazonLinkKind, amazonLinkViolatesRel } from '../qa/amazon-link-policy.mjs';

const reviews = { href: 'https://www.amazon.es/dp/B0GB6LGQFH#customerReviews', rel: 'noopener noreferrer', readerReview: true };

test('enlace de opiniones no es afiliado ni exige sponsored', () => {
  assert.equal(amazonLinkKind(reviews), 'reviews');
  assert.equal(amazonLinkViolatesRel(reviews), false);
});

test('seguimiento de autor no exige sponsored', () => {
  const l = { href: 'https://www.amazon.es/stores/author/B0X', rel: 'noopener', className: 'amazon-author-follow-link' };
  assert.equal(amazonLinkViolatesRel(l), false);
});

test('afiliados correctos pasan y mal configurados fallan', () => {
  const ok = { href: 'https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21', rel: 'sponsored nofollow noopener noreferrer' };
  assert.equal(amazonLinkKind(ok), 'affiliate');
  assert.equal(amazonLinkViolatesRel(ok), false);
  assert.equal(amazonLinkViolatesRel({ ...ok, rel: 'noopener noreferrer' }), true);
  assert.equal(amazonLinkViolatesRel({ href: 'https://amzn.to/abc', rel: 'noopener' }), true);
  assert.equal(amazonLinkViolatesRel({ href: 'https://amzn.to/abc', rel: 'sponsored' }), false);
});

test('enlace de compra sin tag ni clasificación explícita se detecta', () => {
  assert.equal(amazonLinkViolatesRel({ href: 'https://www.amazon.es/dp/B0GB6LGQFH', rel: 'noopener' }), true);
  assert.equal(amazonLinkViolatesRel({ href: 'https://www.amazon.es/s?k=9788498382372', rel: '' }), true);
});

test('customerReviews sin marcador de reseña de lector no se exime ni se camufla un dominio falso', () => {
  assert.equal(amazonLinkViolatesRel({ href: reviews.href, rel: 'noopener' }), true);
  assert.equal(amazonLinkKind({ href: 'https://amazon.es.fake.test/dp/X', rel: '' }), 'other');
});
