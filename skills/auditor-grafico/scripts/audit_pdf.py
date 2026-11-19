"""Audite um PDF diagramado e relate os achados por página."""

import argparse
import json
from pathlib import Path
import sys

import pdfplumber

from pdfcheck import checks
from pdfcheck.model import Report
from pdfcheck.rules import load_rules

CHECKS = (
    checks.check_overlaps,
    checks.check_safe_zone,
    checks.check_duplicates,
    checks.check_fonts,
    checks.check_text_layer,
    checks.check_page_size,
    checks.check_page_numbers,
    checks.check_toc,
)


def load_origins(path: Path) -> dict[tuple[int, int], float]:
    origins = {}
    for entry in json.loads(path.read_text(encoding="utf-8")).values():
        size = tuple(entry["pixels"])
        origins[size] = max(entry["ppi"], origins.get(size, 0))
    return origins


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--rules", metavar="JSON", help="regras gráficas no formato de graphic-rules.json")
    parser.add_argument("--inherited", type=Path, metavar="LISTA", help="origem.json do Diagramador")
    parser.add_argument("--json", type=Path, metavar="OUT", help="grava o relatório em JSON")
    parser.add_argument("--md", type=Path, metavar="OUT", help="grava o relatório em Markdown")
    args = parser.parse_args(argv)

    try:
        outputs = [path for path in (args.json, args.md) if path is not None]
        input_paths = [Path(path) for path in (args.pdf, args.rules, args.inherited) if path is not None]
        for index, output in enumerate(outputs):
            for path in [*input_paths, *outputs[:index]]:
                if output.resolve() == path.resolve() or (
                    output.exists() and path.exists() and output.samefile(path)
                ):
                    raise ValueError("a saída precisa de um caminho distinto das entradas e demais saídas")

        rules = load_rules(args.rules)
        origins = load_origins(args.inherited) if args.inherited else None
        with pdfplumber.open(args.pdf) as pdf:
            report = Report(str(args.pdf), len(pdf.pages))
            for check in CHECKS:
                report.findings.extend(check(pdf, rules))
            report.findings.extend(checks.check_images(pdf, rules, origins))

        markdown = report.to_markdown()
        if args.json:
            args.json.write_text(report.to_json() + "\n", encoding="utf-8")
        if args.md:
            args.md.write_text(markdown, encoding="utf-8")
    except Exception as error:
        print(f"Não foi possível auditar {args.pdf}: {error}", file=sys.stderr)
        return 2

    if not outputs:
        print(markdown, end="")
    return 1 if report.errors() else 0


if __name__ == "__main__":
    sys.exit(main())
