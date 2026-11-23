"""Extrai um roteiro e reaproveita objetos editáveis de slides PowerPoint."""

from collections import Counter
from colorsys import hls_to_rgb, rgb_to_hls
from copy import deepcopy
from io import BytesIO
import json
import math
from pathlib import Path
import re
from typing import NamedTuple
from unicodedata import category
from zipfile import BadZipFile

from PIL import Image, ImageStat, JpegImagePlugin, UnidentifiedImageError
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.exc import PackageNotFoundError
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.oxml import serialize_part_xml
from pptx.opc.packuri import PackURI
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.oxml.shapes.picture import CT_Picture
from pptx.shapes.picture import Picture
from pptx.text.text import Font
from pptx.util import Inches, Length, Pt


REL_PREFIX = qn("r:id").split("}")[0] + "}"
GROUP = MSO_SHAPE_TYPE.GROUP
NUMBER = re.compile(r"\d+(?:\s*/\s*\d+)?")
QUOTE_END = {'"': '"', "'": "'", "“": "”", "‘": "’", "«": "»"}


def open_deck(path):
    try:
        return Presentation(str(path))
    except (OSError, ValueError, KeyError, PackageNotFoundError, BadZipFile) as exc:
        raise ValueError(f"não foi possível abrir o deck {path}: {exc}") from exc


def slide_numbers(selection, total):
    if selection is None:
        return range(1, total + 1)
    numbers = set()
    for item in selection.split(","):
        match = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", item.strip())
        if not match:
            raise ValueError(f"seletor inválido: {item!r}. Use números e intervalos como 3,5-9.")
        first = int(match[1])
        last = int(match[2] or match[1])
        if not 1 <= first <= last <= total:
            raise ValueError(f"seletor fora do deck de {total} slides: {item!r}")
        numbers.update(range(first, last + 1))
    return sorted(numbers)


def reading_order(shapes):
    return sorted(shapes, key=lambda shape: (shape.top or 0, shape.left or 0))


def texts(shape):
    if shape.shape_type == GROUP:
        for child in reading_order(shape.shapes):
            yield from texts(child)
    elif shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                if cell.text:
                    yield cell.text
    elif shape.has_text_frame and shape.text:
        yield shape.text
    elif shape.has_chart:
        if shape.chart.has_title and shape.chart.chart_title.has_text_frame:
            yield shape.chart.chart_title.text_frame.text
        for node in shape.chart._element.iter(qn("c:tx"), qn("c:cat")):
            for value in node.iter(qn("c:v"), qn("a:t")):
                if value.text:
                    yield value.text


def relationship_attributes(element):
    for node in element.iter():
        for key, rid in node.attrib.items():
            if key.startswith(REL_PREFIX) and rid:
                yield node, key, rid


def image_references(shape):
    for node, _, rid in relationship_attributes(shape._element):
        rel = shape.part.rels.get(rid)
        if rel is not None and rel.reltype == RT.IMAGE and not rel.is_external:
            yield node, rel.target_part


def covers_slide(shape, width, height):
    left, top = shape.left or 0, shape.top or 0
    return (shape.rotation == 0 and left <= width * 0.01 and top <= height * 0.01
            and left + (shape.width or 0) >= width * 0.99
            and top + (shape.height or 0) >= height * 0.99)


def is_full_slide_picture(shape, width, height):
    return (
        shape._element.tag == qn("p:pic")
        or shape._element.find(f"{qn('p:spPr')}/{qn('a:blipFill')}") is not None
    ) and covers_slide(shape, width, height)


def background_picture(slide, width, height):
    fill = slide._element.find(f"{qn('p:cSld')}/{qn('p:bg')}/{qn('p:bgPr')}/{qn('a:blipFill')}")
    if fill is None or fill.blip is None:
        return None
    blip = fill.blip
    rid = blip.get(qn("r:embed")) or blip.get(qn("r:link"))
    if not rid:
        return None
    element = CT_Picture.new_pic(0, "Original slide background image", "", rid, 0, 0, width, height)
    copied_fill = deepcopy(fill)
    copied_fill.tag = qn("p:blipFill")
    element.replace(element.blipFill, copied_fill)
    return Picture(element, slide.shapes)


def is_decoration(shape, width, height):
    label = shape.name.casefold().lstrip("!").replace("_", " ")
    if re.match(r"(?:logo(?:tipo)?|slide number|page number|número (?:de|do) (?:slide|página))\b", label):
        return True
    if shape.is_placeholder and shape.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
        return True
    x, y, w, h = shape.left or 0, shape.top or 0, shape.width or 0, shape.height or 0
    value = shape.text if shape.has_text_frame else ""
    corner = x <= width * 0.1 or x + w >= width * 0.9
    picture = shape._element.tag == qn("p:pic")
    if picture and corner and w <= width * 0.12 and h <= height * 0.16:
        return y <= height * 0.05 or y + h >= height * 0.95
    return corner and y >= height * 0.9 and h <= height * 0.1 and NUMBER.fullmatch(value.strip())


def shape_fill(shape, theme):
    properties = shape._element.find(qn("p:spPr"))
    if properties is None:
        return None, None
    fill = properties.eg_fillProperties
    placeholder = None
    if fill is None:
        reference = shape._element.find(f"{qn('p:style')}/{qn('a:fillRef')}")
        styles = theme.theme.find(f".//{qn('a:fillStyleLst')}")
        if reference is not None and styles is not None:
            index = int(reference.get("idx", 0))
            if 1 <= index <= len(styles):
                fill = styles[index - 1]
                placeholder = next(iter(reference), None)
    return fill, placeholder


