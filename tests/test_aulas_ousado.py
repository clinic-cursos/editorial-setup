"""Para consultar a impressão digital de um PowerPoint sem sobrescrever a da v1:

uv run --locked python tests/test_aulas_ousado.py /var/tmp/aulas-render/in/modelo.pptx
"""

from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from textwrap import wrap
from zipfile import ZipFile

from PIL import Image
from pptx import Presentation
from pptx.enum.dml import MSO_COLOR_TYPE
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from pptx.util import Inches
import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "aulas"
FIXTURE = Path(__file__).parent / "fixtures" / "aulas" / "modelo-v1.json"
MODEL = SKILL / "references" / "modelo_hof_roteiro.json"
BOLD_EXAMPLE = SKILL / "references" / "exemplo_ousado.json"
MORPH = "{http://schemas.microsoft.com/office/powerpoint/2015/09/main}morph"
# Cada !!foto mantém a geometria original e ganha as caixas de texto do prompt.
# Os slides 5, 6 e 13 têm título, corpo e instrução. Os demais incluem aviso.
PHOTO_REPLACEMENTS = {
    5: ("!!foto", 3),
    6: ("!!foto", 3),
    8: ("!!foto", 4),
    11: ("!!foto", 4),
    13: ("!!foto", 3),
    14: ("!!foto", 4),
}


def fingerprint(slide, *, omit_text=()):
    morph_shapes = [shape for shape in slide.shapes if shape.name.startswith("!!")]
    assert len(morph_shapes) == len({shape.name for shape in morph_shapes})
    background = next(shape for shape in morph_shapes if shape.name == "!!fundo")
    text_shapes = [shape for shape in slide.shapes
                   if shape.has_text_frame and shape.text and shape.name not in omit_text]
    return {
        "background": str(background.fill.fore_color.rgb),
        "shapes": {
            shape.name: [round(getattr(shape, dimension).inches, 5)
                         for dimension in ("left", "top", "width", "height")]
            for shape in morph_shapes
        },
        "texts": [shape.text for shape in text_shapes],
        "runs": [run_fingerprint(run)
                 for shape in text_shapes for paragraph in shape.text_frame.paragraphs
                 for run in paragraph.runs if run.text],
    }


def run_fingerprint(run):
    font = run.font
    return {
        "text": run.text,
        "size_pt": font.size.pt if font.size is not None else None,
        "font": font.name,
        "bold": font.bold,
        "color": str(font.color.rgb) if font.color.type == MSO_COLOR_TYPE.RGB else None,
    }


def run_styles(runs):
    styles = defaultdict(list)
    for run in runs:
        styles[run["text"]].append((run["size_pt"], run["font"], run["bold"], run["color"]))
    return styles


def generate(path, out):
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "aulas.py"), "gerar", str(path), str(out)],
        capture_output=True, text=True,
    )


def write_script(tmp_path, slides, **fields):
    path = tmp_path / "roteiro.json"
    spec = {"estilo": "ousado", "avulso": True, "slides": slides, **fields}
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def assert_motion(slide):
    assert next(slide._element.iter(MORPH)).get("option") == "byObject"
    timing = slide._element.find(qn("p:timing"))
    assert timing is not None
    targets = {int(target.get("spid")) for target in timing.iter(qn("p:spTgt"))}
    assert targets and targets <= {shape.shape_id for shape in slide.shapes}


def test_bold_example_passes_editorial_check(tmp_path):
    assert BOLD_EXAMPLE.is_file(), "Falta o roteiro de exemplo do estilo ousado"
    example = json.loads(BOLD_EXAMPLE.read_text(encoding="utf-8"))
    assert example["estilo"] == "ousado"
    assert Counter(slide["tipo"] for slide in example["slides"]) == Counter({
        kind: 1 for kind in (
            "capa", "sumario", "modulo", "frase", "pilares", "texto_imagem",
            "passo_a_passo", "numero", "duas_colunas", "anatomia", "comparativo",
            "alerta", "numeros", "encerramento",
        )
    })
    out = tmp_path / "exemplo.pptx"
    result = generate(BOLD_EXAMPLE, out)
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(Presentation(out).slides) == len(example["slides"])


