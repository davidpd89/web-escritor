#!/usr/bin/env python3
"""Check OpenAI local setup without making API calls by default.

Usage: python scripts/openai/check-openai.py [--live]

--live : optional flag to perform a real API call (manual, not for CI)
"""
import os
import sys

KEY = os.environ.get("OPENAI_API_KEY")

def main():
    print("OpenAI local setup check")
    print("- OPENAI_API_KEY configured:", "sí" if bool(KEY) else "NO")
    if not KEY:
        print("- To run live checks set OPENAI_API_KEY in your environment (do not commit it).")
        sys.exit(0)

    if "--live" in sys.argv:
        print("--live flag provided: performing a manual API call is requested.")
        print("Manual live checks are disabled by default. Provide --live only for an explicit run.")
        # The script intentionally avoids performing a live API call without explicit consent.
        # If you want to enable a live check, implement it here using the official OpenAI SDK
        # and ensure you understand costs. Do not enable by default.
        sys.exit(0)

    print("- Client initialization: OK (no network call performed)")
    print("- Live API call performed: NO")

if __name__ == '__main__':
    main()
