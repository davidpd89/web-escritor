import { foldQuery } from "./assistant-core.mjs";
import { EDITORIAL_PUBLIC_FACTS } from "./editorial-public-facts.mjs";

function includesAny(text, phrases) {
  return phrases.some((phrase) => text.includes(phrase));
}

function words(text) {
  return [...new Set(String(text || "").split(/[^\p{L}\p{N}]+/u).filter(Boolean))];
}

function includesWordFrom(text, candidates) {
  const tokens = new Set(words(text));
  return candidates.some((candidate) => tokens.has(candidate));
}

function boundedEditDistance(left, right, maxDistance = 2) {
  const a = String(left || "");
  const b = String(right || "");
  if (a === b) return 0;
  if (Math.abs(a.length - b.length) > maxDistance) return maxDistance + 1;
  const previous = Array.from({ length: b.length + 1 }, (_, index) => index);
  for (let row = 1; row <= a.length; row += 1) {
    const current = [row];
    let rowMin = row;
    for (let column = 1; column <= b.length; column += 1) {
      const cost = a[row - 1] === b[column - 1] ? 0 : 1;
      const value = Math.min(
        current[column - 1] + 1,
        previous[column] + 1,
        previous[column - 1] + cost,
      );
      current[column] = value;
      rowMin = Math.min(rowMin, value);
    }
    if (rowMin > maxDistance) return maxDistance + 1;
    previous.splice(0, previous.length, ...current);
  }
  return previous[b.length];
}

