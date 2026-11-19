"""Regressão do sumário original copiado para o manuscrito no ensaio 3.8."""

from pathlib import Path
import json
import subprocess
import sys

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from lib.pdfcheck import checks

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

from build_book import build  # noqa: E402
from text_fidelity import fidelity  # noqa: E402

WINE = (0.57, 0.0, 0.2)
INK = (0.14, 0.14, 0.14)
BODY_TEXT = "A amostra incluiu 42"
GROUP_LINES = ("Grupo A incluiu 42", "Grupo B incluiu 35", "Grupo C incluiu 29")
CHAPTERS = (
    ("Introducao aos preenchedores", 9),
    ("Reticulacao e reologia", 12),
    ("Volume", 25),
    ("Suporte", 48),
    ("Contorno", 102),
)
PARAGRAPH = "O preenchedor modifica a relacao entre volume, suporte e contorno do rosto."
META = "title: T\ncourse: C\nauthors: A\nversion: 1\n\n"


def _text(c, y, value, size=10, color=INK):
    c.setFont("Helvetica", size)
    c.setFillColorRGB(*color)
    c.drawString(60, y, value)


def _extract(pdf, tmp_path):
    out, images = tmp_path / "texto" / "manuscrito.md", tmp_path / "texto" / "imagens"
    done = subprocess.run(
        [sys.executable, str(SCRIPTS / "extract_pdf.py"), str(pdf), "--out", str(out), "--images", str(images)],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    return out, done.stderr


def _book_with_toc(path, *, figure=False):
    """Livro composto com sumário próprio: números de página antigos, que não valem no livro recomposto."""
    c = canvas.Canvas(str(path), pagesize=A4)
    _text(c, 760, "Sumário")
    for index, (title, number) in enumerate(CHAPTERS):
        y = 700 - 30 * index
        if index == 0:
            _text(c, y, f"{title.upper()} . . . {number}")
        else:
            _text(c, y, title)
            c.drawRightString(500, y, str(number))
    if figure:
        c.drawImage(ImageReader(Image.new("RGB", (40, 30), "red")), 60, 400, width=80, height=60)
    c.showPage()
    for index, (title, _) in enumerate(CHAPTERS):
        if index == 1:
            first, second = title.split(" ", 1)
            _text(c, 760, first, 14, WINE)
            _text(c, 744, second, 14, WINE)
        else:
            _text(c, 760, title, 20, WINE)
        _text(c, 700, PARAGRAPH)
        c.showPage()
    c.save()


def _book_with_mixed_toc(path):
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(60, 760, "Sumário")
    c.drawString(60, 720, "Capitulo 9")
    c.drawString(60, 660, BODY_TEXT)
    c.showPage()
    c.drawString(60, 760, "Corpo preservado nesta pagina.")
    c.save()


# Causa 1 (6 dos 13 erros): extract_pdf.py copia o sumário do original para o corpo do manuscrito.
def test_extraction_drops_only_entries_confirmed_by_headings(tmp_path):
    pdf = tmp_path / "livro.pdf"
    _book_with_toc(pdf)
    out, _ = _extract(pdf, tmp_path)
    md = out.read_text(encoding="utf-8")
    assert "Sumário" in md
    assert "INTRODUCAO AOS PREENCHEDORES . . . 9" not in md
    for title, number in CHAPTERS[1:]:
        assert f"{title} {number}" not in md
    assert "## Reticulacao e reologia" in md


def test_recomposed_book_has_no_toc_mismatch(tmp_path, open_pdf, test_rules):
    pdf = tmp_path / "livro.pdf"
    _book_with_toc(pdf)
    out, _ = _extract(pdf, tmp_path)
    built = build(str(out), str(tmp_path / "v1"))
    findings = checks.check_toc(open_pdf(built.pdf), test_rules)
    assert [f.detail for f in findings] == []


def test_fidelity_ignores_original_toc(tmp_path):
    pdf = tmp_path / "livro.pdf"
    _book_with_toc(pdf)
    md = tmp_path / "manuscrito.md"
    expected = ["Sumário", *(f"# {title}\n\n{PARAGRAPH}" for title, _ in CHAPTERS)]
    md.write_text(META + "\n\n".join(expected) + "\n", encoding="utf-8")
    assert fidelity(str(pdf), str(md)) == (1.0, 1.0)


def test_extraction_keeps_mixed_toc_page(tmp_path):
    pdf = tmp_path / "livro.pdf"
    _book_with_mixed_toc(pdf)
    out, warnings = _extract(pdf, tmp_path)
    md = out.read_text(encoding="utf-8")
    assert BODY_TEXT in md
    assert "Sumário" in md and "Capitulo 9" in md
    assert "página 1: sumário com texto de corpo, mantido para conferência" in warnings


def test_fidelity_detects_missing_text_on_mixed_toc_page(tmp_path):
    pdf = tmp_path / "livro.pdf"
    _book_with_mixed_toc(pdf)
    md = tmp_path / "manuscrito.md"
    preserved = META + f"Sumário\n\nCapitulo 9\n\n{BODY_TEXT}\n\nCorpo preservado nesta pagina.\n"
    md.write_text(preserved, encoding="utf-8")
    assert fidelity(str(pdf), str(md)) == (1.0, 1.0)
    md.write_text(preserved.replace(f"{BODY_TEXT}\n\n", ""), encoding="utf-8")
    kept, added = fidelity(str(pdf), str(md))
    assert kept < 0.995 and added == 1.0


def test_aligned_body_lines_survive_extraction_and_fidelity(tmp_path):
    pdf = tmp_path / "livro.pdf"
    c = canvas.Canvas(str(pdf), pagesize=A4)
    _text(c, 760, "Sumário", 20, WINE)
    c.setFont("Helvetica", 10)
    for index, text in enumerate(GROUP_LINES):
        c.drawRightString(500, 700 - 30 * index, text)
    c.showPage()
    _text(c, 760, "Corpo preservado nesta pagina.")
    c.save()

    out, _ = _extract(pdf, tmp_path)
    manuscript = out.read_text(encoding="utf-8")
    for line in GROUP_LINES:
        assert line in manuscript
    assert fidelity(str(pdf), str(out)) == (1.0, 1.0)
    out.write_text(manuscript.replace(GROUP_LINES[1], ""), encoding="utf-8")
    assert fidelity(str(pdf), str(out))[0] < 0.995


def test_figure_on_toc_page_survives_matching_entries(tmp_path):
    pdf = tmp_path / "livro.pdf"
    _book_with_toc(pdf, figure=True)

    out, _ = _extract(pdf, tmp_path)
    manuscript = out.read_text(encoding="utf-8")
    assert "![](imagens/fig-1.png){#fig-1}" in manuscript
    assert "Contorno 102" not in manuscript
    images = out.parent / "imagens"
    assert Image.open(images / "fig-1.png").getpixel((0, 0)) == (255, 0, 0)
    assert "fig-1.png" in json.loads((images / "origem.json").read_text(encoding="utf-8"))


def test_only_headings_on_other_pages_confirm_entries(tmp_path):
    pdf = tmp_path / "livro.pdf"
    c = canvas.Canvas(str(pdf), pagesize=A4)
    _text(c, 760, "Sumário")
    _text(c, 720, "Volume .... 9")
    _text(c, 680, "Suporte .... 12")
    _text(c, 640, "Contorno .... 25")
    _text(c, 600, "Reologia .... 48")
    _text(c, 560, "Suporte", 20, WINE)
    c.showPage()
    _text(c, 760, "Volume", 20, WINE)
    _text(c, 720, "Contorno")
    _text(c, 680, "Reologia", 12)
    c.save()

    out, _ = _extract(pdf, tmp_path)
    manuscript = out.read_text(encoding="utf-8")
    assert "Volume .... 9" not in manuscript
    for entry in ("Suporte .... 12", "Contorno .... 25", "Reologia .... 48"):
        assert entry in manuscript
    assert fidelity(str(pdf), str(out)) == (1.0, 1.0)
