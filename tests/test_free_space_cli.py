import json
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/imagens/scripts"
sys.path.insert(0, str(SCRIPTS))

from free_space import main  # noqa: E402


def short_page(document):
    document.drawString(60, 740, "Parágrafo curto.")
    document.line(60, 400, 150, 400)
    document.drawString(60, 15, "1")


def test_free_space_cli_lists_candidates(layout_pdf, tmp_path, capsys):
    out = tmp_path / "candidates.json"
    assert main([str(layout_pdf(short_page)), "--json", str(out)]) == 0
    assert "página 1" in capsys.readouterr().out
    row, = json.loads(out.read_text(encoding="utf-8"))
    assert row["page"] == 1
    assert row["width_mm"] == 190.0  # A4 menos duas zonas de segurança de 10 mm; a altura vai até a margem de baixo da mancha (24 mm)
    assert row["height_mm"] == round((400 - 24 * 72 / 25.4) / 72 * 25.4, 1)
    assert row["ratio"] == round(row["width_mm"] / row["height_mm"], 2)
    assert 0.25 < row["fraction"] < 1


def test_free_space_cli_unreadable_pdf_exits_2(tmp_path, capsys):
    broken = tmp_path / "broken.pdf"
    broken.write_text("not a pdf")
    assert main([str(broken)]) == 2
