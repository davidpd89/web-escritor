#!/bin/sh
# uso: piloto_browser.sh <puerto>
P=$1; SRC='C:\GIT\web-escritor-qa-gpt-src'
cd "$SRC" && python -m http.server $P --bind 127.0.0.1 >/dev/null 2>&1 & SRV=$!
cd /c/GIT/web-escritor-qa-gpt/scripts/qa-gpt
QA_NODE_MODULES='C:/GIT/web-escritor/node_modules' node contratos_browser.mjs http://127.0.0.1:$P 'C:\GIT\qa-gpt-state\auditoria\urls-piloto.json' 'C:\GIT\qa-gpt-state\auditoria\piloto-via-a-browser.json'
kill $SRV
