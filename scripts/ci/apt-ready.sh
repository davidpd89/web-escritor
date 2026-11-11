#!/usr/bin/env bash
# Deja apt listo aunque el espejo de Azure de los runners no resuelva. Sale 0 si apt tiene algún espejo
# con DNS (cambiando a archive.ubuntu.com si hace falta) y 1, en menos de 1 min, si no resuelve ninguno.
#
# 11/11/2026: «Temporary failure resolving 'azure.archive.ubuntu.com'» durante horas. apt reintentaba ese espejo
# en cada paquete (5-8 min por intento) y los trabajos agotaban su límite antes de llegar a la prueba.
set -u
etc=${APT_ETC:-/etc/apt}
pause=${APT_PROBE_PAUSE:-10}
azure=azure.archive.ubuntu.com
# Tope de 3 s por host: con el DNS caído cada getent esperaba ~20 s y el sondeo se comía 3 min.
resolves() { timeout 3 getent hosts "$1" >/dev/null 2>&1; }

for n in 1 2 3; do
  resolves "$azure" && exit 0
  if resolves archive.ubuntu.com || resolves security.ubuntu.com; then
    mirrors="$etc/apt-mirrors.txt"
    if [ -f "$mirrors" ] && grep -q "$azure" "$mirrors"; then
      sudo sed -i "/${azure//./\.}/d" "$mirrors"
      grep -q . "$mirrors" || echo 'http://archive.ubuntu.com/ubuntu/' | sudo tee "$mirrors" >/dev/null
    fi
    for f in "$etc/sources.list" "$etc"/sources.list.d/*; do
      [ -f "$f" ] && grep -q "$azure" "$f" && sudo sed -i "s#$azure#archive.ubuntu.com#g" "$f"
    done
    echo "::warning title=apt::$azure no resuelve; apt usa archive.ubuntu.com"
    exit 0
  fi
  [ "$n" -lt 3 ] && sleep "$pause"
done
echo "::warning title=apt sin red::Ningún espejo de Ubuntu resuelve."
exit 1
