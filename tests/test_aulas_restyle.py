import json
from pathlib import Path
import subprocess
import sys

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.oxml import serialize_part_xml
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Inches
import pytest


CLI = Path(__file__).resolve().parents[1] / "skills/aulas/scripts/aulas.py"
CUSTOM_TABLE_STYLE = "{B57B5B66-607D-4D58-ABFC-B740DDD1FF2C}"


def run_cli(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)


@pytest.fixture
def source_deck(tmp_path):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    background.name = "Fundo"
    slide.shapes.title.text = "Título de teste"
    image = tmp_path / "foto.png"
    Image.new("RGB", (32, 16), "#9C4C48").save(image)
    logo = slide.shapes.add_picture(str(image), Inches(9), 0, Inches(0.3))
    logo.name = "Logo"
    page = slide.shapes.add_textbox(Inches(9), Inches(7), Inches(0.5), Inches(0.3))
    page.name = "Número de página"
    page.text = "1"
    slide.shapes.add_picture(str(image), Inches(1), Inches(2), Inches(4))
    slide.shapes.add_textbox(Inches(6), Inches(3), Inches(3), Inches(0.3)).text = "Depois"
    slide.shapes.add_textbox(Inches(6), Inches(2), Inches(3), Inches(0.3)).text = "Antes"
    group = slide.shapes.add_group_shape()
    group.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2), Inches(2.5), Inches(0.8), Inches(0.3)).text = "Rótulo"
    group.shapes.add_picture(str(image), Inches(2), Inches(3), Inches(0.5))
    for x in (1.5, 2.5, 3.5):
        connector = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(2), Inches(x), Inches(3),
        )
        connector.name = f"Conector original {x}"
        connector.end_connect(group.shapes[0], 0)
    table = slide.shapes.add_table(1, 2, Inches(1), Inches(5), Inches(4), Inches(0.5)).table
    table.cell(0, 0).text = "Célula A"
    table.cell(0, 1).text = "Célula B"
    table._tbl.tblPr.find(qn("a:tableStyleId")).text = CUSTOM_TABLE_STYLE
    style_part = prs.part.part_related_by(RT.TABLE_STYLES)
    styles = parse_xml(style_part.blob)
    styles.append(parse_xml(
        f'<a:tblStyle {nsdecls("a")} styleId="{CUSTOM_TABLE_STYLE}" styleName="Teste">'
        '<a:wholeTbl><a:tcStyle><a:fill><a:solidFill><a:srgbClr val="9C4C48"/>'
        '</a:solidFill></a:fill></a:tcStyle></a:wholeTbl></a:tblStyle>'
    ))
    style_part.blob = serialize_part_xml(styles)
    for number in range(2, 6):
        other = prs.slides.add_slide(prs.slide_layouts[5])
        other.shapes.title.text = f"Slide {number}"
        if number in (2, 3):
            drawing = other.shapes.add_group_shape().shapes if number == 2 else other.shapes
            drawing.add_picture(str(image), Inches(1), Inches(2), Inches(4))
            y = Inches(2.5 if number == 2 else 5)
            for x in (1.5, 2.5, 3.5, 4.5):
                drawing.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), y, Inches(x), y + Inches(0.5))
    path = tmp_path / "original.pptx"
    prs.save(path)
    return path, image.read_bytes()


