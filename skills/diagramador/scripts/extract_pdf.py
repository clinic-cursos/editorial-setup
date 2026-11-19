"""Converta um PDF já composto para o formato de manuscrito da Clinic Editora (melhor tentativa)."""

import argparse
from collections import Counter
from os.path import relpath
from pathlib import Path
import re
import sys

import pdfplumber
from pypdf import PdfReader

# Mesma faixa de cabeçalho e rodapé do text_fidelity.py.
HEADER_FRACTION, FOOTER_FRACTION = 0.07, 0.93
PARAGRAPH_GAP = 2.0  # salto entre linhas, em corpos de fonte, que abre outro parágrafo
LIST_ITEM = re.compile(r"(?:\d+\s*(?:—|–|-|\.|\))|[•▪●])\s+(?=\S)")
PLACEHOLDER = "A preencher"


def is_wine(color):
    """Bordô da identidade: vermelho dominante e escuro."""
    if not isinstance(color, (tuple, list)) or len(color) != 3:
        return False
    r, g, b = color
    return r >= 0.4 and g <= 0.25 and b <= 0.35 and r - max(g, b) >= 0.3


def is_caps(text):
    return any(c.isalpha() for c in text) and text == text.upper()


def body_size(pages):
    sizes = Counter(round(c["size"], 1) for page in pages for c in page.chars if c["text"].strip())
    return sizes.most_common(1)[0][0] if sizes else 0.0


def classify(line, body):
    first = next(c for c in line["chars"] if c["text"].strip())
    ratio = first["size"] / body
    if is_wine(first.get("non_stroking_color")) and is_caps(line["text"]):
        return "###"  # o rótulo vale mesmo quando o tamanho pediria título maior
    if ratio >= 1.6:
        return "#"
    if ratio >= 1.3:
        return "##"
    if ratio >= 1.15:
        return "###"
    return "li" if LIST_ITEM.match(line["text"]) else "p"


def page_items(page, body, images_dir, output, figures, warnings, number):
    """(top, bloco) da página, na ordem de leitura."""
    height = page.height
    items = []
    for line in page.extract_text_lines(return_chars=True):
        if line["top"] < height * HEADER_FRACTION or line["bottom"] > height * FOOTER_FRACTION:
            continue
        items.append((line["top"], "line", line))
    if page.find_tables():
        warnings.append(f"página {number}: tabela convertida em parágrafos")
    # shortcut: assume que pdfplumber e pypdf listam as imagens na mesma ordem; trocar por casamento por nome se falhar
    reader_images = list(figures["reader"].pages[number - 1].images)
    for index, placed in enumerate(page.images):
        if index >= len(reader_images):
            warnings.append(f"página {number}: imagem sem dados extraíveis ignorada")
            continue
        image = reader_images[index]
        figures["count"] += 1
        fig_id = f"fig-{figures['count']}"
        filename = images_dir / f"{fig_id}{Path(image.name).suffix or '.png'}"
        figures["files"].append((filename, image.data))
        relative = Path(relpath(filename, output.parent)).as_posix()
        items.append((placed["top"], "figure", f"![]({relative}){{#{fig_id}}}"))
    return sorted(items, key=lambda item: item[0])


def render(source, output, images_dir):
    warnings, blocks, list_items = [], [], []
    figures = {"count": 0, "files": [], "reader": PdfReader(str(source))}
    with pdfplumber.open(source) as pdf:
        body = body_size(pdf.pages)
        if not body:
            raise ValueError("o PDF não tem texto extraível (talvez seja escaneado)")
        info = pdf.metadata or {}
        for number, page in enumerate(pdf.pages, 1):
            previous = None  # (tipo, top, tamanho) da linha anterior
            for top, kind, payload in page_items(page, body, images_dir, output, figures, warnings, number):
                if kind == "figure":
                    flush(blocks, list_items)
                    blocks.append(payload)
                    previous = None
                    continue
                tag = classify(payload, body)
                text = payload["text"].strip()
                size = payload["chars"][0]["size"]
                close = previous and top - previous[1] <= PARAGRAPH_GAP * size
                joins = close and previous[0] == tag
                if tag == "li":
                    list_items.append(LIST_ITEM.sub("", text, count=1))
                elif tag == "p" and close and previous[0] == "li":
                    list_items[-1] += " " + text
                    tag = "li"
                else:
                    flush(blocks, list_items)
                    if joins and blocks:
                        blocks[-1] += " " + text
                    else:
                        blocks.append(text if tag == "p" else f"{tag} {text}")
                previous = (tag, top, size)
        flush(blocks, list_items)
    meta = {
        "title": (info.get("Title") or source.stem).strip(),
        "course": (info.get("Subject") or "").strip() or PLACEHOLDER,
        "authors": (info.get("Author") or "").strip() or PLACEHOLDER,
        "version": PLACEHOLDER,
    }
    if PLACEHOLDER in meta.values():
        warnings.append(f"metadados ausentes no PDF: preencha os campos «{PLACEHOLDER}» do manuscrito")
    header = "\n".join(f"{key}: {' '.join(value.split())}" for key, value in meta.items())
    return "\n\n".join([header, *blocks]) + "\n", figures["files"], warnings


def flush(blocks, list_items):
    if list_items:
        blocks.append("\n".join(f"{n}. {item}" for n, item in enumerate(list_items, 1)))
        list_items.clear()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", metavar="PDF", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="caminho do manuscrito Markdown")
    parser.add_argument("--images", type=Path, required=True, help="pasta das figuras extraídas")
    args = parser.parse_args()
    output, images = args.out.resolve(), args.images.resolve()
    if not images.is_relative_to(output.parent):  # o leitor do manuscrito rejeita caminho com ".."
        parser.error(f"a pasta de imagens {args.images} precisa ficar dentro da pasta do manuscrito {output.parent}")
    try:
        markdown, figures, warnings = render(args.pdf.resolve(), output, images)
    except Exception as error:  # pdfplumber e pypdf levantam tipos próprios em PDF ilegível
        parser.error(f"não foi possível ler {args.pdf}: {error}")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        images.mkdir(parents=True, exist_ok=True)
        for filename, data in figures:
            filename.write_bytes(data)
        output.write_text(markdown, encoding="utf-8")
    except OSError as error:
        parser.exit(1, f"Não foi possível gravar {output} ou as figuras em {images}: {error}\n")
    for warning in warnings:
        print(f"aviso: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
