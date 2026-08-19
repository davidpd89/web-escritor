const WARMUPS = [
  'Si tuvieras que presentarte a alguien que no te conoce, ¿qué tres cosas te gustaría que supiera de ti?',
  '¿Cuál es uno de los primeros recuerdos que te viene a la cabeza cuando piensas en tu infancia?',
  '¿Cómo era un día normal en tu casa cuando eras pequeño/a?',
  '¿Qué lugar de tu niñez puedes recorrer todavía de memoria?',
  '¿Quién fue una persona importante para ti cuando crecías y qué recuerdas de ella?',
];

const CLOSINGS = [
  '¿Hay algo importante de tu vida que no te haya preguntado y te gustaría dejar contado?',
  '¿Qué recuerdo te gustaría que nuestra familia no perdiera?',
  'Si alguien de la familia escuchara esta conversación dentro de muchos años, ¿qué te gustaría decirle?',
  '¿Qué te gustaría que se entendiera mejor de la época en la que te tocó vivir?',
];

const FOLLOW_UPS = [
  '¿Cómo era exactamente?',
  '¿Quién estaba allí?',
  '¿Qué pasó después?',
  '¿Cómo te hizo sentir en aquel momento?',
  '¿Qué detalle pequeño recuerdas todavía?',
  '¿Había algún sonido, olor, comida u objeto que asocies con aquello?',
  '¿Cambió algo en tu vida a partir de ese momento?',
  '¿Qué entendiste entonces y qué entiendes ahora de forma distinta?',
];

const OBJECT_PROMPTS = [
  'Mira esta foto u objeto un momento. ¿Qué es lo primero que recuerdas al verlo?',
  '¿De quién era originalmente y cómo llegó a la familia?',
  '¿Dónde solía estar este objeto o dónde se tomó esta foto?',
  '¿Qué historia contarías sobre esto a alguien que no conociera a nuestra familia?',
  '¿Hay algún detalle de esta imagen u objeto que normalmente pase desapercibido?',
];

export const THEMES = {
  infancia: {
    label: 'Infancia y escuela',
    questions: [
      '¿Cómo era la casa en la que creciste y qué rincón recuerdas mejor?',
      '¿A qué jugabais y con quién pasabas más tiempo?',
      '¿Cómo era ir a la escuela en tu época?',
      '¿Qué norma de casa recuerdas especialmente?',
      '¿Qué te hacía ilusión cuando eras niño/a?',
      '¿Qué cosa cotidiana de entonces sorprendería hoy a un niño?',
    ],
  },
  lugares: {
    label: 'Casa, barrio y lugares',
    questions: [
      '¿Cómo era el barrio o pueblo donde vivías y qué ha cambiado más?',
      '¿Qué tienda, plaza, camino o edificio era importante en vuestra vida diaria?',
      '¿Había un lugar al que ibais para celebrar, descansar o encontraros con otros?',
      '¿Qué sitio desaparecido te gustaría poder enseñar hoy?',
      '¿Qué trayecto hacías tantas veces que aún lo recuerdas de memoria?',
    ],
  },
  familia: {
    label: 'Familia y personas',
    questions: [
      '¿Quién reunía a la familia y cómo eran esos encuentros?',
      '¿Qué persona de la familia tenía una forma de ser que todos recuerdan?',
      '¿Qué historias se contaban una y otra vez en casa?',
      '¿Qué aprendiste de tus padres, abuelos u otras personas cercanas sin que te lo enseñaran expresamente?',
      '¿Había alguna costumbre familiar que dabais por normal y ahora te parece especial?',
    ],
  },
  trabajo: {
    label: 'Trabajo y vida cotidiana',
    questions: [
      '¿Cuál fue tu primer trabajo o la primera responsabilidad que recuerdas?',
      '¿Cómo era un día de trabajo normal en aquella época?',
      '¿Qué trabajo invisible se hacía en casa para que todo funcionara?',
      '¿Qué habilidad aprendiste por necesidad y todavía conservas?',
      '¿Qué ha cambiado más en la forma de trabajar desde entonces?',
    ],
  },
  amor: {
    label: 'Amistades, amor y relaciones',
    questions: [
      '¿Cómo conociste a una amistad que haya sido importante en tu vida?',
      '¿Dónde se reunía la gente joven y qué se hacía para divertirse?',
      '¿Cómo se vivían las relaciones de pareja cuando eras joven?',
      '¿Qué amistad te enseñó algo que todavía recuerdas?',
      '¿Qué gesto de cariño era habitual en tu familia aunque no se dijera con palabras?',
    ],
  },
  tradiciones: {
    label: 'Tradiciones, comidas y celebraciones',
    questions: [
      '¿Qué celebración esperabas con más ganas y cómo se preparaba?',
      '¿Qué comida o receta asocias inmediatamente con tu familia?',
      '¿Quién cocinaba aquello y cómo aprendió?',
      '¿Había canciones, dichos, juegos o rituales que se repitieran cada año?',
      '¿Qué tradición se ha perdido y te gustaría recuperar?',
    ],
  },
  migracion: {
    label: 'Mudanzas y migración',
    questions: [
      '¿Recuerdas alguna mudanza o cambio de lugar que marcara a la familia?',
      '¿Qué fue lo más difícil de dejar atrás y qué fue lo primero que ayudó a sentirse en casa?',
      '¿Qué cosas, costumbres o palabras viajaron con vosotros?',
      '¿Cómo se mantenía el contacto con la gente que quedaba lejos?',
      '¿Hubo algo del nuevo lugar que cambiara vuestra forma de vivir?',
    ],
  },
  cambios: {
    label: 'Decisiones y puntos de inflexión',
    questions: [
      '¿Qué decisión cambió tu vida más de lo que imaginabas en aquel momento?',
      '¿Hubo una oportunidad que casi dejaste pasar?',
      '¿Cuándo sentiste por primera vez que estabas entrando en una etapa nueva?',
      '¿Qué decisión tomarías de otra manera con lo que sabes hoy?',
      '¿Qué cambio de tu época te costó entender o aceptar al principio?',
    ],
  },
  sentidos: {
    label: 'Detalles, sonidos y sentidos',
    questions: [
      '¿Qué olor te devuelve inmediatamente a una época de tu vida?',
      '¿Qué sonido cotidiano de entonces ya casi no se escucha?',
      '¿Qué objeto se usaba todos los días y ahora ha desaparecido?',
      '¿Cómo eran las noches, los domingos o las mañanas de invierno en casa?',
      '¿Qué detalle pequeño recuerdas con una claridad que te sorprende?',
    ],
  },
  dificil: {
    label: 'Cambios difíciles y pérdidas',
    sensitive: true,
    questions: [
      'Si te apetece hablar de ello, ¿hubo una etapa difícil que cambiara a la familia?',
      '¿Qué ayudó a seguir adelante cuando las cosas se complicaron?',
      '¿Hay algo de una persona que ya no está que te gustaría que quedara contado?',
      '¿Qué aprendiste de una pérdida o una despedida importante?',
      '¿Hay algún recuerdo de esa etapa que prefieras conservar tal como tú lo cuentas?',
    ],
  },
  futuro: {
    label: 'Aprendizajes y futuro',
    questions: [
      '¿Qué idea sobre la vida has cambiado con los años?',
      '¿Qué consejo recibiste y tardaste mucho tiempo en entender?',
      '¿Qué te gustaría que las generaciones más jóvenes comprendieran de vuestra época?',
      '¿Qué te da orgullo cuando miras atrás?',
      '¿Qué esperas que siga siendo importante en esta familia dentro de muchos años?',
    ],
  },
};


