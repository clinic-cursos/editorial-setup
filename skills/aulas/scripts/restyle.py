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

from PIL import Image, ImageStat
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


def image_parts(shape):
    for _, _, rid in relationship_attributes(shape._element):
        rel = shape.part.rels.get(rid)
        if rel is not None and rel.reltype == RT.IMAGE and not rel.is_external:
            yield rel.target_part


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


def solid_rectangle_color(shape, theme):
    properties = shape._element.spPr
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
    if fill is not None and fill.tag == qn("a:solidFill") and len(fill):
        return solid_color(fill[0], theme, placeholder)
    return None


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
            color = solid_rectangle_color(shape, Theme(slide, presentation))
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


def is_dark(color):
    channels = rgb_channels(color)
    if channels is None:
        return False
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)) < 0.179


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
    images = [(shape.shape_id, bounds(shape)) for shape in shapes if next(image_parts(shape), None) is not None]
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
        for part in image_parts(shape):
            yield part, width * scale_x, height * scale_y


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
        image_frequency.update({part.sha1 for shape in shapes for part in image_parts(shape)})
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
            for part, w, h in sized_images(shape):
                decorative = (shape.shape_id not in content_ids or w < width * 0.06 or h < height * 0.06
                              or part.sha1 in repeated)
                candidates.append((w * h, part, decorative))
        # Mantém o nome de cada arquivo na ordem original e ordena apenas a lista do roteiro.
        ranked = sorted(enumerate(candidates, 1), key=lambda item: item[1][0], reverse=True)
        for index, (_, part, decorative) in ranked:
            path = f"img/slide-{number}-{index}.{part.partname.ext}"
            (folder / path).write_bytes(part.blob)
            images.append({"caminho": path, "decorativa": decorative})
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
        left = min(rect[0] for rect in geometry)
        top = min(rect[1] for rect in geometry)
        width = max(rect[2] for rect in geometry) - left
        height = max(rect[3] for rect in geometry) - top
        scale = min(w / width if width else math.inf, h / height if height else math.inf)
        if not math.isfinite(scale):
            scale = 1
        dx = x + (w - width * scale) / 2 - left * scale
        dy = y + (h - height * scale) / 2 - top * scale

        style_ids = {node.text for _, element, _ in copies for node in element.iter(qn("a:tableStyleId")) if node.text}
        if style_ids:
            self.copy_table_styles(style_ids, deck.part, target.part.package.presentation_part)
        tree = target.shapes._spTree
        next_id = tree.max_shape_id + 1
        ids = {}
        for _, element, _ in copies:
            for node in element.iter(qn("p:cNvPr")):
                ids[node.get("id")] = str(next_id)
                node.set("id", str(next_id))
                next_id += 1

        for shape, element, frame in copies:
            shape_x, shape_y, shape_width, shape_height = frame or shape_frame(shape)
            element.x = round(shape_x * scale + dx)
            element.y = round(shape_y * scale + dy)
            element.cx = round(shape_width * scale)
            element.cy = round(shape_height * scale)
            if shape.is_placeholder:
                placeholder = element.ph
                placeholder.getparent().remove(placeholder)
                if element.tag == qn("p:sp") and not (element.spPr.prstGeom is not None
                                                      or element.spPr.custGeom is not None):
                    element.nvSpPr.cNvSpPr.set("txBox", "1")
            if shape.shape_type != GROUP:
                scale_details(element, scale)
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
