"""Meça a fidelidade do texto da SAIDA ao ORIGINAL nos dois sentidos (.md ou .pdf dos dois lados)."""

import argparse
from difflib import SequenceMatcher
from pathlib import Path
import re
import sys
import unicodedata

import pdfplumber

from build_book import LABELS
from extract_pdf import HEADER_FRACTION, FOOTER_FRACTION, toc_page_kind
from manuscript import ManuscriptError, cite, parse

THRESHOLD = 0.995
LIGATURES = str.maketrans({"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"})
LEADER = re.compile(r"(?m)(?:\s*\.){4,}\s*\d+\s*$")  # pontilhado e página do sumário

# Estilo de numeração de lista é formatação ("01 — x" no livro, "1. x" no manuscrito): vira "1. ", sem perder o valor.
# Exige espaço depois. Traço só é marcador se o próximo caractere não é dígito ("5 - 10 U" é intervalo); "0.5 mL" não casa.
LIST_MARKER = re.compile(r"(?m)^[ \t]*(?:(\d{1,3})(?:[.)][ \t]+|[ \t]+[-–—][ \t]+(?!\d))|•[ \t]+)")


def _canonical_markers(text: str) -> str:
    # Mantém o valor de propósito: item renumerado (01 contra 02) continua sendo diferença; a bolinha não tem valor e sai.
    return LIST_MARKER.sub(lambda m: f"{int(m[1])}. " if m[1] else "", text)


def _markdown_text(path: str) -> str:
    """Texto do manuscrito, com as citações renderizadas."""
    manuscript = parse(Path(path).read_text(encoding="utf-8"))
    parts: list[str] = []

    def emit(block):
        if block.type == "list":
            parts.extend(f"{n}. {i}" if block.ordered else f"• {i}" for n, i in enumerate(block.items, block.start))
        elif block.type == "references":
            parts.extend(f"• {d}" for _, d in block.entries)  # o modelo põe marcador
        elif block.type != "box":
            parts.append(block.text)
        for child in block.children:  # no faq a introdução vem antes das perguntas
            emit(child)
        if block.kind == "faq":
            parts.extend(f"{q} {a}" for q, a in block.entries)

    for block in manuscript.blocks:
        emit(block)
    return "\n".join(cite(p, manuscript.refs) for p in parts)


def _pdf_pages(path: str, *, drop_toc: bool) -> list[str]:
    with pdfplumber.open(path) as pdf:
        return [
            (page.crop((0, page.height * HEADER_FRACTION, page.width, page.height * FOOTER_FRACTION)).extract_text() or "")
            for page in pdf.pages
            if not drop_toc or toc_page_kind(page) != "toc-only"
        ]


def _pdf_text(path: str, *, template: bool = False) -> str:
    """Descarta o sumário original ou, com `template`, os elementos do modelo."""
    pages = _pdf_pages(path, drop_toc=not template)
    if template and len(pages) > 2 and "expediente" in pages[1].casefold() and "sumário" in pages[2].casefold():
        start = 3
        while start < len(pages) and LEADER.search(pages[start]):
            start += 1  # sumário que passa de uma página
        pages = pages[start:]
        labels = {label.casefold() for label in LABELS.values()}
        pages = ["\n".join(ln for ln in p.splitlines() if ln.strip().casefold() not in labels) for p in pages]
    return "\n".join(pages)


def _normalized(text: str) -> str:
    text = unicodedata.normalize("NFC", text).translate(LIGATURES).replace("\u00ad", "")
    return text.casefold()  # o CSS põe títulos em caixa alta


def _vocabulary(text: str) -> set[str]:
    return set(re.findall(r"\w+(?:-\w+)*", _normalized(text)))


def _tokens(text: str, vocabulary: set[str]) -> list[str]:
    def join(m):  # hífen de quebra de linha; composto só mantém o hífen se o original o tem
        dashed, plain = f"{m[1]}-{m[2]}", m[1] + m[2]
        return dashed if dashed in vocabulary and plain not in vocabulary else plain

    both = {w for w in vocabulary if "-" in w and w.replace("-", "") in vocabulary}  # as duas grafias no original
    text = re.sub(r"(\w+)-\s+(\w+)", join, _normalized(text))  # "5-10" fica
    return re.sub(r"\w+(?:-\w+)+", lambda m: m[0].replace("-", "") if m[0] in both else m[0], text).split()


def _analyze(original: str, output: str) -> tuple[tuple[float, float], list[str], list[str]]:
    is_pdf = lambda p: p.lower().endswith(".pdf")  # noqa: E731
    text_a = _pdf_text(original) if is_pdf(original) else _markdown_text(original)
    if is_pdf(output):  # o modelo só acrescenta texto de desenho a um original em Markdown
        text_b = _pdf_text(output, template=not is_pdf(original))
    else:
        text_b = _markdown_text(output)
    text_a, text_b = _canonical_markers(text_a), _canonical_markers(text_b)
    vocabulary = _vocabulary(text_a)
    a, b = _tokens(text_a, vocabulary), _tokens(text_b, vocabulary)
    total_a, total_b = sum(map(len, a)), sum(map(len, b))
    if not total_a:
        raise ValueError(f"{original}: sem texto para comparar")
    matcher = SequenceMatcher(None, a, b, autojunk=False)
    matched = sum(len(w) for m in matcher.get_matching_blocks() for w in a[m.a : m.a + m.size])
    changes, fragments = [], []
    around = lambda t, x, y: " ".join(t[max(x - 3, 0) : y + 3])  # noqa: E731
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        where = f"original «{around(a, i1, i2)}» / saída «{around(b, j1, j2)}»"
        if any(c.isdigit() for w in a[i1:i2] + b[j1:j2] for c in w):
            changes.append(f"número alterado: {where}")
        else:
            if i2 > i1:
                fragments.append(f"trecho perdido: {where}")
            if j2 > j1:
                fragments.append(f"trecho a mais: {where}")
    return (matched / total_a, matched / total_b if total_b else 1.0), changes, fragments


def fidelity(original: str, output: str) -> tuple[float, float]:
    """(fração do original presente na saída, fração da saída que vem do original), na mesma ordem."""
    return _analyze(original, output)[0]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Fidelidade do texto entre ORIGINAL e SAIDA (.md ou .pdf).")
    parser.add_argument("original")
    parser.add_argument("output")
    args = parser.parse_args(argv)
    try:
        ratios, changes, fragments = _analyze(args.original, args.output)
    except (OSError, ValueError, ManuscriptError) as error:
        print(f"Não foi possível comparar: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # pdfplumber levanta tipos próprios em PDF ilegível
        print(f"Arquivo ilegível: {error}", file=sys.stderr)
        return 2
    print(" ".join(f"{r:.4f}" for r in ratios))
    for change in changes:  # dose, intervalo, concentração ou ano trocados reprovam sozinhos
        print(change, file=sys.stderr)
    if min(ratios) < 1.0:  # a pessoa confere o que mudou, não só as razões
        for fragment in fragments:
            print(fragment, file=sys.stderr)
    return 0 if min(ratios) >= THRESHOLD and not changes else 1


if __name__ == "__main__":
    sys.exit(main())
