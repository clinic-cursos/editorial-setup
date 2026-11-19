"""Converta um PDF já composto para o formato de manuscrito da Clinic Editora (melhor tentativa)."""

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from os.path import relpath
from pathlib import Path
import json
from math import isfinite
import re
import sys
import unicodedata

import pdfplumber
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdffont import PDFType3Font
from pdfminer.pdftypes import resolve_all, stream_value
from pdfminer.utils import MATRIX_IDENTITY, apply_matrix_pt, apply_matrix_rect, get_bound
from pdfplumber.page import PDFPageAggregatorWithMarkedContent, Page
from pypdf import PdfReader
from pypdf.errors import PyPdfError

HEADER_FRACTION, FOOTER_FRACTION = 0.07, 0.93
PARAGRAPH_GAP = 2.0  # salto entre linhas, em corpos de fonte, que abre outro parágrafo
# até 3 dígitos: com mais, um ano ("2024. ") seria lido como marcador de lista
LIST_ITEM = re.compile(r"(?:(\d{1,3})\s*(?:—|–|-|\.|\))|[•▪●])\s+(?=\S)")
PLACEHOLDER = "A preencher"
REFERENCES_TITLE = re.compile(r"refer[eê]ncias( bibliogr[aá]ficas)?", re.IGNORECASE)
MIN_GUTTER = 0.04  # largura mínima do vão entre colunas, em fração da página
MIN_COLUMN_WORDS = 12
REFERENCE_GAP = 1.7  # salto entre linhas, em corpos de fonte, que abre outra referência
TOC_TITLE = re.compile(r"sum[áa]rio(?:\s*\(continua(?:ção)?\))?")  # mesmo padrão de check_toc
TOC_ENTRY = re.compile(r"(?P<title>.+?)(?:(?:[.·…]\s*){2,}|…\s*|\s+)[0-9]+")
CLIP_TOLERANCE = 0.02


def intersect_boxes(first, second):
    return (max(first[0], second[0]), max(first[1], second[1]),
            min(first[2], second[2]), min(first[3], second[3]))


def separated(box):
    x0, y0, x1, y1 = box
    return x0 > x1 + CLIP_TOLERANCE or y0 > y1 + CLIP_TOLERANCE


class ClipPath(list):
    def __init__(self, interpreter):
        super().__init__()
        self.interpreter = interpreter
        self.matrices = []

    def append(self, segment):
        super().append(segment)
        # The path is built in device space, even if cm or Q changes the matrix.
        self.matrices.append(self.interpreter.ctm)

    def bounds(self):
        points = [
            apply_matrix_pt(matrix, (x, y))
            for (_, *coords), matrix in zip(self, self.matrices)
            for x, y in zip(coords[::2], coords[1::2])
        ]
        if not points or not all(isfinite(value) for point in points for value in point):
            return None, False
        # Bezier control points enclose the curve. Concavity, holes and rotation
        # can leave gaps inside that outer box, so report an ambiguous overlap.
        rectangle = (
            "".join(segment[0] for segment in self) in ("mlll", "mlllh", "mllll", "mllllh")
            and (len(points) == 4 or points[0] == points[-1])
            and len(set(points)) == 4
            and all((x0 == x1) != (y0 == y1)
                    for (x0, y0), (x1, y1) in zip(points[:4], points[1:4] + points[:1]))
        )
        return get_bound(points), rectangle


class ClipInterpreter(PDFPageInterpreter):
    @property
    def curpath(self):
        return self._path

    @curpath.setter
    def curpath(self, _):
        # pdfminer clears curpath on every path-ending operator, including n.
        if self.pending_clip:
            self.narrow_clip(*self._path.bounds())
            self.pending_clip = False
        self._path = ClipPath(self)

    def narrow_clip(self, bounds, exact):
        current, current_exact = self.device.clip
        if bounds is not None:
            current = bounds if current is None else intersect_boxes(current, bounds)
        self.device.clip = current, current_exact and exact

    def clip_box(self, box, ctm):
        if not box or len(box) != 4 or not all(isinstance(v, (int, float)) and isfinite(v) for v in box):
            self.narrow_clip(None, False)
            return
        a, b, c, d, _, _ = ctm
        self.narrow_clip(apply_matrix_rect(ctm, box), (b == c == 0) or (a == d == 0))

    def process_page(self, page):
        self.page_boxes = (page.mediabox, page.cropbox)
        super().process_page(page)

    def render_contents(self, resources, streams, ctm=MATRIX_IDENTITY):
        self.pending_clip = False
        boxes = getattr(self, "page_boxes", None)
        if boxes is None:
            # The base interpreter only recurses here for a Form XObject.
            boxes = (resolve_all(stream_value(streams[0])["BBox"]),)
        for box in boxes:
            self.clip_box(box, ctm)
        super().render_contents(resources, streams, ctm)

    def get_current_state(self):
        return super().get_current_state(), self.device.clip

    def set_current_state(self, state):
        graphics, self.device.clip = state
        super().set_current_state(graphics)

    def do_W(self):
        self.pending_clip = True

    do_W_a = do_W

    def do_F(self):
        # The obsolete fill operator still ends the path.
        self.do_n()

    def do_Do(self, xobjid):
        clip = self.device.clip
        try:
            super().do_Do(xobjid)
        finally:
            self.device.clip = clip
            self.device.set_ctm(self.ctm)


