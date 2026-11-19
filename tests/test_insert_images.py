import json
import os
import subprocess
from pathlib import Path
import sys

import pdfplumber
from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

import insert_images  # noqa: E402
from build_book import build  # noqa: E402

PARAGRAPH = "Texto de apoio para ocupar espaço na página do livro de teste. " * 8
MANUSCRIPT = (
    "title: Livro de teste\ncourse: Curso de teste\nauthors: Ana Silva\nversion: 1.0\n\n"
    "# Capítulo\n\n" + "\n\n".join(PARAGRAPH for _ in range(10)) + "\n"
)


def setup(tmp_path, pages=(5,), size=(900, 300)):
    source = tmp_path / "manuscrito.md"
    source.write_text(MANUSCRIPT, encoding="utf-8")
    images = tmp_path / "imagens"
    images.mkdir()
    for page in pages:
        Image.new("RGB", size, "#C88FA0").save(images / f"pagina-{page:02d}.png")
    return source, images


def pdf_images(pdf_path, page):
    with pdfplumber.open(pdf_path) as pdf:
        return pdf.pages[page - 1].images


def test_insert_keeps_pagination(tmp_path, capsys):
    source, images = setup(tmp_path)
    base = build(str(source), str(tmp_path / "base"))
    out = tmp_path / "out"
    assert insert_images.main([str(source), str(images), "--out", str(out)]) == 0
    layout = json.loads((out / "layout.json").read_text(encoding="utf-8"))
    with pdfplumber.open(out / "livro.pdf") as pdf:
        assert len(pdf.pages) == base.pages
    assert {k: layout[k] for k in base.layout} == base.layout
    assert layout["comp-05"] == 5
    assert len(pdf_images(out / "livro.pdf", 5)) == 1
    assert 'class="complementar"' in (out / "livro.html").read_text(encoding="utf-8")
    assert "página 5" in capsys.readouterr().out


def test_insert_reverts_when_page_breaks(tmp_path, monkeypatch, capsys):
    source, images = setup(tmp_path, size=(300, 900))  # alta: com o limite errado, não cabe
    base = build(str(source), str(tmp_path / "base"))
    monkeypatch.setattr(insert_images, "_cap_pt", lambda free, page_height: 700.0)  # mede errado de propósito
    out = tmp_path / "out"
    assert insert_images.main([str(source), str(images), "--out", str(out)]) == 0
    assert "página 5" in capsys.readouterr().err
    layout = json.loads((out / "layout.json").read_text(encoding="utf-8"))
    assert layout == base.layout
    assert "complementar" not in (out / "livro.html").read_text(encoding="utf-8")
    with pdfplumber.open(out / "livro.pdf") as pdf:
        assert len(pdf.pages) == base.pages
    assert pdf_images(out / "livro.pdf", 5) == []


def test_insert_skips_image_for_page_without_free_space(tmp_path, capsys):
    source, images = setup(tmp_path, pages=(4,))  # a página 4 está cheia
    out = tmp_path / "out"
    assert insert_images.main([str(source), str(images), "--out", str(out)]) == 0
    assert "página 4" in capsys.readouterr().err
    assert "complementar" not in (out / "livro.html").read_text(encoding="utf-8")


def test_insert_caps_tall_image_to_free_space(tmp_path):
    source, images = setup(tmp_path, size=(300, 900))
    out = tmp_path / "out"
    assert insert_images.main([str(source), str(images), "--out", str(out)]) == 0
    layout = json.loads((out / "layout.json").read_text(encoding="utf-8"))
    assert layout["comp-05"] == 5
    image, = pdf_images(out / "livro.pdf", 5)
    assert 0 < image["height"] <= 549.5  # o espaço livre da página 5; sem o limite seria 1362 pt


def test_insert_cli_runs_without_pythonpath():
    run = subprocess.run(
        [sys.executable, str(SCRIPTS / "insert_images.py"), "--help"],
        cwd="/", env={"PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")},
        capture_output=True, text=True,
    )
    assert run.returncode == 0, run.stderr
