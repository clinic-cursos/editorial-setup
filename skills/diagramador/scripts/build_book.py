"""Componha o manuscrito em HTML e PDF com o mapa de blocos por página."""

import argparse
from dataclasses import dataclass
from html import escape
import json
import os
from pathlib import Path
import sys
import re
from urllib.parse import quote

from PIL import Image, UnidentifiedImageError
from weasyprint import HTML

from manuscript import ManuscriptError, cite, parse, walk

try:  # dentro da skill a cópia fica ao lado do script; no repositório, em lib/
    from pdfcheck.rules import load_rules
except ImportError:  # shortcut: a raiz do checkout só serve no repositório de desenvolvimento
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from lib.pdfcheck.rules import load_rules

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LABELS = {
    "ponto-chave": "Ponto-chave", "atencao": "Atenção", "evidencia": "Evidência",
    "estudo-pratica": "Estudo e Prática", "aprofundamento": "Leitura e Aprofundamento",
    "aplicacao-clinica": "Aplicação Clínica", "faq": "Perguntas frequentes",
}
CSS_CLASS = {"aprofundamento": "leitura-aprofundamento"}


@dataclass
class BuildResult:
    html: str
    pdf: str
    layout: dict[str, int]  # id do bloco -> página onde ele começa
    pages: int


def _url(target: Path, out_dir: Path) -> str:
    return quote(os.path.relpath(target, out_dir).replace("\\", "/"))


def _figure_width_pt(image: Path) -> float | None:
    try:
        with Image.open(image) as picture:
            pixels = picture.width
    except UnidentifiedImageError:
        return None  # o WeasyPrint também aceita figuras vetoriais, sem PPI

    origin = image.with_name("origem.json")
    metadata = json.loads(origin.read_text(encoding="utf-8")) if origin.is_file() else {}
    ppi = metadata.get(image.name, {}).get("ppi")
    if ppi is None:
        ppi = load_rules().error_ppi
    return pixels / ppi * 72


def _render(block, base: Path, out_dir: Path, refs: dict[str, str]) -> str:
    e = lambda text: escape(cite(text, refs))  # noqa: E731
    if block.type == "heading":
        return f'<h{block.level} id="{block.id}">{e(block.text)}</h{block.level}>'
    if block.type == "paragraph":
        return f'<p id="{block.id}">{e(block.text)}</p>'
    if block.type == "list":
        tag = "ol" if block.ordered else "ul"
        items = "".join(f"<li>{e(i)}</li>" for i in block.items)
        # o WeasyPrint ignora o atributo start; o counter-reset move o marcador
        start = f' start="{block.start}" style="counter-reset: list-item {block.start - 1}"' if block.ordered and block.start != 1 else ""
        return f'<{tag} id="{block.id}"{start}>{items}</{tag}>'
    if block.type == "box":
        css = CSS_CLASS.get(block.kind, block.kind)
        inner = "".join(_render(c, base, out_dir, refs) for c in block.children)
        if block.kind == "faq":
            inner += "<dl>" + "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in block.entries) + "</dl>"
        return f'<div class="{css}" id="{block.id}"><p class="rotulo">{LABELS[block.kind]}</p>{inner}</div>'
    if block.type == "figure":
        image = base / block.src
        if not image.is_file():
            raise ManuscriptError(f"figura {block.fig_id}: arquivo {block.src} não encontrado ao lado do manuscrito")
        width = _figure_width_pt(image)
        style = f' style="width:{width:.8f}pt"' if width is not None else ""
        return (f'<figure id="{block.id}"><img src="{_url(image, out_dir)}" alt="{e(block.text)}"{style}>'
                f'<p class="legenda">{e(block.text)}</p></figure>')
    entries = "".join(f'<li class="referencia">{escape(d)}</li>' for _, d in block.entries)
    return f'<ul id="{block.id}" class="referencias">{entries}</ul>'


def _compose(manuscript, base: Path, out_dir: Path) -> str:
    meta = manuscript.meta
    toc, body, open_chapter = [], [], False
    for block in manuscript.blocks:
        if block.type == "heading" and block.level == 1:
            body.append("</section>" if open_chapter else "")
            body.append('<section class="capitulo">')
            open_chapter = True
        if block.type == "heading" and block.level <= 2:
            css = ' class="nivel-1"' if block.level == 1 else ""
            toc.append(f'<li{css}><a href="#{block.id}">{escape(cite(block.text, manuscript.refs))}</a></li>')
        body.append(_render(block, base, out_dir, manuscript.refs))
    body.append("</section>" if open_chapter else "")
    authors = [a.strip() for a in meta["authors"].split(",")]
    fields = {
        "TITULO": escape(meta["title"]),
        "COLECAO": escape(meta["course"]),
        "SUBTITULO": "",
        "AUTORES": "<br>".join(map(escape, authors)),
        "EXPEDIENTE": (f'<p class="rotulo">Autores</p><p>{escape(", ".join(authors))}</p>'
                       f'<p class="rotulo">Versão</p><p>{escape(meta["version"])}</p>'),
        "SUMARIO": "<ol>" + "".join(toc) + "</ol>",
        "CONTEUDO": "\n".join(body),
    }
    page = (ASSETS / "livro.html").read_text(encoding="utf-8")
    page = page.replace('href="livro.css"', f'href="{_url(ASSETS / "livro.css", out_dir)}"')
    # uma passada só: texto do manuscrito que pareça marcador não é reprocessado
    return re.sub(r"\{\{(\w+)\}\}", lambda m: fields.get(m[1], m[0]), page)


def build(manuscript_path: str, out_dir: str) -> BuildResult:
    source = Path(manuscript_path)
    out = Path(out_dir)
    manuscript = parse(source.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    html = out / "livro.html"
    html.write_text(_compose(manuscript, source.resolve().parent, out.resolve()), encoding="utf-8")
    document = HTML(filename=str(html)).render()
    layout: dict[str, int] = {}
    for number, page in enumerate(document.pages, 1):
        for anchor in page.anchors:
            layout.setdefault(anchor, number)
    ids = [b.id for b in walk(manuscript.blocks)]
    missing = [i for i in ids if i not in layout]
    if missing:
        raise RuntimeError(f"blocos sem página no PDF: {', '.join(missing)}")
    layout = {i: layout[i] for i in ids}
    pdf = out / "livro.pdf"
    document.write_pdf(str(pdf))
    (out / "layout.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
    return BuildResult(str(html), str(pdf), layout, len(document.pages))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Componha o manuscrito em livro.html, livro.pdf e layout.json.")
    parser.add_argument("manuscript")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        result = build(args.manuscript, args.out)
    except OSError as error:
        print(f"Não foi possível ler ou gravar: {error}", file=sys.stderr)
        return 2
    except ManuscriptError as error:
        print(f"Manuscrito fora da convenção: {error}", file=sys.stderr)
        return 1
    print(f"{result.pdf}: {result.pages} páginas, {len(result.layout)} blocos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
