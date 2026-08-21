const BANKS = {
  opening: [
    '¿Qué cambió más tu impresión del libro entre las primeras páginas y el final?',
    'Si tuvieras que explicar en una frase por qué merece la pena hablar de este libro, ¿qué dirías?',
    '¿Qué escena, idea o momento se te quedó encima después de terminar?',
    '¿En qué momento sentiste que entendías qué clase de libro estabas leyendo?',
    '¿Qué expectativa llevabas al empezar y cuál acabó rompiendo el libro?'
  ],
  fiction: [
    '¿Qué decisión de un personaje entendiste aunque no la compartieras?',
    '¿Qué personaje cambia de verdad y cuál solo parece cambiar?',
    '¿Qué relación entre personajes sostiene más historia de la que parece?',
    '¿Qué conflicto habría cambiado por completo si un personaje hubiera dicho una sola cosa a tiempo?',
    '¿Qué información decide ocultar el relato y qué efecto produce en el lector?',
    '¿Qué escena funciona como punto de no retorno, aunque no sea la más espectacular?',
    '¿Dónde notaste más distancia entre lo que un personaje quiere y lo que realmente necesita?',
    '¿Qué personaje interpretaste de forma distinta al resto del grupo y por qué?',
    '¿Qué parte del final estaba preparada desde antes y qué parte te sorprendió de verdad?',
    '¿Qué decisión narrativa volverías a discutir con el autor: punto de vista, estructura, ritmo o cierre?'
  ],
  nonfiction: [
    '¿Cuál es la afirmación central del libro y qué evidencia la sostiene mejor?',
    '¿Qué argumento te resultó convincente y cuál necesitaría más pruebas?',
    '¿Qué presupuestos da por hechos el autor sin discutirlos demasiado?',
    '¿Qué dato o caso cambió más tu forma de pensar sobre el tema?',
    '¿Qué perspectiva relevante queda fuera del libro?',
    '¿Qué parte distingue con claridad hechos, interpretación y opinión? ¿Dónde se mezclan?',
    '¿Qué tendría que ser falso para que la tesis principal perdiera fuerza?',
    '¿Qué idea del libro aplicarías de manera distinta después de esta conversación?',
    '¿A qué lector recomendarías este libro y a cuál no?',
    '¿Qué pregunta importante deja abierta el libro?'
  ],
  personal: [
    '¿Qué parte conectó con una experiencia, miedo, recuerdo o decisión propia?',
    '¿Hubo alguna reacción tuya que te sorprendiera mientras leías?',
    '¿Qué personaje o idea te habría resultado diferente hace cinco años?',
    '¿Qué conversación del libro te gustaría haber escuchado en la vida real?',
    '¿Qué parte te costó más aceptar, no por cómo está escrita sino por lo que plantea?'
  ],
  craft: [
    '¿Qué hace la voz narrativa para acercarte o alejarte de lo que ocurre?',
    '¿Dónde acelera o frena el ritmo y qué gana el libro con ese cambio?',
    '¿Qué escena habría perdido fuerza contada desde otro punto de vista?',
    '¿Qué detalle, objeto o imagen se repite con una función que va cambiando?',
    '¿Qué no explica el autor y funciona mejor precisamente por quedar abierto?',
    '¿Qué parte de la estructura entendiste de otra manera al llegar al final?'
  ],
  disagreement: [
    '¿Qué decisión del libro defenderías aunque sospeches que el resto del grupo no estará de acuerdo?',
    '¿Qué crítica frecuente a este libro te parece injusta o incompleta?',
    '¿Qué personaje merece una lectura más generosa de la que suele recibir?',
    '¿Qué momento admitiría dos interpretaciones opuestas igualmente razonables?',
    'Si tuvieras que eliminar una sola escena o capítulo, ¿cuál elegirías y qué se perdería con ello?'
  ],
  closing: [
    'Después de escuchar al grupo, ¿qué opinión sobre el libro has matizado?',
    '¿Con qué pregunta te vas de la sesión todavía sin resolver?',
    '¿Qué tipo de lector crees ahora que conectaría mejor con este libro?',
    'Si mañana tuvieras que recomendarlo, ¿qué advertencia o matiz añadirías?',
    '¿Qué idea de esta conversación recordarás más que tu primera impresión del libro?'
  ],
  fantasy: [
    '¿Qué regla del mundo fantástico condiciona de verdad las decisiones de los personajes?',
    '¿Qué coste tiene el poder, la magia o la ventaja extraordinaria del mundo?',
    '¿Qué parte del worldbuilding afecta a la historia y cuál funciona sobre todo como atmósfera?',
    '¿Qué institución, tradición o jerarquía del mundo te parece más reveladora de sus valores?'
  ],
  scifi: [
    '¿Qué consecuencia de la premisa especulativa te parece más plausible y cuál menos?',
    '¿La tecnología cambia a las personas o solo amplifica problemas que ya existían?',
    '¿Qué dilema seguiría existiendo aunque quitáramos el elemento de ciencia ficción?',
    '¿Qué norma del mundo futuro refleja mejor una preocupación del presente?'
  ],
  mystery: [
    '¿El libro juega limpio con las pistas o depende de información retenida?',
    '¿Qué sospecha tuviste que resultó equivocada y qué hizo que pareciera razonable?',
    '¿Qué revelación cambia más la lectura de escenas anteriores?',
    '¿El misterio importa más por resolver quién/qué ocurrió o por lo que revela de los personajes?'
  ],
  romance: [
    '¿En qué momento la atracción se convierte en confianza —si llega a hacerlo—?',
    '¿Qué conflicto entre la pareja nace de una diferencia real y cuál de falta de comunicación?',
    '¿La relación cambia a ambos personajes de forma equilibrada?',
    '¿Qué gesto te resultó más convincente que cualquier declaración romántica?'
  ],
  historical: [
    '¿Qué parte del contexto histórico actúa como conflicto y no solo como decorado?',
    '¿Qué perspectiva de la época recibe más espacio y cuál queda en segundo plano?',
    '¿Dónde crees que el libro prioriza verosimilitud narrativa frente a detalle histórico?',
    '¿Qué habría sido imposible para estos personajes en otro momento histórico?'
  ],
  contemporary: [
    '¿Qué norma social cotidiana del libro pasa desapercibida hasta que un personaje la rompe?',
    '¿Qué conflicto reconociste como especialmente contemporáneo?',
    '¿Qué escena podría ocurrir mañana en tu entorno y cuál depende por completo de estos personajes?',
    '¿Qué silencio o malentendido resulta más revelador que una explicación directa?'
  ],
  horror: [
    '¿Qué da más miedo en el libro: lo que se muestra, lo que se insinúa o lo que los personajes imaginan?',
    '¿En qué momento cambia la naturaleza de la amenaza?',
    '¿Qué regla de seguridad parece razonable y termina fallando?',
    '¿El miedo nace más del entorno, de otras personas o del propio protagonista?'
  ],
  memoir: [
    '¿Cómo cambia la distancia entre quien vivió los hechos y quien los narra después?',
    '¿Qué recuerdos parecen construidos alrededor de una interpretación posterior?',
    '¿Qué parte del relato depende especialmente de la confianza que depositamos en la voz autobiográfica?',
    '¿Qué ausencia o silencio del relato te resultó más significativo?'
  ]
};

