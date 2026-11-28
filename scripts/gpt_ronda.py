#!/usr/bin/env python3
"""Una ronda de consulta a GPT (GitHub Models, gratis con el GITHUB_TOKEN) sobre un fichero de ronda.

Uso: python scripts/gpt_ronda.py .ci/gpt-rondas/ronda-1.md [--salida respuesta.md]

El fichero lleva la pregunta y la evidencia sacada del código; el modelo no navega ni ejecuta nada.
La respuesta se imprime entre marcas para leerla en el log del job y se guarda junto a la ronda.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

URLS = ('https://models.github.ai/inference/chat/completions', 'https://models.inference.ai.azure.com/chat/completions')
MODELOS = ('openai/gpt-4.1', 'openai/gpt-4.1-mini')
MAX_ENTRADA = 22000  # caracteres; el nivel gratuito corta hacia 8000 tokens de entrada

SISTEMA = (
    'Eres un auditor senior de SEO y de posicionamiento en buscadores con IA (GEO) para webs editoriales en español. '
    'Respondes en español. Solo afirmas lo que se apoya en la evidencia que te dan o en documentación oficial pública '
    'que conozcas; si algo no se puede comprobar con esa evidencia, lo marcas «sin verificar». No halagas ni rellenas: '
    'si una idea ya está hecha según la evidencia, lo dices y no la propones. Prioriza por impacto real en descubrimiento '
    '(Google, Bing, ChatGPT Search, Perplexity, Gemini, Claude, Copilot) y por coste de implantación. '
    'Desconfía de mitos (keywords meta, llms.txt como factor de ranking, schema inventado, contenido masivo generado sin valor).'
)


def pedir(mensajes, token):
    ultimo = None
    for url, modelo in [(u, m) for m in MODELOS for u in URLS]:
        if 'azure' in url:
            modelo = modelo.split('/', 1)[1]  # el endpoint antiguo usa el nombre sin proveedor
        for intento in range(2):
            cuerpo = json.dumps({'model': modelo, 'messages': mensajes, 'temperature': 0.3, 'max_tokens': 4000}).encode()
            req = urllib.request.Request(url, data=cuerpo, method='POST', headers={
                'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28',
                'User-Agent': 'web-escritor-gpt-rondas/1.0'})
            crudo = b''
            try:
                with urllib.request.urlopen(req, timeout=180) as r:  # noqa: S310 - URL fija
                    crudo = r.read()
                    estado = r.status
                return modelo, json.loads(crudo)['choices'][0]['message']['content']
            except urllib.error.HTTPError as e:
                ultimo = f'HTTP {e.code}: {e.read()[:300]!r}'
            except Exception as e:  # noqa: BLE001 - se reintenta y luego se prueba el modelo de respaldo
                ultimo = f'{e} (estado {locals().get("estado")}, cuerpo {crudo[:300]!r})'
            print(f'{url} {modelo} intento {intento + 1} falló: {ultimo}', file=sys.stderr)
            time.sleep(5)
    raise SystemExit(f'ningún modelo respondió: {ultimo}')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('ronda')
    ap.add_argument('--salida')
    a = ap.parse_args(argv)
    texto = Path(a.ronda).read_text(encoding='utf-8')[:MAX_ENTRADA]
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise SystemExit('falta GITHUB_TOKEN con permiso models: read')
    modelo, respuesta = pedir([{'role': 'system', 'content': SISTEMA}, {'role': 'user', 'content': texto}], token)
    salida = Path(a.salida or str(Path(a.ronda).with_suffix('')) + '.respuesta.md')
    salida.write_text(f'<!-- modelo: {modelo} -->\n{respuesta}\n', encoding='utf-8')
    print('=====RESPUESTA-INICIO=====')
    print(f'modelo: {modelo}')
    print(respuesta)
    print('=====RESPUESTA-FIN=====')


if __name__ == '__main__':
    main()
