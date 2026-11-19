import json
from pathlib import Path

import pytest
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4

from lib.pdfcheck import checks
from lib.pdfcheck.rules import load_rules


def test_low_ppi_new_image_is_error(open_pdf, placed_image_pdf, test_rules):
    pdf = open_pdf(placed_image_pdf(144, 144, pixels=(600, 200)))
    findings = checks.check_images(pdf, test_rules)
    resolution = [f for f in findings if f.kind == "image-low-resolution"]
    assert [(f.page, f.severity) for f in resolution] == [(1, "error")]
    assert "100" in resolution[0].detail


def test_rotated_90_low_ppi_is_error(open_pdf, placed_image_pdf, test_rules):
    pdf = open_pdf(placed_image_pdf(144, 72, rotation=90, pixels=(240, 120)))
    finding, = checks.check_images(pdf, test_rules)
    assert (finding.page, finding.kind, finding.severity) == (1, "image-low-resolution", "error")
    # The axis-aligned box swaps the dimensions and would report 60 ppi.
    assert "120.0 ppi" in finding.detail


def test_low_ppi_inherited_image_is_warning(open_pdf, placed_image_pdf, test_rules):
    pdf = open_pdf(placed_image_pdf(144, 72, pixels=(100, 50)))
    findings = checks.check_images(pdf, test_rules, origins={(100, 50): 50.0})  # no tamanho do original
    assert [(f.kind, f.severity) for f in findings] == [("image-low-resolution", "warning")]


def test_inherited_without_origin_follows_new_image_rule(open_pdf, placed_image_pdf, test_rules):
    pdf = open_pdf(placed_image_pdf(144, 72, pixels=(100, 50)))  # 50 ppi
    assert [f.severity for f in checks.check_images(pdf, test_rules)] == ["error"]
    findings = checks.check_images(pdf, test_rules, origins={(100, 50): 100.0})  # ampliada
    assert [f.severity for f in findings] == ["error"]


@pytest.mark.parametrize("pixels, severity", [((300, 150), "warning"), ((600, 300), None)])
def test_image_resolution_thresholds(open_pdf, placed_image_pdf, test_rules, pixels, severity):
    pdf = open_pdf(placed_image_pdf(144, 72, pixels=pixels))
    findings = checks.check_images(pdf, test_rules)
    assert [f.severity for f in findings] == ([severity] if severity else [])


def test_distorted_image_detected(open_pdf, placed_image_pdf, test_rules):
    pdf = open_pdf(placed_image_pdf(144, 75, rotation=30, pixels=(800, 400)))
    assert [(f.page, f.kind, f.severity) for f in checks.check_images(pdf, test_rules)] == [
        (1, "image-distorted", "error")
    ]


@pytest.mark.parametrize("rotation", [30, 90])
def test_rotated_image_not_distorted(open_pdf, placed_image_pdf, test_rules, rotation):
    pdf = open_pdf(placed_image_pdf(144, 72, rotation=rotation, pixels=(800, 400)))
    assert checks.check_images(pdf, test_rules) == []


def test_clipped_image_uses_full_placement(open_pdf, placed_image_pdf, test_rules):
    pdf = open_pdf(placed_image_pdf(144, 72, clip=True, pixels=(200, 100)))
    assert [f.kind for f in checks.check_images(pdf, test_rules)] == ["image-low-resolution"]


def _with_footer(number):
    def draw(document):
        document.drawString(60, 500, "2026")
        if number is not None:
            document.drawRightString(A4[0] - 60, 30, str(number))

    return draw


def test_page_number_gap_detected(open_pdf, layout_pdf, test_rules):
    pdf = open_pdf(layout_pdf(*map(_with_footer, (1, 2, 4, 5, None, 7))))
    assert [(f.page, f.kind) for f in checks.check_page_numbers(pdf, test_rules)] == [
        (3, "page-number"),
        (5, "page-number"),
    ]


def test_toc_mismatch_detected(open_pdf, layout_pdf, test_rules):
    def toc(document):
        document.drawString(60, 740, "Sumário")
        document.drawString(60, 710, "Introdução ........ 11")
        document.drawString(60, 690, "Análise 11")
        document.drawString(60, 670, "Seção ausente ........ 12")
        _with_footer(10)(document)

    def introduction(document):
        document.drawString(60, 720, "Introdução")
        _with_footer(11)(document)

    def analysis(document):
        document.drawString(60, 720, "Análise")
        _with_footer(12)(document)

    pdf = open_pdf(layout_pdf(toc, introduction, analysis))
    findings = checks.check_toc(pdf, test_rules)
    assert [(f.page, f.kind) for f in findings] == [(1, "toc-mismatch")] * 2
    assert "Análise" in findings[0].detail and "12" in findings[0].detail
    assert "Seção ausente" in findings[1].detail


