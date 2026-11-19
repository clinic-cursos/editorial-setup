#!/usr/bin/env python3
"""PreToolUse: nega escrita em originais/ e em versão aprovada de um projeto com ficha.md. Falha aberto."""
import json
import os
import sys

MSG = "versão aprovada não muda; gere uma versão nova"


def project_root(path):
    d = os.path.dirname(path)
    while True:
        if os.path.isfile(os.path.join(d, "ficha.md")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def approved(root):
    found = set()
    with open(os.path.join(root, "ficha.md"), encoding="utf-8") as f:
        for line in f:
            key, sep, val = line.strip().lstrip("-* ").partition(":")
            if sep and key.strip().lower() == "aprovado" and val.strip():
                p = val.strip().strip("`'\"")
                found.add(os.path.realpath(os.path.join(root, p)))
    return found


def check(data):
    target = (data.get("tool_input") or {}).get("file_path")
    if not target:
        return None
    path = os.path.realpath(os.path.join(data.get("cwd") or os.getcwd(), target))
    root = project_root(path)
    if root is None:
        return None
    root = os.path.realpath(root)
    rel = os.path.relpath(path, root).split(os.sep)
    if rel[0] == "originais" or path in approved(root):
        return MSG
    return None


def main():
    try:
        reason = check(json.load(sys.stdin))
    except Exception as e:  # falha aberto
        print(f"editorial_guard: aviso, não foi possível conferir ({e}); escrita liberada", file=sys.stderr)
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
