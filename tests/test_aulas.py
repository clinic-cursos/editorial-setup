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
    slides = Presentation(str(out)).slides
    assert len(tipos) == 15 and len(slides) == 20  # 15 from the roteiro + 2 pricing + 3 partnership
    first_text = [next(sh.text_frame.text for sh in s.shapes if sh.has_text_frame and sh.text_frame.text) for s in slides]
    # automatic slides sit right before the closing one, in this order
    assert [x.split("\n")[0] for x in first_text[14:]] == [
        "PRECIFICAÇÃO", "PRECIFICAÇÃO", "CLINIC CURSOS   ×   GALDERMA",
        "CLINIC CURSOS   ×   ILIKIA", "CONTINUE SUA", "Obrigado!"]
    # the two pricing slides share a header, so tell them apart by title
    titles = [[sh.text_frame.text for sh in s.shapes if sh.has_text_frame and sh.text_frame.text][1] for s in slides]
    assert titles[14:16] == ["Como compor seu preço", "Aumente seu lucro com técnicas de venda"]


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


def test_custom_pricing_keeps_the_cost_slide_when_declared(tmp_path):
    spec = {"titulo": "T", "slides": [
        {"tipo": "custos"},
        {"tipo": "precificacao", "procedimentos": [{"nome": "Fios", "estrategia": "Upsell", "produto": 40,
                                                   "preco": 150, "custo_fixo": 10, "insumos": 5}]},
        {"tipo": "encerramento"}]}
    out, _ = build(tmp_path, spec)
    slides = list(Presentation(str(out)).slides)

    def texts(s):
        found = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame]
        for sh in s.shapes:
            if sh.has_table:
                found += [c.text for r in sh.table.rows for c in r.cells]
        return found

    assert "Como compor seu preço" in texts(slides[0])
    assert "Aumente seu lucro com técnicas de venda" in texts(slides[1])
    assert any("R$ 150" in x for x in texts(slides[1]))
