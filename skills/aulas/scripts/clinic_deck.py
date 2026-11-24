#!/usr/bin/env python3
"""
Clinic Cursos — gerador de apresentações de aula (.pptx).

Uso:
    python clinic_deck.py roteiro.json saida.pptx

O roteiro é um JSON: {"titulo": "...", "slides": [ {"tipo": "...", ...}, ... ]}
Cada "tipo" corresponde a uma função layout_<tipo> abaixo. Veja SKILL.md para
os campos de cada tipo.

Imagens: qualquer campo "imagem" aceita um caminho de arquivo. Se faltar ou o
arquivo não existir, entra um espaço reservado cinza com a descrição, para o
professor trocar depois.
"""
import copy
import json, os, sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.oxml.ns import qn
from lxml import etree

from restyle import PreservedFrame, PreservedSlides

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

# ---------------------------------------------------------------- identidade
VINHO = RGBColor(0x9C, 0x4C, 0x48)
VINHO_ESC = RGBColor(0x6E, 0x2F, 0x2C)
ROSE = RGBColor(0xB6, 0x8B, 0x85)
ROSE_CLARO = RGBColor(0xF4, 0xEC, 0xEA)
CINZA = RGBColor(0x6E, 0x6F, 0x73)
CINZA_CLARO = RGBColor(0xE6, 0xE6, 0xE7)
TEXTO = RGBColor(0x40, 0x40, 0x40)
PRETO = RGBColor(0x14, 0x12, 0x11)
BRANCO = RGBColor(0xFF, 0xFF, 0xFF)
VERDE = RGBColor(0x6A, 0xA8, 0x4F)      # selo "Conheça nosso curso"
ALERTA = RGBColor(0xD3, 0x2F, 0x2F)     # só em intercorrências

FONTE = "Montserrat"
FONTE_FORTE = "Montserrat ExtraBold"

W, H = 10.0, 5.625
M = 0.45  # margem lateral


def A(name):
    return os.path.join(ASSETS, name)


# ---------------------------------------------------------------- primitivas
def rect(s, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, lw=0.75):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.shadow.inherit = False
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(lw)
    return sh


