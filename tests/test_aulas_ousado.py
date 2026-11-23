"""Para regerar a impressão digital a partir do modelo original:

uv run --locked python tests/test_aulas_ousado.py /var/tmp/aulas-render/in/modelo.pptx > tests/fixtures/aulas/modelo-v1.json
"""

from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
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
    return {
        "background": str(background.fill.fore_color.rgb),
        "shapes": {
            shape.name: [round(getattr(shape, dimension).inches, 5)
                         for dimension in ("left", "top", "width", "height")]
            for shape in morph_shapes
        },
        "texts": [shape.text for shape in slide.shapes
                  if shape.has_text_frame and shape.text and shape.name not in omit_text],
    }


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
        assert_motion(slide)


def test_bold_uses_relative_image_and_slide_text(tmp_path):
    path = write_script(tmp_path, [{
        "tipo": "texto_imagem", "titulo": "Título independente", "texto": "Texto independente",
        "imagem": "foto.png", "prompt_imagem": "Cena de teste",
    }])
    (tmp_path / "foto.png").write_bytes((SKILL / "assets" / "logo_cor.png").read_bytes())
    out = tmp_path / "aula.pptx"
    result = generate(path, out)
    assert result.returncode == 0, result.stderr
    slide = Presentation(out).slides[0]
    photo = next(shape for shape in slide.shapes if shape.name == "!!foto")
    assert photo.shape_type == MSO_SHAPE_TYPE.PICTURE
    assert {"Título independente", "Texto independente"} <= set(fingerprint(slide)["texts"])
    assert not out.with_name("aula - prompts de imagem.md").exists()


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
