import json
from pathlib import Path
import subprocess
import sys

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_FILL, MSO_THEME_COLOR
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.oxml import serialize_part_xml
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Inches, Pt
import pytest


CLI = Path(__file__).resolve().parents[1] / "skills/aulas/scripts/aulas.py"
CUSTOM_TABLE_STYLE = "{B57B5B66-607D-4D58-ABFC-B740DDD1FF2C}"


def run_cli(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)


def restyle_one(tmp_path, original, style, title="Novo título"):
    source = tmp_path / "original.pptx"
    original.save(source)
    script = tmp_path / "roteiro.json"
    script.write_text(json.dumps({
        "estilo": style, "avulso": True,
        "slides": [{"tipo": "preservado", "deck": source.name, "slide": 1, "titulo": title}],
    }), encoding="utf-8")
    out = tmp_path / "restyle.pptx"
    result = run_cli("gerar", script, out)
    assert result.returncode == 0, result.stderr
    return list(Presentation(out).slides[0].shapes)


def picture_fill(slide, image):
    _, rid = slide.part.get_or_add_image_part(str(image))
    slide._element.cSld.insert(0, parse_xml(
        f'<p:bg {nsdecls("p", "a", "r")}><p:bgPr><a:blipFill><a:blip r:embed="{rid}"/>'
        '<a:stretch><a:fillRect/></a:stretch></a:blipFill></p:bgPr></p:bg>'
    ))


@pytest.mark.parametrize("picture_kind", ["shape", "fill"])
def test_preserved_copies_full_slide_picture_behind_labels(tmp_path, picture_kind):
    original = Presentation()
    slide = original.slides.add_slide(original.slide_layouts[6])
    image = tmp_path / "photo.png"
    Image.new("RGB", (32, 24), "#9C4C48").save(image)
    label = slide.shapes.add_textbox(Inches(2), Inches(3), Inches(1), Inches(0.5))
    label.text = "Rótulo"
    if picture_kind == "shape":
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor.from_string("101010")
        picture = slide.shapes.add_picture(str(image), 0, 0, original.slide_width, original.slide_height)
        picture.name = "Fundo foto"
    else:
        picture_fill(slide, image)

    shapes = restyle_one(tmp_path, original, "ousado")
    pictures = [shape for shape in shapes
                if shape.shape_type == MSO_SHAPE_TYPE.PICTURE and shape.image.blob == image.read_bytes()]
    assert len(pictures) == 1
    picture = pictures[0]
    copied_label = next(shape for shape in shapes if shape.has_text_frame and shape.text == label.text)
    assert shapes.index(picture) < shapes.index(copied_label)
    assert picture.top == pytest.approx(Inches(1.79), abs=1)
    assert picture.height == pytest.approx(Inches(5.375 - 1.79), abs=1)
    scale = picture.height / original.slide_height
    assert copied_label.left - picture.left == pytest.approx(label.left * scale, abs=2)
    assert copied_label.top - picture.top == pytest.approx(label.top * scale, abs=2)
    assert all(shape.name != "Preserved content background" for shape in shapes)