def solid_fill_color(theme, fill, placeholder=None):
    if fill is None or fill.tag != qn("a:solidFill") or not len(fill):
        return None
    color = solid_color(fill[0], theme, placeholder)
    return color if rgb_channels(color) is not None else None


def slide_content(presentation, slide):
    from conferir import Theme

    shapes = list(slide.shapes)
    width, height = presentation.slide_width, presentation.slide_height
    picture = background_picture(slide, width, height)
    if picture is not None:
        shapes.insert(0, picture)
    title = slide.shapes.title
    content = []
    backdrops = []
    rectangle_color = None
    for shape in shapes:
        if is_full_slide_picture(shape, width, height):
            backdrops.append(shape)
        elif (shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and shape.auto_shape_type == MSO_SHAPE.RECTANGLE
              and not shape.text and covers_slide(shape, width, height)):
            theme = Theme(slide, presentation)
            color = solid_fill_color(theme, *shape_fill(shape, theme))
            if color is None:
                content.append(shape)
            else:
                rectangle_color = color
        elif not is_decoration(shape, width, height):
            content.append(shape)
    if title is None or not title_line(title.text):
        # Sem placeholder, o primeiro texto curto na faixa superior é o candidato a título.
        title = next((shape for shape in reading_order(content)
                      if shape.has_text_frame and (shape.top or 0) <= height * 0.22
                      and 0 < len(title_line(shape.text)) <= 150), None)
    return shapes, title, backdrops, content, rectangle_color


def title_line(text):
    # python-pptx já traduz quebras DrawingML para tabulação vertical.
    text = re.sub(r"<a:br\s*/>", " ", text)
    text = re.sub(r"(?<=\s)[-:](?=\s)", " ", text)
    return " ".join(text.split())


def normalize_title(text):
    words = "".join(" " if category(char).startswith("P") else char for char in title_line(text).casefold())
    return " ".join(words.split())


def rgb_channels(color):
    if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
        return None
    return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))


def solid_color(node, theme, placeholder=None):
    color = theme.color(node, placeholder)
    channels = rgb_channels(color)
    if channels is None:
        return color
    hue, lightness, saturation = rgb_to_hls(*channels)
    for change in node:
        if change.tag == qn("a:lumMod"):
            lightness *= int(change.get("val")) / 100000
        elif change.tag == qn("a:lumOff"):
            lightness += int(change.get("val")) / 100000
    return "".join(f"{round(value * 255):02X}"
                   for value in hls_to_rgb(hue, min(1, max(0, lightness)), saturation))


def luminance(color):
    channels = rgb_channels(color)
    if channels is None:
        return None
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))


def is_dark(color):
    level = luminance(color)
    return level is not None and level < 0.179


def contrast_ratio(color, background):
    low, high = sorted((luminance(color), luminance(background)))
    return (high + 0.05) / (low + 0.05)


def readable_color(color, background):
    if background is None or contrast_ratio(color, background) >= 4.5:
        return color
    hue, lightness, saturation = rgb_to_hls(*rgb_channels(color))
    choices = []
    for endpoint, extreme in ((0, "000000"), (1, "FFFFFF")):
        if contrast_ratio(extreme, background) < 4.5:
            continue
        fails, passes = lightness, endpoint
        best = extreme
        for _ in range(12):
            middle = (fails + passes) / 2
            candidate = "".join(f"{round(value * 255):02X}" for value in hls_to_rgb(hue, middle, saturation))
            if contrast_ratio(candidate, background) >= 4.5:
                passes, best = middle, candidate
            else:
                fails = middle
        choices.append((abs(passes - lightness), best))
    return min(choices)[1]


def slide_surface(slide, theme):
    for layer in (slide, theme.layout, theme.master):
        background = layer._element.cSld.bg
        if background is None:
            continue
        if background.bgPr is not None:
            return solid_fill_color(theme, background.bgPr.eg_fillProperties)
        colors = list(theme.referenced_fills(background.bgRef))
        return colors[0] if len(colors) == 1 and rgb_channels(colors[0]) is not None else None
    return "FFFFFF"


def fill_surface(theme, background, fill, placeholder=None):
    if fill is None or fill.tag in {qn("a:noFill"), qn("a:grpFill")}:
        return background
    color = solid_fill_color(theme, fill, placeholder)
    return visible_color(color, fill[0], background) if color is not None else None


def visible_color(color, node, background):
    alpha = node.find(qn("a:alpha")) if node is not None else None
    if alpha is None or alpha.get("val") == "100000":
        return color
    if background is None:
        return None
    opacity = int(alpha.get("val")) / 100000
    return "".join(f"{round(255 * (front * opacity + back * (1 - opacity))):02X}"
                   for front, back in zip(rgb_channels(color), rgb_channels(background), strict=True))


def cell_surface(cell, theme, background):
    fill = cell._tc.tcPr.eg_fillProperties if cell._tc.tcPr is not None else None
    return fill_surface(theme, background, fill)