class ClipAggregator(PDFPageAggregatorWithMarkedContent):
    clip = (None, True)

    def status(self, box, proven=True):
        bounds, exact = self.clip
        if bounds is not None:
            overlap = intersect_boxes(bounds, box)
            if separated(bounds) or (proven and separated(overlap)):
                return "hidden"
            if overlap != box or not proven:
                return "review"
        return "visible" if exact else "review"

    def render_string(self, textstate, seq, ncs, graphicstate):
        self.stroked = textstate.render in (1, 2, 5, 6)
        super().render_string(textstate, seq, ncs, graphicstate)

    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate):
        advance = super().render_char(matrix, font, fontsize, scaling, rise, cid, ncs, graphicstate)
        char = self.cur_item._objs[-1]
        x0, y0, x1, y1 = font.bbox
        # Advance boxes can miss ink overhangs. Enclose the font's ink bounds
        # as well, or retain glyphs whose geometry cannot be established here.
        proven = (not self.stroked and not font.is_vertical() and not isinstance(font, PDFType3Font)
                  and x0 < x1 and y0 < y1 and all(map(isfinite, font.bbox)))
        box = char.bbox
        if proven:
            sx, sy = fontsize * scaling * font.hscale, fontsize * font.vscale
            ink = apply_matrix_rect(matrix, (x0 * sx, y0 * sy + rise, x1 * sx, y1 * sy + rise))
            box = (min(box[0], ink[0]), min(box[1], ink[1]), max(box[2], ink[2]), max(box[3], ink[3]))
        status = self.status(box, proven)
        if status == "hidden":
            # Keep the advance so subsequent glyphs retain their positions.
            self.cur_item._objs.pop()
        else:
            char.clip_status = status
        return advance

    def render_image(self, name, stream):
        super().render_image(name, stream)
        image = self.cur_item._objs[-1]
        image.clip_status = self.status(image.bbox)


class ClippedPage(Page):
    @property
    def layout(self):
        if not hasattr(self, "_layout"):
            device = ClipAggregator(self.pdf.rsrcmgr, pageno=self.page_number, laparams=self.pdf.laparams)
            ClipInterpreter(self.pdf.rsrcmgr, device).process_page(self.page_obj)
            self._layout = device.get_result()
        return self._layout

    def process_object(self, obj):
        result = super().process_object(obj)
        if (status := getattr(obj, "clip_status", "visible")) != "visible":
            result["clip_status"] = status
        return result


@contextmanager
def visible_pages(pdf):
    pages = [ClippedPage(pdf, page.page_obj, page.page_number, page.initial_doctop) for page in pdf.pages]
    try:
        yield pages
    finally:
        for page in pages:
            page.close()


