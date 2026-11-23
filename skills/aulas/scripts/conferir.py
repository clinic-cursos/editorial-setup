"""Confere a identidade e a geometria do deck e renderiza a prévia."""

import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from lxml import etree
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Inches

import bold_deck
import clinic_deck
from restyle import bounds, open_deck


# Tons locais de clinic_deck.image, prompt_box, tabela, precificacao e parcerias.
STANDARD_COLORS = {"2A2625", "2A1E1D", "F6EFED", "FBF7F6", "F7F7F7",
                   "FAF6F4", "F5F1F0", "FAF8F7"}
STANDARD_COLORS.update(str(value) for value in vars(clinic_deck).values() if isinstance(value, RGBColor))
PALETTES = {
    "padrao": STANDARD_COLORS,
    "ousado": STANDARD_COLORS | {str(value) for value in vars(bold_deck).values() if isinstance(value, RGBColor)},
}
BLEED_NAMES = {"!!arco", "!!arco2", "!!foto", "!!fundo"}
# As caixas dos arcos do padrão legado são mantidas para preservar o PPTX original.
LEGACY_ARCS = ((0, 4.125, 2.4, 6.525), (7.6, -0.1, 10.1, 2.4),
               (-0.3, -0.3, 1.3, 1.3), (8, 3.425, 10.3, 5.725))
BOUNDS_TOLERANCE = 10  # EMU, arredondamento de coordenadas de formas livres
MARKER = re.compile(r"\[exemplo|\[confirmar\]", re.IGNORECASE)
PRESERVED_EXTENSION = "{A046E92C-840E-4D35-9C5C-4A96E281F065}"
FILL_TAGS = {qn("a:" + name) for name in ("solidFill", "gradFill", "pattFill", "blipFill", "noFill", "grpFill")}


def mark_preserved(shape):
    if is_preserved(shape):
        return
    properties = shape._element._nvXxPr.cNvPr
    extensions = properties.find(qn("a:extLst"))
    if extensions is None:
        extensions = etree.SubElement(properties, qn("a:extLst"))
    extension = etree.SubElement(extensions, qn("a:ext"), uri=PRESERVED_EXTENSION)
    etree.SubElement(extension, "{urn:clinic-cursos:aulas}preserved")


def is_preserved(shape):
    return any(extension.get("uri") == PRESERVED_EXTENSION
               for extension in shape._element._nvXxPr.cNvPr.findall(f"{qn('a:extLst')}/{qn('a:ext')}"))


def legacy_arc(shape, box):
    return (shape.shape_type == MSO_SHAPE_TYPE.FREEFORM
            and sum(1 for _ in shape._element.iter(qn("a:lnTo"))) == 81
            and any(all(abs(value - Inches(expected)) <= BOUNDS_TOLERANCE
                        for value, expected in zip(box, arc, strict=True)) for arc in LEGACY_ARCS))