def field_names(value):
    if isinstance(value, dict):
        return set(value).union(*(field_names(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(field_names(item) for item in value))
    return set()


def test_bold_example_fields_are_documented():
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    _, heading, remainder = skill.partition("## Campos no estilo ousado\n")
    assert heading, "Falta a seção Campos no estilo ousado"
    section = remainder.split("\n## ", 1)[0]
    example = json.loads(BOLD_EXAMPLE.read_text(encoding="utf-8"))
    missing = sorted(field for field in field_names(example) if f"`{field}`" not in section)
    assert not missing, f"Campos do exemplo ausentes na seção: {missing}"


@pytest.mark.parametrize("path,expected", [
    (FIXTURE, "16cd27dfde15fe5c4d97ff610cfdc5ef8a41a2f1be883c5f4459843ba8b06036"),
    (MODEL, "3ef1fe1a54b0600299284841a7be8e95e46b66e3568a56a212038e6754d9fc7f"),
])
def test_master_v1_files_are_immutable(path, expected):
    assert sha256(path.read_bytes()).hexdigest() == expected, (
        f"{path.name}: modelo mestre v1 não muda; para mudar o visual, crie o modelo v2 ao lado"
    )


def test_model_matches_reference(tmp_path):
    out = tmp_path / "modelo.pptx"
    result = generate(MODEL, out)
    assert result.returncode == 0, result.stderr
    reference = json.loads(FIXTURE.read_text(encoding="utf-8"))
    slides = Presentation(out).slides
    assert len(slides) == len(reference) == 16
    style_mismatches = []
    breakable = str.maketrans("\u00a0\u2011", " -")
    for number, (slide, expected) in enumerate(zip(slides, reference, strict=True), 1):
        prompts = [shape for shape in slide.shapes if shape.name.startswith("Texto do prompt ")]
        omitted = ()
        if number in PHOTO_REPLACEMENTS:
            photo_name, count = PHOTO_REPLACEMENTS[number]
            photo = next(shape for shape in slide.shapes if shape.name == photo_name)
            assert photo.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
            omitted = tuple(f"Texto do prompt {i}" for i in range(1, count + 1))
            assert tuple(shape.name for shape in prompts) == omitted
            assert prompts[0].text.startswith("✦ PROMPT DE IMAGEM ")
            assert all(shape.text for shape in prompts)
        else:
            assert not prompts
        actual = fingerprint(slide, omit_text=omitted)
        assert actual["background"] == expected["background"], number
        assert actual["shapes"].keys() == expected["shapes"].keys(), number
        for name, geometry in expected["shapes"].items():
            assert actual["shapes"][name] == pytest.approx(geometry, abs=0.02), (number, name)
        # Estes caracteres mudam a quebra de linha e preservam o texto visível.
        for snapshot in (actual, expected):
            snapshot["texts"] = [value.translate(breakable) for value in snapshot["texts"]]
            for run in snapshot["runs"]:
                run["text"] = run["text"].translate(breakable)
        assert Counter(actual["texts"]) == Counter(expected["texts"]), number
        actual_texts = Counter(run["text"] for run in actual["runs"])
        expected_texts = Counter(run["text"] for run in expected["runs"])
        # No slide 13, dois runs do modelo formam um run no roteiro.
        unmatched = (sum((expected_texts - actual_texts).values()),
                     sum((actual_texts - expected_texts).values()))
        assert unmatched == ((2, 1) if number == 13 else (0, 0)), number
        actual_styles = run_styles(actual["runs"])
        expected_styles = run_styles(expected["runs"])
        for text in expected_styles:
            if text in actual_styles and actual_styles[text] != expected_styles[text]:
                style_mismatches.append((number, text, expected_styles[text], actual_styles[text]))
        assert_motion(slide)
    assert not style_mismatches, f"Tipografia (slide, texto, modelo, gerado): {style_mismatches}"


@pytest.mark.parametrize("kicker, multiline", [(True, False), (False, False), (True, True)])
def test_bold_preserved_uses_model_content_frame(tmp_path, kicker, multiline):
    reference = json.loads(FIXTURE.read_text(encoding="utf-8"))[7]
    kicker_text = reference["texts"][0]
    first_run, accent = (run["text"] for run in reference["runs"][1:3])
    separator = "\n" if multiline else ""
    original = Presentation()
    source = original.slides.add_slide(original.slide_layouts[6])
    body = source.shapes.add_shape(MSO_SHAPE.OVAL, Inches(2), Inches(1), Inches(1), Inches(3))
    source_path = tmp_path / "original.pptx"
    original.save(source_path)
    data = {"tipo": "preservado", "deck": source_path.name, "slide": 1,
            "titulo": f"{first_run}{separator}**{accent}**"}
    if kicker:
        data["kicker"] = kicker_text.lower()
    out = tmp_path / "preservado.pptx"

    result = generate(write_script(tmp_path, [data], avulso=True), out)
    assert result.returncode == 0, result.stderr
    slide = Presentation(out).slides[0]
    actual = fingerprint(slide)
    assert actual["background"] == reference["background"]
    frame = {name: box for name, box in reference["shapes"].items() if name != "!!foto"}
    assert actual["shapes"] == {name: pytest.approx(box, abs=0.02) for name, box in frame.items()}
    assert len(slide.shapes) == len(frame) + 2 + kicker
    assert all(shape.shape_type != MSO_SHAPE_TYPE.LINE for shape in slide.shapes)
    title_text = f"{first_run}{separator}{accent}"
    heading = next(shape for shape in slide.shapes if shape.has_text_frame and shape.text == title_text)
    assert (heading.left.inches, heading.top.inches, heading.width.inches) == pytest.approx(
        (0.45, 0.62, 6.0), abs=0.02)
    expected_texts = [title_text]
    expected_runs = reference["runs"][1:3]
    if kicker:
        label = next(shape for shape in slide.shapes if shape.has_text_frame and shape.text == kicker_text)
        assert (label.left.inches, label.top.inches, label.width.inches, label.height.inches) == pytest.approx(
            (0.45, 0.42, 5.0, 0.25), abs=0.02)
        expected_texts.insert(0, kicker_text)
        expected_runs = reference["runs"][:3]
    assert actual["texts"] == expected_texts
    assert actual["runs"] == expected_runs
    if multiline:
        assert heading.height.inches > 0.6
    else:
        assert heading.height.inches == pytest.approx(0.6, abs=0.02)
    copied = next(shape for shape in slide.shapes if shape.name == body.name)
    assert copied.top.inches == pytest.approx(1.35 + max(0, heading.height.inches - 0.6), abs=0.02)
    assert_motion(slide)


@pytest.mark.parametrize("slide,model_size", [
    ({"tipo": "numero"}, 130),
    ({"tipo": "anatomia", "prompt_imagem": "Cena de teste"}, 40),
])
def test_bold_number_size_respects_text_width(tmp_path, slide, model_size):
    values = ["123", "123456789012345"]
    path = write_script(tmp_path, [
        {**slide, "valor": value, "indicador": {"valor": value}}
        for value in values
    ])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stderr
    presentation = Presentation(out)
    for generated, value in zip(presentation.slides, values, strict=True):
        shape = next(shape for shape in generated.shapes
                     if shape.has_text_frame and shape.text == value)
        size = shape.text_frame.paragraphs[0].runs[0].font.size.pt
        available_pt = shape.width.pt - shape.text_frame.margin_left.pt - shape.text_frame.margin_right.pt
        assert shape.left + shape.width <= presentation.slide_width
        assert size * len(value) <= available_pt
        if value == values[0]:
            assert size == model_size
        else:
            assert 0 < size < model_size


@pytest.mark.parametrize("value,advance", [("3 a 4", 2.513), ("WWWWW", 5.920)])
def test_bold_number_fits_inside_arc(tmp_path, value, advance):
    out = tmp_path / "aula.pptx"
    result = generate(write_script(tmp_path, [{"tipo": "numero", "valor": value}]), out)
    assert result.returncode == 0, result.stdout + result.stderr
    shape = next(shape for shape in Presentation(out).slides[0].shapes
                 if shape.has_text_frame and shape.text == value)
    size = shape.text_frame.paragraphs[0].runs[0].font.size.pt
    left = shape.left.pt + (shape.width.pt - size * advance) / 2
    # Borda interna esquerda na altura do topo do valor, mais 0,1 pol de folga.
    assert left >= Inches(3.1279).pt


@pytest.mark.parametrize("dimensions,content", [
    ((240, 160), (0, 16, 240, 144)),
    ((80, 240), (0, 0, 80, 240)),
])
def test_bold_pillars_photo_covers_panel(tmp_path, dimensions, content):
    photo = Image.new("RGB", dimensions, (254, 254, 254))
    photo.paste((90, 70, 65), content)
    photo.save(tmp_path / "foto.png")
    path = write_script(tmp_path, [{"tipo": "pilares", "imagem": "foto.png"}])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr
    deck = Presentation(out)
    picture = next(shape for shape in deck.slides[0].shapes if shape.name == "!!foto")
    assert (picture.left, picture.top, picture.width, picture.height) == (
        0, 0, Inches(4.3), deck.slide_height,
    )
    width, height = dimensions
    left, top, right, bottom = content
    assert picture.crop_top * height >= top
    assert picture.crop_bottom * height >= height - bottom
    assert picture.crop_left - picture.crop_right == pytest.approx((left + right - width) / width)
    assert picture.crop_top - picture.crop_bottom == pytest.approx((top + bottom - height) / height)
    cropped_width = width * (1 - picture.crop_left - picture.crop_right)
    cropped_height = height * (1 - picture.crop_top - picture.crop_bottom)
    assert cropped_width / cropped_height == pytest.approx(4.3 / 5.625, abs=0.0001)


def test_bold_pillars_keeps_dividers_below_item_text(tmp_path):
    long_body = " ".join(["Detalhe importante para a atividade."] * 4)
    rows = [{"titulo": "Primeiro", "texto": long_body}, {"titulo": "Próximo", "texto": "Resumo"}]
    path = write_script(tmp_path, [{"tipo": "pilares", "prompt_imagem": "Cena de teste", "pilares": rows}])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    shapes = Presentation(out).slides[0].shapes
    body = next(shape for shape in shapes if shape.has_text_frame and shape.text == long_body)
    divider = next(shape for shape in shapes if shape.shape_type == MSO_SHAPE_TYPE.LINE)
    following = next(shape for shape in shapes if shape.has_text_frame and shape.text == "PRÓXIMO")
    assert body.height > Inches(0.5)
    assert body.top + body.height < divider.top < following.top
    assert result.returncode == 0, result.stdout + result.stderr


def test_bold_pillars_grows_info_band(tmp_path):
    info = "\n".join(f"Informação {i}" for i in range(1, 6))
    Image.new("RGB", (100, 100), (90, 70, 65)).save(tmp_path / "foto.png")
    path = write_script(tmp_path, [{"tipo": "pilares", "imagem": "foto.png", "info": info}])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    shapes = Presentation(out).slides[0].shapes
    label = next(shape for shape in shapes if shape.has_text_frame and shape.text == info)
    band = next(shape for shape in shapes if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
                and shape.left == 0 and shape.width == Inches(4.3))
    assert band.height > Inches(1)
    assert band.top < label.top < label.top + label.height < band.top + band.height
    assert result.returncode == 0, result.stdout + result.stderr


def test_bold_uses_relative_image_and_slide_text(tmp_path):
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": "Título independente", "texto": "Texto independente",
        "imagem": "foto.png", "prompt_imagem": "Cena de teste",
    }])
    (tmp_path / "foto.png").write_bytes((SKILL / "assets" / "logo_cor.png").read_bytes())
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stderr
    deck = Presentation(out)
    slide = deck.slides[0]
    photo = next(shape for shape in slide.shapes if shape.name == "!!foto")
    assert photo.shape_type == MSO_SHAPE_TYPE.PICTURE
    assert photo.width == Inches(3) and photo.height == deck.slide_height
    assert photo.crop_left > 0 and photo.crop_right > 0
    assert {"Título independente", "Texto independente"} <= set(fingerprint(slide)["texts"])
    assert not out.with_name("aula - prompts de imagem.md").exists()