def shape_surfaces(shapes, theme, background):
    layers = []
    for shape in shapes:
        if shape._element._nvXxPr.cNvPr.get("hidden") in {"1", "true"}:
            yield background
            continue
        left, top, width, height = shape_frame(shape)
        x, y = left + width / 2, top + height / 2
        behind = next((color for box, color in reversed(layers)
                       if box[0] <= x <= box[2] and box[1] <= y <= box[3]), background)
        fill, placeholder = shape_fill(shape, theme)
        surface = fill_surface(theme, behind, fill, placeholder)
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            layers.append((bounds(shape), None))
        elif (shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and shape.auto_shape_type == MSO_SHAPE.RECTANGLE
              and not shape.rotation and fill is not None and fill.tag != qn("a:noFill")):
            layers.append((bounds(shape), surface))
        yield surface


def dark_image_fill(fill, part):
    blip = fill.blip
    relationship = part.rels.get(blip.get(qn("r:embed"))) if blip is not None else None
    if relationship is None or relationship.is_external or relationship.reltype != RT.IMAGE:
        return False
    try:
        with Image.open(BytesIO(relationship.target_part.blob)) as image:
            image.thumbnail((64, 64), Image.Resampling.BOX)
            channels = ImageStat.Stat(image.convert("RGB")).mean
    except (OSError, Image.DecompressionBombError):
        return False
    return is_dark("".join(f"{round(channel):02X}" for channel in channels))


def has_dark_background(presentation, slide):
    from conferir import Theme, fill_colors

    layout = slide.slide_layout
    for owner in (slide, layout, layout.slide_master):
        background = owner._element.cSld.bg
        if background is None:
            continue
        properties = background.bgPr
        if properties is not None:
            fill = properties.eg_fillProperties
            if fill is not None and fill.tag == qn("a:blipFill"):
                return dark_image_fill(fill, owner.part)
            theme = Theme(slide, presentation)
            if fill is not None and fill.tag == qn("a:solidFill") and len(fill):
                return is_dark(solid_color(fill[0], theme))
            colors = list(fill_colors(properties, theme))
        else:
            colors = list(Theme(slide, presentation).referenced_fills(background.bgRef))
        return bool(colors) and all(is_dark(color) for color in colors)
    return False


def is_drawing(shape):
    if shape.shape_type in (MSO_SHAPE_TYPE.LINE, MSO_SHAPE_TYPE.FREEFORM, GROUP):
        return True
    return (shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
            and (not shape.text.strip() or "ARROW" in shape.auto_shape_type.name))


def shape_size(shape):
    if shape.has_table:
        # O quadro de uma tabela importada pode divergir da grade que é exibida.
        return sum(column.width for column in shape.table.columns), sum(row.height for row in shape.table.rows)
    return shape.width or 0, shape.height or 0


def bounds(shape, size=None):
    return frame_bounds(shape_frame(shape, size), shape.rotation)


def shape_frame(shape, size=None):
    return shape.left or 0, shape.top or 0, *(shape_size(shape) if size is None else size)


def frame_bounds(frame, rotation):
    x, y, w, h = frame
    angle = math.radians(rotation)
    dx = (abs(w * math.cos(angle)) + abs(h * math.sin(angle))) / 2
    dy = (abs(w * math.sin(angle)) + abs(h * math.cos(angle))) / 2
    return x + w / 2 - dx, y + h / 2 - dy, x + w / 2 + dx, y + h / 2 + dy


def has_paint(shape):
    from conferir import FILL_TAGS

    properties = shape._element.spPr
    style = shape._element.find(qn("p:style"))
    for node, reference in ((properties, "fillRef"), (properties.ln, "lnRef")):
        fill = next((item for item in node if item.tag in FILL_TAGS), None) if node is not None else None
        if fill is not None:
            if fill.tag != qn("a:noFill"):
                return True
            continue
        ref = style.find(qn(f"a:{reference}")) if style is not None else None
        if ref is not None and ref.get("idx") not in (None, "0", "1000"):
            return True
        if reference == "lnRef" and node is not None:
            return True
    return False


def visible_shape(shape):
    if shape._element._nvXxPr.cNvPr.get("hidden") in ("1", "true"):
        return False
    if shape._element.tag not in (qn("p:sp"), qn("p:cxnSp")):
        return True
    if shape.has_text_frame and shape.text.strip():
        return True
    return not shape.is_placeholder and has_paint(shape)


def text_fit_frame(shape, theme, slide_height):
    from conferir import check_text

    if not shape.has_text_frame or not shape.text.strip() or has_paint(shape):
        return None
    frame = shape.text_frame
    if (frame.auto_size not in (MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT, MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE)
            or frame._bodyPr.get("vert", "horz") != "horz"):
        return None
    margins = frame.margin_left, frame.margin_right, frame.margin_top, frame.margin_bottom
    height, rows = check_text(frame, shape, theme, set(), lambda *args: None, shape.width, shape.height,
                              margins, shape.top, slide_height)
    if not rows:
        return None
    left = min(row[0] for row in rows)
    right = max(row[2] for row in rows)
    top = min(row[1] for row in rows)
    bottom = max(row[3] for row in rows)
    x, y, w, h = shape.left, shape.top, shape.width, shape.height
    width = right - left + margins[0] + margins[1]
    if w > 1.3 * (right - left) and w > width:
        x, w = left - margins[0], width
    if h > 1.3 * (bottom - top):
        anchor = {MSO_ANCHOR.MIDDLE: 0.5, MSO_ANCHOR.BOTTOM: 1}.get(frame.vertical_anchor, 0)
        offset = anchor * max(0, h - height)
        if frame.auto_size == MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT:
            height = bottom - y - offset + margins[3]
        if h > height:
            y, h = y + offset, height
    trimmed = x, y, w, h
    return rotated_crop(shape, trimmed) if trimmed != shape_frame(shape) else None