class Theme:
    def __init__(self, slide, presentation):
        self.layout = slide.slide_layout
        master = self.layout.slide_master
        self.master = master
        self.text_styles = master._element.find(qn("p:txStyles"))
        self.default_style = presentation._element.find(qn("p:defaultTextStyle"))
        self.theme = etree.fromstring(master.part.part_related_by(RT.THEME).blob)
        self.color_map = dict(master._element.find(qn("p:clrMap")).attrib)
        for element in (slide.slide_layout._element, slide._element):
            override = element.find(f"{qn('p:clrMapOvr')}/{qn('a:overrideClrMapping')}")
            if override is not None:
                self.color_map.update(override.attrib)

    def font(self, font):
        if font in ("+mn-lt", "+mj-lt"):
            family = "minorFont" if font == "+mn-lt" else "majorFont"
            node = self.theme.find(f".//{qn('a:' + family)}/{qn('a:latin')}")
            return node.get("typeface")
        return font

    def color(self, node, placeholder=None):
        if node.tag == qn("a:srgbClr"):
            return node.get("val").upper()
        if node.tag == qn("a:sysClr"):
            return node.get("lastClr", node.get("val")).upper()
        if node.tag == qn("a:schemeClr"):
            value = node.get("val")
            if value == "phClr" and placeholder is not None:
                return self.color(placeholder)
            key = self.color_map.get(value, value)
            entry = self.theme.find(f".//{qn('a:clrScheme')}/{{{etree.QName(node).namespace}}}{key}")
            if entry is not None and len(entry):
                return self.color(entry[0])
            return value
        if node.tag == qn("a:scrgbClr"):
            channels = (max(0, min(1, int(node.get(key)) / 100000)) for key in "rgb")
            return "".join(f"{round(255 * (v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)):02X}"
                           for v in channels)
        return node.get("val", etree.QName(node).localname)

    def defaults(self, shape, frame, level):
        path = f"{qn(f'a:lvl{level + 1}pPr')}/{qn('a:defRPr')}"
        style = frame._txBody.find(qn("a:lstStyle"))
        if style is not None:
            yield style.find(path)
        if shape.is_placeholder:
            placeholder = self.layout.placeholders.get(idx=shape.placeholder_format.idx)
            if placeholder is not None and placeholder.has_text_frame:
                yield placeholder._element.find(f"{qn('p:txBody')}/{qn('a:lstStyle')}/{path}")
                yield placeholder._element.find(f"{qn('p:txBody')}/{qn('a:p')}/{qn('a:pPr')}/{qn('a:defRPr')}")
                master_placeholder = self.master.placeholders.get(ph_type=placeholder.placeholder_format.type)
                if master_placeholder is not None:
                    yield master_placeholder._element.find(f"{qn('p:txBody')}/{qn('a:lstStyle')}/{path}")
            placeholder_type = shape.placeholder_format.type.name
            style_name = "titleStyle" if "TITLE" in placeholder_type else "bodyStyle"
        else:
            style_name = "otherStyle"
        if self.text_styles is not None:
            yield self.text_styles.find(f"{qn('p:' + style_name)}/{path}")
        if self.default_style is not None:
            yield self.default_style.find(path)
            yield self.default_style.find(f"{qn('a:defPPr')}/{qn('a:defRPr')}")

    def referenced_fills(self, reference):
        if reference is None:
            return
        index = int(reference.get("idx", 0))
        if index in (0, 1000):
            return
        matrix, offset = ("bgFillStyleLst", 1001) if index > 1000 else ("fillStyleLst", 1)
        styles = self.theme.find(f".//{qn('a:' + matrix)}")
        if styles is not None and index - offset < len(styles):
            placeholder = reference[0] if len(reference) else None
            yield from fill_colors([styles[index - offset]], self, placeholder)


def fill_colors(properties, theme, placeholder=None):
    if properties is None:
        return
    paths = {qn("a:solidFill"): "*", qn("a:gradFill"): f"{qn('a:gsLst')}/{qn('a:gs')}/*",
             qn("a:pattFill"): "*/*"}
    for fill in properties:
        if fill.tag in paths:
            for color in fill.findall(paths[fill.tag]):
                yield theme.color(color, placeholder)


def check_fill(properties, theme, palette, add, reference=None):
    if properties is not None and any(node.tag in FILL_TAGS for node in properties):
        colors = fill_colors(properties, theme)
    else:
        colors = theme.referenced_fills(reference)
    for color in sorted(set(colors) - palette):
        add("fill_color", f"Preenchimento {color} fora da paleta.")


