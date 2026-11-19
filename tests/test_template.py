import re
from pathlib import Path

import pdfplumber
import pytest
from weasyprint import HTML

from lib.pdfcheck.checks import check_fonts, check_page_size, check_toc
from lib.pdfcheck.rules import load_rules

ROOT = Path(__file__).parent.parent
ASSETS = ROOT / "skills" / "diagramador" / "assets"
SAMPLE = ROOT / "tests" / "samples" / "amostra.html"
COMPONENTS = ["estudo-pratica", "leitura-aprofundamento", "aplicacao-clinica", "ponto-chave", "atencao", "evidencia", "faq", "legenda"]


@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory):
    out = tmp_path_factory.mktemp("amostra") / "amostra.pdf"
    HTML(filename=str(SAMPLE)).write_pdf(str(out))
    return out


def test_template_renders_with_brand_fonts(sample_pdf):
    rules = load_rules()
    with pdfplumber.open(sample_pdf) as pdf:
        assert len(pdf.pages) >= 5
        assert check_fonts(pdf, rules) == []
        assert check_page_size(pdf, rules) == []


def test_css_has_one_class_per_component():
    css = (ASSETS / "livro.css").read_text(encoding="utf-8")
    for name in COMPONENTS:
        assert f".{name}" in css, name
    assert "target-counter" in css and "size: A4" in css


def _toc_report(html_path, out):
    HTML(filename=str(html_path)).write_pdf(str(out))
    with pdfplumber.open(out) as pdf:
        text = pdf.pages[2].extract_text()
        return text, check_toc(pdf, load_rules())


def test_toc_entries_carry_the_page_where_the_title_appears(tmp_path):
    text, findings = _toc_report(SAMPLE, tmp_path / "ok.pdf")
    assert re.search(r"Introdução aos preenchedores\W*4\b", text)
    assert re.search(r"Texto com caixas\W*5\b", text)
    assert re.search(r"Imagem com legenda\W*6\b", text)
    assert findings == []


def test_sample_uses_every_component():
    html = SAMPLE.read_text(encoding="utf-8")
    for name in COMPONENTS:
        assert re.search(rf'class="[^"]*\b{name}\b', html), name


def test_shell_has_content_slot():
    html = (ASSETS / "livro.html").read_text(encoding="utf-8")
    for slot in ("{{CONTEUDO}}", "{{TITULO}}", "{{SUMARIO}}"):
        assert slot in html