def rotated_crop(shape, frame):
    x, y, w, h = frame
    left, top, width, height = shape_frame(shape)
    dx = x + w / 2 - (left + width / 2)
    dy = y + h / 2 - (top + height / 2)
    transform = shape._element.xfrm
    if transform is not None:
        dx = -dx if transform.flipH else dx
        dy = -dy if transform.flipV else dy
    angle = math.radians(shape.rotation)
    return (left + (width - w) / 2 + dx * math.cos(angle) - dy * math.sin(angle),
            top + (height - h) / 2 + dx * math.sin(angle) + dy * math.cos(angle), w, h)


def text_bounds(shape, theme, slide_height, *, original=False):
    """Estima a extensão vertical com folga sem alterar a caixa editável."""
    from conferir import check_text

    def padded_height(frame, width, height, margins, top):
        if not frame.text.strip():
            return 0
        if frame._bodyPr.get("vert", "horz") != "horz":
            return height
        needed, _ = check_text(frame, shape, theme, set(), lambda *args: None,
                               width, height, margins, top, slide_height)
        if not needed:
            return height
        anchor = {MSO_ANCHOR.MIDDLE: 0.5, MSO_ANCHOR.BOTTOM: 1}.get(frame.vertical_anchor, 0)
        offset = anchor * max(0, height - needed)
        return offset + needed + 0.2 * (needed - margins[2] - margins[3])

    if not visible_shape(shape):
        return None
    x, y, width, height = shape_frame(shape)
    if shape.shape_type == GROUP:
        transform = shape._element.xfrm
        if transform is None:
            return None
        origin, extent = transform.chOff, transform.chExt
        boxes = [box for child in shape.shapes
                 if (box := text_bounds(child, theme, slide_height, original=original)) is not None]
        if not boxes or origin is None or extent is None:
            return None
        scale_x = width / extent.cx if extent.cx else 1
        scale_y = height / extent.cy if extent.cy else 1
        left, top = min(box[0] for box in boxes), min(box[1] for box in boxes)
        right, bottom = max(box[2] for box in boxes), max(box[3] for box in boxes)
        frame = (x + (left - origin.x) * scale_x, y + (top - origin.y) * scale_y,
                 (right - left) * scale_x, (bottom - top) * scale_y)
        return frame_bounds(rotated_crop(shape, frame), shape.rotation)
    if shape.has_text_frame and shape.text.strip():
        frame = shape.text_frame
        fixed = frame.auto_size in (None, MSO_AUTO_SIZE.NONE)
        if original and fixed:
            return bounds(shape)
        margins = frame.margin_left, frame.margin_right, frame.margin_top, frame.margin_bottom
        needed = padded_height(frame, width, height, margins, y)
        if fixed:
            needed = max(height, needed)
    elif shape.has_table:
        table = shape.table
        heights = [row.height for row in table.rows]
        top = y
        for index, row in enumerate(table.rows):
            for col, cell in enumerate(row.cells):
                if cell.is_spanned or not cell.text.strip():
                    continue
                end = index + cell.span_height
                cell_height = sum(heights[index:end])
                cell_width = sum(table.columns[i].width for i in range(col, col + cell.span_width))
                margins = cell.margin_left, cell.margin_right, cell.margin_top, cell.margin_bottom
                needed = padded_height(cell.text_frame, cell_width, cell_height, margins, top)
                heights[end - 1] += max(0, needed - cell_height)
            top += heights[index]
        needed = top - y
    else:
        return None
    return frame_bounds(rotated_crop(shape, (x, y, width, needed)), shape.rotation)


def visible_copy(shape, element, theme, slide_height):
    if not visible_shape(shape):
        return None
    if shape.shape_type != GROUP:
        return element, text_fit_frame(shape, theme, slide_height)

    geometry = []
    changed = False
    for child, child_element in zip(shape.shapes, list(element.iter_shape_elms()), strict=True):
        copied = visible_copy(child, child_element, theme, slide_height)
        if copied is None:
            element.remove(child_element)
            changed = True
            continue
        _, frame = copied
        if frame is not None:
            child_element.x, child_element.y, child_element.cx, child_element.cy = map(round, frame)
            changed = True
        geometry.append(frame_bounds(frame or shape_frame(child), child.rotation))
    if not geometry:
        return None
    transform = element.xfrm
    if not changed or transform is None:
        return element, None
    child_origin, child_extent = transform.chOff, transform.chExt
    if child_origin is None or child_extent is None:
        return element, None

    left = math.floor(min(rect[0] for rect in geometry))
    top = math.floor(min(rect[1] for rect in geometry))
    width = math.ceil(max(rect[2] for rect in geometry)) - left
    height = math.ceil(max(rect[3] for rect in geometry)) - top
    # Mantém a escala dos filhos ao reduzir a moldura do grupo.
    scale_x = shape.width / child_extent.cx if child_extent.cx else 1
    scale_y = shape.height / child_extent.cy if child_extent.cy else 1
    frame = (shape.left + (left - child_origin.x) * scale_x,
             shape.top + (top - child_origin.y) * scale_y, width * scale_x, height * scale_y)
    child_origin.x, child_origin.y = left, top
    child_extent.cx, child_extent.cy = width, height
    return element, rotated_crop(shape, frame)


