import json
import os
from pathlib import Path
import subprocess
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Inches, Pt
import pytest


SKILL = Path(__file__).resolve().parents[1] / "skills/aulas"
CLI = SKILL / "scripts/aulas.py"
EXAMPLE = SKILL / "references/exemplo_roteiro.json"
BOLD_EXAMPLE = SKILL / "references/exemplo_ousado.json"


def run_cli(*args, env=None):
    return subprocess.run(
        [sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True, env=env,
    )


def write_script(tmp_path, style, slides):
    script = tmp_path / "roteiro.json"
    script.write_text(json.dumps({"estilo": style, "avulso": True, "slides": slides}), encoding="utf-8")
    return script


def add_content_text(shapes, value, *, left=1, top=1, width=8):
    box = shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(1.5))
    box.text = value
    for paragraph in box.text_frame.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Montserrat"
            run.font.size = Pt(16)
            run.font.color.rgb = RGBColor.from_string("404040")
    return box


def save_content_deck(path, *slides):
    deck = Presentation()
    for value in slides:
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        add_content_text(slide.shapes, value)
    deck.save(path)


@pytest.mark.parametrize("original,rewritten,kept,missing,replaced_by", [
    ("Até\u00a012 unidades", ("ATE\u0301 **12** UNIDADES",), 3, [], []),
    ("Até\u00a012 unidades", ("Até\u00a012",), 2, ["unidades"], []),
    ("Até\u00a012 unidades", ("Até 15 unidades",), 2, ["12"], ["15"]),
    ("Até\u00a012 unidades", ("unidades Até 12",), 2, ["unidades"], []),
    ("Até\u00a012 unidades", ("Kicker Até 12 unidades",), 3, [], []),
    ("Até\u00a012 unidades", ("Até 12", "unidades"), 2, ["unidades"], []),
    ("Até 12\nunidades", ("Até 12", "unidades"), 3, [], []),
    ("Módulo 1", ("Módulo 01",), 2, [], []),
    ("Veja ex clínicos", ("Veja exemplos clínicos",), 2, ["ex"], ["exemplos"]),
    ("Os pacientes podem possuir sintomas", ("O paciente pode ter sintomas",), 1,
     ["os", "pacientes", "podem", "possuir"], ["o", "paciente", "pode", "ter"]),
    ("Primeiro. Uma frase inteira.", ("Primeiro.",), 1, ["uma", "frase", "inteira"], []),
    ("Veja casos clínicos", ("Veja novos casos clínicos",), 3, ["veja", "casos", "clínicos"], []),
])
def test_content_fidelity(tmp_path, original, rewritten, kept, missing, replaced_by):
    origin = tmp_path / "original.pptx"
    deck = tmp_path / "aula.pptx"
    save_content_deck(origin, original)
    save_content_deck(deck, *rewritten)

    result = run_cli("conferir", deck, "--origem", origin, "--json")
    assert result.returncode == int(bool(missing)), result.stderr or result.stdout
    report = json.loads(result.stdout)
    total = len(original.split())
    assert report["content"] == {
        "origin": str(origin), "origin_tokens": total, "kept_tokens": kept,
        "fidelity_pct": round(100 * kept / total, 2),
        "divergences": [{
            "origin_slide": 1, "paragraph": original, "missing": missing, "replaced_by": replaced_by,
        }] if missing else [],
    }
    assert report["errors"] == int(bool(missing))
    assert [(item["slide"], item["rule"], item["severity"]) for item in report["findings"]] == (
        [(1, "content", "error")] if missing else []
    )


