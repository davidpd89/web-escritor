# Claude Code instructions

Project policy is shared with the other coding agents. Read and follow `docs/agents/AI_WORKFLOW.md`; keep this file as a thin Claude-specific entrypoint rather than a second policy document.

When a task matches a repository skill under `.agents/skills/`, read the matching `SKILL.md` and follow it even if the current Claude client does not auto-discover that directory.

Useful mappings:

- PR/readiness verification → `.agents/skills/verify-web-change/SKILL.md`, if present
- code review → `.agents/skills/web-escritor-review/SKILL.md`, when present

Do not load every skill by default. Use only the guidance needed for the current task.