def overlaps(first, second):
    x1, y1, x2, y2 = first
    a1, b1, a2, b2 = second
    # A igualdade conta a linha horizontal ou vertical sobre a imagem.
    return x1 <= a2 and a1 <= x2 and y1 <= b2 and b1 <= y2


def is_title_rule(shape, title_bounds):
    if shape.shape_type != MSO_SHAPE_TYPE.LINE or shape.line.width > Pt(3):
        return False
    left, top, right, bottom = title_bounds
    x1, y1, x2, y2 = bounds(shape)
    gap = Inches(0.30)
    # Pelo menos metade do fio deve acompanhar a caixa do título no eixo longo.
    if x2 - x1 <= 1 and y2 > y1:
        overlap = min(y2, bottom) - max(y1, top)
        return 2 * overlap >= y2 - y1 and min(abs(x1 - left), abs(x1 - right)) <= gap
    if y2 - y1 <= 1 and x2 > x1:
        overlap = min(x2, right) - max(x1, left)
        return 2 * overlap >= x2 - x1 and min(abs(y1 - top), abs(y1 - bottom)) <= gap
    return False


def drawing_counts(shapes):
    images = [(shape.shape_id, bounds(shape)) for shape in shapes
              if next(image_references(shape), None) is not None]
    drawings = overlays = 0
    for shape in shapes:
        if is_drawing(shape):
            drawings += 1
            overlays += any(shape.shape_id != image_id and overlaps(bounds(shape), box)
                            for image_id, box in images)
        if shape.shape_type == GROUP:
            child_drawings, child_overlays = drawing_counts(shape.shapes)
            drawings += child_drawings
            overlays += child_overlays
    return drawings, overlays


def sized_images(shape, scale_x=1, scale_y=1):
    width, height = shape_size(shape)
    if shape.shape_type == GROUP:
        transform = shape._element.xfrm
        child_extent = transform.chExt if transform is not None else None
        if child_extent is not None:
            scale_x *= width / child_extent.cx if child_extent.cx else 1
            scale_y *= height / child_extent.cy if child_extent.cy else 1
        for child in shape.shapes:
            yield from sized_images(child, scale_x, scale_y)
    else:
        for node, part in image_references(shape):
            crop = node.getparent().find(qn("a:srcRect")) if node.tag == qn("a:blip") else None
            yield part, crop, width * scale_x, height * scale_y


def cropped_image(part, crop):
    if crop is None or not any((crop.l, crop.t, crop.r, crop.b)):
        return None
    try:
        image = Image.open(BytesIO(part.blob), formats=("PNG", "JPEG", "GIF", "BMP", "TIFF", "WEBP"))
    except UnidentifiedImageError:
        return None
    with image:
        width, height = image.size
        left, top = round(width * crop.l), round(height * crop.t)
        right, bottom = round(width * (1 - crop.r)), round(height * (1 - crop.b))
        box = left, top, right, bottom
        if box == (0, 0, width, height):
            return None
        if right <= left or bottom <= top:
            raise ValueError("o recorte não contém pixels")
        padded = left < 0 or top < 0 or right > width or bottom > height
        output = BytesIO()
        if image.format == "JPEG" and not padded:
            image.crop(box).save(output, "JPEG", qtables=image.quantization,
                                 subsampling=JpegImagePlugin.get_sampling(image),
                                 icc_profile=image.info.get("icc_profile"))
            return output.getvalue(), part.partname.ext
        if padded or image.format != "PNG":
            image = image.convert("RGBA")
        image.crop(box).save(output, "PNG")
        return output.getvalue(), "png"