@pytest.mark.parametrize("kind,fields", [
    ("pilares", {"pilares": [{"titulo": "Entrada", "texto": "Texto principal"}]}),
    ("passo_a_passo", {"passos": [{"titulo": "Entrada", "texto": "Texto principal"}]}),
    ("alerta", {"itens": [{"titulo": "Entrada", "texto": "Texto principal"}]}),
    ("texto_imagem", {"texto": "Texto principal"}),
])
def test_bold_optional_image_panel_uses_full_text_width_when_omitted(tmp_path, kind, fields):
    Image.new("RGB", (60, 40)).save(tmp_path / "foto.png")
    slide = {"tipo": kind, "titulo": "Título de teste", "legenda": "Legenda de reserva", **fields}
    path = write_script(tmp_path, [
        slide, {**slide, "imagem": "foto.png"}, {**slide, "prompt_imagem": "Cena de teste"},
    ], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr

    deck = Presentation(out)
    text_only, with_photo, with_prompt = deck.slides
    assert not any(shape.name == "!!foto" or shape.name.startswith("Texto do prompt ")
                   for shape in text_only.shapes)
    assert any(shape.name == "!!foto" and shape.shape_type == MSO_SHAPE_TYPE.PICTURE
               for shape in with_photo.shapes)
    assert any(shape.name == "!!foto" and shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
               for shape in with_prompt.shapes)
    assert any(shape.name.startswith("Texto do prompt ") and "Cena de teste" in shape.text
               for shape in with_prompt.shapes)
    if kind == "passo_a_passo":
        assert not any(shape.width == Inches(5.2) and shape.height == Inches(3)
                       for shape in text_only.shapes)

    full, narrow, prompt = (
        next(shape for shape in generated.shapes if shape.has_text_frame and "Texto principal" in shape.text)
        for generated in deck.slides
    )
    assert full.width > narrow.width == prompt.width
    assert full.left + full.width == pytest.approx(deck.slide_width - Inches(0.45), abs=1)


@pytest.mark.parametrize("kind,field,expected_size", [
    ("passo_a_passo", "passos", 18),
    ("alerta", "itens", 18),
    ("pilares", "pilares", 18),
    ("texto_imagem", "topicos", 15),
])
def test_bold_text_only_enlarges_five_short_items(tmp_path, kind, field, expected_size):
    items = [f"Item {i}" for i in range(1, 6)]
    values = items if kind == "texto_imagem" else [{"texto": item} for item in items]
    path = write_script(tmp_path, [{"tipo": kind, "titulo": "Roteiro", field: values}], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    runs = run_styles(fingerprint(Presentation(out).slides[0])["runs"])
    assert [runs[item][0][0] for item in items] == [expected_size] * len(items)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("kind,field,count", [
    ("passo_a_passo", "passos", 6),
    ("alerta", "itens", 4),
    ("pilares", "pilares", 5),
    ("texto_imagem", "topicos", 5),
])
def test_bold_text_only_fits_dense_items_at_the_floor(tmp_path, kind, field, count):
    content = "Planeje as etapas e revise o material. " * 5 + "Fim."
    items = [f"{i}. {content}" for i in range(1, count + 1)]
    values = items if kind == "texto_imagem" else [{"titulo": f"Etapa {i}", "texto": item}
                                                   for i, item in enumerate(items, 1)]
    path = write_script(tmp_path, [{"tipo": kind, "titulo": "Roteiro", field: values}], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    deck = Presentation(out)
    slide = deck.slides[0]
    runs = run_styles(fingerprint(slide)["runs"])
    for item in items:
        assert runs[item][0][0] == 8
    if kind != "texto_imagem":
        assert 8 < runs["ETAPA 1" if kind != "passo_a_passo" else "Etapa 1"][0][0] <= 10
    boxes = [shape for shape in slide.shapes if shape.has_text_frame
             and any(item in shape.text for item in items)]
    assert all(first.top + first.height <= second.top for first, second in zip(boxes, boxes[1:]))
    assert boxes[-1].top + boxes[-1].height <= deck.slide_height
    if kind == "texto_imagem":
        for box in boxes:
            frame = box.text_frame
            width = box.width.pt - frame.margin_left.pt - frame.margin_right.pt
            line_count = sum(len(wrap(line, width=int(width / (8 * 0.6)))) for line in box.text.splitlines())
            assert line_count * 8 * 1.2 + frame.margin_top.pt + frame.margin_bottom.pt <= box.height.pt
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("heading", [
    "Planejamento",
    "Um roteiro claro ajuda a organizar as atividades da oficina e preparar o material de apoio",
])
def test_bold_text_only_title_has_a_two_line_limit(tmp_path, heading):
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": heading, "texto": "Confira o roteiro.",
    }], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr
    slide = Presentation(out).slides[0]
    title, body = [next(shape for shape in slide.shapes if shape.has_text_frame and shape.text == value)
                   for value in (heading, "Confira o roteiro.")]
    frame = title.text_frame
    size = frame.paragraphs[0].runs[0].font.size.pt
    width = title.width.pt - frame.margin_left.pt - frame.margin_right.pt
    assert 18 <= size <= 40
    assert len(wrap(heading, width=int(width / (size * 0.7)), break_long_words=False)) <= 2
    assert title.top + title.height <= body.top


def test_bold_text_only_topic_heading_scales_with_body(tmp_path):
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": "Roteiro",
        "topicos": [{"titulo": "Planejamento", "texto": "Confira o roteiro."}],
    }], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    runs = run_styles(fingerprint(Presentation(out).slides[0])["runs"])
    assert runs["Planejamento"][0][0] == pytest.approx(runs["Confira o roteiro."][0][0] * 1.2)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("panel", [{}, {"prompt_imagem": "Cena de teste"}], ids=["text-only", "with-panel"])
