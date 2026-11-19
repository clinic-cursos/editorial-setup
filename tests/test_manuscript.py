from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"))

from manuscript import ManuscriptError, parse  # noqa: E402

META = "title: Exemplo\ncourse: Curso\nauthors: Ana Silva, Rui Costa\nversion: 1.0\n\n"


def body(text):
    return parse(META + text)


def test_parse_headings():
    ms = body("# Capítulo\n\n## Seção\n\n### Item\n")
    assert ms.meta["authors"] == "Ana Silva, Rui Costa"
    assert [(b.type, b.level, b.text) for b in ms.blocks] == [
        ("heading", 1, "Capítulo"), ("heading", 2, "Seção"), ("heading", 3, "Item")]
    assert [b.id for b in ms.blocks] == ["b0001", "b0002", "b0003"]
    with pytest.raises(ManuscriptError):
        body("#### Fundo demais\n")


def test_parse_lists():
    ms = body("- um\n- dois\n\n1. a\n2. b\n")
    assert [(b.ordered, b.items) for b in ms.blocks] == [(False, ["um", "dois"]), (True, ["a", "b"])]


def test_parse_blocks():
    ms = body("Antes.\ncontinua.\n\n:::ponto-chave\nSíntese.\n\n- item\n:::\n\nDepois.\n")
    para, box, after = ms.blocks
    assert para.text == "Antes. continua."
    assert box.type == "box" and box.kind == "ponto-chave"
    assert [(c.type, c.text or c.items) for c in box.children] == [("paragraph", "Síntese."), ("list", ["item"])]
    assert after.text == "Depois."
    with pytest.raises(ManuscriptError, match="fechamento"):
        body(":::atencao\nSem fim.\n")


def test_parse_slide_marker():
    ms = body("<!-- slide: 12 -->\nTexto do slide.\n\nOutro.\n")
    assert [b.slide for b in ms.blocks] == [12, None]
    assert len(ms.blocks) == 2


def test_parse_citation_and_references():
    ms = body("Fato [@a1].\n\n## Referências\n\n- [@a1] Dados da fonte.\n")
    refs = ms.blocks[-1]
    assert refs.type == "references" and refs.entries == [("a1", "Dados da fonte.")]
    with pytest.raises(ManuscriptError, match="@x9"):
        body("Fato [@x9].\n\n## Referências\n\n- [@a1] Dados.\n")


def test_parse_figure_with_id():
    fig = body("![Esquema](imagens/e.png){#fig-esquema}\n").blocks[0]
    assert (fig.type, fig.text, fig.src, fig.fig_id) == ("figure", "Esquema", "imagens/e.png", "fig-esquema")
    with pytest.raises(ManuscriptError, match="repetido"):
        body("![a](a.png){#fig-x}\n\n![b](b.png){#fig-x}\n")
    with pytest.raises(ManuscriptError):
        body("![sem id](a.png)\n")


def test_unknown_block_is_error():
    with pytest.raises(ManuscriptError, match=":::dica"):
        body(":::dica\nTexto.\n:::\n")
    with pytest.raises(ManuscriptError, match="metadados"):
        parse("title: só um\n\nTexto.\n")