def test_extract_retains_text_and_filters_slides(tmp_path, source_deck):
    source, image = source_deck
    folder = tmp_path / "rascunho"
    result = run_cli("extrair", source, folder, "--slides", "1-3,5")
    assert result.returncode == 0, result.stderr
    draft = json.loads((folder / "roteiro-rascunho.json").read_text(encoding="utf-8"))
    assert draft["avulso"] is True
    assert [slide["origem"] for slide in draft["slides"]] == [1, 2, 3, 5]
    first = draft["slides"][0]
    assert first["titulo"] == "Título de teste"
    assert first["textos"] == ["Título de teste", "Antes", "Rótulo", "Depois", "Célula A", "Célula B", "1"]
    assert first["formas_desenhadas"] == 4
    assert first["tipo"] == "preservado"
    assert len(first["imagens"]) == 3
    assert all((folder / path).read_bytes() == image for path in first["imagens"])
    assert [slide["tipo"] for slide in draft["slides"]] == ["preservado", "preservado", "texto_imagem", "modulo"]
    assert [slide["revisar"] for slide in draft["slides"]] == [False, False, True, False]
    assert draft["slides"][2]["imagem_modo"] == "conter"
    assert draft["slides"][1]["formas_desenhadas"] == 5
    out = folder / "rascunho.pptx"
    generated = run_cli("gerar", folder / "roteiro-rascunho.json", out)
    assert generated.returncode == 0, generated.stderr
    assert len(Presentation(out).slides) == 4
    bad = run_cli("extrair", source, tmp_path / "invalido", "--slides", "4-6")
    assert bad.returncode == 2
    assert "6" in bad.stderr
    assert not (tmp_path / "invalido").exists()


def test_extract_suggests_layouts_from_simple_slide_content(tmp_path):
    prs = Presentation()
    cases = [
        ("Aula de teste", "Turma A", "capa", False),
        ("CONTEÚDO programático", "Primeiro\n\nSegundo", "sumario", True),
        ("Introdução", "", "modulo", False),
        ("Materiais", "Item A\vItem B", "texto_imagem", True),
        ("“Uma frase curta.”", "", "frase", True),
        ("Prática", "", "modulo", False),
        ("Sumário", "Parte A\nParte B", "sumario", True),
        ("Uma frase comum " * 6, "", "texto_imagem", True),
    ]
    for title, body, _, _ in cases:
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = title
        if body:
            slide.shapes.add_textbox(Inches(1), Inches(2), Inches(7), Inches(3)).text = body
    source = tmp_path / "sugestoes.pptx"
    prs.save(source)
    folder = tmp_path / "rascunho"

    result = run_cli("extrair", source, folder)

    assert result.returncode == 0, result.stderr
    slides = json.loads((folder / "roteiro-rascunho.json").read_text(encoding="utf-8"))["slides"]
    assert [(slide["tipo"], slide.get("revisar")) for slide in slides] == [
        (kind, review) for _, _, kind, review in cases
    ]
    assert [slide["textos"] for slide in slides] == [
        [title, body] if body else [title] for title, body, _, _ in cases
    ]
    assert [slides[2]["numero"], slides[5]["numero"]] == [1, 2]
    assert slides[1]["itens"] == ["Primeiro", "Segundo"]
    assert slides[6]["itens"] == ["Parte A", "Parte B"]
    assert slides[3]["topicos"] == ["Item A", "Item B"]
    assert slides[3]["imagem_modo"] == slides[7]["imagem_modo"] == "conter"
    assert "imagem" not in slides[3]
    assert slides[4]["frase"] == "“Uma frase curta.”"


@pytest.mark.parametrize("style", ["padrao", "ousado"])
def test_preserved_frame_keeps_divider_below_title(tmp_path, source_deck, style):
    source, _ = source_deck
    titles = ["Título curto", "INDICAÇÕES ESTÉTICAS\nAVANÇADAS\n\n"]
    script = tmp_path / "roteiro.json"
    script.write_text(json.dumps({
        "estilo": style, "avulso": True,
        "slides": [
            {"tipo": "preservado", "deck": source.name, "slide": 1, "titulo": title, "kicker": "Teste"}
            for title in titles
        ],
    }), encoding="utf-8")
    out = tmp_path / "restyle.pptx"
    result = run_cli("gerar", script, out)
    assert result.returncode == 0, result.stderr

    original = Presentation(source).slides[0]
    copied_names = {shape.name for shape in list(original.shapes)[4:]}
    for slide, title in zip(Presentation(out).slides, titles, strict=True):
        expected = title.rstrip().upper() if style == "padrao" else title.rstrip()
        heading = next(
            shape for shape in slide.shapes
            if shape.has_text_frame and shape.text.rstrip() == expected
        )
        divider = next(
            shape for shape in slide.shapes
            if shape.name == "!!barra" or (shape.shape_type == MSO_SHAPE_TYPE.LINE and shape.height == 0)
        )
        copied = [shape for shape in slide.shapes if shape.name in copied_names]
        if "\n" in expected:
            assert heading.height >= Inches(0.8 if style == "padrao" else 1.0)
            assert [paragraph.text for paragraph in heading.text_frame.paragraphs] == expected.splitlines()
        assert heading.top + heading.height < divider.top
        assert min(shape.top for shape in copied) > divider.top + divider.height


