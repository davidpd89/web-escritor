#!/bin/sh
# Claude Code hook bootstrap. Only exit 0 (allow) or 2 (block).
# In PreToolUse, 1/126/127 would fail open instead of denying the Bash call.
if [ -z "${CLAUDE_PROJECT_DIR:-}" ]; then
  printf '%s\n' 'BLOCKED: CLAUDE_PROJECT_DIR is unavailable.' >&2
  exit 2
fi
if command -v python3 >/dev/null 2>&1; then
  interpreter=python3
elif command -v python >/dev/null 2>&1; then
  interpreter=python
else
  printf '%s\n' 'BLOCKED: Python is unavailable; cannot run Git guard.' >&2
  exit 2
fi

"$interpreter" "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-main.py"
result=$?
if [ "$result" -ne 0 ]; then
  if [ "$result" -ne 2 ]; then
    printf 'BLOCKED: Git guard failed (exit %s).\n' "$result" >&2
  fi
  exit 2
fi
exit 0
