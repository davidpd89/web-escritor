#!/usr/bin/env python3
import re
from pathlib import Path
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
robots_text = (ROOT / 'robots.txt').read_text(encoding='utf-8')
rp = RobotFileParser()
rp.parse(robots_text.splitlines())

NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
xml = ET.parse(ROOT / 'sitemap.xml')
urls = [n.text.strip() for n in xml.findall('.//s:url/s:loc', NS) if n.text]
assert len(urls) >= 100, f'Sitemap sospechosamente pequeño: {len(urls)}'

agents = [
    'Googlebot', 'bingbot', 'OAI-SearchBot',
    'ChatGPT-User', 'Claude-SearchBot',
    'Claude-User', 'PerplexityBot',
]
blocked = []
for url in urls:
    parsed = urlsplit(url)
    assert parsed.scheme == 'https' and parsed.hostname == 'davidportodiaz.com', url
    for agent in agents:
        if not rp.can_fetch(agent, url):
            blocked.append((agent, url))

assert not blocked, f'URLs anunciadas pero bloqueadas para buscadores: {blocked[:30]}'
declared = re.findall(r'(?im)^\s*Sitemap:\s*(\S+)\s*$', robots_text)
assert declared.count('https://davidportodiaz.com/sitemap.xml') == 1, declared
print(f'OK: {len(urls)} URLs x {len(agents)} agentes comprobados sin red')
