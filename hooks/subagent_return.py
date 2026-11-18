#!/usr/bin/env python3
"""SubagentStop: exige o bloco de retorno.md dos cinco papéis. Com --stop (Stop): lembra a ficha. Falha aberto."""
import json
import os
import re
import sys

ROLES = {"editor-cientifico", "auditor-cientifico", "diagramador", "imagens", "auditor-grafico"}
STATUS = re.compile(r"^\W*Status:\W*(PRONTO_COM_RESSALVAS|PRONTO|PRECISA_DE_DADO|BLOQUEADO)\W*$", re.M)
SKILL_USED = re.compile(r'"skill"\s*:\s*"(?:[\w-]+:)?editor-chefe"|<command-name>/?(?:[\w-]+:)?editor-chefe</command-name>')
AUDITORS = {"auditor-cientifico", "auditor-grafico"}
PHASE_DONE = re.compile(r"fase\s*\d+\S*\s+(?:está\s+|foi\s+)?conclu[íi]d", re.I)


def role(data):
    return (data.get("agent_type") or "").split(":")[-1]


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))


def subagent(data):
    text = data.get("last_assistant_message") or ""
    fields = ["Arquivos entregues:", "Pendências:"] + (["Nota:", "Achados:"] if role(data) in AUDITORS else [])
    if role(data) not in ROLES or (STATUS.search(text) and all(f in text for f in fields)):
        return
    if data.get("stop_hook_active"):
        print("subagent_return: aviso, o papel seguiu sem o bloco de retorno; liberado", file=sys.stderr)
        return
    block("Falta o bloco de retorno. Devolva a mensagem final no formato de retorno.md, "
          "com 'Status:' (PRONTO, PRONTO_COM_RESSALVAS, PRECISA_DE_DADO ou BLOQUEADO), 'Arquivos entregues:' e 'Pendências:' (auditores também 'Nota:' e 'Achados:').")


def chief_skill_used(data):
    if not data.get("transcript_path"):
        return False
    with open(data["transcript_path"], encoding="utf-8", errors="replace") as f:
        return bool(SKILL_USED.search(f.read()))


def ficha_written(path):
    """Houve Write/Edit em ficha*.md desde a última mensagem real do usuário?"""
    if not path:
        return False
    written = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            entry = json.loads(line)
            content = (entry.get("message") or {}).get("content")
            if entry.get("type") == "user":
                if isinstance(content, str) or any(c.get("type") != "tool_result" for c in content or []):
                    written = False
                continue
            for c in content if isinstance(content, list) else []:
                name = os.path.basename((c.get("input") or {}).get("file_path") or "")
                if c.get("type") == "tool_use" and c.get("name") in ("Write", "Edit", "MultiEdit") \
                        and name.startswith("ficha") and name.endswith(".md"):
                    written = True
    return written


def stop(data):
    text = data.get("last_assistant_message") or ""
    if data.get("stop_hook_active") or not (role(data) == "editor-chefe" or chief_skill_used(data)):
        return
    if PHASE_DONE.search(text) and not ficha_written(data.get("transcript_path")):
        block("Houve fase concluída sem atualização da ficha. Atualize e entregue a ficha.md do projeto.")


def main(argv):
    try:
        data = json.load(sys.stdin)
        (stop if "--stop" in argv else subagent)(data)
    except Exception as e:  # falha aberto
        print(f"subagent_return: aviso, não foi possível conferir ({e}); liberado", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
