from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

from text_fidelity import fidelity, main  # noqa: E402

META = "title: T\ncourse: C\nauthors: A\nversion: 1\n\n"
PARAGRAPHS = [
    "A eficiência do tratamento depende da hifenização correta e da avaliação clínica cuidadosa.",
    "Cada paciente apresenta características próprias que orientam a escolha da técnica adequada.",
    "O registro fotográfico segue o protocolo definido pela equipe responsável pelo atendimento.",
]


def write(tmp_path, name, paragraphs):
    path = tmp_path / name
    path.write_text(META + "\n\n".join(paragraphs) + "\n", encoding="utf-8")
    return path


def test_fidelity_identical_is_one(tmp_path, capsys):
    a = write(tmp_path, "a.md", PARAGRAPHS)
    b = write(tmp_path, "b.md", PARAGRAPHS)
    assert fidelity(str(a), str(b)) == 1.0
    assert main([str(a), str(b)]) == 0
    assert capsys.readouterr().out.strip() == "1.0000"


def test_fidelity_ligature_and_hyphenation_normalized(tmp_path):
    changed = [
        "A eﬁciência do trata\u00admento depende da hifeni-\nzação correta e da avaliação clínica cuidadosa.",
        "Cada paciente apresenta caracteri\u0301sticas próprias  que orientam a escolha da técnica adequada.",
        PARAGRAPHS[2],
    ]
    a = write(tmp_path, "a.md", PARAGRAPHS)
    b = write(tmp_path, "b.md", changed)
    assert fidelity(str(a), str(b)) == pytest.approx(1.0)


def test_fidelity_missing_paragraph_fails(tmp_path, capsys):
    a = write(tmp_path, "a.md", PARAGRAPHS)
    b = write(tmp_path, "b.md", PARAGRAPHS[:2])
    assert main([str(a), str(b)]) == 1
    assert float(capsys.readouterr().out) < 0.995


def test_fidelity_reads_pdf_without_header_footer_and_page_number(tmp_path, layout_pdf):
    def page(c):
        c.setFont("Helvetica", 10)
        c.drawString(60, 820, "CABECALHO DO LIVRO")
        c.drawString(60, 100, "Texto da pagina com conteudo proprio.")
        c.drawString(300, 20, "7")
    pdf = layout_pdf(page)
    md = tmp_path / "o.md"
    md.write_text(META + "Texto da pagina com conteudo proprio.\n", encoding="utf-8")
    assert fidelity(str(md), str(pdf)) == 1.0
    assert fidelity(str(pdf), str(pdf)) == 1.0
