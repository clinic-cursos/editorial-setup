"""A composição não amplia a figura abaixo da resolução do original nem do mínimo das regras."""

import json
from pathlib import Path
import sys

import pdfplumber
from PIL import Image

from lib.pdfcheck.checks import check_images
from lib.pdfcheck.rules import load_rules

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

from build_book import build  # noqa: E402

HEADER = "title: Livro de teste\ncourse: Curso de teste\nauthors: Ana Silva\nversion: 1.0\n\n# Capítulo\n\nTexto.\n\n"


def _compose(tmp_path, pixels, origin_ppi=None):
    images = tmp_path / "imagens-originais"
    images.mkdir()
    Image.new("RGB", pixels, "#800020").save(images / "fig-1.png")
    origins = {}
    if origin_ppi is not None:  # o mesmo origem.json que o extract_pdf.py grava ao lado das figuras
        (images / "origem.json").write_text(json.dumps({"fig-1.png": {"pixels": list(pixels), "ppi": origin_ppi}}))
        origins = {pixels: origin_ppi}
    source = tmp_path / "manuscrito.md"
    source.write_text(HEADER + "![](imagens-originais/fig-1.png){#fig-1}\n", encoding="utf-8")
    result = build(str(source), str(tmp_path / "out"))
    with pdfplumber.open(result.pdf) as pdf:
        return check_images(pdf, load_rules(), origins)


def test_inherited_figure_keeps_original_resolution(tmp_path):
    # 444 x 351 px a 136 ppi no original (a primeira figura do livro de Preenchedores tem esse perfil)
    findings = _compose(tmp_path, (444, 351), origin_ppi=136.0)
    errors = [f.detail for f in findings if f.severity == "error"]
    assert errors == [], errors


def test_new_figure_is_not_enlarged_below_error_ppi(tmp_path):
    findings = _compose(tmp_path, (900, 601))
    errors = [f.detail for f in findings if f.severity == "error"]
    assert errors == [], errors
    assert any(f.kind == "image-low-resolution" and f.severity == "warning" for f in findings)
