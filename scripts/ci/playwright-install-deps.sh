#!/usr/bin/env bash
# Instala Playwright y sus dependencias del sistema sin que una caída de apt tumbe la QA de navegador.
#   playwright-install-deps.sh deps chromium   (navegador en caché: solo librerías del sistema)
#   playwright-install-deps.sh full chromium   (navegador + librerías)
#
# 11/11/2026: los runners no resolvían azure.archive.ubuntu.com y 11 trabajos de navegador fallaron a la vez
# tras 8 min reintentando apt. apt-ready.sh cambia de espejo o, si no hay ninguno, se salta apt en ~20 s: las
# librerías de Chromium ya vienen en la imagen fijada ubuntu-24.04 (trae Chrome) y la prueba real decide.
set -u
mode=${1:?deps|full}; shift
here=$(dirname "$0")
pause=${PW_DEPS_PAUSE:-30}
limit=${PW_DEPS_TIMEOUT:-300}

case "$mode" in
  deps|full) ;;
  *) echo "modo desconocido: $mode (deps|full)" >&2; exit 2 ;;
esac

if bash "$here/apt-ready.sh"; then
  if [ "$mode" = full ]; then
    timeout "$limit" npx playwright install --with-deps "$@" && exit 0
  else
    timeout "$limit" npx playwright install-deps "$@" && exit 0
  fi
fi

echo "::warning title=apt sin red::No se pudieron instalar las dependencias del sistema de Playwright; se usan las de la imagen del runner."
if [ "$mode" = full ]; then
  # El navegador sale del CDN de Playwright, no de apt: sin él no hay prueba posible.
  for n in 1 2; do
    timeout "$limit" npx playwright install "$@" && exit 0
    [ "$n" -lt 2 ] && sleep "$pause"
  done
  exit 1
fi
exit 0
