from pathlib import Path
import sys

from PIL import Image
from reportlab.lib.utils import ImageReader

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

import check_layout  # noqa: E402


def page(number, *lines, image=None):
    """Página com texto, fólio no rodapé e, opcionalmente, uma imagem de (pixels)."""
    def draw(document):
        document.setFont("Helvetica", 12)
        for y, text in lines:
            document.drawString(80, y, text)
        document.drawString(300, 40, str(number))
        if image:
            document.drawImage(ImageReader(Image.new("RGB", image, "#800020")), 100, 300, 288, 144)
    return draw


def run(monkeypatch, test_rules, pdf, *args):
    monkeypatch.setattr(check_layout, "load_rules", lambda: test_rules)
    return check_layout.main([str(pdf), *args])


def test_check_layout_exit_codes(layout_pdf, tmp_path, test_rules, monkeypatch, capsys):
    clean = layout_pdf(page(1, (700, "Texto limpo.")), page(2, (700, "Outra página.")))
    assert run(monkeypatch, test_rules, clean) == 0
    assert "Erros: 0" in capsys.readouterr().out
    overlap = layout_pdf(page(1, (700, "Linha de cima do trecho"), (696, "Linha que cai por cima")))
    assert run(monkeypatch, test_rules, overlap) == 1
    assert "overlap" in capsys.readouterr().out
    assert run(monkeypatch, test_rules, tmp_path / "missing.pdf") == 2


def test_check_layout_reports_toc_and_images(layout_pdf, test_rules, monkeypatch, capsys):
    pdf = layout_pdf(
        page(1, (700, "Sumário"), (680, "Introdução ........ 7")),
        page(2, (700, "Texto."), image=(100, 50)),
    )
    assert run(monkeypatch, test_rules, pdf) == 1
    out = capsys.readouterr().out
    assert "toc-mismatch" in out and "image-low-resolution" in out


def test_check_layout_inherited_image_is_warning(layout_pdf, test_rules, monkeypatch, capsys):
    import pdfplumber

    pdf = layout_pdf(page(1, (700, "Texto."), image=(100, 50)))
    assert run(monkeypatch, test_rules, pdf) == 1
    capsys.readouterr()
    with pdfplumber.open(pdf) as opened:
        name = opened.pages[0].images[0]["name"]
    assert run(monkeypatch, test_rules, pdf, "--inherited", name) == 0
    assert "aviso | image-low-resolution" in capsys.readouterr().out
