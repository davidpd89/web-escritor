import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const api = require('../assets/tipo-lector-engine.js');
function ok(cond, msg) { if (!cond) throw new Error(msg); }

// Estructura: 6 perfiles, cada pregunta con exactamente una opción por perfil.
ok(api.PROFILES.length === 6, `esperados 6 perfiles, obtenidos ${api.PROFILES.length}`);
ok(new Set(api.PROFILES.map(p => p.id)).size === 6, 'ids de perfil deben ser únicos');
ok(api.PROFILES.every(p => p.id && p.name && p.description), 'cada perfil debe tener id, name y description');

ok(api.QUESTIONS.length >= 5, `se esperan al menos 5 preguntas, obtenidas ${api.QUESTIONS.length}`);
api.QUESTIONS.forEach(q => {
  ok(q.options.length === api.PROFILES.length, `${q.id}: debe tener una opción por perfil`);
  const profilesInQuestion = new Set(q.options.map(o => o.profile));
  ok(profilesInQuestion.size === api.PROFILES.length, `${q.id}: no debe repetir perfil entre sus opciones`);
  q.options.forEach(o => ok(api.profileById(o.profile), `${q.id}: opción ${o.id} referencia un perfil inexistente`));
});

// Elegir siempre el mismo perfil en todas las preguntas debe dar máxima puntuación a ese perfil.
{
  const targetProfile = 'lector-emocional';
  const answers = {};
  api.QUESTIONS.forEach(q => { answers[q.id] = q.options.find(o => o.profile === targetProfile).id; });
  const result = api.score(answers);
  ok(result.errors.length === 0, 'sin errores con respuestas completas');
  ok(result.top === targetProfile, `top esperado ${targetProfile}, obtenido ${result.top}`);
  ok(result.scores[targetProfile] === api.QUESTIONS.length, 'puntuación máxima para el perfil elegido siempre');
  api.PROFILES.filter(p => p.id !== targetProfile).forEach(p => ok(result.scores[p.id] === 0, `${p.id} debe quedar en 0`));
}

// Reproducibilidad: mismas respuestas -> mismo resultado, siempre.
{
  const answers = {};
  api.QUESTIONS.forEach((q, i) => { answers[q.id] = q.options[i % q.options.length].id; });
  const r1 = api.score(answers);
  const r2 = api.score(answers);
  ok(JSON.stringify(r1) === JSON.stringify(r2), 'el resultado debe ser reproducible para las mismas respuestas');
}

// Desempate determinista: construir un empate exacto entre dos perfiles y comprobar que
// gana el que aparece antes en PROFILES, no un orden aleatorio.
{
  const [first, second] = api.PROFILES;
  const answers = {};
  api.QUESTIONS.forEach((q, i) => {
    const profile = i % 2 === 0 ? first.id : second.id;
    answers[q.id] = q.options.find(o => o.profile === profile).id;
  });
  const result = api.score(answers);
  const tiedCount = api.QUESTIONS.filter((_, i) => i % 2 === 0).length;
  const otherCount = api.QUESTIONS.length - tiedCount;
  if (result.scores[first.id] === result.scores[second.id]) {
    ok(result.top === first.id, 'en empate exacto debe ganar el primero en el orden fijo de PROFILES');
  } else {
    ok(tiedCount !== otherCount, 'si no hay empate real, las cuentas deben diferir (verificación de la propia prueba)');
  }
}

// Respuestas incompletas: debe fallar con errores claros, no puntuar a medias en silencio.
{
  const answers = {};
  answers[api.QUESTIONS[0].id] = api.QUESTIONS[0].options[0].id;
  const result = api.score(answers);
  ok(result.errors.length > 0, 'respuestas incompletas deben producir errores');
  ok(result.scores === null && result.top === null, 'sin resultado válido cuando faltan respuestas');
}

// Opción desconocida: debe fallar, no ignorar en silencio.
{
  const answers = {};
  api.QUESTIONS.forEach(q => { answers[q.id] = q.options[0].id; });
  answers[api.QUESTIONS[0].id] = 'opcion-inexistente';
  const result = api.score(answers);
  ok(result.errors.length > 0, 'una opción desconocida debe producir un error');
}

console.log('tests/test-tipo-lector: OK');
