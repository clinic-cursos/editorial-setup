"""Para regerar a impressão digital a partir do modelo original:

uv run --locked python tests/test_aulas_ousado.py /var/tmp/aulas-render/in/modelo.pptx > tests/fixtures/aulas/modelo-v1.json
"""

from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys
from textwrap import wrap
from zipfile import ZipFile

from PIL import Image
from pptx import Presentation
from pptx.enum.dml import MSO_COLOR_TYPE
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from pptx.util import Inches
import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "aulas"
FIXTURE = Path(__file__).parent / "fixtures" / "aulas" / "modelo-v1.json"
MODEL = SKILL / "references" / "modelo_hof_roteiro.json"
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
    spec = {"estilo": "ousado", "parcerias": False, "precificacao": False, "slides": slides, **fields}
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def assert_motion(slide):
    assert next(slide._element.iter(MORPH)).get("option") == "byObject"
    timing = slide._element.find(qn("p:timing"))
    assert timing is not None
    targets = {int(target.get("spid")) for target in timing.iter(qn("p:spTgt"))}
    assert targets and targets <= {shape.shape_id for shape in slide.shapes}


def test_model_matches_reference(tmp_path):
    out = tmp_path / "modelo.pptx"
    result = generate(MODEL, out)
    assert result.returncode == 0, result.stderr
    reference = json.loads(FIXTURE.read_text(encoding="utf-8"))
    slides = Presentation(out).slides
    assert len(slides) == len(reference) == 16
    style_mismatches = []
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


@pytest.mark.parametrize("slide,model_size", [
    ({"tipo": "numero"}, 130),
    ({"tipo": "anatomia"}, 40),
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


@pytest.mark.parametrize("heading", [
    "Envelhecimento",
    "TECNOLOGIA DE FABRICAÇÃO DOS NEUROMODULADORES",
])
def test_bold_text_image_title_fits_without_splitting_words(tmp_path, heading):
    path = write_script(tmp_path, [{"tipo": "texto_imagem", "titulo": heading, "texto": "Corpo do slide"}])
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
    path = write_script(tmp_path, [{"tipo": "texto_imagem", "titulo": "Título", "texto": content}])
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


@pytest.mark.parametrize("image_size", [(400, 100), (100, 400)])
def test_bold_text_image_contains_picture_inside_panel(tmp_path, image_size):
    Image.new("RGB", image_size).save(tmp_path / "diagrama.png")
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": "Diagrama", "imagem": "diagrama.png", "imagem_modo": "conter",
    }])
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stdout + result.stderr
    deck = Presentation(out)
    photo = next(shape for shape in deck.slides[0].shapes if shape.name == "!!foto")
    assert photo.shape_type == MSO_SHAPE_TYPE.PICTURE
    assert photo.width / photo.height == pytest.approx(image_size[0] / image_size[1], abs=1e-5)
    assert (photo.crop_left, photo.crop_right, photo.crop_top, photo.crop_bottom) == (0, 0, 0, 0)
    panel_left = deck.slide_width - Inches(3)
    assert panel_left <= photo.left <= photo.left + photo.width <= deck.slide_width
    assert 0 <= photo.top <= photo.top + photo.height <= deck.slide_height
    assert 2 * photo.left + photo.width == pytest.approx(panel_left + deck.slide_width, abs=2)
    assert 2 * photo.top + photo.height == pytest.approx(deck.slide_height, abs=2)


def test_bold_animates_standard_layouts(tmp_path):
    example = json.loads((SKILL / "references" / "exemplo_roteiro.json").read_text(encoding="utf-8"))
    fallback = {"tabela", "grafico", "antes_depois", "artigo", "caso_clinico", "referencias"}
    slides = [slide for slide in example["slides"] if slide["tipo"] in fallback]
    path = write_script(tmp_path, slides, parcerias=True, precificacao=True)
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stderr
    generated = Presentation(out).slides
    assert len(generated) == len(fallback) + 5
    for slide in generated:
        assert_motion(slide)


def test_switching_to_bold_keeps_shared_content_fields(tmp_path):
    path = write_script(tmp_path, [
        {"tipo": "modulo", "titulo": "Módulo", "selo": "Material de apoio"},
        {"tipo": "anatomia", "titulo": "Estruturas", "marcacoes": [{"nome": "A", "desc": "Descrição A"}]},
        {"tipo": "alerta", "titulo": "Alerta", "sinais": ["Sinal A"], "conduta": ["Conduta A"],
         "urgente": "Aviso A"},
        {"tipo": "encerramento", "titulo": "Fim", "contatos": ["Site A"]},
        {"tipo": "comparativo", "titulo": "Comparativo"},
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
