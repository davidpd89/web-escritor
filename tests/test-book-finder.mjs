import assert from "node:assert/strict";
import fs from "node:fs";
import { buscar, interpretar, formatear } from "../bots/book-finder.mjs";

const indice = JSON.parse(fs.readFileSync(new URL("../data/bot-books.json", import.meta.url), "utf8"));
const hoy = new Date("2026-11-02");
const titulos = (q, o = {}) => buscar(indice, q, { hoy, ...o }).resultados.map(r => r.libro);

// Interpretación de la frase.
const q1 = interpretar("Busco una novela de ciencia ficción en Kindle de menos de 9,99 €");
assert.deepEqual(q1.categorias, ["ciencia-ficcion"], "«ciencia ficción» no debe activar también divulgación");
assert.equal(q1.formato, "ebook");
assert.equal(q1.precioMax, 999);
assert.equal(interpretar("para mi hija de 9 años").edad, 9);
assert.ok(interpretar("novedades de fantasía").nuevo);
assert.deepEqual(interpretar("neil gaiman").libres, ["neil", "gaiman"]);

// Cada libro del índice tiene lo que necesita el bot.
assert.ok(indice.libros.length > 100, "índice vacío o incompleto: regenerar con scripts/build-bot-index.py");
for (const b of indice.libros) {
  assert.ok(b.titulo && b.web.startsWith("https://davidportodiaz.com/lecturas/#q="), b.id);
  assert.match(b.amazon || "", /^https:\/\/www\.amazon\.es\//, `${b.id} sin enlace de Amazon`);
  for (const f of Object.values(b.formatos)) assert.match(f.url, /tag=davidporto-21/, `${b.id}: enlace sin tag de afiliado`);
}

// Filtros duros: género, formato, precio y edad.
for (const b of titulos("thriller", { limite: 50 })) assert.ok(b.categorias.includes("misterio-y-thriller"), b.titulo);
for (const b of titulos("fantasía en ebook", { limite: 50 })) assert.ok(b.formatos.ebook, b.titulo);
for (const r of buscar(indice, "romántica de menos de 10 euros", { hoy, limite: 50 }).resultados) assert.ok(r.compra.precio <= 1000, r.libro.titulo);
for (const b of titulos("terror para un niño de 10 años", { limite: 50 })) {
  assert.ok(b.categorias.includes("terror"), `${b.titulo}: «terror» es obligatorio aunque también pida infantil`);
  assert.ok(b.edad_min != null && b.edad_min <= 10, b.titulo);
}

// Autor y temas.
assert.deepEqual(titulos("neil gaiman").map(b => b.titulo), ["Coraline"], "autor por palabra exacta (Neill ≠ Neil)");
assert.equal(titulos("un libro que trate de dragones")[0].titulo.includes("dragones"), true);
assert.equal(titulos("qwerty zzz").length, 0);

// Variedad: el top 3 no repite autor si hay alternativas.
const autores = titulos("thriller").map(b => b.autores[0]);
assert.equal(new Set(autores).size, autores.length, `autores repetidos: ${autores}`);

// Respuesta formateada.
const txt = formatear(buscar(indice, "neil gaiman", { hoy }), "neil gaiman");
assert.match(txt, /\*\*1\. Coraline\*\*/);
assert.match(txt, /tag=davidporto-21/);
assert.match(txt, /Enlaces de afiliado/);
assert.match(formatear({ resultados: [], total: 0 }, "zzz"), /No he encontrado nada/);

console.log("test-book-finder: PASS");
