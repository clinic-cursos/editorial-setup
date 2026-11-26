"""Confere a identidade e a geometria do deck e renderiza a prévia."""

import json
import re
import shutil
import subprocess
from bisect import bisect_right
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from functools import cached_property
from io import BytesIO
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from unicodedata import combining, decimal, normalize

from lxml import etree
from PIL import Image, UnidentifiedImageError
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

import bold_deck
import clinic_deck
from restyle import (
    PAINT_TAGS, annotation_colors, background_picture, bounds, cell_fill, cell_outlines, contrast_ratio,
    fill_surface, matches_annotation, open_deck, reading_order, rgb_channels, shape_paint, shape_surfaces,
    sized_images, slide_surface,
    solid_color, solid_fill_color,
    slide_numbers, slide_shape_roles, table_style, texts, visible_color,
)


PRESERVED_WARNING_LABELS = {
    "bounds": ("forma fora dos limites do slide", "formas fora dos limites do slide"),
    "fill_color": ("preenchimento fora da paleta", "preenchimentos fora da paleta"),
    "marker": ("marcador editorial pendente", "marcadores editoriais pendentes"),
    "outline_color": ("contorno fora da paleta", "contornos fora da paleta"),
    "overflow": ("estouro de texto", "estouros de texto"),
}

SCORE_CATEGORIES = {
    "elementos-base": (20, ("morph_shape",)),
    "transicao": (15, ("morph",)),
    "animacao": (15, ("animation",)),
    "fonte": (15, ("font",)),
    "paleta": (15, ("fill_color", "outline_color", "text_color", "marker")),
    "leitura": (20, ("bounds", "overflow", "text_overlap", "contrast")),
}
SCORE_CATEGORY_BY_RULE = {
    rule: category
    for category, (_, rules) in SCORE_CATEGORIES.items()
    for rule in rules
}
CONTENT_METADATA = {PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.DATE}


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
MARKER_ONLY = re.compile(r"\[(?:exemplo[^\]]*|confirmar)\]", re.IGNORECASE)
PRESERVED_EXTENSION = "{A046E92C-840E-4D35-9C5C-4A96E281F065}"
TEXT_OVERFLOW_RATIO = 1.10

# Métricas verticais da Montserrat em unidades por em.
CAP_HEIGHT = 0.7
DESCENT = 0.251
# Avanços hmtx em milésimos de em. Regular e Bold vêm dos TTF do diagramador;
# ExtraBold vem da Montserrat variável no peso 800. A tabela dispensa fonte instalada.
WIDTH_CHARS = "".join(map(chr, range(32, 127))) + "\u2013\u2014‘’“”…•→"
MONTSERRAT_WIDTHS = {
    "regular": dict(zip(WIDTH_CHARS, (
        262, 260, 373, 696, 615, 829, 669, 202, 329, 329, 386, 575, 212, 382, 212, 335, 662, 361,
        568, 564, 661, 566, 609, 589, 638, 609, 212, 212, 575, 575, 575, 567, 1033, 717, 754, 709,
        826, 669, 633, 773, 813, 302, 501, 711, 589, 955, 813, 839, 718, 839, 723, 615, 574, 792,
        698, 1111, 656, 635, 651, 318, 335, 318, 576, 500, 600, 590, 678, 563, 678, 604, 339, 686,
        677, 269, 274, 598, 269, 1061, 677, 627, 678, 678, 401, 489, 406, 673, 542, 879, 534, 542,
        511, 334, 295, 334, 575, 500, 1000, 212, 212, 382, 382, 647, 295, 600,
    ), strict=True)),
    "bold": dict(zip(WIDTH_CHARS, (
        283, 289, 437, 720, 638, 877, 728, 230, 357, 358, 434, 599, 262, 386, 262, 392, 679, 392,
        590, 592, 689, 595, 637, 620, 660, 637, 262, 262, 599, 599, 599, 589, 1035, 766, 765, 724,
        826, 671, 639, 771, 808, 328, 541, 740, 604, 955, 808, 844, 732, 844, 735, 638, 618, 788,
        746, 1163, 714, 676, 671, 368, 392, 368, 600, 500, 600, 617, 690, 591, 692, 631, 387, 700,
        691, 301, 307, 655, 301, 1049, 691, 655, 690, 690, 431, 531, 435, 687, 598, 937, 595, 598,
        543, 391, 309, 391, 599, 500, 1000, 262, 262, 498, 498, 798, 358, 600,
    ), strict=True)),
    "extrabold": dict(zip(WIDTH_CHARS, (
        291, 301, 462, 730, 647, 897, 752, 242, 369, 369, 453, 609, 283, 388, 283, 415, 685, 405,
        599, 603, 700, 607, 649, 632, 669, 649, 283, 283, 609, 609, 609, 597, 1036, 786, 769, 730,
        826, 672, 642, 770, 806, 339, 557, 752, 610, 954, 806, 846, 737, 846, 740, 647, 635, 786,
        766, 1184, 737, 693, 679, 389, 415, 389, 610, 500, 600, 628, 695, 603, 698, 642, 406, 705,
        696, 313, 320, 677, 313, 1045, 696, 666, 695, 695, 443, 547, 447, 692, 620, 956, 619, 620,
        556, 414, 314, 414, 609, 500, 1000, 283, 283, 545, 545, 858, 383, 600,
    ), strict=True)),
}


