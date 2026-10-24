#!/usr/bin/env python3
"""Offline proof contract for publisher contacts and manuscript-reception status.

Research-only. Reads manually recorded observations and an *independently vetted*
source-host allowlist. Does not fetch webpages, extract email addresses, write
public datasets, or infer manuscript acceptance from a group/contact page.

Usage:
  python scripts/research/gpt_editoriales_contact_evidence.py \
    --observations input-observations.json --trusted-hosts vetted-hosts.json \
    --as-of 2026-10-22

Trusted hosts must be vetted against an official organization page, not supplied
by an untrusted observation itself. Reports contain URLs and status suggestions,
never contact addresses or raw page excerpts. All suggestions require review.
"""
from __future__ import annotations

import argparse
import ipaddress
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

PURPOSES = {"general_contact", "press_contact", "submissions_open",
            "submissions_paused", "group_submission_channel", "publisher_imprint"}
STATUS_KIND = {"submissions_open": "open", "submissions_paused": "closed"}
STATUS_TTL_DAYS = 45
CONTACT_TTL_DAYS = 180
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DNS = re.compile(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\Z", re.I)


def safe_host(url: object) -> str | None:
    if not isinstance(url, str) or len(url) > 1400 or any(ord(c) < 32 for c in url):
        return None
    try:
        parts = urlsplit(url)
        host = parts.hostname
        if not (parts.scheme == "https" and host and DNS.fullmatch(host)
                and "." in host and ".." not in host and not parts.username
                and not parts.password and parts.port in (None, 443)
                and not parts.fragment and not host.endswith((".local", ".internal",
                    ".test", ".example", ".invalid"))):
            return None
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return host.lower()
    except ValueError:
        return None
    return None


def review(observations: dict, vetted_hosts: dict, *, as_of: date) -> dict:
    if observations.get("schema_version") != 1 or not isinstance(observations.get("observations"), list):
        raise ValueError("observations schema must be version 1 and contain a list")
    if vetted_hosts.get("schema_version") != 1 or not isinstance(vetted_hosts.get("publishers"), dict):
        raise ValueError("host approval schema must be version 1 and contain publishers map")
    approvals = {}
    for slug, entry in vetted_hosts["publishers"].items():
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or not isinstance(entry, dict):
            raise ValueError("invalid trusted publisher entry")
        allowed = entry.get("hosts")
        if (not isinstance(allowed, list) or not allowed or
                not all(isinstance(v, str) and safe_host("https://" + v) == v for v in allowed)):
            raise ValueError("hosts must be verified lowercase public DNS names")
        approvals[slug] = set(allowed)
    observed_ids = set()
    observed_facts = set()
    issues = []
    by_slug = defaultdict(lambda: {
        "general_sources": [], "press_sources": [], "publisher_sources": [],
        "group_submission_sources": [], "submission_status_candidates": []})
    for i, obs in enumerate(observations["observations"]):
        ref = f"observation[{i}]"
        if not isinstance(obs, dict):
            issues.append({"record": ref, "reason": "invalid_record"})
            continue
        ident = obs.get("id")
        slug = obs.get("publisher_slug")
        purpose = obs.get("purpose")
        source_url = obs.get("source_url")
        host = safe_host(source_url)
        scope = obs.get("scope")
        if (not isinstance(ident, str) or not SLUG.fullmatch(ident)
                or ident in observed_ids):
            issues.append({"record": ref, "reason": "missing_or_duplicate_id"})
            continue
        observed_ids.add(ident)
        # Automatically extracted text is NOT a human-verified official
        # observation, even if the domain/URL was independently allowlisted.
        # A reviewer must create a separate, human-authored record first.
        if obs.get("origin") == "html_pilot_unreviewed":
            issues.append({"record": ident, "reason": "automated_evidence_needs_human_review"})
            continue
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or slug not in approvals:
            issues.append({"record": ident, "reason": "publisher_not_approved"})
            continue
        if purpose not in PURPOSES or scope not in {"publisher_specific", "group_general"}:
            issues.append({"record": ident, "reason": "invalid_purpose_or_scope"})
            continue
        if not host or host not in approvals[slug]:
            issues.append({"record": ident, "reason": "source_host_not_approved"})
            continue
        try:
            day = date.fromisoformat(obs["checked_at"])
            if day.isoformat() != obs["checked_at"]:
                raise ValueError("Expected YYYY-MM-DD")
        except (ValueError, KeyError, TypeError):
            issues.append({"record": ident, "reason": "invalid_date"})
            continue
        age = (as_of - day).days
        if age < 0:
            issues.append({"record": ident, "reason": "future_evidence"})
            continue
        # Explicit human-authored summary: not an automatic keyword extraction.
        summary = obs.get("evidence_summary")
        if not isinstance(summary, str) or not 15 <= len(summary) <= 300:
            issues.append({"record": ident, "reason": "missing_evidence_summary"})
            continue
        if "@" in summary or "@" in source_url:
            issues.append({"record": ident, "reason": "possible_personal_data_or_address"})
            continue
        fact = (slug, purpose, scope, source_url, day)
        if fact in observed_facts:
            issues.append({"record": ident, "reason": "duplicate_evidence"})
            continue
        observed_facts.add(fact)
        limit = STATUS_TTL_DAYS if purpose.startswith("submissions_") or purpose == "group_submission_channel" else CONTACT_TTL_DAYS
        expired = age > limit
        evidence = {"id": ident, "source_url": source_url,
                    "checked_at": day.isoformat(), "expired": expired,
                    "purpose": purpose, "scope": scope}
        dest = by_slug[slug]
        if purpose == "general_contact":
            dest["general_sources"].append(evidence)
        elif purpose == "press_contact":
            dest["press_sources"].append(evidence)
        elif purpose == "publisher_imprint":
            dest["publisher_sources"].append(evidence)
        elif purpose == "group_submission_channel":
            dest["group_submission_sources"].append(evidence)
        else:
            evidence["proposed_status"] = STATUS_KIND[purpose] if scope == "publisher_specific" and not expired else "unknown"
            dest["submission_status_candidates"].append(evidence)

    results = []
    for slug, values in sorted(by_slug.items()):
        current = {item["proposed_status"] for item in values["submission_status_candidates"]
                   if item["proposed_status"] != "unknown"}
        if len(current) > 1:
            status = "conflict_review"
        elif current:
            status = next(iter(current))
        else:
            status = "not_inferred"
        result = {"slug": slug, **values, "proposed_manuscript_status": status,
                  "manual_review_required": True, "publication_allowed": False}
        results.append(result)
    return {
        "schema_version": 1, "as_of": as_of.isoformat(),
        "policy": "No group inheritance, no email inference, no automatic publication.",
        "publishers": results, "rejected_observations": issues,
        "writes_to_public_data": False,
    }


# Small E6.3 experimental extractor. NOT a generic legal/status classifier.
# Use the HTTP/robots/cache implementation ALREADY in main
# (reading_editorial_sources.CachedHTTP) to supply HTML only after approval.
class _PilotVisibleText(HTMLParser):
    """Text eligible as visible evidence; no DOM/CSS engine required."""
    BLOCKED_TAGS = {'script', 'style', 'noscript', 'svg', 'head', 'template', 'title'}
    VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
                 'meta', 'param', 'source', 'track', 'wbr'}
    SEPARATORS = {'p', 'h1', 'h2', 'h3', 'h4', 'li', 'br', 'div'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.stack = []
        self.hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        style = attributes.get('style') or ''
        is_hidden = (
            self.hidden_depth > 0 or tag in self.BLOCKED_TAGS or
            'hidden' in attributes or
            (attributes.get('aria-hidden') or '').lower() == 'true' or
            bool(re.search(
                r'(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)\b',
                style, re.I,
            ))
        )
        if tag not in self.VOID_TAGS:
            self.stack.append((tag, is_hidden))
            if is_hidden:
                self.hidden_depth += 1
        if tag in self.SEPARATORS and not is_hidden:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in self.SEPARATORS and not self.hidden_depth:
            self.parts.append(' ')
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.hidden_depth -= sum(hidden for _, hidden in self.stack[index:])
                del self.stack[index:]
                break

    def handle_data(self, data):
        if not self.hidden_depth:
            self.parts.append(data)


# These known-page rules are a bounded experiment, not reusable auto-approval.
# Extend only after testing diverse layouts with full real HTML; leave UNKNOWN
# if the source changes or if the explicit statement disappears.
_PILOT_EVIDENCE_RULES = {
    'editorial-anagrama': (r'pausad[ao].{0,90}recepcion de manuscritos', 'paused'),
    'nocturna-ediciones': (r'si desea enviarnos un manuscrito.{0,150}correo electronico', 'open'),
    'minotauro': (r'el proyecto debera enviarse por correo electronico', 'open'),
    'alienta-editorial': (r'alienta editorial acepta la recepcion de manuscritos originales', 'open'),
    'alfaguara': (r'solo recibe manuscritos espontaneos a traves de la web', 'group_only'),
}

# Exact human-checked pages, independent of the pilot input JSON.
_PILOT_OFFICIAL_URLS = {
    'editorial-anagrama': 'https://www.anagrama-ed.es/manuscritos',
    'nocturna-ediciones': 'https://www.nocturnaediciones.com/contacto',
    'minotauro': 'https://www.planetadelibros.com/editorial/minotauro/21',
    'alienta-editorial': 'https://www.planetadelibros.com/editorial/alienta-editorial/15',
    'alfaguara': 'https://www.penguinrandomhousegrupoeditorial.com/sellos-y-negocios/quiero-enviar-un-manuscrito/',
}


# These anchors are tied to explicit instructions on reviewed official pages.
# Do NOT collect the first visible address: Nocturna/Minotauro also list press
# and reader mailboxes, and Alienta lists personal press contacts.
_OFFICIAL_SUBMISSION_EMAILS = {
    'nocturna-ediciones': ('nocturnaediciones.com',
        r'si desea enviarnos un manuscrito.{0,150}?a la siguiente direcci[oó]n:\s*'),
    'minotauro': ('planeta.es',
        r'el proyecto deber[aá] enviarse por correo electr[oó]nico a la direcci[oó]n\s*'),
    'alienta-editorial': ('planeta.es',
        r'la direcci[oó]n de correo electr[oó]nico para los manuscritos en formato digital es:\s*'),
}
_ROLE_EMAIL = r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})'


