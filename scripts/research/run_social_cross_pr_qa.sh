#!/usr/bin/env bash
# Reproduce all OFFLINE social-stats tests from four draft PR branches.
# Read-only on the repository. Does NOT merge, push, run Actions or publish.
set -euo pipefail

REPO="${SOCIAL_QA_REPO:-$(git rev-parse --show-toplevel)}"
UX="${SOCIAL_QA_UX_REF:-refs/remotes/origin/research/gpt-social-ux-2026-10-22}"
METRICOOL="${SOCIAL_QA_METRICOOL_REF:-refs/remotes/origin/research/gpt-social-metricool-2026-10-22}"
BLUESKY="${SOCIAL_QA_BLUESKY_REF:-refs/remotes/origin/research/gpt-social-bluesky-2026-10-22}"
MASTODON="${SOCIAL_QA_MASTODON_REF:-refs/remotes/origin/research/gpt-social-mastodon-2026-10-22}"

for tool in git python node; do
    command -v "$tool" >/dev/null || { echo "Missing required tool: $tool" >&2; exit 1; }
done
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/scripts/research" "$TMP/tests"

read_file() {
    local ref="$1" path="$2" expected actual
    if ! git -C "$REPO" cat-file -e "$ref:$path" 2>/dev/null; then
        echo "Missing $path at $ref; fetch that branch first" >&2
        exit 1
    fi
    git -C "$REPO" show "$ref:$path" > "$TMP/$path"
    expected="$(git -C "$REPO" rev-parse "$ref:$path")"
    actual="$(git hash-object "$TMP/$path")"
    [[ "$expected" == "$actual" ]] || { echo "Blob mismatch: $path" >&2; exit 1; }
    echo "$actual  $path"
}

for path in \
    scripts/research/gpt_social_compose.py \
    scripts/research/gpt_social_reader.mjs \
    tests/test_gpt_social_compose.py \
    tests/test_gpt_social_pipeline.py \
    tests/test_gpt_social_verified_profiles.py \
    tests/test_gpt_social_expiration.py \
    tests/test_gpt_social_reader.mjs \
    tests/test_gpt_social_python_to_js.mjs; do
    read_file "$UX" "$path"
done
for path in \
    scripts/research/gpt_metricool_threads.py \
    scripts/research/gpt_metricool_followers.py \
    tests/test_gpt_metricool_threads.py \
    tests/test_gpt_metricool_followers.py; do
    read_file "$METRICOOL" "$path"
done
for path in scripts/research/gpt_social_bluesky.py tests/test_gpt_social_bluesky.py; do
    read_file "$BLUESKY" "$path"
done
for path in scripts/research/gpt_social_mastodon.py tests/test_gpt_social_mastodon.py; do
    read_file "$MASTODON" "$path"
done

(cd "$TMP" && python -m unittest discover -s tests -p 'test_*.py' -v)
(cd "$TMP" && node --test tests/test_gpt_social_reader.mjs tests/test_gpt_social_python_to_js.mjs)
echo "QA completed from exact Git blobs; temporary worktree discarded."
