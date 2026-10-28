/* Atlas literario: filtros del catálogo. Mejora progresiva: sin JS se ven todas las entradas. */
(function () {
  'use strict';
  var root = document.querySelector('.atlas-catalogue');
  if (!root) return;
  var form = root.querySelector('[data-atlas-filters]');
  var cards = Array.prototype.slice.call(root.querySelectorAll('[data-atlas-card]'));
  var count = root.querySelector('[data-atlas-count]');
  var empty = root.querySelector('[data-atlas-empty]');
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
    cards.forEach(function (card) {
      var ok = matches(card, state, query, null);
      card.hidden = !ok;
      if (ok) shown += 1;
    });
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
    if (count) count.textContent = shown === 1 ? '1 resultado' : shown + ' resultados';
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

  form.addEventListener('input', apply);
  form.addEventListener('change', apply);
  form.addEventListener('submit', function (event) { event.preventDefault(); apply(); });
  form.addEventListener('reset', function () { window.setTimeout(apply, 0); });
  if (fieldset) fieldset.disabled = false;
  readUrl();
  apply();
})();
