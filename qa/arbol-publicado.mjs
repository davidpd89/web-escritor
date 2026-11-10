// El árbol publicado (versionado + generado en disco) para los .mjs. La lista de lo generado vive en un solo
// sitio, scripts/materializar_generados.py; aquí se pregunta a scripts/arbol_publicado.py, que da la misma salida
// que `git ls-files`. Tras el corte de la fase 5, `git ls-files` ya no ve las fichas.
import { execFileSync } from 'node:child_process';
import path from 'node:path';

const PYTHON = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');

export function listarPublicado(root, ...patrones) {
  return execFileSync(PYTHON, [path.join(root, 'scripts', 'arbol_publicado.py'), '-z', '--', ...patrones], {
    cwd: root, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024,
  }).split('\0').filter(Boolean);
}
