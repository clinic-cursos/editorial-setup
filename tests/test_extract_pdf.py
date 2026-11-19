from pathlib import Path
import subprocess
import sys

from PIL import Image
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

from build_book import build  # noqa: E402
from text_fidelity import fidelity  # noqa: E402

SCRIPT = SCRIPTS / "extract_pdf.py"
WINE = (0.57, 0.0, 0.2)
INK = (0.14, 0.14, 0.14)
BODY = [
    "O preenchedor modifica a relacao entre volume, suporte e contorno do rosto",
    "e exige avaliacao criteriosa antes de cada aplicacao no paciente atendido.",
]
SECOND = "Segundo paragrafo separado do primeiro por um salto maior entre as linhas."


def text(c, y, value, size=10, color=INK):
    c.setFont("Helvetica", size)
    c.setFillColorRGB(*color)
    c.drawString(60, y, value)


@pytest.fixture
def book_pdf(tmp_path):
    path = tmp_path / "livro.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    for page in (1, 2):
        text(c, 820, "CLINIC EDITORA PREENCHEDORES", 7)  # cabeçalho
        text(c, 20, f"Pagina {page}", 8)  # rodapé com número
        if page == 1:
            text(c, 740, "Introducao aos preenchedores", 20, WINE)
            text(c, 700, "DIMENSOES PARA O PLANEJAMENTO", 9, WINE)
            for n, line in enumerate(BODY):
                text(c, 670 - 14 * n, line)
            text(c, 620, SECOND)
            text(c, 580, "1. Tome ciencia dos materiais permitidos para o procedimento")
            text(c, 566, "e verifique a regularizacao dos produtos.")
            text(c, 540, "2. Investigue aplicacoes anteriores, mesmo antigas.")
        else:
            image = Image.new("RGB", (40, 30), "red")
            c.drawImage(ImageReader(image), 60, 600, width=80, height=60)
            text(c, 560, "Texto depois da imagem na segunda pagina do livro.")
        c.showPage()
    c.save()
    return path


def extract(pdf, tmp_path):
    out, images = tmp_path / "texto" / "manuscrito.md", tmp_path / "texto" / "imagens"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(pdf), "--out", str(out), "--images", str(images)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    return out, images, result.stderr


def test_headings_recovered(book_pdf, tmp_path):
    out, _, _ = extract(book_pdf, tmp_path)
    md = out.read_text(encoding="utf-8")
    assert "# Introducao aos preenchedores\n" in md
    assert "### DIMENSOES PARA O PLANEJAMENTO\n" in md
    assert " ".join(BODY) + "\n\n" + SECOND in md
    assert "1. Tome ciencia dos materiais permitidos para o procedimento e verifique" in md
    assert "2. Investigue aplicacoes anteriores" in md


def test_header_footer_dropped(book_pdf, tmp_path):
    md = extract(book_pdf, tmp_path)[0].read_text(encoding="utf-8")
    assert "CLINIC EDITORA" not in md
    assert "Pagina 1" not in md and "Pagina 2" not in md


def test_image_extracted_and_referenced(book_pdf, tmp_path):
    out, images, _ = extract(book_pdf, tmp_path)
    md = out.read_text(encoding="utf-8")
    assert "![](imagens/fig-1.png){#fig-1}" in md
    assert (images / "fig-1.png").is_file()
    assert md.index("#fig-1") < md.index("Texto depois da imagem")


def test_round_trip_fidelity(book_pdf, tmp_path):
    out, _, _ = extract(book_pdf, tmp_path)
    assert min(fidelity(str(book_pdf), str(out))) >= 0.995
    built = build(str(out), str(tmp_path / "build"))
    assert min(fidelity(str(out), built.pdf)) >= 0.995


def test_bordo_uppercase_label_wins_over_size(tmp_path):
    path = tmp_path / "label.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    text(c, 700, "ROTULO EM DESTAQUE", 14, WINE)
    for n in range(6):
        text(c, 660 - 14 * n, BODY[n % 2])
    c.save()
    md = extract(path, tmp_path)[0].read_text(encoding="utf-8")
    assert "\n### ROTULO EM DESTAQUE\n" in md


def test_images_dir_outside_manuscript_dir_fails(book_pdf, tmp_path):
    out = tmp_path / "texto" / "manuscrito.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(book_pdf), "--out", str(out), "--images", str(tmp_path / "figuras")],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "dentro da pasta do manuscrito" in result.stderr
    assert not out.exists()
