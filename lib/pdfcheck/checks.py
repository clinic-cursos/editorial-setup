"""Checagens de PDF por página. Cada uma recebe (pdf, rules) e devolve list[Finding]."""

import re

from .model import Finding
from .rules import Rules

MM = 72 / 25.4
_SUBSET = re.compile(r"^[A-Z]{6}\+")
_MIN_PARAGRAPH = 100  # caracteres
_PAGE_TOLERANCE = 1.0  # pt


def _lines(page, y_tolerance=1):
    # dedupe_chars: negrito simulado (letra desenhada duas vezes no mesmo lugar) não conta
    return page.dedupe_chars().extract_text_lines(y_tolerance=y_tolerance, return_chars=False)


def _crosses(a, b) -> bool:
    return min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]) > 1 and min(a["bottom"], b["bottom"]) - max(a["top"], b["top"]) > 1


def check_overlaps(pdf, rules: Rules) -> list[Finding]:
    out = []
    for page in pdf.pages:
        lines = sorted(_lines(page, y_tolerance=0.1), key=lambda l: l["top"])
        for i, a in enumerate(lines):
            for b in lines[i + 1 :]:
                if b["top"] - a["bottom"] > 1:
                    break
                if _crosses(a, b):
                    out.append(
                        Finding(
                            page.page_number,
                            "overlap",
                            "error",
                            f"linhas sobrepostas: «{a['text'][:40]}» e «{b['text'][:40]}»",
                            (min(a["x0"], b["x0"]), min(a["top"], b["top"]), max(a["x1"], b["x1"]), max(a["bottom"], b["bottom"])),
                        )
                    )
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


def _paragraphs(page) -> list[str]:
    paragraphs, current, prev = [], [], None
    for line in _lines(page):
        if prev is not None and line["top"] - prev["bottom"] > 0.5 * (prev["bottom"] - prev["top"]):
            paragraphs.append(" ".join(current))
            current = []
        current.append(line["text"])
        prev = line
    if current:
        paragraphs.append(" ".join(current))
    return [" ".join(p.split()).casefold() for p in paragraphs]


def check_duplicates(pdf, rules: Rules) -> list[Finding]:
    seen: dict[str, int] = {}
    out = []
    for page in pdf.pages:
        for p in _paragraphs(page):
            if len(p) < _MIN_PARAGRAPH:
                continue
            if p in seen:
                out.append(
                    Finding(page.page_number, "duplicate-paragraph", "error", f"parágrafo repetido da página {seen[p]}: «{p[:50]}...»")
                )
            else:
                seen[p] = page.page_number
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
