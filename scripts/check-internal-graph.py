#!/usr/bin/env python3
"""Internal graph checker.

Scans local HTML files, extracts internal links and canonicals, reports:
- broken internal links
- pages with zero incoming internal links (orphan pages)
- pages missing `link rel="canonical"`
- canonical collisions (multiple pages claiming same canonical)

Excludes assets, feeds, robots, and pages with `meta name="robots" content="noindex"`.
"""
from pathlib import Path
import re
import sys
import json
from collections import defaultdict

ROOT = Path('.').resolve()
DOMAIN = 'https://davidportodiaz.com'
EXCLUDE_PATH_PARTS = {'node_modules', '.git', 'assets', 'images', 'videos', 'android'}


def read_text(p: Path):
    try:
        return p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def find_html_files(root: Path):
    for p in root.rglob('*.html'):
        if any(part in EXCLUDE_PATH_PARTS for part in p.parts):
            continue
        yield p


def extract_canonical(text):
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', text, flags=re.I)
    if not m:
        return None
    h = re.search(r'href=["\']([^"\']+)["\']', m.group(0), flags=re.I)
    if h:
        return h.group(1).strip()
    return None


def has_noindex(text):
    m = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*>', text, flags=re.I)
    if not m:
        return False
    c = re.search(r'content=["\']([^"\']+)["\']', m.group(0), flags=re.I)
    return bool(c and 'noindex' in c.group(1).lower())


def extract_links(text):
    # find href/src etc.
    links = []
    for m in re.finditer(r'href=["\']([^"\'#]+)(?:#[^"\']*)?["\']', text, flags=re.I):
        links.append(m.group(1))
    for m in re.finditer(r'src=["\']([^"\'#]+)(?:#[^"\']*)?["\']', text, flags=re.I):
        links.append(m.group(1))
    return links


def resolve_link(src_path: Path, link: str):
    # absolute http(s)
    if link.startswith('http://') or link.startswith('https://'):
        return link
    if link.startswith('//'):
        return 'https:' + link
    # root-relative
    if link.startswith('/'):
        return DOMAIN.rstrip('/') + link
    # relative path
    return str((src_path.parent / link).resolve())


def to_site_path(root: Path, loc: str):
    # convert generated absolute domain URL back to file path if possible
    if loc.startswith('http://') or loc.startswith('https://'):
        if DOMAIN in loc:
            suffix = loc.split(DOMAIN, 1)[1]
            if suffix.startswith('/'):
                candidate = root.joinpath(suffix.lstrip('/'))
                if candidate.exists():
                    return candidate
    # fallback: if loc is filesystem path
    p = Path(loc)
    if p.exists():
        return p
    return None


def short(p: Path):
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)


def main():
    files = list(find_html_files(ROOT))
    pages = {}
    for f in files:
        txt = read_text(f)
        if has_noindex(txt):
            continue
        canonical = extract_canonical(txt)
        links = extract_links(txt)
        pages[str(f)] = {
            'path': f,
            'canonical': canonical,
            'links': links,
        }

    # build graph
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    broken = []

    for p, meta in pages.items():
        src_path = meta['path']
        for link in meta['links']:
            if link.startswith('mailto:') or link.startswith('tel:'):
                continue
            resolved = resolve_link(src_path, link)
            # if link is internal (domain or filesystem)
            if resolved.startswith(DOMAIN) or resolved.startswith(str(ROOT)) or not re.match(r'https?://', resolved):
                target_path = to_site_path(ROOT, resolved)
                if target_path and target_path.exists():
                    outgoing[p].append(str(target_path))
                    incoming[str(target_path)].append(p)
                else:
                    # allow index.html mapping
                    # try adding index.html
                    if resolved.endswith('/'):
                        candidate = to_site_path(ROOT, resolved + 'index.html')
                        if candidate and candidate.exists():
                            outgoing[p].append(str(candidate))
                            incoming[str(candidate)].append(p)
                        else:
                            broken.append((p, link, resolved))
                    else:
                        # try resolved + '.html'
                        candidate = to_site_path(ROOT, resolved + '.html')
                        if candidate and candidate.exists():
                            outgoing[p].append(str(candidate))
                            incoming[str(candidate)].append(p)
                        else:
                            broken.append((p, link, resolved))

    # orphan pages: pages with zero incoming links (excluding index/home)
    orphans = []
    for p in pages:
        ppath = pages[p]['path']
        if str(ppath) not in incoming:
            # skip root index
            if ppath.name.lower() in ('index.html', 'home.html'):
                continue
            orphans.append(p)

    # missing canonical
    missing_canonical = [p for p,m in pages.items() if not m['canonical']]

    # canonical collisions
    canon_map = defaultdict(list)
    for p,m in pages.items():
        if m['canonical']:
            canon_map[m['canonical']].append(p)
    collisions = {c: lst for c,lst in canon_map.items() if len(lst) > 1}

    # print report
    print('INTERNAL GRAPH REPORT')
    print('Files scanned:', len(files))
    print('Pages considered (noindex excluded):', len(pages))
    print('\nBROKEN INTERNAL LINKS:')
    for b in broken[:200]:
        print('-', short(Path(b[0])), '->', b[1], '(resolved:', b[2], ')')
    print('\nORPHAN PAGES (no incoming):')
    for o in orphans[:200]:
        print('-', short(Path(o)))
    print('\nPAGES MISSING CANONICAL:')
    for m in missing_canonical[:200]:
        print('-', short(Path(m)))
    print('\nCANONICAL COLLISIONS:')
    for c,lst in collisions.items():
        print('-', c)
        for p in lst[:10]:
            print('   *', short(Path(p)))

    # exit code non-zero if severe issues found (broken links > 0)
    if broken:
        sys.exit(2)


if __name__ == '__main__':
    main()