def check_text(frame, shape, theme, palette, add, width, height, margins):
    if not frame.text.strip():
        return
    if MARKER.search(frame.text):
        add("marker", "Marcador editorial pendente.", "warning")
    fonts, colors = set(), set()
    available_width = (width - margins[0] - margins[1]) / 12700
    available_height = (height - margins[2] - margins[3]) / 12700
    total_height = longest_line = 0
    family = clinic_deck.FONTE.casefold()
    is_quote = frame.text.strip() == bold_deck.QUOTE_MARK
    for paragraph in frame.paragraphs:
        defaults = [paragraph._p.find(f"{qn('a:pPr')}/{qn('a:defRPr')}"),
                    *theme.defaults(shape, frame, paragraph.level)]
        lines = [[]]
        for node in paragraph._p:
            if node.tag == qn("a:br"):
                lines.append([])
            content = node.findtext(qn("a:t"), "")
            if not content:
                continue
            styles = [item for item in (node.find(qn("a:rPr")), *defaults) if item is not None]
            font = theme.font(next((latin.get("typeface") for style in styles
                                    if (latin := style.find(qn("a:latin"))) is not None), "+mn-lt"))
            decorative = is_quote and font == bold_deck.QUOTE_FONT
            font_family = font.casefold()
            if (content.strip() and not decorative and font_family != family
                and not font_family.startswith(family + " ")):
                fonts.add(font)
            color = next((values for style in styles if (values := list(fill_colors(style, theme)))), [])
            colors.update(set(color) - palette)
            if decorative:
                continue
            size = next((int(style.get("sz")) / 100 for style in styles if "sz" in style.attrib), 18)
            tokens = re.split(r"([\v\n])", content)
            for token in tokens:
                if token in ("\v", "\n"):
                    lines.append([])
                elif token:
                    lines[-1].append((token, size))
        spacing = paragraph.line_spacing
        for line in lines:
            if not line:
                continue
            length = sum(len(text) * size * 0.48 for text, size in line)
            line_height = max(size for _, size in line)
            rows = 1
            if frame.word_wrap is not False and available_width > 0:
                rows = max(1, math.ceil(length / available_width))
            else:
                longest_line = max(longest_line, length)
            total_height += line_height
            if rows > 1:
                step = spacing.pt if hasattr(spacing, "pt") else line_height * (spacing or 1)
                total_height += (rows - 1) * step
        total_height += sum(value.pt for value in (paragraph.space_before, paragraph.space_after)
                            if value is not None)
    for font in sorted(fonts):
        add("font", f"Fonte {font} fora da família {clinic_deck.FONTE}.")
    for color in sorted(colors):
        add("text_color", f"Cor de texto {color} fora da paleta.")
    # Estimativa: largura média de 0,48 em por caractere, com tolerância para o impacto dos glifos
    # e da quebra de linha real. Uma linha usa a altura da fonte; a partir da segunda, conta o entrelinhamento.
    if frame.auto_size != MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE and (
        total_height > max(0, available_height) * 1.20 + 2
        or longest_line > max(0, available_width) * 1.20 + 2
    ):
        add("overflow", "Texto provavelmente estourado (estimativa por largura média do caractere).")


def check_shape(shape, theme, palette, add, preserved=False):
    if shape._element._nvXxPr.cNvPr.get("hidden") in {"1", "true"}:
        return
    preserved = preserved or is_preserved(shape)

    def finding(rule, message, severity="error"):
        add(rule, message, "warning" if preserved else severity, shape.name)

    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        for child in shape.shapes:
            check_shape(child, theme, palette, add, preserved)
    elif not shape.has_chart and shape._element.tag != qn("p:pic"):
        reference = shape._element.find(f"{qn('p:style')}/{qn('a:fillRef')}")
        check_fill(shape._element.find(qn("p:spPr")), theme, palette, finding, reference)
        if shape.has_text_frame:
            frame = shape.text_frame
            margins = (frame.margin_left, frame.margin_right, frame.margin_top, frame.margin_bottom)
            check_text(frame, shape, theme, palette, finding, shape.width, shape.height, margins)
        if shape.has_table:
            for cell in shape.table.iter_cells():
                if cell.is_spanned:
                    continue
                row, col = cell._tc.row_idx, cell._tc.col_idx
                width = sum(shape.table.columns[i].width for i in range(col, col + cell.span_width))
                height = sum(shape.table.rows[i].height for i in range(row, row + cell.span_height))
                check_fill(cell._tc.tcPr, theme, palette, finding)
                margins = (cell.margin_left, cell.margin_right, cell.margin_top, cell.margin_bottom)
                check_text(cell.text_frame, shape, theme, palette, finding, width, height, margins)


