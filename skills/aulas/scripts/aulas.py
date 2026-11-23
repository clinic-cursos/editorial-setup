#!/usr/bin/env python3
"""Entrada da ferramenta de aulas."""

import argparse
import json
from pathlib import Path

import clinic_deck
from bold_deck import BOLD_LAYOUTS
import restyle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("gerar", help="Gera um PowerPoint a partir de um roteiro JSON")
    generate.add_argument("roteiro", type=Path)
    generate.add_argument("saida", type=Path)
    extract = commands.add_parser("extrair", help="Extrai o roteiro e as imagens de um PowerPoint")
    extract.add_argument("deck", type=Path)
    extract.add_argument("pasta", type=Path)
    extract.add_argument("--slides", help="Números e intervalos de slides, como 3,5-9")
    args = parser.parse_args()

    if args.command == "extrair":
        try:
            path = restyle.extract(args.deck, args.pasta, args.slides)
        except (OSError, ValueError) as exc:
            extract.error(str(exc))
        print("ok:", path)
        return

    try:
        spec = json.loads(args.roteiro.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        generate.error(f"não foi possível ler o roteiro {args.roteiro}: {exc}")
    if not isinstance(spec, dict) or not isinstance(spec.get("slides"), list):
        generate.error("o roteiro deve conter uma lista de slides")
    if any(not isinstance(slide, dict) for slide in spec["slides"]):
        generate.error("cada slide do roteiro deve ser um objeto")
    if not isinstance(spec.get("avulso", False), bool):
        generate.error("avulso deve ser true ou false")

    style = spec.get("estilo", "padrao")
    if style not in ("padrao", "ousado"):
        generate.error(f"estilo desconhecido: {style}. Disponíveis: padrao, ousado")
    layouts = BOLD_LAYOUTS if style == "ousado" else clinic_deck.LAYOUTS
    try:
        clinic_deck.build(spec, args.saida, args.roteiro.absolute().parent, layouts=layouts)
    except (OSError, ValueError) as exc:
        generate.error(str(exc))
    print("ok:", args.saida)


if __name__ == "__main__":
    main()
