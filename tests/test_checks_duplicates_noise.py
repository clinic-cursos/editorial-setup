"""check_duplicates não confunde cabeçalho corrido nem pontilhado do sumário com parágrafo repetido."""

import dataclasses

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from lib.pdfcheck import checks

HEADER = "CLINIC EDITORA                                   TITULO DO LIVRO DE TESTE COM NOME LONGO"
OPENING = "Esquema didatico do curso, legenda curta que abre a pagina"  # < 100 caracteres


def test_running_header_plus_same_opening_is_not_duplicate(tmp_path, open_pdf, test_rules):
    # Quatro páginas com o cabeçalho corrido na faixa de cima (acima dos 26 mm) e o corpo abrindo
    # com a mesma legenda curta; o resto do corpo é diferente. Nenhum trecho do corpo chega a 100 caracteres repetidos.
    path = tmp_path / "header.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    height = A4[1]
    for n in range(4):
        c.setFont("Helvetica", 6.5)
        c.drawString(62, height - 50, HEADER)  # topo da linha a ~44 pt: dentro da faixa de 26 mm (73,7 pt)
        c.setFont("Helvetica", 9.5)
        c.drawString(62, height - 100, OPENING)
        c.drawString(62, height - 120, f"Conteudo proprio da pagina numero {n} sem relacao com as outras {n * 7}.")
        c.drawString(290, 40, str(n + 1))
        c.showPage()
    c.save()
    found = checks.check_duplicates(open_pdf(path), test_rules)
    assert found == [], [(f.page, f.detail) for f in found]


def test_toc_dot_leaders_are_not_duplicate(tmp_path, open_pdf, test_rules):
    # Sumário gerado com leader("."): cada entrada é título, pontilhado longo e número da página.
    path = tmp_path / "toc.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica", 10)
    titles = ("Introducao", "Anatomia facial", "Complicacoes", "Referencias")
    for i, title in enumerate(titles):
        c.drawString(62, 700 - 20 * i, f"{title} {'.' * (120 - len(title))} {3 + 10 * i}")
    c.save()
    found = checks.check_duplicates(open_pdf(path), test_rules)
    assert found == [], [(f.page, f.detail) for f in found]


def test_real_body_repetition_is_still_flagged_with_running_header(tmp_path, open_pdf, test_rules):
    path = tmp_path / "real.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    height = A4[1]
    para = ("Este paragrafo de corpo repete de verdade em duas paginas e tem bem mais de cem caracteres, "
            "portanto precisa continuar sendo acusado pela checagem.")
    for n in range(4):
        c.setFont("Helvetica", 6.5)
        c.drawString(62, height - 50, HEADER)
        c.setFont("Helvetica", 9.5)
        if n in (1, 2):
            c.drawString(62, height - 100, para[:95])
            c.drawString(62, height - 112, para[95:])
        else:
            c.drawString(62, height - 100, f"Conteudo unico da pagina {n} sem relacao com as outras {n * 7}.")
        c.drawString(290, 40, str(n + 1))
        c.showPage()
    c.save()
    found = checks.check_duplicates(open_pdf(path), test_rules)
    assert [(f.page, f.kind) for f in found] == [(3, "duplicate-paragraph")], found


def test_allowed_repeat_with_ellipsis_is_not_flagged(tmp_path, open_pdf, test_rules):
    notice = ("Aviso legal permitido que se repete de proposito em varias paginas do livro... "
              "e que contem reticencias no meio do texto corrido para o teste.")
    path = tmp_path / "ellipsis.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica", 9)
    for n in range(2):
        c.drawString(62, 700, notice[:80])
        c.drawString(62, 688, notice[80:])
        c.drawString(62, 600, f"Conteudo unico {n} {n * 13}.")
        c.showPage()
    c.save()
    rules = dataclasses.replace(test_rules, allowed_repeats=[notice])
    assert checks.check_duplicates(open_pdf(path), rules) == []