def inspect(path, style):
    deck = open_deck(path)
    palette = PALETTES[style]
    findings = []
    for number, slide in enumerate(deck.slides, 1):
        def add(rule, message, severity="error", shape=None):
            findings.append({"slide": number, "shape": shape, "rule": rule, "severity": severity,
                             "message": message})

        theme = Theme(slide, deck)
        for layer in (slide, theme.layout, theme.master):
            background = layer._element.find(f"{qn('p:cSld')}/{qn('p:bg')}")
            if background is not None:
                check_fill(background.find(qn("p:bgPr")), theme, palette, add, background.find(qn("p:bgRef")))
                break
        if style == "ousado":
            names = {shape.name for shape in slide.shapes}
            for name in sorted({"!!fundo", "!!logo"} - names):
                add("morph_shape", f"Forma obrigatória ausente: {name}.")
            if next(slide._element.iter(f"{{{bold_deck.P159}}}morph"), None) is None:
                add("morph", "Transição Morph ausente.")
            timing = slide._element.find(qn("p:timing"))
            ids = {str(shape.shape_id) for shape in slide.shapes}
            if timing is None or not any(target.get("spid") in ids for target in timing.iter(qn("p:spTgt"))):
                add("animation", "Animação de forma ausente.")
        for shape in slide.shapes:
            box = bounds(shape)
            if (shape.name not in BLEED_NAMES
                and (min(box[:2]) < -BOUNDS_TOLERANCE
                     or box[2] > deck.slide_width + BOUNDS_TOLERANCE
                     or box[3] > deck.slide_height + BOUNDS_TOLERANCE)
                and not legacy_arc(shape, box)):
                add("bounds", "Forma fora dos limites do slide.",
                    "warning" if is_preserved(shape) else "error", shape.name)
            check_shape(shape, theme, palette, add)
    return {"style": style, "slides": len(deck.slides), "findings": findings,
            "errors": sum(item["severity"] == "error" for item in findings),
            "warnings": sum(item["severity"] == "warning" for item in findings)}


def report(path, style, *, as_json=False):
    result = inspect(path, style)
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Conferência ({style}): {result['slides']} slide(s), "
              f"{result['errors']} reprovação(ões), {result['warnings']} aviso(s).")
        for item in result["findings"]:
            severity = "Reprovação" if item["severity"] == "error" else "Aviso"
            shape = f" ({item['shape']})" if item["shape"] else ""
            print(f"Slide {item['slide']}{shape} | {severity}: {item['message']}")
    return int(result["errors"] > 0)


def preview(deck, folder):
    soffice, pdftoppm = (shutil.which(binary) for binary in ("soffice", "pdftoppm"))
    missing = [name for name, path in (("soffice", soffice), ("pdftoppm", pdftoppm)) if path is None]
    if missing:
        raise ValueError(f"instale os executáveis ausentes para gerar a prévia: {', '.join(missing)}")
    deck = deck.resolve()
    expected = len(open_deck(deck).slides)
    with TemporaryDirectory() as tmp:
        directory = Path(tmp)
        options = 'pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}'
        pdf = directory / deck.with_suffix(".pdf").name
        commands = [
            [soffice, f"-env:UserInstallation={(directory / 'profile').as_uri()}", "--headless",
             "--convert-to", options, "--outdir", str(directory), str(deck)],
            [pdftoppm, "-png", str(pdf), str(directory / "slide")],
        ]
        for command in commands:
            try:
                subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
            except subprocess.TimeoutExpired as exc:
                raise ValueError(f"{Path(command[0]).name} excedeu 120 segundos") from exc
            except subprocess.CalledProcessError as exc:
                detail = (exc.stderr or exc.stdout).strip()
                raise ValueError(f"{Path(command[0]).name} falhou: {detail}") from exc
        images = list(directory.glob("slide-*.png"))
        if len(images) != expected:
            raise ValueError(f"a renderização produziu {len(images)} PNG(s) para {expected} slide(s)")
        folder.mkdir(parents=True, exist_ok=True)
        for image in images:
            shutil.move(image, folder / image.name)
    return expected