def glyph_width(char, widths):
    if char in widths:
        return widths[char]
    # Letras acentuadas usam o avanço da base; símbolos ausentes usam 0,6 em.
    return sum(widths.get(base, 600) for base in normalize("NFKD", char) if not combining(base))


def measure_line(line, width, wrap):
    """Mede palavras que cruzam runs e devolve tamanho da fonte e avanço por linha visual."""
    text = "".join(part for part, _, _ in line)
    metrics = [(glyph_width(char, widths) * size / 1000, size)
               for part, size, widths in line for char in part]
    used = gap = size = 0
    rows = []
    wide_word = False
    # O espaço inseparável pertence à palavra para fins de quebra.
    for match in re.finditer(r"(?:(?!\u00a0)\s)+|(?:\S|\u00a0)+", text):
        token = metrics[match.start():match.end()]
        advance = sum(length for length, _ in token)
        if match.group().isspace() and "\u00a0" not in match.group():
            gap += advance
            continue
        wide_word |= advance > width
        if wrap and used and used + gap + advance > width:
            rows.append((size, used))
            used = gap = size = 0
        used += gap + advance if used else advance
        size = max(size, max(point_size for _, point_size in token))
        gap = 0
    if not wrap and used > width:
        wide_word = True
    rows.append((size or max((size for _, size, _ in line), default=0), used))
    return rows, wide_word


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
        self.presentation_part = presentation.part
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

    @cached_property
    def table_styles(self):
        try:
            part = self.presentation_part.part_related_by(RT.TABLE_STYLES)
        except KeyError:
            return {}
        return {style.get("styleId"): style for style in parse_xml(part.blob).findall(qn("a:tblStyle"))}

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
        for properties in self.paragraph_defaults(shape, frame, level):
            yield properties.find(qn("a:defRPr"))

    def paragraph_defaults(self, shape, frame, level):
        path = qn(f"a:lvl{level + 1}pPr")
        style = frame._txBody.find(qn("a:lstStyle"))
        if style is not None:
            yield from style.findall(path)
        if shape.is_placeholder:
            placeholder = self.layout.placeholders.get(idx=shape.placeholder_format.idx)
            if placeholder is not None and placeholder.has_text_frame:
                yield from placeholder._element.findall(f"{qn('p:txBody')}/{qn('a:lstStyle')}/{path}")
                properties = placeholder._element.find(f"{qn('p:txBody')}/{qn('a:p')}/{qn('a:pPr')}")
                if properties is not None:
                    yield properties
                master_placeholder = self.master.placeholders.get(ph_type=placeholder.placeholder_format.type)
                if master_placeholder is not None:
                    yield from master_placeholder._element.findall(f"{qn('p:txBody')}/{qn('a:lstStyle')}/{path}")
            placeholder_type = shape.placeholder_format.type.name
            style_name = "titleStyle" if "TITLE" in placeholder_type else "bodyStyle"
        else:
            style_name = "otherStyle"
        if self.text_styles is not None:
            yield from self.text_styles.findall(f"{qn('p:' + style_name)}/{path}")
        if self.default_style is not None:
            yield from self.default_style.findall(path)
            yield from self.default_style.findall(qn("a:defPPr"))

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
    if properties is not None and any(node.tag in PAINT_TAGS for node in properties):
        colors = fill_colors(properties, theme)
    else:
        colors = theme.referenced_fills(reference)
    for color in sorted(set(colors) - palette):
        add("fill_color", f"Preenchimento {color} fora da paleta.")


def check_preserved_paint(fill, theme, palette, add, strict, *, placeholder=None, outline=False):
    if fill is None:
        return
    if fill.tag == qn("a:solidFill"):
        solid = solid_fill_color(theme, fill, placeholder)
        colors = [solid] if solid is not None else fill_colors([fill], theme, placeholder)
    else:
        colors = fill_colors([fill], theme, placeholder)
    rule, label = ("outline_color", "Contorno") if outline else ("fill_color", "Preenchimento")
    severity = "error" if strict and fill.tag == qn("a:solidFill") else "warning"
    for color in sorted(set(colors) - palette):
        add(rule, f"{label} {color} fora da paleta.", severity)


