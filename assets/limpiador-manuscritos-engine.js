(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ManuscriptCleaner = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // Cada regla es una transformacion de higiene de manuscrito ampliamente
  // reconocida (no una decision de estilo discutible): normaliza artefactos
  // habituales de pegar desde Word/Google Docs/WhatsApp, no reescribe prosa.
  // Cada regla es independiente, deterministica y cuenta cuantas veces se
  // aplico, para que el usuario pueda verificar el resultado antes de fiarse.
  const RULES = [
    {
      id: 'trailingSpaces',
      label: 'Espacios al final de línea',
      apply(text) {
        let n = 0;
        const out = text.replace(/[ \t]+(?=\r?\n|$)/g, () => { n += 1; return ''; });
        return { text: out, count: n };
      },
    },
    {
      id: 'doubleSpaces',
      label: 'Espacios dobles o múltiples entre palabras',
      apply(text) {
        let n = 0;
        const out = text.replace(/([^\S\r\n]){2,}/g, (m) => { n += 1; return ' '; });
        return { text: out, count: n };
      },
    },
    {
      id: 'tabs',
      label: 'Tabulaciones convertidas a espacio simple',
      apply(text) {
        let n = 0;
        const out = text.replace(/\t/g, () => { n += 1; return ' '; });
        return { text: out, count: n };
      },
    },
    {
      id: 'nbsp',
      label: 'Espacios no separables (pegados desde web) a espacio normal',
      apply(text) {
        let n = 0;
        const out = text.replace(/\u00A0/g, () => { n += 1; return ' '; });
        return { text: out, count: n };
      },
    },
    {
      id: 'blankLines',
      label: 'Más de una línea en blanco consecutiva',
      apply(text) {
        let n = 0;
        const out = text.replace(/\n{3,}/g, () => { n += 1; return '\n\n'; });
        return { text: out, count: n };
      },
    },
    {
      id: 'spaceBeforePunct',
      label: 'Espacio antes de , . ; : ! ?',
      apply(text) {
        let n = 0;
        const out = text.replace(/[ \t]+([,.;:!?])/g, (m, p) => { n += 1; return p; });
        return { text: out, count: n };
      },
    },
    {
      id: 'straightQuotes',
      label: 'Comillas rectas dobles (") a comillas españolas «»',
      apply(text) {
        let n = 0;
        let open = true;
        const out = text.replace(/"/g, () => {
          n += 1;
          const ch = open ? '«' : '»';
          open = !open;
          return ch;
        });
        return { text: out, count: n };
      },
    },
    {
      id: 'dashDialogue',
      label: 'Guion simple («- Dijo») a raya de diálogo («— Dijo»)',
      apply(text) {
        let n = 0;
        const out = text.replace(/(^|\n)[ \t]*-[ \t]+(?=\S)/g, (m, pre) => { n += 1; return `${pre}— `; });
        return { text: out, count: n };
      },
    },
    {
      id: 'ellipsis',
      label: 'Cuatro puntos o más a puntos suspensivos (...)',
      apply(text) {
        let n = 0;
        const out = text.replace(/\.{4,}/g, () => { n += 1; return '...'; });
        return { text: out, count: n };
      },
    },
  ];

  function ruleIds() {
    return RULES.map(r => r.id);
  }

  function ruleList() {
    return RULES.map(r => ({ id: r.id, label: r.label }));
  }

  // enabled: Set/array de ids activos, o null/undefined para aplicar todos.
  function clean(text, enabled) {
    const activeIds = enabled ? new Set(enabled) : null;
    let current = String(text ?? '');
    const applied = [];
    for (const rule of RULES) {
      if (activeIds && !activeIds.has(rule.id)) continue;
      const result = rule.apply(current);
      current = result.text;
      applied.push({ id: rule.id, label: rule.label, count: result.count });
    }
    const totalChanges = applied.reduce((sum, r) => sum + r.count, 0);
    return { text: current, applied, totalChanges };
  }

  return { RULES: ruleList(), ruleIds, clean };
});
