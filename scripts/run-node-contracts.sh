#!/usr/bin/env bash
# Contratos Node del repositorio (tests/*.mjs), uno tras otro.
#
# Lo usan la puerta de las PR (required-merge-gate.yml) y main tras cada fusión (main-contratos.yml), como
# run-python-contracts.sh: un tests/*.mjs roto en main por dos PR verdes por separado se ve antes de la carga de la
# noche (R5-02 de la revisión GPT, 25/11). confirmar_fallos.py repite los que fallan e imprime `FALLA: tests/...`.
set -uo pipefail

failed="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/node-failed"; : > "$failed"
for f in tests/*.mjs; do
  [ -e "$f" ] || continue
  echo "::group::$f"
  node "$f" || echo "$f" >> "$failed"
  echo "::endgroup::"
done
python scripts/confirmar_fallos.py --modo node "$failed"
