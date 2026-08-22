(() => {
  'use strict';

  const app = document.querySelector('[data-samuel-quiz]');
  if (!app) return;

  const QUESTIONS = [
    {
      text: 'Encuentras una puerta que no debería existir. ¿Qué haces?',
      options: [
        { text: 'La cruzo. Tengo que saber qué hay al otro lado.', key: 'mensajero' },
        { text: 'Estudio sus mecanismos antes de decidir nada.', key: 'sabio' },
        { text: 'Me aseguro de que nadie más la cruce.', key: 'silenciadora' },
        { text: 'La protejo. Hay puertas que existen por algo.', key: 'guardian' },
      ],
    },
    {
      text: '¿Cuál es tu mayor defecto?',
      options: [
        { text: 'No sé cuándo parar de buscar.', key: 'mensajero' },
        { text: 'Analizo tanto que a veces no actúo.', key: 'sabio' },
        { text: 'Soy demasiado estricto/a, conmigo y con los demás.', key: 'silenciadora' },
        { text: 'Me cuesta soltar lo que protejo.', key: 'guardian' },
      ],
    },
    {
      text: 'La magia que siempre tiene un precio representa para ti…',
      options: [
        { text: 'Una aventura con consecuencias reales.', key: 'mensajero' },
        { text: 'Un sistema que hay que comprender antes de usar.', key: 'sabio' },
        { text: 'Una responsabilidad que la mayoría ignora.', key: 'silenciadora' },
        { text: 'Una razón para ser cauteloso con el poder.', key: 'guardian' },
      ],
    },
    {
      text: 'Una verdad que podría destruirte: ¿preferirías conocerla o ignorarla?',
      options: [
        { text: 'Conocerla siempre. La incertidumbre es peor.', key: 'mensajero' },
        { text: 'Conocerla, pero en el momento justo.', key: 'sabio' },
        { text: 'Conocerla, para poder actuar en consecuencia.', key: 'silenciadora' },
        { text: 'Depende de cuántas personas proteja esa verdad.', key: 'guardian' },
      ],
    },
    {
      text: '¿Qué te llevarías a Noveris?',
      options: [
        { text: 'Nada. Las manos vacías son más honestas.', key: 'mensajero' },
        { text: 'Un cuaderno donde anotar todo lo que descubra.', key: 'sabio' },
        { text: 'Algo que me recuerde las normas del mundo al que vuelvo.', key: 'silenciadora' },
        { text: 'Algo que pertenezca a alguien que quiero proteger.', key: 'guardian' },
      ],
    },
  ];

  const RESULTS = {
    mensajero: {
      name: 'El Mensajero',
      desc: 'Eres el tipo de habitante que Noveris no esperaba. Curioso hasta el riesgo, incapaz de dejar una pregunta sin responder, cruzarías la barrera aunque todo te dijera que no. Como Samuel, tu fuerza no es la fuerza: es la necesidad de saber. Noveris te necesita aunque no lo sepa todavía.',
    },
    sabio: {
      name: 'El Sabio del Espejo',
      desc: 'Observas más de lo que hablas. El Espejo Ancestral no revela lo que ves: revela lo que eres, y tú llevas tiempo mirándote. En Noveris guardarías el conocimiento como se guarda el fuego — con cuidado, para que no queme lo que no debe. La paciencia es tu poder más subestimado.',
    },
    silenciadora: {
      name: 'La Silenciadora',
      desc: 'Disciplina absoluta. Conoces los costes de la magia mejor que nadie — y te aseguras de que nadie los olvide. En Noveris no eres el villano: eres la consecuencia necesaria. Lo que otros llaman frialdad, tú lo llamas honestidad. Noveris funciona porque hay gente como tú dispuesta a mantener el precio real.',
    },
    guardian: {
      name: 'El Guardián',
      desc: 'Firme, leal, con el peso de lo que cuidas grabado en cada decisión. En Noveris entenderías que la barrera existe por algo y que no todo lo que está al otro lado merece cruzar. Tu fortaleza no está en atacar: está en lo que decides no soltar nunca, cueste lo que cueste.',
    },
  };

  const stage = app.querySelector('[data-quiz-stage]');
  const stepLabel = app.querySelector('[data-quiz-step]');
  const questionText = app.querySelector('[data-quiz-question]');
  const optionsEl = app.querySelector('[data-quiz-options]');
  const resultEl = app.querySelector('[data-quiz-result]');
  const resultName = app.querySelector('[data-quiz-result-name]');
  const resultDesc = app.querySelector('[data-quiz-result-desc]');
  const progressBar = app.querySelector('[data-quiz-progress]');
  const shareBtn = app.querySelector('[data-quiz-share]');
  const restartBtn = app.querySelector('[data-quiz-restart]');
  if (!stage || !stepLabel || !questionText || !optionsEl || !resultEl || !resultName || !resultDesc || !progressBar || !shareBtn || !restartBtn) return;

  let current = 0;
  const scores = { mensajero: 0, sabio: 0, silenciadora: 0, guardian: 0 };

  function shuffled(options) {
    const result = options.slice();
    for (let i = result.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  }

  function focusFirstOption() {
    optionsEl.querySelector('button')?.focus({ preventScroll: true });
  }

  function showQuestion(index, moveFocus = false) {
    const question = QUESTIONS[index];
    stepLabel.textContent = `Pregunta ${index + 1} de ${QUESTIONS.length}`;
    questionText.textContent = question.text;
    progressBar.style.width = `${index / QUESTIONS.length * 100}%`;
    optionsEl.replaceChildren();
    shuffled(question.options).forEach((option) => {
      const button = document.createElement('button');
      button.className = 'quiz-option';
      button.type = 'button';
      button.textContent = option.text;
      button.addEventListener('click', () => choose(option.key));
      optionsEl.append(button);
    });
    if (moveFocus) focusFirstOption();
  }

  function winnerKey() {
    return Object.entries(scores).reduce((winner, candidate) => candidate[1] > winner[1] ? candidate : winner)[0];
  }

  function showResult() {
    progressBar.style.width = '100%';
    stage.hidden = true;
    resultEl.hidden = false;
    const key = winnerKey();
    const result = RESULTS[key];
    resultName.textContent = result.name;
    resultDesc.textContent = result.desc;
    resultEl.dataset.result = key;
    resultEl.focus({ preventScroll: true });
  }

  function choose(key) {
    if (!Object.hasOwn(scores, key) || current >= QUESTIONS.length) return;
    scores[key] += 1;
    current += 1;
    if (current < QUESTIONS.length) showQuestion(current, true);
    else showResult();
  }

  async function shareResult() {
    const result = RESULTS[resultEl.dataset.result];
    if (!result) return;
    const text = `He descubierto mi perfil de Noveris: ${result.name}. Hazlo aquí: https://davidportodiaz.com/libros/samuel-entre-mundos/#quiz-noveris`;
    if (navigator.share) {
      try { await navigator.share({ text }); } catch {}
      return;
    }
    if (!navigator.clipboard?.writeText) return;
    try {
      await navigator.clipboard.writeText(text);
      const original = shareBtn.textContent;
      shareBtn.textContent = '✓ Texto copiado';
      setTimeout(() => { shareBtn.textContent = original; }, 2200);
    } catch {}
  }

  function restart() {
    current = 0;
    Object.keys(scores).forEach((key) => { scores[key] = 0; });
    delete resultEl.dataset.result;
    resultEl.hidden = true;
    stage.hidden = false;
    showQuestion(0, true);
  }

  shareBtn.addEventListener('click', () => { void shareResult(); });
  restartBtn.addEventListener('click', restart);
  showQuestion(0);
})();
