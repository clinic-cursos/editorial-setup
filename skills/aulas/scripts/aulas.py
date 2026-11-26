#!/usr/bin/env python3
"""Entrada da ferramenta de aulas."""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import clinic_deck
from bold_deck import BOLD_LAYOUTS
import conferir
import restyle


def build_deck(spec, output, base_dir, layouts):
    if not any(slide.get("tipo") == "preservado" for slide in spec["slides"]):
        clinic_deck.build(spec, output, base_dir, layouts=layouts, enforce_structure=True)
        return

    layout = layouts["preservado"]

    def marked_layout(prs, slide, data, preserved):
        def copy(target, script, box):
            shapes = preserved.copy(target, script, box)
            for shape in shapes:
                conferir.mark_preserved(shape)
            return shapes

        # Os layouts de preservado usam apenas o método copy.
        layout(prs, slide, data, SimpleNamespace(copy=copy))

    # O gerador padrão usa a identidade do mapa para acrescentar o rodapé.
    layouts["preservado"] = marked_layout
    try:
        clinic_deck.build(spec, output, base_dir, layouts=layouts, enforce_structure=True)
    finally:
        layouts["preservado"] = layout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("gerar", help="Gera um PowerPoint a partir de um roteiro JSON")
    generate.add_argument("roteiro", type=Path)
    generate.add_argument("saida", type=Path)
    generate.add_argument("--sem-conferir", action="store_true", help=argparse.SUPPRESS)
    extract = commands.add_parser("extrair", help="Extrai o roteiro e as imagens de um PowerPoint")
    extract.add_argument("deck", type=Path)
    extract.add_argument("pasta", type=Path)
    extract.add_argument("--slides", help="Números e intervalos de slides, como 3,5-9")
    check = commands.add_parser("conferir", help="Confere um PowerPoint pelo padrão editorial")
    check.add_argument("deck", type=Path)
    check.add_argument("--estilo", choices=conferir.PALETTES, default="padrao")
    check.add_argument("--origem", type=Path, help="Deck original para conferir a fidelidade do texto")
    check.add_argument("--origem-slides", help="Números e intervalos de slides da origem, como 3,5-9")
    check.add_argument("--json", action="store_true")
    preview = commands.add_parser("previa", help="Gera um PNG por slide")
    preview.add_argument("deck", type=Path)
    preview.add_argument("pasta", type=Path)
    args = parser.parse_args()

    if args.command == "conferir":
        if args.origem_slides is not None and args.origem is None:
            check.error("--origem-slides exige --origem")
        try:
            return conferir.report(args.deck, args.estilo, as_json=args.json,
                                   origin=args.origem, origin_selection=args.origem_slides)
        except ValueError as exc:
            check.error(str(exc))
    if args.command == "previa":
        try:
            count = conferir.preview(args.deck, args.pasta)
        except (OSError, ValueError) as exc:
            preview.error(f"previa de {args.deck}: {exc}")
        print(f"Prévia: {count} PNG(s) em {args.pasta}")
        return 0

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
        build_deck(spec, args.saida, args.roteiro.absolute().parent, layouts)
        print("ok:", args.saida)
        return 0 if args.sem_conferir else conferir.report(args.saida, style)
    except (OSError, ValueError) as exc:
        generate.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