def text_defaults(paragraph, shape, frame, theme):
    return [paragraph._p.find(f"{qn('a:pPr')}/{qn('a:defRPr')}"),
            *theme.defaults(shape, frame, paragraph.level)]


def bullet_color_node(paragraph, shape, frame, theme):
    properties = [node for node in (
        paragraph._p.pPr, *theme.paragraph_defaults(shape, frame, paragraph.level)
    ) if node is not None]
    bullet_types = {qn(f"a:{name}") for name in ("buNone", "buChar", "buAutoNum", "buBlip")}
    bullet_type = next((child.tag for node in properties for child in node if child.tag in bullet_types), None)
    if bullet_type in {qn("a:buNone"), qn("a:buBlip")}:
        return None
    for node in properties:
        if node.find(qn("a:buClrTx")) is not None:
            return None
        paint = node.find(qn("a:buClr"))
        if paint is not None and len(paint):
            return paint[0]
    return None


def text_color_node(styles, shape):
    for style in styles:
        fill = style.eg_fillProperties
        if fill is not None:
            return fill[0] if fill.tag == qn("a:solidFill") and len(fill) else None
    reference = shape._element.find(f"{qn('p:style')}/{qn('a:fontRef')}")
    return reference[0] if reference is not None and len(reference) else None


def check_text(frame, shape, theme, palette, add, width, height, margins, top, slide_bottom, *,
               grows=False, background=None, allow_quote_font=True, annotations=None, preserved=False):
    text = frame.text.strip()
    if not text:
        return 0, []
    if MARKER.search(text):
        add("marker", "Marcador editorial pendente.", "warning")
    fonts, colors, bullet_colors = set(), set(), set()
    available_width = Emu(width - margins[0] - margins[1]).pt
    available_height = Emu(height - margins[2] - margins[3]).pt
    cursor = text_bottom = 0
    text_rows = []
    wide_word = False
    low_contrast = False
    autofit = frame._bodyPr.normAutofit
    scale = autofit.fontScale / 100 if autofit is not None else 1
    family = clinic_deck.FONTE.casefold()
    is_quote = allow_quote_font and text == bold_deck.QUOTE_MARK
    for paragraph in frame.paragraphs:
        alignment = {PP_ALIGN.CENTER: 0.5, PP_ALIGN.RIGHT: 1}.get(paragraph.alignment, 0)
        defaults = text_defaults(paragraph, shape, frame, theme)
        if annotations is not None and paragraph.text.strip():
            bullet = bullet_color_node(paragraph, shape, frame, theme)
            if bullet is not None:
                color = solid_color(bullet, theme)
                if color not in palette and not matches_annotation(color, annotations, background):
                    bullet_colors.add(color)
                if background is not None and rgb_channels(color) is not None:
                    low_contrast |= contrast_ratio(visible_color(color, bullet, background), background) < 3
        lines = [[]]
        previous_size = next((int(style.get("sz")) / 100 for style in defaults
                              if style is not None and "sz" in style.attrib), 18) * scale
        for node in paragraph._p:
            if node.tag == qn("a:br"):
                if not lines[-1]:
                    lines[-1].append(("", previous_size, MONTSERRAT_WIDTHS["regular"]))
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
            color_node = text_color_node(styles, shape)
            if annotations is not None and color_node is not None:
                color = solid_color(color_node, theme)
                if content.strip() and color not in palette and not matches_annotation(color, annotations, background):
                    colors.add(color)
            else:
                color = next((values for style in styles if (values := list(fill_colors(style, theme)))), [])
                colors.update(set(color) - palette)
            if background is not None and not low_contrast and content.strip():
                foreground = solid_color(color_node, theme) if color_node is not None else "000000"
                if rgb_channels(foreground) is not None:
                    low_contrast = contrast_ratio(visible_color(foreground, color_node, background), background) < 3
            if decorative:
                continue
            size = next((int(style.get("sz")) / 100 for style in styles if "sz" in style.attrib), 18) * scale
            previous_size = size
            bold = next((style.get("b") in {"1", "true"} for style in styles if "b" in style.attrib), False)
            weight = "extrabold" if font_family == clinic_deck.FONTE_FORTE.casefold() else "bold" if bold else "regular"
            for token in re.split(r"([\v\n])", content):
                if token in {"\v", "\n"}:
                    lines[-1].append(("", size, MONTSERRAT_WIDTHS[weight]))
                    lines.append([])
                elif token:
                    lines[-1].append((token, size, MONTSERRAT_WIDTHS[weight]))
        spacing = paragraph.line_spacing
        cursor += paragraph.space_before.pt if paragraph.space_before is not None else 0
        for line in lines:
            rows, over_width = measure_line(line, available_width, frame.word_wrap is not False)
            wide_word |= over_width
            has_text = any(part.strip() for part, _, _ in line)
            for size, advance in rows:
                if not size:
                    continue
                # Métricas verticais da Montserrat em unidades por em.
                ascent = size * 0.968
                line_height = ascent + size * DESCENT
                if has_text:
                    text_bottom = max(text_bottom, cursor + line_height)
                    if advance:
                        left = max(0, available_width - advance) * alignment
                        # Estima a faixa das letras entre a altura das maiúsculas e a linha de base.
                        baseline = cursor + ascent
                        text_rows.append((left, baseline - size * CAP_HEIGHT, left + advance, baseline))
                cursor += spacing.pt if hasattr(spacing, "pt") else line_height * (spacing or 1)
        cursor += paragraph.space_after.pt if paragraph.space_after is not None else 0
    for font in sorted(fonts):
        add("font", f"Fonte {font} fora da família {clinic_deck.FONTE}.")
    for color in sorted(colors):
        add("text_color", f"Cor de texto {color} fora da paleta.")
    for color in sorted(bullet_colors):
        add("text_color", f"Cor de marcador de lista {color} fora da paleta.")
    if low_contrast:
        add("contrast", "Texto com contraste abaixo de 3:1.", "warning")
    if not text_bottom:
        return 0, []
    grows = grows or frame.auto_size == MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
    anchor = {MSO_ANCHOR.MIDDLE: 0.5, MSO_ANCHOR.BOTTOM: 1}.get(frame.vertical_anchor, 0)
    offset = anchor * max(0, available_height - text_bottom)
    reasons = []
    if wide_word:
        reasons.append("Palavra ou linha sem quebra excede a largura útil da caixa.")
    height_overflow = not grows and text_bottom > max(0, available_height) * TEXT_OVERFLOW_RATIO
    if height_overflow:
        reasons.append("Texto excede a altura da caixa fixa em mais de 10%.")
    if Emu(slide_bottom - top - margins[2]).pt < offset + text_bottom:
        reasons.append("Texto ultrapassa a borda inferior do slide.")
    if reasons:
        if preserved:
            severity = "error" if height_overflow else "warning"
        else:
            severity = "warning" if MARKER_ONLY.fullmatch(text) else "error"
        add("overflow", "Texto provavelmente estourado. " + " ".join(reasons), severity)
    left = shape.left + margins[0]
    line_top = top + margins[2] + Pt(offset)
    return Pt(text_bottom) + margins[2] + margins[3], [
        (left + Pt(x1), line_top + Pt(y1), left + Pt(x2), line_top + Pt(y2))
        for x1, y1, x2, y2 in text_rows
    ]


