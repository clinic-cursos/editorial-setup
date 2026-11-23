import json
import os
from pathlib import Path
import subprocess
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Inches, Pt
import pytest


SKILL = Path(__file__).resolve().parents[1] / "skills/aulas"
CLI = SKILL / "scripts/aulas.py"
EXAMPLE = SKILL / "references/exemplo_roteiro.json"


def run_cli(*args, env=None):
    return subprocess.run(
        [sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True, env=env,
    )


def write_script(tmp_path, style, slides):
    script = tmp_path / "roteiro.json"
    script.write_text(json.dumps({"estilo": style, "avulso": True, "slides": slides}), encoding="utf-8")
    return script


@pytest.mark.parametrize("style,script", [
    ("padrao", EXAMPLE),
    ("ousado", SKILL / "references/modelo_hof_roteiro.json"),
])
def test_generated_deck_passes(tmp_path, style, script):
    deck = tmp_path / "aula.pptx"
    generated = run_cli("gerar", script, deck)
    assert generated.returncode == 0, generated.stderr or generated.stdout
    assert "Conferência" in generated.stdout
    checked = run_cli("conferir", deck, "--estilo", style, "--json")
    assert checked.returncode == 0, checked.stderr or checked.stdout
    assert json.loads(checked.stdout)["errors"] == 0


def test_bold_fallbacks_pass(tmp_path):
    fallback = {"antes_depois", "artigo", "grafico", "tabela", "caso_clinico",
                "referencias", "custos", "precificacao", "parceria", "continue_evolucao"}
    slides = [slide for slide in json.loads(EXAMPLE.read_text())["slides"] if slide["tipo"] in fallback]
    slides.extend({"tipo": kind} for kind in sorted(fallback - {slide["tipo"] for slide in slides}))
    assert len(slides) == len(fallback)
    deck = tmp_path / "fallback.pptx"
    result = run_cli("gerar", write_script(tmp_path, "ousado", slides), deck)
    assert result.returncode == 0, result.stderr or result.stdout
    for slide in Presentation(deck).slides:
        assert {"!!fundo", "!!logo"} <= {shape.name for shape in slide.shapes}
    result = run_cli("conferir", deck, "--estilo", "ousado")
    assert result.returncode == 0, result.stderr or result.stdout


def test_reports_rejections_and_warnings_by_slide(tmp_path):
    presentation = Presentation()
    presentation.slides.add_slide(presentation.slide_layouts[6])
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(0.75), Inches(0.25))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(1, 2, 3)
    run = box.text_frame.paragraphs[0].add_run()
    run.text = "[EXEMPLO [confirmar] Texto muito comprido para esta caixa."
    run.font.name = "Arial"
    run.font.size = Pt(24)
    run.font.color.rgb = RGBColor(2, 3, 4)
    slide.shapes.add_textbox(Inches(-1), Inches(2), Inches(2), Inches(1))
    deck = tmp_path / "fora.pptx"
    presentation.save(deck)
    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 1
    findings = json.loads(result.stdout)["findings"]
    assert {(item["slide"], item["rule"], item["severity"]) for item in findings} == {
        (2, "font", "error"), (2, "text_color", "error"), (2, "fill_color", "error"),
        (2, "bounds", "error"), (2, "overflow", "error"), (2, "marker", "warning"),
    }


@pytest.mark.parametrize("name,geometry,auto_size,parts,reason", [
    ("Palavra", (1, 3, 2), MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT,
     ("MMMMMM", "MMMMM"), "Palavra"),
    ("Caixa fixa", (1, 2.3, 0.62), MSO_AUTO_SIZE.NONE,
     ("WWWWWW WWWWWW WWWWWW",), "altura da caixa"),
    ("Base do slide", (6.45, 3, 0.4), MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT,
     ("Um\v\v\vDois",), "borda inferior do slide"),
])
def test_rejects_each_text_overflow_reason(tmp_path, name, geometry, auto_size, parts, reason):
    presentation = Presentation()
    presentation.slides.add_slide(presentation.slide_layouts[6])
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    top, width, height = geometry
    box = slide.shapes.add_textbox(Inches(1), Inches(top), Inches(width), Inches(height))
    box.name = name
    frame = box.text_frame
    frame.auto_size = auto_size
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = Inches(0.1)
    if len(parts) == 1:
        frame.text = parts[0]
    else:
        for part in parts:
            frame.paragraphs[0].add_run().text = part
    for run in frame.paragraphs[0].runs:
        run.font.name = "Montserrat"
        run.font.size = Pt(20)
        run.font.color.rgb = RGBColor(0x2A, 0x26, 0x25)
    deck = tmp_path / "estouro.pptx"
    presentation.save(deck)

    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 1, result.stderr or result.stdout
    findings = json.loads(result.stdout)["findings"]
    assert [(item["slide"], item["shape"], item["rule"], item["severity"]) for item in findings] == [
        (2, name, "overflow", "error"),
    ]
    assert reason in findings[0]["message"]


