"""Converta um PDF já composto para o formato de manuscrito da Clinic Editora (melhor tentativa)."""

import argparse
from collections import Counter
from os.path import relpath
from pathlib import Path
import json
import re
import sys
import unicodedata

import pdfplumber
from pypdf import PdfReader

# Mesma faixa de cabeçalho e rodapé do text_fidelity.py.
HEADER_FRACTION, FOOTER_FRACTION = 0.07, 0.93
PARAGRAPH_GAP = 2.0  # salto entre linhas, em corpos de fonte, que abre outro parágrafo
# até 3 dígitos: com mais, um ano ("2024. ") seria lido como marcador de lista
LIST_ITEM = re.compile(r"(?:(\d{1,3})\s*(?:—|–|-|\.|\))|[•▪●])\s+(?=\S)")
PLACEHOLDER = "A preencher"
REFERENCES_TITLE = re.compile(r"refer[eê]ncias( bibliogr[aá]ficas)?", re.IGNORECASE)
MIN_GUTTER = 0.04  # largura mínima do vão entre colunas, em fração da página
MIN_COLUMN_WORDS = 12
REFERENCE_GAP = 1.7  # salto entre linhas, em corpos de fonte, que abre outra referência


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


def gutter(page, max_size=None):
    """x do meio do vão vertical largo e vazio entre dois grupos de texto, ou None.

    Com `max_size`, ignora as palavras maiores (títulos que atravessam o vão)."""
    top, bottom = page.height * HEADER_FRACTION, page.height * FOOTER_FRACTION
    words = [
        w for w in page.extract_words(extra_attrs=["size"])
        if w["top"] >= top and w["bottom"] <= bottom and (max_size is None or w["size"] <= max_size)
    ]
    gaps, edge = [], 0.0
    for word in sorted(words, key=lambda w: w["x0"]):
        mid = (edge + word["x0"]) / 2
        if word["x0"] - edge >= page.width * MIN_GUTTER and 0.3 * page.width <= mid <= 0.7 * page.width:
            gaps.append((word["x0"] - edge, mid))
        edge = max(edge, word["x1"])
    if not gaps:
        return None
    mid = max(gaps)[1]
    left = sum(w["x1"] <= mid for w in words)
    return mid if min(left, len(words) - left) >= MIN_COLUMN_WORDS else None


def page_items(page, body, images_dir, output, figures, warnings, number):
    """(top, bloco) da página, na ordem de leitura."""
    height = page.height
    items = []
    split = gutter(page)
    wide = []  # linhas de título que atravessam o vão; saem antes das colunas
    if split is not None:
        warnings.append(f"página {number}: duas colunas, lidas coluna a coluna")
    elif (split := gutter(page, body * 1.15)) is not None:
        warnings.append(f"página {number}: possíveis duas colunas com título largo; verifique a ordem do texto desta página")
        wide = [
            line for line in page.extract_text_lines(return_chars=True)
            if line["chars"][0]["size"] > body * 1.15 and line["x0"] < split < line["x1"]
            and height * HEADER_FRACTION <= line["top"] and line["bottom"] <= height * FOOTER_FRACTION
        ]
        items.extend((-1, line["top"], "line", line) for line in wide)
    columns = [page] if split is None else [page.crop((0, 0, split, height)), page.crop((split, 0, page.width, height))]
    for column, region in enumerate(columns):
        for line in region.extract_text_lines(return_chars=True):
            if line["top"] < height * HEADER_FRACTION or line["bottom"] > height * FOOTER_FRACTION:
                continue
            if any(abs(line["top"] - w["top"]) < 2 for w in wide):
                continue  # pedaço do título largo, já emitido inteiro
            items.append((column, line["top"], "line", line))
    if page.find_tables():
        warnings.append(f"página {number}: tabela convertida em parágrafos")
    source = figures["reader"].pages[number - 1]
    source_images = source.images
    by_object, inline_paths = {}, []
    # Os nomes de XObject podem se repetir entre Forms. Indexe pelo objeto sem converter os XObjects.
    for path in source_images.keys():
        if isinstance(path, str) and path.startswith("~"):
            inline_paths.append(path)
            continue
        xobject = source
        for name in [path] if isinstance(path, str) else path:
            xobject = xobject["/Resources"]["/XObject"][name]
        reference = xobject.indirect_reference
        if reference is None:
            inline_paths.append(path)
        else:
            by_object.setdefault(reference.idnum, path)
    inline = iter(inline_paths)
    for placed in page.images:
        objid = placed["stream"].objid
        path = by_object.get(objid) if objid is not None else next(inline, None)
        if path is None:
            warnings.append(f"página {number}: imagem sem dados extraíveis ignorada")
            continue
        figures["count"] += 1
        fig_id = f"fig-{figures['count']}"
        key = objid if objid is not None else (number, placed["name"])
        if key not in figures["saved"]:  # imagem reutilizada é convertida e gravada uma vez só
            image = source_images[path]
            filename = images_dir / f"{fig_id}{Path(image.name).suffix or '.png'}"
            figures["saved"][key] = filename
            figures["files"].append((filename, image.data))
        pixels = tuple(placed["srcsize"])
        ppi = round(min(pixels[0] / (placed["x1"] - placed["x0"]), pixels[1] / (placed["bottom"] - placed["top"])) * 72, 1)
        entry = figures["origin"].setdefault(figures["saved"][key].name, {"pixels": list(pixels), "ppi": ppi})
        entry["ppi"] = max(entry["ppi"], ppi)  # imagem reutilizada: vale o maior tamanho, o mais exigente
        relative = Path(relpath(figures["saved"][key], output.parent)).as_posix()
        column = int(split is not None and (placed["x0"] + placed["x1"]) / 2 > split)
        items.append((column, placed["top"], "figure", f"![]({relative}){{#{fig_id}}}"))
    return [item[1:] for item in sorted(items, key=lambda item: item[:2])]


