"""Checagens de PDF e medição de espaço livre por página."""

import re
from collections import defaultdict
from itertools import chain
from math import hypot
from unicodedata import normalize

from pdfplumber.page import LTContainer

from .model import Finding, FreeSpace
from .rules import Rules

MM = 72 / 25.4
_SUBSET = re.compile(r"^[A-Z]{6}\+")
_MIN_PARAGRAPH = 100  # caracteres
_LEADER = re.compile(r"[.·…]{3,}")  # pontilhado do sumário
_PAGE_TOLERANCE = 1.0  # pt
_GAP = 15.0  # pt: pares de letras mais próximos que isso formam a mesma região de sobreposição
_FOLIO = re.compile(r"[0-9]+")
_TOC_HEADING = re.compile(r"sum[áa]rio(?:\s*\(continua(?:ção)?\))?")
_TOC_ENTRY = re.compile(r"(?P<title>.+?)(?P<leader>\s+|[.·…]{2,}|…)\s*(?P<number>[0-9]+)")


def _lines(page, *, return_chars=False):
    # dedupe_chars: negrito simulado (letra desenhada duas vezes no mesmo lugar) não conta
    return page.dedupe_chars().extract_text_lines(y_tolerance=1, return_chars=return_chars)


def _area(c) -> float:
    return max(c["x1"] - c["x0"], 0) * max(c["bottom"] - c["top"], 0)


def _inter(a, b) -> float:
    return max(min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]), 0) * max(min(a["bottom"], b["bottom"]) - max(a["top"], b["top"]), 0)


def check_overlaps(pdf, rules: Rules) -> list[Finding]:
    # Caixas dos caracteres (após dedupe_chars): cruzamento acima de 30% da área do menor.
    # Vizinhos na ordem de leitura (kerning) não contam; pares viram um achado por região.
    out = []
    for page in pdf.pages:
        chars = [c for c in page.dedupe_chars().chars if c["text"].strip() and _area(c) > 0]
        order = sorted(range(len(chars)), key=lambda i: chars[i]["top"])
        regions: list[list] = []  # [x0, top, x1, bottom, pares]
        for n, i in enumerate(order):
            a = chars[i]
            for j in order[n + 1 :]:
                b = chars[j]
                if b["top"] >= a["bottom"]:
                    break
                if abs(i - j) == 1 or _inter(a, b) <= 0.3 * min(_area(a), _area(b)):
                    continue
                box = [min(a["x0"], b["x0"]), min(a["top"], b["top"]), max(a["x1"], b["x1"]), max(a["bottom"], b["bottom"]), 1]
                for r in [r for r in regions if r[0] - _GAP <= box[2] and box[0] <= r[2] + _GAP and r[1] - _GAP <= box[3] and box[1] <= r[3] + _GAP]:
                    regions.remove(r)
                    box = [min(box[0], r[0]), min(box[1], r[1]), max(box[2], r[2]), max(box[3], r[3]), box[4] + r[4]]
                regions.append(box)
        for x0, top, x1, bottom, n_pairs in regions:
            out.append(Finding(page.page_number, "overlap", "error", f"caracteres sobrepostos na região ({n_pairs} par(es))", (x0, top, x1, bottom)))
    return out


def check_safe_zone(pdf, rules: Rules) -> list[Finding]:
    m = rules.safe_zone_mm * MM
    out = []
    for page in pdf.pages:
        bad = [
            w
            for w in page.extract_words()
            if w["x0"] < m - 0.01 or w["top"] < m - 0.01 or w["x1"] > page.width - m + 0.01 or w["bottom"] > page.height - m + 0.01
        ]
        if bad:
            bbox = (min(w["x0"] for w in bad), min(w["top"] for w in bad), max(w["x1"] for w in bad), max(w["bottom"] for w in bad))
            out.append(
                Finding(
                    page.page_number,
                    "outside-safe-zone",
                    "error",
                    f"{len(bad)} palavra(s) a menos de {rules.safe_zone_mm:g} mm da borda, a primeira «{bad[0]['text']}»",
                    bbox,
                )
            )
    return out