def submission_email_candidate(visible_text: str, *, slug: str,
                               suggestion: str) -> str | None:
    """Public role mailbox explicitly following a reviewed submission instruction.

    Only a review candidate, NEVER an approved or automatically published
    address. It deliberately ignores general/press/awards contacts.
    """
    if suggestion != 'open' or slug not in _OFFICIAL_SUBMISSION_EMAILS:
        return None
    domain, introduction = _OFFICIAL_SUBMISSION_EMAILS[slug]
    matched = re.search(introduction + _ROLE_EMAIL, visible_text,
                        flags=re.IGNORECASE | re.DOTALL)
    if not matched:
        return None
    email = matched.group(1).lower()
    return email if len(email) <= 254 and email.rsplit('@', 1)[-1] == domain else None


def draft_from_html(html, *, slug, source_url, checked_at, source_allowlist):
    """Read one *pre-approved* page. Returns a tentative candidate, never edits."""
    if not isinstance(html, str) or len(html) > 2_000_000 or not html.strip():
        raise ValueError('Missing or oversized HTML')
    if source_allowlist.get(slug) != source_url or slug not in _PILOT_EVIDENCE_RULES:
        raise ValueError('Source or pilot slug not in independently reviewed allowlist')
    if not isinstance(checked_at, str) or date.fromisoformat(checked_at).isoformat() != checked_at:
        raise ValueError('Invalid check date')
    parser = _PilotVisibleText()
    parser.feed(html)
    visible = ' '.join(''.join(parser.parts).split())
    folded = unicodedata.normalize('NFKD', visible.casefold())
    folded = ''.join(c for c in folded if not unicodedata.combining(c))
    pattern, intended = _PILOT_EVIDENCE_RULES[slug]
    found = re.search(pattern, folded)
    # A positive fragment may coexist with a sentence expressly closing
    # submissions. Do not call that "open" just because the regex matched.
    # Keep this intentionally narrow so "no recibimos manuscritos físicos"
    # and "no publicamos ficción" don't suppress valid electronic/essay routes.
    negation = re.compile(
        r'recepcion de (?:manuscritos|originales) (?:esta )?(?:cerrada|pausada|suspendida)'
        r'|no lo (?:haga|envie|mande) por correo electronico'
        # Closure wordings observed in real editorial FAQs. Do NOT classify
        # format/genre restrictions ("no recibimos originales en papel",
        # "no aceptamos manuscritos de ficcion") as general closure.
        r'|(?:ya no (?:estamos )?(?:aceptando|recibiendo|admitiendo)'
        r'|no (?:estamos )?(?:aceptando|recibiendo|admitiendo)'
        r'|no (?:aceptamos|recibimos|admitimos))'
        r'\s+(?:manuscritos|originales)\b'
        r'(?!\s+(?:fisicos?|impresos?|en papel|en formato fisico|de ficcion))'
    )
    # The official page may announce closure much later than its initial
    # submission instructions. For the FIVE reviewed official sources, any
    # general contradictory statement makes an 'open' suggestion unknown.
    # Format/genre-only restrictions are excluded by negation's regex.
    nearby = folded if found else ''
    conflict = intended == 'open' and bool(found) and bool(negation.search(nearby))
    suggestion = 'unknown' if conflict else intended if found else 'unknown'
    scope = 'group_general' if slug == 'alfaguara' else 'publisher_specific'
    contact = submission_email_candidate(visible, slug=slug, suggestion=suggestion)
    return {
        'publisher_slug': slug, 'source_url': source_url,
        'checked_at': checked_at, 'detected': bool(found),
        'suggestion': suggestion, 'scope': scope,
        'submission_email_candidate': contact,
        'submission_email_basis': 'explicit_manuscript_instruction' if contact else 'not_proven',
        'manual_review_required': True, 'publish': False,
        # Only a matching phrase is retained; no email/contact information.
        'matching_fragment': re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[correo]', found.group(0))[:180] if found else '',
        'reason': 'Conflicting intake wording: human review' if conflict else
                  'Explicit known-page pattern' if found else 'No matching explicit statement',
    }


