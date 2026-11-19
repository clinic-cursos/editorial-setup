"""Insira as imagens complementares no espaço livre sem mover o texto."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote

import pdfplumber
from PIL import Image
from weasyprint import HTML

from build_book import ASSETS, build
from manuscript import ManuscriptError, parse

try:  # dentro da skill a cópia fica ao lado do script; no repositório, em lib/
    from pdfcheck.checks import free_space
    from pdfcheck.rules import load_rules
except ImportError:  # shortcut: a raiz do checkout só serve no repositório de desenvolvimento
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from lib.pdfcheck.checks import free_space
    from lib.pdfcheck.rules import load_rules

MM = 72 / 25.4
IMAGE_NAME = re.compile(r"pagina-(\d+)\.png")
TOKENS = (ASSETS / "tokens.css").read_text(encoding="utf-8")


def _token_pt(name: str) -> float:
    return float(re.search(rf"--{name}:\s*([\d.]+)mm", TOKENS)[1]) * MM


# A medição pára no fim da última letra; a margem e a entrelinha do bloco vêm depois dela.
BLOCK_GAP_PT = _token_pt("space-3")


def _cap_pt(free) -> float:
    """Altura máxima da imagem: o espaço livre menos a margem do último bloco."""
    return free.bottom - free.top - BLOCK_GAP_PT


def _measure(pdf_path: str) -> list:
    with pdfplumber.open(pdf_path) as pdf:
        return free_space(pdf, load_rules())


def _figure(page: int, image: Path, out: Path, cap: float) -> str:
    src = quote(os.path.relpath(image.resolve(), out.resolve()).replace("\\", "/"))
    return (f'<figure id="comp-{page:02d}" class="complementar" style="margin:0">'
            f'<img src="{src}" alt="Imagem conceitual complementar" '
            f'style="display:block;margin:0 auto;width:auto;max-width:100%;max-height:{cap:.1f}pt"></figure>')


def _render(html: str, out: Path) -> tuple[dict[str, int], int]:
    (out / "livro.html").write_text(html, encoding="utf-8")
    document = HTML(filename=str(out / "livro.html")).render()
    layout: dict[str, int] = {}
    for number, page in enumerate(document.pages, 1):
        for anchor in page.anchors:
            layout.setdefault(anchor, number)
    document.write_pdf(str(out / "livro.pdf"))
    return layout, len(document.pages)


def _place(html: str, plan: dict[int, tuple[str, str]]) -> str:
    """Cada bloco de topo ocupa uma linha do HTML; a figura entra na linha seguinte."""
    lines, after = html.split("\n"), {block_id: fig for block_id, fig in plan.values()}
    out = []
    for line in lines:
        out.append(line)
        m = re.match(r'<\w+ [^>]*?id="(b\d+)"', line)
        if m and m[1] in after:
            out.append(after[m[1]])
    return "\n".join(out)


def insert(manuscript: str, images_dir: str, out_dir: str) -> tuple[list[int], list[str]]:
    """Devolva as páginas com imagem inserida e os avisos."""
    out, warnings = Path(out_dir), []
    base = build(manuscript, out_dir)
    base_html = Path(base.html).read_text(encoding="utf-8")
    top = [b.id for b in parse(Path(manuscript).read_text(encoding="utf-8")).blocks]
    free = {f.page: f for f in _measure(base.pdf)}
    plan: dict[int, tuple[str, str]] = {}  # página -> (bloco de topo, figura em HTML)
    for image in sorted(Path(images_dir).iterdir()):
        m = IMAGE_NAME.fullmatch(image.name)
        if not m:
            continue
        page = int(m[1])
        try:
            with Image.open(image) as picture:
                picture.load()
        except (OSError, SyntaxError):  # Pillow levanta OSError (ou SyntaxError em PNG truncado)
            warnings.append(f"página {page}: {image.name} não abre como imagem; não entrou")
            continue
        starting = [i for i in top if base.layout[i] == page]
        cap = _cap_pt(free[page]) if page in free else 0
        if page not in free:
            warnings.append(f"página {page}: sem espaço livre acima do limite; {image.name} não entrou")
        elif cap <= 0 or not starting:
            warnings.append(f"página {page}: sem bloco que comece nela ou sem altura útil; {image.name} não entrou")
        else:
            plan[page] = (starting[-1], _figure(page, image, out, cap))
    accepted: dict[int, tuple[str, str]] = {}
    for page in sorted(plan):  # uma por vez: a que estoura sai, as seguintes são avaliadas sobre as aceitas
        trial = {**accepted, page: plan[page]}
        layout, pages = _render(_place(base_html, trial), out)
        if layout.get(f"comp-{page:02d}") == page and pages == base.pages \
                and all(layout.get(i) == n for i, n in base.layout.items()):
            accepted = trial
        else:
            warnings.append(f"página {page}: a imagem mudaria a paginação; foi retirada")
    layout, pages = _render(_place(base_html, accepted), out)
    plan = accepted
    (out / "layout.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
    return sorted(plan), warnings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manuscript")
    parser.add_argument("images_dir", help="pasta com pagina-NN.png")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        inserted, warnings = insert(args.manuscript, args.images_dir, args.out)
    except OSError as error:
        print(f"Não foi possível ler ou gravar: {error}", file=sys.stderr)
        return 2
    except ManuscriptError as error:
        print(f"Manuscrito fora da convenção: {error}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"Aviso: {warning}", file=sys.stderr)
    for page in inserted:
        print(f"imagem inserida na página {page}")
    print(f"{Path(args.out) / 'livro.pdf'}: {len(inserted)} imagens inseridas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
