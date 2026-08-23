(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ReaderTypeQuiz = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // El orden de este array es tambien el criterio de desempate (P.1):
  // ante un empate de puntuacion, gana el perfil que aparece antes aqui.
  // Es una regla fija y documentada, no un desempate aleatorio ni oculto.
  const PROFILES = [
    { id: 'detector-pistas', name: 'Detector de pistas', description: 'Lees buscando la pieza que no encaja: relees frases, anotas contradicciones y disfrutas reconstruyendo lo que el texto no dice del todo.' },
    { id: 'explorador-mundos', name: 'Explorador de mundos', description: 'Lo que más te engancha es el lugar: geografía, reglas propias, historia y detalle sensorial de un mundo que puedas habitar mentalmente.' },
    { id: 'lector-personajes', name: 'Lector de personajes', description: 'Sigues personas, no tramas: te importa por qué alguien actúa así, y sigues leyendo por ellos aunque la trama vaya despacio.' },
    { id: 'lector-ritmo', name: 'Lector de ritmo', description: 'Te mueve el pulso de la lectura: capítulos cortos, tensión creciente, ganas de saber qué pasa después ya.' },
    { id: 'lector-emocional', name: 'Lector emocional', description: 'Buscas que un libro te remueva: una escena que te encoja el pecho vale más que una vuelta de trama ingeniosa.' },
    { id: 'lector-estilo', name: 'Lector de estilo', description: 'Te fijas en cómo está escrito: el ritmo de una frase, una imagen concreta, una estructura narrativa poco habitual.' },
  ];

  // Cada pregunta ofrece exactamente una opcion por perfil (6), para que la
  // puntuacion sea simetrica y facil de razonar: elegir siempre la opcion
  // del mismo perfil produce la puntuacion maxima para ese perfil.
  const QUESTIONS = [
    {
      id: 'q1',
      prompt: 'Empiezas un libro nuevo. ¿Qué te hace seguir después del primer capítulo?',
      options: [
        { id: 'q1-a', profile: 'detector-pistas', label: 'Un detalle que no cuadra y quiero saber por qué.' },
        { id: 'q1-b', profile: 'explorador-mundos', label: 'Un lugar que quiero seguir explorando.' },
        { id: 'q1-c', profile: 'lector-personajes', label: 'Un personaje cuya cabeza quiero seguir viendo por dentro.' },
        { id: 'q1-d', profile: 'lector-ritmo', label: 'Un final de capítulo que me deja con ganas de más.' },
        { id: 'q1-e', profile: 'lector-emocional', label: 'Una escena que ya me ha afectado emocionalmente.' },
        { id: 'q1-f', profile: 'lector-estilo', label: 'Una frase o una voz narrativa que me ha sorprendido.' },
      ],
    },
    {
      id: 'q2',
      prompt: 'En una reunión de club de lectura, ¿de qué hablas primero?',
      options: [
        { id: 'q2-a', profile: 'detector-pistas', label: 'De la pista que se me escapó y que sí encajaba.' },
        { id: 'q2-b', profile: 'explorador-mundos', label: 'De cómo estaba construido el mundo o el escenario.' },
        { id: 'q2-c', profile: 'lector-personajes', label: 'De si un personaje tomó la decisión correcta.' },
        { id: 'q2-d', profile: 'lector-ritmo', label: 'De en qué punto no pude parar de leer.' },
        { id: 'q2-e', profile: 'lector-emocional', label: 'De la escena que más me afectó.' },
        { id: 'q2-f', profile: 'lector-estilo', label: 'De una frase o recurso narrativo concreto.' },
      ],
    },
    {
      id: 'q3',
      prompt: '¿Qué tipo de final te deja más satisfecho?',
      options: [
        { id: 'q3-a', profile: 'detector-pistas', label: 'Uno que resignifica todo lo anterior si lo relees.' },
        { id: 'q3-b', profile: 'explorador-mundos', label: 'Uno que deja el mundo abierto a seguir explorándolo.' },
        { id: 'q3-c', profile: 'lector-personajes', label: 'Uno coherente con quién es de verdad el personaje.' },
        { id: 'q3-d', profile: 'lector-ritmo', label: 'Uno con una recta final que no puedes dejar de leer.' },
        { id: 'q3-e', profile: 'lector-emocional', label: 'Uno que te deja con un nudo en la garganta.' },
        { id: 'q3-f', profile: 'lector-estilo', label: 'Uno resuelto con una imagen o frase memorable.' },
      ],
    },
    {
      id: 'q4',
      prompt: 'Cuando relees un libro que te gustó, ¿qué buscas la segunda vez?',
      options: [
        { id: 'q4-a', profile: 'detector-pistas', label: 'Las pistas que dejé pasar la primera vez.' },
        { id: 'q4-b', profile: 'explorador-mundos', label: 'Detalles del mundo que no había notado.' },
        { id: 'q4-c', profile: 'lector-personajes', label: 'Momentos que explican mejor a un personaje.' },
        { id: 'q4-d', profile: 'lector-ritmo', label: 'Las partes que más rápido leí, para disfrutarlas otra vez.' },
        { id: 'q4-e', profile: 'lector-emocional', label: 'La escena que más me emocionó.' },
        { id: 'q4-f', profile: 'lector-estilo', label: 'Cómo está construida una frase o un capítulo.' },
      ],
    },
    {
      id: 'q5',
      prompt: '¿Qué reseña negativa te haría dudar más de leer un libro?',
      options: [
        { id: 'q5-a', profile: 'detector-pistas', label: '"El misterio es previsible desde la mitad."' },
        { id: 'q5-b', profile: 'explorador-mundos', label: '"El mundo apenas está desarrollado."' },
        { id: 'q5-c', profile: 'lector-personajes', label: '"Los personajes no tienen motivaciones creíbles."' },
        { id: 'q5-d', profile: 'lector-ritmo', label: '"Tiene un ritmo muy lento a mitad de libro."' },
        { id: 'q5-e', profile: 'lector-emocional', label: '"Es frío, no conecta emocionalmente."' },
        { id: 'q5-f', profile: 'lector-estilo', label: '"La prosa es plana, sin ninguna voz propia."' },
      ],
    },
    {
      id: 'q6',
      prompt: 'Si pudieras hablar cinco minutos con el autor, ¿qué le preguntarías?',
      options: [
        { id: 'q6-a', profile: 'detector-pistas', label: 'Si planeó cada pista desde el principio.' },
        { id: 'q6-b', profile: 'explorador-mundos', label: 'Cómo construyó las reglas de ese mundo.' },
        { id: 'q6-c', profile: 'lector-personajes', label: 'En qué se inspiró para un personaje concreto.' },
        { id: 'q6-d', profile: 'lector-ritmo', label: 'Cómo decidió dónde cortar cada capítulo.' },
        { id: 'q6-e', profile: 'lector-emocional', label: 'Si esa escena también le afectó a él o ella al escribirla.' },
        { id: 'q6-f', profile: 'lector-estilo', label: 'Cómo llegó a esa forma de escribir las frases.' },
      ],
    },
  ];

  function profileById(id) {
    return PROFILES.find(p => p.id === id) || null;
  }

  function questionById(id) {
    return QUESTIONS.find(q => q.id === id) || null;
  }

  // answers: { [questionId]: optionId }
  function score(answers) {
    const scores = {};
    PROFILES.forEach(p => { scores[p.id] = 0; });
    const errors = [];

    QUESTIONS.forEach(q => {
      const chosenOptionId = answers ? answers[q.id] : undefined;
      if (!chosenOptionId) { errors.push(`Falta respuesta para «${q.id}».`); return; }
      const option = q.options.find(o => o.id === chosenOptionId);
      if (!option) { errors.push(`Opción desconocida «${chosenOptionId}» para «${q.id}».`); return; }
      scores[option.profile] += 1;
    });

    if (errors.length) return { errors, scores: null, ranked: null, top: null };

    // Desempate determinista: puntuacion desc, y en empate, el orden fijo
    // de PROFILES (indexOf), nunca Math.random ni orden de insercion del
    // objeto de puntuaciones.
    const ranked = PROFILES
      .map(p => p.id)
      .sort((a, b) => {
        if (scores[b] !== scores[a]) return scores[b] - scores[a];
        return PROFILES.findIndex(p => p.id === a) - PROFILES.findIndex(p => p.id === b);
      });

    return { errors: [], scores, ranked, top: ranked[0] };
  }

  return { PROFILES, QUESTIONS, profileById, questionById, score };
});
