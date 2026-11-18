"""PDFs sintéticos gerados por código (ReportLab); nenhum binário no git."""

import dataclasses

import pdfplumber
import pytest
from PIL import Image
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from lib.pdfcheck.rules import load_rules

PARAGRAPH = (
    "Este paragrafo longo repete exatamente o mesmo texto em duas paginas para que a checagem "
    "de duplicacao o encontre sem duvida alguma."
)
assert len(PARAGRAPH) >= 110


def _make(path, size=A4):
    return canvas.Canvas(str(path), pagesize=size)


@pytest.fixture
def test_rules():
    rules = load_rules()
    return dataclasses.replace(rules, allowed_fonts=[*rules.allowed_fonts, "Helvetica"])


@pytest.fixture
def clean_pdf(tmp_path):
    p = tmp_path / "clean.pdf"
    c = _make(p)
    c.setFont("Helvetica", 12)
    c.drawString(80, 700, "Primeira linha do texto limpo.")
    c.drawString(80, 680, "Segunda linha, sem nenhum problema.")
    # negrito simulado: mesma letra duas vezes no mesmo lugar não é sobreposição
    c.drawString(80, 660, "Linha em negrito simulado")
    c.drawString(80.3, 660, "Linha em negrito simulado")
    c.showPage()
    c.setFont("Helvetica", 12)
    c.drawString(80, 700, "Pagina dois com outro conteudo.")
    c.save()
    return p


@pytest.fixture
def overlap_pdf(tmp_path):
    p = tmp_path / "overlap.pdf"
    c = _make(p)
    c.setFont("Helvetica", 12)
    c.drawString(80, 700, "Pagina um sem problema.")
    c.showPage()
    c.setFont("Helvetica", 12)
    c.drawString(80, 700, "Linha de cima do trecho")
    c.drawString(80, 696, "Linha que cai por cima")
    c.save()
    return p


@pytest.fixture
def safe_zone_pdf(tmp_path):
    p = tmp_path / "safe.pdf"
    c = _make(p)
    c.setFont("Helvetica", 12)
    c.drawString(5 * 72 / 25.4, 700, "Texto a cinco milimetros da borda")
    c.save()
    return p


@pytest.fixture
def duplicate_pdf(tmp_path):
    p = tmp_path / "dup.pdf"
    c = _make(p)
    for extra in ("Pagina um.", "Pagina dois."):
        c.setFont("Helvetica", 9)
        c.drawString(60, 700, extra)
        c.drawString(60, 650, PARAGRAPH)
        c.showPage()
    c.save()
    return p


@pytest.fixture
def image_only_pdf(tmp_path):
    p = tmp_path / "image.pdf"
    c = _make(p)
    c.setFont("Helvetica", 12)
    c.drawString(80, 700, "Pagina com texto.")
    c.showPage()
    c.drawImage(ImageReader(Image.new("RGB", (40, 40), "#800020")), 100, 300, 200, 200)
    c.save()
    return p


@pytest.fixture
def letter_pdf(tmp_path):
    p = tmp_path / "letter.pdf"
    c = _make(p, letter)
    c.setFont("Helvetica", 12)
    c.drawString(80, 700, "Pagina em tamanho Carta.")
    c.save()
    return p


@pytest.fixture
def open_pdf():
    opened = []

    def _open(path):
        pdf = pdfplumber.open(path)
        opened.append(pdf)
        return pdf

    yield _open
    for pdf in opened:
        pdf.close()


@pytest.fixture
def near_overlap_pdf(tmp_path):
    p = tmp_path / "near_overlap.pdf"
    c = _make(p)
    c.setFont("Helvetica", 12)
    c.drawString(80, 700, "Bloco de cima")
    c.drawString(80, 699.5, "Bloco de baixo")
    c.save()
    return p


@pytest.fixture
def duplicate_under_titles_pdf(tmp_path):
    p = tmp_path / "dup_titles.pdf"
    c = _make(p)
    for title in ("Titulo da primeira secao", "Outro titulo bem diferente"):
        c.setFont("Helvetica", 12)
        c.drawString(60, 720, title)
        c.drawString(60, 706, "Este paragrafo de duas linhas aparece igual sob dois titulos distintos")
        c.drawString(60, 692, "e nenhum revisor deveria deixar a repeticao passar em silencio.")
        c.showPage()
    c.save()
    return p


CAPTION = (
    "Divulgação autorizada pelo usuário em TCLE. Esta imagem não representa, em hipótese alguma, "
    "garantia de resultado. Cada ser humano tem características anatômicas e fisiológicas únicas."
)


@pytest.fixture
def caption_repeat_pdf(tmp_path):
    p = tmp_path / "caption.pdf"
    c = _make(p)
    for title in ("Caso clinico um", "Outro caso clinico bem diferente"):
        c.setFont("Helvetica", 9)
        c.drawString(60, 720, title)
        cut = CAPTION.index(" ", 90)
        c.drawString(60, 650, CAPTION[:cut])
        c.drawString(60, 638.5, CAPTION[cut + 1 :])
        c.showPage()
    c.save()
    return p


@pytest.fixture
def same_page_duplicate_pdf(tmp_path):
    p = tmp_path / "same_page.pdf"
    c = _make(p)
    c.setFont("Helvetica", 9)
    c.drawString(60, 700, "Pagina com repeticao interna.")
    c.drawString(60, 650, PARAGRAPH)
    c.drawString(60, 600, "Texto intermediario diferente.")
    c.drawString(60, 550, PARAGRAPH)
    c.save()
    return p
