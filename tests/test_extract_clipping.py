from pathlib import Path
import sys

from PIL import Image
import pytest
from reportlab.lib.utils import ImageReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"))

from extract_pdf import render  # noqa: E402
from text_fidelity import fidelity  # noqa: E402


@pytest.fixture(params=["W", "W*", "Form"])
def clipped_pdf(request, layout_pdf):
    def draw(c):
        image = ImageReader(Image.new("RGB", (10, 10), "blue"))
        c.setFont("Helvetica", 12)
        c.drawString(60, 730, "Restaurado")
        c.saveState()
        c.translate(60, 450)
        if request.param == "Form":
            c.beginForm("panel", 25, 100, 170, 250)
        else:
            path = c.beginPath()
            path.rect(25, 100, 145, 150)
            c.clipPath(path, stroke=0, fillMode=int(request.param == "W"))
            # The path remains in place when the drawing matrix changes.
            c.translate(10, 0)
        c.setFont("Helvetica", 12)
        c.drawString(50, 225, "Visivel")
        c.drawString(50, 70, "Oculto")
        c.drawString(50, 98, "Parcial")
        c.drawImage(image, 50, 125, 10, 10)
        c.drawImage(image, 50, 75, 10, 10)
        c.drawImage(image, 50, 95, 10, 10)
        if request.param == "Form":
            c.endForm()
            c.doForm("panel")
        c.restoreState()
        c.drawString(290, 500, "Fora do painel")

    return layout_pdf(draw)


def test_extraction_retains_only_visible_placements(clipped_pdf, tmp_path):
    markdown, files, warnings = render(clipped_pdf, tmp_path / "out.md", tmp_path / "images")

    assert "Oculto" not in markdown
    assert all(word in markdown for word in ("Restaurado", "Visivel", "Parcial", "Fora do painel"))
    assert markdown.count("{#fig-") == 2
    assert sum(path.suffix == ".png" for path, _ in files) == 1
    assert any("página 1" in warning and "recorte" in warning for warning in warnings)


def test_fidelity_excludes_hidden_text_but_detects_visible_loss(clipped_pdf, tmp_path):
    markdown = tmp_path / "expected.md"
    metadata = "title: T\ncourse: C\nauthors: A\nversion: 1\n\n"
    visible = "Restaurado\n\nVisivel\n\nParcial\n\nFora do painel\n"
    markdown.write_text(metadata + visible, encoding="utf-8")
    assert fidelity(str(clipped_pdf), str(markdown)) == (1.0, 1.0)

    markdown.write_text(metadata + visible.replace("Parcial\n\n", ""), encoding="utf-8")
    kept, added = fidelity(str(clipped_pdf), str(markdown))
    assert kept < 0.995 and added == 1.0


def test_intersecting_bounds_keep_ambiguous_even_odd_clip(layout_pdf, tmp_path):
    def draw(c):
        c.setFont("Helvetica", 12)
        mask = c.beginPath()
        mask.rect(30, 400, 300, 200)
        mask.rect(50, 470, 150, 60)
        c.clipPath(mask, stroke=0, fillMode=0)
        c.drawString(70, 550, "Visivel")
        c.drawString(70, 500, "No interior do furo")
        c.drawString(70, 350, "Fora do recorte")

    markdown, _, warnings = render(layout_pdf(draw), tmp_path / "out.md", tmp_path / "images")
    assert "Visivel" in markdown
    assert "No interior do furo" in markdown
    assert "Fora do recorte" not in markdown
    assert any("página 1" in warning and "recorte" in warning for warning in warnings)