def text(s, x, y, w, h, runs, size=12, color=TEXTO, bold=False, font=FONTE,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.1, caps=False,
         italic=False):
    """runs: str | list de parágrafos; cada parágrafo é str ou lista de
    segmentos (texto, {opções}). Use **negrito** dentro de str simples."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) else [runs]
    if paras and any(isinstance(x, tuple) for x in paras):
        paras = [paras]  # lista de segmentos = um parágrafo só
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align; para.line_spacing = spacing
        segs = p if isinstance(p, list) else _parse_bold(p)
        for seg in segs:
            t, o = (seg, {}) if isinstance(seg, str) else seg
            r = para.add_run(); r.text = t.upper() if caps else t
            f = r.font; f.name = o.get("font", font); f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold); f.italic = o.get("italic", italic)
            f.color.rgb = o.get("color", color)
    return tb


def _parse_bold(t):
    """'texto **destaque** texto' -> segmentos; destaque em negrito vinho."""
    out, bold = [], False
    for part in str(t).split("**"):
        if part:
            out.append((part, {"bold": True, "color": VINHO} if bold else {}))
        bold = not bold
    return out or [""]


def line(s, x1, y1, x2, y2, color=VINHO, w=1.0, dash=False):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(w)
    if dash:
        ln = c.line._get_or_add_ln()
        pd = etree.SubElement(ln, qn("a:prstDash")); pd.set("val", "dash")
    return c


def image(s, path, x, y, w, h, label="imagem", dark=False):
    """Insere imagem recortada para preencher a caixa (cover). Sem arquivo ->
    espaço reservado com a descrição."""
    if path and os.path.exists(path):
        from PIL import Image
        iw, ih = Image.open(path).size
        pic = s.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
        box, img = w / h, iw / ih
        if img > box:
            c = (1 - box / img) / 2; pic.crop_left = pic.crop_right = c
        else:
            c = (1 - img / box) / 2; pic.crop_top = pic.crop_bottom = c
        return pic
    if isinstance(label, dict):  # {"prompt":..., "alerta":..., "titulo":...}
        return prompt_box(s, x, y, w, h, label["prompt"], label.get("titulo", ""), label.get("alerta"), dark,
                          label.get("estilo", True))
    bg = RGBColor(0x2A, 0x26, 0x25) if dark else CINZA_CLARO
    fg = ROSE if dark else CINZA
    r = rect(s, x, y, w, h, fill=bg)
    text(s, x + 0.15, y, w - 0.3, h, [[("▢  ", {"size": 14, "color": fg})],
         [(label, {"size": 9, "color": fg})]], align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    return r


def dots(s, x, y, color=VINHO, cols=3, rows=3, gap=0.085, d=0.035):
    """Grade de pontinhos — eco do 'DNA' do logo."""
    for i in range(rows):
        for j in range(cols):
            rect(s, x + j * gap, y + i * gap, d, d, fill=color, shape=MSO_SHAPE.OVAL)


def bracket(s, x, y, w, h, color=VINHO, t=0.045, arm=0.28):
    """Colchete do logo: cantos superior-esquerdo e inferior-direito."""
    rect(s, x, y, arm, t, fill=color); rect(s, x, y, t, arm, fill=color)
    rect(s, x + w - arm, y + h - t, arm, t, fill=color)
    rect(s, x + w - t, y + h - arm, t, arm, fill=color)


def arc(s, x, y, d, color=ROSE, thick=0.18, start=180, end=270):
    """Arco do 'C' do logo como grafismo (anel parcial desenhado em
    freeform). (x, y, d) = caixa do círculo; ângulos em graus, 0 = direita,
    sentido horário."""
    import math
    cx, cy, r2 = x + d / 2, y + d / 2, d / 2
    r1 = r2 - thick
    n = 40
    angs = [math.radians(start + (end - start) * i / n) for i in range(n + 1)]
    outer = [(cx + r2 * math.cos(a), cy + r2 * math.sin(a)) for a in angs]
    inner = [(cx + r1 * math.cos(a), cy + r1 * math.sin(a)) for a in reversed(angs)]
    pts = outer + inner
    E = 914400
    fb = s.shapes.build_freeform(int(pts[0][0] * E), int(pts[0][1] * E), scale=1.0)
    fb.add_line_segments([(int(px * E), int(py * E)) for px, py in pts[1:]], close=True)
    sh = fb.convert_to_shape()
    sh.fill.solid(); sh.fill.fore_color.rgb = color; sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def badge(s, txt, x, y, w=2.6, color=VERDE):
    """Selo verde 'Conheça nosso curso…' (herdado do template)."""
    r = rect(s, x, y, w, 0.26, fill=color)
    text(s, x, y, w, 0.26, txt, size=7, color=BRANCO, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def _lab(d, default):
    """Rótulo do espaço de imagem: prompt (se houver prompt_imagem) ou texto."""
    if d.get("prompt_imagem"):
        return {"prompt": d["prompt_imagem"], "alerta": d.get("alerta_imagem"), "titulo": d.get("titulo", ""),
                "estilo": d.get("estilo_imagem", True)}
    return d.get("legenda") or default


def notes(s, txt):
    if txt:
        tf = s.notes_slide.notes_text_frame
        tf.text = txt + ("\n\n" + tf.text if tf.text else "")


# ---------------------------------------------------------------- prompts de imagem
ESTILO_CASA = ("Estilo da casa Clinic Cursos: ilustração médica 3D realista, estilo atlas de anatomia moderno, "
               "iluminação suave de estúdio, fundo creme claro liso, detalhes em vinho #9C4C48 e rosé #B68B85, "
               "alta definição, sem texto, sem letras, sem rótulos, sem marca d'água.")
ESTILO_FOTO = ("Estilo da casa Clinic Cursos (foto): fotografia editorial realista de estúdio, luz suave e difusa, "
               "pele natural sem retoque excessivo, tons quentes discretos com toques de vinho #9C4C48, "
               "alta definição, sem texto, sem letras, sem marca d'água.")
PROMPTS = []  # (n, slide_titulo, formato, prompt, alerta)


def formato(w, h):
    r = w / h
    if r > 2.2:  return "horizontal 16:9 (será recortada em faixa panorâmica, deixe o assunto centralizado)"
    if r > 1.6:  return "horizontal 16:9"
    if r > 1.2:  return "horizontal 3:2"
    if r > 0.85: return "quadrado 1:1"
    if r > 0.6:  return "vertical 2:3"
    return "vertical 9:16 (será recortada, deixe o assunto centralizado)"


def prompt_box(s, x, y, w, h, prompt, slide_titulo="", alerta=None, dark=False, estilo=True):
    """Quadro reservado com o prompt pronto para gerar a imagem no ChatGPT.
    alerta: aviso (ex.: anatomia que precisa de conferência)."""
    n = len(PROMPTS) + 1
    fmt = formato(w, h)
    st = ESTILO_FOTO if estilo == "foto" else (ESTILO_CASA if estilo else "")
    full = prompt.strip().rstrip(".") + ". " + (st + " " if st else "") + f"Formato {fmt.split(' (')[0]}."
    PROMPTS.append((n, slide_titulo, fmt, full, alerta))
    bgc = RGBColor(0x2A, 0x1E, 0x1D) if dark else RGBColor(0xF6, 0xEF, 0xED)
    fg = CINZA_CLARO if dark else TEXTO
    r = rect(s, x, y, w, h, fill=bgc, line=ROSE, lw=1.25)
    ln = r.line._get_or_add_ln(); pd = etree.SubElement(ln, qn("a:prstDash")); pd.set("val", "dash")
    r.name = f"PROMPT {n:02d}"
    pad = 0.14
    text(s, x + pad, y + pad, w - 2 * pad, 0.22,
         [[("✦ PROMPT DE IMAGEM ", {"bold": True, "color": VINHO if not dark else ROSE}),
           (f"#{n:02d} · {fmt.split(' (')[0]}", {"color": CINZA})]], size=7)
    body_h = h - 2 * pad - 0.5 - (0.42 if alerta else 0)
    size = 7 if len(full) > 520 or w < 3 else 7.5
    if w * h < 6: size = 6.2
    text(s, x + pad, y + pad + 0.28, w - 2 * pad, body_h, full, size=size, color=fg, spacing=1.05)
    if alerta:
        text(s, x + pad, y + h - pad - 0.62, w - 2 * pad, 0.4,
             [[("⚠ ", {"color": ALERTA}), (alerta, {"color": ALERTA if not dark else ROSE, "bold": True})]], size=6.5)
    text(s, x + pad, y + h - pad - 0.18, w - 2 * pad, 0.18, "copie, gere no ChatGPT e substitua este quadro pela imagem",
         size=6, color=CINZA, italic=True)
    try:
        cur = s.notes_slide.notes_text_frame.text
        s.notes_slide.notes_text_frame.text = (cur + "\n\n" if cur else "") + f"PROMPT #{n:02d} ({fmt}):\n{full}" + (f"\n⚠ {alerta}" if alerta else "")
    except Exception:
        pass
    return r


def prompts_markdown(titulo):
    out = [f"# Prompts de imagem — {titulo}", "", "Todos os prompts já trazem o estilo da casa no final. Dica: gere todos na mesma conversa do ChatGPT; assim as imagens saem mais parecidas entre si.", ""]
    for n, st, fmt, pr, al in PROMPTS:
        out += [f"## #{n:02d} · {st}", f"Formato: {fmt}", "", pr, ""]
        if al: out += [f"> ⚠ {al}", ""]
    return "\n".join(out)


# ---------------------------------------------------------------- moldes
def bg_photo(s, shade=0.0):
    s.shapes.add_picture(A("fundo_foto.jpg"), 0, 0, Inches(W), Inches(H))
    if shade:
        r = rect(s, 0, 0, W, H, fill=PRETO)
        _alpha(r, shade)


def _alpha(shape, a):
    sf = shape.fill._xPr.find(qn("a:solidFill"))
    clr = sf[0]
    el = etree.SubElement(clr, qn("a:alpha")); el.set("val", str(int(a * 100000)))


def header(s, title, dark_logo=False):
    """Tarja escura do template + título em caixa alta + logo à direita."""
    pic = s.shapes.add_picture(A("fundo_foto.jpg"), 0, 0, Inches(W), Inches(0.62))
    pic.crop_top = 0.0; pic.crop_bottom = 1 - (0.62 / W) / (941 / 1672)
    rect(s, 0, 0.62, W, 0.035, fill=VINHO)
    text(s, M, 0.12, W - 2 * M - 0.8, 0.42, title, size=15, color=BRANCO,
         font=FONTE_FORTE, bold=True, caps=True, anchor=MSO_ANCHOR.MIDDLE)
    s.shapes.add_picture(A("logo_branco.png"), Inches(W - M - 0.62), Inches(0.12), height=Inches(0.42))


def header_editorial(s, title, kicker=None, *, title_height=0.45):
    """Variação refinada (estilo dos slides novos do HOF): fundo claro,
    título vinho, grade de pontinhos e fio fino."""
    dots(s, M, 0.36)
    if kicker:
        text(s, M + 0.36, 0.18, 6, 0.22, kicker, size=8, color=ROSE, bold=True, caps=True)
    title_top = 0.3
    text(s, M + 0.36, title_top, W - 2 * M - 1.2, title_height, title, size=20, color=VINHO,
         font=FONTE_FORTE, bold=True, caps=True, anchor=MSO_ANCHOR.MIDDLE)
    divider_top = title_top + title_height + 0.11
    line(s, M, divider_top, W - M, divider_top, color=VINHO, w=0.75)
    s.shapes.add_picture(A("logo_cor.png"), Inches(W - M - 0.62), Inches(0.24), height=Inches(0.44))
    return divider_top


def footer(s, n, total, label=""):
    text(s, M, H - 0.32, 5, 0.2, label, size=7, color=CINZA, caps=True)


# ---------------------------------------------------------------- layouts
def layout_capa(prs, s, d):
    """Capa da aula. campos: titulo, subtitulo (ex.: "Módulo 1"), curso"""
    bg_photo(s, 0.25)
    arc(s, -2.4, H - 1.5, 4.8, color=VINHO, thick=0.34, start=270, end=360)
    s.shapes.add_picture(A("logo_branco.png"), Inches(M + 0.05), Inches(0.45), height=Inches(0.85))
    if d.get("curso"):
        text(s, M + 0.05, 2.0, 6, 0.3, d["curso"], size=10, color=ROSE, bold=True, caps=True)
    text(s, M + 0.05, 2.3, 6.2, 1.6, d.get("titulo", ""), size=36, color=BRANCO,
         font=FONTE_FORTE, bold=True, spacing=0.95, anchor=MSO_ANCHOR.TOP)
    if d.get("subtitulo"):
        rect(s, M + 0.08, 4.05, 0.5, 0.04, fill=ROSE)
        text(s, M + 0.05, 4.18, 6, 0.4, d["subtitulo"], size=12, color=BRANCO)


def layout_modulo(prs, s, d):
    """Capa de módulo (divisória). campos: numero, titulo, descricao, selo"""
    bg_photo(s, 0.15)
    s.shapes.add_picture(A("logo_branco.png"), Inches(M + 0.05), Inches(0.45), height=Inches(0.55))
    num = str(d.get("numero", "")).zfill(2)
    text(s, M, 1.65, 3, 1.2, num, size=72, color=ROSE, font=FONTE_FORTE, bold=True)
    rect(s, M + 0.08, 3.0, 0.04, 0.95, fill=VINHO)
    text(s, M + 0.3, 2.95, 7, 0.6, d.get("titulo", ""), size=30, color=BRANCO,
         font=FONTE_FORTE, bold=True, caps=True)
    if d.get("descricao"):
        text(s, M + 0.3, 3.55, 6, 0.5, d["descricao"], size=11, color=CINZA_CLARO)
    if d.get("selo"):
        badge(s, d["selo"], W - M - 2.9, H - 0.6, w=2.9)


def layout_sumario(prs, s, d):
    """Tópicos / sumário. campos: titulo, itens[], destaque (índice opcional)"""
    header(s, d.get("titulo", "Conteúdo programático"))
    itens = d.get("itens", [])
    if d.get("info"):
        text(s, M, 0.85, W - 2 * M, 0.25, d["info"], size=9, color=VINHO, bold=True)
    half = (len(itens) + 1) // 2
    top = 1.25 if d.get("info") else 1.0
    rowh = min(0.52, (H - top - 0.45) / max(half, 1))
    for i, it in enumerate(itens):
        col, row = divmod(i, half)
        x = M + col * 4.65; y = top + row * rowh
        hl = d.get("destaque") == i
        text(s, x, y, 0.6, rowh, f"{i+1:02d}", size=18, color=VINHO if hl or True else ROSE,
             font=FONTE_FORTE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        text(s, x + 0.62, y, 3.8, rowh, it, size=11, color=PRETO if hl else TEXTO,
             bold=hl, anchor=MSO_ANCHOR.MIDDLE)
        line(s, x + 0.62, y + rowh - 0.02, x + 4.3, y + rowh - 0.02, color=CINZA_CLARO, w=0.5)


def layout_texto_imagem(prs, s, d):
    """Texto + imagem clínica. campos: titulo, kicker, topicos[] (str ou
    {titulo, texto}), imagem, legenda, lado ('direita'|'esquerda'), destaque"""
    header_editorial(s, d.get("titulo", ""), d.get("kicker"))
    esq = d.get("lado") == "esquerda"
    ix = M if esq else 5.55; tx = 4.95 if esq else M
    image(s, d.get("imagem"), ix, 1.1, 4.0, 3.95, _lab(d, "imagem clínica"))
    if d.get("legenda") and d.get("imagem"):
        text(s, ix, 5.08, 4, 0.2, d["legenda"], size=7, color=CINZA, italic=True)
    tops = d.get("topicos", [])
    y = 1.15; step = min(0.95, 3.5 / max(len(tops), 1))
    for i, t in enumerate(tops):
        rect(s, tx, y + 0.05, 0.34, 0.34, line=VINHO, shape=MSO_SHAPE.OVAL, lw=1)
        text(s, tx, y + 0.05, 0.34, 0.34, str(i + 1), size=10, color=VINHO, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if isinstance(t, dict):
            body = [[(t.get("titulo", ""), {"bold": True, "color": PRETO, "size": 11})]] + \
                   [_parse_bold(t.get("texto", ""))]
        else:
            body = [_parse_bold(t)]
        text(s, tx + 0.5, y, 4.0, step, body, size=10)
        y += step
    if d.get("destaque"):
        rect(s, tx, 4.6, 4.5, 0.48, fill=ROSE_CLARO)
        rect(s, tx, 4.6, 0.05, 0.48, fill=VINHO)
        text(s, tx + 0.18, 4.6, 4.25, 0.48, d["destaque"], size=9, color=VINHO_ESC,
             bold=True, anchor=MSO_ANCHOR.MIDDLE)


def layout_anatomia(prs, s, d):
    """Anatomia: imagem grande com marcações numeradas.
    campos: titulo, imagem, marcacoes[{nome, x, y, desc}] (x,y = 0..1 da
    imagem), nota"""
    header(s, d.get("titulo", ""))
    ix, iy, iw, ih = M, 0.85, 5.6, 4.45
    image(s, d.get("imagem"), ix, iy, iw, ih, _lab(d, "imagem anatômica"))
    mk = sorted(d.get("marcacoes", []), key=lambda m: float(m.get("y", 0.5)))
    lx = 6.35; step = min(0.6, 4.2 / max(len(mk), 1)); y0 = 0.95
    ys, prev = [], y0 - step
    for i, m in enumerate(mk):  # rótulo alinhado à altura da marcação, sem sobrepor
        py = iy + float(m.get("y", 0.5)) * ih
        yy = min(max(prev + step, py - 0.13), H - 0.95 - (len(mk) - i) * step)
        ys.append(yy); prev = yy
    for i, m in enumerate(mk):
        px = ix + float(m.get("x", 0.5)) * iw; py = iy + float(m.get("y", 0.5)) * ih
        ly = ys[i] + 0.13
        line(s, px, py, lx - 0.08, ly, color=VINHO, w=0.75)
        rect(s, px - 0.11, py - 0.11, 0.22, 0.22, fill=VINHO, line=BRANCO, shape=MSO_SHAPE.OVAL, lw=1)
        text(s, px - 0.11, py - 0.11, 0.22, 0.22, str(i + 1), size=7, color=BRANCO,
             bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        text(s, lx, ys[i], 3.2, step,
             [[(f"{i+1}  ", {"bold": True, "color": VINHO}), (m.get("nome", ""), {"bold": True, "color": PRETO})],
              [(m.get("desc", ""), {"size": 8, "color": CINZA})]], size=10)
    if d.get("nota"):
        ny = min((ys[-1] + step + 0.1) if ys else 1.0, H - 0.75)
        text(s, lx, ny, 3.2, 0.4, d["nota"], size=8, color=VINHO, italic=True)


def layout_passo_a_passo(prs, s, d):
    """Passo a passo de técnica. campos: titulo, passos[{titulo, texto}],
    imagem (opcional, mostra coluna lateral), dica"""
    header(s, d.get("titulo", ""))
    passos = d.get("passos", [])
    n = len(passos)
    if d.get("imagem") is not None or n > 5:
        # vertical, com imagem à direita
        image(s, d.get("imagem"), 6.0, 0.9, 3.55, 4.2, _lab(d, "foto da técnica"))
        step = min(0.8, 4.1 / max(n, 1)); y = 0.95
        line(s, M + 0.17, y + 0.2, M + 0.17, y + step * (n - 1) + 0.2, color=ROSE, w=1.25)
        for i, p in enumerate(passos):
            rect(s, M, y + 0.03, 0.34, 0.34, fill=VINHO, shape=MSO_SHAPE.OVAL)
            text(s, M, y + 0.03, 0.34, 0.34, str(i + 1), size=10, color=BRANCO, bold=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            text(s, M + 0.5, y, 4.9, step,
                 [[(p.get("titulo", ""), {"bold": True, "color": PRETO})], _parse_bold(p.get("texto", ""))],
                 size=9.5)
            y += step
    else:
        # horizontal: trilha com círculos (como a linha do tempo do HOF)
        gap = (W - 2 * M) / n; cy = 1.75
        line(s, M + gap / 2, cy, W - M - gap / 2, cy, color=ROSE, w=1.5)
        for i, p in enumerate(passos):
            cx = M + gap * i + gap / 2
            rect(s, cx - 0.36, cy - 0.36, 0.72, 0.72, fill=BRANCO, line=VINHO, shape=MSO_SHAPE.OVAL, lw=1.5)
            text(s, cx - 0.36, cy - 0.36, 0.72, 0.72, f"{i+1:02d}", size=16, color=VINHO,
                 font=FONTE_FORTE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            text(s, cx - gap / 2 + 0.08, cy + 0.5, gap - 0.16, 0.45, p.get("titulo", ""), size=10.5,
                 color=PRETO, bold=True, caps=True, align=PP_ALIGN.CENTER)
            text(s, cx - gap / 2 + 0.1, cy + 0.95, gap - 0.2, 1.9, _parse_bold(p.get("texto", "")),
                 size=9, align=PP_ALIGN.CENTER)
    if d.get("dica"):
        rect(s, M, H - 0.75, W - 2 * M if d.get("imagem") is None and n <= 5 else 5.3, 0.4, fill=ROSE_CLARO)
        text(s, M + 0.15, H - 0.75, 5.0 if (d.get("imagem") is not None or n > 5) else W - 2 * M - 0.3, 0.4,
             [[("DICA  ", {"bold": True, "color": VINHO}), (d["dica"], {})]], size=9,
             anchor=MSO_ANCHOR.MIDDLE)


def layout_antes_depois(prs, s, d):
    """Antes e depois. campos: titulo, antes, depois (caminhos), rotulo_antes,
    rotulo_depois, legenda (produto/técnica/tempo)"""
    header(s, d.get("titulo", ""))
    w = (W - 2 * M - 0.2) / 2; y = 0.9; h = 3.95
    for k, (key, lab) in enumerate([("antes", d.get("rotulo_antes", "Antes")),
                                     ("depois", d.get("rotulo_depois", "Depois"))]):
        x = M + k * (w + 0.2)
        image(s, d.get(key), x, y, w, h, f"foto {lab.lower()}")
        rect(s, x, y + h - 0.36, 1.3, 0.36, fill=PRETO if k == 0 else VINHO)
        text(s, x, y + h - 0.36, 1.3, 0.36, lab, size=10, color=BRANCO, bold=True, caps=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if d.get("legenda"):
        text(s, M, y + h + 0.08, W - 2 * M, 0.3, d["legenda"], size=8.5, color=CINZA,
             align=PP_ALIGN.CENTER)


def layout_artigo(prs, s, d):
    """Print de artigo com destaque na conclusão.
    campos: titulo, imagem (print), referencia, conclusao, comentario"""
    header_editorial(s, d.get("titulo", "Análise de artigo"), d.get("kicker", "Evidência científica"))
    image(s, d.get("imagem"), M, 1.1, 4.3, 3.95, "print do artigo (título + abstract)")
    rect(s, M, 1.1, 4.3, 3.95, line=CINZA_CLARO, lw=0.75)
    bx, by, bw, bh = 5.1, 1.2, 4.45, 2.35
    rect(s, bx, by, bw, bh, fill=ROSE_CLARO)
    bracket(s, bx - 0.08, by - 0.08, bw + 0.16, bh + 0.16, color=VINHO)
    text(s, bx + 0.25, by + 0.18, bw - 0.5, 0.25, "CONCLUSÃO", size=8, color=VINHO, bold=True)
    text(s, bx + 0.25, by + 0.45, bw - 0.5, bh - 0.6, d.get("conclusao", ""), size=12,
         color=PRETO, italic=True, spacing=1.15)
    if d.get("comentario"):
        text(s, bx, 3.75, bw, 0.9,
             [[("Na prática clínica: ", {"bold": True, "color": VINHO}), (d["comentario"], {})]], size=9.5)
    if d.get("referencia"):
        text(s, bx, H - 0.6, bw, 0.4, d["referencia"], size=7, color=CINZA)


def layout_grafico(prs, s, d):
    """Gráficos e infográficos. campos: titulo, tipo_grafico ('barra'|'coluna'|'linha'|
    'pizza'), categorias[], series[{nome, valores[]}], destaque{valor, texto},
    fonte"""
    header(s, d.get("titulo", ""))
    tipo = {"barra": XL_CHART_TYPE.BAR_CLUSTERED, "coluna": XL_CHART_TYPE.COLUMN_CLUSTERED,
            "linha": XL_CHART_TYPE.LINE_MARKERS, "pizza": XL_CHART_TYPE.DOUGHNUT}[d.get("tipo_grafico", "coluna")]
    cd = CategoryChartData(); cd.categories = d.get("categorias", [])
    for se in d.get("series", []):
        cd.add_series(se["nome"], se["valores"])
    has_kpi = bool(d.get("destaque"))
    cw = 6.1 if has_kpi else W - 2 * M
    gf = s.shapes.add_chart(tipo, Inches(M), Inches(0.9), Inches(cw), Inches(4.15), cd)
    ch = gf.chart
    ch.font.name = FONTE; ch.font.size = Pt(9); ch.font.color.rgb = TEXTO
    pal = [VINHO, ROSE, CINZA, VINHO_ESC]
    if tipo == XL_CHART_TYPE.DOUGHNUT:
        pts = ch.plots[0].series[0].points
        for i in range(len(d.get("categorias", []))):
            pts[i].format.fill.solid(); pts[i].format.fill.fore_color.rgb = pal[i % 4]
        ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.RIGHT
        ch.legend.include_in_layout = False
    else:
        for i, se in enumerate(ch.plots[0].series):
            if tipo == XL_CHART_TYPE.LINE_MARKERS:
                se.format.line.color.rgb = pal[i % 4]; se.format.line.width = Pt(2.25)
                se.marker.format.fill.solid(); se.marker.format.fill.fore_color.rgb = pal[i % 4]
            else:
                se.format.fill.solid(); se.format.fill.fore_color.rgb = pal[i % 4]
        if tipo != XL_CHART_TYPE.LINE_MARKERS:
            ch.plots[0].gap_width = 60
            ch.plots[0].has_data_labels = True
            dl = ch.plots[0].data_labels; dl.font.size = Pt(8); dl.font.bold = True
            dl.font.color.rgb = TEXTO; dl.position = XL_LABEL_POSITION.OUTSIDE_END
        va = ch.value_axis; va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = CINZA_CLARO
        va.format.line.fill.background(); va.tick_labels.font.size = Pt(8)
        ch.category_axis.format.line.color.rgb = CINZA_CLARO
        ch.category_axis.tick_labels.font.size = Pt(8.5)
        ch.has_legend = len(d.get("series", [])) > 1
        if ch.has_legend:
            ch.legend.position = XL_LEGEND_POSITION.TOP; ch.legend.include_in_layout = False
    if has_kpi:
        k = d["destaque"]; kx = 6.85
        rect(s, kx, 1.15, 2.7, 3.2, fill=VINHO)
        dots(s, kx + 0.25, 1.35, color=ROSE)
        text(s, kx + 0.2, 1.75, 2.3, 1.0, k.get("valor", ""), size=40, color=BRANCO,
             font=FONTE_FORTE, bold=True)
        text(s, kx + 0.2, 2.8, 2.3, 1.4, k.get("texto", ""), size=10, color=BRANCO)
    if d.get("fonte"):
        text(s, M, H - 0.5, W - 2 * M, 0.2, "Fonte: " + d["fonte"], size=7, color=CINZA)


def layout_tabela(prs, s, d):
    """Comparativo em tabela. campos: titulo, colunas[], linhas[[...]],
    destacar_coluna (índice), nota"""
    header(s, d.get("titulo", ""))
    cols = d.get("colunas", []); rows = d.get("linhas", [])
    nr, nc = len(rows) + 1, len(cols)
    th = min(4.1, 0.42 * nr)
    gt = s.shapes.add_table(nr, nc, Inches(M), Inches(0.95), Inches(W - 2 * M), Inches(th))
    tbl = gt.table
    tblPr = gt._element.graphic.graphicData.tbl.tblPr
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is not None:
        sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # sem estilo, grade
    first_w = 1.9 if nc > 2 else (W - 2 * M) / nc
    tbl.columns[0].width = Inches(first_w)
    for j in range(1, nc):
        tbl.columns[j].width = Inches((W - 2 * M - first_w) / (nc - 1))
    hl = d.get("destacar_coluna")
    for i in range(nr):
        for j in range(nc):
            c = tbl.cell(i, j)
            v = cols[j] if i == 0 else (rows[i - 1][j] if j < len(rows[i - 1]) else "")
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.04)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.text = ""
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            r = p.add_run(); r.text = str(v); f = r.font; f.name = FONTE; f.size = Pt(9)
            c.fill.solid()
            if i == 0:
                c.fill.fore_color.rgb = VINHO if j != hl else VINHO_ESC
                f.bold = True; f.color.rgb = BRANCO; f.size = Pt(9.5)
            elif j == 0:
                c.fill.fore_color.rgb = ROSE_CLARO; f.bold = True; f.color.rgb = PRETO
            else:
                c.fill.fore_color.rgb = RGBColor(0xFB, 0xF7, 0xF6) if j == hl else (BRANCO if i % 2 else RGBColor(0xF7, 0xF7, 0xF7))
                f.color.rgb = TEXTO
                if j == hl: f.bold = True; f.color.rgb = VINHO_ESC
    if d.get("nota"):
        text(s, M, 0.95 + th + 0.12, W - 2 * M, 0.3, d["nota"], size=8, color=CINZA, italic=True)


def layout_caso_clinico(prs, s, d):
    """Caso clínico. campos: titulo, paciente{idade, sexo, queixa},
    avaliacao, plano, resultado, imagens[] (até 3), legenda"""
    header_editorial(s, d.get("titulo", "Caso clínico"), d.get("kicker", "Caso clínico"))
    x, y, w = M, 1.1, 3.9
    rect(s, x, y, w, 3.95, fill=ROSE_CLARO)
    rect(s, x, y, w, 0.05, fill=VINHO)
    pac = d.get("paciente", {})
    yy = y + 0.2
    chips = [v for v in [pac.get("sexo"), f'{pac["idade"]} anos' if pac.get("idade") else None] if v]
    cx = x + 0.2
    for c in chips:
        cw = 0.15 + 0.075 * len(c)
        rect(s, cx, yy, cw, 0.26, fill=VINHO, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        text(s, cx, yy, cw, 0.26, c, size=8, color=BRANCO, bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE)
        cx += cw + 0.1
    yy += 0.42
    for lab, key in [("Queixa", None), ("Avaliação", "avaliacao"), ("Plano", "plano"), ("Resultado", "resultado")]:
        val = pac.get("queixa") if key is None else d.get(key)
        if not val:
            continue
        text(s, x + 0.2, yy, w - 0.4, 0.2, lab, size=7.5, color=VINHO, bold=True, caps=True)
        tb = text(s, x + 0.2, yy + 0.2, w - 0.4, 0.62, _parse_bold(val), size=9)
        yy += 0.85
    imgs = d.get("imagens") or [None, None]
    n = len(imgs); gx = 4.55; gw = W - M - gx
    iw = (gw - 0.12 * (n - 1)) / n
    for i, im in enumerate(imgs):
        image(s, im, gx + i * (iw + 0.12), 1.1, iw, 3.6, ["pré", "pós", "controle"][i % 3])
    if d.get("legenda"):
        text(s, gx, 4.8, gw, 0.25, d["legenda"], size=8, color=CINZA, align=PP_ALIGN.CENTER)


def layout_alerta(prs, s, d):
    """Intercorrências / alerta. campos: titulo, intercorrencia, sinais[],
    conduta[], urgente (texto da faixa)"""
    header(s, d.get("titulo", "Intercorrências"))
    rect(s, 0, 0.655, W, 0.42, fill=ALERTA)
    text(s, M, 0.655, W - 2 * M, 0.42,
         [[("⚠  ", {"size": 13}), (d.get("intercorrencia", "").upper(), {"bold": True})]],
         size=11, color=BRANCO, anchor=MSO_ANCHOR.MIDDLE)
    cw = (W - 2 * M - 0.3) / 2
    for k, (lab, key, col) in enumerate([("Sinais de alerta", "sinais", ALERTA), ("Conduta", "conduta", VINHO)]):
        x = M + k * (cw + 0.3); y = 1.3
        text(s, x, y, cw, 0.3, lab, size=11, color=col, bold=True, caps=True)
        line(s, x, y + 0.34, x + cw, y + 0.34, color=col, w=1.25)
        yy = y + 0.48
        items = d.get(key, [])
        step = min(0.55, 2.7 / max(len(items), 1))
        for i, it in enumerate(items):
            mark = "!" if k == 0 else str(i + 1)
            rect(s, x, yy + 0.04, 0.26, 0.26, fill=col, shape=MSO_SHAPE.OVAL)
            text(s, x, yy + 0.04, 0.26, 0.26, mark, size=8, color=BRANCO, bold=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            text(s, x + 0.38, yy, cw - 0.4, step, _parse_bold(it), size=9.5)
            yy += step
    if d.get("urgente"):
        rect(s, M, H - 0.78, W - 2 * M, 0.42, fill=PRETO)
        text(s, M + 0.2, H - 0.78, W - 2 * M - 0.4, 0.42, d["urgente"], size=9.5, color=BRANCO,
             bold=True, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)


def layout_frase(prs, s, d):
    """Frase de impacto. campos: frase, autor, fundo ('vinho'|'foto'|'claro')"""
    fundo = d.get("fundo", "vinho")
    if fundo == "foto":
        bg_photo(s, 0.35); fg, ac = BRANCO, ROSE
    elif fundo == "claro":
        rect(s, 0, 0, W, H, fill=ROSE_CLARO); fg, ac = VINHO_ESC, VINHO
    else:
        rect(s, 0, 0, W, H, fill=VINHO); fg, ac = BRANCO, ROSE
    arc(s, W - 2.4, -2.6, 5.0, color=ac, thick=0.34, start=90, end=180)
    text(s, M + 0.3, 0.9, 1, 1, "“", size=90, color=ac, font="Georgia")
    text(s, M + 0.5, 1.75, W - 2 * M - 1.5, 2.4, d.get("frase", ""), size=24, color=fg,
         font=FONTE_FORTE, bold=True, spacing=1.05, anchor=MSO_ANCHOR.MIDDLE)
    if d.get("autor"):
        rect(s, M + 0.55, 4.35, 0.45, 0.035, fill=ac)
        text(s, M + 0.5, 4.45, 6, 0.3, d["autor"], size=10, color=fg)
    logo = "logo_branco.png" if fundo != "claro" else "logo_vinho.png"
    s.shapes.add_picture(A(logo), Inches(W - M - 0.7), Inches(H - 0.75), height=Inches(0.5))


def layout_referencias(prs, s, d):
    """Referências bibliográficas. campos: titulo, refs[]"""
    header(s, d.get("titulo", "Referências"))
    refs = d.get("refs", [])
    two = len(refs) > 6
    per = (len(refs) + 1) // 2 if two else len(refs)
    cw = (W - 2 * M - 0.3) / 2 if two else W - 2 * M
    size = 8 if two else 9
    step = min(0.62, 4.1 / max(per, 1))
    for i, r in enumerate(refs):
        col, row = divmod(i, per) if two else (0, i)
        x = M + col * (cw + 0.3); y = 0.95 + row * step
        text(s, x, y, 0.35, step, f"{i+1}.", size=size, color=VINHO, bold=True)
        text(s, x + 0.32, y, cw - 0.35, step, r, size=size, color=TEXTO, spacing=1.0)


def layout_encerramento(prs, s, d):
    """Encerramento com contato. campos: titulo, mensagem, contatos[],
    qr (caminho de imagem), selo"""
    bg_photo(s, 0.3)
    arc(s, W - 2.0, H - 2.2, 4.6, color=VINHO, thick=0.34, start=180, end=270)
    s.shapes.add_picture(A("logo_branco.png"), Inches(M + 0.05), Inches(0.5), height=Inches(1.0))
    text(s, M + 0.05, 1.9, 6, 0.9, d.get("titulo", "Obrigado!"), size=36, color=BRANCO,
         font=FONTE_FORTE, bold=True)
    if d.get("mensagem"):
        text(s, M + 0.05, 2.75, 5.5, 0.6, d["mensagem"], size=11, color=CINZA_CLARO)
    y = 3.45
    for c in d.get("contatos", []):
        rect(s, M + 0.08, y + 0.09, 0.08, 0.08, fill=ROSE, shape=MSO_SHAPE.OVAL)
        text(s, M + 0.28, y, 5, 0.26, c, size=10.5, color=BRANCO, bold=True)
        y += 0.32
    if d.get("qr") is not None:
        rect(s, W - M - 1.55, 1.9, 1.55, 1.55, fill=BRANCO)
        image(s, d.get("qr"), W - M - 1.47, 1.98, 1.39, 1.39, "QR code")
        text(s, W - M - 1.9, 3.5, 1.9, 0.3, d.get("qr_legenda", "Material de apoio"), size=8,
             color=ROSE, align=PP_ALIGN.RIGHT)
    if d.get("selo"):
        badge(s, d["selo"], W - M - 2.9, H - 0.55, w=2.9)




def _brl(v):
    try:
        return "R$ " + f"{float(v):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return str(v) if v not in (None, "") else "R$ —"


def layout_custos(prs, s, d):
    """Composição do preço (6 blocos de custo). campos: titulo, kicker,
    custos[{titulo, exemplos}], formula"""
    rect(s, 0, 0, W, H, fill=RGBColor(0xFA, 0xF6, 0xF4))
    arc(s, -1.9, -1.9, 3.2, color=VINHO, thick=0.3, start=0, end=90)
    s.shapes.add_picture(A("logo_cor.png"), Inches(W - M - 0.68), Inches(0.32), height=Inches(0.42))
    text(s, 1.55, 0.45, 6, 0.25, d.get("kicker", "Precificação"), size=8.5, color=VINHO, bold=True, caps=True)
    text(s, 1.55, 0.68, 7, 0.6, [[("Como compor ", {}), ("seu preço", {"color": VINHO})]] if not d.get("titulo") else d["titulo"],
         size=26, color=PRETO, font=FONTE_FORTE, bold=True)
    custos = d.get("custos") or [
        {"titulo": "Insumos", "exemplos": "gaze, seringa, agulha, luva"},
        {"titulo": "Injetável", "exemplos": "toxina, ácido hialurônico, fios"},
        {"titulo": "Custos fixos", "exemplos": "locação, internet, contabilidade"},
        {"titulo": "Experiência", "exemplos": "snacks, bebidas, cafés"},
        {"titulo": "Hora profissional", "exemplos": "o valor do seu tempo e da sua técnica"},
        {"titulo": "Financeiros", "exemplos": "maquininha, antecipação, impostos"}]
    cw, ch, gx, gy = 2.9, 1.25, 0.2, 0.2
    x0 = (W - 3 * cw - 2 * gx) / 2; y0 = 1.55
    for i, c in enumerate(custos[:6]):
        x = x0 + (i % 3) * (cw + gx); y = y0 + (i // 3) * (ch + gy)
        dark = i in (1, 4)
        rect(s, x, y, cw, ch, fill=VINHO if dark else BRANCO, line=None if dark else CINZA_CLARO)
        text(s, x + 0.2, y + 0.12, 1, 0.5, f"{i+1:02d}", size=22, color=ROSE if dark else VINHO, font=FONTE_FORTE, bold=True)
        text(s, x + 0.2, y + 0.6, cw - 0.4, 0.3, c.get("titulo", ""), size=11.5, color=BRANCO if dark else PRETO, bold=True, caps=True)
        text(s, x + 0.2, y + 0.88, cw - 0.4, 0.35, c.get("exemplos", ""), size=8.5, color=ROSE_CLARO if dark else CINZA)
    f = d.get("formula", "Preço justo = custos totais + hora profissional + margem de lucro")
    rect(s, x0, H - 0.72, 3 * cw + 2 * gx, 0.42, fill=PRETO)
    text(s, x0, H - 0.72, 3 * cw + 2 * gx, 0.42, f, size=10, color=BRANCO, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def layout_precificacao(prs, s, d):
    """Tabela de lucratividade (editável). campos: titulo, kicker,
    estrategias[{nome, texto}], procedimentos[{nome, estrategia, produto,
    preco, custo_fixo, insumos}], taxa_pct (3), imposto_pct (8), nota.
    Custo financeiro, imposto e lucro são calculados pelo gerador."""
    rect(s, 0, 0, W, H, fill=RGBColor(0xFA, 0xF6, 0xF4))
    s.shapes.add_picture(A("logo_cor.png"), Inches(W - M - 0.68), Inches(0.28), height=Inches(0.42))
    dots(s, M, 0.4)
    text(s, M + 0.36, 0.22, 6, 0.22, d.get("kicker", "Precificação"), size=8, color=VINHO, bold=True, caps=True)
    text(s, M + 0.36, 0.38, 7.5, 0.5, d.get("titulo", "Aumente seu lucro com técnicas de venda"), size=20,
         color=PRETO, font=FONTE_FORTE, bold=True)
    est = d.get("estrategias") or [
        {"nome": "Upsell", "texto": "versão de maior valor do que o paciente pretendia"},
        {"nome": "Cross-sell", "texto": "algo complementar ao que ele já comprou"},
        {"nome": "Downsell", "texto": "opção mais acessível quando a principal não fecha"}]
    ew = (W - 2 * M - 0.3) / 3
    for i, e in enumerate(est[:3]):
        x = M + i * (ew + 0.15)
        rect(s, x, 1.0, 0.05, 0.5, fill=VINHO)
        text(s, x + 0.15, 0.98, ew - 0.2, 0.55, [[(e["nome"].upper(), {"bold": True, "color": VINHO, "size": 9.5})],
                                                [(e.get("texto", ""), {"size": 8, "color": TEXTO})]], size=8)
    tx, tp = d.get("taxa_pct", 3), d.get("imposto_pct", 8)
    procs = d.get("procedimentos") or [{"nome": "Procedimento " + str(i + 1), "estrategia": ""} for i in range(5)]
    rows = [("Produto injetável", "produto"), (f"Custo fixo por hora", "custo_fixo"), ("Insumos", "insumos"),
            (f"Custo financeiro ({tx}% maquininha)", "_taxa"), (f"Imposto ({tp}% Simples Nacional)", "_imp"),
            ("Preço médio em clínicas", "preco"), ("Lucro líquido por paciente", "_lucro")]
    nc = len(procs) + 1; nr = len(rows) + 1
    top = 1.68; th = H - top - 0.45
    gt = s.shapes.add_table(nr, nc, Inches(M), Inches(top), Inches(W - 2 * M), Inches(th))
    tbl = gt.table
    sid = gt._element.graphic.graphicData.tbl.tblPr.find(qn("a:tableStyleId"))
    if sid is not None: sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"
    fw = 2.35; tbl.columns[0].width = Inches(fw)
    for j in range(1, nc): tbl.columns[j].width = Inches((W - 2 * M - fw) / (nc - 1))
    tbl.rows[0].height = Inches(0.6)
    for i in range(1, nr): tbl.rows[i].height = Inches((th - 0.6) / (nr - 1))

    def val(p, key):
        try:
            prod = float(p.get("produto") or 0); pr = float(p.get("preco") or 0)
            cf = float(p.get("custo_fixo") or 0); ins = float(p.get("insumos") or 0)
        except (TypeError, ValueError):
            return p.get(key, "")
        if not p.get("preco"):
            return "R$ —"
        if key == "_lucro" and any(p.get(k) in (None, "") for k in ("produto", "custo_fixo", "insumos")):
            return "R$ —"  # missing cost must not count as zero
        taxa = round(pr * tx / 100); imp = round(pr * tp / 100)
        return {"_taxa": taxa, "_imp": imp, "_lucro": pr - prod - cf - ins - taxa - imp}.get(key, p.get(key))

    for i in range(nr):
        for j in range(nc):
            c = tbl.cell(i, j); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_left = c.margin_right = Inches(0.08); c.margin_top = c.margin_bottom = Inches(0.02)
            tf = c.text_frame; tf.text = ""; para = tf.paragraphs[0]
            para.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            last = i == nr - 1
            c.fill.solid()
            if i == 0:
                c.fill.fore_color.rgb = PRETO if j == 0 else VINHO
                if j == 0:
                    r = para.add_run(); r.text = "Procedimento"
                    r.font.size = Pt(8.5); r.font.bold = True; r.font.color.rgb = BRANCO; r.font.name = FONTE
                else:
                    p = procs[j - 1]
                    if p.get("estrategia"):
                        r = para.add_run(); r.text = p["estrategia"].upper()
                        r.font.size = Pt(6.5); r.font.bold = True; r.font.color.rgb = ROSE_CLARO; r.font.name = FONTE
                        para = tf.add_paragraph(); para.alignment = PP_ALIGN.CENTER
                    r = para.add_run(); r.text = p.get("nome", "")
                    r.font.size = Pt(7.5); r.font.bold = True; r.font.color.rgb = BRANCO; r.font.name = FONTE
                continue
            label, key = rows[i - 1]
            txt = label if j == 0 else _brl(val(procs[j - 1], key))
            r = para.add_run(); r.text = txt; f = r.font; f.name = FONTE
            f.size = Pt(8.5 if not last else 9.5)
            if last:
                c.fill.fore_color.rgb = ROSE_CLARO; f.bold = True; f.color.rgb = VINHO_ESC
            elif key == "preco":
                c.fill.fore_color.rgb = BRANCO; f.bold = True; f.color.rgb = PRETO
            else:
                c.fill.fore_color.rgb = BRANCO if i % 2 else RGBColor(0xF5, 0xF1, 0xF0)
                f.color.rgb = TEXTO if j else PRETO; f.bold = (j == 0)
    text(s, M, H - 0.36, W - 2 * M, 0.25, d.get("nota", "Valores de referência — edite na tabela conforme sua região e seus custos."),
         size=7, color=CINZA, italic=True)
    notes(s, "Para recalcular custo financeiro, imposto e lucro com outros valores, peça ao Claude ou ajuste à mão: "
             f"lucro = preço − produto − custo fixo − insumos − {tx}% − {tp}% do preço.")


PRECIFICACAO_PADRAO = [
    {"tipo": "custos"},
    {"tipo": "precificacao"},
]

P = lambda n: A(os.path.join("parcerias", n))


def layout_parceria(prs, s, d):
    """Slide de parceria (Galderma, Ilikia…). campos: parceiro, kicker, titulo,
    destaque_titulo (trecho do título em vinho), texto, beneficios[], validade,
    logo, qr, contato[] (linhas), qr_legenda"""
    rect(s, 0, 0, W, H, fill=RGBColor(0xFA, 0xF8, 0xF7))
    rect(s, 0, 0, 0.09, H, fill=VINHO)
    arc(s, W - 1.1, -0.75, 1.5, color=ROSE, thick=0.16, start=90, end=180)
    text(s, M + 0.1, 0.38, 6.5, 0.35,
         [[("CLINIC CURSOS", {"color": VINHO}), ("   ×   ", {"color": ROSE, "font": FONTE, "bold": False}),
           (d.get("parceiro", "").upper(), {"color": CINZA})]],
         size=15, font=FONTE_FORTE, bold=True)
    y = 1.2
    if d.get("kicker"):
        rect(s, M + 0.1, y + 0.02, 0.035, 0.2, fill=VINHO)
        text(s, M + 0.25, y, 4, 0.25, d["kicker"], size=8.5, color=CINZA, bold=True, caps=True)
        y += 0.38
    tit, hl = d.get("titulo", ""), d.get("destaque_titulo")
    segs = [(tit, {})]
    if hl and hl in tit:
        a, b = tit.split(hl, 1); segs = [(a, {}), (hl, {"color": VINHO}), (b, {})]
    text(s, M + 0.1, y, 5.3, 1.1, [segs], size=24, color=PRETO, font=FONTE_FORTE, bold=True, spacing=0.95)
    y += 1.15
    if d.get("texto"):
        text(s, M + 0.1, y, 5.0, 0.6, d["texto"], size=9.5, color=TEXTO); y += 0.68
    for b in d.get("beneficios", []):
        rect(s, M + 0.12, y + 0.04, 0.2, 0.2, fill=VINHO, shape=MSO_SHAPE.OVAL)
        text(s, M + 0.12, y + 0.04, 0.2, 0.2, "✓", size=7, color=BRANCO, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        nl = 1 + len(b.replace("**", "")) // 72
        text(s, M + 0.42, y, 4.8, 0.2 + 0.17 * nl, _parse_bold(b), size=9.5)
        y += 0.15 + 0.17 * nl
    if d.get("validade"):
        y += 0.08
        rect(s, M + 0.1, y, 2.6, 0.3, fill=VINHO)
        text(s, M + 0.1, y, 2.6, 0.3, d["validade"], size=8, color=BRANCO, bold=True, caps=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # painel direito
    px, py, pw, ph = 6.05, 1.05, 3.5, 3.9
    rect(s, px, py, pw, ph, fill=ROSE_CLARO)
    rect(s, px, py, pw, 0.05, fill=VINHO)
    if d.get("logo") and os.path.exists(d["logo"]):
        rect(s, px + 0.25, py + 0.3, pw - 0.5, 0.62, fill=BRANCO)
        from PIL import Image
        iw, ih = Image.open(d["logo"]).size
        lh = 0.46; lw = min(pw - 0.7, lh * iw / ih); lh = lw * ih / iw
        s.shapes.add_picture(d["logo"], Inches(px + (pw - lw) / 2), Inches(py + 0.3 + (0.62 - lh) / 2), Inches(lw), Inches(lh))
    rect(s, px + (pw - 1.6) / 2, py + 1.12, 1.6, 1.6, fill=BRANCO)
    image(s, d.get("qr"), px + (pw - 1.45) / 2, py + 1.195, 1.45, 1.45, "QR code")
    if d.get("contato"):
        segs = [[(c, {"bold": i == 1, "color": PRETO if i == 1 else (VINHO if i == 2 else TEXTO),
                      "size": 10 if i == 1 else 8})] for i, c in enumerate(d["contato"])]
        text(s, px + 0.2, py + 2.85, pw - 0.4, 0.75, segs, align=PP_ALIGN.CENTER, size=8)
    text(s, px + 0.2, py + ph - 0.32, pw - 0.4, 0.22, d.get("qr_legenda", "Escaneie o código"), size=7,
         color=CINZA, bold=True, caps=True, align=PP_ALIGN.CENTER)


def layout_continue_evolucao(prs, s, d):
    """Vitrine dos próximos cursos (ClinicPlus, Residência, Pós, MBA).
    campos: cards[{titulo, texto, icone, qr, selo}], frase1, frase2"""
    rect(s, 0, 0, W, H, fill=RGBColor(0xFA, 0xF8, 0xF7))
    arc(s, -1.9, -1.9, 3.2, color=VINHO, thick=0.3, start=0, end=90)
    text(s, 2.5, 0.28, 5, 0.42, "CONTINUE SUA", size=22, color=CINZA, font=FONTE_FORTE, bold=True, align=PP_ALIGN.CENTER)
    text(s, 2.5, 0.66, 5, 0.55, "EVOLUÇÃO", size=32, color=VINHO, font=FONTE_FORTE, bold=True, align=PP_ALIGN.CENTER)
    text(s, 2.5, 1.25, 5, 0.25, d.get("subtitulo", "Acesso ao conhecimento que transforma sua carreira na estética"),
         size=8, color=CINZA, caps=True, align=PP_ALIGN.CENTER)
    cards = d.get("cards", [])
    cw, ch = 4.4, 1.38; gx = 0.2; x0 = (W - 2 * cw - gx) / 2; y0 = 1.62
    for i, c in enumerate(cards[:4]):
        x = x0 + (i % 2) * (cw + gx); y = y0 + (i // 2) * (ch + 0.14)
        rect(s, x, y, cw, ch, fill=VINHO, shape=MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.08
        rect(s, x + 0.2, y + (ch - 0.78) / 2, 0.78, 0.78, line=ROSE, shape=MSO_SHAPE.OVAL, lw=1.5)
        if c.get("icone") and os.path.exists(c["icone"]):
            s.shapes.add_picture(c["icone"], Inches(x + 0.29), Inches(y + (ch - 0.6) / 2), Inches(0.6), Inches(0.6))
        text(s, x + 1.15, y + 0.14, 2.0, 0.35, c.get("titulo", ""), size=14, color=BRANCO, font=FONTE_FORTE, bold=True)
        text(s, x + 1.15, y + 0.5, 2.05, 0.7, c.get("texto", ""), size=7.5, color=BRANCO, spacing=1.0)
        if c.get("selo"):
            rect(s, x + 1.15, y + ch - 0.32, 1.1, 0.2, fill=BRANCO, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
            text(s, x + 1.15, y + ch - 0.32, 1.1, 0.2, c["selo"], size=6.5, color=VINHO, bold=True, caps=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        text(s, x + cw - 1.15, y + 0.08, 1.0, 0.18, "Acesse agora", size=6, color=BRANCO, bold=True, caps=True,
             align=PP_ALIGN.CENTER)
        rect(s, x + cw - 1.08, y + 0.28, 0.98, 0.98, fill=BRANCO)
        image(s, c.get("qr"), x + cw - 1.03, y + 0.33, 0.88, 0.88, "QR")
    by = y0 + 2 * ch + 0.14 + 0.18
    arc(s, 1.55, by, 0.55, color=VINHO, thick=0.1, start=270, end=360)
    text(s, 2.25, by, 7, 0.5, [[(d.get("frase1", "Estamos com você em cada etapa da sua evolução."), {"color": CINZA})],
                               [(d.get("frase2", "Escolha o próximo passo e transforme seu futuro!"), {"color": VINHO, "bold": True})]],
         size=10.5, caps=True)


PARCERIAS_PADRAO = [
    {"tipo": "parceria", "parceiro": "Galderma", "kicker": "Parceria exclusiva",
     "titulo": "Condição especial para alunos Clinic Cursos", "destaque_titulo": "alunos Clinic Cursos",
     "texto": "Uma parceria pensada para impulsionar sua prática clínica, com condições especiais firmadas diretamente com a Galderma.",
     "beneficios": ["**Até 12% de desconto** em até 4 frascos de Sculptra®, 4 frascos de Dysport® e 10 mL de Restylane®",
                    "Acesso à plataforma **GAINCONNECT**", "Participação no programa de fidelidade **Aspire Club®**"],
     "validade": "Válido até dezembro de 2026", "logo": "parcerias/logos_galderma.png", "qr": "parcerias/qr_galderma.png",
     "contato": ["Para detalhamento das condições, fale com o especialista de negócios:", "Luis Henrique",
                 "Especialista de negócios · (11) 96647-6816"],
     "qr_legenda": "Escaneie para falar no WhatsApp"},
    {"tipo": "parceria", "parceiro": "Ilikia", "kicker": "Parceria exclusiva",
     "titulo": "Mais possibilidades para aprimorar sua prática clínica", "destaque_titulo": "aprimorar sua prática clínica",
     "texto": "O aprendizado não termina em sala de aula. A parceria entre Clinic Cursos e Ilikia aproxima nossos alunos de soluções desenvolvidas com ciência, inovação e visão de futuro.",
     "beneficios": ["Condições exclusivas", "Portfólio Ilikia", "Atendimento personalizado"],
     "validade": "Benefício exclusivo para alunos", "logo": "parcerias/logo_ilikia.png", "qr": "parcerias/qr_ilikia.png",
     "contato": ["", "Descubra suas vantagens", "Escaneie e fale com a equipe Ilikia"],
     "qr_legenda": "Benefício exclusivo para alunos"},
    {"tipo": "continue_evolucao", "cards": [
        {"titulo": "ClinicPlus", "texto": "Plataforma de vídeos introdutórios sobre harmonização facial e corporal. Teórico e prático.",
         "icone": "parcerias/ic_clinicplus.png", "qr": "parcerias/qr_clinicplus.png", "selo": "30 dias grátis"},
        {"titulo": "Residência", "texto": "Programa intensivo de 4 meses de aprimoramento técnico em harmonização facial.",
         "icone": "parcerias/ic_residencia.png", "qr": "parcerias/qr_residencia.png"},
        {"titulo": "Pós-graduação", "texto": "Harmonização facial e corporal, estilo carrossel, com certificação e práticas 100% presenciais.",
         "icone": "parcerias/ic_pos.png", "qr": "parcerias/qr_pos.png"},
        {"titulo": "MBA", "texto": "Formação completa em Gestão e Marketing para Clínicas. Aprenda a gerir, posicionar e escalar seu negócio.",
         "icone": "parcerias/ic_mba.png", "qr": "parcerias/qr_mba.png"}]},
]


def layout_preservado(prs, s, d, preserved):
    title_lines = d.get("titulo", "").rstrip().splitlines()
    divider_top = header_editorial(s, title_lines, d.get("kicker"), title_height=0.8)
    content_top = divider_top + 0.19
    frame = PreservedFrame(Inches(M), Inches(content_top), Inches(W - 2 * M), Inches(H - 0.35 - content_top), PRETO)
    preserved.copy(s, d, frame)


LAYOUTS = {k[7:]: v for k, v in globals().items() if k.startswith("layout_")}


def validate_lesson_structure(slides, script_positions, spec):
    opening = {"capa": 1, "sumario": 2}
    tail = {kind: rank for rank, kind in enumerate(
        ("referencias", "custos", "precificacao", "parceria", "continue_evolucao", "encerramento")
    )}
    kinds = [slide["tipo"] for slide in slides]
    last_body = max((i for i, kind in enumerate(kinds, 1) if kind not in opening and kind not in tail), default=0)
    errors = []
    for kind, position in opening.items():
        if kinds[position - 1:position] != [kind]:
            errors.append(f"slide {position}: deve ser {kind}")

    seen = set()
    quotes = 0
    latest_tail = None
    closing_label = f"slide {len(script_positions) + 1}"
    for i, slide in enumerate(slides, 1):
        kind = slide["tipo"]
        position = script_positions.get(id(slide))
        label = f"slide {position}" if position else f"slide automático {i}"
        if "encerramento" in seen:
            errors.append(f"{label}: {kind} vem depois do encerramento")
        if kind in opening:
            if i != opening[kind]:
                errors.append(f"{label}: {kind} só pode aparecer no slide {opening[kind]}")
        elif kind in tail:
            if i < last_body:
                errors.append(f"{label}: {kind} deve vir depois do último conteúdo")
            if latest_tail is not None and tail[kind] < tail[latest_tail]:
                errors.append(f"{label}: {kind} deve vir antes de {latest_tail}")
            else:
                latest_tail = kind
            if kind in {"custos", "precificacao", "continue_evolucao"} and kind in seen:
                errors.append(f"{label}: {kind} só pode aparecer uma vez")
            if kind == "encerramento" and kind not in seen:
                closing_label = label
        elif kind == "frase":
            quotes += 1
            if quotes > 2:
                errors.append(f"{label}: frase excede o limite de duas por aula")
        elif kind != "modulo" and "modulo" not in seen:
            errors.append(f"{label}: {kind} deve vir depois de um modulo")
        seen.add(kind)

    for option, required in (("precificacao", ("custos", "precificacao")),
                             ("parcerias", ("parceria", "continue_evolucao"))):
        if spec.get(option, True) or seen.intersection(required):
            for kind in required:
                if kind not in seen:
                    errors.append(f"{closing_label}: falta {kind} antes do encerramento")
    if "encerramento" not in seen:
        errors.append(f"{closing_label}: falta encerramento no fim da aula")
    if errors:
        raise ValueError("esqueleto inválido:\n" + "\n".join(errors))


def number_modules(slides):
    number = 0
    for i, slide in enumerate(slides, 1):
        if slide["tipo"] == "modulo":
            number += 1
            expected = f"{number:02d}"
            if "numero" in slide and str(slide["numero"]).zfill(2) != expected:
                print(f"Aviso, slide {i}: numero do modulo {slide['numero']!r} substituído por {expected}",
                      file=sys.stderr)
            slide["numero"] = expected


def build(spec, out, base_dir=".", *, layouts=LAYOUTS, enforce_structure=False):
    slides = copy.deepcopy(spec["slides"])
    script_positions = {id(slide): i for i, slide in enumerate(slides, 1)}
    avulso = spec.get("avulso", False)
    tipos = [x.get("tipo") for x in slides]
    for tipo in tipos:
        if not isinstance(tipo, str) or tipo not in layouts:
            raise SystemExit(f"tipo desconhecido: {tipo}. Disponíveis: {', '.join(layouts)}")
    if not avulso and spec.get("parcerias", True) and "parceria" not in tipos and "continue_evolucao" not in tipos:
        pos = tipos.index("encerramento") if "encerramento" in tipos else len(slides)
        extra = copy.deepcopy(PARCERIAS_PADRAO)
        for e in extra:  # assets padrão
            for k in ("logo", "qr"):
                if e.get(k): e[k] = A(e[k])
            for c in e.get("cards", []):
                c["icone"] = A(c["icone"]); c["qr"] = A(c["qr"])
        slides[pos:pos] = extra
    tipos = [x.get("tipo") for x in slides]
    if not avulso and spec.get("precificacao", True) and "precificacao" not in tipos:
        pos = tipos.index("parceria") if "parceria" in tipos else (tipos.index("encerramento") if "encerramento" in tipos else len(slides))
        slides[pos:pos] = [x for x in copy.deepcopy(PRECIFICACAO_PADRAO) if x["tipo"] not in tipos]
    if enforce_structure:
        if not avulso:
            validate_lesson_structure(slides, script_positions, spec)
        number_modules(slides)

    PROMPTS.clear()
    prs = Presentation()
    prs.slide_width = Inches(W); prs.slide_height = Inches(H)
    blank = prs.slide_layouts[6]
    total = len(slides)
    preserved = PreservedSlides()
    for n, d in enumerate(slides, 1):
        # resolve caminhos relativos
        for k in ("imagem", "antes", "depois", "qr", "logo"):
            if isinstance(d.get(k), str) and d[k] and not os.path.isabs(d[k]):
                d[k] = os.path.join(base_dir, d[k])
        if "imagens" in d:
            image_paths = []
            for path in d["imagens"]:
                if isinstance(path, dict):
                    if path.get("decorativa") is True:
                        continue
                    path = path.get("caminho")
                    if not isinstance(path, str):
                        raise ValueError(f"slide {n}: caminho em imagens deve ser texto")
                if isinstance(path, str) and not os.path.isabs(path):
                    path = os.path.join(base_dir, path)
                image_paths.append(path)
            d["imagens"] = image_paths
        s = prs.slides.add_slide(blank)
        tipo = d.get("tipo")
        if tipo == "preservado":
            if isinstance(d.get("deck"), str) and d["deck"]:
                d["deck"] = os.path.join(base_dir, d["deck"])
            layouts[tipo](prs, s, d, preserved)
        else:
            layouts[tipo](prs, s, d)
        if layouts is LAYOUTS and tipo not in ("capa", "modulo", "frase", "encerramento", "parceria", "continue_evolucao", "custos", "precificacao"):
            footer(s, n, total, spec.get("rodape", ""))
        notes(s, d.get("notas"))
    prs.save(out)
    if PROMPTS:
        open(os.path.splitext(out)[0] + " - prompts de imagem.md", "w", encoding="utf-8").write(prompts_markdown(spec.get("titulo", "")))
    return out


if __name__ == "__main__":
    spec_path, out = sys.argv[1], sys.argv[2]
    spec = json.load(open(spec_path, encoding="utf-8"))
    build(spec, out, os.path.dirname(os.path.abspath(spec_path)))
    print("ok:", out)
