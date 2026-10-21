#!/usr/bin/env python3
"""Vigila las fuentes oficiales del radar de concursos y marca lo que necesita revisión humana.

No publica nada ni cambia fechas: la web exige que cada convocatoria esté verificada contra su
fuente oficial. Este monitor reduce el trabajo de vigilancia: cada ejecución revisa un número
acotado de fuentes (las menos recientes primero), respeta robots.txt y guarda solo una huella
(hash, años y fechas citadas), nunca el contenido de la página.

Marca: caída persistente (2 fallos seguidos), cambio sustancial del texto y aparición de un año
nuevo en la página (señal típica de «convocatoria 2027 abierta»).
Sin modelos ni claves. Uso: python scripts/radar_source_monitor.py [--max 40] [--state ruta]
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[1]
AGENT = 'DavidPortoRadarMonitor/1.0 (+https://davidportodiaz.com)'
MAX_BYTES = 1_500_000
SIMILARITY_ALERT = 0.90   # por debajo de este solape de palabras se considera cambio sustancial
MONTHS = 'enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre'
DATE_RE = re.compile(r'\b\d{1,2}\s+de\s+(?:' + MONTHS + r')(?:\s+de\s+20\d{2})?', re.I)
YEAR_RE = re.compile(r'\b(20[2-3]\d)\b')
_DROP = re.compile(r'<(script|style|noscript|svg|nav|header|footer|form|iframe)\b.*?</\1>', re.S | re.I)


def page_text(document: str) -> str:
    body = _DROP.sub(' ', document)
    body = re.sub(r'<[^>]+>', ' ', body)
    return ' '.join(html.unescape(body).lower().split())[:300_000]


def fingerprint(document: str) -> dict:
    text = page_text(document)
    words = re.findall(r'[a-záéíóúüñ0-9]{3,}', text)
    unique = sorted(set(words))
    keep = sorted(unique, key=lambda w: hashlib.sha1(w.encode()).hexdigest())[:400]
    return {
        'hash': hashlib.sha256(text.encode()).hexdigest()[:16],
        'words': keep,
        'years': sorted(set(YEAR_RE.findall(text))),
        'dates': sorted(set(m.group(0).lower() for m in DATE_RE.finditer(text)))[:12],
    }


def similarity(old: list[str], new: list[str]) -> float:
    a, b = set(old), set(new)
    return 1.0 if not a and not b else len(a & b) / max(1, len(a | b))


def judge(previous: dict | None, current: dict | None, error: str | None, today: date) -> list[str]:
    """Banderas para una fuente: 'caida', 'cambio', 'anio-nuevo'. `previous` es la huella guardada."""
    flags: list[str] = []
    if error:
        if previous and previous.get('error'):
            flags.append('caida')
        return flags
    if not previous or previous.get('error') or not previous.get('hash'):
        return flags
    if current['hash'] != previous['hash'] and similarity(previous['words'], current['words']) < SIMILARITY_ALERT:
        flags.append('cambio')
    newest_before = max(previous.get('years') or ['0'])
    if any(y > newest_before and int(y) >= today.year for y in current['years']):
        flags.append('anio-nuevo')
    return flags


class Fetcher:
    def __init__(self, delay=1.5, opener=urlopen):
        self.delay, self.opener, self.last, self.robots = delay, opener, 0.0, {}

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        host = parts.scheme + '://' + parts.netloc
        if host not in self.robots:
            parser = RobotFileParser(host + '/robots.txt')
            try:
                with self.opener(Request(host + '/robots.txt', headers={'User-Agent': AGENT}), timeout=12) as r:
                    parser.parse(r.read(200_000).decode('utf-8', 'replace').splitlines())
            except Exception:
                parser = None  # Sin robots legible se trata como permitido (política habitual).
            self.robots[host] = parser
        parser = self.robots[host]
        return True if parser is None else parser.can_fetch(AGENT, url)

    def __call__(self, url: str) -> str:
        if not self.allowed(url):
            raise PermissionError('robots.txt no permite consultar esta URL')
        pause = self.delay - (time.monotonic() - self.last)
        if pause > 0:
            time.sleep(pause)
        self.last = time.monotonic()
        with self.opener(Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html'}), timeout=20) as response:
            return response.read(MAX_BYTES).decode('utf-8', 'replace')


def sources(data: dict) -> list[dict]:
    out, seen = [], set()
    for item in [*data.get('items', []), *data.get('watchlist', [])]:
        url = item.get('source_url', '')
        if item.get('published') and url.startswith('https://') and url not in seen:
            seen.add(url)
            out.append({'id': item['id'], 'title': item['title'], 'url': url})
    return out


def run(data: dict, state: dict, fetch, today: date, *, max_sources=40) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    todo = sorted(sources(data), key=lambda s: (state.get(s['url'], {}).get('checked_at', ''), s['url']))[:max_sources]
    report = {'generated_at': now, 'checked': 0, 'flagged': [], 'ok': 0}
    for source in todo:
        previous = state.get(source['url'])
        current = error = None
        try:
            current = fingerprint(fetch(source['url']))
        except Exception as exc:  # una fuente caída no detiene a las demás
            error = type(exc).__name__
        flags = judge(previous, current, error, today)
        report['checked'] += 1
        state[source['url']] = ({**current, 'checked_at': now} if current else {**(previous or {}), 'error': error, 'checked_at': now})
        if flags:
            report['flagged'].append({**source, 'flags': flags, 'error': error})
        else:
            report['ok'] += 1
    return report


def markdown(report: dict) -> str:
    lines = [f"# Radar de concursos: fuentes para revisar ({report['generated_at']})", '',
             f"Revisadas {report['checked']} fuentes; {report['ok']} sin novedades; {len(report['flagged'])} para revisar.", '']
    labels = {'caida': 'Fuente caída dos veces seguidas', 'cambio': 'Cambio sustancial del texto', 'anio-nuevo': 'Aparece un año nuevo (¿nueva edición?)'}
    for item in report['flagged']:
        lines.append(f"- **{item['title']}** (`{item['id']}`): " + '; '.join(labels[f] for f in item['flags']) + f" — {item['url']}")
    if not report['flagged']:
        lines.append('Nada que revisar esta semana.')
    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max', type=int, default=40)
    parser.add_argument('--state', type=Path, default=ROOT / '.ci/radar-monitor/state.json')
    parser.add_argument('--out', type=Path, default=ROOT / '.ci/radar-monitor')
    args = parser.parse_args()
    data = json.loads((ROOT / 'data/radar-opportunities.json').read_text(encoding='utf-8'))
    state = json.loads(args.state.read_text(encoding='utf-8')) if args.state.exists() else {}
    report = run(data, state, Fetcher(), date.today(), max_sources=args.max)
    args.out.mkdir(parents=True, exist_ok=True)
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding='utf-8')
    (args.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    (args.out / 'report.md').write_text(markdown(report), encoding='utf-8')
    print(markdown(report))
    return 0


if __name__ == '__main__':
    sys.exit(main())