const ACTIVITIES = {
  social: [
    'Ronda rápida: cada persona elige una escena para enseñársela a alguien que no haya leído el libro y explica por qué.',
    'Semáforo: una decisión del libro que marcarías en verde, una en amarillo y una en rojo.',
    'Reparto imposible: cada participante elige quién defendería a un personaje en una discusión y por qué.'
  ],
  balanced: [
    'Línea de interpretación: puntúa del 1 al 5 cuánto estás de acuerdo con una afirmación polémica del libro y compara razones.',
    'Escena bisagra: elegid una escena cuya eliminación cambiaría más el libro y defended la elección.',
    'Mapa rápido: anotad tres ideas que el libro pone en tensión y trazad qué personajes representan cada una.'
  ],
  deep: [
    'Lectura de contraste: escoged dos escenas que parezcan decir cosas opuestas sobre el mismo tema y discutid la contradicción.',
    'Hipótesis contraria: formulad la interpretación opuesta a la lectura dominante del grupo e intentad sostenerla con el texto.',
    'Cambio de lente: elegid una escena y discutid cómo cambiaría su sentido desde otro punto de vista.'
  ]
};

const ENDING_FOCUSED = /\b(final|terminar|terminaste|acabó|cierre)\b|después de terminar|llegar al final|principio y el final/i;

