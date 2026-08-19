import assert from 'node:assert/strict';
import { buildJsonLd, validateInput, scriptTag } from '../assets/jsonld-escritores-core.js';
const book=buildJsonLd('book',{name:'Libro X',url:'https://example.com/libro/',authorName:'Autora',isbn:'123',pages:'272'});
assert.equal(book['@type'],'Book');assert.equal(book.numberOfPages,272);assert.equal(book.publisher,undefined);
const bcheck=validateInput('book',{name:'Libro X',url:'https://example.com/libro/',authorName:'Autora'});assert.equal(bcheck.valid,true);assert.ok(bcheck.info.some(x=>x.includes('rich result')));
const profile=buildJsonLd('profile',{name:'Ana',url:'https://example.com/ana/',sameAs:'https://instagram.com/ana\nhttps://example.org/ana'});assert.equal(profile['@type'],'ProfilePage');assert.equal(profile.mainEntity['@type'],'Person');assert.equal(profile.mainEntity.sameAs.length,2);
const bad=validateInput('event',{name:'Firma',url:'http://example.com',startDate:'2026-09-03'});assert.equal(bad.valid,false);assert.ok(bad.errors.length>=2);
const tag=scriptTag(buildJsonLd('article',{headline:'Título',url:'https://example.com/a',authorName:'Ana',datePublished:'2026-08-17'}));assert.ok(tag.includes('application/ld+json'));assert.ok(tag.includes('Article'));
console.log('tests/test-jsonld-escritores-core: OK');
