#!/usr/bin/env python3
"""Entrada da ferramenta de aulas."""

import argparse
import json
from pathlib import Path

import clinic_deck
from bold_deck import BOLD_LAYOUTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("gerar", help="Gera um PowerPoint a partir de um roteiro JSON")
    generate.add_argument("roteiro", type=Path)
    generate.add_argument("saida", type=Path)
    args = parser.parse_args()

    try:
        spec = json.loads(args.roteiro.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        generate.error(f"não foi possível ler o roteiro {args.roteiro}: {exc}")
    if not isinstance(spec, dict) or not isinstance(spec.get("slides"), list):
        generate.error("o roteiro deve conter uma lista de slides")
    if any(not isinstance(slide, dict) for slide in spec["slides"]):
        generate.error("cada slide do roteiro deve ser um objeto")

    style = spec.get("estilo", "padrao")
    if style not in ("padrao", "ousado"):
        generate.error(f"estilo desconhecido: {style}. Disponíveis: padrao, ousado")
    layouts = BOLD_LAYOUTS if style == "ousado" else clinic_deck.LAYOUTS
    clinic_deck.build(spec, args.saida, args.roteiro.absolute().parent, layouts=layouts)
    print("ok:", args.saida)


if __name__ == "__main__":
    main()