@pytest.mark.parametrize("style, panel_color", [("padrao", "141211"), ("ousado", "1C1212")])
@pytest.mark.parametrize("surface", ["slide", "layout", "master", "rectangle", "layout-image", "shaded", "light"])
def test_preserved_matches_effective_background_contrast(tmp_path, style, panel_color, surface):
    original = Presentation()
    layout = original.slide_layouts[6]
    slide = original.slides.add_slide(layout)
    if surface == "layout-image":
        image = tmp_path / "dark.png"
        Image.new("RGB", (32, 24), "#151515").save(image)
        picture_fill(layout, image)
    elif surface == "rectangle":
        rectangle = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, original.slide_width, original.slide_height)
        rectangle.name = "Retângulo original"
        rectangle.fill.solid()
        rectangle.fill.fore_color.rgb = RGBColor.from_string("303030")
    else:
        fill = {"slide": slide, "layout": layout, "master": layout.slide_master, "shaded": slide,
                "light": layout.slide_master}[surface].background.fill
        fill.solid()
        fill.fore_color.theme_color = MSO_THEME_COLOR.DARK_1
        if surface == "shaded":
            fill.fore_color.theme_color = MSO_THEME_COLOR.LIGHT_1
            fill.fore_color.brightness = -0.8
        if surface == "light":
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = RGBColor.from_string("F0F0F0")
    label = slide.shapes.add_textbox(Inches(2), Inches(3), Inches(3), Inches(1))
    run = label.text_frame.paragraphs[0].add_run()
    run.text = "Texto branco"
    run.font.color.rgb = RGBColor.from_string("FFFFFF")

    shapes = restyle_one(tmp_path, original, style)
    copied_label = next(shape for shape in shapes if shape.has_text_frame and shape.text == label.text)
    assert str(copied_label.text_frame.paragraphs[0].runs[0].font.color.rgb) == "FFFFFF"
    assert all(shape.name != "Retângulo original" for shape in shapes)
    if surface == "layout-image":
        assert all(shape.shape_type != MSO_SHAPE_TYPE.PICTURE or shape.image.blob != image.read_bytes()
                   for shape in shapes)
    panels = [shape for shape in shapes if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
              and shape.fill.type == MSO_FILL.SOLID and str(shape.fill.fore_color.rgb) == panel_color]
    if surface == "light":
        assert panels == []
        return
    assert len(panels) == 1
    panel = panels[0]
    assert shapes.index(panel) < shapes.index(copied_label)
    assert panel.left <= copied_label.left <= copied_label.left + copied_label.width <= panel.left + panel.width
    assert panel.top <= copied_label.top <= copied_label.top + copied_label.height <= panel.top + panel.height


@pytest.fixture
def source_deck(tmp_path):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    background.name = "Fundo"
    background.fill.solid()
    background.fill.fore_color.rgb = RGBColor.from_string("FFFFFF")
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
    assert all((folder / item["caminho"]).read_bytes() == image for item in first["imagens"])
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


def test_extract_ranks_images_by_slide_area_and_filters_decorations(tmp_path):
    prs = Presentation()
    strip = tmp_path / "faixa.png"
    logo = tmp_path / "marca.png"
    photo = tmp_path / "foto.png"
    Image.new("RGB", (1674, 50), "black").save(strip)
    Image.new("RGB", (20, 20), "white").save(logo)
    Image.new("RGB", (16, 16), "red").save(photo)
    for number in range(1, 11):
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = f"Slide {number}"
        if number < 10:
            slide.shapes.add_picture(str(logo), Inches(1), Inches(1), Inches(6), Inches(3))
        if number == 2:
            slide.shapes.add_picture(str(strip), 0, 0, prs.slide_width, Inches(0.3))
            group = slide.shapes.add_group_shape()
            group.shapes.add_picture(str(photo), Inches(2), Inches(4), Inches(2), Inches(1))
            group.width = Inches(4)
            group.height = Inches(2)
    source = tmp_path / "imagens.pptx"
    prs.save(source)
    folder = tmp_path / "rascunho"

    result = run_cli("extrair", source, folder, "--slides", "2")

    assert result.returncode == 0, result.stderr
    slide, = json.loads((folder / "roteiro-rascunho.json").read_text(encoding="utf-8"))["slides"]
    assert slide["tipo"] == "texto_imagem"
    assert [(folder / item["caminho"]).read_bytes() for item in slide["imagens"]] == [
        logo.read_bytes(), photo.read_bytes(), strip.read_bytes(),
    ]
    assert [item["decorativa"] for item in slide["imagens"]] == [True, False, True]
    assert slide["imagem"] == slide["imagens"][1]["caminho"]


