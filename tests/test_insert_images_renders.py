"""insert_images compõe o livro uma vez com todas as imagens que cabem, não uma vez por imagem."""

import json
from pathlib import Path
import sys

import pdfplumber
from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

import insert_images  # noqa: E402
from build_book import build  # noqa: E402

SHORT = "Texto curto do capítulo que deixa a página quase vazia."
# Capítulos curtos com título pequeno: cada um abre página nova e deixa espaço livre embaixo.
MANUSCRIPT = "title: Livro de teste\ncourse: Curso de teste\nauthors: Ana Silva\nversion: 1.0\n\n" + "".join(
    f"# Cap {n}\n\n{SHORT}\n\n" for n in range(1, 6)
)


def test_all_fitting_images_cost_one_composition(tmp_path, monkeypatch):
    source = tmp_path / "manuscrito.md"
    source.write_text(MANUSCRIPT, encoding="utf-8")
    base = build(str(source), str(tmp_path / "base"))
    chapter_pages = sorted({n for n in base.layout.values()})[-5:]
    images = tmp_path / "imagens"
    images.mkdir()
    for page in chapter_pages:
        Image.new("RGB", (600, 300), "#C88FA0").save(images / f"pagina-{page:02d}.png")

    calls = []
    real = insert_images._render
    monkeypatch.setattr(insert_images, "_render", lambda html, out: calls.append(1) or real(html, out))
    out = tmp_path / "out"
    inserted, warnings = insert_images.insert(str(source), str(images), str(out))

    assert inserted == chapter_pages, warnings
    # garantia da spec, conferida no PDF final: mesma paginação, mesmas âncoras, cada imagem na página dela
    layout = json.loads((out / "layout.json").read_text(encoding="utf-8"))
    assert {k: layout[k] for k in base.layout} == base.layout
    assert all(layout[f"comp-{p:02d}"] == p for p in chapter_pages)
    with pdfplumber.open(out / "livro.pdf") as pdf:
        assert len(pdf.pages) == base.pages
    # uma composição com todas as imagens (a conferência usa a mesma); hoje são 5 tentativas + a final
    assert len(calls) == 1, f"{len(calls)} composições para {len(chapter_pages)} imagens"


def test_breaking_image_is_dropped_and_rest_keeps_pagination(tmp_path, monkeypatch):
    source = tmp_path / "manuscrito.md"
    source.write_text(MANUSCRIPT, encoding="utf-8")
    base = build(str(source), str(tmp_path / "base"))
    chapter_pages = sorted({n for n in base.layout.values()})[-5:]
    images = tmp_path / "imagens"
    images.mkdir()
    for page in chapter_pages:
        Image.new("RGB", (600, 300), "#C88FA0").save(images / f"pagina-{page:02d}.png")
    bad = chapter_pages[2]
    Image.new("RGB", (300, 900), "#C88FA0").save(images / f"pagina-{bad:02d}.png")  # alta: estoura a página
    real = insert_images._cap_pt
    monkeypatch.setattr(insert_images, "_cap_pt", lambda free: 700.0 if free.page == bad else real(free))
    out = tmp_path / "out"
    inserted, warnings = insert_images.insert(str(source), str(images), str(out))

    assert inserted == [p for p in chapter_pages if p != bad]
    assert any(f"página {bad}" in w for w in warnings)
    layout = json.loads((out / "layout.json").read_text(encoding="utf-8"))
    assert {k: layout[k] for k in base.layout} == base.layout
    assert all(layout[f"comp-{p:02d}"] == p for p in inserted) and f"comp-{bad:02d}" not in layout
    with pdfplumber.open(out / "livro.pdf") as pdf:
        assert len(pdf.pages) == base.pages
