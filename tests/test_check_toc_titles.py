from lib.pdfcheck import checks


def test_toc_accepts_heading_wrapped_in_two_lines(open_pdf, layout_pdf, test_rules):
    def toc(document):
        document.drawString(60, 740, "Sumário")
        document.drawString(60, 710, "Fundamentos da harmonizacao facial e envelhecimento ........ 2")

    def chapter(document):
        document.setFont("Helvetica", 24)
        document.drawString(60, 720, "Fundamentos da harmonizacao")
        document.drawString(60, 690, "facial e envelhecimento")

    pdf = open_pdf(layout_pdf(toc, chapter))
    assert [f.detail for f in checks.check_toc(pdf, test_rules)] == []


def test_toc_accepts_heading_ending_in_period(open_pdf, layout_pdf, test_rules):
    def toc(document):
        document.drawString(60, 740, "Sumário")
        document.drawString(60, 710, "Conhecimento. Criterio. Pratica. ........ 2")

    def closing(document):
        document.drawString(60, 720, "Conhecimento. Criterio. Pratica.")

    pdf = open_pdf(layout_pdf(toc, closing))
    assert [f.detail for f in checks.check_toc(pdf, test_rules)] == []


def test_toc_accepts_heading_wrapped_in_three_lines(open_pdf, layout_pdf, test_rules):
    def toc(document):
        document.drawString(60, 740, "Sumário")
        document.drawString(60, 710, "Primeira parte. Segunda parte. Terceira parte. ........ 2")

    def chapter(document):
        document.drawString(60, 720, "Primeira parte.")
        document.drawString(60, 690, "Segunda parte.")
        document.drawString(60, 660, "Terceira parte.")

    pdf = open_pdf(layout_pdf(toc, chapter))
    assert [f.detail for f in checks.check_toc(pdf, test_rules)] == []