@pytest.mark.parametrize("original,shapes,total", [
    ("Introdução\nAnatomia\nPlanejamento\nPrática",
     [("Introdução\nPlanejamento", 1, 1), ("Anatomia\nPrática", 5, 1)], 4),
    ("Título principal\nVisão geral", [("Visão geral", 1, 1), ("Título principal", 1, 3)], 4),
    ("Cuidados após o procedimento.", [("Cuidados após", 1, 1), ("o procedimento.", 1, 3)], 4),
])
def test_content_accepts_changes_in_layout(tmp_path, original, shapes, total):
    origin = tmp_path / "original.pptx"
    deck = tmp_path / "aula.pptx"
    save_content_deck(origin, original)
    output = Presentation()
    slide = output.slides.add_slide(output.slide_layouts[6])
    for value, left, top in shapes:
        add_content_text(slide.shapes, value, left=left, top=top, width=3.5)
    output.save(deck)

    result = run_cli("conferir", deck, "--origem", origin, "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    content = json.loads(result.stdout)["content"]
    assert content["origin_tokens"] == content["kept_tokens"] == total
    assert content["fidelity_pct"] == 100
    assert content["divergences"] == []


def test_content_cursor_uses_earliest_match_and_does_not_move_back(tmp_path):
    origin = tmp_path / "original.pptx"
    deck = tmp_path / "aula.pptx"
    save_content_deck(origin, "Terceiro\nPrimeiro", "Segundo", "Ausente", "Início")
    save_content_deck(deck, "Início", "Primeiro", "Segundo", "Terceiro")

    result = run_cli("conferir", deck, "--origem", origin, "--json")
    assert result.returncode == 1, result.stderr or result.stdout
    content = json.loads(result.stdout)["content"]
    assert content["origin_tokens"] == 5
    assert content["kept_tokens"] == 3
    assert content["divergences"] == [
        {"origin_slide": 3, "paragraph": "Ausente", "missing": ["ausente"], "replaced_by": []},
        {"origin_slide": 4, "paragraph": "Início", "missing": ["início"], "replaced_by": []},
    ]


def test_content_aligns_with_best_slide_in_cursor_window(tmp_path):
    origin = tmp_path / "original.pptx"
    deck = tmp_path / "aula.pptx"
    save_content_deck(origin, "Abertura", "Veja riscos e benefícios clínicos")
    save_content_deck(deck, "Veja riscos e prazos clínicos", "Abertura", "Veja riscos",
                      "Outro assunto", "Veja riscos e critérios", "Veja riscos e benefícios gerais")

    result = run_cli("conferir", deck, "--origem", origin, "--json")
    assert result.returncode == 1, result.stderr or result.stdout
    content = json.loads(result.stdout)["content"]
    assert content["kept_tokens"] == 4
    assert content["divergences"] == [{
        "origin_slide": 2, "paragraph": "Veja riscos e benefícios clínicos",
        "missing": ["benefícios", "clínicos"], "replaced_by": ["critérios"],
    }]


def test_content_reads_nested_groups_and_tables_without_notes_or_metadata(tmp_path):
    origin = tmp_path / "original.pptx"
    deck = tmp_path / "aula.pptx"
    source = Presentation()
    slide = source.slides.add_slide(source.slide_layouts[6])
    box = add_content_text(slide.shapes, "Primeira")
    table = slide.shapes.add_table(1, 2, Inches(1), Inches(3), Inches(4), Inches(1))
    table.table.cell(0, 0).text = "Segunda\nQuarta"
    table.table.cell(0, 1).text = "Terceira"
    inner = slide.shapes.add_group_shape([box, table])
    slide.shapes.add_group_shape([inner])
    slide.notes_slide.notes_text_frame.text = "Nota do apresentador"
    for placeholder in ("sldNum", "ftr", "dt"):
        box = add_content_text(slide.shapes, placeholder)
        properties = box._element.find(f"{qn('p:nvSpPr')}/{qn('p:nvPr')}")
        properties.append(parse_xml(f'<p:ph {nsdecls("p")} type="{placeholder}"/>'))
    source.save(origin)
    save_content_deck(deck, "Primeira Segunda Terceira Quarta")

    result = run_cli("conferir", deck, "--origem", origin, "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    content = json.loads(result.stdout)["content"]
    assert content["origin_tokens"] == content["kept_tokens"] == 4
    assert content["divergences"] == []


def test_content_selection_reports_actual_origin_slide_numbers(tmp_path):
    origin = tmp_path / "original.pptx"
    deck = tmp_path / "aula.pptx"
    save_content_deck(origin, "Ignorado", "Primeiro", "Segundo", "Terceiro")
    save_content_deck(deck, "Primeiro")

    result = run_cli("conferir", deck, "--origem", origin, "--origem-slides", "4,2-3", "--json")
    assert result.returncode == 1, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["content"]["origin_tokens"] == 3
    assert report["content"]["divergences"] == [
        {"origin_slide": 3, "paragraph": "Segundo", "missing": ["segundo"], "replaced_by": []},
        {"origin_slide": 4, "paragraph": "Terceiro", "missing": ["terceiro"], "replaced_by": []},
    ]
    assert report["errors"] == 2
    assert report["model_score"]["min"] == 100
    assert [(item["slide"], item["rule"]) for item in report["findings"]] == [(3, "content"), (4, "content")]

    result = run_cli("conferir", deck, "--origem", origin, "--origem-slides", "4,2-3")
    assert result.returncode == 1, result.stderr
    assert "Slide 3 da origem" in result.stdout
    assert "segundo" in result.stdout


@pytest.mark.parametrize("selection,has_origin,error", [
    ("1", False, "--origem"),
    ("1,5-3", True, "seletor fora do deck"),
    ("primeiro", True, "seletor inválido"),
])
def test_content_rejects_invalid_origin_selection(tmp_path, selection, has_origin, error):
    deck = tmp_path / "aula.pptx"
    save_content_deck(deck, "Texto")
    origin_args = ("--origem", deck) if has_origin else ()

    result = run_cli("conferir", deck, *origin_args, "--origem-slides", selection)
    assert result.returncode == 2
    assert "unrecognized arguments" not in result.stderr
    assert error in result.stderr


@pytest.mark.parametrize("style,script", [
    ("padrao", EXAMPLE),
    ("ousado", SKILL / "references/modelo_hof_roteiro.json"),
    ("ousado", BOLD_EXAMPLE),
])
def test_generated_deck_passes(tmp_path, style, script):
    deck = tmp_path / "aula.pptx"
    generated = run_cli("gerar", script, deck)
    assert generated.returncode == 0, generated.stderr or generated.stdout
    assert "Conferência" in generated.stdout
    checked = run_cli("conferir", deck, "--estilo", style, "--json")
    assert checked.returncode == 0, checked.stderr or checked.stdout
    report = json.loads(checked.stdout)
    assert report["errors"] == 0
    assert "content" not in report
    assert report["scores"] == [
        {"slide": number, "score": 100, "gaps": []}
        for number in range(1, len(Presentation(deck).slides) + 1)
    ]
    assert report["model_score"] == {"min": 100, "mean": 100, "slides_below_100": 0}


@pytest.mark.parametrize("change,category,rule,score", [
    ("remove_logo", "elementos-base", "morph_shape", 80),
    ("replace_font", "fonte", "font", 85),
])
def test_bold_model_score_reports_slide_gap(tmp_path, change, category, rule, score):
    deck = tmp_path / "aula.pptx"
    generated = run_cli("gerar", BOLD_EXAMPLE, deck, "--sem-conferir")
    assert generated.returncode == 0, generated.stderr or generated.stdout
    presentation = Presentation(deck)
    slide = presentation.slides[0]
    if change == "remove_logo":
        logo = next(shape for shape in slide.shapes if shape.name == "!!logo")
        logo._element.getparent().remove(logo._element)
    else:
        run = next(
            run for shape in slide.shapes if shape.has_text_frame
            for paragraph in shape.text_frame.paragraphs for run in paragraph.runs
            if run.text.strip()
        )
        run.font.name = "Arial"
    presentation.save(deck)

    checked = run_cli("conferir", deck, "--estilo", "ousado", "--json")
    assert checked.returncode == 1, checked.stderr or checked.stdout
    report = json.loads(checked.stdout)
    assert report["errors"] == 1
    finding = next(item for item in report["findings"] if item["severity"] == "error")
    assert (finding["slide"], finding["rule"]) == (1, rule)
    assert report["scores"][0] == {
        "slide": 1, "score": score,
        "gaps": [{"category": category, "rule": rule, "message": finding["message"]}],
    }
    assert all(item["score"] == 100 for item in report["scores"][1:])
    assert report["model_score"]["min"] == score
    assert report["model_score"]["slides_below_100"] == 1

    checked = run_cli("conferir", deck, "--estilo", "ousado")
    assert checked.returncode == 1, checked.stderr or checked.stdout
    total = len(presentation.slides)
    score_lines = [line for line in checked.stdout.splitlines() if "Placar do modelo:" in line]
    assert score_lines == [
        f"Placar do modelo: {score}/100 ({total - 1} de {total} slides com 100)",
        f"Slide 1 | Placar do modelo: {score}/100 | Categorias faltantes: {category}",
    ]


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
    report = json.loads(result.stdout)
    findings = report["findings"]
    assert {(item["slide"], item["rule"], item["severity"]) for item in findings} == {
        (2, "font", "error"), (2, "text_color", "error"), (2, "fill_color", "error"),
        (2, "bounds", "error"), (2, "overflow", "error"), (2, "marker", "warning"),
    }
    assert [item["score"] for item in report["scores"]] == [100, 28]
    assert {gap["rule"] for gap in report["scores"][1]["gaps"]} == {
        "font", "text_color", "fill_color", "bounds", "overflow",
    }
    assert report["model_score"] == {"min": 28, "mean": 64, "slides_below_100": 1}


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


@pytest.mark.parametrize("violation", ["font", "quote_font", "fill_color", "contrast"])
def test_rejects_preserved_content_outside_model(tmp_path, violation):
    source = Presentation()
    slide = source.slides.add_slide(source.slide_layouts[6])
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2), Inches(2), Inches(4), Inches(1))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor.from_string("FAF6F4")
    if violation != "fill_color":
        box.text = "“" if violation == "quote_font" else "Conteúdo original"
    original = tmp_path / "original.pptx"
    source.save(original)
    script = write_script(tmp_path, "padrao", [
        {"tipo": "preservado", "deck": original.name, "slide": 1, "titulo": "Título"},
    ])
    deck = tmp_path / "preservado.pptx"
    generated = run_cli("gerar", script, deck, "--sem-conferir")
    assert generated.returncode == 0, generated.stderr or generated.stdout
    presentation = Presentation(deck)
    copied = next(shape for shape in presentation.slides[0].shapes if shape.name == box.name)
    if violation == "fill_color":
        copied.fill.fore_color.rgb = RGBColor.from_string("EEECE1")
    else:
        run = copied.text_frame.paragraphs[0].runs[0]
        if violation in {"font", "quote_font"}:
            run.font.name = "Georgia" if violation == "quote_font" else "Calibri"
        else:
            run.font.color.rgb = RGBColor.from_string("FFFFFF")
    presentation.save(deck)

    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 1, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["errors"] == 1
    assert [(item["shape"], item["rule"], item["severity"]) for item in report["findings"]] == [
        (box.name, "font" if violation == "quote_font" else violation, "error"),
    ]


