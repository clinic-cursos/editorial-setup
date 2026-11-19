#!/usr/bin/env python3
"""Exploração criativa 'Editorial ousado' — HOF básico.
Morph entre slides (formas com nome '!!...') + animações de entrada."""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clinic_deck import *  # noqa
from clinic_deck import _parse_bold, _alpha, prompt_box, prompts_markdown, PROMPTS
from lxml import etree

IMG = "/tmp/hof/img/"
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


def pic(s, f, x, y, w, h, nm=None):
    p = image(s, IMG + f, x, y, w, h)
    if nm: name(p, nm)
    return p


def ppic(s, x, y, w, h, prompt, titulo, alerta=None, dark=False, nm=None, estilo=True):
    b = prompt_box(s, x, y, w, h, prompt, titulo, alerta, dark, estilo)
    if nm: b.name = nm
    return b


ANAT = "Anatomia gerada por IA pode errar trajetos e inserções: confira com atlas antes de usar."

# ---------------------------------------------------------------- slides
def s_capa(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    s.shapes.add_picture(A("fundo_foto.jpg"), 0, 0, Inches(W), Inches(H))
    r = rect(s, 0, 0, W, H, fill=NOITE); _alpha(r, 0.45); name(r, "!!fundo")
    big_arc(s, -3.6, 2.9, 7.0, VINHO, 0.62, 270, 360)
    logo(s, True, M, 0.4, 0.55)
    an.add(kicker(s, "Curso de Harmonização Facial", M, 1.75))
    an.add(title(s, "TOXINA +", M, 2.0, 7, 0.9, size=50), eff="up", gap=150)
    an.add(title(s, "PREENCHEDORES", M, 2.75, 8, 0.9, size=50, color=ROSE), eff="up", gap=250)
    bar(s, M, 3.85, 0.7)
    an.add(text(s, M, 3.98, 4, 0.35, "Módulo 1", size=13, color=BRANCO))
    morph(s); an.build()


def s_sumario(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, CREME)
    p = name(rect(s, 0, 0, 3.4, H, fill=NOITE), "!!painel")
    big_arc(s, -2.2, H - 1.4, 4.2, VINHO, 0.42, 270, 360)
    logo(s, True, M, 0.4, 0.42)
    text(s, M, 1.25, 2.8, 0.25, "Conteúdo programático", size=8.5, color=ROSE, bold=True, caps=True)
    an.add(text(s, M, 1.5, 2.8, 1.2, "12", size=88, color=BRANCO, font=FONTE_FORTE, bold=True), eff="up")
    an.add(text(s, M, 2.85, 2.6, 0.5, "temas em 2 dias de imersão", size=12, color=BRANCO))
    text(s, M, 3.45, 2.7, 0.8, [[("Dia 1 ", {"bold": True, "color": ROSE}), ("teórico", {})],
                                 [("Dia 2 ", {"bold": True, "color": ROSE}), ("prático · 9h–17h", {})]], size=9.5, color=CINZA_CLARO)
    itens = ["Fisiopatologia do envelhecimento", "Anatomia e áreas de risco", "Mecanismo de ação",
             "Prescrição que prolonga a toxina", "Imunogenicidade", "Marcas comerciais",
             "Tendência: Relfydess", "Reações adversas e manejo", "Reticulação dos materiais",
             "Reconstituição e armazenamento", "Preenchimento com cânula", "Técnicas anestésicas"]
    for i, t in enumerate(itens):
        col, row = divmod(i, 6); x = 3.85 + col * 3.0; y = 0.75 + row * 0.7
        a = text(s, x, y, 0.6, 0.5, f"{i+1:02d}", size=20, color=ROSE, font=FONTE_FORTE, bold=True)
        b = text(s, x + 0.62, y + 0.06, 2.2, 0.5, t, size=10, color=PRETO, bold=False)
        an.add(a, gap=0); an.add(b, gap=90)
    morph(s); an.build()


def s_divisoria(prs, num, word, sub):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, VINHO)
    big_arc(s, W - 6.4, -2.6, 9.0, VINHO_ESC, 0.9, 90, 180)
    small_arc(s, W - 2.2, H - 1.8, 2.6, ROSE, 0.22, 180, 270)
    logo(s, True)
    t = text(s, M - 0.08, 0.7, 6, 2.6, num, size=190, color=ROSE, font=FONTE_FORTE, bold=True, spacing=0.8)
    an.add(t, eff="up", dur=700, gap=250)
    bar(s, M + 0.05, 3.55, 0.9, BRANCO)
    an.add(title(s, word, M, 3.7, 8, 0.8, size=40), eff="left", gap=200)
    an.add(text(s, M + 0.03, 4.45, 6, 0.4, sub, size=12, color=ROSE_CLARO))
    morph(s); an.build()


