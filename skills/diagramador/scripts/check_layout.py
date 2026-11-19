"""Rode as checagens técnicas de layout num PDF composto e imprima o relatório em Markdown."""

import argparse
import json
from pathlib import Path
import sys

import pdfplumber

from pdfcheck import checks
from pdfcheck.model import Report
from pdfcheck.rules import load_rules

CHECKS = (
    checks.check_overlaps, checks.check_safe_zone, checks.check_duplicates, checks.check_fonts,
    checks.check_text_layer, checks.check_page_size, checks.check_page_numbers, checks.check_toc,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--inherited", default="", metavar="ORIGEM_JSON", help="origem.json do extract_pdf.py, com a resolução das imagens herdadas")
    args = parser.parse_args(argv)
    origins = {}
    try:
        if args.inherited:
            for entry in json.loads(Path(args.inherited).read_text(encoding="utf-8")).values():
                size = tuple(entry["pixels"])
                origins[size] = max(entry["ppi"], origins.get(size, 0))  # mesmo tamanho em pixels: vale o mais exigente
        rules = load_rules()
        with pdfplumber.open(args.pdf) as pdf:
            report = Report(args.pdf, len(pdf.pages))
            for check in CHECKS:
                report.findings += check(pdf, rules)
            report.findings += checks.check_images(pdf, rules, origins)
    except Exception as error:  # arquivo inexistente ou PDF ilegível
        print(f"Não foi possível checar {args.pdf}: {error}", file=sys.stderr)
        return 2
    print(report.to_markdown(), end="")
    return 1 if report.errors() else 0


if __name__ == "__main__":
    sys.exit(main())
