#!/usr/bin/env python3
"""Claude Code Bash hook: avoid accidental merges and destructive Git writes.

An agent guardrail, not repository authorization: GitHub API operations and
commands executed outside Claude Code are not intercepted here.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

CONTROL = {";", "&&", "||", "|", "&", ";;", "|&"}
FORCE_FLAGS = {"-f", "--force", "--force-with-lease", "--force-if-includes"}
MASS_PUSH_FLAGS = {"--all", "--mirror", "--delete", "-d", "--prune", "--tags"}


def split_commands(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    segments: list[list[str]] = [[]]
    for token in lexer:
        if token in CONTROL:
            segments.append([])
        else:
            segments[-1].append(token)
    return segments


def _command_arguments(tokens: list[str], executable: str) -> list[str] | None:
    if not tokens or tokens[0] != executable:
        return None
    args = tokens[1:]
    # GitHub CLI/global git options before the verb (-R, -C etc.) do not
    # alter the safety restriction.
    while args:
        if args[0] in {"-C", "-c", "--git-dir", "--work-tree", "-R", "--repo", "--hostname"}:
            args = args[2:]
        elif args[0].startswith("-"):
            args = args[1:]
        else:
            break
    return args


def unsafe_command(segment: list[str]) -> str | None:
    gh = _command_arguments(segment, "gh")
    if gh:
        if gh[0] == "pr" and (_command_arguments(gh, "pr") or [])[:1] == ["merge"]:
            return "El merge de PR está reservado al autor."
        if gh[0] == "api" and any(
            re.fullmatch(r"(?:https?://api\.github\.com)?/?repos/[^/]+/[^/]+/pulls/\d+/merge(?:\?.*)?", arg)
            for arg in gh[1:]
        ):
            return "El endpoint de merge de PR está reservado al autor."

    git = _command_arguments(segment, "git")
    if not git:
        return None
    verb, *args = git
    if verb == "push":
        if any(flag in args or any(a.startswith(flag + "=") for a in args) for flag in FORCE_FLAGS | MASS_PUSH_FLAGS):
            return "Prohibido el push forzado o masivo."
        refs = [arg for arg in args if not arg.startswith("-")]
        if any(ref.startswith(("+", ":")) for ref in refs[1:]):
            return "Push forzado o eliminación remota por refspec prohibido."
        # Bare/default pushes are ambiguous: they might update main.
        if len(refs) < 2 or any(ref in {"HEAD", "main", "refs/heads/main"} or
                                 ref.lstrip("+").split(":")[-1] in {"main", "refs/heads/main"}
                                 for ref in refs[1:]):
            return "Push sin rama explícita o dirigido a main."
    elif verb == "merge":
        return "No fusionar ramas desde el agente; integración reservada al autor."
    elif verb == "pull" and "--ff-only" not in args:
        return "git pull puede hacer un merge implícito; usa fetch o --ff-only."
    elif verb == "reset" and "--hard" in args:
        return "Reset destructivo prohibido."
    elif verb == "clean" and any(a.startswith("-") and "f" in a for a in args) and not any(
        a == "--dry-run" or (a.startswith("-") and not a.startswith("--") and "n" in a)
        for a in args
    ):
        return "Limpieza destructiva prohibida."
    elif verb == "branch" and (
        "-D" in args
        or (any(v in args for v in ("-d", "--delete")) and any(v in args for v in ("-f", "--force")))
        or any(v.startswith("-") and not v.startswith("--") and "d" in v and "f" in v for v in args)
    ):
        return "Borrado forzado de rama prohibido."
    elif verb == "checkout" and "." in args:
        return "Descartar todos los cambios está prohibido."
    elif verb == "restore" and "." in args:
        return "Restaurar todo el árbol está prohibido."
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "")
        if not isinstance(command, str):
            return 2
        segments = split_commands(command)
    except (ValueError, TypeError) as exc:
        print(f"BLOCKED: entrada Bash inválida ({exc}).", file=sys.stderr)
        return 2

    for segment in segments:
        reason = unsafe_command(segment)
        if reason:
            print(f"BLOCKED: {reason} No ejecutes este comando como agente.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
