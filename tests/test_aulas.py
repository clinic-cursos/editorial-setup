import json
import subprocess
import sys
from pathlib import Path

from pptx import Presentation

SKILL = Path(__file__).resolve().parent.parent / "skills" / "aulas"
EXAMPLE = SKILL / "references" / "exemplo_roteiro.json"


def build(tmp_path, spec, name="aula"):
    roteiro = tmp_path / "roteiro.json"
    roteiro.write_text(json.dumps(spec), encoding="utf-8")
    out = tmp_path / f"{name}.pptx"
    subprocess.run([sys.executable, str(SKILL / "scripts" / "clinic_deck.py"), str(roteiro), str(out)],
                   check=True, capture_output=True)
    return out, [s["tipo"] for s in spec["slides"]]


def test_example_script_builds_pptx(tmp_path):
    spec = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    out, tipos = build(tmp_path, spec)
    n = len(Presentation(str(out)).slides)
    # the generator adds 3 partnership slides, plus the pricing slides, when the script omits them
    assert n > len(tipos) + 3


def test_prompts_markdown_written(tmp_path):
    spec = {"titulo": "T", "slides": [{"tipo": "texto_imagem", "titulo": "X", "topicos": ["a"],
                                       "prompt_imagem": "cena de teste"}]}
    out, _ = build(tmp_path, spec)
    md = out.with_name(out.stem + " - prompts de imagem.md")
    assert "cena de teste" in md.read_text(encoding="utf-8")


def test_partnership_slides_inserted_by_default(tmp_path):
    spec = {"titulo": "T", "slides": [{"tipo": "capa", "titulo": "T", "curso": "C"}, {"tipo": "encerramento"}]}
    with_default, _ = build(tmp_path, spec, "padrao")
    spec["parcerias"] = False
    without, _ = build(tmp_path, spec, "sem")
    assert len(Presentation(str(with_default)).slides) - len(Presentation(str(without)).slides) == 3


def test_partnerships_can_be_disabled(tmp_path):
    spec = {"titulo": "T", "parcerias": False, "precificacao": False,
            "slides": [{"tipo": "capa", "titulo": "T", "curso": "C"}, {"tipo": "encerramento"}]}
    out, tipos = build(tmp_path, spec)
    assert len(Presentation(str(out)).slides) == len(tipos)