def run_live_pilot(cases: dict, vetted_hosts: dict, *,
                   as_of: date, cache_dir: Path, budget: int = 12,
                   http=None) -> dict:
    """Five reviewed URLs, via existing CachedHTTP or offline fake. Review-only."""
    if (cases.get("schema_version") != 1 or
            not isinstance(cases.get("cases"), list) or len(cases["cases"]) != 5):
        raise ValueError("Exactly five pre-reviewed cases required")
    if (vetted_hosts.get("schema_version") != 1 or
            not isinstance(vetted_hosts.get("publishers"), dict)):
        raise ValueError("Invalid host allowlist")
    if type(budget) is not int or not 1 <= budget <= 20:
        raise ValueError("Pilot budget must be 1..20 physical requests")
    if date.fromisoformat(cases["checked_on"]) > as_of:
        raise ValueError("Source review date is in future")
    urls = {}
    expected = {}
    hosts = set()
    for case in cases["cases"]:
        if not isinstance(case, dict):
            raise ValueError("Malformed case")
        slug, url = case.get("slug"), case.get("official_url")
        host = safe_host(url)
        allowed = vetted_hosts["publishers"].get(slug)
        if (not isinstance(slug, str) or slug in urls or
                url != _PILOT_OFFICIAL_URLS.get(slug) or not host or
                not isinstance(allowed, dict) or
                host not in allowed.get("hosts", [])):
            raise ValueError("Unreviewed URL or missing independent host approval")
        reviewed = case.get("expected_pilot_candidate")
        if reviewed is not None and reviewed not in {"open", "paused", "unknown", "group_only"}:
            raise ValueError("Invalid reviewed pilot expectation")
        urls[slug] = url
        expected[slug] = reviewed
        hosts.add(host)
    if set(urls) != set(_PILOT_EVIDENCE_RULES):
        raise ValueError("Must use exactly the five fixed pilot subjects")
    if http is None:
        # Reuse existing robots, cache, redirection and physical-request budget.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from reading_editorial_sources import CachedHTTP
        http = CachedHTTP(cache_dir, sorted(hosts), budget=budget, delay=1.5)
    results = []
    for slug, url in urls.items():
        # CachedHTTP.hits also counts cached robots.txt responses.
        # An increase in hits cannot prove that THIS page was cached.
        key = hashlib.sha256(url.encode()).hexdigest()
        stamp = cache_dir / (key + ".json")
        cached_body = cache_dir / (key + ".body")
        page_was_cached = None
        if isinstance(getattr(http, "cache", None), Path) and callable(getattr(http, "now", None)):
            page_was_cached = False
            try:
                if cached_body.is_file() and stamp.is_file():
                    previous = json.loads(stamp.read_text(encoding="utf-8"))
                    age = http.now() - previous["retrieved_at"]
                    page_was_cached = 0 <= age < 86400 and cached_body.stat().st_size <= 2_000_000
            except (OSError, ValueError, KeyError, TypeError):
                page_was_cached = False
        try:
            body = http.get(url, ttl=86400, limit=2_000_000)
            if not isinstance(body, bytes):
                raise ValueError("CachedHTTP returned non-bytes")
            result = draft_from_html(body.decode("utf-8", errors="replace"),
                                     slug=slug, source_url=url,
                                     checked_at=as_of.isoformat(),
                                     source_allowlist=urls)
            result["retrieval"] = "ok"
            result["content_sha256"] = hashlib.sha256(body).hexdigest()
            result["content_bytes"] = len(body)
            result["served_from_cache"] = page_was_cached
            # CachedHTTP stamps the original retrieval time. A cached copy
            # analysed today is not proof it was fetched again today.
            result["source_retrieved_at_unix"] = None
            if stamp.is_file():
                try:
                    value = json.loads(stamp.read_text(encoding="utf-8")).get("retrieved_at")
                    if isinstance(value, (int, float)) and value >= 0:
                        result["source_retrieved_at_unix"] = value
                except (OSError, ValueError, TypeError):
                    pass
        except (OSError, ValueError, UnicodeError) as exc:
            result = {"publisher_slug": slug, "source_url": url,
                      "checked_at": as_of.isoformat(), "suggestion": "unknown",
                      "matching_fragment": "", "retrieval": "blocked_or_failed",
                      "error_type": type(exc).__name__,
                      "content_sha256": None, "content_bytes": None,
                      "served_from_cache": None,
                      "source_retrieved_at_unix": None,
                      "manual_review_required": True, "publish": False}
        result["previous_manual_expectation"] = expected[slug]
        result["agrees_with_previous_review"] = (
            result["suggestion"] == expected[slug]
            if expected[slug] is not None and result["retrieval"] == "ok" else None
        )
        results.append(result)
    # Bridge to the EXISTING E4 observation contract. These are draft
    # observations, not approved evidence: review() must reject their origin.
    # Excluding unknown/error avoids inventing reception status or a source.
    purposes = {
        "open": "submissions_open",
        "paused": "submissions_paused",
        "group_only": "group_submission_channel",
    }
    pending_observations = []
    for result in results:
        status = result["suggestion"]
        fragment = result.get("matching_fragment", "")
        if result["retrieval"] != "ok" or status not in purposes or not fragment:
            continue
        summary = "Extracto por comprobar: " + fragment[:250]
        if "@" in summary:
            continue
        pending_observations.append({
            "id": "pilot-" + result["publisher_slug"] + "-" + as_of.strftime("%Y%m%d"),
            "publisher_slug": result["publisher_slug"],
            "purpose": purposes[status],
            "scope": result["scope"],
            "source_url": result["source_url"],
            "checked_at": as_of.isoformat(),
            "evidence_summary": summary[:300],
            "origin": "html_pilot_unreviewed",
        })
    return {
        "schema_version": 1, "as_of": as_of.isoformat(),
        "kind": "five_official_pages_review_only",
        "pending_review_observations": {
            "schema_version": 1,
            "observations": pending_observations,
        },
        "compared_to_prior_review": sum(r["agrees_with_previous_review"] is not None for r in results),
        "matched_prior_review": sum(r["agrees_with_previous_review"] is True for r in results),
        "differences_needing_human_review": sum(r["agrees_with_previous_review"] is False for r in results),
        "retrieval_failures": sum(r["retrieval"] != "ok" for r in results),
        "results": results,
        "requests_physical": getattr(http, "requests", None),
        "cache_hits": getattr(http, "hits", None),
        "request_budget": budget,
        "published": False, "writes_to_public_data": False,
        "manual_review_required": True,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--observations", type=Path)
    p.add_argument("--trusted-hosts", type=Path, required=True)
    p.add_argument("--as-of", type=date.fromisoformat, required=True)
    p.add_argument("--live-pilot", action="store_true")
    p.add_argument("--pilot-cases", type=Path)
    p.add_argument("--cache-dir", type=Path,
                   default=Path(".ci/reading-editorial-cache"))
    p.add_argument("--budget", type=int, default=12)
    p.add_argument("--output", type=Path)
    opts = p.parse_args(argv)
    try:
        with opts.trusted_hosts.open(encoding="utf-8") as stream:
            trusted = json.load(stream)
        if opts.live_pilot:
            if opts.observations is not None or opts.pilot_cases is None:
                raise ValueError("Use --pilot-cases only for live pilot")
            with opts.pilot_cases.open(encoding="utf-8") as stream:
                cases = json.load(stream)
            result = run_live_pilot(cases, trusted, as_of=opts.as_of,
                                    cache_dir=opts.cache_dir, budget=opts.budget)
        else:
            if opts.observations is None or opts.pilot_cases is not None:
                raise ValueError("Use --observations only for offline mode")
            with opts.observations.open(encoding="utf-8") as stream:
                observed = json.load(stream)
            result = review(observed, trusted, as_of=opts.as_of)
        if opts.output:
            dest = opts.output.as_posix()
            if (not dest.startswith(".ci/reading-intake/") or
                    ".." in opts.output.parts or opts.output.suffix != ".json"):
                raise ValueError("Report path must be .ci/reading-intake/*.json")
            opts.output.parent.mkdir(parents=True, exist_ok=True)
            opts.output.write_text(json.dumps(result, indent=2,
                                              sort_keys=True, ensure_ascii=False) + "\n",
                                   encoding="utf-8")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Pilot failed safely: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