def test_bold_pillars_badge_matches_module_without_covering_text(tmp_path, panel):
    label = "Conheça nosso curso online de planejamento de aulas"
    path = write_script(tmp_path, [
        {"tipo": "modulo", "numero": 1, "titulo": "Planejamento", "selo": label},
        {"tipo": "pilares", "titulo": "Planejamento", "selo": label,
         "pilares": [{"titulo": f"Etapa {i}", "texto": f"Descrição da etapa {i}"} for i in range(1, 4)],
         "info": "Atividade em grupo\nOficina de aulas", "referencia": "Roteiro da oficina", **panel},
    ], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr

    module, pillars = Presentation(out).slides
    module_label, pillars_label = [
        next((shape for shape in slide.shapes if shape.has_text_frame and shape.text == label), None)
        for slide in (module, pillars)
    ]
    assert module_label is not None
    assert pillars_label is not None, "O selo deve aparecer no slide de pilares"

    def badge_background(slide, box):
        return next(shape for shape in slide.shapes if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
                    and (shape.left, shape.top, shape.width, shape.height)
                    == (box.left, box.top, box.width, box.height))

    module_badge = badge_background(module, module_label)
    pillars_badge = badge_background(pillars, pillars_label)
    assert pillars_badge.auto_shape_type == module_badge.auto_shape_type
    assert pillars_badge.fill.fore_color.rgb == module_badge.fill.fore_color.rgb
    assert pillars_badge.height == module_badge.height
    assert run_fingerprint(pillars_label.text_frame.paragraphs[0].runs[0]) == run_fingerprint(
        module_label.text_frame.paragraphs[0].runs[0],
    )

    content = {shape.text: shape for shape in pillars.shapes
               if shape.has_text_frame and shape.text and shape.shape_id != pillars_label.shape_id}
    assert {"Descrição da etapa 3", "Atividade em grupo\nOficina de aulas", "Roteiro da oficina"} <= content.keys()
    for caption, shape in content.items():
        assert (
            shape.left + shape.width <= pillars_badge.left
            or pillars_badge.left + pillars_badge.width <= shape.left
            or shape.top + shape.height <= pillars_badge.top
            or pillars_badge.top + pillars_badge.height <= shape.top
        ), caption


@pytest.mark.parametrize("kind", ["anatomia", "comparativo"])
def test_bold_required_image_panel_needs_image_or_prompt(tmp_path, kind):
    path = write_script(tmp_path, [{"tipo": kind, "titulo": "Título de teste"}], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode != 0
    assert f"{kind} exige imagem ou prompt_imagem" in result.stderr
    assert not out.exists()


@pytest.mark.parametrize("heading", [
    "Envelhecimento",
    "TECNOLOGIA DE FABRICAÇÃO DOS NEUROMODULADORES",
])
def test_bold_text_image_title_fits_without_splitting_words(tmp_path, heading):
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": heading, "texto": "Corpo do slide", "prompt_imagem": "Cena de teste",
    }])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr
    slide = Presentation(out).slides[0]
    title, body = (
        next(shape for shape in slide.shapes if shape.has_text_frame and shape.text == value)
        for value in (heading, "Corpo do slide")
    )
    frame = title.text_frame
    size = frame.paragraphs[0].runs[0].font.size.pt
    width = title.width.pt - frame.margin_left.pt - frame.margin_right.pt
    # Use a conservative average to verify wrapping in the emitted title box.
    columns = int(width / (size * 0.75))
    assert all(len(word) <= columns for word in heading.split())
    rows = wrap(heading, width=columns, break_long_words=False, break_on_hyphens=False)
    height = len(rows) * size * 1.2 + frame.margin_top.pt + frame.margin_bottom.pt
    assert height <= title.height.pt
    assert title.top + title.height <= body.top
    assert 18 <= size < 46


