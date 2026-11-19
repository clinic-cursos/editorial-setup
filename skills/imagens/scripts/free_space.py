"""Liste as páginas de um PDF com espaço livre acima do limite."""

import argparse
import json
from pathlib import Path
import sys

import pdfplumber

from pdfcheck.checks import free_space
from pdfcheck.rules import load_rules

MM = 72 / 25.4


def candidates(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        found = free_space(pdf, load_rules())
    rows = []
    for f in found:
        width, height = (f.x1 - f.x0) / MM, (f.bottom - f.top) / MM
        rows.append({
            "page": f.page, "width_mm": round(width, 1), "height_mm": round(height, 1),
            "ratio": round(width / height, 2), "fraction": round(f.fraction, 3),
        })
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--json", metavar="OUT", help="grava a lista em JSON")
    args = parser.parse_args(argv)
    try:
        rows = candidates(args.pdf)
        if args.json:
            Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as error:  # PDF ilegível ou pasta de saída inválida
        print(f"Não foi possível medir {args.pdf}: {error}", file=sys.stderr)
        return 2
    for r in rows:
        print(f"página {r['page']}: {r['width_mm']} x {r['height_mm']} mm, "
              f"proporção {r['ratio']}:1, {r['fraction']:.0%} da altura útil")
    if not rows:
        print("Nenhuma página acima do limite de espaço livre.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
