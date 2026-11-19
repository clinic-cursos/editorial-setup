import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from tests.test_extract_pdf import extract, text


@pytest.fixture
def outline_pdf(tmp_path):
    def make(outline):
        path = tmp_path / "outline.pdf"
        pdf = canvas.Canvas(str(path), pagesize=A4)
        pdf.bookmarkPage("first")
        if outline:
            pdf.bookmarkPage("section")
            pdf.bookmarkPage("detail")
            pdf.addOutlineEntry("  primeiro CAPÍTULO em duas linhas  ", "first", level=0)
            pdf.addOutlineEntry("Seção do primeiro", "section", level=1)
            pdf.addOutlineEntry("Detalhe da seção", "detail", level=2)
            pdf.addOutlineEntry(
                "Segundo capítulo" if outline == "valid" else "Destino na página errada",
                "second", level=0,
            )
        text(pdf, 750, "Primeiro capítulo", 24)
        text(pdf, 720, "em duas linhas", 24)
        text(pdf, 683, "Seção do primeiro", 22)
        text(pdf, 625, "Detalhe da seção", 20)
        text(pdf, 575, "Destino na página errada", 20)
        text(pdf, 530, "Este parágrafo define o tamanho de corpo do PDF usado pelo teste.")
        pdf.showPage()
        pdf.bookmarkPage("second")
        text(pdf, 750, "Segundo capítulo", 24)
        text(pdf, 720, "Título interno sem entrada", 22)
        text(pdf, 665, "Seção do primeiro", 20)
        text(pdf, 610, "O mesmo título aparece em outra página sem o destino correspondente.")
        pdf.save()
        return path

    return make


def test_outline_levels_follow_destination_page_and_title(outline_pdf, tmp_path):
    out, _, _ = extract(outline_pdf("valid"), tmp_path)
    headings = [line for line in out.read_text(encoding="utf-8").splitlines() if line.startswith("#")]
    assert headings == [
        "# Primeiro capítulo em duas linhas",
        "## Seção do primeiro",
        "### Detalhe da seção",
        "## Destino na página errada",
        "# Segundo capítulo",
        "## Título interno sem entrada",
        "## Seção do primeiro",
    ]


def test_outline_with_unmatched_chapter_preserves_font_heuristic(outline_pdf, tmp_path):
    baseline, _, _ = extract(outline_pdf(None), tmp_path)
    expected = baseline.read_text(encoding="utf-8")
    out, _, _ = extract(outline_pdf("unreliable"), tmp_path)
    assert out.read_text(encoding="utf-8") == expected
