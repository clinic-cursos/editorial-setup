#!/usr/bin/env python3
"""Layouts do estilo editorial ousado, com Morph e animações de entrada."""

from hashlib import sha1
from math import sqrt
from pathlib import Path
import re

from lxml import etree
from PIL import Image
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches

from clinic_deck import (
    A, ALERTA, BRANCO, CINZA, CINZA_CLARO, FONTE, FONTE_FORTE, H, LAYOUTS, M,
    PRETO, ROSE, ROSE_CLARO, TEXTO, VINHO, VINHO_ESC, W, _alpha, _parse_bold,
    arc, badge, image, keep_numeric_expressions, line, plain_text, rect, text,
)
from restyle import PreservedFrame

NOITE = RGBColor(0x1C, 0x12, 0x12)      # fundo escuro quente (vinho quase preto)
NOITE2 = RGBColor(0x2A, 0x1A, 0x19)
CREME = RGBColor(0xFA, 0xF6, 0xF4)
QUOTE_FONT = "Georgia"
QUOTE_MARK = "“"
KICKER_SIZE = 8.5
MIN_LIST_BODY_SIZE = 8
MAX_TEXT_ONLY_BODY_SIZE = 18
TEXT_ONLY_ITEM_TITLE_SCALE = 1.2
REFERENCE_TOP = H - 0.4

P14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
P159 = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
MC = "http://schemas.openxmlformats.org/markup-compatibility/2006"
PNS = "http://schemas.openxmlformats.org/presentationml/2006/main"


# ---------------------------------------------------------------- movimento
def name(sh, n):
    sh.name = n
    return sh


def morph(slide, dur=1400):
    xml = (f'<mc:AlternateContent xmlns:mc="{MC}" xmlns:p="{PNS}">'
           f'<mc:Choice xmlns:p159="{P159}" xmlns:p14="{P14}" Requires="p159">'
           f'<p:transition spd="slow" p14:dur="{dur}"><p159:morph option="byObject"/></p:transition>'
           f'</mc:Choice><mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback>'
           f'</mc:AlternateContent>')
    el = etree.fromstring(xml)
    sld = slide._element
    clr = sld.find(qn("p:clrMapOvr"))
    (clr if clr is not None else sld.find(qn("p:cSld"))).addnext(el)


