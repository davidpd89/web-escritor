#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

p = ROOT / 'scripts/build-site-shell.py'
text = p.read_text(encoding='utf-8')
old_sig = 'def render_explore(nav: dict, by_id: dict[str, Entry], current_path: str) -> str:'
new_sig = 'def render_explore(nav: dict, by_id: dict[str, Entry], current_path: str, allow_newsletter: bool = True) -> str:'
if text.count(old_sig) != 1:
    raise SystemExit(f'render_explore signature count={text.count(old_sig)}')
text = text.replace(old_sig, new_sig, 1)

form_start = text.index("        '    <form class=\"explore-subscribe\"")
form_end_token = "        '    </form>\\n'\n"
form_end = text.index(form_end_token, form_start) + len(form_end_token)
form_block = text[form_start:form_end]
assignment = "    subscribe_markup = (\n" + form_block + "    ) if allow_newsletter else ''\n    runtime_markup = '<script defer src=\"/assets/newsletter-general.js\"></script>' if allow_newsletter else ''\n\n"
return_pos = text.rfind('    return (', 0, form_start)
if return_pos < 0:
    raise SystemExit('render_explore return not found')
text = text[:return_pos] + assignment + text[return_pos:form_start] + '        + subscribe_markup\n' + text[form_end:]

old_runtime = "        '<script defer src=\"/assets/newsletter-general.js\"></script>'\n"
if text.count(old_runtime) != 1:
    raise SystemExit(f'runtime literal count={text.count(old_runtime)}')
text = text.replace(old_runtime, '        + runtime_markup\n', 1)

old_dialog = '    dialog_html = render_explore(nav, by_id, current_path)\n'
new_dialog = '''    # Public/generated CSP allows the subscription Worker. Privacy-sensitive\n    # tools keep a handwritten stricter CSP (often connect-src 'none'); never\n    # weaken that local-only boundary just to make the global Explore form post.\n    custom_csp = bool(EXISTING_CSP_RE.search(original)) and CSP_START not in original\n    allow_newsletter = (not custom_csp) or ("subscribe.davidpd89.workers.dev" in original)\n    dialog_html = render_explore(nav, by_id, current_path, allow_newsletter=allow_newsletter)\n'''
if text.count(old_dialog) != 1:
    raise SystemExit(f'dialog call count={text.count(old_dialog)}')
text = text.replace(old_dialog, new_dialog, 1)
p.write_text(text, encoding='utf-8')

# Static contract protects the local-only CSP exception.
test_path = ROOT / 'tests/test-newsletter-client-contract.mjs'
test = test_path.read_text(encoding='utf-8')
needle = "assert.match(builderSource, /newsletter-general\\.js/,\n  'shell builder must load the shared general newsletter runtime');\n"
insert = needle + "assert.match(builderSource, /allow_newsletter/,\n  'shell builder must conditionally omit newsletter UI for stricter custom CSP pages');\nassert.match(builderSource, /subscribe\\.davidpd89\\.workers\\.dev/,\n  'shell builder CSP boundary must key off the canonical subscription Worker');\n"
if test.count(needle) != 1:
    raise SystemExit(f'static builder assertion anchor count={test.count(needle)}')
test_path.write_text(test.replace(needle, insert, 1), encoding='utf-8')

# Browser contract: a manuscript tool with connect-src/form-action none keeps
# Explore navigation but must not expose or load the newsletter runtime.
qa_path = ROOT / 'qa/newsletter-consent-browser.mjs'
qa = qa_path.read_text(encoding='utf-8')
anchor = "  await context.close();\n  console.log('newsletter-consent-browser: inline + Explore + shell-only + popup contracts passed');"
extra = '''  const strict = await context.newPage();\n  const strictResponse = await strict.goto(`${ORIGIN}/herramientas/manuscrito/`, { waitUntil: 'domcontentloaded' });\n  assert.ok(strictResponse?.ok(), 'local-only manuscript tool must load');\n  await strict.locator('[data-explore-open]').first().click();\n  await strict.locator('[data-explore-dialog]').waitFor({ state: 'visible' });\n  assert.equal(await strict.locator('#newsletter-form-explore').count(), 0,\n    'local-only CSP page must not expose an unusable newsletter form');\n  assert.equal(await strict.locator('script[src*="newsletter-general.js"]').count(), 0,\n    'local-only CSP page must not load the newsletter runtime');\n  await strict.close();\n\n  await context.close();\n  console.log('newsletter-consent-browser: inline + Explore + shell-only + popup + local-only CSP contracts passed');'''
if qa.count(anchor) != 1:
    raise SystemExit(f'browser QA anchor count={qa.count(anchor)}')
qa_path.write_text(qa.replace(anchor, extra, 1), encoding='utf-8')

subprocess.run(['python3', 'scripts/build-site-shell.py'], cwd=ROOT, check=True)
subprocess.run(['python3', 'scripts/build-site-shell.py', '--check'], cwd=ROOT, check=True)
subprocess.run(['node', 'tests/test-newsletter-client-contract.mjs'], cwd=ROOT, check=True)
print('finish_newsletter_csp_292: PASS')
