/* Atlas literario: filtros del catálogo. Mejora progresiva: sin JS se ven todas las entradas. */
(function () {
  'use strict';
  var root = document.querySelector('.atlas-catalogue');
  if (!root) return;
  var form = root.querySelector('[data-atlas-filters]');
  var cards = Array.prototype.slice.call(root.querySelectorAll('[data-atlas-card]'));
  var count = root.querySelector('[data-atlas-count]');
  var empty = root.querySelector('[data-atlas-empty]');
  var moreWrap = root.querySelector('[data-atlas-more-wrap]');
  var more = root.querySelector('[data-atlas-more]');
  var PAGE = 24;
  var limit = PAGE;
  if (!form || !cards.length) return;
  var fieldset = form.querySelector('fieldset');
  var search = form.querySelector('[data-filter="q"]');
  var reset = form.querySelector('button[type="reset"]');
  var groups = Array.prototype.slice.call(form.querySelectorAll('[data-facet-group]'));
  var KEYS = groups.map(function (g) { return g.getAttribute('data-facet-group'); });

  function norm(s) {
    return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  }
  cards.forEach(function (card) { card._search = norm(card.getAttribute('data-search')); });

  function selected() {
    var out = {};
    KEYS.forEach(function (key) {
      out[key] = Array.prototype.slice.call(form.querySelectorAll('input[data-facet="' + key + '"]:checked'))
        .map(function (i) { return i.value; });
    });
    return out;
  }
  function matches(card, state, query, skip) {
    if (query && card._search.indexOf(query) === -1) return false;
    return KEYS.every(function (key) {
      if (key === skip || !state[key].length) return true;
      var values = (card.getAttribute('data-' + key) || '').split(' ').filter(Boolean);
      return state[key].some(function (v) { return values.indexOf(v) !== -1; });
    });
  }
  function apply() {
    var state = selected();
    var query = norm(search ? search.value.trim() : '');
    var shown = 0;
    var shownNow = 0;
    cards.forEach(function (card) {
      var ok = matches(card, state, query, null);
      if (ok) shown += 1;
      var visible = ok && shown <= limit;
      card.hidden = !visible;
      if (visible) shownNow += 1;
    });
    if (moreWrap) moreWrap.hidden = shownNow >= shown;
    groups.forEach(function (group) {
      var key = group.getAttribute('data-facet-group');
      var chosen = state[key].length;
      var badge = group.querySelector('[data-facet-selected]');
      if (badge) badge.textContent = chosen ? '(' + chosen + ')' : '';
      Array.prototype.slice.call(group.querySelectorAll('input[data-facet]')).forEach(function (input) {
        var n = cards.filter(function (card) {
          if (!matches(card, state, query, key)) return false;
          return (card.getAttribute('data-' + key) || '').split(' ').indexOf(input.value) !== -1;
        }).length;
        var small = input.parentNode.querySelector('[data-facet-count]');
        if (small) small.textContent = '(' + n + ')';
        input.disabled = n === 0 && !input.checked;
      });
    });
    if (count) {
      var total = shown === 1 ? '1 resultado' : shown + ' resultados';
      // Tras «Mostrar más» el total no cambia: el estado anuncia cuántas se ven ya.
      if (limit > PAGE && shown > PAGE) total += shownNow >= shown ? ' · se muestran todos' : ' · se muestran ' + shownNow;
      count.textContent = total;
    }
    if (empty) empty.hidden = shown !== 0;
    var dirty = Boolean(query) || KEYS.some(function (key) { return state[key].length; });
    if (reset) reset.disabled = !dirty;
    writeUrl(state, search ? search.value.trim() : '');
  }
  function writeUrl(state, q) {
    try {
      var params = new URLSearchParams();
      if (q) params.set('q', q);
      KEYS.forEach(function (key) { state[key].forEach(function (v) { params.append(key, v); }); });
      var qs = params.toString();
      history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash);
    } catch (e) { /* sin historial: los filtros siguen funcionando */ }
  }
  function readUrl() {
    try {
      var params = new URLSearchParams(location.search);
      if (search && params.get('q')) search.value = params.get('q').slice(0, 200);
      KEYS.forEach(function (key) {
        params.getAll(key).forEach(function (v) {
          var input = form.querySelector('input[data-facet="' + key + '"][value="' + (window.CSS && CSS.escape ? CSS.escape(v) : v) + '"]');
          if (input) { input.checked = true; var d = input.closest('details'); if (d) d.open = true; }
        });
      });
    } catch (e) { /* URL ilegible: se ignora */ }
  }

  function filtered() { limit = PAGE; apply(); }
  form.addEventListener('input', filtered);
  form.addEventListener('change', filtered);
  // Al revelar una tanda, el foco pasa al enlace de la primera entrada nueva,
  // tanto si el botón sigue como si desaparece en la última tanda.
  function showMore() {
    var before = cards.filter(function (card) { return !card.hidden; });
    limit += PAGE;
    apply();
    var first = cards.filter(function (card) { return !card.hidden && before.indexOf(card) === -1; })[0];
    if (!first) return;
    var target = first.querySelector('a[href]');
    if (!target) { first.setAttribute('tabindex', '-1'); target = first; }
    target.focus();
  }
  if (more) more.addEventListener('click', showMore);
  form.addEventListener('submit', function (event) { event.preventDefault(); filtered(); });
  form.addEventListener('reset', function () {
    window.setTimeout(function () {
      filtered();
      // Restablecer se deshabilita a sí mismo: no dejar el foco en un botón inerte.
      var active = document.activeElement;
      if (search && (!active || active === document.body || active === reset)) search.focus();
    }, 0);
  });
  if (fieldset) fieldset.disabled = false;
  readUrl();
  apply();
})();