@pytest.mark.parametrize("repetitions,exit_code", [(30, 0), (100, 1)])
def test_bold_text_image_body_fits_or_keeps_overflow_for_review(tmp_path, repetitions, exit_code):
    content = "Texto de apoio " * repetitions + "Fim do texto."
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": "Título", "texto": content, "prompt_imagem": "Cena de teste",
    }])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == exit_code, result.stdout + result.stderr
    slide = Presentation(out).slides[0]
    body = next(shape for shape in slide.shapes if shape.has_text_frame and shape.text == content)
    size = body.text_frame.paragraphs[0].runs[0].font.size.pt
    if exit_code:
        assert size == 8
        assert "Texto provavelmente estourado" in result.stdout
    else:
        assert 8 <= size < 11


@pytest.mark.parametrize("kind,bottom,default_size,reduced,overflow", [
    ("passo_a_passo", 4.78, 8.5, 13, 14),
    ("duas_colunas", 5.075, 11, 8, 14),
    ("alerta", 5.025, 9.5, 12, 17),
    ("sumario", 4.95, 10, 9, 16),
])
@pytest.mark.parametrize("case", ["default", "reduced", "overflow"])
def test_bold_list_fits_items_or_keeps_overflow_for_review(tmp_path, kind, bottom, default_size, reduced, overflow, case):
    repetitions = {"default": 4, "reduced": reduced, "overflow": overflow}[case]
    body = "Primeiro item. " + "Texto de teste com várias palavras. " * repetitions + "Final."
    next_item = "Segundo item."
    heading = "UM TÍTULO LONGO PARA TESTAR A TERCEIRA LINHA"
    item_title = (
        "UM TÍTULO DE TESTE QUE PRECISA OCUPAR TRÊS LINHAS PARA EXERCITAR O ESPAÇO"
        if kind == "passo_a_passo" else "Entrada"
    )
    blocks = [{"titulo": item_title, "texto": body},
              {"titulo": "Continuação", "texto": next_item}]
    fields = {
        "passo_a_passo": {"passos": blocks, "prompt_imagem": "Cena de teste"},
        "duas_colunas": {"colunas": [{"titulo": heading, "itens": [body, next_item]}], "nota": "Rodapé"},
        "alerta": {"itens": blocks, "urgente": "Rodapé", "prompt_imagem": "Cena de teste"},
        "sumario": {"itens": [body, next_item]},
    }
    path = write_script(tmp_path, [{"tipo": kind, **fields[kind]}], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    slide = Presentation(out).slides[0]
    first = next(shape for shape in slide.shapes if shape.has_text_frame and body in shape.text)
    second = next(shape for shape in slide.shapes if shape.has_text_frame and next_item in shape.text)
    run = next(run for paragraph in first.text_frame.paragraphs for run in paragraph.runs if run.text == body)
    assert run.font.size.pt >= 8
    if case == "overflow":
        assert run.font.size.pt == 8
        assert result.returncode == 1, result.stdout + result.stderr
        assert "Forma fora dos limites do slide" in result.stdout
        return

    if kind == "duas_colunas":
        column = next(shape for shape in slide.shapes if shape.has_text_frame and shape.text == heading)
        assert column.height > Inches(0.5)
        assert column.top + column.height <= first.top
    assert first.height > Inches(0.75)
    assert first.top + first.height <= second.top
    assert second.top + second.height <= Inches(bottom)
    assert run.font.size.pt == (default_size if case == "default" else max(8, default_size - 1))
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("image_size,topics,min_width", [
    ((300, 100), [], 0.90),
    ((100, 400), [], 0),
    ((300, 100), ["Primeiro item.", "Segundo item."], 0.55),
])
def test_bold_text_image_contains_picture_in_available_content(tmp_path, image_size, topics, min_width):
    Image.new("RGB", image_size).save(tmp_path / "diagrama.png")
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": "Diagrama", "imagem": "diagrama.png", "imagem_modo": "conter",
        "topicos": topics,
    }])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr
    deck = Presentation(out)
    shapes = deck.slides[0].shapes
    photo = next(shape for shape in shapes if shape.name == "!!foto")
    assert photo.shape_type == MSO_SHAPE_TYPE.PICTURE
    assert photo.width / photo.height == pytest.approx(image_size[0] / image_size[1], abs=1e-5)
    assert (photo.crop_left, photo.crop_right, photo.crop_top, photo.crop_bottom) == (0, 0, 0, 0)
    margin = Inches(0.45)
    useful_width = deck.slide_width - 2 * margin
    assert photo.width >= min_width * useful_width
    heading = next(shape for shape in shapes if shape.has_text_frame and shape.text == "Diagrama")
    assert margin <= photo.left < photo.left + photo.width <= deck.slide_width - margin
    assert heading.top + heading.height <= photo.top < photo.top + photo.height <= deck.slide_height - margin
    if topics:
        body = next(shape for shape in shapes if shape.has_text_frame and shape.text.splitlines() == topics)
        assert body.width <= 0.40 * useful_width
        assert body.left + body.width < photo.left
    else:
        assert 2 * photo.left + photo.width == pytest.approx(deck.slide_width, abs=2)


