import json
from pathlib import Path
import sys

import pdfplumber
from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

from build_book import build, main  # noqa: E402
from manuscript import walk, parse  # noqa: E402

TEXT = """title: Livro de teste
course: Curso de teste
authors: Ana Silva, Rui Costa
version: 1.0

# Primeiro capítulo

Parágrafo com citação [@fonte].

## Seção

<!-- slide: 3 -->
- um
- dois

:::ponto-chave
Síntese.
:::

![Figura de teste](img/f.png){#fig-f}

# Segundo capítulo

Texto final.

## Referências

- [@fonte] Dados da fonte.
"""


def make_manuscript(tmp_path):
    (tmp_path / "img").mkdir()
    Image.new("RGB", (60, 40), "#800020").save(tmp_path / "img" / "f.png")
    source = tmp_path / "manuscrito.md"
    source.write_text(TEXT, encoding="utf-8")
    return source


def test_build_writes_three_files(tmp_path):
    out = tmp_path / "saida"
    result = build(str(make_manuscript(tmp_path)), str(out))
    assert (out / "livro.html").is_file() and (out / "layout.json").is_file()
    assert Path(result.pdf) == out / "livro.pdf"
    with pdfplumber.open(result.pdf) as pdf:
        assert len(pdf.pages) == result.pages >= 4
    assert json.loads((out / "layout.json").read_text()) == result.layout


def test_layout_maps_every_block(tmp_path):
    source = make_manuscript(tmp_path)
    result = build(str(source), str(tmp_path / "saida"))
    ids = [b.id for b in walk(parse(TEXT).blocks)]
    assert set(result.layout) == set(ids)
    pages = [result.layout[i] for i in ids]
    assert pages == sorted(pages) and pages[0] >= 4  # capa, expediente e sumário vêm antes
    assert 'id="b0001"' in Path(result.html).read_text(encoding="utf-8")


def test_cli_reports_manuscript_error(tmp_path, capsys):
    bad = tmp_path / "ruim.md"
    bad.write_text(TEXT.replace(":::ponto-chave", ":::dica"), encoding="utf-8")
    assert main([str(bad), "--out", str(tmp_path / "o")]) == 1
    assert ":::dica" in capsys.readouterr().err
    assert main([str(tmp_path / "nao-existe.md"), "--out", str(tmp_path / "o")]) == 2


def test_placeholder_text_in_manuscript_kept(tmp_path):
    source = tmp_path / "m.md"
    source.write_text(TEXT.replace("title: Livro de teste", "title: {{AUTORES}} em {{SUMARIO}}")
                      .replace("Texto final.", "Veja {{CONTEUDO}}.").replace("![Figura de teste](img/f.png){#fig-f}", ""),
                      encoding="utf-8")
    html = Path(build(str(source), str(tmp_path / "o")).html).read_text(encoding="utf-8")
    assert "<title>{{AUTORES}} em {{SUMARIO}}</title>" in html
    assert "Veja {{CONTEUDO}}." in html


def test_citation_is_rendered_not_literal(tmp_path):
    source = make_manuscript(tmp_path)
    source.write_text(TEXT.replace("Dados da fonte.", "SILVA, A. Obra. Editora, 2024."), encoding="utf-8")
    html = Path(build(str(source), str(tmp_path / "o")).html).read_text(encoding="utf-8")
    assert "(SILVA, 2024)" in html and "[@" not in html


def test_faq_renders_definition_list(tmp_path):
    source = make_manuscript(tmp_path)
    source.write_text(TEXT.replace("Texto final.", "Texto final.\n\n:::faq\nPosso?\nSim.\n:::"), encoding="utf-8")
    html = Path(build(str(source), str(tmp_path / "o")).html).read_text(encoding="utf-8")
    assert "<dt>Posso?</dt><dd>Sim.</dd>" in html


def test_list_start_number_survives_build(tmp_path):
    source = tmp_path / "m.md"
    source.write_text("title: T\ncourse: C\nauthors: A\nversion: 1\n\n# Cap\n\n4. quarto\n5. quinto\n", encoding="utf-8")
    assert parse(source.read_text(encoding="utf-8")).blocks[1].start == 4
    result = build(str(source), str(tmp_path / "out"))
    assert '<ol id="b0002" start="4">' in Path(result.html).read_text(encoding="utf-8")
