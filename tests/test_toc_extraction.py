"""Regressão do sumário original copiado para o manuscrito no ensaio 3.8."""

from pathlib import Path
import subprocess
import sys

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from lib.pdfcheck import checks

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

from build_book import build  # noqa: E402
from text_fidelity import fidelity  # noqa: E402

WINE = (0.57, 0.0, 0.2)
INK = (0.14, 0.14, 0.14)
CHAPTER_START = "Texto aprovado no inicio do capitulo."


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


def _book_with_toc(path):
    """Livro composto com sumário próprio: números de página antigos, que não valem no livro recomposto."""
    c = canvas.Canvas(str(path), pagesize=A4)
    _text(c, 760, "Sumário", 20, WINE)
    _text(c, 700, "Introducao aos preenchedores 9")
    _text(c, 670, "Reticulacao e reologia .... 12")
    c.showPage()
    for title in ("Introducao aos preenchedores", "Reticulacao e reologia"):
        _text(c, 760, title, 20, WINE)
        _text(c, 720, "O preenchedor modifica a relacao entre volume, suporte e contorno do rosto.")
        c.showPage()
    c.save()


def _book_with_mixed_toc(path):
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(60, 760, "Sumário")
    c.drawString(60, 720, "Capitulo 9")
    c.drawString(60, 660, CHAPTER_START)
    c.showPage()
    c.drawString(60, 760, "Corpo preservado nesta pagina.")
    c.save()


# Causa 1 (6 dos 13 erros): extract_pdf.py copia o sumário do original para o corpo do manuscrito.
def test_extraction_drops_original_toc(tmp_path):
    pdf = tmp_path / "livro.pdf"
    _book_with_toc(pdf)
    out, _ = _extract(pdf, tmp_path)
    md = out.read_text(encoding="utf-8")
    assert "Sumário" not in md
    assert "preenchedores 9" not in md and "reologia .... 12" not in md


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
    md.write_text(
        "title: T\ncourse: C\nauthors: A\nversion: 1\n\n"
        "# Introducao aos preenchedores\n\n"
        "O preenchedor modifica a relacao entre volume, suporte e contorno do rosto.\n\n"
        "# Reticulacao e reologia\n\n"
        "O preenchedor modifica a relacao entre volume, suporte e contorno do rosto.\n",
        encoding="utf-8",
    )
    assert fidelity(str(pdf), str(md)) == (1.0, 1.0)


def test_extraction_keeps_mixed_toc_page(tmp_path):
    pdf = tmp_path / "livro.pdf"
    _book_with_mixed_toc(pdf)
    out, warnings = _extract(pdf, tmp_path)
    md = out.read_text(encoding="utf-8")
    assert CHAPTER_START in md
    assert "Sumário" in md and "Capitulo 9" in md
    assert "página 1: sumário com texto de corpo, mantido para conferência" in warnings


def test_fidelity_detects_missing_text_on_mixed_toc_page(tmp_path):
    pdf = tmp_path / "livro.pdf"
    _book_with_mixed_toc(pdf)
    md = tmp_path / "manuscrito.md"
    metadata = "title: T\ncourse: C\nauthors: A\nversion: 1\n\n"
    preserved = metadata + f"Sumário\n\nCapitulo 9\n\n{CHAPTER_START}\n\nCorpo preservado nesta pagina.\n"
    md.write_text(preserved, encoding="utf-8")
    assert fidelity(str(pdf), str(md)) == (1.0, 1.0)
    md.write_text(preserved.replace(f"{CHAPTER_START}\n\n", ""), encoding="utf-8")
    kept, added = fidelity(str(pdf), str(md))
    assert kept < 0.995 and added == 1.0
