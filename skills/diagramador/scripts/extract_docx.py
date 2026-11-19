"""Converta um DOCX para o formato de manuscrito da Clinic Editora."""

import argparse
from os.path import relpath
from pathlib import Path
import re
from zipfile import BadZipFile

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.exceptions import InvalidXmlError
from docx.oxml.ns import qn


def single_line(text):
    return " ".join(text.splitlines()).strip()


def paragraph_format(paragraph, numbering):
    style = paragraph.style
    numbering_properties = [paragraph._p.pPr]
    while style is not None:
        if style.style_id == "Title":
            return "# ", None
        properties = style.element.pPr
        outline = properties.outlineLvl if properties is not None else None
        if outline is not None and 0 <= outline.val <= 8:
            return "#" * min(outline.val + 1, 3) + " ", None
        heading = re.fullmatch(r"Heading([1-9])", style.style_id)
        if heading:
            return "#" * min(int(heading[1]), 3) + " ", None
        numbering_properties.append(properties)
        style = style.base_style

    for properties in numbering_properties:
        num_pr = properties.numPr if properties is not None else None
        if num_pr is None or num_pr.numId is None:
            continue
        num_id = num_pr.numId.val
        if num_id == 0 or numbering is None:
            break
        level = num_pr.ilvl.val if num_pr.ilvl is not None else 0
        num = numbering.num_having_numId(num_id)
        abstract_id = num.abstractNumId.val
        formats = num.xpath(f'./w:lvlOverride[@w:ilvl="{level}"]/w:lvl/w:numFmt/@w:val')
        if not formats:
            formats = numbering.xpath(
                f'./w:abstractNum[@w:abstractNumId="{abstract_id}"]'
                f'/w:lvl[@w:ilvl="{level}"]/w:numFmt/@w:val'
            )
        if formats and formats[0] == "bullet":
            return "- ", 0
        if formats and formats[0] != "none":
            return "", num_id
        break
    return "", None


def paragraph_images(paragraph):
    for drawing in paragraph._p.xpath(".//wp:inline | .//wp:anchor"):
        properties = drawing.find(qn("wp:docPr"))
        caption = single_line(properties.get("descr", "")) if properties is not None else ""
        for blip in drawing.iter(qn("a:blip")):
            relationship_id = blip.get(qn("r:embed"))
            if relationship_id is None:
                continue
            relationship = paragraph.part.rels[relationship_id]
            if relationship.reltype == RELATIONSHIP_TYPE.IMAGE and not relationship.is_external:
                yield caption, relationship.target_part


def render_document(document, source, output, images):
    properties = document.core_properties
    blocks = [
        "\n".join(
            [
                f"title: {single_line(properties.title) or source.stem}",
                f"course: {single_line(properties.subject)}",
                f"authors: {single_line(properties.author)}",
                f"version: {single_line(properties.version)}",
            ]
        )
    ]
    try:
        numbering = document.part.part_related_by(RELATIONSHIP_TYPE.NUMBERING).element
    except KeyError:
        numbering = None
    figures = []
    list_items = []
    last_list = None

    for paragraph in document.paragraphs:
        text = single_line(paragraph.text)
        if text:
            prefix, list_id = paragraph_format(paragraph, numbering)
            if list_id != last_list and list_items:
                blocks.append("\n".join(list_items))
                list_items.clear()
            if list_id is None:
                blocks.append(prefix + text)
            else:
                marker = f"{len(list_items) + 1}. " if list_id else prefix
                list_items.append(marker + text)
            last_list = list_id

        for caption, image in paragraph_images(paragraph):
            if list_items:
                blocks.append("\n".join(list_items))
                list_items.clear()
                last_list = None
            figure_id = f"fig-{len(figures) + 1}"
            filename = images / f"{figure_id}.{image.partname.ext}"
            relative = Path(relpath(filename, output.parent)).as_posix()
            blocks.append(f"![{caption}]({relative}){{#{figure_id}}}")
            figures.append((filename, image.blob))

    if list_items:
        blocks.append("\n".join(list_items))
    return "\n\n".join(blocks) + "\n", figures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", metavar="DOCX", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="caminho do manuscrito Markdown")
    parser.add_argument("--images", type=Path, required=True, help="pasta das figuras extraídas")
    args = parser.parse_args()

    try:
        source = args.docx.resolve()
        output = args.out.resolve()
        images = args.images.resolve()
        if source == output:
            parser.error("o manuscrito Markdown deve ter um caminho diferente do DOCX")
        with source.open("rb") as stream:
            document = Document(stream)
        markdown, figures = render_document(document, source, output, images)
        for filename, _ in figures:
            if filename.resolve() in (source, output):
                parser.error(f"a figura {filename} entra em conflito com o DOCX ou o manuscrito")
    except (
        OSError, BadZipFile, PackageNotFoundError, InvalidXmlError, KeyError, SyntaxError, ValueError
    ) as error:
        parser.error(f"não foi possível ler {args.docx}: {error}")

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        images.mkdir(parents=True, exist_ok=True)
        for filename, blob in figures:
            filename.write_bytes(blob)
        output.write_text(markdown, encoding="utf-8")
    except OSError as error:
        parser.exit(1, f"Não foi possível gravar {output} ou as figuras em {images}: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
