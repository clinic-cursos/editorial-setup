"""Meça quanto do texto do ORIGINAL chega à SAIDA (.md ou .pdf dos dois lados)."""

import argparse
from difflib import SequenceMatcher
from pathlib import Path
import re
import sys
import unicodedata

import pdfplumber

from manuscript import ManuscriptError, parse, walk

THRESHOLD = 0.995
LIGATURES = str.maketrans({"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"})
# Cabeçalho e rodapé do modelo ficam nas margens; o corpo começa a 26 mm e termina a 24 mm do fim.
HEADER_FRACTION, FOOTER_FRACTION = 0.07, 0.93


def _markdown_text(path: str) -> str:
    manuscript = parse(Path(path).read_text(encoding="utf-8"))
    parts = []
    for block in walk(manuscript.blocks):
        parts += [block.text, *block.items, *(f"[@{k}] {d}" for k, d in block.entries)]
    return "\n".join(parts)


def _pdf_text(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        pages = []
        for page in pdf.pages:
            body = page.crop((0, page.height * HEADER_FRACTION, page.width, page.height * FOOTER_FRACTION))
            pages.append(body.extract_text() or "")
    return "\n".join(pages)


def _tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).translate(LIGATURES).replace("­", "")
    text = re.sub(r"(\w)-\s+(?=\w)", r"\1", text)  # hífen de fim de linha
    return [w for w in (t.replace("-", "") for t in text.split()) if w]


def fidelity(original: str, output: str) -> float:
    """Fração dos caracteres do original que aparecem, na mesma ordem, na saída."""
    read = lambda p: (_pdf_text if p.lower().endswith(".pdf") else _markdown_text)(p)  # noqa: E731
    a, b = _tokens(read(original)), _tokens(read(output))
    total = sum(map(len, a))
    if not total:
        raise ValueError(f"{original}: sem texto para comparar")
    matcher = SequenceMatcher(None, a, b, autojunk=False)
    matched = sum(len(w) for m in matcher.get_matching_blocks() for w in a[m.a : m.a + m.size])
    return matched / total


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Fidelidade do texto entre ORIGINAL e SAIDA (.md ou .pdf).")
    parser.add_argument("original")
    parser.add_argument("output")
    args = parser.parse_args(argv)
    try:
        ratio = fidelity(args.original, args.output)
    except (OSError, ValueError, ManuscriptError) as error:
        print(f"Não foi possível comparar: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # pdfplumber levanta tipos próprios em PDF ilegível
        print(f"Arquivo ilegível: {error}", file=sys.stderr)
        return 2
    print(f"{ratio:.4f}")
    return 0 if ratio >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
