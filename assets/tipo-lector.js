(() => {
  'use strict';
  const app = document.querySelector('[data-quiz-app]'); if (!app || !window.ReaderTypeQuiz) return;
  const form = app.querySelector('[data-quiz-form]'), questionsBox = form.querySelector('[data-quiz-questions]'), status = form.querySelector('[data-quiz-status]'), restart = form.querySelector('[data-quiz-restart]');
  const results = app.querySelector('[data-quiz-results]'), resultCard = app.querySelector('[data-quiz-result-card]'), breakdown = app.querySelector('[data-quiz-breakdown]');

  window.ReaderTypeQuiz.QUESTIONS.forEach((q, qi) => {
    const fieldset = document.createElement('fieldset'); fieldset.className = 'quiz-question';
    const legend = document.createElement('legend'); legend.textContent = `${qi + 1}. ${q.prompt}`;
    fieldset.appendChild(legend);
    const list = document.createElement('ul'); list.className = 'quiz-options';
    q.options.forEach(opt => {
      const li = document.createElement('li');
      const label = document.createElement('label'); label.className = 'quiz-option';
      const input = document.createElement('input'); input.type = 'radio'; input.name = q.id; input.value = opt.id; input.required = true;
      label.append(input, document.createTextNode(opt.label));
      li.appendChild(label); list.appendChild(li);
    });
    fieldset.appendChild(list);
    questionsBox.appendChild(fieldset);
  });

  function collectAnswers() {
    const answers = {};
    window.ReaderTypeQuiz.QUESTIONS.forEach(q => {
      const checked = form.querySelector(`input[name="${q.id}"]:checked`);
      if (checked) answers[q.id] = checked.value;
    });
    return answers;
  }

  function render(result) {
    const top = window.ReaderTypeQuiz.profileById(result.top);
    resultCard.replaceChildren();
    const eyebrow = document.createElement('p'); eyebrow.textContent = 'Tu perfil de lectura';
    const h3 = document.createElement('h3'); h3.textContent = top.name;
    const desc = document.createElement('div'); desc.textContent = top.description;
    resultCard.append(eyebrow, h3, desc);

    breakdown.replaceChildren();
    result.ranked.forEach(profileId => {
      const profile = window.ReaderTypeQuiz.profileById(profileId);
      const li = document.createElement('li');
      const row = document.createElement('div');
      const strong = document.createElement('strong'); strong.textContent = profile.name;
      const span = document.createElement('span'); span.textContent = `${result.scores[profileId]} / ${window.ReaderTypeQuiz.QUESTIONS.length}`;
      row.append(strong, span); li.appendChild(row); breakdown.appendChild(li);
    });

    results.hidden = false; restart.hidden = false;
    status.textContent = `Resultado calculado a partir de tus 6 respuestas. No se ha enviado ningún dato.`;
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const answers = collectAnswers();
    const result = window.ReaderTypeQuiz.score(answers);
    if (result.errors.length) {
      results.hidden = true;
      status.textContent = 'Responde todas las preguntas para ver tu resultado.';
      const firstUnanswered = window.ReaderTypeQuiz.QUESTIONS.find(q => !answers[q.id]);
      if (firstUnanswered) {
        const field = form.querySelector(`input[name="${firstUnanswered.id}"]`);
        field?.closest('.quiz-question')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }
    render(result);
  });

  restart.addEventListener('click', () => {
    form.reset();
    results.hidden = true;
    restart.hidden = true;
    status.textContent = 'Responde las 6 preguntas y pulsa «Ver mi resultado».';
    questionsBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
})();