def extract(deck, folder, selection):
    presentation = open_deck(deck)
    total = len(presentation.slides)
    numbers = slide_numbers(selection, total)
    width, height = presentation.slide_width, presentation.slide_height
    image_frequency = Counter()
    for slide in presentation.slides:
        backdrop = background_picture(slide, width, height)
        shapes = list(slide.shapes)
        if backdrop is not None:
            shapes.append(backdrop)
        image_frequency.update({part.sha1 for shape in shapes for _, part in image_references(shape)})
    # Conta a presença em pelo menos 90% do deck inteiro, mesmo com --slides.
    repeated = {digest for digest, count in image_frequency.items() if count > 1 and count * 10 >= total * 9}
    (folder / "img").mkdir(parents=True, exist_ok=True)
    slides = []
    section_number = 0
    source = str(deck.resolve())
    for number in numbers:
        slide = presentation.slides[number - 1]
        shapes, title, backdrops, content, _ = slide_content(presentation, slide)
        content = backdrops + [
            shape for shape in content if title is None or shape.shape_id != title.shape_id
        ]
        ordered = reading_order(shapes)
        images = []
        content_ids = {shape.shape_id for shape in content}
        candidates = []
        for shape in ordered:
            for part, crop, w, h in sized_images(shape):
                decorative = (shape.shape_id not in content_ids or w < width * 0.06 or h < height * 0.06
                              or part.sha1 in repeated)
                candidates.append((w * h, part, crop, decorative))
        # Mantém o nome de cada arquivo na ordem original e ordena apenas a lista do roteiro.
        ranked = sorted(enumerate(candidates, 1), key=lambda item: item[1][0], reverse=True)
        for index, (_, part, crop, decorative) in ranked:
            try:
                cropped = cropped_image(part, crop)
            except (OSError, ValueError) as exc:
                raise ValueError(f"slide {number}, imagem {part.partname}: não foi possível aplicar o recorte: {exc}") from exc
            blob, extension = cropped if cropped is not None else (part.blob, part.partname.ext)
            path = f"img/slide-{number}-{index}.{extension}"
            (folder / path).write_bytes(blob)
            item = {"caminho": path, "decorativa": decorative}
            if cropped is not None:
                item["recortada"] = True
            images.append(item)
        content_images = [image["caminho"] for image in images if not image["decorativa"]]
        drawings, annotations = drawing_counts(content)
        title_text = title.text if title is not None else ""
        heading = title_text.strip()
        paragraphs = [value for shape in reading_order(content) for value in texts(shape) if value.strip()]
        topics = [line for value in paragraphs for line in value.splitlines() if line.strip()]
        entry = {
            "origem": number, "deck": source, "slide": number, "titulo": title_line(title_text),
            "textos": [value for shape in ordered for value in texts(shape)],
            "imagens": images, "formas_desenhadas": drawings,
        }
        # Preserva composições complexas antes de sugerir um layout, inclusive no primeiro slide.
        complex_content = (annotations >= 4 or len(content_images) > 1
                           or any(shape.has_table or shape.has_chart for shape in content))
        short_heading = bool(heading) and len(heading) <= 80 and len(heading.splitlines()) == 1
        entry["revisar"] = False
        if not (heading or paragraphs):
            entry["tipo"] = "preservado"
            visual_content = content_images or any(
                shape._element.tag != qn("p:pic")
                and not (shape.has_text_frame and (shape.is_placeholder or shape.shape_type == MSO_SHAPE_TYPE.TEXT_BOX))
                for shape in content
            )
            if visual_content:
                entry.update(revisar=True, motivo="conteúdo só em imagem")
            else:
                entry["vazio"] = True
        elif complex_content or (not content_images and drawings and not (short_heading and len(topics) == 1)):
            entry["tipo"] = "preservado"
        elif number == 1 and heading:
            entry["tipo"] = "capa"
        elif content_images:
            if Path(content_images[0]).suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}:
                entry.update(tipo="texto_imagem", imagem=content_images[0], imagem_modo="conter", topicos=topics)
            else:
                entry["tipo"] = "preservado"
        else:
            # Citação ocupa o slide inteiro. Divisória admite uma linha de chamada além do título curto.
            blocks = ([heading] if heading else []) + paragraphs
            quote = blocks[0].strip() if len(blocks) == 1 else ""
            if len(quote) > 2 and quote[1:-1].strip() and quote[-1] == QUOTE_END.get(quote[0]):
                entry.update(tipo="frase", frase=quote)
            elif topics and any(word in heading.casefold() for word in ("conteúdo", "sumário")):
                entry.update(tipo="sumario", itens=topics)
            elif short_heading and len(topics) <= 1:
                section_number += 1
                entry.update(tipo="modulo", numero=section_number)
                if topics:
                    entry["selo"] = topics[0]
            else:
                entry.update(tipo="texto_imagem", imagem_modo="conter", topicos=topics)
        if entry["tipo"] not in {"preservado", "capa", "modulo"}:
            entry["revisar"] = True
        slides.append(entry)
    path = folder / "roteiro-rascunho.json"
    path.write_text(json.dumps({"estilo": "ousado", "avulso": True, "slides": slides},
                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


class PreservedFrame(NamedTuple):
    x: Length
    y: Length
    width: Length
    height: Length
    panel_color: RGBColor


class PreservedSlides:
    """Reusa cada deck de origem e importa partes OPC uma vez por geração."""

    def __init__(self):
        self.decks = {}
        self.parts = {}

    def source(self, path, number):
        if not isinstance(path, str) or not path:
            raise ValueError("informe o caminho do deck para o tipo preservado")
        if type(number) is not int or number < 1:
            raise ValueError(f"informe um número de slide positivo em {path}")
        path = Path(path).resolve()
        if path not in self.decks:
            self.decks[path] = open_deck(path)
        deck = self.decks[path]
        if number > len(deck.slides):
            raise ValueError(f"slide {number} fora do deck {path} ({len(deck.slides)} slides)")
        return deck, deck.slides[number - 1]

    def import_part(self, original, package):
        if original in self.parts:
            return self.parts[original]
        # O diretório fica igual para resolver os alvos relativos dos .rels originais.
        name = PackURI(f"{original.partname.baseURI}/restyle-{len(self.parts) + 1}-{original.partname.filename}")
        part = type(original).load(name, original.content_type, package, original.blob)
        self.parts[original] = part
        if original.rels:
            linked = {rel.target_part.partname: self.import_part(rel.target_part, package)
                      for rel in original.rels.values() if not rel.is_external}
            part.load_rels_from_xml(parse_xml(original.rels.xml), linked)
        return part

    def copy(self, target, script, box):
        from conferir import Theme

        deck, source = self.source(script.get("deck"), script.get("slide"))
        _, title, backdrops, content, rectangle_color = slide_content(deck, source)
        titles = {normalize_title(script.get("titulo", ""))}
        if title is not None:
            titles.add(normalize_title(title.text))
        titles.discard("")
        for index, shape in enumerate(content):
            if shape.has_text_frame and normalize_title(shape.text) in titles:
                del content[index]
                title_bounds = bounds(shape)
                content = [item for item in content if not is_title_rule(item, title_bounds)]
                break
        theme = Theme(source, deck)
        copies = [(shape, *copy) for shape in backdrops + content
                  if (copy := visible_copy(shape, deepcopy(shape._element), theme, deck.slide_height)) is not None]
        if not copies:
            return []
        x, y, w, h, panel_color = box
        dark = not backdrops and (is_dark(rectangle_color) if rectangle_color is not None
                                  else has_dark_background(deck, source))
        if dark:
            panel = target.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
            panel.name = "Preserved content background"
            panel.shadow.inherit = False
            panel.fill.solid()
            panel.fill.fore_color.rgb = panel_color
            panel.line.fill.background()

        geometry = [frame_bounds(frame or shape_frame(shape), shape.rotation) for shape, _, frame in copies]
        text_geometry = [rect for shape, _, _ in copies
                         if (rect := text_bounds(shape, theme, deck.slide_height, original=True)) is not None]
        left = min(rect[0] for rect in geometry)
        top = min(rect[1] for rect in geometry)
        width = max(rect[2] for rect in geometry) - left
        height = max(rect[3] for rect in geometry + text_geometry) - top
        scale = min(w / width if width else math.inf, h / height if height else math.inf)
        if not math.isfinite(scale):
            scale = 1
        target_deck = target.part.package.presentation_part.presentation
        target_theme = Theme(target, target_deck)
        existing = list(target.shapes)
        background = slide_surface(target, target_theme)
        # Fontes herdadas e novas quebras podem mudar a altura após a escala.
        for _ in range(64):
            dx = x + (w - width * scale) / 2 - left * scale
            dy = y + (h - height * scale) / 2 - top * scale
            positioned = [position_copy(shape, element, frame, scale, dx, dy, target.shapes, target_theme)
                          for shape, element, frame in copies]
            targets = [target.shapes._shape_factory(element) for element in positioned]
            surfaces = list(shape_surfaces(existing + targets, target_theme, background))[len(existing):]
            for (shape, _, _), copied, surface in zip(copies, targets, surfaces, strict=True):
                normalize_shape_text(shape, copied, theme, target_theme, surface)
            bottom = max((rect[3] for copied in targets
                          if (rect := text_bounds(copied, target_theme, target_deck.slide_height)) is not None),
                         default=y)
            if bottom <= y + h + 1:  # Tolerância de 1 EMU pelo arredondamento do XML.
                break
            scale *= max(0.5, min(0.98, (h / 2) / (bottom - y - h / 2 + 2)))
        else:
            raise ValueError(f"o texto do slide {script.get('slide')} não cabe na área de conteúdo")

        style_ids = {node.text for element in positioned for node in element.iter(qn("a:tableStyleId")) if node.text}
        if style_ids:
            self.copy_table_styles(style_ids, deck.part, target.part.package.presentation_part)
        tree = target.shapes._spTree
        next_id = tree.max_shape_id + 1
        ids = {}
        for element in positioned:
            for node in element.iter(qn("p:cNvPr")):
                ids[node.get("id")] = str(next_id)
                node.set("id", str(next_id))
                next_id += 1

        for element in positioned:
            for endpoint in list(element.iter(qn("a:stCxn"), qn("a:endCxn"))):
                new_id = ids.get(endpoint.get("id"))
                if new_id is None:
                    endpoint.getparent().remove(endpoint)
                else:
                    endpoint.set("id", new_id)
            self.relink(element, source.part, target.part)
            tree.insert_element_before(element, "p:extLst")
        return list(target.shapes)[-len(copies):]

    def copy_table_styles(self, style_ids, source, target):
        # Os GUIDs das tabelas apontam para uma parte da apresentação, fora dos .rels do slide.
        try:
            source_part = source.part_related_by(RT.TABLE_STYLES)
        except KeyError:
            return
        target_part = target.part_related_by(RT.TABLE_STYLES)
        target_styles = parse_xml(target_part.blob)
        original_count = len(target_styles)
        style_tag = qn("a:tblStyle")
        missing = style_ids - {node.get("styleId") for node in target_styles.findall(style_tag)}
        if not missing:
            return
        for style in parse_xml(source_part.blob).findall(style_tag):
            style_id = style.get("styleId")
            if style_id in missing:
                self.relink(style, source_part, target_part)
                target_styles.append(style)
                missing.remove(style_id)
        if len(target_styles) > original_count:
            target_part.blob = serialize_part_xml(target_styles)

    def relink(self, element, source, target):
        for node, key, rid in list(relationship_attributes(element)):
            rel = source.rels.get(rid)
            # Links para páginas do deck original não têm destino confiável num recorte.
            if rel is None or rel.reltype == RT.SLIDE:
                if node.tag in {qn("a:hlinkClick"), qn("a:hlinkMouseOver")}:
                    node.getparent().remove(node)
                else:
                    del node.attrib[key]
                continue
            part = rel.target_ref if rel.is_external else self.import_part(rel.target_part, target.package)
            node.set(key, target.relate_to(part, rel.reltype, rel.is_external))


def position_copy(shape, element, frame, scale, dx, dy, target_shapes, theme):
    element = deepcopy(element)
    x, y, width, height = frame or shape_frame(shape)
    element.x = round(x * scale + dx)
    element.y = round(y * scale + dy)
    element.cx = round(width * scale)
    element.cy = round(height * scale)
    if shape.is_placeholder:
        placeholder = element.ph
        placeholder.getparent().remove(placeholder)
        if element.tag == qn("p:sp") and element.spPr.prstGeom is None and element.spPr.custGeom is None:
            element.nvSpPr.cNvSpPr.set("txBox", "1")
    if shape.shape_type != GROUP:
        if shape.has_text_frame or shape.has_table:
            set_inherited_text_sizes(target_shapes._shape_factory(element), theme)
        scale_details(element, scale)
    return element


def set_inherited_text_sizes(shape, theme):
    frames = ([cell.text_frame for cell in shape.table.iter_cells() if not cell.is_spanned]
              if shape.has_table else [shape.text_frame])
    for frame in frames:
        for paragraph in frame.paragraphs:
            if not any(run.text and run.font.size is None for run in paragraph.runs):
                continue
            default = paragraph._p.get_or_add_pPr().get_or_add_defRPr()
            if "sz" not in default.attrib:
                sizes = (style.get("sz") for style in theme.defaults(shape, frame, paragraph.level)
                         if style is not None and "sz" in style.attrib)
                default.set("sz", next(sizes, "1800"))


def normalize_shape_text(source, target, source_theme, target_theme, surface):
    if target.shape_type == GROUP:
        originals = {shape.shape_id: shape for shape in source.shapes}
        for child, background in zip(target.shapes, shape_surfaces(target.shapes, target_theme, surface), strict=True):
            normalize_shape_text(originals[child.shape_id], child, source_theme, target_theme, background)
    elif target.has_table:
        for original, cell in zip(source.table.iter_cells(), target.table.iter_cells(), strict=True):
            if not cell.is_spanned:
                background = cell_surface(cell, target_theme, surface)
                normalize_text(source, original.text_frame, cell.text_frame, source_theme, background)
    elif target.has_text_frame:
        normalize_text(source, source.text_frame, target.text_frame, source_theme, surface)


def normalize_text(shape, source, target, theme, background):
    from clinic_deck import CINZA_CLARO, FONTE, FONTE_FORTE, TEXTO
    from conferir import text_color_node, text_defaults

    title = shape.is_placeholder and shape.placeholder_format.type in {
        PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.VERTICAL_TITLE,
    }
    style_color = str(CINZA_CLARO if background is not None and is_dark(background) else TEXTO)
    for original, paragraph in zip(source.paragraphs, target.paragraphs, strict=True):
        defaults = text_defaults(original, shape, source, theme)
        original_runs = (node for node in original._p if node.findtext(qn("a:t"), ""))
        copied_runs = (node for node in paragraph._p if node.findtext(qn("a:t"), ""))
        for source_node, node in zip(original_runs, copied_runs, strict=True):
            styles = [style for style in (source_node.find(qn("a:rPr")), *defaults) if style is not None]
            bold, italic = (next((style.get(key) in {"1", "true"} for style in styles if key in style.attrib), False)
                            for key in ("b", "i"))
            color_node = text_color_node(styles, shape)
            base = theme.color(color_node) if color_node is not None else "000000"
            color = solid_color(color_node, theme) if color_node is not None else base
            neutral = color != "FFFFFF" and color[0:2] == color[2:4] == color[4:6]
            if rgb_channels(color) is None or base == "1F497D" or neutral:
                color = style_color
            font = Font(node.get_or_add_rPr())
            font.name = FONTE_FORTE if title and bold else FONTE
            font.bold, font.italic = bold, italic
            for script in ("ea", "cs"):
                existing = font._rPr.find(qn(f"a:{script}"))
                if existing is not None:
                    existing.set("typeface", font.name)
            fill = font._rPr.eg_fillProperties
            if fill is not None:
                font._rPr.remove(fill)
            font.color.rgb = RGBColor.from_string(readable_color(color, background))


def scale_details(element, scale):
    # Grupos mantêm o sistema de coordenadas interno. Nos demais objetos,
    # ajusta as métricas fixas que o PowerPoint não redimensiona junto com a caixa.
    for node in element.iter(qn("a:rPr"), qn("a:defRPr"), qn("a:endParaRPr")):
        if "sz" in node.attrib:
            node.set("sz", str(max(100, min(400000, round(int(node.get("sz")) * scale)))))
    for tag, attr in (("a:gridCol", "w"), ("a:tr", "h"), ("a:ln", "w"), ("a:lnL", "w"),
                      ("a:lnR", "w"), ("a:lnT", "w"), ("a:lnB", "w"), ("a:lnTlToBr", "w"),
                      ("a:lnBlToTr", "w"), ("a:spcPts", "val"), ("a:buSzPts", "val")):
        for node in element.iter(qn(tag)):
            if attr in node.attrib:
                node.set(attr, str(round(int(node.get(attr)) * scale)))
    for body in element.iter(qn("p:txBody")):
        for attr in ("lIns", "rIns", "tIns", "bIns"):
            setattr(body.bodyPr, attr, round(getattr(body.bodyPr, attr) * scale))
    for cell in element.iter(qn("a:tc")):
        for attr in ("marL", "marR", "marT", "marB"):
            setattr(cell, attr, round(getattr(cell, attr) * scale))