def check_table(shape, theme, palette, add, slide_bottom, background, preserved, strict, annotations):
    table = shape.table
    style = table_style(table, theme) if preserved else None
    if style is not None:
        for borders in style.iter(qn("a:tcBdr")):
            for fill in borders.iter(qn("a:solidFill")):
                check_preserved_paint(fill, theme, palette, add, strict, outline=True)
    heights = [row.height for row in table.rows]
    top = shape.top
    for row, table_row in enumerate(table.rows):
        for col, cell in enumerate(table_row.cells):
            fill = cell_fill(table, cell, row, col, style) if preserved else None
            if preserved:
                check_preserved_paint(fill, theme, palette, add, strict)
                for line in cell_outlines(cell):
                    for paint in line:
                        check_preserved_paint(paint, theme, palette, add, strict, outline=True)
            if cell.is_spanned:
                continue
            width = sum(table.columns[i].width for i in range(col, col + cell.span_width))
            last_row = row + cell.span_height - 1
            height = sum(heights[row:last_row + 1])
            if not preserved:
                check_fill(cell._tc.tcPr, theme, palette, add)
            margins = (cell.margin_left, cell.margin_right, cell.margin_top, cell.margin_bottom)
            surface = fill_surface(theme, background, fill) if preserved else None
            needed, _ = check_text(cell.text_frame, shape, theme, palette, add, width, height, margins,
                                   top, slide_bottom, grows=True, background=surface,
                                   allow_quote_font=not preserved, annotations=annotations if preserved else None,
                                   preserved=preserved)
            # A altura gravada é mínima. O crescimento da célula desloca as linhas seguintes.
            heights[last_row] += max(0, needed - height)
        top += heights[row]


