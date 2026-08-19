#!/usr/bin/env python3
"""Lightweight secret scanner for tracked files.

Scans tracked files for patterns likely to be API keys (sk-..., sk-proj-...)
and reports redacted matches. Intended for manual use before commits.
"""
import re
import subprocess
import sys

patterns = [
    re.compile(r'sk-[A-Za-z0-9_-]{20,}'),
    re.compile(r'sk-proj-[A-Za-z0-9_-]{10,}'),
    # match only if OPENAI_API_KEY has a value (non-empty) to avoid false positives in .env.example
    re.compile(r'OPENAI_API_KEY\s*=\s*\S+')
]

def git_tracked_files():
    p = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
    return p.stdout.splitlines()

def scan_file(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f, start=1):
                for pat in patterns:
                    m = pat.search(line)
                    if m:
                        s = m.group(0)
                        redacted = s[:6] + '...' + s[-4:]
                        print(f"POSSIBLE SECRET: {path}:{i}: {redacted}")
                        return 1
    except Exception:
        return 0
    return 0

def main():
    files = git_tracked_files()
    found = 0
    for f in files:
        found += scan_file(f)
    if found:
        print('\nSecrets scanning failed.')
        sys.exit(2)
    print('No obvious secrets found in tracked files.')

if __name__ == '__main__':
    main()
