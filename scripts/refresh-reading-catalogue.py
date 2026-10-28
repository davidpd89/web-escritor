#!/usr/bin/env python3
"""Single writer for free, bounded publisher intake and generated-only PRs."""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from reading_intake_pipeline import ingest
from reading_intake_fetch import read_json, write_if_changed
from reading_ratings_refresh import refresh as refresh_ratings, google_response, hardcover_response, write_changed

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_publication', ROOT / 'scripts/publish-reading-refresh.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


def command(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def refresh(*, publish=False):
    config = read_json(ROOT / 'data/reading-intake-config.json')
    if publish and subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).strip():
        raise ValueError('La publicación automática exige un checkout limpio')
    if publish and not config.get('autopublish'):
        raise ValueError('Autopublicación desactivada en la configuración')
    # A failed previous batch stays inspectable; never pile up duplicate writers.
    opened = json.loads(publisher.publication.gh('pr', 'list', '--state', 'open', '--base', 'main', '--limit', '100', '--json', 'headRefName'))
    pending = [p['headRefName'] for p in opened if p['headRefName'].startswith('automation/reading-catalogue-')]
    if pending:
        if len(pending) != 1:
            raise ValueError('Hay varias cargas pendientes; revisar antes de continuar')
        if not publish or publisher.resume_pending(pending[0]):
            print('Carga pendiente conservada: ' + pending[0])
            return
    report = ingest(config, ROOT, ROOT / '.ci/reading-editorial-cache', apply=publish)
    write_if_changed(ROOT / '.ci/reading-intake/publisher-report.json', report)
    print(json.dumps(report['stats'], ensure_ascii=True), flush=True)
    if not publish:
        return

    # This runs DAILY, even when publishers have no new ISBNs.
    # Single writer and ONE generated PR for publisher + rating changes.
    market_path = ROOT / 'assets/reading-market.json'
    market = read_json(market_path)
    ratings_config = config.get('ratings_refresh', {})
    ratings_stats = {}
    changed_ratings = False
    if ratings_config.get('enabled', False):
        books = read_json(ROOT / 'data/reading-catalogue.json')
        now = datetime.now(timezone.utc)
        google_key = os.getenv('GOOGLE_BOOKS_API_KEY', '').strip()
        hardcover_key = os.getenv('HARDCOVER_API_KEY', '').strip()
        providers = [
            ('google_books', google_key, google_response, int(ratings_config.get('google_books_requests_per_day', 25))),
            ('hardcover', hardcover_key, hardcover_response, int(ratings_config.get('hardcover_requests_per_day', 0))),
        ]
        from reading_goodreads import GoodreadsPublic
        goodreads = GoodreadsPublic()
        providers.insert(0, ('goodreads', 'public', lambda isbn, unused: goodreads(isbn), int(ratings_config.get('goodreads_requests_per_day', 40))))
        for source, secret, query, budget in providers:
            if not secret or not budget:
                ratings_stats[source] = {'status': 'sin_credencial_o_deshabilitado'}
                continue
            # A failing provider must not prevent the publisher intake or corrupt
            # existing ratings. Failures remain in the CI report.
            def provider(isbn, query=query, secret=secret):
                return query(isbn, secret)
            market, stats = refresh_ratings(books, market, provider, now=now,
                                            budget=budget, source=source)
            ratings_stats[source] = stats
        changed_ratings = write_changed(market_path, market)
    if ratings_stats:
        write_if_changed(ROOT / '.ci/reading-intake/ratings-report.json', ratings_stats)
        print('Valoraciones: ' + json.dumps(ratings_stats, ensure_ascii=True), flush=True)
    # Recheck existing free API access once each day. While Amazon refuses
    # eligibility the provider stops at its first error and prices stay absent.
    amazon_config=config.get('amazon_price_refresh',{})
    amazon_id=os.getenv('AMAZON_CREATORS_CLIENT_ID','').strip()
    amazon_secret=os.getenv('AMAZON_CREATORS_CLIENT_SECRET','').strip()
    if amazon_config.get('enabled') and amazon_id and amazon_secret:
        from reading_amazon_market import CreatorsPrices, refresh_offers
        books=read_json(ROOT/'data/reading-catalogue.json')
        tag=config['amazon_partner_tag']
        market,price_stats=refresh_offers(books,market,CreatorsPrices(amazon_id,amazon_secret,tag),tag,
                                         datetime.now(timezone.utc),int(amazon_config.get('requests_per_day',100)))
        write_if_changed(ROOT/'.ci/reading-intake/prices-report.json',price_stats)
        print('Precios Amazon: '+json.dumps(price_stats,ensure_ascii=True),flush=True)
        changed_ratings=write_changed(market_path,market) or changed_ratings
    # A scheduled RSS item can become due without a new book or rating. Build
    # current pages first, then advance feeds inside this SAME daily writer.
    command(sys.executable, 'scripts/build-reading-catalogue.py')
    rss_config=read_json(ROOT / 'data/reading-pinterest-boards.json')
    command(sys.executable, 'scripts/build-reading-pinterest-rss.py', *(['--assign'] if rss_config.get('rss_enabled') else []))
    rss_changed=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','assets/pinterest/feeds','data/reading-pinterest-state.json'],cwd=ROOT,text=True).strip())
    if not (report['new_books'] or report['updated_books'] or changed_ratings or report['stats'].get('author_profiles_updated') or rss_changed):
        return
    # Register new routes before builders that deliberately consume git ls-files.
    command(sys.executable, 'scripts/build-reading-catalogue.py')
    command(sys.executable, 'scripts/build-editoriales.py', '--data', 'data/editoriales.json', '--output', '.')
    command(sys.executable, 'scripts/build-page-order.py')
    command('git', 'add', '--', 'assets/page-order.generated.js', 'assets/reading-market.json', 'data/reading-catalogue.json', 'data/reading-authors.json', 'data/reading-intake-state.json',
            'data/content-registry.json', 'assets/reading-covers', 'assets/reading-audio', 'recomendaciones', 'editoriales', 'editoriales-sitemap.xml', 'mapa-del-sitio/index.html')
    command('git','add','--','assets/pinterest/feeds')
    for script in ('build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        command(sys.executable, 'scripts/' + script)
    for script in ('build-reading-catalogue.py', 'build-page-order.py', 'build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        command(sys.executable, 'scripts/' + script, '--check')
    command(sys.executable, 'tests/test-reading-catalogue.py')
    command(sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_reading*.py', '-q')
    command('git', 'diff', '--check')
    changed = subprocess.check_output(
        ['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True)
    paths = [line[3:] for line in changed.splitlines()]
    if not paths or any(not publisher.allowed_path(p) for p in paths):
        raise ValueError('Cambios fuera de los artefactos permitidos: ' + str([p for p in paths if not publisher.allowed_path(p)]))
    command('git', 'add', '--', *paths)
    day = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    branch = 'automation/reading-catalogue-' + day + '-' + os.environ.get('GITHUB_RUN_ID', datetime.now().strftime('%H%M%S'))
    command('git', 'config', 'user.name', 'github-actions[bot]')
    command('git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    command('git', 'switch', '-c', branch)
    command('git', 'commit', '-m', 'Actualizar catálogo de lectura ' + day)
    command('git', 'push', 'origin', 'HEAD:refs/heads/' + branch)
    body = ROOT / '.ci/reading-intake/pr-body.md'
    body.write_text('Incorpora ' + str(len(report['new_books'])) + ' ediciones verificadas en sus fichas editoriales oficiales.\n\n'
                    'Carga sin LLM ni API de pago; portadas optimizadas, ISBN comprobados, autores y enlaces internos generados. '
                    'No importa precios ni valoraciones sin un proveedor autorizado. Los candidatos incompletos quedan pendientes.\n\n'
                    'Se ejecutan las pruebas reales del commit y las reglas de main antes de fusionar. Después se despliega y se comprueba producción.\n', encoding='utf-8')
    publisher.publication.gh('pr', 'create', '--base', 'main', '--head', branch,
                             '--title', 'Actualizar catálogo de lectura ' + day, '--body-file', str(body))
    publisher.run(branch)


def main(publish):
    try:
        refresh(publish=publish)
    except publisher.publication.StaleMerge as exc:
        # The stale bot PR is closed and regenerated by the next invocation.
        print(exc, flush=True)
        sys.exit(publisher.publication.STALE_EXIT_CODE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    main(args.publish)