def check_shape(shape, theme, palette, add, slide_bottom, text_boxes, structural, annotations,
                preserved=False, background=None):
    if shape._element._nvXxPr.cNvPr.get("hidden") in {"1", "true"}:
        return
    preserved = preserved or is_preserved(shape)
    strict = shape._element in structural

    def finding(rule, message, severity="error"):
        if preserved and rule == "contrast":
            severity = "error"
        rejects = rule in {"font", "contrast", "fill_color", "outline_color", "text_color", "overflow"} and severity == "error"
        add(rule, message, severity, shape.name, preserved=preserved and not rejects)

    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        transform = shape._element.grpSpPr.xfrm
        child_origin, child_extent = transform.chOff, transform.chExt
        if shape.height and child_origin is not None and child_extent is not None:
            slide_bottom = child_origin.y + (slide_bottom - shape.top) * child_extent.cy / shape.height
        child_boxes = []
        surfaces = shape_surfaces(shape.shapes, theme, background)
        for child, surface in zip(shape.shapes, surfaces, strict=True):
            check_shape(child, theme, palette, add, slide_bottom, child_boxes, structural, annotations,
                        preserved, surface)
        # A comparação usa retângulos alinhados aos eixos do slide.
        if (child_boxes and child_origin is not None and child_extent is not None
            and child_extent.cx and child_extent.cy and not (shape.rotation or transform.flipH or transform.flipV)):
            scale_x, scale_y = shape.width / child_extent.cx, shape.height / child_extent.cy
            offset_x = shape.left - child_origin.x * scale_x
            offset_y = shape.top - child_origin.y * scale_y
            for child, top, rows in child_boxes:
                text_boxes.append((child, offset_y + top * scale_y, [
                    (offset_x + x1 * scale_x, offset_y + y1 * scale_y,
                     offset_x + x2 * scale_x, offset_y + y2 * scale_y)
                    for x1, y1, x2, y2 in rows
                ]))
    elif not shape.has_chart and shape._element.tag != qn("p:pic"):
        if preserved:
            for kind in ("fill", "ln"):
                paint, placeholder = shape_paint(shape, theme, kind)
                check_preserved_paint(paint, theme, palette, finding, strict, placeholder=placeholder,
                                      outline=kind == "ln")
        else:
            reference = shape._element.find(f"{qn('p:style')}/{qn('a:fillRef')}")
            check_fill(shape._element.find(qn("p:spPr")), theme, palette, finding, reference)
        if shape.has_text_frame:
            frame = shape.text_frame
            margins = (frame.margin_left, frame.margin_right, frame.margin_top, frame.margin_bottom)
            needed, rows = check_text(frame, shape, theme, palette, finding, shape.width, shape.height,
                                      margins, shape.top, slide_bottom, background=background if preserved else None,
                                      allow_quote_font=not preserved, annotations=annotations if preserved else None,
                                      preserved=preserved)
            if rows and not preserved and not shape.rotation:
                if (len(rows) > 1 and needed > shape.height
                    and frame.auto_size == MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT):
                    # Inclua os descendentes das linhas que avançam além da altura nominal.
                    nominal_bottom = shape.top + shape.height - margins[3]
                    for i, (x1, y1, x2, baseline) in enumerate(rows):
                        bottom = baseline + (baseline - y1) * DESCENT / CAP_HEIGHT
                        if bottom > nominal_bottom:
                            rows[i] = (x1, y1, x2, bottom)
                text_boxes.append((shape, shape.top, rows))
        if shape.has_table:
            check_table(shape, theme, palette, finding, slide_bottom, background, preserved, strict, annotations)