def check_duplicates(pdf, rules: Rules) -> list[Finding]:
    # Janela deslizante de _MIN_PARAGRAPH caracteres do texto normalizado da página: acha o
    # trecho repetido mesmo quando título ou entrelinha diferentes mudam o agrupamento em parágrafos.
    allowed = [_LEADER.sub(" ", " ".join(a.split()).casefold()) for a in rules.allowed_repeats]
    seen: dict[int, tuple[int, int]] = {}  # hash -> (página, posição) da primeira ocorrência
    out = []
    pages = _band_lines(pdf, rules)
    running = _running_lines(pages)  # cabeçalho e rodapé corridos não são parágrafo
    for page in pdf.pages:
        kept = (line["text"] for line, _, _ in pages[page.page_number] if id(line) not in running)
        text = _LEADER.sub(" ", " ".join(" ".join(kept).split()).casefold())
        for a in allowed:
            text = text.replace(a, "\x00")  # texto de repetição proposital sai antes da busca
        sources = set()
        for i in range(len(text) - _MIN_PARAGRAPH + 1):
            w = text[i : i + _MIN_PARAGRAPH]
            h = hash(w)
            first = seen.setdefault(h, (page.page_number, i))
            # na mesma página, só vale repetição sem sobreposição das janelas
            if first == (page.page_number, i) or (first[0] == page.page_number and i - first[1] < _MIN_PARAGRAPH):
                continue
            sources.add(first[0])
        for src in sorted(sources):
            where = "na própria página" if src == page.page_number else f"da página {src}"
            out.append(Finding(page.page_number, "duplicate-paragraph", "error", f"trecho de {_MIN_PARAGRAPH}+ caracteres repetido {where}"))
    return out


def check_fonts(pdf, rules: Rules) -> list[Finding]:
    allowed = [a.casefold() for a in rules.allowed_fonts]
    out = []
    for page in pdf.pages:
        names = {c.get("fontname") or "" for c in page.chars}
        for raw in sorted(names):
            name = _SUBSET.sub("", raw)
            if not name or name.casefold() == "unknown":
                out.append(Finding(page.page_number, "font-unnamed", "warning", "fonte sem nome (possível Type3); conferir a mão"))
            elif not any(name.split('-')[0].casefold() == a for a in allowed):
                out.append(Finding(page.page_number, "font-not-allowed", "error", f"fonte fora da marca: {name}"))
    return out


def check_text_layer(pdf, rules: Rules) -> list[Finding]:
    return [
        Finding(p.page_number, "page-without-text", "warning", "página sem camada de texto (imagem, escaneada ou em branco); texto não conferido")
        for p in pdf.pages
        if not p.chars
    ]


def check_page_size(pdf, rules: Rules) -> list[Finding]:
    w, h = rules.page_size_pt
    return [
        Finding(
            p.page_number,
            "page-size",
            "error",
            f"tamanho {p.width:.2f} x {p.height:.2f} pt; esperado {w:.2f} x {h:.2f} pt (A4)",
        )
        for p in pdf.pages
        if abs(p.width - w) > _PAGE_TOLERANCE or abs(p.height - h) > _PAGE_TOLERANCE
    ]


def _placed_images(container):
    for item in container:
        if isinstance(item, LTContainer):
            yield from _placed_images(item)
        elif hasattr(item, "srcsize"):
            # pdfplumber expõe a caixa alinhada aos eixos em page.images.
            # A figura pai preserva a matriz da imagem inteira, mesmo com recorte.
            yield item, container.matrix


