#!/usr/bin/env python3
"""Paridad factual de Event entre agenda y archivo. Sin red."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def events(filename):
    html = (ROOT / filename).read_text(encoding='utf-8')
    blocks = re.findall(r'<script\b[^>]*type=[\'\"]application/ld\+json[\'\"][^>]*>(.*?)</script>', html, re.S | re.I)
    result = {}
    for block in blocks:
        doc = json.loads(block)
        nodes = doc.get('@graph', [doc]) if isinstance(doc, dict) else doc
        for node in nodes:
            if not isinstance(node, dict):
                continue
            types = node.get('@type', [])
            if isinstance(types, str):
                types = [types]
            if 'Event' not in types:
                continue
            identifier = str(node.get('@id', ''))
            fragment = identifier.partition('#')[2]
            if fragment:
                if fragment in result:
                    raise AssertionError(f'Evento duplicado: {filename} #{fragment}')
                result[fragment] = node
    return result


class EventIdentity(unittest.TestCase):
    def test_shared_events_have_identical_facts(self):
        agenda = events('eventos.html')
        archive = events('ferias.html')
        self.assertTrue(agenda)
        self.assertTrue(archive)
        self.assertEqual(set(agenda), set(archive))
        fields = ('name', 'startDate', 'endDate', 'eventStatus', 'location', 'organizer')
        for identifier in sorted(agenda):
            for field in fields:
                with self.subTest(event=identifier, field=field):
                    self.assertEqual(agenda[identifier].get(field), archive[identifier].get(field))


if __name__ == '__main__':
    unittest.main()