@pytest.mark.parametrize("style", ["padrao", "ousado"])
def test_generate_clinical_case_from_extracted_images(tmp_path, style):
    original = Presentation()
    slide = original.slides.add_slide(original.slide_layouts[5])
    slide.shapes.title.text = "Caso de teste"
    decoration = tmp_path / "marca.png"
    photo = tmp_path / "foto.png"
    Image.new("RGB", (16, 16), "white").save(decoration)
    Image.new("RGB", (32, 24), "red").save(photo)
    logo = slide.shapes.add_picture(str(decoration), Inches(9), 0, Inches(0.4))
    logo.name = "Logo"
    slide.shapes.add_picture(str(photo), Inches(1), Inches(2), Inches(4))
    source = tmp_path / "original.pptx"
    original.save(source)
    folder = tmp_path / "rascunho"

    extracted = run_cli("extrair", source, folder)
    assert extracted.returncode == 0, extracted.stderr
    script = folder / "roteiro-rascunho.json"
    draft = json.loads(script.read_text(encoding="utf-8"))
    draft_slide, = draft["slides"]
    assert [item["decorativa"] for item in draft_slide["imagens"]] == [False, True]
    draft_slide["tipo"] = "caso_clinico"
    draft["estilo"] = style
    script.write_text(json.dumps(draft), encoding="utf-8")

    out = tmp_path / "caso.pptx"
    generated = run_cli("gerar", script, out)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    slide, = Presentation(out).slides
    pictures = [shape.image.blob for shape in slide.shapes if shape.shape_type == MSO_SHAPE_TYPE.PICTURE]
    assert pictures.count(photo.read_bytes()) == 1
    assert decoration.read_bytes() not in pictures


def test_extract_maps_single_callout_to_module_badge(tmp_path):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Aula de teste"
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Prática"
    callout = "Conheça o material de apoio"
    slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1), Inches(6), Inches(6), Inches(0.5))
    slide.shapes.add_textbox(Inches(1), Inches(6), Inches(6), Inches(0.5)).text = callout
    source = tmp_path / "divisoria.pptx"
    prs.save(source)
    folder = tmp_path / "rascunho"

    result = run_cli("extrair", source, folder)

    assert result.returncode == 0, result.stderr
    slide = json.loads((folder / "roteiro-rascunho.json").read_text(encoding="utf-8"))["slides"][1]
    assert slide["tipo"] == "modulo"
    assert slide["selo"] == callout
    assert slide["textos"] == ["Prática", callout]


def test_extract_preserves_textless_content_and_flags_empty_slides(tmp_path):
    prs = Presentation()
    photo = tmp_path / "foto.png"
    Image.new("RGB", (16, 16), "red").save(photo)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_picture(str(photo), 0, 0, prs.slide_width, prs.slide_height)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1), Inches(2), Inches(2), Inches(2))
    prs.slides.add_slide(prs.slide_layouts[5])
    source = tmp_path / "sem-texto.pptx"
    prs.save(source)
    folder = tmp_path / "rascunho"

    result = run_cli("extrair", source, folder)

    assert result.returncode == 0, result.stderr
    picture, drawing, empty = json.loads(
        (folder / "roteiro-rascunho.json").read_text(encoding="utf-8")
    )["slides"]
    for slide in (picture, drawing):
        assert slide["tipo"] == "preservado"
        assert slide["revisar"] is True
        assert slide["motivo"] == "conteúdo só em imagem"
        assert not slide.get("vazio")
    assert empty["vazio"] is True


@pytest.mark.parametrize("style", ["padrao", "ousado"])
@pytest.mark.parametrize("title_source", ["detected", "script", "both"])
def test_preserved_omits_only_first_matching_text_box(tmp_path, style, title_source):
    original = Presentation()
    slide = original.slides.add_slide(original.slide_layouts[6])
    notes = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(5), Inches(1))
    notes.name = "Title with notes"
    notes.text = "Título original\nTexto complementar"
    title = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
    title.name = "Original title"
    title.text = "Título original" if title_source == "detected" else "  TÍTULO:\v  ORIGINAL!"
    repeated_top = 0.5 if title_source == "both" else 4
    repeated = slide.shapes.add_textbox(Inches(1), Inches(repeated_top), Inches(5), Inches(1))
    repeated.name = "Second match"
    repeated.text = "título original."
    script_title = "Título revisado" if title_source == "detected" else "Título original"

    shapes = restyle_one(tmp_path, original, style, script_title)

    copied_text = {shape.name: shape.text for shape in shapes if shape.has_text_frame}
    assert title.name not in copied_text
    assert copied_text[notes.name] == "Título original\nTexto complementar"
    assert copied_text[repeated.name] == "título original."
    assert sum(value.casefold() == script_title.casefold() for value in copied_text.values()) == 1


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


