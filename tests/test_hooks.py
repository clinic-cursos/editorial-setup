import json
import subprocess
import sys
from pathlib import Path

import pytest

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


def test_guard_finds_ficha_in_parent_folder(tmp_path):
    path = "versoes/fase-1/manuscrito-v1.docx"
    p = project(tmp_path, ficha=f"aprovado: {path}\n")
    (p / path).parent.mkdir(parents=True)
    assert denied(run("editorial_guard.py", write(path, p)))


def test_guard_allows_new_version(tmp_path):
    p = project(tmp_path)
    assert decision(run("editorial_guard.py", write(p / "capitulo-1-v2.docx", p))) == {}
    assert decision(run("editorial_guard.py", write(p / "ficha.md", p))) == {}
    outside = tmp_path.parent / "solto"
    outside.mkdir(exist_ok=True)
    assert decision(run("editorial_guard.py", write(outside / "originais" / "a.txt", outside))) == {}


@pytest.mark.parametrize("tool_name", ["Write", "Edit"])
@pytest.mark.parametrize("path", [
    "tests/fixtures/aulas/modelo-v1.json",
    "skills/aulas/references/modelo_hof_roteiro.json",
    "skills/aulas/assets/fundo_foto.jpg",
    "skills/aulas/assets/parcerias/logo_ilikia.png",
])
def test_guard_blocks_master_v1(tmp_path, tool_name, path):
    repo = tmp_path / "editorial-setup"
    target = repo / path if tool_name == "Write" else path
    proc = run("editorial_guard.py", write(target, repo, tool=tool_name))
    assert proc.returncode == 0
    assert decision(proc).get("hookSpecificOutput") == {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "modelo mestre v1 não muda; para mudar o visual, crie o modelo v2 ao lado",
    }


@pytest.mark.parametrize("path", [
    "tests/fixtures/aulas/modelo-v2.json",
    "skills/aulas/references/modelo_hof_roteiro_v2.json",
    "skills/aulas/assets-v2/fundo_foto.jpg",
    "other-skills/aulas/assets/fundo_foto.jpg",
])
def test_guard_allows_files_outside_master_v1(tmp_path, path):
    proc = run("editorial_guard.py", write(path, tmp_path, tool="Edit"))
    assert proc.returncode == 0
    assert decision(proc) == {}


def msg(text, active=False, agent="clinic-editorial:diagramador"):
    return {"hook_event_name": "SubagentStop", "agent_type": agent, "stop_hook_active": active, "last_assistant_message": text}


def test_return_missing_asks_once():
    first = run("subagent_return.py", msg("terminei"))
    assert decision(first)["decision"] == "block"
    second = run("subagent_return.py", msg("terminei", active=True))
    assert decision(second) == {} and second.returncode == 0 and second.stderr.strip()


def test_return_present_passes():
    ok = "Resumo\nStatus: PRONTO_COM_RESSALVAS\nArquivos entregues:\n- a\nPendências:\n- x\n"
    assert decision(run("subagent_return.py", msg(ok))) == {}
    assert decision(run("subagent_return.py", msg("sem bloco", agent="Explore"))) == {}


def test_stop_reminds_ficha_once():
    stop = {"hook_event_name": "Stop", "agent_type": "editor-chefe", "stop_hook_active": False,
            "last_assistant_message": "A fase 2 está concluída."}
    assert decision(run("subagent_return.py", stop, "--stop"))["decision"] == "block"


def test_stop_reminds_on_phase_done_without_number():
    stop = {"hook_event_name": "Stop", "agent_type": "editor-chefe", "stop_hook_active": False,
            "last_assistant_message": "Fase concluída: validação de conteúdo"}
    assert decision(run("subagent_return.py", stop, "--stop")).get("decision") == "block"


def test_hook_fails_open_on_bad_json():
    for script, args in (("editorial_guard.py", ()), ("subagent_return.py", ()), ("subagent_return.py", ("--stop",))):
        proc = run(script, None, *args, raw="{não é json")
        assert proc.returncode == 0 and proc.stdout.strip() == "" and proc.stderr.strip()


def test_stop_reminds_when_skill_used(tmp_path):
    done = "A fase 2 está concluída."
    for line in ('{"type":"tool_use","name":"Skill","input":{"skill":"clinic-editorial:editor-chefe"}}',
                 '{"type":"user","message":{"content":"<command-name>/editor-chefe</command-name>"}}'):
        t = tmp_path / "t.jsonl"
        t.write_text(line + "\n", encoding="utf-8")
        stop = {"hook_event_name": "Stop", "stop_hook_active": False, "transcript_path": str(t), "last_assistant_message": done}
        assert decision(run("subagent_return.py", stop, "--stop"))["decision"] == "block"
    t.write_text('{"name":"Skill","input":{"skill":"run"}}\n', encoding="utf-8")
    assert decision(run("subagent_return.py", stop, "--stop")) == {}


def test_return_without_files_asks_once():
    assert decision(run("subagent_return.py", msg("Status: PRONTO")))["decision"] == "block"


def test_auditor_return_without_score_asks_once():
    base = "Status: PRONTO\nArquivos entregues:\n- a\nPendências:\n- Nenhuma.\n"
    assert decision(run("subagent_return.py", msg(base, agent="auditor-grafico")))["decision"] == "block"
    full = base + "Nota: 92\nAchados:\n- Nenhum.\n"
    assert decision(run("subagent_return.py", msg(full, agent="auditor-grafico"))) == {}
    assert decision(run("subagent_return.py", msg(base, agent="diagramador"))) == {}


def transcript(tmp_path, *entries):
    lines = [json.dumps({"type": "user", "message": {"content": "<command-name>/editor-chefe</command-name>"}})]
    for e in entries:
        lines.append(json.dumps(e))
    t = tmp_path / "t.jsonl"
    t.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return t


def tool(name, path):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": {"file_path": path}}]}}


def stop_input(t, text):
    return {"hook_event_name": "Stop", "stop_hook_active": False, "transcript_path": str(t), "last_assistant_message": text}


def test_stop_reminds_when_ficha_only_mentioned(tmp_path):
    t = transcript(tmp_path, tool("Write", "/p/capitulo.md"))
    out = run("subagent_return.py", stop_input(t, "A fase 2 está concluída e a ficha ainda precisa ser atualizada."), "--stop")
    assert decision(out)["decision"] == "block"


def test_stop_passes_when_ficha_written(tmp_path):
    result = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}
    t = transcript(tmp_path, tool("Edit", "/p/ficha.md"), result)
    assert decision(run("subagent_return.py", stop_input(t, "A fase 2 está concluída."), "--stop")) == {}
    older = tmp_path / "o.jsonl"
    older.write_text(t.read_text(encoding="utf-8") + json.dumps({"type": "user", "message": {"content": "continue"}}) + "\n", encoding="utf-8")
    assert decision(run("subagent_return.py", stop_input(older, "A fase 3 está concluída."), "--stop"))["decision"] == "block"


def test_field_names_inside_sentence_do_not_count():
    text = "Status: PRONTO\nO campo Arquivos entregues: ficou fora e a seção Pendências: também.\n"
    assert decision(run("subagent_return.py", msg(text)))["decision"] == "block"
    ok = "Status: PRONTO\n  - Arquivos entregues:\n- a\n* Pendências:\n- Nenhuma.\n"
    assert decision(run("subagent_return.py", msg(ok))) == {}