def test_toc_continues_without_heading_or_dot_leaders(open_pdf, layout_pdf, test_rules):
    def toc(document):
        document.drawString(60, 740, "Sumário")
        document.drawString(60, 710, "Introdução 3")

    def continued_toc(document):
        document.drawString(60, 710, "Conclusão 3")

    def introduction(document):
        document.drawString(60, 710, "Introdução")

    def conclusion(document):
        document.drawString(60, 710, "Conclusão")

    pdf = open_pdf(layout_pdf(toc, continued_toc, introduction, conclusion))
    findings = checks.check_toc(pdf, test_rules)
    assert [(f.page, f.kind) for f in findings] == [(2, "toc-mismatch")]


def test_free_space_listed_with_fraction(open_pdf, layout_pdf, test_rules):
    def draw(document):
        document.drawString(60, 740, "Parágrafo curto.")
        document.line(60, 400, 150, 400)
        document.drawString(60, 15, "1")

    pdf = open_pdf(layout_pdf(draw))
    page = pdf.pages[0]
    margin = test_rules.safe_zone_mm * 72 / 25.4
    top_margin = test_rules.page_margins_mm["top"] * 72 / 25.4
    bottom_margin = test_rules.page_margins_mm["bottom"] * 72 / 25.4
    candidate, = checks.free_space(pdf, test_rules)
    assert candidate.page == 1
    assert candidate.x0 == pytest.approx(margin)
    assert candidate.x1 == pytest.approx(page.width - margin)
    assert candidate.top == pytest.approx(page.height - 400)
    assert candidate.bottom == pytest.approx(page.height - bottom_margin)
    assert candidate.fraction == pytest.approx(
        (400 - bottom_margin) / (page.height - top_margin - bottom_margin)
    )


def test_free_space_ignores_running_footer(open_pdf, layout_pdf, test_rules):
    def draw(document):
        document.drawString(60, 740, "Parágrafo curto.")
        document.drawString(60, 500, "Meio da página.")
        document.drawRightString(A4[0] - 60, 13 * 72 / 25.4, "7")  # número a 13 mm da borda

    pdf = open_pdf(layout_pdf(draw))
    page = pdf.pages[0]
    top_margin = test_rules.page_margins_mm["top"] * 72 / 25.4
    bottom_margin = test_rules.page_margins_mm["bottom"] * 72 / 25.4
    candidate, = checks.free_space(pdf, test_rules)
    assert candidate.top == pytest.approx(page.height - 500 + 3, abs=12)
    assert candidate.bottom == pytest.approx(page.height - bottom_margin)
    assert candidate.fraction == pytest.approx(
        (candidate.bottom - candidate.top) / (page.height - top_margin - bottom_margin)
    )


def test_content_text_in_footer_band_counts_as_object(open_pdf, layout_pdf, test_rules):
    def page(caption):
        def draw(document):
            document.drawString(60, 740, "Parágrafo curto.")
            document.drawString(60, 15, caption)

        return draw

    pdf = open_pdf(layout_pdf(page("Legenda um."), page("Legenda dois."), page("Legenda três.")))
    assert checks.free_space(pdf, test_rules) == []
    assert checks.free_space(open_pdf(layout_pdf(page("Legenda um."))), test_rules) == []


def test_repeated_header_and_number_ignored(open_pdf, layout_pdf, test_rules):
    def page(number):
        def draw(document):
            document.drawString(60, 740, "Parágrafo curto.")
            document.drawString(60, 815, "CLINIC EDITORA")
            document.drawRightString(A4[0] - 60, 13 * 72 / 25.4, str(number))

        return draw

    candidates = checks.free_space(open_pdf(layout_pdf(page(1), page(2))), test_rules)
    assert [c.page for c in candidates] == [1, 2]


def _band_page(number, footer_y=30, footer="TÍTULO DO LIVRO"):
    def draw(document):
        document.drawString(60, 740, "Parágrafo curto.")
        document.drawString(60, footer_y, footer)
        document.drawRightString(A4[0] - 60, 13 * 72 / 25.4, str(number))

    return draw


def test_number_not_matching_page_sequence_counts(open_pdf, layout_pdf, test_rules):
    def stray(document):
        document.drawString(60, 740, "Parágrafo curto.")
        document.drawString(60, 15, "99")  # fora da sequência das páginas

    pdf = open_pdf(layout_pdf(_band_page(1), _band_page(2), stray))
    assert [c.page for c in checks.free_space(pdf, test_rules)] == [1, 2]