@pytest.mark.parametrize("image_size,heading,at_floor", [
    ((160, 90), "Leitura e interpretação das informações do diagrama", False),
    ((300, 100), "Leitura e interpretação das informações do diagrama", False),
    ((100, 400), "Guia de leitura e interpretação das informações do diagrama", True),
])
def test_bold_text_image_compacts_header_without_body(tmp_path, monkeypatch, image_size, heading, at_floor):
    monkeypatch.syspath_prepend(str(SKILL / "scripts"))
    from conferir import Theme, check_text

    Image.new("RGB", image_size).save(tmp_path / "diagrama.png")
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": heading, "kicker": "Visão geral",
        "imagem": "diagrama.png", "imagem_modo": "conter",
    }])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr
    deck = Presentation(out)
    slide = deck.slides[0]
    labels = {shape.text: shape for shape in slide.shapes if shape.has_text_frame}
    title, kicker = labels[heading], labels["VISÃO GERAL"]
    assert (kicker.left.inches, kicker.top.inches, kicker.width.inches, kicker.height.inches) == pytest.approx(
        (0.45, 0.42, 5.0, 0.25), abs=0.02)
    assert kicker.top < title.top
    model_kicker = json.loads(FIXTURE.read_text(encoding="utf-8"))[7]["runs"][0]
    assert run_fingerprint(kicker.text_frame.paragraphs[0].runs[0]) == {**model_kicker, "text": kicker.text}
    logo = next(shape for shape in slide.shapes if shape.name == "!!logo")
    assert max(kicker.left + kicker.width, title.left + title.width) <= logo.left

    frame = title.text_frame
    margins = frame.margin_left, frame.margin_right, frame.margin_top, frame.margin_bottom
    _, rows = check_text(frame, title, Theme(slide, deck), set(), lambda *args: None,
                         title.width, title.height, margins, title.top, deck.slide_height)
    assert len(rows) == 1
    assert frame.word_wrap is False
    size = frame.paragraphs[0].runs[0].font.size.pt
    assert 18 <= size < 36
    if at_floor:
        assert size == 18

    photo = next(shape for shape in slide.shapes if shape.name == "!!foto")
    margin = Inches(0.45)
    useful_width = deck.slide_width - 2 * margin
    content_top = title.top + title.height + Inches(0.1)
    content_bottom = deck.slide_height - margin
    useful_height = content_bottom - content_top
    assert photo.width >= 0.85 * useful_width or photo.height >= 0.80 * useful_height
    assert photo.width / photo.height == pytest.approx(image_size[0] / image_size[1], abs=1e-5)
    assert photo.width == pytest.approx(min(useful_width, useful_height * image_size[0] / image_size[1]), abs=3)
    assert 2 * photo.left + photo.width == pytest.approx(deck.slide_width, abs=3)
    assert 2 * photo.top + photo.height == pytest.approx(content_top + content_bottom, abs=3)


@pytest.mark.parametrize("body", ["", "Texto de apoio"])
def test_bold_text_image_reports_title_that_exceeds_two_lines(tmp_path, body):
    heading = " ".join(["Organização da oficina"] * 15)
    Image.new("RGB", (160, 90)).save(tmp_path / "diagrama.png")
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": heading, "texto": body,
        "imagem": "diagrama.png", "imagem_modo": "conter",
    }])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Texto provavelmente estourado" in result.stdout
    slide = Presentation(out).slides[0]
    assert any(shape.has_text_frame and shape.text == heading for shape in slide.shapes)


