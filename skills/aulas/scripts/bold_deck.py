#!/usr/bin/env python3
"""Layouts do estilo editorial ousado, com Morph e animações de entrada."""

from pathlib import Path

from lxml import etree
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches

from clinic_deck import (
    A, ALERTA, BRANCO, CINZA, CINZA_CLARO, FONTE, FONTE_FORTE, H, LAYOUTS, M,
    PRETO, ROSE, ROSE_CLARO, TEXTO, VINHO, VINHO_ESC, W, _alpha, _parse_bold,
    arc, badge, image, line, rect, text,
)

NOITE = RGBColor(0x1C, 0x12, 0x12)      # fundo escuro quente (vinho quase preto)
NOITE2 = RGBColor(0x2A, 0x1A, 0x19)
CREME = RGBColor(0xFA, 0xF6, 0xF4)

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
    return text(s, x, y, w, 0.25, t, size=8.5, color=color, bold=True, caps=True)


def title(s, t, x, y, w, h, color=BRANCO, size=34, hl=None, hlc=ROSE):
    segs = [(t, {})]
    if hl and hl in t:
        a, b = t.split(hl, 1); segs = [(a, {}), (hl, {"color": hlc}), (b, {})]
    return text(s, x, y, w, h, [segs], size=size, color=color, font=FONTE_FORTE, bold=True, spacing=0.9)


def bar(s, x, y, w=0.6, color=ROSE, h=0.05):
    return name(rect(s, x, y, w, h, fill=color), "!!barra")


def photo(s, d, x, y, w, h, *, dark=False, prompt_height=None):
    label = {
        "prompt": d.get("prompt_imagem") or d.get("legenda") or d.get("titulo") or "Imagem do slide",
        "titulo": d.get("titulo", ""),
        "alerta": d.get("alerta_imagem"),
        "estilo": d.get("estilo_imagem", True),
    }
    before = len(s.shapes)
    path = d.get("imagem")
    height = prompt_height if prompt_height and not (path and Path(path).exists()) else h
    shape = image(s, path, x, y, w, height, label, dark)
    if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
        for i, box in enumerate(list(s.shapes)[before + 1:], 1):
            box.name = f"Texto do prompt {i}"
    shape.height = Inches(h)
    return name(shape, "!!foto")


