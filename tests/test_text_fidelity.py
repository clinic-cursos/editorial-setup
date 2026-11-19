from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

from build_book import build  # noqa: E402
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
    assert fidelity(str(a), str(b)) == (1.0, 1.0)
    assert main([str(a), str(b)]) == 0
    assert capsys.readouterr().out.strip() == "1.0000 1.0000"


def test_fidelity_ligature_and_hyphenation_normalized(tmp_path):
    changed = [
        "A eﬁciência do trata\u00admento depende da hifeni-\nzação correta e da avaliação clínica cuidadosa.",
        "Cada paciente apresenta caracteri\u0301sticas próprias  que orientam a escolha da técnica adequada.",
        PARAGRAPHS[2],
    ]
    a = write(tmp_path, "a.md", PARAGRAPHS)
    b = write(tmp_path, "b.md", changed)
    assert fidelity(str(a), str(b)) == pytest.approx((1.0, 1.0))


def test_fidelity_missing_paragraph_fails(tmp_path, capsys):
    a = write(tmp_path, "a.md", PARAGRAPHS)
    b = write(tmp_path, "b.md", PARAGRAPHS[:2])
    assert main([str(a), str(b)]) == 1
    kept, added = map(float, capsys.readouterr().out.split())
    assert kept < 0.995 and added == 1.0


def test_fidelity_reads_pdf_without_header_footer_and_page_number(tmp_path, layout_pdf):
    def page(c):
        c.setFont("Helvetica", 10)
        c.drawString(60, 820, "CABECALHO DO LIVRO")
        c.drawString(60, 100, "Texto da pagina com conteudo proprio.")
        c.drawString(300, 20, "7")
    pdf = layout_pdf(page)
    md = tmp_path / "o.md"
    md.write_text(META + "Texto da pagina com conteudo proprio.\n", encoding="utf-8")
    assert fidelity(str(md), str(pdf)) == (1.0, 1.0)
    assert fidelity(str(pdf), str(pdf)) == (1.0, 1.0)


def test_added_sentence_fails(tmp_path, capsys):
    a = write(tmp_path, "a.md", PARAGRAPHS)
    b = write(tmp_path, "b.md", [*PARAGRAPHS, "Recomenda-se dobrar a dose em pacientes com resposta lenta ao tratamento."])
    assert main([str(a), str(b)]) == 1
    kept, added = map(float, capsys.readouterr().out.split())
    assert kept == 1.0 and added < 0.995


def test_repeated_paragraph_fails(tmp_path):
    a = write(tmp_path, "a.md", PARAGRAPHS)
    b = write(tmp_path, "b.md", [*PARAGRAPHS, PARAGRAPHS[1]])
    assert main([str(a), str(b)]) == 1


def test_uppercase_heading_matches(tmp_path):
    a = write(tmp_path, "a.md", ["# Capítulo um", "## Objetivo geral", *PARAGRAPHS])
    b = write(tmp_path, "b.md", ["# CAPÍTULO UM", "## OBJETIVO GERAL", *PARAGRAPHS])
    assert fidelity(str(a), str(b)) == (1.0, 1.0)


def test_content_hyphen_preserved(tmp_path):
    a = write(tmp_path, "a.md", ["A dose é 5-10 mg por sessão, conforme o protocolo da clínica."])
    b = write(tmp_path, "b.md", ["A dose é 510 mg por sessão, conforme o protocolo da clínica."])
    assert main([str(a), str(b)]) == 1


def test_built_book_keeps_fidelity(tmp_path):
    source = tmp_path / "livro.md"
    source.write_text(
        META.replace("title: T", "title: Título do livro") + "# Capítulo um\n\n## Objetivo geral\n\n"
        + PARAGRAPHS[0] + " Veja [@fonte].\n\n- primeiro item\n- segundo item\n\n1. passo um\n2. passo dois\n\n"
        ":::ponto-chave\nSíntese da seção.\n:::\n\n:::faq\nPosso repetir?\nSim, após a avaliação.\n:::\n\n"
        + PARAGRAPHS[1] + "\n\n## Referências\n\n- [@fonte] SILVA, A. Obra citada. Editora, 2024.\n",
        encoding="utf-8")
    result = build(str(source), str(tmp_path / "o"))
    assert fidelity(str(source), result.pdf) == (1.0, 1.0)
    assert main([str(source), result.pdf]) == 0