def normalize_heading(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def toc_pages(pages, body):
    """Retorna páginas candidatas com somente os caracteres das entradas confirmadas removidos."""
    candidates, headings = {}, defaultdict(set)
    for number, page in enumerate(pages, 1):
        top, bottom = page.height * HEADER_FRACTION, page.height * FOOTER_FRACTION
        lines = [
            line for line in page.extract_text_lines()
            if top <= line["top"] and line["bottom"] <= bottom and line["text"].strip()
        ]
        if lines and TOC_TITLE.fullmatch(normalize_heading(lines[0]["text"])):
            candidates[number] = lines[1:]
        for title in page_headings(lines, body):
            headings[normalize_heading(title)].add(number)

    filtered = {}
    for number, lines in candidates.items():
        removed, count = set(), 0
        for line in lines:
            entry = TOC_ENTRY.fullmatch(line["text"].strip())
            if entry and headings.get(normalize_heading(entry["title"]), set()) - {number}:
                removed.update(id(char) for char in line["chars"])
                count += 1
        page = pages[number - 1]
        if removed:
            # As linhas do pdfplumber apontam para os mesmos caracteres da página.
            page = page.filter(lambda obj, removed=removed: id(obj) not in removed)
        filtered[number] = (page, count)
    return filtered


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


def page_headings(lines, body):
    titles, previous = [], None
    for line in lines:
        tag = classify(line, body)
        if tag not in ("#", "##"):
            previous = None
            continue
        top, size = line["top"], line["chars"][0]["size"]
        if previous and previous[0] == tag and top - previous[1] <= PARAGRAPH_GAP * size:
            titles[-1] += " " + line["text"].strip()
        else:
            titles.append(line["text"].strip())
        previous = (tag, top)
    return titles


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


def page_lines(page, body, warnings, number):
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
    return items, split


def outline_destinations(reader, entries, depth=0):
    for entry in entries:
        if isinstance(entry, list):
            yield from outline_destinations(reader, entry, depth + 1)
        else:
            yield reader.get_destination_page_number(entry), normalize_heading(entry.title), depth


def title_spans(items, title):
    for start, (column, top, _, line) in enumerate(items):
        text = normalize_heading(line["text"])
        end = start + 1
        while title.startswith(text + " ") and end < len(items):
            next_column, next_top, _, next_line = items[end]
            if next_column != column or next_top - top > PARAGRAPH_GAP * next_line["chars"][0]["size"]:
                break
            text += " " + normalize_heading(next_line["text"])
            top = next_top
            end += 1
        if text == title:
            yield range(start, end)


def outline_layouts(reader, pages, filtered, body, warnings):
    """Usa o índice quando cada capítulo aponta para um único título visível."""
    try:
        destinations = list(outline_destinations(reader, reader.outline))
    except (PyPdfError, AttributeError, KeyError, TypeError, ValueError):
        warnings.append("índice interno ilegível: níveis inferidos pelo tamanho dos glifos")
        return {}
    if not destinations:
        return {}
    titles = defaultdict(dict)
    for index, title, depth in sorted(destinations, key=lambda destination: destination[2]):
        if index is not None and 0 <= index < len(pages) and title:
            titles[index + 1].setdefault(title, depth)
        elif depth == 0:
            warnings.append("índice interno com destino de capítulo inválido: níveis inferidos pelo tamanho dos glifos")
            return {}
    if not any(depth == 0 for _, _, depth in destinations):
        return {}

    layouts = {}
    for number, page_titles in titles.items():
        page = filtered[number][0] if number in filtered else pages[number - 1]
        page_warnings = []
        items, split = page_lines(page, body, page_warnings, number)
        replacements, consumed = {}, set()
        for title, depth in page_titles.items():
            spans = list(title_spans(items, title))
            if len(spans) != 1 or consumed.intersection(spans[0]):
                if depth == 0:
                    warnings.append(f"página {number}: título de capítulo do índice sem correspondência única; níveis inferidos pelo tamanho dos glifos")
                    return {}
                continue
            span = spans[0]
            column, top, kind, line = items[span.start]
            text = " ".join(items[i][3]["text"].strip() for i in span)
            replacements[span.start] = (column, top, kind, {**line, "text": text, "outline_tag": "#" * min(depth + 1, 3)})
            consumed.update(span)
        layouts[number] = (
            [replacements[i] if i in replacements else item
             for i, item in enumerate(items) if i in replacements or i not in consumed],
            split,
            page_warnings,
        )
    return layouts


def page_items(page, body, images_dir, output, figures, warnings, number, layout=None):
    """(top, bloco) da página, na ordem de leitura."""
    if layout is None:
        items, split = page_lines(page, body, warnings, number)
    else:
        items, split, page_warnings = layout
        warnings.extend(page_warnings)
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
        # Inline image keys follow stream order, including hidden occurrences.
        if placed.get("clip_status") == "hidden":
            continue
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
    with pdfplumber.open(source) as pdf, visible_pages(pdf) as pages:
        body = body_size(pages)
        if not body:
            raise ValueError("o PDF não tem texto extraível (talvez seja escaneado)")
        info = pdf.metadata or {}
        filtered = toc_pages(pages, body)
        layouts = outline_layouts(figures["reader"], pages, filtered, body, warnings)
        for number, page in enumerate(pages, 1):
            if any(obj.get("clip_status") == "review" for group in (page.chars, page.images) for obj in group):
                warnings.append(f"página {number}: recorte parcial ou ambíguo; confira o texto e as imagens no original")
            if number in filtered:
                page, count = filtered[number]
                if count:
                    warnings.append(f"página {number}: entradas de sumário confirmadas removidas")
                else:
                    warnings.append(f"página {number}: sumário com texto de corpo, mantido para conferência")
            previous = None  # (tipo, top, tamanho) da linha anterior
            for top, kind, payload in page_items(page, body, images_dir, output, figures, warnings, number, layouts.get(number)):
                if previous and top < previous[1]:  # voltou ao topo: outra coluna
                    previous = None
                if kind == "figure":
                    in_references = False
                    flush(blocks, list_items)
                    blocks.append(payload)
                    previous = None
                    continue
                outline_tag = payload.get("outline_tag")
                tag = outline_tag or classify(payload, body)
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
                if (outline_tag or tag in ("#", "##")) and REFERENCES_TITLE.fullmatch(text):
                    flush(blocks, list_items)
                    in_references = True
                    previous = None
                    continue
                if outline_tag or tag in ("#", "##"):
                    in_references = False
                close = previous and top - previous[1] <= PARAGRAPH_GAP * size
                joins = close and previous[0] == tag and not outline_tag
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
                        marker = "##" if layouts and tag == "#" and not outline_tag else tag
                        blocks.append(text if tag == "p" else f"{marker} {text}")
                previous = None if outline_tag else (tag, top, size)
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