const UNIVERSAL_PROMPTS = [
  '¿Qué momento cotidiano de aquella época te gustaría poder volver a ver durante cinco minutos?',
  '¿Qué cosa que entonces parecía normal hoy resultaría difícil de explicar?',
  '¿Qué aprendiste observando a otras personas, sin que nadie te lo enseñara directamente?',
  '¿Cuál fue una conversación que recuerdas muchos años después?',
  '¿Qué pequeño lujo, premio o capricho tenía mucho valor para ti entonces?',
  '¿Qué noticia o acontecimiento recuerdas haber vivido de una manera especialmente personal?',
  '¿Qué tarea cotidiana se hacía de una forma completamente distinta a la de hoy?',
  '¿Qué recuerdo familiar crees que dos personas contarían de manera diferente?',
  '¿Hubo una época en la que sentiste que todo estaba cambiando muy deprisa?',
  '¿Qué costumbre tuya actual viene de aquellos años aunque casi nunca pienses en ello?',
  '¿Qué pregunta te habría gustado hacer a alguien de una generación anterior y ya no puedes?',
  '¿Qué historia de tu vida suele empezar con «esto ahora parecería increíble, pero…»?',
];

const DURATION_COUNTS = { 15: 6, 30: 10, 45: 14, 60: 18 };

function pick(list, used, rng) {
  const available = list.filter((item) => !used.has(item));
  if (!available.length) return null;
  const index = Math.min(available.length - 1, Math.floor(rng() * available.length));
  const value = available[index];
  used.add(value);
  return value;
}

export function buildInterviewPlan(options = {}, rng = Math.random) {
  const duration = Number(options.duration) || 30;
  const total = DURATION_COUNTS[duration] || DURATION_COUNTS[30];
  const selectedThemes = (options.themes || []).filter((key) => THEMES[key]);
  const themes = selectedThemes.length ? selectedThemes : ['infancia', 'familia', 'sentidos'];
  const used = new Set();
  const questions = [];

  questions.push({ type: 'warmup', theme: 'Para empezar', text: pick(WARMUPS, used, rng) });

  if (options.objectMode) {
    const objectCount = total >= 14 ? 2 : 1;
    for (let i = 0; i < objectCount; i += 1) {
      const text = pick(OBJECT_PROMPTS, used, rng);
      if (text) questions.push({ type: 'object', theme: 'Foto u objeto', text });
    }
  }

  let themeCursor = 0;
  let stalledRounds = 0;
  while (questions.length < total - 1 && stalledRounds < themes.length) {
    const key = themes[themeCursor % themes.length];
    const theme = THEMES[key];
    const text = pick(theme.questions, used, rng);
    if (text) {
      questions.push({ type: 'theme', theme: theme.label, text, sensitive: Boolean(theme.sensitive) });
      stalledRounds = 0;
    } else {
      stalledRounds += 1;
    }
    themeCursor += 1;
  }

  while (questions.length < total - 1) {
    const text = pick(UNIVERSAL_PROMPTS, used, rng);
    if (!text) break;
    questions.push({ type: 'theme', theme: 'Para seguir tirando del hilo', text });
  }

  const closing = pick(CLOSINGS, used, rng) || CLOSINGS[0];
  questions.push({ type: 'closing', theme: 'Para cerrar', text: closing });

  const followUps = [];
  const followUsed = new Set();
  for (let i = 0; i < 4; i += 1) {
    const text = pick(FOLLOW_UPS, followUsed, rng);
    if (text) followUps.push(text);
  }

  return {
    duration,
    questions,
    followUps,
    hasSensitiveTheme: themes.some((key) => THEMES[key]?.sensitive),
    objectMode: Boolean(options.objectMode),
  };
}