def check_images(
    pdf, rules: Rules, origins: dict[tuple[int, int], float] | None = None
) -> list[Finding]:
    """origins: tamanho em pixels de cada imagem herdada -> ppi dela no original.

    Só com a resolução de origem a imagem herdada é aviso, e só se não foi ampliada (95% do ppi original
    ou mais). Sem origem, ou ampliada, segue a regra de imagem nova.
    """
    origins = origins or {}
    out = []
    for page in pdf.pages:
        for image, (a, b, c, d, _, _) in _placed_images(page.layout):
            width, height = hypot(a, b), hypot(c, d)
            pixels_x, pixels_y = image.srcsize
            if min(width, height, pixels_x, pixels_y) <= 0:
                continue
            box = page.process_object(image)
            bbox = (box["x0"], box["top"], box["x1"], box["bottom"])
            ppi = min(pixels_x / width, pixels_y / height) * 72
            if ppi < rules.warning_ppi:
                original = origins.get((pixels_x, pixels_y))
                kept = original is not None and ppi >= 0.95 * original
                severity = "error" if not kept and ppi < rules.error_ppi else "warning"
                detail = f"imagem {image.name} com {ppi:.1f} ppi efetivos"
                out.append(Finding(page.page_number, "image-low-resolution", severity, detail, bbox))

            distortion = abs((width / height) / (pixels_x / pixels_y) - 1)
            if distortion > rules.distortion_tolerance:
                detail = f"imagem {image.name} com {distortion:.1%} de alteração na proporção"
                out.append(Finding(page.page_number, "image-distorted", "error", detail, bbox))
    return out


def _footer_top(page, rules: Rules) -> float:
    return page.bbox[3] - max(page.height * 0.10, rules.safe_zone_mm * MM)


def _printed_number(lines, footer_top: float) -> int | None:
    numbers = [
        line for line in lines if line["top"] >= footer_top and _FOLIO.fullmatch(line["text"])
    ]
    return int(max(numbers, key=lambda line: line["bottom"])["text"]) if numbers else None


def check_page_numbers(pdf, rules: Rules) -> list[Finding]:
    out = []
    expected = None
    if len(pdf.pages) >= 3 and all(
        _printed_number(_lines(page), _footer_top(page, rules)) is None for page in pdf.pages
    ):  # a isenção da capa não vale para um livro sem numeração nenhuma
        return [Finding(1, "page-number", "error", "nenhuma página numerada no rodapé")]
    for page in pdf.pages:
        printed = _printed_number(_lines(page), _footer_top(page, rules))
        if printed is None:
            # antes do primeiro fólio, a falta é do modelo só nas primeiras páginas (capa, expediente, sumário)
            if expected is not None or page.page_number > rules.front_matter_max_pages:
                out.append(Finding(page.page_number, "page-number", "error", "número de página ausente no rodapé"))
        elif expected is not None and printed != expected:
            detail = f"número {printed} no rodapé, esperado {expected}"
            out.append(Finding(page.page_number, "page-number", "error", detail))
        if printed is not None:
            expected = printed + 1
        elif expected is not None:
            expected += 1
    return out


def _normalized(text: str) -> str:
    return " ".join(normalize("NFKC", text).casefold().split())


def check_toc(pdf, rules: Rules) -> list[Finding]:
    entries = []
    title_pages = defaultdict(set)
    printed_pages = {}
    continuing = False
    for page in pdf.pages:
        lines = _lines(page)
        footer_top = _footer_top(page, rules)
        printed_pages[page.page_number] = _printed_number(lines, footer_top)
        body = [line for line in lines if line["top"] < footer_top]
        texts = [_normalized(line["text"]) for line in body]
        heading = next((i for i, text in enumerate(texts) if _TOC_HEADING.fullmatch(text)), None)
        rows = body[heading + 1 :] if heading is not None else body
        matches = [match for line in rows if (match := _TOC_ENTRY.fullmatch(line["text"]))]
        looks_like_toc = bool(matches) and (
            len(matches) == len(rows) or any(m["leader"].strip() for m in matches)
        )
        continuing = heading is not None or (continuing and looks_like_toc)
        if continuing:
            entries.extend(
                (page.page_number, m["title"].rstrip(" .·…"), int(m["number"])) for m in matches
            )
        else:
            body_texts = [line["text"] for line in body]
            for start in range(len(body_texts)):
                for end in range(start + 1, min(start + 3, len(body_texts)) + 1):
                    title = " ".join(body_texts[start:end]).rstrip(" .·…")
                    title_pages[_normalized(title)].add(page.page_number)

    uses_printed_pages = any(number is not None for number in printed_pages.values())
    out = []
    for page, title, declared in entries:
        actual = title_pages.get(_normalized(title), set())
        if uses_printed_pages:
            actual = {printed_pages[p] for p in actual} - {None}
        if declared not in actual:
            location = ", ".join(map(str, sorted(actual))) or "sem página correspondente"
            detail = f"sumário indica {declared} para «{title}», encontrado: {location}"
            out.append(Finding(page, "toc-mismatch", "error", detail))
    return out


