"""Checagens de PDF por página. Cada uma recebe (pdf, rules) e devolve list[Finding]."""

import re

from .model import Finding
from .rules import Rules

MM = 72 / 25.4
_SUBSET = re.compile(r"^[A-Z]{6}\+")
_MIN_PARAGRAPH = 100  # caracteres
_PAGE_TOLERANCE = 1.0  # pt
_GAP = 15.0  # pt: pares de letras mais próximos que isso formam a mesma região de sobreposição


def _lines(page):
    # dedupe_chars: negrito simulado (letra desenhada duas vezes no mesmo lugar) não conta
    return page.dedupe_chars().extract_text_lines(y_tolerance=1, return_chars=False)


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
    allowed = [" ".join(a.split()).casefold() for a in rules.allowed_repeats]
    seen: dict[int, tuple[int, int]] = {}  # hash -> (página, posição) da primeira ocorrência
    out = []
    for page in pdf.pages:
        text = " ".join(" ".join(l["text"] for l in _lines(page)).split()).casefold()
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