@pytest.mark.parametrize("kind, color, legend", [
    ("text", "1769F2", False),
    ("text", "dk2", False),
    ("text", "6930AB", True),
    ("bullet", "1769F2", False),
    ("bullet", "dk2", False),
    ("bullet", "682FAA", True),
])
def test_checks_preserved_annotation_colors(tmp_path, kind, color, legend, monkeypatch):
    monkeypatch.syspath_prepend(str(CLI.parent))
    from conferir import mark_preserved

    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(2), Inches(3), Inches(4), Inches(1))
    mark_preserved(box)
    paragraph = box.text_frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = "Legenda" if legend else "Item"
    run.font.name = "Montserrat"
    run.font.color.rgb = RGBColor.from_string("404040")
    if kind == "bullet":
        paint = f'<a:schemeClr val="{color}"/>' if color == "dk2" else f'<a:srgbClr val="{color}"/>'
        paragraph._p.get_or_add_pPr().extend(parse_xml(node) for node in (
            f'<a:buClr {nsdecls("a")}>{paint}</a:buClr>',
            f'<a:buChar {nsdecls("a")} char="•"/>',
        ))
    elif color == "dk2":
        run.font.color.theme_color = MSO_THEME_COLOR.DARK_2
    else:
        run.font.color.rgb = RGBColor.from_string(color)
    if legend:
        point = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.7), Inches(3), Inches(0.15), Inches(0.15))
        point.fill.solid()
        point.fill.fore_color.rgb = RGBColor.from_string("682FAA")
        point.line.fill.background()
        mark_preserved(point)
    deck = tmp_path / "deck.pptx"
    presentation.save(deck)

    result = run_cli("conferir", deck, "--json")
    assert result.returncode == (0 if legend else 1), result.stderr or result.stdout
    report = json.loads(result.stdout)
    errors = [item for item in report["findings"] if item["severity"] == "error"]
    if legend:
        assert not errors
        assert all(item["rule"] != "text_color" for item in report["preserved_findings"])
    else:
        assert len(errors) == 1
        assert errors[0]["rule"] == "text_color"
        assert ("1F497D" if color == "dk2" else color) in errors[0]["message"]


