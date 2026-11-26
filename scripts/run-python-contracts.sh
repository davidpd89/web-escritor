#!/usr/bin/env bash
# Contratos Python del repositorio, en paralelo (4 a la vez: los vCPU del runner).
#
#   bash scripts/run-python-contracts.sh guion      # tests/test-*.py, un proceso por fichero
#   bash scripts/run-python-contracts.sh subrayado  # tests/test_*.py vía unittest discover (rc 5 = sin tests, vale)
#
# Lo usan la puerta de las PR (required-merge-gate.yml) y main tras cada fusión (main-contratos.yml): las dos corren
# lo mismo, así un main roto por dos PR verdes por separado se ve igual que en la puerta. La línea `FALLA: tests/...`
# (la imprime confirmar_fallos.py) la leen publish-radar-refresh.py (fallo_determinista) y night-autorepair.py: no cambiar su forma.
set -uo pipefail

modo="${1:?uso: run-python-contracts.sh guion|subrayado}"
logs="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/contracts-$modo"
rm -rf "$logs"; mkdir -p "$logs"

case "$modo" in
  guion)
    for f in tests/test-*.py; do
      [ -e "$f" ] || continue
      { python "$f" > "$logs/${f##*/}.log" 2>&1 || echo "$f" >> "$logs/failed"; } &
      while [ "$(jobs -rp | wc -l)" -ge 4 ]; do wait -n; done
    done
    wait
    for f in tests/test-*.py; do
      [ -e "$f" ] || continue
      echo "::group::$f"; cat "$logs/${f##*/}.log"; echo "::endgroup::"
    done
    ;;
  subrayado)
    for f in tests/test_*.py; do
      [ -e "$f" ] || continue
      { rc=0; python -m unittest discover -s tests -p "${f##*/}" > "$logs/${f##*/}.log" 2>&1 || rc=$?; [ "$rc" -eq 0 ] || [ "$rc" -eq 5 ] || echo "$f" >> "$logs/failed"; } &
      while [ "$(jobs -rp | wc -l)" -ge 4 ]; do wait -n; done
    done
    wait
    if [ -s "$logs/failed" ]; then
      while read -r f; do echo "::group::$f"; cat "$logs/${f##*/}.log"; echo "::endgroup::"; done < "$logs/failed"
    fi
    ;;
  *) echo "modo desconocido: $modo" >&2; exit 2 ;;
esac

# Solo es FALLA (fallo determinista: la carga para sin reintentar la puerta) lo que falla dos veces seguidas sobre
# la misma revisión; lo que pasa a la segunda sale como INESTABLE y no tumba el paso (scripts/confirmar_fallos.py).
if [ -s "$logs/failed" ]; then
  [ "$modo" = guion ] && tipo=script || tipo=unittest
  python scripts/confirmar_fallos.py --modo "$tipo" "$logs/failed" || exit 1
fi
echo "$(ls "$logs"/*.log 2>/dev/null | wc -l) ficheros de contratos ($modo) OK"
