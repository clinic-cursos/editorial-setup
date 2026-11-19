"""Meça a fidelidade do texto da SAIDA ao ORIGINAL nos dois sentidos (.md ou .pdf dos dois lados)."""

import argparse
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import re
import sys
import unicodedata

import pdfplumber

from build_book import design_text
from manuscript import ManuscriptError, cite, parse, walk

THRESHOLD = 0.995
LIGATURES = str.maketrans({"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"})
# Cabeçalho e rodapé do modelo ficam nas margens; o corpo começa a 26 mm e termina a 24 mm do fim.
HEADER_FRACTION, FOOTER_FRACTION = 0.07, 0.93
LEADER = re.compile(r"(?:\s*\.){3,}\s*\d+")


def _markdown_text(path: str) -> tuple[str, list[str]]:
    """Texto do manuscrito (com citações renderizadas) e o texto que o modelo acrescenta por desenho."""
    manuscript = parse(Path(path).read_text(encoding="utf-8"))
    parts = []
    for block in walk(manuscript.blocks):
        if block.type == "list":
            parts += [f"{n}. {i}" if block.ordered else f"• {i}" for n, i in enumerate(block.items, 1)]
        elif block.type == "references":
            parts += [f"• {d}" for _, d in block.entries]  # o modelo põe marcador
        elif block.kind == "faq":
            parts += [f"{q} {a}" for q, a in block.entries]
        else:
            parts.append(block.text)
    return "\n".join(cite(p, manuscript.refs) for p in parts), design_text(manuscript)


def _pdf_text(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        pages = []
        for page in pdf.pages:
            body = page.crop((0, page.height * HEADER_FRACTION, page.width, page.height * FOOTER_FRACTION))
            pages.append(body.extract_text() or "")
    return LEADER.sub("", "\n".join(pages))  # pontilhado e página do sumário


def _normalized(text: str) -> str:
    text = unicodedata.normalize("NFC", text).translate(LIGATURES).replace("\u00ad", "")
    return text.casefold()  # o CSS põe títulos em caixa alta


def _vocabulary(text: str) -> set[str]:
    return set(re.findall(r"\w+(?:-\w+)*", _normalized(text)))


def _tokens(text: str, vocabulary: set[str]) -> list[str]:
    def join(m):  # hífen de quebra de linha; composto só mantém o hífen se o original o tem
        dashed, plain = f"{m[1]}-{m[2]}", m[1] + m[2]
        return dashed if dashed in vocabulary and plain not in vocabulary else plain

    return re.sub(r"(\w+)-\s+(\w+)", join, _normalized(text)).split()  # "5-10" fica


def _drop_design(tokens: list[str], design: list[str], vocabulary: set[str]) -> list[str]:
    budget = Counter(_tokens(" ".join(design), vocabulary))
    kept = []
    for token in tokens:
        if budget[token] > 0:
            budget[token] -= 1
        else:
            kept.append(token)
    return kept


def fidelity(original: str, output: str) -> tuple[float, float]:
    """(fração do original presente na saída, fração da saída que vem do original), na mesma ordem."""
    is_pdf = lambda p: p.lower().endswith(".pdf")  # noqa: E731
    design: list[str] = []
    if is_pdf(original):
        text_a = _pdf_text(original)
    else:
        text_a, design = _markdown_text(original)
    if is_pdf(output):
        text_b = _pdf_text(output)
    else:
        text_b = _markdown_text(output)[0]
    vocabulary = _vocabulary(text_a)
    a, b = _tokens(text_a, vocabulary), _tokens(text_b, vocabulary)
    if is_pdf(output) and design:
        b = _drop_design(b, design, vocabulary)
    total_a, total_b = sum(map(len, a)), sum(map(len, b))
    if not total_a:
        raise ValueError(f"{original}: sem texto para comparar")
    matcher = SequenceMatcher(None, a, b, autojunk=False)
    matched = sum(len(w) for m in matcher.get_matching_blocks() for w in a[m.a : m.a + m.size])
    return matched / total_a, (matched / total_b if total_b else 1.0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Fidelidade do texto entre ORIGINAL e SAIDA (.md ou .pdf).")
    parser.add_argument("original")
    parser.add_argument("output")
    args = parser.parse_args(argv)
    try:
        ratios = fidelity(args.original, args.output)
    except (OSError, ValueError, ManuscriptError) as error:
        print(f"Não foi possível comparar: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # pdfplumber levanta tipos próprios em PDF ilegível
        print(f"Arquivo ilegível: {error}", file=sys.stderr)
        return 2
    print(" ".join(f"{r:.4f}" for r in ratios))
    return 0 if min(ratios) >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
