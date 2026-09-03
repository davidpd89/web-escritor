import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const api = require('../assets/limpiador-manuscritos-engine.js');
function ok(cond, msg) { if (!cond) throw new Error(msg); }

// Todas las reglas activas por defecto (sin segundo argumento).
{
  const input = 'Hola   mundo.\t\nEsto  tiene   espacios al final.   \n\n\n\nY una línea nueva de más.';
  const r = api.clean(input);
  ok(!r.text.includes('   '), 'no deben quedar espacios múltiples');
  ok(!/\n{3,}/.test(r.text), 'no deben quedar 3+ saltos de línea seguidos');
  ok(r.totalChanges > 0, 'debe reportar cambios totales > 0');
}

// Espacio antes de puntuación.
{
  const r = api.clean('Hola ,  mundo !', ['spaceBeforePunct', 'doubleSpaces']);
  ok(r.text.includes('Hola,'), `esperado "Hola," en "${r.text}"`);
}

// Comillas rectas a comillas españolas, alternando apertura/cierre.
{
  const r = api.clean('Dijo "hola" y luego "adiós".', ['straightQuotes']);
  ok(r.text === 'Dijo «hola» y luego «adiós».', `obtenido: ${r.text}`);
}

// Marca de pulgadas (6" de alto) tras un dígito: no es diálogo, debe quedar
// intacta en lugar de consumir un turno de apertura/cierre.
{
  const r = api.clean('Medía 6" de alto.', ['straightQuotes']);
  ok(r.text === 'Medía 6" de alto.', `la comilla tras dígito no debe convertirse: obtenido "${r.text}"`);
}

// Auditoría de casos límite de diálogo en español (2026-09): una comilla
// suelta (marca de pulgadas u otro origen) en un párrafo NO debe invertir la
// apertura/cierre de los diálogos de los párrafos SIGUIENTES -- confirmado en
// vivo antes de este fix: "hola"/"adiós" en el segundo párrafo se convertían
// en »hola«/»adiós« (invertido) por una comilla de pulgadas en el primero.
{
  const input = 'Medía 6" de alto.\n\nElla dijo "hola" y él respondió "adiós".';
  const r = api.clean(input, ['straightQuotes']);
  ok(r.text === 'Medía 6" de alto.\n\nElla dijo «hola» y él respondió «adiós».', `obtenido: ${JSON.stringify(r.text)}`);
}

// La misma contención debe aplicarse a una comilla suelta que NO es una
// marca de pulgadas (un typo, o un artefacto de copiar/pegar): el error debe
// quedar contenido en su propio párrafo, no propagarse al resto del texto.
{
  const input = 'Un texto raro con una comilla suelta " aquí.\n\nElla dijo "hola" y él "adiós".';
  const r = api.clean(input, ['straightQuotes']);
  ok(r.text.endsWith('Ella dijo «hola» y él «adiós».'), `el segundo párrafo debe quedar bien formado: obtenido "${r.text}"`);
}

// Guion de diálogo a raya larga, solo al inicio de línea.
{
  const r = api.clean('- Hola, dijo Ana.\nTexto normal - con guion en medio.', ['dashDialogue']);
  ok(r.text.startsWith('— Hola'), `esperado inicio "— Hola" en "${r.text}"`);
  ok(r.text.includes('Texto normal - con guion en medio.'), 'el guion en medio de línea no debe tocarse');
}

// Guion de diálogo sin espacio tras el guion (la forma más común al escribir raya de diálogo).
{
  const r = api.clean('-Hola, dijo Ana.\n-Adiós, dijo Juan.', ['dashDialogue']);
  ok(r.text.startsWith('— Hola'), `esperado inicio "— Hola" en "${r.text}"`);
  ok(r.text.includes('\n— Adiós'), `esperado "— Adiós" tras salto de línea en "${r.text}"`);
}

// Puntos suspensivos: 4+ puntos -> exactamente 3.
{
  const r = api.clean('Esperaba....', ['ellipsis']);
  ok(r.text === 'Esperaba...', `obtenido: ${r.text}`);
}

// Espacio no separable (NBSP) -> espacio normal.
{
  const r = api.clean('Palabra\u00A0pegada', ['nbsp']);
  ok(r.text === 'Palabra pegada', `obtenido: ${JSON.stringify(r.text)}`);
}

// Selección vacía de reglas: no cambia nada.
{
  const input = 'Texto   con   espacios.';
  const r = api.clean(input, []);
  ok(r.text === input, 'sin reglas activas el texto no debe cambiar');
  ok(r.totalChanges === 0, 'sin reglas activas totalChanges debe ser 0');
}

// Cada regla reporta su propio contador de aplicaciones.
{
  const r = api.clean('a  b   c    d', ['doubleSpaces']);
  const rule = r.applied.find(x => x.id === 'doubleSpaces');
  ok(rule && rule.count === 3, `esperado count=3 para doubleSpaces, obtenido ${rule && rule.count}`);
}

// RULES expone id+label para poblar la UI de checkboxes.
{
  ok(Array.isArray(api.RULES) && api.RULES.length >= 8, 'RULES debe listar al menos 8 reglas');
  ok(api.RULES.every(r => r.id && r.label), 'cada regla debe tener id y label');
}

console.log('tests/test-limpiador-manuscritos: OK');
