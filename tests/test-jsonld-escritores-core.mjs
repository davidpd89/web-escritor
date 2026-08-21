import assert from 'node:assert/strict';
import { buildJsonLd, validateInput, scriptTag } from '../assets/jsonld-escritores-core.js';

const book=buildJsonLd('book',{name:'Libro X',url:'https://example.com/libro/',authorName:'Autora',isbn:'123',pages:'272'});
assert.equal(book['@type'],'Book');
assert.equal(book.numberOfPages,272);
assert.equal(book.publisher,undefined);
assert.equal(book.inLanguage,undefined, 'no debe inventar idioma si el usuario no lo aporta');

const bcheck=validateInput('book',{name:'Libro X',url:'https://example.com/libro/',authorName:'Autora'});
assert.equal(bcheck.valid,true);
assert.ok(bcheck.info.some(x=>x.includes('rich result')));

const profile=buildJsonLd('profile',{name:'Ana',url:'https://example.com/ana/',sameAs:'https://instagram.com/ana\nhttps://example.org/ana'});
assert.equal(profile['@type'],'ProfilePage');
assert.equal(profile.mainEntity['@type'],'Person');
assert.equal(profile.mainEntity.sameAs.length,2);

for (const invalidUrl of ['http://example.com','https://','https://exa mple.com','javascript:alert(1)']) {
  const check = validateInput('profile',{name:'Ana',url:invalidUrl});
  assert.equal(check.valid,false, `URL inválida aceptada: ${invalidUrl}`);
}
assert.equal(validateInput('profile',{name:'Ana',url:'https://example.com',sameAs:'javascript:alert(1)'}).valid,false);

const article=buildJsonLd('article',{headline:'Título',url:'https://example.com/a',authorName:'Ana',datePublished:'2026-08-17'});
assert.equal(article['@type'],'Article');
assert.equal(article.inLanguage,undefined);
assert.equal(validateInput('article',{headline:'Título',url:'https://example.com/a',authorName:'Ana',datePublished:'2026-02-30'}).valid,false);

const event=buildJsonLd('event',{name:'Firma',url:'https://example.com/firma',startDate:'2026-09-03T18:00'});
assert.equal(event['@type'],'Event');
assert.equal(event.eventStatus,undefined, 'no debe inventar estado');
assert.equal(event.eventAttendanceMode,undefined, 'no debe inventar modalidad');
assert.equal(event.location,undefined, 'no debe inventar lugar');
assert.equal(validateInput('event',{name:'Firma',url:'https://example.com',startDate:'2026-13-40T27:90'}).valid,false);
assert.equal(validateInput('event',{name:'Firma',url:'https://example.com',startDate:'2026-09-03T18:00',endDate:'2026-09-03T17:59'}).valid,false);

const malicious=buildJsonLd('book',{name:'</script><img src=x onerror=alert(1)> & "libro"',url:'https://example.com/libro',authorName:'Ana'});
const tag=scriptTag(malicious);
assert.ok(tag.includes('application/ld+json'));
assert.ok(tag.includes('Book'));
assert.equal(tag.includes('</script><img'), false);
assert.ok(tag.includes('\\u003C/script\\u003E'));
assert.ok(tag.includes('\\u0026'));
const serialized = tag.match(/\n([\s\S]*)\n<\/script>$/)?.[1];
assert.ok(serialized);
assert.doesNotThrow(() => JSON.parse(serialized));

console.log('tests/test-jsonld-escritores-core: OK');
