"""Render the book sample with the current and logo palettes."""

import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = Path("tests/samples/amostra.html")
ASSETS = Path("skills/diagramador/assets")
OUTPUT = ROOT / "docs/medicoes/paleta"
LOGO_COLORS = {
    "--color-brand": "#9C4C48",
    "--color-heading": "#6E2F2C",
    "--color-text": "#404040",
    "--color-muted": "#6E6F73",
    "--color-header": "#6E6F73",
    "--color-tint": "#F4ECEA",
    "--color-rule": "#B68B85",
}
SAMPLE_PAGES = (
    ("cap1", "abertura-capitulo", "Abertura de capítulo"),
    ("sec-texto", "texto-com-caixas", "Texto com caixas"),
    ("sec-imagem", "imagem-com-legenda", "Imagem com legenda"),
)


def apply_logo_colors(path: Path) -> dict[str, str]:
    css = path.read_text(encoding="utf-8")
    original_colors = {}
    for token, color in LOGO_COLORS.items():
        matches = list(re.finditer(rf"(?m)^[ \t]*{token}:[ \t]*(#[0-9a-fA-F]{{6}})[ \t]*;", css))
        if len(matches) != 1:
            raise ValueError(f"Esperava uma declaração hexadecimal para {token} em tokens.css.")
        match = matches[0]
        original_colors[token] = match[1]
        start, end = match.span(1)
        css = css[:start] + color + css[end:]
    path.write_text(css, encoding="utf-8")
    return original_colors


def render_samples(sample: Path, work: Path, palette: str) -> None:
    document = HTML(filename=str(sample)).render()
    pdf = work / f"{palette}.pdf"
    document.write_pdf(pdf)
    for anchor, slug, _ in SAMPLE_PAGES:
        pages = [number for number, page in enumerate(document.pages, 1) if anchor in page.anchors]
        if len(pages) != 1:
            raise ValueError(f"Esperava encontrar a seção {anchor} em uma página da amostra.")
        number = str(pages[0])
        subprocess.run(
            [
                "pdftoppm", "-png", "-r", "80", "-f", number, "-l", number,
                "-singlefile", str(pdf), str(work / f"{palette}-{slug}"),
            ],
            check=True,
        )


def write_comparison(path: Path, original_colors: dict[str, str]) -> None:
    lines = [
        "# Comparação de paletas do livro",
        "",
        "As duas versões usam a mesma amostra sintética, com o mesmo conteúdo, "
        "a mesma tipografia e a mesma diagramação.",
        "",
        "| Página | Paleta atual (bordô) | Paleta do logo (vinho) |",
        "| --- | --- | --- |",
    ]
    for _, slug, title in SAMPLE_PAGES:
        lines.append(
            f"| {title} | ![{title} na paleta atual](atual-{slug}.png) "
            f"| ![{title} na paleta do logo](logo-{slug}.png) |"
        )
    lines.extend([
        "",
        "## Cores trocadas",
        "",
        "Cores da seção Identidade visual do [design system da Julie]"
        "(../../fontes/2026-11-19-julie-design-system/design-system-aulas-clinic-cursos.html#identidade).",
        "",
        "| Token | Paleta atual | Paleta do logo |",
        "| --- | --- | --- |",
    ])
    for token, color in LOGO_COLORS.items():
        if original_colors[token].lower() != color.lower():
            lines.append(f"| `{token}` | `{original_colors[token]}` | `{color}` |")
    lines.extend([
        "",
        "O branco do papel e do texto sobre fundos de marca é o mesmo nas duas versões.",
        "",
        "Para recriar as imagens e esta comparação, execute "
        "`uv run --locked python scripts/render_palette_samples.py` na raiz do repositório. "
        "O script usa o `pdftoppm` do Poppler para gerar os PNGs.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    try:
        with TemporaryDirectory(prefix="editorial-palettes-") as directory:
            work = Path(directory)
            sample_copy = work / SAMPLE
            sample_copy.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / SAMPLE, sample_copy)
            shutil.copytree(ROOT / ASSETS, work / ASSETS)
            original_colors = apply_logo_colors(work / ASSETS / "tokens.css")

            render_samples(ROOT / SAMPLE, work, "atual")
            render_samples(sample_copy, work, "logo")
            comparison = work / "comparacao.md"
            write_comparison(comparison, original_colors)

            OUTPUT.mkdir(parents=True, exist_ok=True)
            for image in work.glob("*.png"):
                shutil.copyfile(image, OUTPUT / image.name)
            shutil.copyfile(comparison, OUTPUT / comparison.name)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Falha ao renderizar as amostras de paleta: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
