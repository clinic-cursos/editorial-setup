#!/usr/bin/env python3
"""SubagentStop: exige o bloco de retorno.md dos cinco papéis. Com --stop (Stop): lembra a ficha. Falha aberto."""
import json
import re
import sys

ROLES = {"editor-cientifico", "auditor-cientifico", "diagramador", "imagens", "auditor-grafico"}
STATUS = re.compile(r"^\W*Status:\W*(PRONTO_COM_RESSALVAS|PRONTO|PRECISA_DE_DADO|BLOQUEADO)\W*$", re.M)
PHASE_DONE = re.compile(r"fase\s*\d+\S*\s+(?:está\s+|foi\s+)?conclu[íi]d", re.I)


def role(data):
    return (data.get("agent_type") or "").split(":")[-1]


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))


def subagent(data):
    if role(data) not in ROLES or STATUS.search(data.get("last_assistant_message") or ""):
        return
    if data.get("stop_hook_active"):
        print("subagent_return: aviso, o papel seguiu sem o bloco de retorno; liberado", file=sys.stderr)
        return
    block("Falta o bloco de retorno. Devolva a mensagem final no formato de retorno.md, "
          "com a linha 'Status:' (PRONTO, PRONTO_COM_RESSALVAS, PRECISA_DE_DADO ou BLOQUEADO).")


def stop(data):
    text = data.get("last_assistant_message") or ""
    if role(data) != "editor-chefe" or data.get("stop_hook_active"):
        return
    if PHASE_DONE.search(text) and "ficha" not in text.lower():
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
