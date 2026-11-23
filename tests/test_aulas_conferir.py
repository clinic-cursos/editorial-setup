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
    ("ousado", SKILL / "references/exemplo_ousado.json"),
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


LONG_TEXT = "Primeira linha segunda linha terceira linha quarta linha quinta linha"


@pytest.mark.parametrize("upper_text,lower_left,variant,overlaps", [
    (LONG_TEXT, 1.5, None, True),
    ("Uma linha", 1.5, None, False),
    (LONG_TEXT, 5, None, False),
    (LONG_TEXT, 1.5, "grouped", True),
    (LONG_TEXT, 1.5, "preserved_upper", False),
    (LONG_TEXT, 1.5, "preserved_lower", False),
])
def test_checks_text_overlap_between_shapes(tmp_path, monkeypatch, upper_text, lower_left, variant, overlaps):
    presentation = Presentation()
    presentation.slides.add_slide(presentation.slide_layouts[6])
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    for position, name, left, top, value in (
        ("lower", "Item inferior", lower_left, 1.75, "Próximo item"),
        ("upper", "Item superior", 1, 1, upper_text),
    ):
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(3), Inches(0.4))
        box.name = name
        frame = box.text_frame
        frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        frame.word_wrap = True
        frame.text = value
        for run in frame.paragraphs[0].runs:
            run.font.name = "Montserrat"
            run.font.size = Pt(20)
            run.font.color.rgb = RGBColor(0x2A, 0x26, 0x25)
        if variant == "grouped" and position == "lower":
            box.top = Inches(5)
            group = slide.shapes.add_group_shape([box])
            group.top = Inches(1.75)
        if variant == f"preserved_{position}":
            monkeypatch.syspath_prepend(str(CLI.parent))
            from conferir import mark_preserved

            mark_preserved(box)
    deck = tmp_path / "itens.pptx"
    presentation.save(deck)

    result = run_cli("conferir", deck, "--json")
    assert result.returncode == int(overlaps), result.stderr or result.stdout
    findings = json.loads(result.stdout)["findings"]
    if overlaps:
        assert [(item["slide"], item["shape"], item["rule"], item["severity"]) for item in findings] == [
            (2, "Item superior", "text_overlap", "error"),
        ]
        message = findings[0]["message"]
        assert message.startswith("Texto sobreposto")
        assert "Item superior" in message and "Item inferior" in message
    else:
        assert findings == []


def test_rejects_two_line_title_over_first_step(tmp_path):
    title = "Preparação da leitura para a revisão em dupla"
    step = "Leia\nConfira o material."
    script = write_script(tmp_path, "ousado", [{
        "tipo": "passo_a_passo", "titulo": title, "prompt_imagem": "Material de leitura",
        "passos": [{"titulo": "Leia", "texto": "Confira o material."}],
    }])
    deck = tmp_path / "passos.pptx"
    generated = run_cli("gerar", script, deck, "--sem-conferir")
    assert generated.returncode == 0, generated.stderr or generated.stdout
    presentation = Presentation(deck)
    boxes = {shape.text: shape for shape in presentation.slides[0].shapes if shape.has_text_frame}
    boxes[title].name = "Título"
    boxes[title].height = Inches(0.6)
    boxes[step].name = "Primeiro passo"
    boxes[step].top = Inches(1.38)
    presentation.save(deck)

    result = run_cli("conferir", deck, "--estilo", "ousado", "--json")
    assert result.returncode == 1, result.stderr or result.stdout
    findings = json.loads(result.stdout)["findings"]
    assert [(item["shape"], item["rule"], item["severity"]) for item in findings] == [
        ("Título", "text_overlap", "error"),
    ]
    assert "Primeiro passo" in findings[0]["message"]


