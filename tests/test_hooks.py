import json
import subprocess
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"


def run(script, payload, *args, raw=None):
    data = raw if raw is not None else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(HOOKS / script), *args], input=data, capture_output=True, text=True
    )


def decision(proc):
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


def project(tmp_path, ficha="aprovado: capitulo-1-v1.docx\n"):
    (tmp_path / "originais").mkdir()
    (tmp_path / "ficha.md").write_text(ficha, encoding="utf-8")
    return tmp_path


def write(path, cwd, tool="Write"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(cwd), "tool_input": {"file_path": str(path)}}


def denied(proc):
    out = decision(proc).get("hookSpecificOutput", {})
    return out.get("permissionDecision") == "deny" and "versão aprovada não muda; gere uma versão nova" in out["permissionDecisionReason"]


def test_guard_blocks_originais(tmp_path):
    p = project(tmp_path)
    assert denied(run("editorial_guard.py", write(p / "originais" / "x.docx", p)))
    rel = write("originais/x.docx", p, tool="Edit")
    assert denied(run("editorial_guard.py", rel))


def test_guard_blocks_approved_version(tmp_path):
    p = project(tmp_path)
    assert denied(run("editorial_guard.py", write(p / "capitulo-1-v1.docx", p)))
    assert denied(run("editorial_guard.py", write("capitulo-1-v1.docx", p, tool="MultiEdit")))


def test_guard_allows_new_version(tmp_path):
    p = project(tmp_path)
    assert decision(run("editorial_guard.py", write(p / "capitulo-1-v2.docx", p))) == {}
    assert decision(run("editorial_guard.py", write(p / "ficha.md", p))) == {}
    outside = tmp_path.parent / "solto"
    outside.mkdir(exist_ok=True)
    assert decision(run("editorial_guard.py", write(outside / "originais" / "a.txt", outside))) == {}


def msg(text, active=False, agent="clinic-editorial:diagramador"):
    return {"hook_event_name": "SubagentStop", "agent_type": agent, "stop_hook_active": active, "last_assistant_message": text}


def test_return_missing_asks_once():
    first = run("subagent_return.py", msg("terminei"))
    assert decision(first)["decision"] == "block"
    second = run("subagent_return.py", msg("terminei", active=True))
    assert decision(second) == {} and second.returncode == 0 and second.stderr.strip()


def test_return_present_passes():
    ok = "Resumo\nStatus: PRONTO_COM_RESSALVAS\nArquivos entregues:\n- a\n"
    assert decision(run("subagent_return.py", msg(ok))) == {}
    assert decision(run("subagent_return.py", msg("sem bloco", agent="Explore"))) == {}


def test_stop_reminds_ficha_once():
    stop = {"hook_event_name": "Stop", "agent_type": "editor-chefe", "stop_hook_active": False,
            "last_assistant_message": "A fase 2 está concluída."}
    assert decision(run("subagent_return.py", stop, "--stop"))["decision"] == "block"
    stop["last_assistant_message"] = "A fase 2 está concluída e a ficha foi atualizada."
    assert decision(run("subagent_return.py", stop, "--stop")) == {}


def test_hook_fails_open_on_bad_json():
    for script, args in (("editorial_guard.py", ()), ("subagent_return.py", ()), ("subagent_return.py", ("--stop",))):
        proc = run(script, None, *args, raw="{não é json")
        assert proc.returncode == 0 and proc.stdout.strip() == "" and proc.stderr.strip()