@pytest.mark.parametrize("style", ["padrao", "ousado"])
def test_preserved_objects_and_exact_standalone_slide_count(tmp_path, source_deck, style):
    source, image = source_deck
    script = tmp_path / "roteiro.json"
    script.write_text(json.dumps({
        "estilo": style, "avulso": True, "precificacao": True, "parcerias": True,
        "slides": [{"tipo": "preservado", "deck": source.name, "slide": 1, "titulo": "Novo título", "kicker": "Teste"}],
    }), encoding="utf-8")
    out = tmp_path / "restyle.pptx"
    result = run_cli("gerar", script, out)
    assert result.returncode == 0, result.stderr
    presentation = Presentation(out)
    assert len(presentation.slides) == 1
    slide = presentation.slides[0]
    shapes = slide.shapes
    original = Presentation(source).slides[0].shapes
    kept = list(original)[4:]
    copied = [shape for shape in shapes if shape.name in {item.name for item in kept}]
    assert [shape.shape_type for shape in copied] == [shape.shape_type for shape in kept]
    assert {shape.name for shape in shapes}.isdisjoint({"Fundo", "Logo", "Número de página"})
    assert all(shape.text != "Título de teste" for shape in shapes if shape.has_text_frame)
    assert copied[0].image.blob == image
    group = next(shape for shape in copied if shape.shape_type == MSO_SHAPE_TYPE.GROUP)
    assert group.shapes[0].text == "Rótulo"
    assert group.shapes[1].image.blob == image
    assert copied[-1].table.cell(0, 1).text == "Célula B"
    shape_ids = [node.get("id") for node in slide._element.iter(qn("p:cNvPr"))]
    assert len(set(shape_ids)) == len(shape_ids)
    rel_prefix = qn("r:id").rsplit("}", 1)[0] + "}"
    used_rels = {value for node in slide._element.iter() for attr, value in node.attrib.items()
                 if attr.startswith(rel_prefix) and value}
    assert used_rels <= set(slide.part.rels)
    table_style_id = copied[-1].table._tbl.tblPr.find(qn("a:tableStyleId")).text
    assert table_style_id == CUSTOM_TABLE_STYLE
    styles = parse_xml(presentation.part.part_related_by(RT.TABLE_STYLES).blob)
    definitions = [node for node in styles.iter(qn("a:tblStyle")) if node.get("styleId") == table_style_id]
    assert len(definitions) == 1
    assert definitions[0].find(".//" + qn("a:srgbClr")).get("val") == "9C4C48"
    for shape in copied:
        if shape.shape_type == MSO_SHAPE_TYPE.LINE:
            assert int(shape._element.find(".//" + qn("a:endCxn")).get("id")) == group.shapes[0].shape_id
    scale = copied[0].width / kept[0].width
    for old, new in zip(kept, copied, strict=True):
        assert new.width == pytest.approx(old.width * scale, abs=2)
        assert new.height == pytest.approx(old.height * scale, abs=2)
        assert new.left - copied[0].left == pytest.approx((old.left - kept[0].left) * scale, abs=2)
        assert new.top - copied[0].top == pytest.approx((old.top - kept[0].top) * scale, abs=2)