def test_table_rows_grow_into_the_remaining_slide_space(tmp_path):
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    for x, top in ((1, 1), (5, 6.35)):
        shape = slide.shapes.add_table(2, 1, Inches(x), Inches(top), Inches(3), Inches(0.5))
        shape.name = f"Tabela {x}"
        for i, text in enumerate(("Um\vDois\vTrês", "Quatro")):
            frame = shape.table.cell(i, 0).text_frame
            frame.text = text
            for run in frame.paragraphs[0].runs:
                run.font.name = "Montserrat"
                run.font.size = Pt(18)
                run.font.color.rgb = RGBColor(0x2A, 0x26, 0x25)
    deck = tmp_path / "tabelas.pptx"
    presentation.save(deck)

    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 1, result.stderr or result.stdout
    overflows = [item for item in json.loads(result.stdout)["findings"] if item["rule"] == "overflow"]
    assert [(item["slide"], item["shape"], item["severity"]) for item in overflows] == [
        (1, "Tabela 5", "error"),
    ]
    assert "borda inferior do slide" in overflows[0]["message"]


def test_preserved_font_remains_a_warning_when_reopened(tmp_path):
    source = Presentation()
    slide = source.slides.add_slide(source.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(3), Inches(1))
    run = box.text_frame.paragraphs[0].add_run()
    run.text = "Texto preservado"
    run.font.name = "Arial"
    original = tmp_path / "original.pptx"
    source.save(original)
    script = write_script(tmp_path, "padrao", [
        {"tipo": "preservado", "deck": original.name, "slide": 1, "titulo": "Título"},
    ])
    deck = tmp_path / "preservado.pptx"
    result = run_cli("gerar", script, deck)
    assert result.returncode == 0, result.stderr or result.stdout
    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    assert any(item["rule"] == "font" and item["severity"] == "warning"
               for item in json.loads(result.stdout)["findings"])


def test_georgia_is_allowed_only_in_the_decorative_quote(tmp_path):
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    for x, value in ((1, "“"), (5, "“Citação”")):
        box = slide.shapes.add_textbox(Inches(x), Inches(1), Inches(3), Inches(1))
        box.name = value
        run = box.text_frame.paragraphs[0].add_run()
        run.font.name = "Georgia"
        run.font.color.rgb = RGBColor(0x9C, 0x4C, 0x48)
        run.text = value
    deck = tmp_path / "aspas.pptx"
    presentation.save(deck)
    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 1
    findings = json.loads(result.stdout)["findings"]
    assert [(item["shape"], item["rule"]) for item in findings] == [("“Citação”", "font")]


def test_generate_propagates_rejection_unless_explicitly_bypassed(tmp_path):
    script = write_script(tmp_path, "padrao", [{"tipo": "capa", "titulo": "Título " * 200}])
    deck = tmp_path / "longa.pptx"
    assert run_cli("gerar", script, deck).returncode == 1
    assert run_cli("gerar", script, deck, "--sem-conferir").returncode == 0


def test_bold_rejects_missing_markers_and_motion(tmp_path):
    presentation = Presentation()
    presentation.slides.add_slide(presentation.slide_layouts[6])
    deck = tmp_path / "sem-movimento.pptx"
    presentation.save(deck)

    result = run_cli("conferir", deck, "--estilo", "ousado", "--json")
    assert result.returncode == 1
    findings = json.loads(result.stdout)["findings"]
    assert sorted(item["rule"] for item in findings) == ["animation", "morph", "morph_shape", "morph_shape"]


def test_preview_reports_missing_soffice(tmp_path):
    result = run_cli("previa", tmp_path / "aula.pptx", tmp_path / "png",
                     env={**os.environ, "PATH": str(tmp_path)})
    assert result.returncode == 2
    assert "soffice" in result.stderr
    assert "previa" in result.stderr


@pytest.mark.parametrize("converter_available", [False, True])
def test_preview_requires_pngs_for_every_slide(tmp_path, converter_available):
    presentation = Presentation()
    presentation.slides.add_slide(presentation.slide_layouts[6])
    presentation.slides.add_slide(presentation.slide_layouts[6])
    deck = tmp_path / "aula.pptx"
    presentation.save(deck)

    soffice = tmp_path / "soffice"
    soffice.write_text(
        f"#!{sys.executable}\n"
        "from pathlib import Path\nimport sys\n"
        "folder = Path(sys.argv[sys.argv.index('--outdir') + 1])\n"
        "(folder / Path(sys.argv[-1]).with_suffix('.pdf').name).write_text('2')\n"
    )
    soffice.chmod(0o755)
    if converter_available:
        converter = tmp_path / "pdftoppm"
        converter.write_text(
            f"#!{sys.executable}\n"
            "from pathlib import Path\nimport sys\n"
            "from PIL import Image\n"
            "assert sys.argv[1] == '-png'\n"
            "for number in range(1, int(Path(sys.argv[2]).read_text()) + 1):\n"
            "    Image.new('RGB', (2, 2)).save(f'{sys.argv[3]}-{number}.png')\n"
        )
        converter.chmod(0o755)

    destination = tmp_path / "png"
    result = run_cli("previa", deck, destination, env={**os.environ, "PATH": str(tmp_path)})
    if converter_available:
        assert result.returncode == 0, result.stderr
        assert {file.name for file in destination.iterdir()} == {"slide-1.png", "slide-2.png"}
        assert all(file.read_bytes().startswith(b"\x89PNG") for file in destination.iterdir())
    else:
        assert result.returncode == 2
        assert "pdftoppm" in result.stderr
        assert not destination.exists()