@pytest.mark.parametrize("variant,left,overlaps", [
    ("same_top", 1.25, True),
    ("same_top", 3, False),
    ("wrapped", 1.25, True),
])
def test_checks_comparison_items_for_text_overlap(tmp_path, variant, left, overlaps):
    item = "Revise os registros\nCompare as imagens" if variant == "wrapped" else "Revise as imagens"
    script = write_script(tmp_path, "ousado", [{
        "tipo": "comparativo", "titulo": "Dois formatos", "prompt_imagem": "Material de leitura",
        "colunas": [{"itens": [item]}, {"itens": ["Compare os exemplos"]}],
    }])
    deck = tmp_path / "comparativo.pptx"
    generated = run_cli("gerar", script, deck, "--sem-conferir")
    assert generated.returncode == 0, generated.stderr or generated.stdout
    presentation = Presentation(deck)
    boxes = {shape.text: shape for shape in presentation.slides[0].shapes if shape.has_text_frame}
    first, second = boxes[item], boxes["Compare os exemplos"]
    first.name, second.name = "Item esquerdo", "Item direito"
    assert first.top == second.top
    second.left = Inches(left)
    assert first.left < second.left < first.left + first.width
    if variant == "wrapped":
        first.height = Inches(0.3)
        second.top = first.top + first.height
    presentation.save(deck)

    result = run_cli("conferir", deck, "--estilo", "ousado", "--json")
    assert result.returncode == int(overlaps), result.stderr or result.stdout
    findings = json.loads(result.stdout)["findings"]
    if overlaps:
        assert [(item["shape"], item["rule"], item["severity"]) for item in findings] == [
            ("Item esquerdo", "text_overlap", "error"),
        ]
        assert "Item direito" in findings[0]["message"]
    else:
        assert findings == []


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


def test_preserved_warnings_are_grouped_by_slide_and_rule(tmp_path):
    source = Presentation()
    slide = source.slides.add_slide(source.slide_layouts[6])
    boxes = []
    for number in (1, 2):
        box = slide.shapes.add_textbox(Inches(number), Inches(2), Inches(1), Inches(1))
        box.name = f"Conteúdo original {number}"
        run = box.text_frame.paragraphs[0].add_run()
        run.text = "M" * 100
        run.font.name = "Arial"
        run.font.size = Pt(20)
        run.font.color.rgb = RGBColor(1, 2, 3)
        boxes.append(box)
    slide.shapes.add_group_shape(boxes)
    original = tmp_path / "original.pptx"
    source.save(original)
    script = write_script(tmp_path, "padrao", [
        {"tipo": "preservado", "deck": original.name, "slide": 1, "titulo": title}
        for title in ("Primeiro", "Segundo")
    ])
    deck = tmp_path / "preservado.pptx"
    result = run_cli("gerar", script, deck, "--sem-conferir")
    assert result.returncode == 0, result.stderr or result.stdout

    presentation = Presentation(deck)
    slide = presentation.slides[0]
    box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1))
    box.name = "Nota editorial"
    run = box.text_frame.paragraphs[0].add_run()
    run.text = "[confirmar]"
    run.font.name = "Montserrat"
    run.font.color.rgb = RGBColor(0x2A, 0x26, 0x25)
    presentation.save(deck)

    result = run_cli("conferir", deck)
    assert result.returncode == 0, result.stderr or result.stdout
    lines = result.stdout.splitlines()
    assert "1 aviso(s), 12 aviso(s) em conteúdo preservado" in lines[0]
    assert len(lines[1:]) == 7
    assert "Slide 1 (Nota editorial) | Aviso: Marcador editorial pendente." in lines
    for number in (1, 2):
        for label in ("fontes fora da família", "cores de texto fora da paleta", "estouros de texto"):
            assert lines.count(f"Slide {number} | Aviso: conteúdo preservado com 2 {label}.") == 1

    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert (report["errors"], report["warnings"], report["preserved_warnings"]) == (0, 1, 12)
    assert [(item["shape"], item["rule"]) for item in report["findings"]] == [("Nota editorial", "marker")]
    details = report["preserved_findings"]
    assert len(details) == 12
    assert {(item["slide"], item["shape"], item["rule"], item["severity"]) for item in details} == {
        (slide, f"Conteúdo original {shape}", rule, "warning")
        for slide in (1, 2) for shape in (1, 2) for rule in ("font", "text_color", "overflow")
    }
    assert all(item["message"] for item in details)


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