def _chapter_opening(page, useful_width: float, rules: Rules) -> bool:
    lines = _lines(page, return_chars=True)
    if not lines:
        return False
    # A caixa do texto aproxima a largura ocupada pelo título no PDF final.
    title = max(lines, key=lambda line: max(char["size"] for char in line["chars"]))
    return (
        title["top"] < page.bbox[1] + page.height / 3
        and title["x1"] - title["x0"] >= useful_width * rules.chapter_title_min_width_fraction
        and max(char["size"] for char in title["chars"]) >= rules.chapter_title_min_pt
    )


def _running_lines(pages: dict) -> set:
    """Ids das linhas de faixa que são texto corrido: fólio em sequência ou linha repetida na mesma altura."""
    band = [(number, line, text) for number, lines in pages.items() for line, text, in_band in lines if in_band]
    total = len(pages)
    offsets = defaultdict(set)  # deslocamento (número impresso - página do PDF) -> páginas
    for number, _, text in band:
        if text.isdecimal():
            offsets[int(text) - number].add(number)
    folio = max(offsets, key=lambda k: len(offsets[k]), default=None)
    folio_is_sequence = folio is not None and len(offsets[folio]) * 2 > total
    running = set()
    for number, line, text in band:
        if text.isdecimal():
            if folio_is_sequence and int(text) - number == folio:
                running.add(id(line))
        elif total >= 3:
            same = {n for n, other, t in band if t == text and abs(other["top"] - line["top"]) <= 2}
            if len(same) * 2 >= total:
                running.add(id(line))
    return running


def _band_lines(pdf, rules: Rules) -> dict:
    """Por página: (linha, texto normalizado, está na faixa de cabeçalho ou rodapé)."""
    pages = {}
    for page in pdf.pages:
        text_top = page.bbox[1] + rules.page_margins_mm["top"] * MM
        bottom = page.bbox[3] - rules.page_margins_mm["bottom"] * MM
        pages[page.page_number] = [(line, _normalized(line["text"]), line["bottom"] <= text_top or line["top"] >= bottom)
                                   for line in _lines(page, return_chars=True)]
    return pages


def free_space(pdf, rules: Rules) -> list[FreeSpace]:
    margin = rules.safe_zone_mm * MM
    out = []
    pages = _band_lines(pdf, rules)
    running = _running_lines(pages)
    for page in pdf.pages:
        x0, y0, x1, y1 = page.bbox
        x0, x1 = x0 + margin, x1 - margin
        text_top = y0 + rules.page_margins_mm["top"] * MM
        bottom = y1 - rules.page_margins_mm["bottom"] * MM
        useful_height = bottom - text_top
        if useful_height <= 0 or x1 <= x0:
            continue
        # sai da conta só o texto corrido das faixas (fólio em sequência e linha repetida na mesma altura);
        # imagem, linha, retângulo e texto de conteúdo contam onde estiverem
        text = (c for line, _, _ in pages[page.page_number] if id(line) not in running for c in line["chars"])
        objects = chain(text, page.images, page.lines, page.rects, page.curves)
        top = max((obj["bottom"] for obj in objects), default=None)
        if top is None:
            continue
        top = max(top, text_top)
        fraction = (bottom - top) / useful_height
        if fraction > rules.free_space_fraction and not _chapter_opening(page, x1 - x0, rules):
            out.append(FreeSpace(page.page_number, x0, top, x1, bottom, fraction))
    return out
