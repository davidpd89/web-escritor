#!/usr/bin/env bash
# Instala Playwright y sus dependencias del sistema sin que una caída de apt tumbe la QA de navegador.
#   playwright-install-deps.sh deps chromium   (navegador en caché: solo librerías del sistema)
#   playwright-install-deps.sh full chromium   (navegador + librerías)
#
# 11/11/2026: los runners no resolvían azure.archive.ubuntu.com y 11 trabajos de navegador fallaron a la vez
# tras 8 min reintentando apt. apt-ready.sh cambia de espejo o, si no hay ninguno, se salta apt en ~20 s: las
# librerías de Chromium ya vienen en la imagen fijada ubuntu-24.04 (trae Chrome) y la prueba real decide.
# 18/11/2026: con apt vivo pero lento, install-deps (125 MB) agotó el tope y la QA siguió «con la imagen», que trae las
# librerías de Chromium pero no las de WebKit (libevent-2.1.so.7): Cross-engine, Post-deploy y Nightly cayeron.
# 24/11/2026: install-deps terminó bien y WebKit siguió sin libevent (navegador en caché de otra imagen): la comprobación
# de ldd se hace también tras un install-deps correcto.
# Si install-deps no termina, se instalan solo los paquetes de las librerías que ldd marca como ausentes.
set -u
shopt -s nullglob
mode=${1:?deps|full}; shift
here=$(dirname "$0")
pause=${PW_DEPS_PAUSE:-30}
limit=${PW_DEPS_TIMEOUT:-300}

case "$mode" in
  deps|full) ;;
  *) echo "modo desconocido: $mode (deps|full)" >&2; exit 2 ;;
esac

# Paquetes candidatos para cada soname según la política de Debian (8.1): libfoo.so.3 -> libfoo3,
# libevent-2.1.so.7 -> libevent-2.1-7; con la variante t64 de Ubuntu 24.04 (libevent-2.1-7t64).
soname_packages() {
  local so base ver pkg
  for so in "$@"; do
    base=${so%%.so.*}; ver=${so#*.so.}
    [ "$base" = "$so" ] && continue
    base=$(printf '%s' "$base" | tr 'A-Z_' 'a-z-')
    case "$base" in *[0-9]) pkg="$base-$ver" ;; *) pkg="$base$ver" ;; esac
    printf '%s
%st64
' "$pkg" "$pkg"
  done
}

# Librerías que ldd no encuentra para los navegadores pedidos (con sus propias carpetas de librerías en la ruta).
missing_sonames() {
  local root=${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright} dirs=() b d libpath=
  for b in "$@"; do dirs+=("$root/$b"-* "$root/${b}_headless_shell"-*); done
  [ ${#dirs[@]} -eq 0 ] && return 0
  for d in $(find "${dirs[@]}" -name '*.so*' -printf '%h
' 2>/dev/null | sort -u); do libpath="$libpath:$d"; done
  find "${dirs[@]}" -type f \( -perm -u+x -o -name '*.so*' \) -print0 2>/dev/null     | LD_LIBRARY_PATH="${libpath#:}" xargs -0 -r ldd 2>/dev/null | awk '/not found/ {print $1}' | sort -u
}

install_missing() {
  local missing pkgs=() p left
  missing=$(missing_sonames "$@")
  [ -z "$missing" ] && return 0
  echo "Librerías ausentes: $(echo $missing)"
  for p in $(soname_packages $missing); do
    apt-cache show "$p" >/dev/null 2>&1 && pkgs+=("$p")
  done
  [ ${#pkgs[@]} -gt 0 ] && timeout "$limit" sudo apt-get install -y --no-install-recommends "${pkgs[@]}"
  left=$(missing_sonames "$@")
  [ -n "$left" ] && echo "::warning title=librerías ausentes::Siguen faltando: $(echo $left)"
  return 0
}

apt_ok=0
if bash "$here/apt-ready.sh"; then
  apt_ok=1
  if [ "$mode" = full ]; then
    timeout "$limit" npx playwright install --with-deps "$@" && { install_missing "$@"; exit 0; }
  else
    timeout "$limit" npx playwright install-deps "$@" && { install_missing "$@"; exit 0; }
  fi
fi

echo "::warning title=apt sin red::No se pudieron instalar las dependencias del sistema de Playwright; se usan las de la imagen del runner y solo se instalan las librerías que falten."
if [ "$mode" = full ]; then
  # El navegador sale del CDN de Playwright, no de apt: sin él no hay prueba posible.
  ok=0
  for n in 1 2; do
    timeout "$limit" npx playwright install "$@" && { ok=1; break; }
    [ "$n" -lt 2 ] && sleep "$pause"
  done
  [ "$ok" = 1 ] || exit 1
fi
[ "$apt_ok" = 1 ] && install_missing "$@"
exit 0
