"""Gere as duas páginas da prova de figuras e meça cada imagem nos PDFs."""

from dataclasses import dataclass
import json
from math import cos, pi, sin
from pathlib import Path
import re
import shutil
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pdfplumber
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/diagramador/scripts"))
import build_book
from pdfcheck.rules import load_rules

OUTPUT = ROOT / "docs/medicoes/figuras"


@dataclass(frozen=True)
class Sample:
    name: str
    size: tuple[int, int]
    origin_ppi: int | None
    caption: str


SAMPLES = (
    Sample("rings", (444, 351), 136, "Figura 1. Curvas concêntricas em um original de 444 × 351 px."),
    Sample("mark", (94, 94), None, "Figura 2. Marca de registro de 94 × 94 px."),
    Sample("lines", (600, 400), None, "Figura 3. Feixe de linhas de 600 × 400 px."),
    Sample("plate", (1122, 1402), 300, "Figura 4. Prancha vertical de 1122 × 1402 px."),
)


def draw_sample(sample, palette, path):
    w, h = sample.size
    ink = palette["brand"]
    image = Image.new("RGB", sample.size, palette["tint"])
    draw = ImageDraw.Draw(image)
    if sample.name == "mark":
        draw.ellipse((14, 14, 80, 80), outline=ink, width=6)
        draw.line((47, 4, 47, 90), fill=ink, width=4)
        draw.line((4, 47, 90, 47), fill=ink, width=4)
    elif sample.name == "lines":
        for row in range(31):
            points = [(x, h * (.18 + .016 * row + .12 * sin(x / w * 2 * pi + row / 28)))
                      for x in range(w // 12, w - w // 12)]
            draw.line(points, fill=ink, width=2)
    else:
        # As linhas finas tornam a perda de definição visível na prova ampliada.
        for ring in range(1, 30):
            points = []
            for degree in range(361):
                angle = degree * pi / 180
                radius = ring / 29 * (.32 + .06 * cos(3 * angle + ring / 18))
                points.append((w * (.5 + radius * cos(angle)), h * (.5 + radius * sin(angle))))
            draw.line(points, fill=ink, width=max(1, w // 230))
    image.save(path)


def write_manuscript(folder):
    tokens = (build_book.ASSETS / "tokens.css").read_text(encoding="utf-8")
    palette = dict(re.findall(r"--color-([\w-]+):\s*([^;]+);", tokens))
    blocks = [
        "title: Escala das figuras\ncourse: Prova gráfica\nauthors: Clinic Editora\nversion: 1",
        "# Traço e proporção",
        "Observe as curvas da primeira figura e o espaço que a marca de registro ocupa "
        "na página. As quatro figuras desta prova foram desenhadas para comparar tamanhos de impressão.",
    ]
    origins = {}
    for sample in SAMPLES:
        filename = f"{sample.name}.png"
        draw_sample(sample, palette, folder / filename)
        if sample.origin_ppi:
            origins[filename] = {"pixels": sample.size, "ppi": sample.origin_ppi}
        blocks.append(f"![{sample.caption}]({filename}){{#fig-{sample.name}}}")
    (folder / "origem.json").write_text(json.dumps(origins), encoding="utf-8")
    manuscript = folder / "manuscrito.md"
    manuscript.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    return manuscript


def preview_assets(folder):
    assets = shutil.copytree(build_book.ASSETS, folder / "assets")
    origins = json.loads((folder / "origem.json").read_text(encoding="utf-8"))
    min_ppi = load_rules(ROOT / "shared/rules/graphic-rules.json").error_ppi
    # Só a folha temporária ganha uma largura física por arquivo.
    with (assets / "livro.css").open("a", encoding="utf-8") as css:
        css.write("\nfigure img { width: auto; max-width: 100%; }\n")
        for sample in SAMPLES:
            filename = f"{sample.name}.png"
            ppi = origins.get(filename, {}).get("ppi", min_ppi)
            with Image.open(folder / filename) as image:
                width_pt = image.width * 72 / ppi
            css.write(f'figure img[src$="/{filename}"] {{ width: {width_pt:.8f}pt; }}\n')
    return assets


def measure_and_export(result, variant):
    figures = {}
    with pdfplumber.open(result.pdf) as pdf:
        for page in pdf.pages:
            for image in page.images:
                size = tuple(image["srcsize"])
                ppi = min(size[0] / image["width"], size[1] / image["height"]) * 72
                figures[size] = (page.page_number, image["width"] * 25.4 / 72, ppi)
        if set(figures) != {sample.size for sample in SAMPLES}:
            raise ValueError("O PDF precisa conter os quatro perfis da prova.")
        first_page = figures[SAMPLES[0].size][0]
        print(f"{variant}: {len(pdf.pages)} páginas. PNG da página {first_page}.")
        for sample in SAMPLES:
            number, width_mm, ppi = figures[sample.size]
            print(f"  {sample.name}: pág. {number}, {width_mm:.2f} mm, {ppi:.2f} ppi")
        page = pdf.pages[first_page - 1]
        page.to_image(resolution=150, antialias=True).original.save(OUTPUT / f"{variant}.png")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as tmp:
        folder = Path(tmp)
        manuscript = write_manuscript(folder)
        before = build_book.build(manuscript, folder / "antes")
        with patch.object(build_book, "ASSETS", preview_assets(folder)):
            after = build_book.build(manuscript, folder / "depois")
        measure_and_export(before, "antes")
        measure_and_export(after, "depois")


if __name__ == "__main__":
    main()