def test_rejects_preserved_label_that_still_overflows_at_font_floor(tmp_path):
    source = Presentation()
    slide = source.slides.add_slide(source.slide_layouts[6])
    label = slide.shapes.add_textbox(Inches(2), Inches(3), Inches(3), Pt(16))
    frame = label.text_frame
    frame.margin_top = frame.margin_bottom = 0
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.text = "Rótulo sintético\nSegunda linha"
    for paragraph in frame.paragraphs:
        paragraph.runs[0].font.size = Pt(20)
    original = tmp_path / "original.pptx"
    source.save(original)
    script = write_script(tmp_path, "padrao", [
        {"tipo": "preservado", "deck": original.name, "slide": 1, "titulo": "Título"},
    ])
    deck = tmp_path / "preservado.pptx"
    result = run_cli("gerar", script, deck, "--sem-conferir")
    assert result.returncode == 0, result.stderr or result.stdout

    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 1, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert [(item["shape"], item["rule"], item["severity"]) for item in report["findings"]] == [
        (label.name, "overflow", "error"),
    ]
    copied = next(shape for shape in Presentation(deck).slides[0].shapes if shape.name == label.name)
    initial = round(20 * copied.width / label.width, 2)
    for paragraph in copied.text_frame.paragraphs:
        assert paragraph.runs[0].font.size.pt == pytest.approx(initial * 0.7, abs=0.01)


