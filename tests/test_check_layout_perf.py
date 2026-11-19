import os
from pathlib import Path
from random import Random
import subprocess
import sys
from time import perf_counter

import pdfplumber
from PIL import Image, ImageDraw
import pytest

from lib.pdfcheck import checks

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"


def write_manuscript(directory, chapters):
    directory.mkdir(parents=True, exist_ok=True)
    figure = Image.new("RGB", (1200, 300), "#ececec")
    ImageDraw.Draw(figure).rectangle((100, 70, 1100, 230), fill="#800020")
    figure.save(directory / "figura.png")

    words = (
        "amostra arquivo bloco cadeia campo capitulo cartao caixa ciclo codigo coluna conjunto "
        "contagem dado desenho eixo elemento escala espaco figura forma fundo grafico grupo "
        "indice largura leitura legenda letra limite linha lista livro matriz medida modelo "
        "numero objeto ordem pagina paragrafo parte passo ponto quadro regra resumo secao "
        "serie sinal tabela tamanho teste texto tipo titulo valor volume"
    ).split()
    random = Random(514)
    blocks = ["title: Livro sintetico\ncourse: Teste editorial\nauthors: Equipe de teste\nversion: 1"]
    for chapter in range(1, chapters + 1):
        blocks.append(f"# Capitulo sintetico {chapter}")
        for _ in range(10):
            blocks.append(" ".join(random.choices(words, k=26)).capitalize() + ".")
        if chapter % 5 == 0:
            blocks.append(f"![Figura sintetica {chapter}](figura.png){{#fig-{chapter}}}")
    source = directory / "manuscrito.md"
    source.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return source


def test_layout_checks_reuse_deduplicated_characters(clean_pdf, open_pdf, test_rules, monkeypatch):
    pdf = open_pdf(clean_pdf)
    expected = [page.dedupe_chars().chars for page in pdf.pages]
    dedupe_chars = pdfplumber.utils.dedupe_chars
    calls = []

    def count_deduplication(chars, **kwargs):
        calls.append(len(chars))
        return dedupe_chars(chars, **kwargs)

    monkeypatch.setattr(pdfplumber.utils, "dedupe_chars", count_deduplication)
    assert checks.check_overlaps(pdf, test_rules) == []
    assert checks.check_duplicates(pdf, test_rules) == []
    assert calls == [len(page.chars) for page in pdf.pages]
    for page, chars in zip(pdf.pages, expected):
        assert list(map(id, checks._deduped_page(page).chars)) == list(map(id, chars))


@pytest.mark.skipif(os.environ.get("EDITORIAL_PERF") != "1", reason="requires EDITORIAL_PERF=1")
def test_check_layout_finishes_dense_book_within_budget(tmp_path, record_property):
    source = write_manuscript(tmp_path, chapters=40)
    subprocess.run(
        [sys.executable, str(SCRIPTS / "build_book.py"), str(source), "--out", str(tmp_path)],
        check=True,
    )
    book = tmp_path / "livro.pdf"
    with pdfplumber.open(book) as pdf:
        pages = len(pdf.pages)
    assert pages >= 40

    start = perf_counter()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_layout.py"), str(book)],
        capture_output=True,
        text=True,
    )
    elapsed = perf_counter() - start
    record_property("check_layout_seconds", elapsed)
    assert result.returncode == 0, result.stderr or result.stdout
    assert f"Páginas: {pages}. Erros: 0." in result.stdout
    assert elapsed < 24, f"check_layout took {elapsed:.2f} s for {pages} pages (budget: 24 s)"
