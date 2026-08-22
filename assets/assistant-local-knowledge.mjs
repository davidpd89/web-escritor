import { foldQuery } from "./assistant-core.mjs";

function hasAny(text, phrases) {
  return phrases.some((phrase) => text.includes(phrase));
}

function result(intent, answer, sourceIds, options = {}) {
  return {
    intent,
    answer,
    sourceIds,
    confidence: options.confidence || "high",
    pending: options.pending || null,
    suggestions: options.suggestions || [],
  };
}

export function resolveLocalAnswer(query, context = {}) {
  const q = foldQuery(query);
  if (!q) return null;

  if (context.pending === "fragment-choice") {
    if (hasAny(q, ["samuel", "noveris", "primer capitulo", "capitulo 1"])) {
      return result("samuel-fragment", "Sí. Puedes leer gratis el primer capítulo completo de «Samuel entre mundos» desde la web.", ["samuel-fragment"]);
    }
    if (hasAny(q, ["manecillas", "reloj", "memoria"])) {
      return result("manecillas-fragment", "Sí. Hay una página con fragmentos de «Las manecillas del recuerdo» para que puedas probar la lectura.", ["work-manecillas-fragments"]);
    }
  }

  const mentionsManecillas = hasAny(q, ["manecillas", "reloj del recuerdo"]);
  const mentionsSamuel = hasAny(q, ["samuel", "noveris"]);
  const asksFragment = hasAny(q, ["fragmento", "capitulo", "muestra", "leer gratis", "primeras paginas"]);
  const asksAward = hasAny(q, ["premio", "premios", "premiado", "reconocimiento", "reconocimientos", "finalista", "letras como espada", "juan andres", "teno"]);

  if (asksFragment && mentionsManecillas) {
    return result("manecillas-fragment", "Puedes leer varios fragmentos de «Las manecillas del recuerdo» directamente en la web.", ["work-manecillas-fragments"]);
  }
  if (asksFragment && mentionsSamuel) {
    return result("samuel-fragment", "Puedes leer gratis el primer capítulo completo de «Samuel entre mundos» directamente en la web.", ["samuel-fragment"]);
  }
  if (asksFragment && !mentionsManecillas && !mentionsSamuel) {
    return result(
      "fragment-choice",
      "Tengo lectura gratuita de los dos libros. ¿Cuál buscas?",
      ["work-manecillas-fragments", "samuel-fragment"],
      {
        pending: "fragment-choice",
        suggestions: [
          { label: "Las manecillas", query: "Quiero leer un fragmento de Las manecillas del recuerdo" },
          { label: "Samuel", query: "Quiero leer el primer capítulo de Samuel entre mundos" },
        ],
      },
    );
  }

  if (mentionsManecillas && hasAny(q, ["cuando", "fecha", "publica", "sale", "lanzamiento"])) {
    return result("manecillas-date", "La fecha de publicación de «Las manecillas del recuerdo» es el 3 de septiembre de 2026, con Monza Ediciones.", ["work-manecillas"]);
  }
  if (mentionsManecillas) {
    return result("manecillas", "«Las manecillas del recuerdo» es una novela coral sobre el tiempo heredado y la memoria familiar, unida por un reloj que va pasando de mano en mano y adquiere significados distintos en cada vida.", ["work-manecillas"]);
  }

  if (mentionsSamuel && asksAward) {
    return result(
      "samuel-awards",
      "No se atribuye a «Samuel entre mundos» el Primer Premio Letras Como Espada de 2026: ese premio pertenece a David Porto Díaz por un certamen de microrrelatos. Tampoco se atribuye al libro la selección Top 10 — Finalista del I Premio de Literatura Infantil Juan Andrés Teno, porque la obra presentada no está identificada en la fuente pública oficial localizada.",
      ["awards", "work-samuel"],
    );
  }
  if (mentionsSamuel && q.includes("noveris")) {
    return result("noveris", "Noveris es la ciudad fantástica dimensional de «Samuel entre mundos». En su guía puedes explorar el mundo, las facciones, el sistema mágico y el glosario sin necesidad de buscarlo por distintas páginas.", ["samuel-noveris"]);
  }
  if (mentionsSamuel) {
    return result("samuel", "«Samuel entre mundos» es una novela de fantasía juvenil y portal fantasy: Samuel Osborne descubre su vínculo con Noveris, un mundo donde la magia tiene reglas y exige un coste real.", ["work-samuel"]);
  }

  if (hasAny(q, ["libros ha publicado", "libros tiene", "sus libros", "obras", "novelas", "que libros"])) {
    return result("works", "En la web encontrarás las dos obras principales de David Porto Díaz: «Las manecillas del recuerdo», la obra actual, y «Samuel entre mundos», su primera novela publicada.", ["work-manecillas", "work-samuel", "works-hub"]);
  }

  if (hasAny(q, ["quien es david", "sobre david", "biografia", "autor", "trayectoria"])) {
    return result("author", "Puedes consultar la biografía, trayectoria y obra de David Porto Díaz en su página de autor.", ["author"]);
  }

  if (hasAny(q, ["contactar", "contacto", "email", "correo", "entrevista", "medio", "periodista", "prensa", "kit de prensa", "podcast"])) {
    return result("press", "Para entrevistas, medios, reseñas o contacto profesional, la página de Prensa reúne el kit, los materiales y la vía de contacto adecuada.", ["press"]);
  }

  if (hasAny(q, ["evento", "eventos", "firma", "firmas", "feria", "agenda", "presentacion"])) {
    return result("events", "La agenda de Eventos y firmas reúne las apariciones, presentaciones y fechas públicas disponibles en la web.", ["events"]);
  }

  if (asksAward) {
    return result("awards", "Los premios y reconocimientos de David están reunidos en una página específica para poder comprobarlos con su contexto.", ["awards"]);
  }

  if (hasAny(q, ["editorial", "editoriales", "mandar manuscrito", "mandar un manuscrito", "mando manuscrito", "mando un manuscrito", "enviar manuscrito", "enviar novela", "mandar novela", "mando novela", "publicar manuscrito", "publicar novela"])) {
    return result("editorials", "Hay un directorio de editoriales que aceptan manuscritos, pensado para ayudarte a localizar opciones y revisar sus condiciones antes de enviar una obra.", ["editorials-hub"]);
  }

  if (hasAny(q, ["convocatoria", "convocatorias", "concurso", "concursos", "certamen", "certamenes", "premios literarios"])) {
    return result("opportunities", "La web tiene un directorio de convocatorias para escritores con concursos, premios y oportunidades que puedes revisar desde una sola página.", ["opportunities"]);
  }

  if (hasAny(q, ["herramienta", "herramientas", "revisar texto", "revisar manuscrito", "escribir mejor", "recursos para escritores", "utilidades"])) {
    return result("tools", "Sí. Hay herramientas gratuitas para escritores orientadas a revisar texto, estructura y personajes, y también a preparar publicación, promoción y materiales editoriales.", ["tools-hub"]);
  }

  if (hasAny(q, ["recomiend", "recomendacion", "recomendaciones", "que leer", "lecturas parecidas"])) {
    return result("recommendations", "La sección de Recomendaciones reúne selecciones de lectura y artículos para encontrar libros por afinidades, temas y tipos de fantasía.", ["recommendations-hub"]);
  }

  if (hasAny(q, ["cuaderno", "articulo", "articulos", "blog", "escribe sobre"])) {
    return result("notebook", "El Cuaderno reúne los artículos y piezas editoriales de la web: fantasía, escritura, Noveris, lecturas y otros contenidos relacionados.", ["notebook-hub"]);
  }

  if (hasAny(q, ["que puedo encontrar", "que hay en esta web", "ayuda", "por donde empiezo"])) {
    return result("site-overview", "Puedo orientarte entre los libros y fragmentos, el universo de Noveris, artículos, herramientas para escritores, editoriales, convocatorias, eventos, premios y prensa. Dime qué estás buscando y te llevo a la parte adecuada.", ["works-hub", "tools-hub", "notebook-hub"]);
  }

  return null;
}