@pytest.mark.parametrize("style, content_top, content_bottom", [
    ("padrao", 1.4, 5.275),
    ("ousado", 1.79, 5.375),
])
@pytest.mark.parametrize("extra_extent", ["table-frame", "background"])
def test_preserved_fits_centered_content(tmp_path, style, content_top, content_bottom, extra_extent):
    original = Presentation()
    slide = original.slides.add_slide(original.slide_layouts[5])
    slide.shapes.title.text = "Título original"
    if extra_extent == "background":
        background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, original.slide_width, original.slide_height)
        background.fill.solid()
        background.fill.fore_color.rgb = RGBColor.from_string("FFFFFF")
    label = slide.shapes.add_textbox(Inches(3), Inches(3), Inches(4), Inches(1))
    label.name = "Rótulo central"
    label.text_frame.margin_left = Inches(0.2)
    run = label.text_frame.paragraphs[0].add_run()
    run.text = "Conteúdo"
    run.font.size = Pt(8)
    label.line.width = Pt(2)
    frame = slide.shapes.add_table(1, 1, Inches(3), Inches(4), Inches(4), Inches(1))
    frame.name = "Tabela central"
    cell = frame.table.cell(0, 0)
    cell.text = "Célula"
    cell._tc.get_or_add_tcPr().append(parse_xml(f'<a:lnL {nsdecls("a")} w="{Pt(1)}"/>'))
    if extra_extent == "table-frame":
        frame.height = Inches(5)
    source = tmp_path / "original.pptx"
    original.save(source)

    script = tmp_path / "roteiro.json"
    script.write_text(json.dumps({
        "estilo": style, "avulso": True,
        "slides": [{"tipo": "preservado", "deck": source.name, "slide": 1, "titulo": "Novo título"}],
    }), encoding="utf-8")
    out = tmp_path / "restyle.pptx"
    result = run_cli("gerar", script, out)
    assert result.returncode == 0, result.stderr
    deck = Presentation(out)
    shapes = deck.slides[0].shapes
    copied_label = next(shape for shape in shapes if shape.name == label.name)
    copied_table = next(shape for shape in shapes if shape.name == frame.name)

    left, right = Inches(0.45), deck.slide_width - Inches(0.45)
    top, bottom = Inches(content_top), Inches(content_bottom)
    copied_bottom = copied_table.top + copied_table.table.rows[0].height
    copied_width = copied_label.width
    copied_height = copied_bottom - copied_label.top
    assert max(copied_width / (right - left), copied_height / (bottom - top)) >= 0.90
    assert copied_width / copied_height == pytest.approx(2, abs=0.00001)
    assert copied_table.top + copied_table.height == copied_bottom
    assert copied_label.left + copied_width / 2 == pytest.approx((left + right) / 2, abs=2)
    assert copied_label.top + copied_height / 2 == pytest.approx((top + bottom) / 2, abs=2)
    for copied in (copied_label, copied_table):
        assert left <= copied.left <= copied.left + copied.width <= right
        assert top - 1 <= copied.top <= copied.top + copied.height <= bottom + 1

    scale = copied_width / label.width
    copied_run = copied_label.text_frame.paragraphs[0].runs[0]
    assert scale > 1
    assert copied_run.font.size.pt == pytest.approx(8 * scale, abs=0.005)
    assert copied_label.line.width == pytest.approx(Pt(2) * scale, abs=1)
    assert copied_label.text_frame.margin_left == pytest.approx(Inches(0.2) * scale, abs=1)
    assert copied_label.text_frame.margin_top == pytest.approx(Inches(0.05) * scale, abs=1)
    copied_cell = copied_table.table.cell(0, 0)
    assert copied_cell.margin_left == pytest.approx(Inches(0.1) * scale, abs=1)
    border_width = int(copied_cell._tc.tcPr.find(qn("a:lnL")).get("w"))
    assert border_width == pytest.approx(Pt(1) * scale, abs=1)
    if extra_extent == "background":
        assert all(shape.name != slide.shapes[1].name for shape in shapes)