def render(source, output, images_dir):
    warnings, blocks, list_items, references, in_references, joined = [], [], [], [], False, False
    figures = {"count": 0, "files": [], "saved": {}, "origin": {}, "reader": PdfReader(str(source))}
    with pdfplumber.open(source) as pdf:
        body = body_size(pdf.pages)
        if not body:
            raise ValueError("o PDF não tem texto extraível (talvez seja escaneado)")
        info = pdf.metadata or {}
        for number, page in enumerate(pdf.pages, 1):
            previous = None  # (tipo, top, tamanho) da linha anterior
            for top, kind, payload in page_items(page, body, images_dir, output, figures, warnings, number):
                if previous and top < previous[1]:  # voltou ao topo: outra coluna
                    previous = None
                if kind == "figure":
                    in_references = False
                    flush(blocks, list_items)
                    blocks.append(payload)
                    previous = None
                    continue
                tag = classify(payload, body)
                text = payload["text"].strip()
                size = payload["chars"][0]["size"]
                if in_references and tag in ("p", "li"):  # bibliografia: uma entrada por referência
                    marker = LIST_ITEM.match(text) if tag == "li" else None
                    if previous and top - previous[1] <= REFERENCE_GAP * size and not marker and references:
                        references[-1] += " " + text
                        joined = True
                    else:
                        references.append(text[marker.end():] if marker else text)
                    previous = (tag, top, size)
                    continue
                if tag in ("#", "##") and REFERENCES_TITLE.fullmatch(text):
                    flush(blocks, list_items)
                    in_references = True
                    previous = None
                    continue
                if tag in ("#", "##"):
                    in_references = False
                close = previous and top - previous[1] <= PARAGRAPH_GAP * size
                joins = close and previous[0] == tag
                if tag == "li":
                    marker = LIST_ITEM.match(text)
                    mark = f"{int(marker[1])}. " if marker[1] else "- "  # mantém o número e o tipo da origem
                    if list_items and list_items[-1].startswith("- ") != (not marker[1]):
                        flush(blocks, list_items)
                    list_items.append(mark + text[marker.end():])
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
    if joined:
        # shortcut: referências coladas sem salto entre entradas ficam numa só; só avisa, trocar por recuo ou marcador
        warnings.append("verifique a separação das referências: entradas com mais de uma linha foram unidas")
    if references:  # o leitor exige as referências no fim do manuscrito
        taken = set()
        blocks.append("## Referências")
        blocks.append("\n".join(f"- [@{reference_key(r, taken)}] {r}" for r in references))
    meta = {
        "title": (info.get("Title") or source.stem).strip(),
        "course": (info.get("Subject") or "").strip() or PLACEHOLDER,
        "authors": (info.get("Author") or "").strip() or PLACEHOLDER,
        "version": PLACEHOLDER,
    }
    if PLACEHOLDER in meta.values():
        warnings.append(f"metadados ausentes no PDF: preencha os campos «{PLACEHOLDER}» do manuscrito")
    header = "\n".join(f"{key}: {' '.join(value.split())}" for key, value in meta.items())
    # origem.json: tamanho e ppi de cada imagem no PDF de entrada; o check_layout.py usa para achar imagem herdada ampliada
    origin = json.dumps(figures["origin"], indent=2).encode()
    return "\n\n".join([header, *blocks]) + "\n", figures["files"] + [(images_dir / "origem.json", origin)], warnings


def reference_key(entry, taken):
    """Chave a partir do sobrenome (primeira palavra) e do primeiro ano da entrada."""
    word = re.match(r"[^\W\d_]+", entry)
    name = unicodedata.normalize("NFKD", word[0]).encode("ascii", "ignore").decode().lower() if word else ""
    year = re.search(r"\b(?:19|20)\d\d\b", entry)
    key = (name or "ref") + (year[0] if year else "")
    unique, suffix = key, 1
    while unique in taken:
        suffix += 1
        unique = f"{key}-{suffix}"
    taken.add(unique)
    return unique


def flush(blocks, list_items):
    if list_items:
        blocks.append("\n".join(list_items))
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
    if re.search(r"\s", relpath(images, output.parent)):  # a sintaxe de figura do manuscrito não aceita espaço em branco
        parser.error(f"a pasta de imagens {args.images} tem espaço em branco no caminho: use um nome de pasta sem espaços")
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
