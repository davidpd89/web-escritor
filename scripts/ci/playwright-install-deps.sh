#!/usr/bin/env bash
# Instala Playwright y sus dependencias del sistema sin que una caída de apt tumbe la QA de navegador.
#   playwright-install-deps.sh deps chromium   (navegador en caché: solo librerías del sistema)
#   playwright-install-deps.sh full chromium   (navegador + librerías)
#
# 11/11/2026: los runners no resolvían azure.archive.ubuntu.com y 11 trabajos de navegador fallaron a la vez
# tras 8 min reintentando apt. Las librerías de Chromium ya vienen en la imagen fijada ubuntu-24.04 (trae
# Chrome), así que si apt no tiene red se avisa y se sigue: la prueba real decide, no el espejo de Ubuntu.
set -u
mode=${1:?deps|full}; shift
pause=${PW_DEPS_PAUSE:-30}
limit=${PW_DEPS_TIMEOUT:-420}

apt_has_network() {
  for n in 1 2 3 4; do
    for host in azure.archive.ubuntu.com archive.ubuntu.com security.ubuntu.com; do
      getent hosts "$host" >/dev/null 2>&1 && return 0
    done
    [ "$n" -lt 4 ] && sleep "$pause"
  done
  return 1
}

attempt() {
  for n in 1 2; do
    timeout "$limit" "$@" && return 0
    echo "::warning::intento $n fallido: $*"
    [ "$n" -lt 2 ] && sleep "$pause"
  done
  return 1
}

case "$mode" in
  deps) ;;
  full) ;;
  *) echo "modo desconocido: $mode (deps|full)" >&2; exit 2 ;;
esac

if apt_has_network; then
  if [ "$mode" = full ]; then
    attempt npx playwright install --with-deps "$@" && exit 0
  else
    attempt npx playwright install-deps "$@" && exit 0
  fi
fi

echo "::warning title=apt sin red::No se pudieron instalar las dependencias del sistema de Playwright; se usan las de la imagen del runner."
if [ "$mode" = full ]; then
  # El navegador sale del CDN de Playwright, no de apt: sin él no hay prueba posible.
  attempt npx playwright install "$@" || exit 1
fi
exit 0