def score_slides(slide_count, style, findings):
    weights = {
        category: weight for category, (weight, _) in SCORE_CATEGORIES.items()
        if style != "padrao" or category not in {"transicao", "animacao"}
    }
    total_weight = sum(weights.values())
    gaps_by_slide = defaultdict(list)
    for item in findings:
        if item["severity"] == "error":
            rule = item["rule"]
            category = SCORE_CATEGORY_BY_RULE.get(rule, "leitura")
            gaps_by_slide[item["slide"]].append({
                "category": category, "rule": rule, "message": item["message"],
            })

    scores = []
    for slide in range(1, slide_count + 1):
        gaps = gaps_by_slide.get(slide, [])
        missing = {gap["category"] for gap in gaps}
        earned = sum(weight for category, weight in weights.items() if category not in missing)
        scores.append({"slide": slide, "score": earned * 100 // total_weight, "gaps": gaps})

    values = [item["score"] for item in scores]
    model_score = {
        "min": min(values, default=100),
        "mean": sum(values) // slide_count if slide_count else 100,
        "slides_below_100": slide_count - values.count(100),
    }
    return scores, model_score


def content_paragraphs(shapes):
    for shape in shapes:
        if shape.is_placeholder and shape.placeholder_format.type in CONTENT_METADATA:
            continue
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from content_paragraphs(shape.shapes)
        elif shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    yield from (paragraph.text for paragraph in cell.text_frame.paragraphs)
        elif shape.has_text_frame:
            yield from (paragraph.text for paragraph in shape.text_frame.paragraphs)
        else:
            for value in texts(shape):
                yield from value.split("\n")


def content_tokens(value):
    tokens = re.findall(r"\w+", normalize("NFC", value).casefold())
    for index, token in enumerate(tokens):
        if token.isdecimal():
            first = next((pos for pos, digit in enumerate(token) if decimal(digit)), len(token) - 1)
            tokens[index] = token[first:]
    return tokens


def align_paragraph(tokens, slides):
    best_kept = 0
    missing, replaced_by = tokens, []
    for slide in slides:
        matcher = SequenceMatcher(None, tokens, slide, autojunk=False)
        kept = sum(block.size for block in matcher.get_matching_blocks())
        if kept == len(tokens):
            inserted = [
                token
                for tag, start, _, output_start, output_end in matcher.get_opcodes()
                if tag == "insert" and 0 < start < len(tokens)
                for token in slide[output_start:output_end]
            ]
            return 0, [], inserted
        if kept <= best_kept:
            continue
        best_kept = kept
        missing, replaced_by = [], []
        for tag, start, end, output_start, output_end in matcher.get_opcodes():
            if tag in {"delete", "replace"}:
                missing.extend(tokens[start:end])
                replaced_by.extend(slide[output_start:output_end])
    return best_kept, missing, replaced_by


def compare_content(deck, source, numbers):
    output = [
        [token for paragraph in content_paragraphs(slide.shapes) for token in content_tokens(paragraph)]
        for slide in deck.slides
    ]
    # Os espaços delimitam tokens, inclusive nas extremidades do slide.
    searchable = [f" {' '.join(tokens)} " for tokens in output]

    def find(needle, start, end):
        return next((index for index in range(start, end) if needle in searchable[index]), None)

    slides = []
    paragraph_counts = Counter()
    for number in numbers:
        paragraphs = []
        for paragraph in content_paragraphs(source.slides[number - 1].shapes):
            tokens = content_tokens(paragraph)
            if tokens:
                paragraphs.append((paragraph, tokens, f" {' '.join(tokens)} "))
        slides.append((number, paragraphs))
        paragraph_counts.update({needle for _, _, needle in paragraphs})

    repeated = {needle for needle, count in paragraph_counts.items() if count > 1}
    starts, anchors, unique_hits = [], [], []
    cursor = 0
    for _, paragraphs in slides:
        starts.append(cursor)
        hits = [hit for _, _, needle in paragraphs
                if needle not in repeated and (hit := find(needle, cursor, len(output))) is not None]
        unique_hits.append(hits)
        if not hits:
            hits = [find(needle, cursor, len(output)) for _, _, needle in paragraphs if needle in repeated]
        cursor = min((hit for hit in hits if hit is not None), default=cursor)
        anchors.append(cursor)

    # Um título pode ficar em um slide separado, antes do primeiro parágrafo único.
    segment_starts = []
    segment_start = 0
    for index, anchor in enumerate(anchors):
        if index and anchors[index - 1] < anchor:
            last_previous = max((hit for hit in unique_hits[index - 1] if hit < anchor),
                                default=anchors[index - 1])
            segment_start = last_previous + 1
        segment_starts.append(segment_start)

    total = kept = 0
    divergences = []
    for index, ((number, paragraphs), start) in enumerate(zip(slides, starts, strict=True)):
        # Títulos repetidos ficam no trecho do próprio slide, inclusive se ele foi dividido.
        next_anchor = bisect_right(anchors, anchors[index])
        end = segment_starts[next_anchor] if next_anchor < len(anchors) else len(output)
        for paragraph, tokens, needle in paragraphs:
            total += len(tokens)
            left, right = (segment_starts[index], end) if needle in repeated else (start, len(output))
            if find(needle, left, right) is not None:
                kept += len(tokens)
                continue
            matched, missing, replaced_by = align_paragraph(tokens, output[left:min(left + 4, right)])
            kept += matched
            divergences.append({
                "origin_slide": number, "paragraph": paragraph,
                "missing": missing, "replaced_by": replaced_by,
            })
    return {
        "origin_tokens": total,
        "kept_tokens": kept,
        "fidelity_pct": 100 if kept == total else min(round(100 * kept / total, 2), 99.99),
        "divergences": divergences,
    }


def slide_images(slide, width, height):
    shapes = list(slide.shapes)
    backdrop = background_picture(slide, width, height)
    if backdrop is not None:
        shapes.insert(0, backdrop)
    # Replica a enumeração do extrair antes da ordenação por área.
    for shape in reading_order(shapes):
        yield from sized_images(shape)


def image_signature(part, crop=None):
    cropped = crop is not None and any((crop.l, crop.t, crop.r, crop.b))
    try:
        with Image.open(BytesIO(part.blob), formats=("PNG", "JPEG", "GIF", "BMP", "TIFF", "WEBP")) as image:
            if cropped:
                width, height = image.size
                box = (round(width * crop.l), round(height * crop.t),
                       round(width * (1 - crop.r)), round(height * (1 - crop.b)))
                if box[2] <= box[0] or box[3] <= box[1]:
                    raise ValueError("o recorte não contém pixels")
                image = image.crop(box)
            pixels = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS).tobytes()
    except UnidentifiedImageError:
        # Formatos vetoriais sem recorte ainda podem ser conferidos por igualdade binária.
        return None if cropped else part.sha1
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError(f"imagem {part.partname}: não foi possível calcular a fidelidade: {exc}") from exc
    digest = 0
    for start in range(0, len(pixels), 9):
        row = pixels[start:start + 9]
        for left, right in zip(row[:-1], row[1:], strict=True):
            digest = (digest << 1) | (left > right)
    return digest


def compare_images(deck, source, numbers, omitted_images, findings):
    width, height = source.slide_width, source.slide_height
    slide_area = width * height
    images = {"origin": 0, "kept": 0, "omitted": 0, "missing": []}
    candidates = []
    unknown = set(omitted_images)
    for number in numbers:
        for index, (part, crop, w, h) in enumerate(slide_images(source.slides[number - 1], width, height), 1):
            key = (number, index)
            unknown.discard(key)
            area = w * h
            if area < slide_area * 0.02:
                continue
            background = area >= slide_area * 0.90
            images["origin"] += not background
            if key in omitted_images:
                images["omitted"] += not background
            else:
                item = {"origin_slide": number, "index": index,
                        "width_pct": round(100 * w / width, 2), "height_pct": round(100 * h / height, 2)}
                candidates.append((part, crop, background, item))
    if unknown:
        invalid = ", ".join(f"{slide}:{index}" for slide, index in sorted(unknown))
        raise ValueError(f"--imagens-omitidas: imagem inexistente na seleção da origem: {invalid}")
    if not candidates:
        return images

    output_parts = {part for slide in deck.slides
                    for part, _, _, _ in slide_images(slide, deck.slide_width, deck.slide_height)}
    output = {image_signature(part) for part in output_parts}
    hashes = [digest for digest in output if isinstance(digest, int)]
    for part, crop, background, item in candidates:
        signature = image_signature(part, crop)
        found = signature in output or (
            isinstance(signature, int) and any((signature ^ digest).bit_count() <= 10 for digest in hashes)
        )
        if found:
            images["kept"] += not background
            continue
        if not background:
            images["missing"].append(item)
        label = "Imagem de fundo" if background else "Imagem"
        findings.append({"slide": item["origin_slide"], "shape": None, "rule": "content_image",
                         "severity": "warning" if background else "error",
                         "message": f"{label} {item['index']} ausente."})
    return images


def inspect(path, style, *, origin=None, origin_selection=None, omitted_images=frozenset()):
    deck = open_deck(path)
    palette = PALETTES[style]
    findings = []
    preserved_findings = []
    pending_image_slides = []
    for number, slide in enumerate(deck.slides, 1):
        def add(rule, message, severity="error", shape=None, *, preserved=False):
            target = preserved_findings if preserved else findings
            target.append({"slide": number, "shape": shape, "rule": rule,
                           "severity": "warning" if preserved else severity, "message": message})

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
        text_boxes = []
        roles = list(slide_shape_roles(slide.shapes, deck.slide_width * deck.slide_height))
        # Cada quadro tem um cabeçalho, mesmo quando o estilo ousado renomeia suas formas.
        pending_count = sum(shape.has_text_frame and shape.text.startswith("✦ PROMPT DE IMAGEM #")
                            for shape, _, _ in roles)
        if pending_count:
            pending_image_slides.append({"slide": number, "count": pending_count})
        structural = {shape._element for shape, strict, _ in roles if strict}
        annotations = annotation_colors(roles, theme)
        surfaces = shape_surfaces(slide.shapes, theme, slide_surface(slide, theme))
        for shape, surface in zip(slide.shapes, surfaces, strict=True):
            box = bounds(shape)
            if (shape.name not in BLEED_NAMES
                and (min(box[:2]) < -BOUNDS_TOLERANCE
                     or box[2] > deck.slide_width + BOUNDS_TOLERANCE
                     or box[3] > deck.slide_height + BOUNDS_TOLERANCE)
                and not legacy_arc(shape, box)):
                add("bounds", "Forma fora dos limites do slide.", shape=shape.name,
                    preserved=is_preserved(shape))
            check_shape(shape, theme, palette, add, deck.slide_height, text_boxes, structural, annotations,
                        background=surface)
        text_boxes.sort(key=lambda box: box[1])
        for (upper, _, upper_rows), (lower, _, lower_rows) in combinations(text_boxes, 2):
            if any(
                max(x1, a1) < min(x2, a2) and max(y1, b1) < min(y2, b2)
                for x1, y1, x2, y2 in upper_rows for a1, b1, a2, b2 in lower_rows
            ):
                severity = "warning" if MARKER_ONLY.fullmatch(upper.text.strip()) else "error"
                add("text_overlap", f"Texto sobreposto: {upper.name} invade a caixa de {lower.name}.",
                    severity, upper.name)
    slide_count = len(deck.slides)
    # Divergências de conteúdo apontam para slides da origem, que podem ter outra numeração.
    scores, model_score = score_slides(slide_count, style, findings)
    result = {"style": style, "slides": slide_count, "findings": findings,
              "scores": scores, "model_score": model_score,
              "pending_images": {"total": sum(item["count"] for item in pending_image_slides),
                                 "slides": pending_image_slides},
              "preserved_findings": preserved_findings, "preserved_warnings": len(preserved_findings)}
    if origin is not None:
        source = open_deck(origin)
        numbers = slide_numbers(origin_selection, len(source.slides))
        content = {"origin": str(origin), **compare_content(deck, source, numbers)}
        result["content"] = content
        for item in content["divergences"]:
            missing = " ".join(item["missing"])
            replacement = " ".join(item["replaced_by"])
            message = f"Trecho ausente ou fora de ordem: {missing}."
            if not missing:
                message = f"Trecho inserido: {replacement}."
            elif replacement:
                message = f"Trecho trocado: {missing} por {replacement}."
            findings.append({"slide": item["origin_slide"], "shape": None, "rule": "content",
                             "severity": "error", "message": message})
        images = compare_images(deck, source, numbers, omitted_images, findings)
        content["images"] = images
        expected = images["origin"] - images["omitted"]
        kept = images["kept"]
        content["image_fidelity_pct"] = 100 if kept == expected else min(round(100 * kept / expected, 2), 99.99)
    result["errors"] = sum(item["severity"] == "error" for item in findings)
    result["warnings"] = sum(item["severity"] == "warning" for item in findings)
    return result


def report(path, style, *, as_json=False, origin=None, origin_selection=None, omitted_images=frozenset()):
    result = inspect(path, style, origin=origin, origin_selection=origin_selection, omitted_images=omitted_images)
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Conferência ({style}): {result['slides']} slide(s), "
              f"{result['errors']} reprovação(ões), {result['warnings']} aviso(s), "
              f"{result['preserved_warnings']} aviso(s) em conteúdo preservado.")
        for item in result["findings"]:
            severity = "Reprovação" if item["severity"] == "error" else "Aviso"
            shape = f" ({item['shape']})" if item["shape"] else ""
            source = " da origem" if item["rule"] in {"content", "content_image"} else ""
            print(f"Slide {item['slide']}{source}{shape} | {severity}: {item['message']}")
        counts = Counter((item["slide"], item["rule"]) for item in result["preserved_findings"])
        for (slide, rule), count in sorted(counts.items()):
            singular, plural = PRESERVED_WARNING_LABELS[rule]
            label = singular if count == 1 else plural
            print(f"Slide {slide} | Aviso: conteúdo preservado com {count} {label}.")
        model_score = result["model_score"]
        total = result["slides"]
        perfect = total - model_score["slides_below_100"]
        print(f"Placar do modelo: {model_score['min']}/100 ({perfect} de {total} slides com 100)")
        for item in result["scores"]:
            if item["score"] < 100:
                categories = ", ".join(sorted({gap["category"] for gap in item["gaps"]}))
                print(f"Slide {item['slide']} | Placar do modelo: {item['score']}/100 | "
                      f"Categorias faltantes: {categories}")
        if "content" in result:
            print(f"Fidelidade de conteúdo: {result['content']['fidelity_pct']:g}%")
            images = result["content"]["images"]
            print(f"Imagens de conteúdo: {images['kept']} de {images['origin']} ({images['omitted']} omitidas)")
        pending = result["pending_images"]
        if pending["total"]:
            print(f"Imagens pendentes (quadros de prompt): {pending['total']} em {len(pending['slides'])} slides")
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