function entityMatch(text, aliases) {
  const foldedAliases = aliases.map(foldQuery).filter(Boolean);
  if (includesAny(text, foldedAliases)) return true;

  const queryWords = words(text);
  return foldedAliases.some((alias) => {
    if (alias.includes(" ") || alias.length < 5) return false;
    const maxDistance = alias.length >= 8 ? 2 : 1;
    return queryWords.some((token) => token.length >= 5 && boundedEditDistance(token, alias, maxDistance) <= maxDistance);
  });
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

const STARTER_SUGGESTIONS = Object.freeze([
  { label: "Ver los libros", query: "¿Qué libros ha publicado David Porto Díaz?" },
  { label: "Leer un fragmento", query: "¿Dónde puedo leer un fragmento gratis?" },
  { label: "Herramientas", query: "¿Qué herramientas gratuitas hay para escritores?" },
]);

const SITE_SUGGESTIONS = Object.freeze([
  { label: "Obras", query: "Llévame a los libros" },
  { label: "Cuaderno", query: "Quiero ver el Cuaderno" },
  { label: "Herramientas", query: "Quiero ver las herramientas" },
]);

const MANECILLAS_ALIASES = Object.freeze([
  "manecillas",
  "las manecillas del recuerdo",
  "libro de las manecillas",
  "libro del reloj",
  "reloj del recuerdo",
]);

const SAMUEL_ALIASES = Object.freeze([
  "samuel",
  "samuel entre mundos",
  "libro de samuel",
]);

const NOVERIS_ALIASES = Object.freeze([
  "noveris",
  "mundo de samuel",
  "universo de samuel",
]);

const RECOMMENDATION_TERMS = Object.freeze([
  "recomiend",
  "recomendacion",
  "recomendaciones",
  "que leer",
  "que puedo leer",
  "que libros",
  "lecturas",
  "libros parecidos",
  "busco libros",
  "quiero libros",
  "quiero leer",
  "dame lecturas",
]);

const PORTAL_RECOMMENDATION_TERMS = Object.freeze([
  "portal fantasy",
  "fantasia de portales",
  "cruzar a otro mundo",
]);

const MAGIC_COST_RECOMMENDATION_TERMS = Object.freeze([
  "magia con coste",
  "magia tenga un coste",
  "magia tiene un coste",
  "magia con consecuencias",
  "magia que exige un precio",
  "magia exige un precio",
  "usar magia cueste",
  "usar magia cuesta",
  "magia cueste",
  "precio real",
  "precio de la magia",
]);

const READ_TERMS = Object.freeze([
  "fragmento",
  "fragmentos",
  "capitulo",
  "muestra",
  "leer gratis",
  "primeras paginas",
  "primeras páginas",
  "probar",
  "echar un vistazo",
  "leer algo",
]);

const NAVIGATION_TERMS = Object.freeze([
  "donde esta",
  "donde encuentro",
  "como llego",
  "llevame",
  "ir a",
  "abrir",
  "enlace",
  "pagina",
  "seccion",
]);

const EDITORIAL_SUBMISSION_PHRASES = Object.freeze([
  "editorial",
  "editoriales",
  "mandar manuscrito",
  "mandar un manuscrito",
  "mandar mi manuscrito",
  "mando manuscrito",
  "mando un manuscrito",
  "enviar manuscrito",
  "enviar mi manuscrito",
  "enviar novela",
  "enviar mi novela",
  "mandar novela",
  "mandar mi novela",
  "mando novela",
  "publicar manuscrito",
  "publicar novela",
  "presentar obra",
  "presentar mi obra",
  "aceptan manuscritos",
]);

function asksEditorialSubmission(text) {
  if (includesAny(text, EDITORIAL_SUBMISSION_PHRASES)) return true;
  const hasSubmissionAction = includesWordFrom(text, ["mandar", "mando", "enviar", "envio", "publicar", "presentar", "presento"]);
  const hasManuscriptObject = includesWordFrom(text, ["manuscrito", "novela", "obra", "libro", "texto"]);
  return hasSubmissionAction && hasManuscriptObject;
}

function isGreetingOnly(text) {
  return /^(?:hola|buenas|buenos dias|buenas tardes|buenas noches|hey|ey)(?:[ ,.!¡¿?]*(?:que tal|como estas))?[ ,.!¡¿?]*$/u.test(text);
}

function isThanksOnly(text) {
  return /^(?:gracias|muchas gracias|mil gracias|genial,? gracias|perfecto,? gracias|vale,? gracias)[ ,.!¡¿?]*$/u.test(text);
}

function isFarewellOnly(text) {
  return /^(?:adios|hasta luego|hasta pronto|nos vemos|chao|ciao)[ ,.!¡¿?]*$/u.test(text);
}

export function resolveLocalAnswer(query, context = {}) {
  const q = foldQuery(query);
  if (!q) return null;

  // Small talk only wins when the whole turn is social. A prefix such as
  // "Hola, ¿de qué trata Manecillas?" must continue to the real intent.
  if (isGreetingOnly(q)) {
    return result(
      "greeting",
      "Hola. Puedes preguntarme por los libros, fragmentos, artículos, herramientas, editoriales, convocatorias, eventos o información sobre David.",
      [],
      { suggestions: STARTER_SUGGESTIONS },
    );
  }

  if (includesAny(q, ["quien eres", "que puedes hacer", "para que sirves", "como puedes ayudarme", "en que puedes ayudarme", "para que sirve esto"])) {
    return result(
      "capabilities",
      "Sirvo para encontrar contenido dentro de esta web. Puedo responder preguntas breves sobre lo publicado y, si no hay una respuesta exacta, llevarte a la página más útil.",
      [],
      { suggestions: STARTER_SUGGESTIONS },
    );
  }

  if (isThanksOnly(q)) {
    return result(
      "thanks",
      "De nada. Si quieres seguir, dime qué necesitas encontrar y te llevo a la parte adecuada de la web.",
      [],
      { suggestions: STARTER_SUGGESTIONS },
    );
  }

  if (isFarewellOnly(q)) {
    return result("farewell", "Hasta luego. Cuando vuelvas, puedes preguntarme directamente por cualquier parte de la web.", []);
  }

  const mentionsManecillas = entityMatch(q, MANECILLAS_ALIASES);
  const mentionsSamuel = entityMatch(q, SAMUEL_ALIASES);
  const mentionsNoveris = entityMatch(q, NOVERIS_ALIASES);
  const asksFragment = includesAny(q, READ_TERMS);
  const asksNavigation = includesAny(q, NAVIGATION_TERMS);
  const asksAward = includesAny(q, ["premio", "premios", "premiado", "reconocimiento", "reconocimientos", "finalista", "letras como espada", "juan andres", "teno"]);
  const asksRecommendation = includesAny(q, RECOMMENDATION_TERMS);
  const asksPortalRecommendation = asksRecommendation && (
    includesAny(q, PORTAL_RECOMMENDATION_TERMS)
    || (mentionsSamuel && includesAny(q, ["parecidos", "cruzar a otro mundo"]))
  );
  const asksMagicCostRecommendation = asksRecommendation && includesAny(q, MAGIC_COST_RECOMMENDATION_TERMS);

  if (context.pending === "fragment-choice") {
    if (mentionsSamuel || mentionsNoveris || includesAny(q, ["primer capitulo", "capitulo 1"])) {
      return result("samuel-fragment", "Sí. El primer capítulo completo de «Samuel entre mundos» está disponible para leer en la web.", ["samuel-fragment"]);
    }
    if (mentionsManecillas || includesAny(q, ["el del reloj", "el de la memoria"])) {
      return result("manecillas-fragment", "Sí. Hay una página con fragmentos de «Las manecillas del recuerdo». Puedes leerlos aquí antes de ir a la ficha del libro.", ["work-manecillas-fragments"]);
    }
  }

  if (asksFragment && mentionsManecillas) {
    return result("manecillas-fragment", "Sí. Hay una página con fragmentos de «Las manecillas del recuerdo». Puedes leerlos aquí antes de ir a la ficha del libro.", ["work-manecillas-fragments"]);
  }
  if (asksFragment && (mentionsSamuel || mentionsNoveris)) {
    return result("samuel-fragment", "Sí. El primer capítulo completo de «Samuel entre mundos» está disponible para leer en la web.", ["samuel-fragment"]);
  }
  if (asksFragment && !mentionsManecillas && !mentionsSamuel && !mentionsNoveris) {
    return result(
      "fragment-choice",
      "Sí. ¿Quieres leer «Las manecillas del recuerdo» o el primer capítulo de «Samuel entre mundos»?",
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

  if (asksPortalRecommendation) {
    return result(
      "recommendations-portal-fantasy",
      "Si buscas portal fantasy juvenil en español, esta selección reúne diez libros recomendados y explica por qué encaja cada uno.",
      ["recommend-portal-es"],
    );
  }

  if (asksMagicCostRecommendation) {
    return result(
      "recommendations-magic-cost",
      "Si buscas fantasía donde la magia tenga un coste o consecuencias, esta selección reúne seis libros en español centrados precisamente en ese criterio.",
      ["recommend-magic-cost"],
    );
  }

  if (mentionsManecillas && includesAny(q, ["cuando", "fecha", "publica", "sale", "lanzamiento"])) {
    const { manecillas } = EDITORIAL_PUBLIC_FACTS;
    return result("manecillas-date", `La fecha de publicación de «${manecillas.title}» es el ${manecillas.publicationDateHuman}, con ${manecillas.publisher}.`, ["work-manecillas"]);
  }
  if (mentionsManecillas) {
    if (asksNavigation) {
      return result("manecillas", "La página de «Las manecillas del recuerdo» reúne la información principal del libro. Puedes abrirla desde aquí.", ["work-manecillas"]);
    }
    return result("manecillas", "«Las manecillas del recuerdo» es una novela coral sobre el tiempo heredado y la memoria familiar, unida por un reloj que va pasando de mano en mano y adquiere significados distintos en cada vida.", ["work-manecillas"]);
  }

  if ((mentionsSamuel || mentionsNoveris) && asksAward) {
    const { letrasComoEspada, juanAndresTeno } = EDITORIAL_PUBLIC_FACTS.recognitions;
    return result(
      "samuel-awards",
      `No se atribuye a «Samuel entre mundos» el ${letrasComoEspada.result} ${letrasComoEspada.organizer} de ${letrasComoEspada.year}: ese premio pertenece a ${letrasComoEspada.holder} por un certamen de microrrelatos. Tampoco se atribuye al libro la selección ${juanAndresTeno.result} del ${juanAndresTeno.name}, porque la obra presentada no está identificada en la fuente pública oficial localizada.`,
      ["awards", "work-samuel"],
    );
  }
  if (mentionsNoveris) {
    return result("noveris", "Noveris es el mundo fantástico de «Samuel entre mundos». Su guía reúne el universo, las facciones, el sistema mágico y el glosario.", ["samuel-noveris"]);
  }
  if (mentionsSamuel) {
    if (asksNavigation) {
      return result("samuel", "La página de «Samuel entre mundos» reúne la información principal del libro y sus materiales relacionados. Puedes abrirla desde aquí.", ["work-samuel"]);
    }
    return result("samuel", "«Samuel entre mundos» es una novela de fantasía juvenil y portal fantasy: Samuel Osborne descubre su vínculo con Noveris, un mundo donde la magia tiene reglas y exige un coste real.", ["work-samuel"]);
  }

  if (includesAny(q, ["libros ha publicado", "libros tiene", "sus libros", "obras", "novelas", "que libros", "ver los libros", "llevame a los libros", "ir a los libros"])) {
    return result("works", "Puedes empezar por Obras. Allí están «Las manecillas del recuerdo» y «Samuel entre mundos», con acceso a sus páginas y materiales de lectura.", ["works-hub", "work-manecillas", "work-samuel"]);
  }

  if (includesAny(q, ["quien es david", "sobre david", "biografia", "autor", "trayectoria"])) {
    return result("author", "La página de Autor reúne la biografía, trayectoria y obra de David Porto Díaz.", ["author"]);
  }

  if (includesAny(q, ["contactar", "contacto", "email", "correo", "entrevista", "medio", "periodista", "prensa", "kit de prensa", "podcast"])) {
    return result("press", "Para contacto profesional, entrevistas, reseñas o medios, la página de Prensa reúne los materiales y la vía de contacto adecuada.", ["press"]);
  }

  if (includesAny(q, ["evento", "eventos", "firma", "firmas", "feria", "agenda", "presentacion"])) {
    return result("events", "La página de Eventos y firmas reúne las fechas públicas disponibles y su contexto.", ["events"]);
  }

  if (asksAward) {
    return result("awards", "Los premios y reconocimientos están reunidos en una página específica para poder comprobar cada mención con su contexto.", ["awards"]);
  }

  if (asksEditorialSubmission(q)) {
    return result("editorials", "Hay un directorio de editoriales que aceptan manuscritos. Úsalo para localizar opciones y comprobar sus condiciones antes de enviar una obra.", ["editorials-hub"]);
  }

  if (includesAny(q, ["convocatoria", "convocatorias", "concurso", "concursos", "certamen", "certamenes", "premios literarios", "presentar un relato", "presentar relato"])) {
    return result("opportunities", "El directorio de convocatorias reúne concursos, premios y oportunidades para escritores en una sola página.", ["opportunities"]);
  }

  if (includesAny(q, ["herramienta", "herramientas", "revisar texto", "revisar manuscrito", "escribir mejor", "recursos para escritores", "utilidades", "analizar texto", "analizar manuscrito"])) {
    return result("tools", "La sección de Herramientas reúne utilidades gratuitas para revisar texto, estructura y personajes y preparar publicación o materiales editoriales.", ["tools-hub"]);
  }

  if (asksRecommendation) {
    return result("recommendations", "La sección de Recomendaciones organiza lecturas por afinidades, temas y tipos de fantasía.", ["recommendations-hub"]);
  }

  if (includesAny(q, ["cuaderno", "articulo", "articulos", "blog", "escribe sobre", "ver el cuaderno", "ir al cuaderno"])) {
    return result("notebook", "El Cuaderno reúne los artículos y piezas editoriales de la web. Puedes entrar por el índice y seguir por tema.", ["notebook-hub"]);
  }

  if (includesAny(q, [
    "que puedo encontrar",
    "que hay en esta web",
    "por donde empiezo",
    "por donde empezar",
    "no se por donde empezar",
    "orientame",
    "orientar",
    "mapa de la web",
    "mapa del sitio",
    "todos los enlaces",
    "que enlaces",
    "que secciones",
    "secciones de la web",
  ])) {
    return result(
      "site-overview",
      "La web se organiza en cinco territorios principales: Obras, Autor, Cuaderno, Herramientas y Prensa. Si quieres verlo todo de una vez, el Mapa del sitio reúne los destinos públicos; si me dices si vienes a leer, escribir o buscar información sobre David, puedo afinar el camino.",
      ["site-map", "works-hub", "author", "notebook-hub", "tools-hub", "press"],
      { suggestions: SITE_SUGGESTIONS },
    );
  }

  return null;
}