@pytest.mark.parametrize("heading,lines", [
    ("Revisão em dupla", 1),
    ("Preparação da leitura para a revisão em dupla", 2),
])
def test_bold_steps_with_panel_start_below_title(tmp_path, heading, lines):
    path = write_script(tmp_path, [{
        "tipo": "passo_a_passo", "titulo": heading, "prompt_imagem": "Material de leitura",
        "passos": [{"titulo": "Leia", "texto": "Confira o material."},
                   {"titulo": "Compare", "texto": "Converse em dupla."},
                   {"titulo": "Anote", "texto": "Registre as dúvidas."},
                   {"titulo": "Revise", "texto": "Confira as anotações."},
                   {"titulo": "Envie", "texto": "Compartilhe o resumo."}],
    }], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    slide = Presentation(out).slides[0]
    boxes = {shape.text: shape for shape in slide.shapes if shape.has_text_frame}
    title = boxes[heading]
    first = boxes["Leia\nConfira o material."]
    last = boxes["Envie\nCompartilhe o resumo."]
    assert first.top >= title.top + title.height
    if lines == 1:
        assert first.top == Inches(1.38)
    else:
        assert title.height >= Inches(0.9)
        assert first.top > Inches(1.38)
        photo = next(shape for shape in slide.shapes if shape.name == "!!foto")
        assert photo.top >= title.top + title.height
    assert last.top + last.height <= Inches(4.78)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("panel", [False, True])
def test_bold_steps_keep_even_visible_gaps(tmp_path, monkeypatch, panel):
    monkeypatch.syspath_prepend(str(SKILL / "scripts"))
    from conferir import Theme, check_text

    texts = ["Leia o material.", "Compare as notas.", "Confira os rótulos e as legendas."]
    if panel:
        texts += ["Organize o material da oficina e compartilhe as anotações com a turma.",
                  "Prepare um resumo da oficina e envie junto com as observações de cada etapa."]
    else:
        texts[2] = "Confira os rótulos e as legendas antes de compartilhar as anotações com o grupo."
        texts += ["Organize o material da oficina e compartilhe as anotações com a turma "
                  "antes de preparar as próximas atividades em dupla.",
                  "Prepare um resumo dos assuntos da oficina e envie junto com as anotações "
                  "e as observações feitas ao longo de cada etapa."]
    fields = {"prompt_imagem": "Material de leitura"} if panel else {}
    path = write_script(tmp_path, [{
        "tipo": "passo_a_passo", "titulo": "Roteiro",
        "passos": [{"texto": value} for value in texts], **fields,
    }], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr

    deck = Presentation(out)
    slide = deck.slides[0]
    boxes = {shape.text.strip(): shape for shape in slide.shapes if shape.has_text_frame}
    theme = Theme(slide, deck)
    text_rows = []
    for value in texts:
        box = boxes[value]
        frame = box.text_frame
        margins = frame.margin_left, frame.margin_right, frame.margin_top, frame.margin_bottom
        _, rows = check_text(frame, box, theme, set(), lambda *args: None,
                             box.width, box.height, margins, box.top, deck.slide_height)
        text_rows.append(rows)
    assert [len(rows) for rows in text_rows] == [1, 1, 1, 2, 2]
    gaps = [second[0][1] - first[-1][3] for first, second in zip(text_rows, text_rows[1:])]
    assert min(gaps) > 0
    assert max(gaps) - min(gaps) <= Inches(0.02), [gap / Inches(1) for gap in gaps]

    dots = [shape for shape in slide.shapes if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
            and shape.auto_shape_type == MSO_SHAPE.OVAL]
    assert len(dots) == len(texts)
    for dot, value in zip(dots, texts):
        assert dot.top - boxes[value].top == pytest.approx(Inches(0.03), abs=1)
    track = next(shape for shape in slide.shapes if shape.shape_type == MSO_SHAPE_TYPE.LINE)
    assert track.top == pytest.approx(dots[0].top + dots[0].height / 2, abs=1)
    assert track.top + track.height == pytest.approx(dots[-1].top + dots[-1].height / 2, abs=1)


@pytest.mark.parametrize("mode", [None, "sangrar", "conter", "esticar"])
def test_bold_comparison_image_mode(tmp_path, mode):
    Image.new("RGB", (100, 200)).save(tmp_path / "diagrama.png")
    fields = {"imagem_modo": mode} if mode is not None else {}
    path = write_script(tmp_path, [{
        "tipo": "comparativo", "titulo": "Dois formatos", "imagem": "diagrama.png", **fields,
    }], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    if mode == "esticar":
        assert result.returncode == 2
        assert "imagem_modo de comparativo" in result.stderr
        return

    assert result.returncode == 0, result.stdout + result.stderr
    deck = Presentation(out)
    photo = next(shape for shape in deck.slides[0].shapes if shape.name == "!!foto")
    if mode == "conter":
        assert (photo.crop_left, photo.crop_right, photo.crop_top, photo.crop_bottom) == (0, 0, 0, 0)
        assert photo.width / photo.height == pytest.approx(0.5)
        assert photo.height == Inches(2.7)
        assert 2 * photo.left + photo.width == pytest.approx(deck.slide_width, abs=2)
    else:
        assert photo.crop_top > 0 and photo.crop_bottom > 0
        assert photo.left == 0
        assert photo.width == deck.slide_width
    assert photo.top == 0


@pytest.mark.parametrize("kind,image_size", [
    ("comparativo", (500, 100)),
    ("comparativo", (900, 100)),
    ("comparativo", None),
    ("texto_imagem", (500, 100)),
])
def test_bold_contained_image_clears_logo(tmp_path, kind, image_size):
    if image_size:
        Image.new("RGB", image_size, "white").save(tmp_path / "diagrama.png")
        panel = {"imagem": "diagrama.png"}
    else:
        panel = {"prompt_imagem": "Material de leitura"}
    path = write_script(tmp_path, [{
        "tipo": kind, "titulo": "Diagrama", "imagem_modo": "conter", **panel,
    }])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr

    shapes = Presentation(out).slides[0].shapes
    photo = next(shape for shape in shapes if shape.name == "!!foto")
    logo = next(shape for shape in shapes if shape.name == "!!logo")
    margin = Inches(0.1)
    assert photo.top >= logo.top + logo.height + margin or photo.left + photo.width <= logo.left - margin
    if image_size:
        assert photo.width / photo.height == pytest.approx(image_size[0] / image_size[1], abs=1e-5)


def test_bold_comparison_columns_make_room_for_wrapped_items(tmp_path):
    first_items = [
        "Confira **o título e a ordem dos tópicos** antes da discussão em dupla.",
        "Confira **os rótulos e as legendas** antes de compartilhar com o grupo.",
    ]
    next_items = ["Compare as anotações.", "Abra a prévia."]
    path = write_script(tmp_path, [{
        "tipo": "comparativo", "titulo": "Dois formatos", "prompt_imagem": "Material de leitura",
        "colunas": [{"itens": [first, second]} for first, second in zip(first_items, next_items)],
        "nota": "Abra a prévia antes de compartilhar.",
    }], avulso=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    slide = Presentation(out).slides[0]
    boxes = {shape.text: shape for shape in slide.shapes if shape.has_text_frame}
    for first_text, next_text in zip(first_items, next_items):
        first = boxes[first_text.replace("**", "")]
        second = boxes[next_text]
        assert first.height > Inches(0.3)
        assert first.top + first.height <= second.top
    assert result.returncode == 0, result.stdout + result.stderr


def test_bold_animates_standard_layouts(tmp_path):
    example = json.loads((SKILL / "references" / "exemplo_roteiro.json").read_text(encoding="utf-8"))
    fallback = {"tabela", "grafico", "antes_depois", "artigo", "caso_clinico", "referencias"}
    slides = [
        {"tipo": "capa", "titulo": "Oficina"},
        {"tipo": "sumario", "itens": ["Exemplos"]},
        {"tipo": "modulo", "titulo": "Exemplos"},
        *(slide for slide in example["slides"] if slide["tipo"] in fallback),
        {"tipo": "encerramento"},
    ]
    path = write_script(tmp_path, slides, avulso=False)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr
    generated = Presentation(out).slides
    assert len(generated) == len(fallback) + 9
    for slide in generated:
        assert_motion(slide)


@pytest.mark.parametrize("kind, content", [
    ("antes_depois", "ANTES"),
    ("tabela", MSO_SHAPE_TYPE.TABLE),
    ("grafico", MSO_SHAPE_TYPE.CHART),
    ("artigo", "CONCLUSÃO"),
    ("caso_clinico", "AVALIAÇÃO"),
    ("referencias", "1."),
])
@pytest.mark.parametrize("separator", ["", "\n"])
def test_bold_fallback_uses_model_content_frame(tmp_path, kind, content, separator):
    reference = json.loads(FIXTURE.read_text(encoding="utf-8"))[7]
    kicker, first_run, accent = (run["text"] for run in reference["runs"][:3])
    example = json.loads((SKILL / "references" / "exemplo_roteiro.json").read_text(encoding="utf-8"))
    data = next(slide for slide in example["slides"] if slide["tipo"] == kind)
    data.update(titulo=f"{first_run}{separator}**{accent}**", kicker=kicker.lower())
    if kind == "antes_depois":
        Image.new("RGB", (64, 48), "blue").save(tmp_path / "sintetica.png")
        data.update(antes="sintetica.png", depois="sintetica.png",
                    rotulo_antes="Antes", rotulo_depois="Depois")
    out = tmp_path / "fallback.pptx"

    result = generate(write_script(tmp_path, [data]), out)
    assert result.returncode == 0, result.stderr
    slide = Presentation(out).slides[0]
    actual = fingerprint(slide)
    frame = {name: box for name, box in reference["shapes"].items() if name != "!!foto"}
    assert actual["background"] == reference["background"]
    assert actual["shapes"] == {name: pytest.approx(box, abs=0.02) for name, box in frame.items()}
    assert actual["runs"][:3] == reference["runs"][:3]

    label, heading = slide.shapes[3], slide.shapes[4]
    assert label.text == kicker
    assert (label.left.inches, label.top.inches) == pytest.approx((0.45, 0.42), abs=0.02)
    assert heading.text == f"{first_run}{separator}{accent}"
    assert (heading.left.inches, heading.top.inches, heading.width.inches) == pytest.approx(
        (0.45, 0.62, 6.0), abs=0.02)
    assert (heading.height.inches > 0.6) == bool(separator)
    body = list(slide.shapes)[5:]
    content_top = 1.35 + max(0, heading.height.inches - 0.6)
    assert all(content_top - 0.02 <= shape.top.inches for shape in body)
    assert all(shape.top + shape.height <= Inches(5.375) for shape in body)
    assert all(shape.left.inches >= 0.43 and (shape.left + shape.width) <= Inches(9.57)
               for shape in body)
    if isinstance(content, str):
        assert any(shape.has_text_frame and shape.text == content for shape in body)
    else:
        assert any(shape.shape_type == content for shape in body)
    if kind == "antes_depois":
        assert sum(shape.shape_type == MSO_SHAPE_TYPE.PICTURE for shape in body) == 2
        assert any(shape.has_text_frame and shape.text == "DEPOIS" for shape in body)
    assert_motion(slide)


def test_switching_to_bold_keeps_shared_content_fields(tmp_path):
    path = write_script(tmp_path, [
        {"tipo": "modulo", "titulo": "Módulo", "selo": "Material de apoio"},
        {"tipo": "anatomia", "titulo": "Estruturas", "marcacoes": [{"nome": "A", "desc": "Descrição A"}],
         "prompt_imagem": "Cena de teste"},
        {"tipo": "alerta", "titulo": "Alerta", "sinais": ["Sinal A"], "conduta": ["Conduta A"],
         "urgente": "Aviso A"},
        {"tipo": "encerramento", "titulo": "Fim", "contatos": ["Site A"]},
        {"tipo": "comparativo", "titulo": "Comparativo", "prompt_imagem": "Cena de teste"},
        {"tipo": "duas_colunas", "titulo": "Duas colunas"},
    ])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stderr
    for slide, expected in zip(Presentation(out).slides, [
        ["Material de apoio"], ["Descrição A"], ["Sinal A", "Conduta A", "Aviso A"],
        ["Site A"], ["Comparativo"], ["Duas colunas"],
    ], strict=True):
        slide_text = "\n".join(fingerprint(slide)["texts"])
        assert all(value in slide_text for value in expected)
        assert_motion(slide)


@pytest.mark.parametrize("style,valid", [("padrao", "tabela"), ("ousado", "numeros")])
def test_unknown_type_lists_style_layouts(tmp_path, style, valid):
    path = write_script(tmp_path, [{"tipo": "inexistente"}], estilo=style)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode != 0
    assert "tipo desconhecido: inexistente" in result.stderr
    assert "Disponíveis:" in result.stderr
    assert valid in result.stderr.split("Disponíveis: ")[1].strip().split(", ")
    assert not out.exists()


def test_default_and_explicit_standard_style_match_legacy(tmp_path):
    legacy = tmp_path / "legacy.pptx"
    example = SKILL / "references" / "exemplo_roteiro.json"
    subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "clinic_deck.py"), str(example), str(legacy)],
        check=True, capture_output=True,
    )
    spec = json.loads(example.read_text(encoding="utf-8"))
    explicit = tmp_path / "roteiro.json"
    explicit.write_text(json.dumps({**spec, "estilo": "padrao"}), encoding="utf-8")
    for path in (example, explicit):
        out = tmp_path / "aula.pptx"
        result = generate(path, out)
        assert result.returncode == 0, result.stderr
        with ZipFile(legacy) as expected, ZipFile(out) as actual:
            slide_parts = {name for name in expected.namelist() if name.startswith("ppt/slides/")}
            assert slide_parts == {name for name in actual.namelist() if name.startswith("ppt/slides/")}
            assert all(expected.read(name) == actual.read(name) for name in slide_parts)


if __name__ == "__main__":
    print(json.dumps([fingerprint(slide) for slide in Presentation(sys.argv[1]).slides],
                     ensure_ascii=False, indent=2))