function isEndingFocused(question) {
  return ENDING_FOCUSED.test(question);
}

function hashString(value) {
  let h = 2166136261;
  for (const ch of String(value)) {
    h ^= ch.codePointAt(0);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function rng(seed) {
  let state = seed || 1;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function shuffle(items, random) {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function parseTokens(raw) {
  return String(raw || '').split(',').map(x => x.trim()).filter(Boolean).slice(0, 4);
}

function customQuestions(tokens, kind) {
  const rows = [];
  for (const token of tokens) {
    rows.push(kind === 'nonfiction'
      ? `¿Cómo trata el libro «${token}»: como hecho, problema, causa, consecuencia o interpretación?`
      : `¿Cómo cambia el significado de «${token}» entre el principio y el final?`);
    rows.push(kind === 'nonfiction'
      ? `¿Qué evidencia o ejemplo del libro ayuda más a discutir «${token}»?`
      : `¿Qué personaje, escena o decisión revela mejor lo que el libro quiere decir sobre «${token}»?`);
  }
  return rows;
}

function minutesFor(duration) {
  if (duration === 30) return { opening: 5, core: 20, close: 5, questions: 5, activity: false };
  if (duration === 90) return { opening: 10, core: 65, close: 15, questions: 10, activity: true };
  return { opening: 8, core: 42, close: 10, questions: 7, activity: true };
}

export function buildSession(config = {}, variant = 0) {
  const title = String(config.title || '').trim();
  const author = String(config.author || '').trim();
  const kind = config.kind === 'nonfiction' ? 'nonfiction' : 'fiction';
  const genre = String(config.genre || 'general');
  const tone = ['social', 'balanced', 'deep'].includes(config.tone) ? config.tone : 'balanced';
  const duration = [30, 60, 90].includes(Number(config.duration)) ? Number(config.duration) : 60;
  const tokens = parseTokens(config.tokens);
  const scope = config.scope === 'partial' ? 'partial' : 'complete';
  const timing = minutesFor(duration);
  const seedBase = JSON.stringify({ title, author, kind, genre, tone, duration, tokens, scope, variant });
  const random = rng(hashString(seedBase));

  const openingPool = scope === 'partial' ? BANKS.opening.filter(q => !isEndingFocused(q)) : BANKS.opening;
  const opening = shuffle(openingPool, random).slice(0, duration === 90 ? 2 : 1);
  let core = [...BANKS[kind]];
  if (BANKS[genre]) core.push(...BANKS[genre]);
  if (tone === 'social') core.push(...BANKS.personal, ...BANKS.personal);
  if (tone === 'balanced') core.push(...BANKS.personal, ...BANKS.craft, ...BANKS.disagreement);
  if (tone === 'deep') core.push(...BANKS.craft, ...BANKS.craft, ...BANKS.disagreement, ...BANKS.disagreement);
  core.push(...customQuestions(tokens, kind));
  if (scope === 'partial') {
    core = core.filter(q => !isEndingFocused(q));
    core.push('Sin anticipar lo que falta por leer, ¿qué preguntas ha abierto el libro hasta este punto?');
  }
  const questions = shuffle([...new Set(core)], random).slice(0, timing.questions);
  const closing = shuffle(BANKS.closing, random).slice(0, duration === 90 ? 2 : 1);
  const activity = timing.activity ? shuffle(ACTIVITIES[tone], random)[0] : null;

  return {
    title,
    author,
    kind,
    genre,
    tone,
    duration,
    scope,
    timing,
    opening,
    questions,
    activity,
    closing,
    facilitator: [
      'Haz preguntas abiertas y deja unos segundos de silencio antes de intervenir.',
      'No conviertas la sesión en un examen ni busques una respuesta correcta.',
      'Invita a hablar a quien participa menos sin obligarle.',
      'Si aparece desacuerdo, pide ejemplos del libro antes de cerrar la interpretación.',
      'Lleva más preguntas de las que esperas usar; abandona las que no estén dando conversación.'
    ]
  };
}