def test_repeated_text_at_different_heights_counts(open_pdf, layout_pdf, test_rules):
    pdf = open_pdf(layout_pdf(*(_band_page(n, footer_y=15 + 3 * n) for n in (1, 2, 3, 4))))
    assert checks.free_space(pdf, test_rules) == []


def test_repeated_text_needs_three_pages(open_pdf, layout_pdf, test_rules):
    pdf = open_pdf(layout_pdf(_band_page(1), _band_page(2)))
    assert checks.free_space(pdf, test_rules) == []


def test_repeated_text_at_same_height_is_ignored(open_pdf, layout_pdf, test_rules):
    pdf = open_pdf(layout_pdf(*map(_band_page, (1, 2, 3))))
    assert [c.page for c in checks.free_space(pdf, test_rules)] == [1, 2, 3]


def test_image_in_footer_band_counts_as_object(open_pdf, layout_pdf, test_rules):
    def draw(document):
        document.drawString(60, 740, "Parágrafo curto.")
        image = ImageReader(Image.new("RGB", (600, 300), "#800020"))
        document.drawImage(image, 60, 5, 40, 20)  # imagem na faixa do rodapé

    assert checks.free_space(open_pdf(layout_pdf(draw)), test_rules) == []


def test_free_space_begins_below_image(open_pdf, placed_image_pdf, test_rules):
    pdf = open_pdf(placed_image_pdf(144, 72))
    candidate, = checks.free_space(pdf, test_rules)
    assert candidate.top == pytest.approx(pdf.pages[0].height - 350)


def test_blank_page_not_candidate(open_pdf, layout_pdf, test_rules):
    pdf = open_pdf(layout_pdf(lambda document: None))
    assert len(pdf.pages) == 1
    assert checks.free_space(pdf, test_rules) == []


def test_chapter_opening_not_candidate(open_pdf, layout_pdf, test_rules):
    def draw(document):
        document.setFont("Helvetica-Bold", 32)
        document.drawString(42, 690, "Capítulo 1. Introdução ao estudo")
        document.setFont("Helvetica", 11)
        document.drawString(42, 630, "Texto de abertura.")

    pdf = open_pdf(layout_pdf(draw))
    assert checks.free_space(pdf, test_rules) == []


@pytest.mark.parametrize("threshold, value", [
    ("chapter_title_min_pt", 40),
    ("chapter_title_min_width_fraction", 0.95),
])
def test_chapter_opening_thresholds_from_rules(open_pdf, layout_pdf, tmp_path, threshold, value):
    def draw(document):
        document.setFont("Helvetica-Bold", 32)
        document.drawString(42, 690, "Capítulo 1. Introdução ao estudo")

    pdf = open_pdf(layout_pdf(draw))
    assert checks.free_space(pdf, load_rules()) == []

    source = Path(__file__).resolve().parents[1] / "shared" / "rules" / "graphic-rules.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    del data["chapter_title_min_pt"]
    del data["chapter_title_min_width_fraction"]
    custom = tmp_path / "graphic-rules.json"
    custom.write_text(json.dumps(data), encoding="utf-8")
    assert checks.free_space(pdf, load_rules(str(custom))) == []

    data[threshold] = value
    custom.write_text(json.dumps(data), encoding="utf-8")

    candidate, = checks.free_space(pdf, load_rules(str(custom)))
    assert candidate.page == 1


def test_front_matter_without_folio_is_not_an_error(open_pdf, layout_pdf, test_rules):
    # A capa e as páginas iniciais não têm fólio no modelo; só falta ou salto depois do primeiro fólio conta.
    pdf = open_pdf(layout_pdf(*map(_with_footer, (None, None, 3, 4, None, 6))))
    assert [(f.page, f.kind) for f in checks.check_page_numbers(pdf, test_rules)] == [(5, "page-number")]


def test_book_without_any_folio_is_flagged(open_pdf, layout_pdf, test_rules):
    pdf = open_pdf(layout_pdf(*map(_with_footer, (None, None, None))))
    findings = checks.check_page_numbers(pdf, test_rules)
    assert [(f.page, f.kind, f.severity) for f in findings] == [(1, "page-number", "error")]
    assert "nenhuma página numerada" in findings[0].detail
    short = open_pdf(layout_pdf(*map(_with_footer, (None, None))))  # só capa e uma página: abaixo do mínimo
    assert checks.check_page_numbers(short, test_rules) == []


def test_front_matter_exemption_is_limited(open_pdf, layout_pdf, test_rules):
    assert test_rules.front_matter_max_pages == 8
    numbers = (None,) * 9 + (10,)  # o primeiro fólio só aparece na 10ª página
    pdf = open_pdf(layout_pdf(*map(_with_footer, numbers)))
    assert [(f.page, f.kind) for f in checks.check_page_numbers(pdf, test_rules)] == [(9, "page-number")]
