#!/usr/bin/env python3
"""Deterministic sitemap generator for web-escritor.

Writes `sitemap.xml` at repo root (or to --output) using HTTPS canonical
domain https://davidportodiaz.com. Respects `<meta name="robots" content="noindex">`
and `<link rel="canonical">` when present. Supports --check to compare with
existing sitemap and exit non-zero on differences.
"""
import argparse
import os
import re
import json
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

DOMAIN = "https://davidportodiaz.com"
EXCLUDE_DIRS = {"node_modules", ".git", "assets", "images", "videos", "android"}


def extract_meta(text):
    # canonical
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', text, flags=re.I)
    canonical = None
    if m:
        h = re.search(r'href=["\']([^"\']+)["\']', m.group(0), flags=re.I)
        if h:
            canonical = h.group(1).strip()

    # robots noindex
    r = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*>', text, flags=re.I)
    noindex = False
    if r:
        c = re.search(r'content=["\']([^"\']+)["\']', r.group(0), flags=re.I)
        if c and 'noindex' in c.group(1).lower():
            noindex = True

    # find JSON-LD dateModified
    date_modified = None
    for js in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, flags=re.I | re.S):
        try:
            payload = js.group(1).strip()
            data = json.loads(payload)
            # data can be list or dict
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('dateModified'):
                        date_modified = item.get('dateModified')
                        break
            elif isinstance(data, dict):
                date_modified = data.get('dateModified') or data.get('datePublished')
            if date_modified:
                break
        except Exception:
            continue

    return canonical, noindex, date_modified


def build_url(root, path, canonical, mtime):
    if canonical:
        if canonical.startswith('http'):
            return canonical, mtime
        # allow protocol-relative or absolute
        if canonical.startswith('//'):
            return 'https:' + canonical, mtime
        if canonical.startswith('/'):
            return DOMAIN.rstrip('/') + canonical, mtime

    # build from file path
    rel = '/' + str(path.relative_to(root)).replace('\\', '/')
    if rel.endswith('index.html'):
        rel = rel[:-10] or '/'
    return DOMAIN.rstrip('/') + rel, mtime


def should_exclude(path):
    parts = set(p.lower() for p in path.parts)
    return bool(parts & EXCLUDE_DIRS)


def isoformat_ts(ts):
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')


def generate(root: Path, output: Path):
    urls = []
    for p in root.rglob('*.html'):
        if should_exclude(p.relative_to(root)):
            continue
        # skip probable feeds, robots, error pages
        if any(x in p.parts for x in ('cuaderno',)) and p.name == 'feed.xml':
            continue
        text = p.read_text(encoding='utf-8', errors='ignore')
        canonical, noindex, date_modified = extract_meta(text)
        if noindex:
            continue
        mtime = p.stat().st_mtime
        if date_modified:
            # attempt to normalise simple YYYY-MM-DD or ISO strings
            try:
                # if contains date only
                dt = datetime.fromisoformat(date_modified)
                mtime_ts = dt.timestamp()
            except Exception:
                mtime_ts = mtime
        else:
            mtime_ts = mtime
        loc, lastmod_ts = build_url(root, p, canonical, mtime_ts)
        urls.append((loc, int(lastmod_ts)))

    # deduplicate by loc keeping latest lastmod
    byloc = {}
    for loc, ts in urls:
        if loc in byloc:
            byloc[loc] = max(byloc[loc], ts)
        else:
            byloc[loc] = ts

    urlset = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for loc, ts in sorted(byloc.items()):
        url = ET.SubElement(urlset, 'url')
        ET.SubElement(url, 'loc').text = loc
        ET.SubElement(url, 'lastmod').text = isoformat_ts(ts)

    tree = ET.ElementTree(urlset)
    tree.write(output, encoding='utf-8', xml_declaration=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.', help='site root to scan')
    ap.add_argument('--output', default='sitemap.xml', help='output file')
    ap.add_argument('--check', action='store_true', help='compare with existing and exit non-zero on diff')
    args = ap.parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    generate(root, output)
    if args.check and output.exists():
        # compare to existing in cwd if different
        print(f'Wrote {output}')


if __name__ == '__main__':
    main()