def test_preserved_warnings_are_grouped_by_slide_and_rule(tmp_path):
    source = Presentation()
    slide = source.slides.add_slide(source.slide_layouts[6])
    boxes = []
    for number in (1, 2):
        box = slide.shapes.add_textbox(Inches(number), Inches(2), Inches(1), Inches(1))
        box.name = f"Conteúdo original {number}"
        box.text_frame.word_wrap = False
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
    for slide_with_group in presentation.slides:
        group = next(shape for shape in slide_with_group.shapes if shape.shape_type == MSO_SHAPE_TYPE.GROUP)
        for child in group.shapes:
            paragraph = child.text_frame.paragraphs[0]
            paragraph.runs[0].font.name = "Montserrat"
            duplicate = paragraph.add_run()
            duplicate.text = "M"
            duplicate.font.name = "Montserrat"
            duplicate.font.color.rgb = RGBColor.from_string("404040")
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
    assert "Slide 1 (Nota editorial) | Aviso: Marcador editorial pendente." in lines
    for number in (1, 2):
        assert lines.count(f"Slide {number} | Aviso: conteúdo preservado com 2 estouros de texto.") == 1
    assert "1 aviso(s), 4 aviso(s) em conteúdo preservado" in lines[0]
    assert len(lines[1:]) == 4
    assert "Placar do modelo: 100/100 (2 de 2 slides com 100)" in lines

    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert (report["errors"], report["warnings"], report["preserved_warnings"]) == (0, 1, 4)
    assert report["scores"] == [
        {"slide": 1, "score": 100, "gaps": []},
        {"slide": 2, "score": 100, "gaps": []},
    ]
    assert report["model_score"] == {"min": 100, "mean": 100, "slides_below_100": 0}
    assert [(item["shape"], item["rule"]) for item in report["findings"]] == [("Nota editorial", "marker")]
    details = report["preserved_findings"]
    assert len(details) == 4
    assert {(item["slide"], item["shape"], item["rule"], item["severity"]) for item in details} == {
        (slide, f"Conteúdo original {shape}", "overflow", "warning")
        for slide in (1, 2) for shape in (1, 2)
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
    report = json.loads(result.stdout)
    findings = report["findings"]
    assert sorted(item["rule"] for item in findings) == ["animation", "morph", "morph_shape", "morph_shape"]
    assert report["scores"][0]["score"] == 50
    assert {gap["category"] for gap in report["scores"][0]["gaps"]} == {
        "animacao", "transicao", "elementos-base",
    }


def test_empty_deck_has_no_score_deductions(tmp_path):
    deck = tmp_path / "vazio.pptx"
    Presentation().save(deck)
    result = run_cli("conferir", deck, "--json")
    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["scores"] == []
    assert report["model_score"] == {"min": 100, "mean": 100, "slides_below_100": 0}


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
