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
# The direct Bash guard is conservative: only known Git push options are
# allowed to precede an explicit remote AND refspec. Unknown options deny.
# Git push manual: https://git-scm.com/docs/git-push
PUSH_SWITCHES = {
    "-u", "--set-upstream", "-n", "--dry-run", "--porcelain",
    "-q", "--quiet", "-v", "--verbose", "--progress", "--no-progress",
    "--atomic", "--no-atomic", "--follow-tags", "--no-follow-tags",
    "--signed", "--no-signed", "--no-verify", "--verify",
    "--thin", "--no-thin", "--ipv4", "--ipv6", "-4", "-6",
}
PUSH_VALUE_FLAGS = {"--receive-pack", "--exec", "--push-option", "-o"}
PUSH_VALUE_EQUALS = ("--receive-pack=", "--exec=", "--push-option=")
PUSH_VALUE_CHOICES = ("--signed=", "--recurse-submodules=")


def push_positionals(args: list[str]) -> tuple[list[str], str | None]:
    """Exclude recognized option values; do not mistake them for refspecs."""
    positionals: list[str] = []
    options_done = False
    index = 0
    while index < len(args):
        arg = args[index]
        if arg.startswith("#"):
            return [], "Push con comentario de shell ambiguo."
        if not options_done and arg == "--":
            options_done = True
        elif not options_done and arg.startswith("-"):
            if arg in FORCE_FLAGS | MASS_PUSH_FLAGS or any(
                arg.startswith(flag + "=") for flag in FORCE_FLAGS | MASS_PUSH_FLAGS
            ):
                return [], "Push forzado, masivo o con eliminación prohibido."
            if arg in PUSH_VALUE_FLAGS:
                # Consume the next token even if it resembles a remote/ref.
                if index + 1 >= len(args):
                    return [], "Opción de push sin valor; destino ambiguo."
                index += 1
            elif arg.startswith(PUSH_VALUE_EQUALS):
                if not arg.split("=", 1)[1]:
                    return [], "Opción de push sin valor."
            elif arg.startswith("-o") and len(arg) > 2:
                pass  # -omessage is the attached form of -o message.
            elif arg in PUSH_SWITCHES or arg.startswith(PUSH_VALUE_CHOICES):
                pass
            else:
                return [], "Opción de push no reconocida: no se puede demostrar el destino."
        else:
            if arg.startswith(("-", "+", ":")):
                return [], "Refspec ambiguo, forzado o de eliminación."
            positionals.append(arg)
        index += 1
    return positionals, None


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
        if gh[0] == "api":
            # REST: synchronous/asynchronous PR merge and direct branch merges.
            # GitHub Docs: /pulls/{n}/merge-async and /repos/{owner}/{repo}/merges.
            if any(
                re.fullmatch(
                    r"(?:https?://api\.github\.com)?/?repos/[^/]+/[^/]+/"
                    r"(?:pulls/\d+/merge(?:-async)?|merges)(?:\?.*)?",
                    arg,
                )
                for arg in gh[1:]
            ):
                return "Las fusiones REST de PR o ramas están reservadas al autor."
            # GraphQL mutations that merge immediately or schedule future merge.
            # Queries and benign mutations remain available.
            if any(
                re.fullmatch(r"(?:graphql|/?graphql|https?://[^/]+/(?:api/)?graphql)(?:\?.*)?", arg)
                for arg in gh[1:]
            ) and any(
                re.search(
                    r"\b(?:mergePullRequest|mergeBranch|enablePullRequestAutoMerge|"
                    r"enqueuePullRequest)\b",
                    arg,
                )
                for arg in gh[1:]
            ):
                return "La mutación GraphQL puede fusionar o programar una PR."

    git = _command_arguments(segment, "git")
    if not git:
        return None
    verb, *args = git
    if verb == "push":
        refs, error = push_positionals(args)
        if error:
            return error
        # Remote without explicit refspec may use push.default/remote.*.push.
        if len(refs) < 2 or any(
            ref in {"HEAD", "main", "refs/heads/main"} or
            ref.split(":")[-1] in {"main", "refs/heads/main"}
            for ref in refs[1:]
        ):
            return "Push sin remoto + rama explícita o dirigido a main."
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
        any(v in {"-d", "-D", "-m", "-M", "-C", "-f", "--delete", "--move", "--force"}
            or v.startswith(("--delete=", "--move=", "--force=")) for v in args)
        or any(v.startswith("-") and not v.startswith("--") and
               any(flag in v[1:] for flag in "dDmMfC") for v in args)
    ):
        return "No borrar, renombrar ni sobrescribir ramas desde el agente."
    elif verb == "update-ref" and (
        "--stdin" in args
        or ("-d" in args and any(ref.startswith("refs/heads/") for ref in args))
    ):
        return "El agente no debe eliminar referencias de ramas con git update-ref."
    elif verb == "symbolic-ref" and (
        "--delete" in args or "-d" in args
    ) and any(ref.startswith("refs/heads/") for ref in args):
        return "El agente no debe eliminar referencias simbólicas de ramas."
    elif verb == "checkout" and "." in args:
        return "Descartar todos los cambios está prohibido."
    elif verb == "restore" and "." in args:
        return "Restaurar todo el árbol está prohibido."
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("payload debe ser un objeto JSON")
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            raise ValueError("tool_input debe ser un objeto JSON")
        command = tool_input.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command debe ser texto no vacío")
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