def test_compound_broken_at_hyphen_matches(tmp_path):
    a = write(tmp_path, "a.md", ["O efeito anti-inflamatório do pós-procedimento dura vários dias."])
    b = write(tmp_path, "b.md", ["O efeito anti-\ninflamatório do pós-\nprocedimento dura vários dias."])
    assert fidelity(str(a), str(b)) == (1.0, 1.0)


def test_duplicated_paragraph_equal_to_heading_fails(tmp_path, layout_pdf):
    def page(c):
        c.setFont("Helvetica", 10)
        c.drawString(60, 700, "Texto aprovado.")
        c.drawString(60, 680, "Texto aprovado.")
    md = tmp_path / "o.md"
    md.write_text("title: Texto aprovado.\ncourse: C\nauthors: A\nversion: 1\n\nTexto aprovado.\n", encoding="utf-8")
    assert main([str(md), str(layout_pdf(page))]) == 1


def test_number_change_fails_regardless_of_ratio(tmp_path, capsys):
    long = [" ".join(f"palavra{i}" for i in range(300)), "O intervalo mínimo entre as sessões é de 10 dias."]
    a = write(tmp_path, "a.md", long)
    b = write(tmp_path, "b.md", [long[0], long[1].replace("10", "20")])
    assert min(fidelity(str(a), str(b))) >= 0.995  # a razão sozinha absorve a troca
    assert main([str(a), str(b)]) == 1


def test_number_difference_is_listed_with_context(tmp_path, capsys):
    a = write(tmp_path, "a.md", ["Aplicar 5 ml por sessão no protocolo."])
    b = write(tmp_path, "b.md", ["Aplicar 6 ml por sessão no protocolo."])
    main([str(a), str(b)])
    err = capsys.readouterr().err
    assert "5" in err and "6" in err and "ml por" in err



def test_cli_prints_four_decimals(tmp_path, capsys):
    a = write(tmp_path, "a.md", PARAGRAPHS)
    b = write(tmp_path, "b.md", PARAGRAPHS[:2])
    main([str(a), str(b)])
    assert all(len(x.split(".")[1]) == 4 for x in capsys.readouterr().out.split())


def test_compound_with_both_forms_in_original_matches(tmp_path):
    a = write(tmp_path, "a.md", ["O efeito anti-inflamatório e o termo antiinflamatório aparecem aqui."])
    b = write(tmp_path, "b.md", ["O efeito anti-\ninflamatório e o termo antiinflamatório aparecem aqui."])
    assert fidelity(str(a), str(b)) == (1.0, 1.0)


FONT = Path(__file__).resolve().parent.parent / "skills/diagramador/assets/fonts/SourceSans3-Regular.ttf"
FILLER = " ".join(f"palavra{i}" for i in range(300))  # mantém a razão acima do limite sem o teste do número


def _line_pdf(layout_pdf, line):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    pdfmetrics.registerFont(TTFont("SS3", str(FONT)))

    def page(c):
        c.setFont("SS3", 10)
        for n, part in enumerate(line.split("\n")):
            c.drawString(60, 400 - 15 * n, part)
        c.drawString(60, 380, FILLER[:90])
    return layout_pdf(page)


def _compare(tmp_path, layout_pdf, md_line, pdf_line):
    md = tmp_path / "o.md"
    md.write_text(META + md_line + "\n\n" + FILLER[:90] + "\n", encoding="utf-8")
    return main([str(md), str(_line_pdf(layout_pdf, pdf_line))])


def test_list_marker_style_is_not_a_number_change(tmp_path, layout_pdf):
    assert _compare(tmp_path, layout_pdf, "1. Composição", "01 — Composição") == 0


def test_number_inside_list_item_still_checked(tmp_path, layout_pdf, capsys):
    assert _compare(tmp_path, layout_pdf, "1. Dose de 20 U", "01 — Dose de 10 U") == 1
    err = capsys.readouterr().err
    assert "10" in err and "20" in err


def test_decimal_at_line_start_still_checked(tmp_path, layout_pdf):
    assert _compare(tmp_path, layout_pdf, "1.5 mL por sessão", "0.5 mL por sessão") == 1


def test_range_at_line_start_still_checked(tmp_path, layout_pdf):
    assert _compare(tmp_path, layout_pdf, "5 – 20 U por sessão", "5 – 10 U por sessão") == 1


def test_renumbered_list_item_is_a_difference(tmp_path, layout_pdf):
    assert _compare(tmp_path, layout_pdf, "1. Composição\n2. Dose", "01 — Composição\n03 — Dose") == 1
