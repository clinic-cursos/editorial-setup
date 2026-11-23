"""Extrai um roteiro e reaproveita objetos editáveis de slides PowerPoint."""

from copy import deepcopy
import json
import math
from pathlib import Path
import re
from zipfile import BadZipFile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.exc import PackageNotFoundError
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.packuri import PackURI
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn


REL_PREFIX = qn("r:id").split("}")[0] + "}"
GROUP = MSO_SHAPE_TYPE.GROUP
NUMBER = re.compile(r"\d+(?:\s*/\s*\d+)?")


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


def is_decoration(shape, first, width, height):
    label = shape.name.casefold().lstrip("!").replace("_", " ")
    if re.match(r"(?:logo(?:tipo)?|fundo|background|slide number|page number|número (?:de|do) (?:slide|página))\b", label):
        return True
    if shape.is_placeholder and shape.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
        return True
    x, y, w, h = shape.left or 0, shape.top or 0, shape.width or 0, shape.height or 0
    value = shape.text if shape.has_text_frame else ""
    corner = x <= width * 0.1 or x + w >= width * 0.9
    picture = shape._element.tag == qn("p:pic")
    if picture and corner and w <= width * 0.12 and h <= height * 0.16:
        return y <= height * 0.05 or y + h >= height * 0.95
    if corner and y >= height * 0.9 and h <= height * 0.1 and NUMBER.fullmatch(value.strip()):
        return True
    rectangle = shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and shape.auto_shape_type == MSO_SHAPE.RECTANGLE
    return (shape is first and (picture or rectangle) and not value
            and x <= width * 0.01 and y <= height * 0.01
            and x + w >= width * 0.99 and y + h >= height * 0.99)


def slide_content(presentation, slide):
    shapes = list(slide.shapes)
    width, height = presentation.slide_width, presentation.slide_height
    content = [shape for shape in shapes if not is_decoration(shape, shapes[0], width, height)]
    title = slide.shapes.title
    if title is None or not title.text.strip():
        # Sem placeholder, o primeiro texto curto na faixa superior é o candidato a título.
        title = next((shape for shape in reading_order(content)
                      if shape.has_text_frame and 0 < len(shape.text.strip()) <= 150
                      and (shape.top or 0) <= height * 0.22
                      and "\n" not in shape.text and "\v" not in shape.text), None)
    return shapes, title, [shape for shape in content if title is None or shape.shape_id != title.shape_id]


def is_drawing(shape):
    if shape.shape_type in (MSO_SHAPE_TYPE.LINE, MSO_SHAPE_TYPE.FREEFORM, GROUP):
        return True
    return (shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE
            and (not shape.text.strip() or "ARROW" in shape.auto_shape_type.name))


def bounds(shape):
    x, y, w, h = (getattr(shape, attr) or 0 for attr in ("left", "top", "width", "height"))
    angle = math.radians(shape.rotation)
    dx = (abs(w * math.cos(angle)) + abs(h * math.sin(angle))) / 2
    dy = (abs(w * math.sin(angle)) + abs(h * math.cos(angle))) / 2
    return x + w / 2 - dx, y + h / 2 - dy, x + w / 2 + dx, y + h / 2 + dy


def overlaps(first, second):
    x1, y1, x2, y2 = first
    a1, b1, a2, b2 = second
    # A igualdade conta a linha horizontal ou vertical sobre a imagem.
    return x1 <= a2 and a1 <= x2 and y1 <= b2 and b1 <= y2


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


def extract(deck, folder, selection):
    presentation = open_deck(deck)
    numbers = slide_numbers(selection, len(presentation.slides))
    (folder / "img").mkdir(parents=True, exist_ok=True)
    slides = []
    source = str(deck.resolve())
    for number in numbers:
        slide = presentation.slides[number - 1]
        shapes, title, content = slide_content(presentation, slide)
        ordered = reading_order(shapes)
        images = []
        content_images = []
        content_ids = {shape.shape_id for shape in content}
        for shape in ordered:
            exported = []
            for part in image_parts(shape):
                path = f"img/slide-{number}-{len(images) + 1}.{part.partname.ext}"
                (folder / path).write_bytes(part.blob)
                images.append(path)
                exported.append(path)
            if exported and shape.shape_id in content_ids:
                content_images.extend(exported)
        drawings, annotations = drawing_counts(content)
        body = [value for shape in ordered for value in texts(shape)]
        entry = {
            "origem": number, "deck": source, "slide": number, "titulo": title.text if title is not None else "",
            "textos": body, "imagens": images, "formas_desenhadas": drawings,
        }
        # Preserva composições complexas. Foto única com até três sobreposições usa texto_imagem.
        # Frases recebem o texto integral na ordem de leitura. O roteiro é uma sugestão para direção.
        complex_content = (annotations >= 4 or len(content_images) > 1
                           or any(shape.has_table or shape.has_chart for shape in content))
        if complex_content or (not content_images and (drawings or not body)):
            entry["tipo"] = "preservado"
        elif content_images and Path(content_images[0]).suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}:
            entry.update(tipo="texto_imagem", imagem=content_images[0],
                         topicos=[value for shape in ordered if title is None or shape.shape_id != title.shape_id
                                  for value in texts(shape)])
        elif content_images:
            entry["tipo"] = "preservado"
        else:
            entry.update(tipo="frase", frase="\n".join(body))
        slides.append(entry)
    path = folder / "roteiro-rascunho.json"
    path.write_text(json.dumps({"estilo": "ousado", "avulso": True, "slides": slides},
                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


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
        deck, source = self.source(script.get("deck"), script.get("slide"))
        _, _, shapes = slide_content(deck, source)
        if not shapes:
            return []
        geometry = [bounds(shape) for shape in shapes]
        left = min(rect[0] for rect in geometry)
        top = min(rect[1] for rect in geometry)
        width = max(rect[2] for rect in geometry) - left
        height = max(rect[3] for rect in geometry) - top
        x, y, w, h = box
        scale = min(w / width if width else math.inf, h / height if height else math.inf)
        if not math.isfinite(scale):
            scale = 1
        dx = x + (w - width * scale) / 2 - left * scale
        dy = y + (h - height * scale) / 2 - top * scale

        elements = [deepcopy(shape._element) for shape in shapes]
        tree = target.shapes._spTree
        next_id = tree.max_shape_id + 1
        ids = {}
        for element in elements:
            for node in element.iter(qn("p:cNvPr")):
                ids[node.get("id")] = str(next_id)
                node.set("id", str(next_id))
                next_id += 1

        for shape, element in zip(shapes, elements, strict=True):
            element.x = round((shape.left or 0) * scale + dx)
            element.y = round((shape.top or 0) * scale + dy)
            element.cx = round((shape.width or 0) * scale)
            element.cy = round((shape.height or 0) * scale)
            if shape.is_placeholder:
                placeholder = element.ph
                placeholder.getparent().remove(placeholder)
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
        return list(target.shapes)[-len(elements):]

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
    for tag, attr in (("a:gridCol", "w"), ("a:tr", "h"), ("a:ln", "w"),
                      ("a:spcPts", "val"), ("a:buSzPts", "val")):
        for node in element.iter(qn(tag)):
            if attr in node.attrib:
                node.set(attr, str(round(int(node.get(attr)) * scale)))
