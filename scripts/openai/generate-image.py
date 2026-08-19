#!/usr/bin/env python3
"""Skeleton helper to generate images with OpenAI API.

This script reads the OPENAI_API_KEY from the environment. It intentionally
does NOT accept an API key via CLI to avoid accidental leakage in shells
or logs.

Usage (example):
  python scripts/openai/generate-image.py --prompt "A cover art" --out assets/img/cover.png

This is a skeleton: it does not perform a network call by default. Implement
the call following official OpenAI documentation when authorized.
"""
import os
import argparse
import sys

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--prompt', required=True)
    p.add_argument('--out', required=True, help='Output image path')
    p.add_argument('--size', default='1024x1024')
    p.add_argument('--live', action='store_true', help='Perform a real API call (manual)')
    return p.parse_args()

def main():
    args = parse_args()
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        print('OPENAI_API_KEY not configured in environment. Aborting.')
        sys.exit(1)

    print('Ready to generate image (dry run).')
    print('Prompt:', args.prompt)
    print('Output:', args.out)
    print('Size:', args.size)
    if not args.live:
        print('\nDry run complete. To perform a real generation, re-run with --live after manual review.')
        sys.exit(0)

    print('Live generation requested. Implement API interaction here following official docs.')
    # TODO: Implement actual API call only after authorization and careful cost control.

if __name__ == '__main__':
    main()