class Anim:
    """Coleta formas para entrar em sequência (fade ou subida), automático."""
    def __init__(self, slide):
        self.s = slide; self.items = []; self.t = 300

    def add(self, sh, gap=180, eff="fade", dur=500):
        self.items.append((sh.shape_id, self.t, eff, dur)); self.t += gap
        return sh

    def build(self):
        if not self.items:
            return
        ids = iter(range(3, 10000))
        pars = []
        for spid, delay, eff, dur in self.items:
            a, b, c, d = next(ids), next(ids), next(ids), next(ids)
            tgt = f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
            beh = (f'<p:set><p:cBhvr><p:cTn id="{c}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>{tgt}'
                   f'<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
                   f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{d}" dur="{dur}"/>{tgt}</p:cBhvr></p:animEffect>')
            preset = 10
            if eff == "up":   # fade + subida leve (preset 'ascend')
                preset = 47
                e1, e2 = next(ids), next(ids)
                beh += (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{e1}" dur="{dur}" fill="hold"/>{tgt}'
                        f'<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst>'
                        f'<p:tav tm="0"><p:val><p:strVal val="#ppt_y+0.05"/></p:val></p:tav>'
                        f'<p:tav tm="100000"><p:val><p:strVal val="#ppt_y"/></p:val></p:tav></p:tavLst></p:anim>')
            elif eff == "left":
                preset = 2
                e1 = next(ids)
                beh += (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{e1}" dur="{dur}" fill="hold"/>{tgt}'
                        f'<p:attrNameLst><p:attrName>ppt_x</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst>'
                        f'<p:tav tm="0"><p:val><p:strVal val="#ppt_x-0.06"/></p:val></p:tav>'
                        f'<p:tav tm="100000"><p:val><p:strVal val="#ppt_x"/></p:val></p:tav></p:tavLst></p:anim>')
            pars.append(f'<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>'
                        f'<p:par><p:cTn id="{b}" presetID="{preset}" presetClass="entr" presetSubtype="0" fill="hold" nodeType="withEffect">'
                        f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{beh}</p:childTnLst></p:cTn></p:par>'
                        f'</p:childTnLst></p:cTn></p:par>')
        xml = (f'<p:timing xmlns:p="{PNS}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
               f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
               f'<p:par><p:cTn id="9999" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
               f'<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>{"".join(pars)}</p:childTnLst></p:cTn></p:par>'
               f'</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
               f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
               f'</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')
        el = etree.fromstring(xml)
        sld = self.s._element
        tr = [c for c in sld if c.tag.endswith("AlternateContent") or c.tag == qn("p:transition")]
        (tr[-1] if tr else sld.find(qn("p:clrMapOvr"))).addnext(el)


# ---------------------------------------------------------------- elementos recorrentes (morph)
def bg(s, color):
    return name(rect(s, 0, 0, W, H, fill=color), "!!fundo")


def big_arc(s, x, y, d, color=VINHO, thick=0.5, a0=180, a1=270):
    return name(arc(s, x, y, d, color=color, thick=thick, start=a0, end=a1), "!!arco")


def small_arc(s, x, y, d, color=ROSE, thick=0.2, a0=180, a1=270):
    return name(arc(s, x, y, d, color=color, thick=thick, start=a0, end=a1), "!!arco2")


def logo(s, white=True, x=None, y=0.32, h=0.42):
    f = "logo_branco.png" if white else "logo_cor.png"
    x = W - M - 0.68 if x is None else x
    return name(s.shapes.add_picture(A(f), Inches(x), Inches(y), height=Inches(h)), "!!logo")


def kicker(s, t, x, y, color=ROSE, w=5):
    return text(s, x, y, w, 0.25, t, size=KICKER_SIZE, color=color, bold=True, caps=True)


def title(s, t, x, y, w, h, color=BRANCO, size=34, hl=None, hlc=ROSE):
    segs = [(t, {})]
    if hl and hl in t:
        a, b = t.split(hl, 1); segs = [(a, {}), (hl, {"color": hlc}), (b, {})]
    return text(s, x, y, w, h, [segs], size=size, color=color, font=FONTE_FORTE, bold=True, spacing=0.9)


def bar(s, x, y, w=0.6, color=ROSE, h=0.05):
    return name(rect(s, x, y, w, h, fill=color), "!!barra")


def has_image_panel(d):
    return bool(d.get("imagem") or d.get("prompt_imagem"))


def photo(s, d, x, y, w, h, *, dark=False, prompt_height=None, contain=False, avoid_logo=None):
    if not has_image_panel(d):
        raise ValueError(f"{d['tipo']} exige imagem ou prompt_imagem no slide {d.get('titulo', '')!r}")
    path = d.get("imagem")
    if avoid_logo is not None:
        margin = Inches(0.1)
        safe_right = avoid_logo.left - margin
        safe_top = avoid_logo.top + avoid_logo.height + margin
        safe_width = safe_right / Inches(1) - x
    if contain and path and Path(path).exists():
        with Image.open(path) as source:
            width, height = source.size
        scale = min(w / width, h / height)
        if (avoid_logo is not None
                and Inches(y + (h - height * scale) / 2) < safe_top
                and Inches(x + (w + width * scale) / 2) > safe_right):
            w = safe_width
            scale = min(w / width, h / height)
        width *= scale
        height *= scale
        picture = s.shapes.add_picture(
            path, Inches(x + (w - width) / 2), Inches(y + (h - height) / 2),
            Inches(width), Inches(height),
        )
        return name(picture, "!!foto")

    if avoid_logo is not None:
        w = safe_width
    label = {
        "prompt": d.get("prompt_imagem") or d.get("legenda") or d.get("titulo") or "Imagem do slide",
        "titulo": d.get("titulo", ""),
        "alerta": d.get("alerta_imagem"),
        "estilo": d.get("estilo_imagem", True),
    }
    before = len(s.shapes)
    height = prompt_height if prompt_height and not (path and Path(path).exists()) else h
    shape = image(s, path, x, y, w, height, label, dark)
    if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
        for i, box in enumerate(list(s.shapes)[before + 1:], 1):
            box.name = f"Texto do prompt {i}"
    shape.height = Inches(h)
    return name(shape, "!!foto")


def crop_pillar_photo(picture, path):
    with Image.open(path) as source:
        width, height = source.size
        bounds = source.convert("L").point(lambda pixel: 255 if pixel < 245 else 0).getbbox()
    # Trim paired near-white margins baked into the source before centering the cover.
    if not bounds or bounds[1] == 0 or bounds[3] == height:
        return
    left, top, right, bottom = bounds
    panel_ratio = picture.width / picture.height
    crop_x = max(0, (right - left - (bottom - top) * panel_ratio) / 2)
    crop_y = max(0, (bottom - top - (right - left) / panel_ratio) / 2)
    picture.crop_left = (left + crop_x) / width
    picture.crop_right = (width - right + crop_x) / width
    picture.crop_top = (top + crop_y) / height
    picture.crop_bottom = (height - bottom + crop_y) / height


# ---------------------------------------------------------------- slides
def s_cover(prs, s, d):
    an = Anim(s)
    s.shapes.add_picture(A("fundo_foto.jpg"), 0, 0, Inches(W), Inches(H))
    r = rect(s, 0, 0, W, H, fill=NOITE); _alpha(r, 0.45); name(r, "!!fundo")
    big_arc(s, -3.6, 2.9, 7.0, VINHO, 0.62, 270, 360)
    logo(s, True, M, 0.4, 0.55)
    an.add(kicker(s, d.get("curso", ""), M, 1.75))
    an.add(title(s, d.get("titulo", ""), M, 2.0, 7, 0.9, size=50), eff="up", gap=150)
    if d.get("titulo_secundario"):
        an.add(title(s, d["titulo_secundario"], M, 2.75, 8, 0.9, size=50, color=ROSE), eff="up", gap=250)
    bar(s, M, 3.85, 0.7)
    an.add(text(s, M, 3.98, 4, 0.35, d.get("subtitulo", ""), size=13, color=BRANCO))
    morph(s); an.build()


def s_agenda(prs, s, d):
    an = Anim(s)
    bg(s, CREME)
    name(rect(s, 0, 0, 3.4, H, fill=NOITE), "!!painel")
    big_arc(s, -2.2, H - 1.4, 4.2, VINHO, 0.42, 270, 360)
    logo(s, True, M, 0.4, 0.42)
    text(s, M, 1.25, 2.8, 0.25, d.get("titulo", "Conteúdo programático"), size=8.5, color=ROSE, bold=True, caps=True)
    items = d.get("itens", [])
    an.add(text(s, M, 1.5, 2.8, 1.2, str(len(items)), size=88, color=BRANCO, font=FONTE_FORTE, bold=True), eff="up")
    an.add(text(s, M, 2.85, 2.6, 0.5, d.get("resumo", ""), size=12, color=BRANCO))
    text(s, M, 3.45, 2.7, 0.8, [_parse_bold(row, ROSE) for row in d.get("info", "").splitlines()],
         size=9.5, color=CINZA_CLARO)
    rows = max(6, (len(items) + 1) // 2)
    stride = max(0.5, 4.2 / rows)
    for col, start in enumerate(range(0, len(items), rows)):
        x = 3.85 + col * 3.0
        column = items[start:start + rows]
        tops = [0.75 + max(row * 0.5, row * 4.2 / rows) for row in range(len(column))]
        size, boxes = fit_list([[(plain_text(item), None)] for item in column], width=2.2,
                               tops=tops, bottom=4.95, base_height=min(0.5, stride - 0.06),
                               body_size=10, inset=0.06)
        for i, (item, (y, height)) in enumerate(zip(column, boxes), start + 1):
            a = text(s, x, y, 0.6, 0.5, f"{i:02d}", size=20, color=ROSE, font=FONTE_FORTE, bold=True)
            b = text(s, x + 0.62, y + 0.06, 2.2, height, item, size=size, color=PRETO)
            an.add(a, gap=0); an.add(b, gap=90)
    morph(s); an.build()


def s_section(prs, s, d):
    an = Anim(s)
    bg(s, VINHO)
    big_arc(s, W - 6.4, -2.6, 9.0, VINHO_ESC, 0.9, 90, 180)
    small_arc(s, W - 2.2, H - 1.8, 2.6, ROSE, 0.22, 180, 270)
    logo(s, True)
    t = text(s, M - 0.08, 0.7, 6, 2.6, str(d.get("numero", "")).zfill(2), size=190, color=ROSE, font=FONTE_FORTE, bold=True, spacing=0.8)
    an.add(t, eff="up", dur=700, gap=250)
    bar(s, M + 0.05, 3.55, 0.9, BRANCO)
    an.add(title(s, d.get("titulo", ""), M, 3.7, 8, 0.8, size=40), eff="left", gap=200)
    an.add(text(s, M + 0.03, 4.45, 6, 0.4, d.get("descricao", ""), size=12, color=ROSE_CLARO))
    if d.get("selo"):
        badge(s, d["selo"], W - M - 2.9, H - 0.6, w=2.9, color=VINHO_ESC)
    morph(s); an.build()


def s_quote(prs, s, d):
    an = Anim(s)
    bg(s, CREME)
    big_arc(s, -5.0, -5.0, 7.0, VINHO, 0.5, 0, 90)
    logo(s, False)
    text(s, M + 0.6, 0.55, 1.4, 1.4, QUOTE_MARK, size=120, color=VINHO, font=QUOTE_FONT)
    an.add(text(s, M + 1.15, 1.5, 7.4, 2.0, d.get("frase", ""), size=21, color=PRETO, font=FONTE, spacing=1.15),
           eff="up", dur=800, gap=500)
    x = M + 0.9
    for c in d.get("selos", []):
        w = 0.3 + 0.068 * len(c)
        r = rect(s, x, 3.85, w, 0.42, fill=None, line=VINHO, shape=MSO_SHAPE.ROUNDED_RECTANGLE, lw=1.25)
        r.adjustments[0] = 0.5
        t = text(s, x, 3.85, w, 0.42, c, size=8, color=VINHO, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        an.add(r, gap=0); an.add(t, gap=150); x += w + 0.15
    if d.get("autor"):
        text(s, M + 1.15, 4.55, 7.4, 0.35, d["autor"], size=9, color=VINHO)
    morph(s); an.build()


def reference_footer(s, value, panel):
    text(s, 4.75 if panel else M, REFERENCE_TOP, 4.8 if panel else W - 2 * M,
         0.25, value, size=6.5, color=CINZA)


def s_pillars(prs, s, d):
    an = Anim(s)
    bg(s, NOITE)
    panel = has_image_panel(d)
    x = 4.75 if panel else M
    full_width = W - 2 * M
    badge_text = d.get("selo")
    badge_width = 2.9
    badge_left = W - M - badge_width
    info_value = d.get("info", "")
    info = [_parse_bold(row, ROSE) for row in info_value.splitlines()]
    if panel:
        picture = photo(s, d, 0, 0, 4.3, H, dark=True, prompt_height=H - 1)
        if picture.shape_type == MSO_SHAPE_TYPE.PICTURE:
            crop_pillar_photo(picture, d["imagem"])
        info_height = max(0.7, list_text_height([(plain_text(info_value), 9)], 3.6, 9))
        band_height = info_height + 0.3
        r = rect(s, 0, H - band_height, 4.3, band_height, fill=NOITE)
        _alpha(r, 0.6)
        text(s, M, H - (info_height + 0.15), 3.6, info_height, info, size=9, color=BRANCO)
    elif info:
        info_width = badge_left - M - 0.15 if badge_text else full_width
        text(s, M, H - 0.85, info_width, 0.45, info, size=9, color=BRANCO)
    small_arc(s, 3.55, -0.9, 1.8, VINHO, 0.2, 90, 180)
    logo(s, True)
    kicker(s, d.get("kicker", ""), x, 0.55)
    an.add(title(s, d.get("titulo", ""), x, 0.8, 4.6 if panel else full_width,
                 1.0, size=24, hl=d.get("destaque_titulo")), eff="up")
    body_width = 3.7 if panel else full_width - 1.0
    rows = [(pillar.get("titulo", ""), pillar.get("texto", "")) for pillar in d.get("pilares", [])]
    if panel:
        size, heading_size = 9.5, 13
        bottom = H - (0.7 if badge_text else 0.4)
        heading_heights = [max(0.3, list_text_height([(plain_text(h).upper(), heading_size)], body_width, size))
                           for h, _ in rows]
        while True:
            body_heights = [max(0.5, list_text_height([(plain_text(t), size)], body_width, size))
                            for _, t in rows]
            heights = [h + b + 0.05 for h, b in zip(heading_heights, body_heights)]
            if 2.0 + sum(heights) + 0.1 * max(0, len(rows) - 1) <= bottom or size == MIN_LIST_BODY_SIZE:
                break
            size = max(MIN_LIST_BODY_SIZE, size - 1)
        boxes = []
        top = 2.0
        for height in heights:
            if top + height > bottom:
                # Keep the item editable and let conferir report it without covering the footer.
                top = max(top, H)
            boxes.append((top, height))
            top += height + 0.1
    else:
        footer = 0.85 if info else 0.7 if badge_text else 0.4
        size, boxes = fit_text_only_list([(plain_text(h).upper(), plain_text(t)) for h, t in rows],
                                         width=body_width, top=2.0, bottom=H - footer, split_title=True)
        heading_size = size * TEXT_ONLY_ITEM_TITLE_SCALE
    for i, ((h, t), (y, height)) in enumerate(zip(rows, boxes)):
        if panel:
            number_top, number_height, number_size = y - 0.1, 0.9, 36
            heading_height, body_height = heading_heights[i], body_heights[i]
            body_top = y + heading_height + 0.02
        else:
            number_top, number_height, number_size = y, height, size
            heading_height = list_text_height([(plain_text(h).upper(), heading_size)], body_width, size) if h else 0
            body_top, body_height = y + heading_height, height - heading_height
        n = text(s, x, number_top, 1.0, number_height, f"{i+1:02d}", size=number_size,
                 color=VINHO, font=FONTE_FORTE, bold=True)
        if h or panel:
            a = text(s, x + 1.0, y, body_width, heading_height, h, size=heading_size,
                     color=BRANCO, bold=True, caps=True)
        if t or panel:
            b = text(s, x + 1.0, body_top, body_width, body_height, t, size=size, color=CINZA_CLARO)
        line(s, x + 0.05, y + height, W - M, y + height, color=NOITE2, w=0.75)
        an.add(n, gap=0, eff="up")
        if h or panel:
            an.add(a, gap=60)
        if t or panel:
            an.add(b, gap=200)
    if badge_text:
        badge(s, badge_text, badge_left, H - 0.7, w=badge_width, color=VINHO_ESC)
    reference_footer(s, d.get("referencia", ""), panel)
    morph(s); an.build()


def measured_words(line):
    # Estimate Montserrat widths in em with room for wide glyphs, independent of
    # installed fonts.
    line = keep_numeric_expressions(line)
    return [(sum(0.35 if ch == "\u00a0" else 1 if ch in "MWmw" else 0.85 if ch.isupper() else 0.75
                 for ch in word),
             len(gap) * 0.35)
            for word, gap in re.findall(r"((?:\S|\u00a0)+)((?:(?!\u00a0)\s)*)", line)]


def wrapped_rows(words, available):
    rows = 1
    used = gap = 0
    for word, next_gap in words:
        if used and used + gap + word > available:
            rows += 1
            used = word
        else:
            used += gap + word
        gap = next_gap
    return rows


def text_image_font_size(paragraphs, width, height, model_size, min_size, spacing, *, max_rows=None):
    # Measure the box inside the 0.02-inch margins from text().
    width_pt = Inches(width - 0.04).pt
    height_pt = Inches(height - 0.04).pt
    lines = [measured_words(line) for paragraph in paragraphs for line in paragraph.splitlines()]
    widest_word = max((word for line in lines for word, _ in line), default=0)
    for size in range(model_size, min_size, -1):
        available = width_pt / size
        if widest_word > available:
            continue
        rows = sum(wrapped_rows(line, available) for line in lines)
        if max_rows is not None and rows > max_rows:
            continue
        # Include room for the first line's glyphs and the following baselines.
        if not rows or size * (1.38 + (rows - 1) * spacing * 1.2) <= height_pt:
            return size
    # Preserve overflowing text at the floor so the editorial check can flag it.
    return min_size


def list_text_height(paragraphs, width, body_size):
    available = Inches(width - 0.04).pt
    height = 0
    for value, fixed_size in paragraphs:
        if value:
            size = fixed_size or body_size
            rows = sum(wrapped_rows(measured_words(line), available / size)
                       for line in re.split(r"[\n\v]", value))
            height += size * (1.38 + (rows - 1) * 1.32)
    return 0.04 + height / 72


def fit_list(items, *, width, tops, bottom, base_height, body_size, inset=0):
    if not items:
        return body_size, []
    size = body_size
    while True:
        heights = [max(base_height, list_text_height(item, width, size)) for item in items]
        end = tops[-1] + inset + base_height + sum(height - base_height for height in heights)
        if end <= bottom + 1e-9 or size == MIN_LIST_BODY_SIZE:
            break
        size = max(MIN_LIST_BODY_SIZE, size - 1)

    boxes = []
    shift = 0
    for top, height in zip(tops, heights):
        y = top + shift
        # Keep the complete overflowing item editable beyond the slide, where
        # conferir reports it instead of letting it cover the footer.
        if y + inset + height > bottom + 1e-9 and y < H:
            shift += H - y
            y = H
        boxes.append((y, height))
        shift += height - base_height
    return size, boxes


def fit_text_only_list(rows, *, width, top, bottom, split_title=False):
    available = Inches(width - 0.04).pt
    for size in range(MAX_TEXT_ONLY_BODY_SIZE, MIN_LIST_BODY_SIZE - 1, -1):
        heading_size = size * TEXT_ONLY_ITEM_TITLE_SCALE
        gap = size / 180
        items = [[(heading, heading_size), (body, size)] for heading, body in rows]
        min_height = 0.04 + 1.38 * size / 72
        heights = [
            max(min_height, list_text_height(item, width, size) + (0.04 if split_title and all(row) else 0))
            for row, item in zip(rows, items)
        ]
        words_fit = all(word * font_size <= available for item in items
                        for value, font_size in item for word, _ in measured_words(value))
        if words_fit and top + sum(heights) + gap * max(0, len(rows) - 1) <= bottom + 1e-9:
            break

    boxes = []
    for height in heights:
        if top + height > bottom + 1e-9:
            # Keep the overflowing item editable and let conferir report it.
            top = max(top, H)
        boxes.append((top, height))
        top += height + gap
    return size, boxes


def text_image_body_width(paragraphs, max_width, height, size):
    widest_word = max(word for paragraph in paragraphs for word, _ in measured_words(paragraph))
    min_width = 0.04 + widest_word * size / 72
    items = [(paragraph, None) for paragraph in paragraphs]
    # Look for the narrowest column in tenths of an inch at the regular body size.
    for tenths in range(1, int(max_width * 10) + 1):
        width = tenths / 10
        if width >= min_width and list_text_height(items, width, size) <= height:
            return width
    return max_width


def s_text_image(prs, s, d):
    image_mode = d.get("imagem_modo", "sangrar")
    if image_mode not in ("sangrar", "conter"):
        raise ValueError("imagem_modo de texto_imagem deve ser sangrar ou conter")

    rows = [(None, d.get("texto", ""))]
    for topic in d.get("topicos", []):
        if isinstance(topic, dict):
            topic_title = topic.get("titulo")
            rows.append((str(topic_title).strip() if topic_title is not None else "", topic.get("texto", "")))
        else:
            rows.append((None, topic))
    rows.append((None, d.get("destaque", "")))

    an = Anim(s)
    bg(s, CREME)
    panel = has_image_panel(d)
    reference = d.get("referencia")
    contain = panel and image_mode == "conter"
    heading = d.get("titulo", "")
    label = d.get("kicker", "")
    useful_width = W - 2 * M
    title_width = 5.4 if panel and not contain else useful_width
    title_top, kicker_top = 1.6, 1.3
    compact = False
    body_top, body_width, body_height = 3.55, 5.0, 1.2
    arrow_x, arrow_top, arrow_bottom = 5.75, 1.0, 4.6
    if panel:
        body = [value for heading, content in rows
                for value in (f"**{heading}**" if heading else "", content) if value]
    if contain:
        body = [value for value in body if plain_text(value).strip()]
        compact = not body
        if compact:
            from conferir import MONTSERRAT_WIDTHS, glyph_width

            kicker_top, title_top = 0.42, 0.62
            model_logo = logo(s, False)
            title_width = model_logo.left.inches - M - 0.1
            title_units = sum(glyph_width(char, MONTSERRAT_WIDTHS["extrabold"])
                              for char in keep_numeric_expressions(heading))
            single_line_size = int(Inches(title_width - 0.04).pt * 1000 / max(1, title_units))
            title_size = max(18, min(36, single_line_size))
            title_rows = 1
        else:
            title_size = text_image_font_size([heading], title_width, 1.8, 36, 18, spacing=0.9, max_rows=2)
            title_rows = max(1, min(2, content_title_rows(heading, title_width, title_size)))
        title_height = 0.04 + title_size * (1.38 + (title_rows - 1) * 0.9 * 1.2) / 72
        body_top = title_top + title_height + 0.1
        body_height = H - M - body_top
        image_left = M
        gutter = 0.36
        if body:
            body_width = text_image_body_width([plain_text(value) for value in body],
                                               0.40 * useful_width, body_height, 11)
            image_left += body_width + gutter
        photo(s, d, image_left, body_top, W - M - image_left, body_height, contain=True)
        arrow_x, arrow_top, arrow_bottom = image_left - gutter / 2, body_top, H - M - 0.17
    elif panel:
        photo(s, d, W - 3, 0, 3, REFERENCE_TOP if reference else H)
        title_height = 1.8
        title_size = text_image_font_size([heading], title_width, title_height, 46, 18, spacing=0.9)
    else:
        title_size = text_image_font_size([heading], title_width, 1.8, 40, 18, spacing=0.9, max_rows=2)
        title_height = 0.04 + title_size * (1.38 + 0.9 * 1.2) / 72

    if not compact:
        logo(s, False, M, 0.4)
    kicker(s, label, M, kicker_top, VINHO)
    heading_box = title(s, heading, M, title_top, title_width, title_height,
                        color=PRETO, size=title_size, hl=d.get("destaque_titulo"), hlc=VINHO)
    if contain:
        heading_box.text_frame.auto_size = MSO_AUTO_SIZE.NONE
        heading_box.text_frame.word_wrap = not compact
    an.add(heading_box, eff="up", dur=700, gap=400)
    if panel and d.get("seta"):
        ln = line(s, arrow_x, arrow_top, arrow_x, arrow_bottom, color=VINHO, w=2.5)
        tri = rect(s, arrow_x - 0.13, arrow_bottom - 0.05, 0.26, 0.22,
                   fill=VINHO, shape=MSO_SHAPE.ISOSCELES_TRIANGLE)
        tri.rotation = 180
        an.add(ln, gap=0, dur=900)
        an.add(tri, gap=300)
    if panel:
        if body or not contain:
            body_size = text_image_font_size([plain_text(value) for value in body],
                                             body_width, body_height, 11, 8, spacing=1.1)
            an.add(text(s, M, body_top, body_width, body_height, body, size=body_size, color=TEXTO), eff="up")
    else:
        rows = [(heading, content) for heading, content in rows if heading or content]
        size, boxes = fit_text_only_list([(plain_text(heading or ""), plain_text(content or ""))
                                         for heading, content in rows],
                                         width=title_width, top=1.75 + title_height, bottom=H - M)
        for (heading, content), (y, height) in zip(rows, boxes):
            paragraphs = []
            if heading:
                paragraphs.append([(heading, {"bold": True, "color": VINHO, "size": size * TEXT_ONLY_ITEM_TITLE_SCALE})])
            if content:
                paragraphs.append(content)
            an.add(text(s, M, y, title_width, height, paragraphs, size=size, color=TEXTO), eff="up")
    if reference:
        reference_footer(s, reference, panel)
    morph(s); an.build()


def space_steps(prs, slide, steps, track, bottom):
    # Use the same Montserrat metrics as the editorial check for visible text.
    from conferir import Theme, check_text

    theme = Theme(slide, prs)
    edges = []
    for _, box in steps:
        frame = box.text_frame
        margins = frame.margin_left, frame.margin_right, frame.margin_top, frame.margin_bottom
        _, rows = check_text(frame, box, theme, set(), lambda *args: None,
                             box.width, box.height, margins, box.top, prs.slide_height)
        edges.append((rows[0][1], rows[-1][3]) if rows else (box.top, box.top + box.height))

    gaps = [start - end for (_, end), (start, _) in zip(edges, edges[1:])]
    # Ignore rounding of the text positions to whole EMUs.
    if max(gaps) - min(gaps) <= 2:
        return
    # Keep the original span unless the measured text needs more room.
    gap = max(0, sum(gaps) / len(gaps))
    tops = [steps[0][1].top]
    for i, old_gap in enumerate(gaps):
        tops.append(tops[-1] + steps[i + 1][1].top - steps[i][1].top + gap - old_gap)
    if tops[-1] + steps[-1][1].height > Inches(bottom) + 1:
        return

    for i, ((dot, box), top) in enumerate(zip(steps, tops)):
        top = round(top)
        dot.top += top - box.top
        box.top = top
        if i + 1 < len(tops):
            box.height = min(box.height, round(tops[i + 1]) - top)
    track.end_y = round(steps[-1][0].top + steps[-1][0].height / 2)


def light_content_frame(s):
    bg(s, CREME)
    name(rect(s, 0, 0, W, 0.08, fill=VINHO), "!!painel")
    logo(s, False)


def content_title_rows(value, width, size):
    available = Inches(width - 0.04).pt / size
    return sum(wrapped_rows(measured_words(line), available) for line in value.splitlines())


def content_title_height(rows, size):
    return 0.04 + size * (1.38 + 0.9 * 1.2) / 72 if rows > 1 else 0.6


def s_steps(prs, s, d):
    an = Anim(s)
    light_content_frame(s)
    kicker(s, d.get("kicker", ""), M, 0.42, VINHO)
    panel = has_image_panel(d)
    full_width = W - 2 * M
    heading_text = d.get("titulo", "")
    heading_size = 26
    heading_width = 6 if panel else full_width
    heading_height = 0.6
    if panel:
        rows = content_title_rows(heading_text, heading_width, heading_size)
        heading_height = content_title_height(rows, heading_size)
    heading = title(s, heading_text, M, 0.62, heading_width, heading_height,
                    color=PRETO, size=heading_size, hl=d.get("destaque_titulo"), hlc=VINHO)
    extra_height = heading_height - 0.6
    steps_top = 1.38 + extra_height
    steps_bottom = 4.78
    if panel:
        rect(s, 4.35, 1.35 + extra_height, 5.2, 3.0 - extra_height, fill=BRANCO)
        an.add(photo(s, d, 4.45, 1.45 + extra_height, 5.0, 2.8 - extra_height), gap=300, dur=700)
    rows = [(str(step.get("titulo", "")), step.get("texto", "")) for step in d.get("passos", [])]
    body_width = 3.4 if panel else full_width - 0.45
    if panel:
        stride = max(0.31, min(0.68, (3.4 - extra_height) / max(len(rows), 1)))
        tops = [steps_top + i * stride for i in range(len(rows))]
        size, boxes = fit_list([[(h, 10.5), (plain_text(t), None)] for h, t in rows],
                               width=body_width, tops=tops, bottom=steps_bottom,
                               base_height=min(0.6, stride), body_size=8.5)
    else:
        size, boxes = fit_text_only_list([(h, plain_text(t)) for h, t in rows],
                                         width=body_width, top=steps_top, bottom=steps_bottom)
    heading_size = 10.5 if panel else size * TEXT_ONLY_ITEM_TITLE_SCALE
    dot_size = 0.28 if panel else size / 64
    if len(rows) > 1:
        center = 0.17 if panel else 0.03 + dot_size / 2
        track_top = 1.55 + extra_height if panel else steps_top + center
        track = line(s, M + dot_size / 2, track_top, M + dot_size / 2, boxes[-1][0] + center, color=ROSE, w=1.5)
    steps = []
    for (h, t), (y, height) in zip(rows, boxes):
        c = rect(s, M, y + 0.03, dot_size, dot_size, fill=VINHO, line=CREME, shape=MSO_SHAPE.OVAL, lw=2)
        paragraphs = [[(h, {"bold": True, "color": PRETO, "size": heading_size})], _parse_bold(t)]
        if not panel:
            paragraphs = [runs for value, runs in zip((h, t), paragraphs) if value]
        a = text(s, M + 0.45, y, body_width, height, paragraphs, size=size)
        steps.append((c, a))
        an.add(c, gap=0); an.add(a, gap=220, eff="left")
    if len(steps) > 2 and boxes[-1][0] < H:
        space_steps(prs, s, steps, track, steps_bottom)
    tip_x, tip_y, tip_width = (4.35, 4.45, 5.2) if panel else (M, 4.85, full_width)
    text(s, tip_x, tip_y, tip_width, 0.4, d.get("dica", ""), size=8.5, color=CINZA, italic=True)
    if not an.items:
        an.add(heading)
    morph(s); an.build()


def number_font_size(value, width, model_size):
    # Reserve one em per character and account for the 0.02-inch margins from text().
    available_pt = Inches(width - 0.04).pt
    return max(1, min(model_size, int(available_pt / max(1, len(value)))))


def s_number(prs, s, d):
    from conferir import MONTSERRAT_WIDTHS, glyph_width

    an = Anim(s)
    bg(s, NOITE)
    arc_x, arc_y, diameter, thickness = 2.2, -0.7, 7.0, 0.55
    big_arc(s, arc_x, arc_y, diameter, VINHO, thickness, 180, 360)
    logo(s, True)
    kicker(s, d.get("kicker", ""), M, 0.55)
    value = str(d.get("valor", ""))
    value_top = 1.55
    radius = diameter / 2 - thickness
    arc_center_x, arc_center_y = arc_x + diameter / 2, arc_y + diameter / 2
    half_chord = sqrt(radius ** 2 - (arc_center_y - value_top) ** 2)
    # The value stays centered on the slide, so use the nearer end of the chord.
    available = Inches(2 * (half_chord - abs(arc_center_x - W / 2) - 0.1)).pt
    widths = MONTSERRAT_WIDTHS["extrabold"]
    advance = sum(glyph_width(char, widths) for char in plain_text(value)) / 1000
    size = min(number_font_size(value, W, 130), max(1, int(available / max(1, advance))))
    an.add(text(s, 0, value_top, W, 1.8, value, size=size,
                color=BRANCO, font=FONTE_FORTE, bold=True, align=PP_ALIGN.CENTER, spacing=0.8),
           eff="up", dur=800, gap=300)
    an.add(text(s, 0, 3.25, W, 0.5, d.get("legenda", ""), size=16, color=ROSE, bold=True, align=PP_ALIGN.CENTER), gap=400)
    an.add(text(s, 2.0, 3.9, 6, 0.8, d.get("texto", ""),
                size=10, color=CINZA_CLARO, align=PP_ALIGN.CENTER))
    morph(s); an.build()


def s_two_columns(prs, s, d):
    an = Anim(s)
    bg(s, CREME)
    name(rect(s, 0, 0, W / 2, H, fill=VINHO), "!!painel")
    small_arc(s, -1.0, H - 1.6, 2.4, VINHO_ESC, 0.25, 270, 360)
    logo(s, False)
    heading = title(s, d.get("titulo", ""), M, 0.45, 4.5, 0.6, size=24)
    for k, col in enumerate(d.get("colunas", [])):
        lab, items = col.get("titulo", "").upper(), col.get("itens", [])
        fg = BRANCO if k == 0 else VINHO
        sub = ROSE_CLARO if k == 0 else TEXTO
        x = M + k * (W / 2)
        label_height = max(0.5, list_text_height([(plain_text(lab), 20)], 4, 20))
        bottom = H - 0.55
        label_top = 1.3 if 1.3 + label_height <= bottom else H
        an.add(text(s, x, label_top, 4, label_height, lab, size=20,
                    color=fg, font=FONTE_FORTE, bold=True), eff="up", gap=200)
        tops = [label_top + label_height + 0.2 + i * 0.62 for i in range(len(items))]
        size, boxes = fit_list([[(plain_text(item), None)] for item in items], width=3.9,
                               tops=tops, bottom=bottom, base_height=0.55, body_size=11, inset=0.02)
        for it, (y, height) in zip(items, boxes):
            mk = text(s, x, y, 0.4, 0.4, "✕" if k == 0 else "!", size=13, color=ROSE if k == 0 else VINHO, bold=True)
            t = text(s, x + 0.42, y + 0.02, 3.9, height, it, size=size, color=sub)
            an.add(mk, gap=0); an.add(t, gap=150, eff="left")
    text(s, M, H - 0.55, 4.2, 0.4, d.get("nota", ""), size=7.5, color=ROSE_CLARO, italic=True)
    if not an.items:
        an.add(heading)
    morph(s); an.build()


def s_anatomy(prs, s, d):
    an = Anim(s)
    bg(s, BRANCO)
    photo(s, d, 0, 0, 3.6, H)
    logo(s, False)
    kicker(s, d.get("kicker", ""), 4.0, 0.42, VINHO)
    heading = title(s, d.get("titulo", ""), 4.0, 0.62, 5, 0.7, color=PRETO, size=32)
    structures = d.get("marcacoes", [])
    labels = "  ·  ".join(f"**{label}**" for item in structures
                         if (label := item.get("nome")) is not None and str(label).strip())
    text(s, 4.0, 1.28, 5, 0.3, labels, size=9)
    details = d.get("passos") or [item["desc"] for item in structures if item.get("desc")]
    width = 3.1 if d.get("indicador") else 5.1
    for i, t in enumerate(details):
        y = 1.8 + i * 0.52
        n = text(s, 4.0, y, 0.5, 0.45, f"{i+1}", size=18, color=ROSE, font=FONTE_FORTE, bold=True)
        b = text(s, 4.45, y + 0.06, width, 0.45, t, size=10, color=TEXTO)
        an.add(n, gap=0); an.add(b, gap=160, eff="left")
    if kpi := d.get("indicador"):
        kpi_width = 1.9
        value = str(kpi.get("valor", ""))
        k = name(rect(s, 7.65, 1.8, kpi_width, 2.0, fill=VINHO), "!!kpi")
        a = text(s, 7.65, 2.0, kpi_width, 0.9, value, size=number_font_size(value, kpi_width, 40), color=BRANCO,
                 font=FONTE_FORTE, bold=True, align=PP_ALIGN.CENTER)
        b = text(s, 7.75, 2.9, 1.7, 0.7, kpi.get("texto", ""), size=9.5, color=ROSE_CLARO, align=PP_ALIGN.CENTER)
        an.add(k, gap=0, eff="up"); an.add(a, gap=0, eff="up"); an.add(b, gap=200)
    if d.get("nota"):
        text(s, 4.0, 4.65, 5.5, 0.5, d["nota"], size=8, color=VINHO)
    if not an.items:
        an.add(heading)
    morph(s); an.build()


def s_comparison(prs, s, d):
    image_mode = d.get("imagem_modo", "sangrar")
    if image_mode not in ("sangrar", "conter"):
        raise ValueError("imagem_modo de comparativo deve ser sangrar ou conter")

    an = Anim(s)
    bg(s, NOITE)
    if image_mode == "conter":
        brand = logo(s, True)
        photo(s, d, 0, 0, W, 2.7, dark=True, contain=True, avoid_logo=brand)
    else:
        photo(s, d, 0, 0, W, 2.7, dark=True)
        logo(s, True)
    heading = title(s, d.get("titulo", ""), M, 2.85, 6, 0.6, size=24, hl=d.get("destaque_titulo"))
    bottom = H - 0.42 if d.get("nota") else H
    for k, col in enumerate(d.get("colunas", [])):
        h, its = col.get("titulo", ""), col.get("itens", [])
        x = M + k * 4.6
        an.add(text(s, x, 3.45, 4, 0.3, h.upper(), size=11, color=ROSE, bold=True), gap=100)
        tops = [3.78 + i * 0.3 for i in range(len(its))]
        size, boxes = fit_list([[(plain_text(item), None)] for item in its], width=4.3,
                               tops=tops, bottom=bottom, base_height=0.3, body_size=9.5)
        for it, (y, height) in zip(its, boxes):
            segs = _parse_bold(it, BRANCO)
            an.add(text(s, x, y, 4.3, height, [segs], size=size, color=CINZA_CLARO), gap=90, eff="left")
    if d.get("nota"):
        r = rect(s, 0, H - 0.42, W, 0.42, fill=VINHO)
        t = text(s, M, H - 0.42, W - 2 * M, 0.42, [[("ATENÇÃO  ", {"bold": True, "color": ROSE_CLARO}),
                 (d["nota"], {})]], size=9.5, color=BRANCO, anchor=MSO_ANCHOR.MIDDLE)
        an.add(r, gap=0); an.add(t, gap=0)
    if not an.items:
        an.add(heading)
    morph(s); an.build()


def s_alert(prs, s, d):
    an = Anim(s)
    bg(s, NOITE)
    name(rect(s, 0, 0, 0.12, H, fill=ALERTA), "!!painel")
    panel = has_image_panel(d)
    if panel:
        photo(s, d, 6.9, 0.55, 2.65, 4.5, dark=True)
    full_width = W - 2 * M
    logo(s, True, M + 0.1)
    an.add(text(s, M + 0.1, 1.05, 5, 0.3, f"⚠  {d.get('intercorrencia', '')}", size=10, color=ALERTA, bold=True, caps=True))
    title(s, d.get("titulo", ""), M + 0.1, 1.35, 5.8 if panel else full_width - 0.1, 1.0, size=24)
    items = d.get("itens", [])
    if not items:
        items = [{"titulo": label, "texto": " · ".join(d[key])}
                 for key, label in (("sinais", "Sinais de alerta"), ("conduta", "Conduta")) if d.get(key)]
    rows = [(item.get("titulo", "").upper(), item.get("texto", "")) for item in items]
    body_width = 5.5 if panel else full_width - 0.35
    if panel:
        tops = [2.55 + i * 0.75 for i in range(len(rows))]
        size, boxes = fit_list([[(h, 12), (t, None)] for h, t in rows], width=body_width, tops=tops,
                               bottom=H - 0.6, base_height=0.7, body_size=9.5)
    else:
        size, boxes = fit_text_only_list(rows, width=body_width, top=2.55, bottom=H - 0.6)
    heading_size = 12 if panel else size * TEXT_ONLY_ITEM_TITLE_SCALE
    for i, ((h, t), (y, height)) in enumerate(zip(rows, boxes)):
        n = rect(s, M + 0.1, y + 0.05, 0.08, 0.55 if panel else min(0.55, height - 0.05),
                 fill=ALERTA if i < 2 else ROSE)
        paragraphs = [[(h, {"bold": True, "color": BRANCO, "size": heading_size})], [(t, {"color": CINZA_CLARO})]]
        if not panel:
            paragraphs = [runs for value, runs in zip((h, t), paragraphs) if value]
        a = text(s, M + 0.35, y, body_width, height, paragraphs, size=size)
        an.add(n, gap=0); an.add(a, gap=250, eff="left")
    if d.get("urgente"):
        an.add(text(s, M + 0.35, H - 0.6, body_width, 0.45,
                    d["urgente"], size=9, color=ROSE_CLARO, bold=True))
    morph(s); an.build()


def s_numbers(prs, s, d):
    an = Anim(s)
    bg(s, CREME)
    big_arc(s, W - 2.0, -0.6, 4.0, ROSE, 0.4, 90, 180)
    logo(s, False)
    kicker(s, d.get("kicker", ""), M, 0.5, VINHO)
    an.add(title(s, d.get("titulo", ""), M, 0.78, 6.2, 1.7, color=PRETO, size=38, hl=d.get("destaque_titulo"), hlc=VINHO), eff="up", dur=700, gap=350)
    for i, item in enumerate(d.get("itens", [])):
        n, t = str(item.get("valor", "")), item.get("texto", "")
        x = M + i * 2.75
        a = text(s, x, 2.9, 2.6, 0.75, n, size=34, color=VINHO, font=FONTE_FORTE, bold=True)
        l = rect(s, x + 0.03, 3.68, 0.5, 0.04, fill=ROSE)
        b = text(s, x, 3.8, 2.4, 0.7, t, size=10, color=TEXTO)
        an.add(a, gap=0, eff="up"); an.add(l, gap=0); an.add(b, gap=250)
    text(s, M, H - 0.5, 7, 0.3, d.get("nota", ""), size=8, color=CINZA, italic=True)
    morph(s); an.build()


def s_closing(prs, s, d):
    an = Anim(s)
    s.shapes.add_picture(A("fundo_foto.jpg"), 0, 0, Inches(W), Inches(H))
    r = rect(s, 0, 0, W, H, fill=NOITE); _alpha(r, 0.45); name(r, "!!fundo")
    big_arc(s, W - 4.0, 1.3, 7.0, VINHO, 0.62, 180, 270)
    logo(s, True, M, 0.4, 0.55)
    an.add(title(s, d.get("titulo", ""), M, 1.9, 6, 1.0, size=54), eff="up", dur=700, gap=300)
    bar(s, M, 3.0, 0.7)
    an.add(text(s, M, 3.15, 5, 0.5, d.get("mensagem", ""), size=13, color=BRANCO))
    if d.get("contatos"):
        an.add(text(s, M, 3.8, 5, 1.2, d["contatos"], size=10, color=ROSE_CLARO))
    if d.get("qr"):
        an.add(image(s, d["qr"], W - M - 1.55, 2.15, 1.55, 1.55, "QR code"))
        an.add(text(s, W - M - 1.9, 3.8, 1.9, 0.3, d.get("qr_legenda", "Material de apoio"),
                    size=8, color=ROSE_CLARO, align=PP_ALIGN.RIGHT))
    if d.get("selo"):
        badge(s, d["selo"], W - M - 2.9, H - 0.55, w=2.9, color=VINHO)
    morph(s); an.build()


def light_content_header(s, heading_text, label):
    light_content_frame(s)
    if label:
        kicker(s, label, M, 0.42, VINHO)
    title_text = heading_text.rstrip()
    title_width, title_size = 6, 26
    rows = content_title_rows(plain_text(title_text), title_width, title_size)
    if rows > 2:
        # Keep the previous width for long titles that need both lines.
        title_width = W - 2 * M - 1
    title_height = content_title_height(rows, title_size)
    title_lines = [_parse_bold(value) for value in title_text.splitlines()]
    heading = text(s, M, 0.62, title_width, title_height, title_lines, size=title_size,
                   color=PRETO, font=FONTE_FORTE, bold=True, spacing=0.9)
    content_top = 1.35 + (title_height - 0.6)
    return heading, content_top


def s_preserved(prs, s, d, preserved):
    heading, content_top = light_content_header(s, d.get("titulo", ""), d.get("kicker"))
    frame = PreservedFrame(Inches(M), Inches(content_top), Inches(W - 2 * M), Inches(H - 0.25 - content_top), NOITE)
    objects = preserved.copy(s, {**d, "titulo": heading.text}, frame)
    animation = Anim(s)
    for shape in [heading, *objects]:
        animation.add(shape, gap=0 if shape is not heading else 250)
    morph(s)
    animation.build()


def s_from_layout(prs, s, d):
    def content_header(slide, heading, label):
        return light_content_header(slide, heading, label)[1]

    LAYOUTS[d["tipo"]](prs, s, d, content_header=content_header)
    animate_layout(s, list(s.shapes)[3:])


def s_from_julie_layout(prs, s, d):
    """Mantém a composição aprovada dos slides de negócio e parceria."""
    LAYOUTS[d["tipo"]](prs, s, d)
    shapes = list(s.shapes)
    first = shapes[0]
    if (first.left, first.top, first.width, first.height) == (0, 0, Inches(W), Inches(H)):
        name(first, "!!fundo")
    else:
        background = bg(s, BRANCO)
        s.shapes._spTree.insert(s.shapes._spTree.index(first._element), background._element)

    logos = {sha1(Path(A(asset)).read_bytes()).hexdigest()
             for asset in ("logo_branco.png", "logo_cor.png")}
    existing_logo = next((shape for shape in shapes
                          if shape.shape_type == MSO_SHAPE_TYPE.PICTURE and shape.image.sha1 in logos), None)
    # Estes layouts legados representam a marca no cabeçalho ou no arco junto ao rodapé.
    if existing_logo is None and d["tipo"] == "parceria":
        existing_logo = next(shape for shape in shapes if shape.has_text_frame and shape.text.startswith("CLINIC CURSOS"))
    if existing_logo is None and d["tipo"] == "continue_evolucao":
        existing_logo = next(shape for shape in reversed(shapes) if shape.shape_type == MSO_SHAPE_TYPE.FREEFORM)
    if existing_logo is not None:
        name(existing_logo, "!!logo")
    animate_layout(s, shapes[1:])


def animate_layout(s, shapes):
    an = Anim(s)
    for sh in shapes:
        if sh.has_text_frame or sh.has_table or sh.shape_type in (MSO_SHAPE_TYPE.PICTURE, MSO_SHAPE_TYPE.CHART):
            an.add(sh, gap=40)
    morph(s); an.build()


BOLD_LAYOUTS = {
    **dict.fromkeys(LAYOUTS, s_from_layout),
    **dict.fromkeys(("custos", "precificacao", "parceria", "continue_evolucao"), s_from_julie_layout),
    "capa": s_cover,
    "sumario": s_agenda,
    "modulo": s_section,
    "frase": s_quote,
    "pilares": s_pillars,
    "texto_imagem": s_text_image,
    "passo_a_passo": s_steps,
    "numero": s_number,
    "duas_colunas": s_two_columns,
    "anatomia": s_anatomy,
    "comparativo": s_comparison,
    "alerta": s_alert,
    "numeros": s_numbers,
    "encerramento": s_closing,
    "preservado": s_preserved,
}
