#!/usr/bin/env python3
"""Small, offline HTML audits. Findings are advisory; exit 1 preserves visibility."""
from __future__ import annotations

import argparse
import json
import posixpath
import subprocess
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
INERT = {'template', 'script', 'style'}


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    line: int = 1
    children: list = field(default_factory=list)


class Tree(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = Node('document')
        self.stack = [self.root]
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        # HTML permits omitted </option> and </optgroup> tags.
        if tag in {'option', 'optgroup'} and self.stack[-1].tag == 'option':
            self.handle_endtag('option')
        if tag == 'optgroup' and self.stack[-1].tag == 'optgroup':
            self.handle_endtag('optgroup')
        node = Node(tag, dict(attrs), self.getpos()[0])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def walk(node):
    if node.tag in INERT:
        return
    yield node
    for child in node.children:
        if isinstance(child, Node):
            yield from walk(child)


def text(node, referenced=False):
    if node.tag in INERT or (not referenced and ('hidden' in node.attrs or node.attrs.get('aria-hidden') == 'true')):
        return ''
    return ''.join(text(c, referenced) if isinstance(c, Node) else c for c in node.children)


def audit_json(source, page):
    """Python's default JSON decoder silently accepts duplicate keys and NaN."""
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate object key {key!r}; ordinary decoders silently overwrite data.')
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f'Non-JSON numeric token {value}; browser JSON parsing rejects it.')

    try:
        json.loads(source, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    except ValueError as error:
        return [dict(page=page, line=getattr(error, 'lineno', 1), rule='json-source', message=str(error))]
    return []


def audit_html(source, page, files, counts=None):
    nodes = list(walk(Tree(source).root))
    ids = {n.attrs['id']: n for n in nodes if n.attrs.get('id')}
    findings = []

    def report(node, rule, message):
        findings.append(dict(page=page, line=node.line, rule=rule, message=message))

    for node in nodes:
        family = {'details': 'disclosures', 'select': 'selects'}.get(node.tag)
        if node.tag == 'input' and node.attrs.get('list'):
            family = 'suggestion_lists'
        if node.tag == 'a' and 'download' in node.attrs:
            family = 'downloads'
        if node.tag == 'input' and node.attrs.get('type', '').lower() in {'number', 'range'}:
            family = 'numeric_inputs'
        if node.tag in {'input', 'button', 'select', 'textarea', 'output', 'fieldset', 'object'} and node.attrs.get('form'):
            if counts is not None:
                counts['form_references'] = counts.get('form_references', 0) + 1
            target = ids.get(node.attrs['form'])
            if target is None or target.tag != 'form':
                report(node, 'form-owner', 'form= must reference an existing form, not just any element ID.')
        if counts is not None and family:
            counts[family] = counts.get(family, 0) + 1
        if node.tag == 'input' and node.attrs.get('type', '').lower() in {'number', 'range'}:
            def finite(name):
                try:
                    value = Decimal(node.attrs.get(name) or '')
                    return value if value.is_finite() else None
                except InvalidOperation:
                    return None
            minimum, maximum, step = finite('min'), finite('max'), finite('step')
            if minimum is not None and maximum is not None and minimum > maximum:
                report(node, 'numeric-bounds', 'Minimum exceeds maximum: no numeric value can satisfy both bounds.')
            if step is not None and step <= 0:
                report(node, 'numeric-step', 'Numeric step must be positive, or use any.')
        if node.tag == 'details':
            elements = [c for c in node.children if isinstance(c, Node)]
            summaries = [c for c in elements if c.tag == 'summary']
            if len(summaries) != 1 or not elements or elements[0].tag != 'summary':
                report(node, 'details-summary', 'Expected exactly one summary as the first element child.')
            for summary in summaries:
                refs = (summary.attrs.get('aria-labelledby') or '').split()
                label = ' '.join(text(ids[r], referenced=True) for r in refs if r in ids) if refs else summary.attrs.get('aria-label') or text(summary)
                if not label.strip():
                    report(summary, 'summary-name', 'Disclosure has no readable text or accessible name.')
        if node.tag == 'select':
            options = [n for n in walk(node) if n.tag == 'option']
            group_disabled = {id(n) for group in walk(node) if group.tag == 'optgroup' and 'disabled' in group.attrs for n in walk(group)}
            values = {}
            for option in options:
                # Effective option value when value= is omitted: collapsed text.
                value = option.attrs.get('value')
                if value is None:
                    value = ' '.join(text(option).split())
                if value and 'disabled' not in option.attrs and id(option) not in group_disabled:
                    if value in values:
                        report(option, 'select-value', f'Duplicate non-empty option value {value!r}; selections cannot be distinguished.')
                    values[value] = option
            if 'multiple' not in node.attrs and sum('selected' in o.attrs for o in options) > 1:
                report(node, 'select-selected', 'Single-choice select declares multiple selected options.')
        if node.tag == 'input' and node.attrs.get('list'):
            target = ids.get(node.attrs['list'])
            if target is None or target.tag != 'datalist':
                report(node, 'input-list', 'list= must reference an existing datalist on this page.')
        if node.tag == 'a' and 'download' in node.attrs:
            href = node.attrs.get('href') or ''
            try:
                url = urlsplit(href)
                port = url.port
            except ValueError:
                report(node, 'download-target', 'Malformed download URL.')
                continue
            if url.scheme in {'data', 'blob'}:
                continue
            if url.netloc and ((url.scheme or 'https') != 'https' or url.hostname != 'davidportodiaz.com' or port not in {None, 443}):
                report(node, 'download-origin', 'Cross-origin download attribute is ignored by browsers; verify the intended action.')
                continue
            if url.scheme and url.scheme not in {'http', 'https'}:
                report(node, 'download-target', 'Unsupported download destination scheme.')
                continue
            raw_path = unquote(url.path)
            # Lexical POSIX paths preserve case on Windows too: production is case-sensitive.
            target = posixpath.normpath(raw_path.lstrip('/') if raw_path.startswith('/') else posixpath.join(posixpath.dirname(page), raw_path))
            if target == '..' or target.startswith('../') or '\\' in target:
                target = ''
            if not raw_path or target not in files:
                report(node, 'download-target', 'Download does not target a tracked file (check path, case and URL encoding).')
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.ci/small-ui-audit')
    args = parser.parse_args()
    files = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')) - {''}
    pages = sorted(p for p in files if p.endswith('.html') and not p.startswith(('tests/', 'qa/', 'lab/', 'data/')))
    findings = []
    counts = dict(disclosures=0, selects=0, suggestion_lists=0, downloads=0, numeric_inputs=0, form_references=0)
    for page in pages:
        findings.extend(audit_html((ROOT/page).read_text(encoding='utf-8'), page, files, counts))
    json_files = sorted(p for p in files if p.startswith(('assets/', 'data/')) and p.endswith('.json'))
    counts['json_sources'] = len(json_files)
    for page in json_files:
        findings.extend(audit_json((ROOT/page).read_text(encoding='utf-8'), page))
    result = dict(pages=len(pages), checked=counts, findings=findings)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    lines = ['# Small UI audit', '', f'Pages: {len(pages)}. Findings: {len(findings)}.', '',
             'Offline source checks; dynamic controls and browser interaction need their existing browser suites.', '']
    lines += [f'- Checked {name}: {count}' for name, count in counts.items()] + ['']
    lines += [f'- `{f["page"]}:{f["line"]}` **{f["rule"]}**: {f["message"]}' for f in findings]
    (args.output/'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(f'Small UI audit: {len(pages)} pages, {len(findings)} findings. Report: {args.output}')
    return int(bool(findings))


if __name__ == '__main__':
    raise SystemExit(main())
