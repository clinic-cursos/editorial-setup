import json
from pathlib import Path
import subprocess
import sys

from PIL import Image
import pytest
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

from build_book import build  # noqa: E402
from manuscript import parse  # noqa: E402
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


def test_reused_image_referenced_twice(tmp_path):
    path = tmp_path / "reuse.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    red = ImageReader(Image.new("RGB", (40, 30), "red"))
    blue = ImageReader(Image.new("RGB", (40, 30), "blue"))
    for y, image in ((700, blue), (560, red), (420, red)):
        c.drawImage(image, 60, y, width=80, height=60)
    text(c, 300, BODY[0])
    c.save()
    out, images, _ = extract(path, tmp_path)
    md = out.read_text(encoding="utf-8")
    refs = [line for line in md.splitlines() if line.startswith("![")]
    files = [line.split("](")[1].split(")")[0] for line in refs]
    assert len(refs) == 3 and len({r.split("#")[1] for r in refs}) == 3
    assert files[1] == files[2] != files[0]  # a mesma imagem aponta para um só arquivo
    assert len(list(images.glob("*.png"))) == 2
    assert Image.open(out.parent / files[0]).getpixel((0, 0))[2] > 200  # azul primeiro


def test_inline_image_extracted(tmp_path):
    path = tmp_path / "inline.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawInlineImage(Image.new("RGB", (20, 20), "blue"), 60, 700, width=40, height=40)
    c.drawInlineImage(Image.new("RGB", (20, 20), "red"), 60, 600, width=40, height=40)
    text(c, 300, BODY[0])
    c.save()
    out, images, stderr = extract(path, tmp_path)
    refs = [line for line in out.read_text(encoding="utf-8").splitlines() if line.startswith("![")]
    assert len(refs) == 2 and "imagem" not in stderr
    assert sorted(p.name for p in images.glob("*.png")) == ["fig-1.png", "fig-2.png"]
    assert Image.open(images / "fig-1.png").getpixel((0, 0))[2] > 200  # azul primeiro


def test_images_dir_with_space_fails(book_pdf, tmp_path):
    out = tmp_path / "texto" / "manuscrito.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(book_pdf), "--out", str(out), "--images", str(out.parent / "minhas imagens")],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "use um nome de pasta sem espaços" in result.stderr
    assert not out.exists()


def test_list_numbering_preserved_across_pages(tmp_path):
    path = tmp_path / "lists.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    for y, line in ((700, "3. Terceiro item da lista numerada"), (680, "4 — Quarto item com marcador de travessao")):
        text(c, y, line)
    c.showPage()
    text(c, 700, "05. Quinto item na pagina seguinte")
    pdfmetrics.registerFont(TTFont("Vera", str(Path(reportlab.__file__).parent / "fonts" / "Vera.ttf")))  # Helvetica não tem "•"
    c.setFont("Vera", 10)
    c.drawString(60, 650, "• Item solto com marcador")
    c.drawString(60, 636, "• Outro item solto")
    c.save()
    md = extract(path, tmp_path)[0].read_text(encoding="utf-8")
    assert "3. Terceiro item" in md and "4. Quarto item" in md and "5. Quinto item" in md
    assert "- Item solto com marcador\n- Outro item solto" in md


def test_references_section_extracted_in_reader_format(tmp_path):
    path = tmp_path / "refs.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    for n, line in enumerate(BODY):
        text(c, 760 - 14 * n, line)
    text(c, 700, "Referências", 14, WINE)
    text(c, 660, "SILVA, A. B. Toxina botulinica em dermatologia. Sao Paulo: Editora, 2020.")
    text(c, 646, "Segunda linha da mesma referencia.")
    text(c, 610, "Costa C. Acido hialuronico na pratica clinica. Rev Derm. 2019;12:1-9.")
    c.save()
    out, _, _ = extract(path, tmp_path)
    md = out.read_text(encoding="utf-8")
    assert "## Referências\n\n- [@silva2020] SILVA, A. B. Toxina botulinica em dermatologia. Sao Paulo: Editora, 2020. Segunda linha" in md
    assert "- [@costa2019] Costa C. Acido hialuronico" in md
    manuscript = parse(md)
    assert manuscript.refs.keys() == {"silva2020", "costa2019"}


def test_two_column_page_read_column_by_column(tmp_path):
    path = tmp_path / "columns.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    for n in range(6):
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(*INK)
        c.drawString(60, 700 - 14 * n, f"Esquerda linha {n + 1} do texto na primeira coluna")
        c.drawString(330, 700 - 14 * n, f"Direita linha {n + 1} do texto na segunda coluna")
    c.save()
    out, _, stderr = extract(path, tmp_path)
    md = out.read_text(encoding="utf-8")
    assert md.index("Esquerda linha 6") < md.index("Direita linha 1")
    assert "Esquerda linha 1 do texto na primeira coluna Esquerda linha 2" in md
    assert "duas colunas" in stderr


def test_images_dir_with_whitespace_fails(book_pdf, tmp_path):
    out = tmp_path / "texto" / "manuscrito.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(book_pdf), "--out", str(out), "--images", str(out.parent / "minhas\timagens")],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "use um nome de pasta sem espaços" in result.stderr
    assert not out.exists()


def test_figure_after_references_stays_in_body(tmp_path):
    path = tmp_path / "refs-figure.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    text(c, 760, BODY[0])
    text(c, 700, "Referências", 14, WINE)
    text(c, 660, "SILVA, A. B. Toxina botulinica em dermatologia. Sao Paulo: Editora, 2020.")
    c.drawImage(ImageReader(Image.new("RGB", (40, 30), "red")), 60, 400, width=80, height=60)
    c.save()
    md = extract(path, tmp_path)[0].read_text(encoding="utf-8")
    assert "- [@silva2020] SILVA" in md
    assert md.index("#fig-1") < md.index("## Referências")


def test_title_crossing_columns_warns(tmp_path):
    path = tmp_path / "columns-title.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    text(c, 740, "Titulo largo que atravessa o vao entre as duas colunas da pagina inteira", 14)
    for n in range(6):
        text(c, 700 - 14 * n, f"Esquerda linha {n + 1} do texto na primeira coluna")
        c.drawString(330, 700 - 14 * n, f"Direita linha {n + 1} do texto na segunda coluna")
    c.save()
    out, _, stderr = extract(path, tmp_path)
    md = out.read_text(encoding="utf-8")
    assert "verifique a ordem do texto desta página" in stderr
    assert md.index("Titulo largo") < md.index("Esquerda linha 1") < md.index("Esquerda linha 6") < md.index("Direita linha 1")


def test_compact_references_warn(tmp_path):
    path = tmp_path / "compact-refs.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    text(c, 760, BODY[0])
    text(c, 700, "Referências", 14, WINE)
    text(c, 660, "SILVA, A. B. Toxina botulinica em dermatologia. Sao Paulo: Editora, 2020.")
    text(c, 646, "COSTA, C. Acido hialuronico na pratica clinica. Rio de Janeiro: Editora, 2019.")
    c.save()
    assert "verifique a separação das referências" in extract(path, tmp_path)[2]


def test_origin_json_records_effective_ppi(book_pdf, tmp_path):
    _, images, _ = extract(book_pdf, tmp_path)
    origin = json.loads((images / "origem.json").read_text(encoding="utf-8"))
    assert origin == {"fig-1.png": {"pixels": [40, 30], "ppi": 36.0}}  # 40 px em 80 pt