def accent_runs(value, color):
    return [(part, {"bold": True, "color": color} if i % 2 else {})
            for i, part in enumerate(value.split("**")) if part]


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
    text(s, M, 3.45, 2.7, 0.8, [accent_runs(row, ROSE) for row in d.get("info", "").splitlines()],
         size=9.5, color=CINZA_CLARO)
    rows = max(6, (len(items) + 1) // 2)
    for i, item in enumerate(items):
        col, row = divmod(i, rows)
        x = 3.85 + col * 3.0
        y = 0.75 + row * 4.2 / rows
        a = text(s, x, y, 0.6, 0.5, f"{i+1:02d}", size=20, color=ROSE, font=FONTE_FORTE, bold=True)
        b = text(s, x + 0.62, y + 0.06, 2.2, 0.5, item, size=10, color=PRETO, bold=False)
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
    text(s, M + 0.6, 0.55, 1.4, 1.4, "“", size=120, color=VINHO, font="Georgia")
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


def s_pillars(prs, s, d):
    an = Anim(s)
    bg(s, NOITE)
    photo(s, d, 0, 0, 4.3, H, dark=True, prompt_height=H - 1)
    r = rect(s, 0, H - 1.0, 4.3, 1.0, fill=NOITE); _alpha(r, 0.6)
    text(s, M, H - 0.85, 3.6, 0.7, [accent_runs(row, ROSE) for row in d.get("info", "").splitlines()],
         size=9, color=BRANCO)
    small_arc(s, 3.55, -0.9, 1.8, VINHO, 0.2, 90, 180)
    logo(s, True)
    kicker(s, d.get("kicker", ""), 4.75, 0.55)
    an.add(title(s, d.get("titulo", ""), 4.75, 0.8, 4.6, 1.0, size=24, hl=d.get("destaque_titulo")), eff="up")
    for i, pillar in enumerate(d.get("pilares", [])):
        h, t = pillar.get("titulo", ""), pillar.get("texto", "")
        y = 2.0 + i * 0.95
        n = text(s, 4.75, y - 0.1, 1.0, 0.9, f"{i+1:02d}", size=36, color=VINHO, font=FONTE_FORTE, bold=True)
        a = text(s, 5.75, y, 3.7, 0.3, h, size=13, color=BRANCO, bold=True, caps=True)
        b = text(s, 5.75, y + 0.32, 3.7, 0.5, t, size=9.5, color=CINZA_CLARO)
        line(s, 4.8, y + 0.85, W - M, y + 0.85, color=NOITE2, w=0.75)
        an.add(n, gap=0, eff="up"); an.add(a, gap=60); an.add(b, gap=200)
    text(s, 4.75, H - 0.4, 4.8, 0.25, d.get("referencia", ""), size=6.5, color=CINZA)
    morph(s); an.build()


def s_text_image(prs, s, d):
    an = Anim(s)
    bg(s, CREME)
    photo(s, d, W - 3, 0, 3, H)
    logo(s, False, M, 0.4)
    kicker(s, d.get("kicker", ""), M, 1.3, VINHO)
    an.add(title(s, d.get("titulo", ""), M, 1.6, 5.4, 1.8, color=PRETO, size=46, hl=d.get("destaque_titulo"), hlc=VINHO), eff="up", dur=700, gap=400)
    if d.get("seta"):
        ln = line(s, 5.75, 1.0, 5.75, 4.6, color=VINHO, w=2.5)
        tri = rect(s, 5.62, 4.55, 0.26, 0.22, fill=VINHO, shape=MSO_SHAPE.ISOSCELES_TRIANGLE)
        tri.rotation = 180
        an.add(ln, gap=0, dur=900)
        an.add(tri, gap=300)
    body = [d.get("texto", "")]
    for topic in d.get("topicos", []):
        if isinstance(topic, dict):
            body.extend([f"**{topic.get('titulo', '')}**", topic.get("texto", "")])
        else:
            body.append(topic)
    body.append(d.get("destaque", ""))
    an.add(text(s, M, 3.55, 5.0, 1.2, [row for row in body if row], size=11, color=TEXTO), eff="up")
    morph(s); an.build()


def s_steps(prs, s, d):
    an = Anim(s)
    bg(s, CREME)
    name(rect(s, 0, 0, W, 0.08, fill=VINHO), "!!painel")
    logo(s, False)
    kicker(s, d.get("kicker", ""), M, 0.42, VINHO)
    title(s, d.get("titulo", ""), M, 0.62, 6, 0.6, color=PRETO, size=26, hl=d.get("destaque_titulo"), hlc=VINHO)
    rect(s, 4.35, 1.35, 5.2, 3.0, fill=BRANCO)
    p = photo(s, d, 4.45, 1.45, 5.0, 2.8)
    an.add(p, gap=300, dur=700)
    steps = d.get("passos", [])
    step_height = min(0.68, 3.4 / max(len(steps), 1))
    if len(steps) > 1:
        line(s, M + 0.14, 1.55, M + 0.14, 1.55 + step_height * (len(steps) - 1), color=ROSE, w=1.5)
    for i, step in enumerate(steps):
        h, t = step.get("titulo", ""), step.get("texto", "")
        y = 1.38 + i * step_height
        c = rect(s, M, y + 0.03, 0.28, 0.28, fill=VINHO, line=CREME, shape=MSO_SHAPE.OVAL, lw=2)
        a = text(s, M + 0.45, y, 3.4, 0.6, [[(h, {"bold": True, "color": PRETO, "size": 10.5})], _parse_bold(t)], size=8.5)
        an.add(c, gap=0); an.add(a, gap=220, eff="left")
    text(s, 4.35, 4.45, 5.2, 0.4, d.get("dica", ""), size=8.5, color=CINZA, italic=True)
    morph(s); an.build()


def number_font_size(value, width, model_size):
    # Reserve one em per character and account for the 0.02-inch margins from text().
    available_pt = Inches(width - 0.04).pt
    return max(1, min(model_size, int(available_pt / max(1, len(value)))))


def s_number(prs, s, d):
    an = Anim(s)
    bg(s, NOITE)
    big_arc(s, 2.2, -0.7, 7.0, VINHO, 0.55, 180, 360)
    logo(s, True)
    kicker(s, d.get("kicker", ""), M, 0.55)
    value = str(d.get("valor", ""))
    an.add(text(s, 0, 1.55, W, 1.8, value, size=number_font_size(value, W, 130),
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
        lab, items = col.get("titulo", ""), col.get("itens", [])
        fg = BRANCO if k == 0 else VINHO
        sub = ROSE_CLARO if k == 0 else TEXTO
        x = M + k * (W / 2)
        an.add(text(s, x, 1.3, 4, 0.5, lab.upper(), size=20, color=fg, font=FONTE_FORTE, bold=True), eff="up", gap=200)
        for i, it in enumerate(items):
            y = 2.0 + i * 0.62
            mk = text(s, x, y, 0.4, 0.4, "✕" if k == 0 else "!", size=13, color=ROSE if k == 0 else VINHO, bold=True)
            t = text(s, x + 0.42, y + 0.02, 3.9, 0.55, it, size=11, color=sub)
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
    labels = "  ·  ".join(f"**{item.get('nome', '')}**" for item in structures)
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
    an = Anim(s)
    bg(s, NOITE)
    photo(s, d, 0, 0, W, 2.7, dark=True)
    logo(s, True)
    heading = title(s, d.get("titulo", ""), M, 2.85, 6, 0.6, size=24, hl=d.get("destaque_titulo"))
    for k, col in enumerate(d.get("colunas", [])):
        h, its = col.get("titulo", ""), col.get("itens", [])
        x = M + k * 4.6
        an.add(text(s, x, 3.45, 4, 0.3, h.upper(), size=11, color=ROSE, bold=True), gap=100)
        for i, it in enumerate(its):
            segs = accent_runs(it, BRANCO)
            an.add(text(s, x, 3.78 + i * 0.3, 4.3, 0.3, [segs], size=9.5, color=CINZA_CLARO), gap=90, eff="left")
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
    photo(s, d, 6.9, 0.55, 2.65, 4.5, dark=True)
    logo(s, True, M + 0.1)
    an.add(text(s, M + 0.1, 1.05, 5, 0.3, f"⚠  {d.get('intercorrencia', '')}", size=10, color=ALERTA, bold=True, caps=True))
    title(s, d.get("titulo", ""), M + 0.1, 1.35, 5.8, 1.0, size=24)
    items = d.get("itens", [])
    if not items:
        items = [{"titulo": label, "texto": " · ".join(d[key])}
                 for key, label in (("sinais", "Sinais de alerta"), ("conduta", "Conduta")) if d.get(key)]
    for i, item in enumerate(items):
        h, t = item.get("titulo", ""), item.get("texto", "")
        y = 2.55 + i * 0.75
        n = rect(s, M + 0.1, y + 0.05, 0.08, 0.55, fill=ALERTA if i < 2 else ROSE)
        a = text(s, M + 0.35, y, 5.5, 0.7, [[(h.upper(), {"bold": True, "color": BRANCO, "size": 12})], [(t, {"color": CINZA_CLARO})]], size=9.5)
        an.add(n, gap=0); an.add(a, gap=250, eff="left")
    if d.get("urgente"):
        an.add(text(s, M + 0.35, H - 0.6, 5.5, 0.45, d["urgente"], size=9, color=ROSE_CLARO, bold=True))
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


def s_preserved(prs, s, d, preserved):
    bg(s, CREME)
    logo(s, False)
    kicker(s, d.get("kicker", ""), M, 0.22, VINHO)
    heading = title(s, d.get("titulo", ""), M, 0.54, W - 2 * M - 1, 0.64, color=PRETO, size=26)
    bar(s, M, 1.23, color=VINHO)
    objects = preserved.copy(s, d, (Inches(M), Inches(1.43), Inches(W - 2 * M), Inches(H - 1.68)))
    animation = Anim(s)
    for shape in [heading, *objects]:
        animation.add(shape, gap=0 if shape is not heading else 250)
    morph(s)
    animation.build()


def s_from_layout(prs, s, d):
    """Usa o layout padrão com Morph e entrada suave do conteúdo."""
    LAYOUTS[d["tipo"]](prs, s, d)
    an = Anim(s)
    for sh in list(s.shapes)[1:]:
        if sh.has_text_frame or sh.has_table or sh.shape_type in (MSO_SHAPE_TYPE.PICTURE, MSO_SHAPE_TYPE.CHART):
            an.add(sh, gap=40)
    morph(s); an.build()


BOLD_LAYOUTS = {
    **dict.fromkeys(LAYOUTS, s_from_layout),
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