def s_frase(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, CREME)
    big_arc(s, -5.0, -5.0, 7.0, VINHO, 0.5, 0, 90)
    logo(s, False)
    text(s, M + 0.6, 0.55, 1.4, 1.4, "“", size=120, color=VINHO, font="Georgia")
    q = ("A harmonização facial é um conjunto de procedimentos que promove **equilíbrio entre as proporções** "
         "do rosto, valorizando características individuais com **naturalidade**.")
    an.add(text(s, M + 1.15, 1.5, 7.4, 2.0, _parse_bold(q), size=21, color=PRETO, font=FONTE, spacing=1.15), eff="up", dur=800, gap=500)
    chips = ["Minimamente invasivo", "Procedimento rápido", "Recuperação reduzida", "Mínimo de complicações"]
    x = M + 0.9
    for c in chips:
        w = 0.3 + 0.068 * len(c)
        r = rect(s, x, 3.85, w, 0.42, fill=None, line=VINHO, shape=MSO_SHAPE.ROUNDED_RECTANGLE, lw=1.25)
        r.adjustments[0] = 0.5
        t = text(s, x, 3.85, w, 0.42, c, size=8, color=VINHO, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        an.add(r, gap=0); an.add(t, gap=150); x += w + 0.15
    morph(s); an.build()


def s_pilares(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, NOITE)
    ppic(s, 0.25, 0.25, 3.8, H - 1.35, "Retrato editorial de estúdio de duas mulheres lado a lado, a da esquerda com cerca de 25 anos e a da direita com cerca de 60 anos, mesmo enquadramento frontal do rosto e pescoço, expressão neutra. Sobre cada rosto, um triângulo de linhas finas: na jovem com a base larga nas maçãs do rosto e a ponta no queixo (triângulo da juventude); na madura invertido, com a base larga na mandíbula. Fotografia realista, pele natural sem retoque excessivo, iluminação suave e uniforme, fundo neutro escuro quente", "Os 3 pilares do envelhecimento", dark=True, nm="!!foto", estilo="foto")
    r = rect(s, 0, H - 1.0, 4.3, 1.0, fill=NOITE); _alpha(r, 0.6)
    text(s, M, H - 0.85, 3.6, 0.7, [[("Intrínseco ", {"bold": True, "color": ROSE}), ("cronológico", {})],
                                    [("Extrínseco ", {"bold": True, "color": ROSE}), ("fotoenvelhecimento", {})]], size=9, color=BRANCO)
    logo(s, True)
    kicker(s, "Envelhecimento", 4.75, 0.55)
    an.add(title(s, "Os 3 pilares do envelhecimento", 4.75, 0.8, 4.6, 1.0, size=24, hl="3 pilares"), eff="up")
    pil = [("Osso", "Remodelação esquelética: a estrutura de suporte recua."),
           ("Gordura", "Perda e deslocamento dos coxins de gordura."),
           ("Pele", "Menos tonicidade e elasticidade.")]
    for i, (h, t) in enumerate(pil):
        y = 2.0 + i * 0.95
        n = text(s, 4.75, y - 0.1, 1.0, 0.9, f"{i+1:02d}", size=36, color=VINHO, font=FONTE_FORTE, bold=True)
        a = text(s, 5.75, y, 3.7, 0.3, h, size=13, color=BRANCO, bold=True, caps=True)
        b = text(s, 5.75, y + 0.32, 3.7, 0.5, t, size=9.5, color=CINZA_CLARO)
        l = line(s, 4.8, y + 0.85, W - M, y + 0.85, color=NOITE2, w=0.75)
        an.add(n, gap=0, eff="up"); an.add(a, gap=60); an.add(b, gap=200)
    text(s, 4.75, H - 0.4, 4.8, 0.25, "Swift A, et al. The Facial Aging Process from the “Inside Out”. Aesthet Surg J. 2021;41(10):1107-19.", size=6.5, color=CINZA)
    morph(s); an.build()


def s_vetor(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, CREME)
    ppic(s, W - 3.1, 0.25, 2.85, H - 0.5, "Retrato em perfil três quartos de uma mulher de cerca de 60 anos, olhos fechados, expressão serena, enquadramento da testa ao pescoço. Setas finas e translúcidas em vinho descendo suavemente sobre a face (sobrancelha, maçã do rosto, sulco nasogeniano, mandíbula), indicando o vetor de envelhecimento de cima para baixo. Sobreposição gráfica minimalista", "Vetor de envelhecimento", nm="!!foto", estilo="foto")
    logo(s, False, M, 0.4)
    kicker(s, "Vetor de envelhecimento", M, 1.3, VINHO)
    an.add(title(s, "De cima\npara baixo.", M, 1.6, 5.4, 1.8, color=PRETO, size=46, hl="baixo.", hlc=VINHO), eff="up", dur=700, gap=400)
    # seta vertical animada
    ln = line(s, 5.75, 1.0, 5.75, 4.6, color=VINHO, w=2.5)
    tri = rect(s, 5.62, 4.55, 0.26, 0.22, fill=VINHO, shape=MSO_SHAPE.ISOSCELES_TRIANGLE); tri.rotation = 180
    an.add(ln, gap=0, eff="fade", dur=900); an.add(tri, gap=300)
    an.add(text(s, M, 3.55, 5.0, 1.2,
                _parse_bold("As alterações começam nos **compartimentos superiores** e repercutem nas regiões inferiores. "
                            "O planejamento segue a mesma direção."), size=11, color=TEXTO), eff="up")
    morph(s); an.build()


def s_mecanismo(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, CREME)
    name(rect(s, 0, 0, W, 0.08, fill=VINHO), "!!painel")
    logo(s, False)
    kicker(s, "Toxina botulínica", M, 0.42, VINHO)
    title(s, "Mecanismo de ação", M, 0.62, 6, 0.6, color=PRETO, size=26, hl="ação", hlc=VINHO)
    p = ppic(s, 4.35, 1.35, 5.2, 3.0, "Ilustração científica 3D da junção neuromuscular em dois painéis lado a lado. Painel esquerdo: terminal nervoso liberando vesículas de acetilcolina na fenda sináptica sobre a fibra muscular. Painel direito: a mesma junção com moléculas de toxina botulínica ligadas ao terminal e as vesículas bloqueadas, sem liberação. Corte em seção transversal, cores limpas, visual de livro de fisiologia moderno", "Mecanismo de ação", alerta="Diagrama científico: confira se a sequência das etapas está correta.", nm="!!foto")
    an.add(p, gap=300, dur=700)
    steps = [("Local", "terminações pré-sinápticas, junção neuromuscular"),
             ("Internalização", "liga-se ao terminal e entra no neurônio"),
             ("Ação proteolítica", "cadeia leve cliva o complexo **SNARE**"),
             ("Efeito", "menos acetilcolina → relaxamento temporário"),
             ("Recuperação", "novas conexões restabelecem a função")]
    line(s, M + 0.14, 1.55, M + 0.14, 1.55 + 0.68 * 4, color=ROSE, w=1.5)
    for i, (h, t) in enumerate(steps):
        y = 1.38 + i * 0.68
        c = rect(s, M, y + 0.03, 0.28, 0.28, fill=VINHO, line=CREME, shape=MSO_SHAPE.OVAL, lw=2)
        a = text(s, M + 0.45, y, 3.4, 0.6, [[(h, {"bold": True, "color": PRETO, "size": 10.5})], _parse_bold(t)], size=8.5)
        an.add(c, gap=0); an.add(a, gap=220, eff="left")
    text(s, 4.35, 4.45, 5.2, 0.4, "O efeito é **reversível**: dura enquanto a terminação nervosa se regenera.".replace("**", ""), size=8.5, color=CINZA, italic=True)
    morph(s); an.build()


def s_numero(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, NOITE)
    big_arc(s, 2.2, -0.7, 7.0, VINHO, 0.55, 180, 360)
    logo(s, True)
    kicker(s, "Duração e efeitos", M, 0.55)
    an.add(text(s, 0, 1.55, W, 1.8, "3–4", size=130, color=BRANCO, font=FONTE_FORTE, bold=True, align=PP_ALIGN.CENTER, spacing=0.8), eff="up", dur=800, gap=300)
    an.add(text(s, 0, 3.25, W, 0.5, "MESES DE EFEITO, EM BULA", size=16, color=ROSE, bold=True, align=PP_ALIGN.CENTER), gap=400)
    an.add(text(s, 2.0, 3.9, 6, 0.8, "A duração varia entre sorotipos, refletindo a meia-vida intracelular da cadeia leve.",
                size=10, color=CINZA_CLARO, align=PP_ALIGN.CENTER))
    morph(s); an.build()


def s_contra(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, CREME)
    name(rect(s, 0, 0, W / 2, H, fill=VINHO), "!!painel")
    small_arc(s, -1.0, H - 1.6, 2.4, VINHO_ESC, 0.25, 270, 360)
    logo(s, False)
    title(s, "Contraindicações", M, 0.45, 4.5, 0.6, size=24)
    for k, (lab, items, fg, sub) in enumerate([
        ("Absolutas", ["Hipersensibilidade à TBA ou componentes", "Gestantes", "Quadro psicológico: expectativas irreais, instabilidade"], BRANCO, ROSE_CLARO),
        ("Relativas", ["Doenças neuromusculares", "Doença autoimune", "Antibióticos (aminoglicosídeos)", "Vacinas recentes (COVID, gripe, HPV)"], PRETO, TEXTO)]):
        x = M + k * (W / 2)
        an.add(text(s, x, 1.3, 4, 0.5, lab.upper(), size=20, color=fg if k == 0 else VINHO, font=FONTE_FORTE, bold=True), eff="up", gap=200)
        for i, it in enumerate(items):
            y = 2.0 + i * 0.62
            mk = text(s, x, y, 0.4, 0.4, "✕" if k == 0 else "!", size=13, color=ROSE if k == 0 else VINHO, bold=True)
            t = text(s, x + 0.42, y + 0.02, 3.9, 0.55, it, size=11, color=sub)
            an.add(mk, gap=0); an.add(t, gap=150, eff="left")
    text(s, M, H - 0.55, 4.2, 0.4, "*Lactantes: dados atuais não mostram contraindicação.", size=7.5, color=ROSE_CLARO, italic=True)
    morph(s); an.build()


def s_glabela(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, BRANCO)
    ppic(s, 0.25, 0.25, 3.35, H - 0.5, "Ilustração anatômica 3D frontal do terço superior da face feminina, pele removida, mostrando a musculatura: músculo prócero na raiz do nariz e músculos corrugadores do supercílio acima das sobrancelhas, destacados em vinho; demais músculos em tom rosado mais suave. Enquadramento da testa até a ponta do nariz, simetria perfeita", "Glabela · planejamento", alerta=ANAT, nm="!!foto")
    logo(s, False)
    kicker(s, "Planejamento", 4.0, 0.42, VINHO)
    title(s, "Glabela", 4.0, 0.62, 5, 0.7, color=PRETO, size=32)
    text(s, 4.0, 1.28, 5, 0.3, [[("M. Prócero", {"bold": True, "color": VINHO}), ("  ·  ", {}), ("M. Corrugadores do supercílio", {"bold": True, "color": VINHO})]], size=9)
    steps = ["Um ponto em cada corrugador, no início da sobrancelha", "Um ponto central no prócero",
             "Pinçar a pele", "Agulha a 90°"]
    for i, t in enumerate(steps):
        y = 1.8 + i * 0.52
        n = text(s, 4.0, y, 0.5, 0.45, f"{i+1}", size=18, color=ROSE, font=FONTE_FORTE, bold=True)
        b = text(s, 4.45, y + 0.06, 3.1, 0.45, t, size=10, color=TEXTO)
        an.add(n, gap=0); an.add(b, gap=160, eff="left")
    k = name(rect(s, 7.65, 1.8, 1.9, 2.0, fill=VINHO), "!!kpi")
    a = text(s, 7.65, 2.0, 1.9, 0.9, "2–5", size=40, color=BRANCO, font=FONTE_FORTE, bold=True, align=PP_ALIGN.CENTER)
    b = text(s, 7.75, 2.9, 1.7, 0.7, "UI de toxina por ponto", size=9.5, color=ROSE_CLARO, align=PP_ALIGN.CENTER)
    an.add(k, gap=0, eff="up"); an.add(a, gap=0, eff="up"); an.add(b, gap=200)
    morph(s); an.build()


def s_agulha(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, NOITE)
    ppic(s, 0.25, 0.2, W - 1.55, 2.5, "Ilustração médica 3D em corte transversal da pele em camadas (epiderme, derme e gordura subcutânea) com um vaso sanguíneo na derme. À esquerda, agulha fina perfurando o vaso, com pequeno ponto de sangramento. À direita, cânula de ponta romba desviando suavemente do mesmo vaso. Composição dividida ao meio", "Agulha ou cânula", dark=True, nm="!!foto")
    logo(s, True)
    title(s, "Agulha ou cânula?", M, 2.85, 6, 0.6, size=24, hl="cânula?")
    cols = [("Agulha", ["Traumatiza o vaso: **aspire 10–20 s**", "Permite superficializar (contorno labial)", "Exige mais prática"]),
            ("Cânula", ["Ponta romba: **desvia do vaso**", "Precisa de pertuito prévio", "Menos dor, mais segura em áreas críticas"])]
    for k, (h, its) in enumerate(cols):
        x = M + k * 4.6
        an.add(text(s, x, 3.45, 4, 0.3, h.upper(), size=11, color=ROSE, bold=True), gap=100)
        for i, it in enumerate(its):
            segs = [(p, {"bold": True, "color": BRANCO} if j % 2 else {}) for j, p in enumerate(it.split("**")) if p]
            an.add(text(s, x, 3.78 + i * 0.3, 4.3, 0.3, [segs], size=9.5, color=CINZA_CLARO), gap=90, eff="left")
    r = rect(s, 0, H - 0.42, W, 0.42, fill=VINHO)
    t = text(s, M, H - 0.42, W - 2 * M, 0.42, [[("ATENÇÃO  ", {"bold": True, "color": ROSE_CLARO}),
             ("Cânulas finas podem agir como agulha. Mais segura: 22G × 50 mm ou 22G × 70 mm.", {})]], size=9.5,
             color=BRANCO, anchor=MSO_ANCHOR.MIDDLE)
    an.add(r, gap=0); an.add(t, gap=0)
    morph(s); an.build()


def s_alerta(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, NOITE)
    name(rect(s, 0, 0, 0.12, H, fill=ALERTA), "!!painel")
    ppic(s, W - 3.25, 0.55, 2.85, 4.5, "Ilustração médica 3D em dois quadros empilhados, de um vaso sanguíneo em corte longitudinal. Quadro superior: gel de ácido hialurônico translúcido azulado dentro do vaso, obstruindo o fluxo (embolização). Quadro inferior: o gel fora do vaso, comprimindo-o por fora e estreitando a luz (compressão). Hemácias visíveis, foco nítido", "Reações de maior gravidade", alerta="Confira com o professor antes de usar em aula.", dark=True, nm="!!foto")
    logo(s, True, M + 0.1)
    an.add(text(s, M + 0.1, 1.05, 5, 0.3, "⚠  REAÇÕES DE MAIOR GRAVIDADE", size=10, color=ALERTA, bold=True))
    title(s, "Reconhecer cedo muda o desfecho.", M + 0.1, 1.35, 5.8, 1.0, size=24)
    its = [("Isquemia", "dor intensa, palidez, livedo, alteração de cor e temperatura"),
           ("Necrose", "isquemia persistente que compromete a viabilidade do tecido"),
           ("Infecção", "dor progressiva, calor, eritema em expansão, secreção")]
    for i, (h, t) in enumerate(its):
        y = 2.55 + i * 0.75
        n = rect(s, M + 0.1, y + 0.05, 0.08, 0.55, fill=ALERTA if i < 2 else ROSE)
        a = text(s, M + 0.35, y, 5.5, 0.7, [[(h.upper(), {"bold": True, "color": BRANCO, "size": 12})], [(t, {"color": CINZA_CLARO})]], size=9.5)
        an.add(n, gap=0); an.add(a, gap=250, eff="left")
    morph(s); an.build()


def s_hialuronidase(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    bg(s, CREME)
    big_arc(s, W - 2.0, -0.6, 4.0, ROSE, 0.4, 90, 180)
    logo(s, False)
    kicker(s, "Hialuronidase", M, 0.5, VINHO)
    an.add(title(s, "Tenha sempre\nno consultório.", M, 0.78, 6.2, 1.7, color=PRETO, size=38, hl="sempre", hlc=VINHO), eff="up", dur=700, gap=350)
    regras = [("2×", "o volume de AH aplicado, para remoção completa"),
              ("7 dias", "de intervalo, se precisar repetir"),
              ("6 h", "de meia-vida: descarte após reconstituir")]
    for i, (n, t) in enumerate(regras):
        x = M + i * 2.75
        a = text(s, x, 2.9, 2.6, 0.75, n, size=34, color=VINHO, font=FONTE_FORTE, bold=True)
        l = rect(s, x + 0.03, 3.68, 0.5, 0.04, fill=ROSE)
        b = text(s, x, 3.8, 2.4, 0.7, t, size=10, color=TEXTO)
        an.add(a, gap=0, eff="up"); an.add(l, gap=0); an.add(b, gap=250)
    text(s, M, H - 0.5, 7, 0.3, "Pó liofilizado: reconstituir com soro fisiológico estéril antes da aplicação.", size=8, color=CINZA, italic=True)
    morph(s); an.build()


def s_fim(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6]); an = Anim(s)
    s.shapes.add_picture(A("fundo_foto.jpg"), 0, 0, Inches(W), Inches(H))
    r = rect(s, 0, 0, W, H, fill=NOITE); _alpha(r, 0.45); name(r, "!!fundo")
    big_arc(s, W - 4.0, 1.3, 7.0, VINHO, 0.62, 180, 270)
    logo(s, True, M, 0.4, 0.55)
    an.add(title(s, "Obrigado.", M, 1.9, 6, 1.0, size=54), eff="up", dur=700, gap=300)
    bar(s, M, 3.0, 0.7)
    an.add(text(s, M, 3.15, 5, 0.5, "Continue sua evolução com a Clinic Cursos.", size=13, color=BRANCO))
    morph(s); an.build()


def s_from_layout(prs, d):
    """Usa os layouts padrão (custos, precificação, parcerias) com Morph +
    entrada suave do conteúdo."""
    import copy
    import clinic_deck as cd
    d = copy.deepcopy(d)
    for k in ("logo", "qr"):
        if isinstance(d.get(k), str): d[k] = A(d[k])
    for c in d.get("cards", []):
        c["icone"] = A(c["icone"]); c["qr"] = A(c["qr"])
    s = prs.slides.add_slide(prs.slide_layouts[6])
    n0 = len(s.shapes)
    cd.LAYOUTS[d["tipo"]](prs, s, d)
    an = Anim(s)
    for sh in list(s.shapes)[1:]:
        if sh.has_text_frame or sh.has_table or sh.shape_type == 13:
            an.add(sh, gap=40)
    morph(s); an.build()


HOF_PRECOS = {"tipo": "precificacao", "procedimentos": [
    {"nome": "Toxina botulínica 50 UI", "produto": 400, "preco": 1100, "custo_fixo": 28, "insumos": 40},
    {"nome": "Preenchimento 1 mL", "produto": 300, "preco": 1200, "custo_fixo": 28, "insumos": 40},
    {"nome": "Harmonização 4 mL + TBA", "estrategia": "Upsell", "produto": 1600, "preco": 5000, "custo_fixo": 28, "insumos": 40},
    {"nome": "Skinbooster (mescla)", "estrategia": "Downsell", "produto": 45, "preco": 300, "custo_fixo": 28, "insumos": 40},
    {"nome": "Bioestimulador (Sculptra)", "estrategia": "Cross-sell", "produto": 1000, "preco": 3500, "custo_fixo": 28, "insumos": 40}]}


def main(out):
    prs = Presentation(); prs.slide_width = Inches(W); prs.slide_height = Inches(H)
    s_capa(prs); s_sumario(prs)
    s_divisoria(prs, "01", "Introdução", "Envelhecimento facial e diagnóstico")
    s_frase(prs); s_pilares(prs); s_vetor(prs)
    s_divisoria(prs, "02", "Toxina botulínica", "Mecanismo, duração e planejamento")
    s_mecanismo(prs); s_numero(prs); s_contra(prs); s_glabela(prs)
    s_divisoria(prs, "03", "Preenchedores AH", "Materiais, técnica e intercorrências")
    s_agulha(prs); s_alerta(prs); s_hialuronidase(prs)
    import clinic_deck as cd
    s_divisoria(prs, "04", "Marketing e precificação", "Custos, preço justo e técnicas de venda")
    s_from_layout(prs, {"tipo": "custos"})
    s_from_layout(prs, HOF_PRECOS)
    for d in cd.PARCERIAS_PADRAO:
        s_from_layout(prs, d)
    s_fim(prs)
    prs.save(out); print("ok", out)
    open(os.path.splitext(out)[0] + " - prompts de imagem.md", "w", encoding="utf-8").write(prompts_markdown("HOF básico (exploração ousada)"))


if __name__ == "__main__":
    main(sys.argv[1])
