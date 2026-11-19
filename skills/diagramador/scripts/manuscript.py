"""Leia o manuscrito na convenção de shared/references/manuscrito.md (e só nela)."""

from dataclasses import dataclass, field
from pathlib import PurePosixPath
import re

BOXES = ("ponto-chave", "atencao", "evidencia", "estudo-pratica", "aprofundamento", "aplicacao-clinica", "faq")
META_KEYS = ("title", "course", "authors", "version")

_HEADING = re.compile(r"(#{1,3}) (\S.*)")
_BULLET = re.compile(r"- (\S.*)")
_NUMBERED = re.compile(r"\d+\. (\S.*)")
_SLIDE = re.compile(r"<!-- slide: (\d+) -->")
_FIGURE = re.compile(r"!\[(.*)\]\((\S+)\)\{#(fig-[A-Za-z0-9_-]+)\}")
_ENTRY = re.compile(r"- \[@([\w:.-]+)\] (\S.*)")
_CITATION = re.compile(r"\[@([\w:.-]+)\]")


class ManuscriptError(ValueError):
    """Manuscrito fora da convenção; a mensagem diz a linha e o que corrigir."""


@dataclass
class Block:
    id: str
    type: str  # heading, paragraph, list, box, figure, references
    text: str = ""  # título, parágrafo ou legenda
    level: int = 0
    ordered: bool = False
    items: list[str] = field(default_factory=list)  # itens da lista
    kind: str = ""  # tipo da caixa editorial
    children: list["Block"] = field(default_factory=list)  # conteúdo da caixa
    src: str = ""
    fig_id: str = ""
    entries: list[tuple[str, str]] = field(default_factory=list)  # (chave, dados) ou, no faq, (pergunta, resposta)
    slide: int | None = None  # slide de origem


@dataclass
class Manuscript:
    meta: dict[str, str]
    blocks: list[Block]
    refs: dict[str, str] = field(default_factory=dict)  # chave -> dados bibliográficos


def _error(number: int, message: str):
    return ManuscriptError(f"linha {number}: {message}")


def _meta(lines: list[str]) -> tuple[dict[str, str], int]:
    meta = {}
    number = 0
    for number, line in enumerate(lines, 1):
        if not line.strip():
            break
        key, sep, value = line.partition(":")
        if not sep or key not in META_KEYS or not value.strip():
            raise _error(number, f"metadado inválido {line!r}; use title, course, authors e version, um por linha")
        meta[key] = value.strip()
    missing = [k for k in META_KEYS if k not in meta]
    if missing:
        raise ManuscriptError("faltam metadados no início do manuscrito: " + ", ".join(missing))
    return meta, number


def _faq(lines, first_number) -> list[tuple[str, str]]:
    """Linha que termina em '?' é pergunta; as linhas seguintes, até a próxima pergunta, são a resposta."""
    pairs: list[list[str]] = []
    for offset, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue
        if line.endswith("?"):
            pairs.append([line, ""])
        elif pairs:
            pairs[-1][1] = f"{pairs[-1][1]} {line}".strip()
        else:
            raise _error(first_number + offset, "o :::faq começa por uma pergunta (linha terminada em '?')")
    return [(q, a) for q, a in pairs]


def _starts_block(line: str) -> bool:
    return bool(
        line.startswith(("#", ":::", "<!--", "!["))
        or _BULLET.fullmatch(line)
        or _NUMBERED.fullmatch(line)
    )


def _parse_blocks(lines, first_number, counter, *, inside_box=False) -> list[Block]:
    blocks: list[Block] = []
    slide = None
    in_references = False

    def new(**kw):
        nonlocal slide
        counter[0] += 1
        block = Block(id=f"b{counter[0]:04d}", slide=slide, **kw)
        slide = None
        blocks.append(block)
        return block

    i = 0
    while i < len(lines):
        line, number = lines[i].rstrip(), first_number + i
        i += 1
        if not line.strip():
            continue
        if in_references:
            entry = _ENTRY.fullmatch(line)
            if not entry:
                raise _error(number, "use '- [@chave] Dados bibliográficos' em cada entrada de Referências")
            blocks[-1].entries.append((entry[1], entry[2]))
        elif m := _SLIDE.fullmatch(line):
            slide = int(m[1])
        elif line.startswith("<!--"):
            raise _error(number, "comentário desconhecido; só <!-- slide: N --> é aceito")
        elif line.startswith(":::"):
            name = line[3:]
            if inside_box or name not in BOXES:
                raise _error(number, f"bloco {line!r} desconhecido ou aninhado; use {', '.join(':::' + b for b in BOXES)}")
            end = next((j for j in range(i, len(lines)) if lines[j].strip() == ":::"), None)
            if end is None:
                raise _error(number, f"bloco {line!r} sem ':::' de fechamento")
            box = new(type="box", kind=name)
            if name == "faq":
                box.entries = _faq(lines[i:end], first_number + i)
            else:
                box.children = _parse_blocks(lines[i:end], first_number + i, counter, inside_box=True)
            i = end + 1
        elif m := _HEADING.fullmatch(line):
            new(type="heading", level=len(m[1]), text=m[2].strip())
            if not inside_box and len(m[1]) == 2 and m[2].strip() == "Referências":
                new(type="references")
                in_references = True
        elif line.startswith("#"):
            raise _error(number, "título inválido; use de # a ### seguido de espaço e texto")
        elif line.startswith("!["):
            m = _FIGURE.fullmatch(line)
            if not m:
                raise _error(number, "figura inválida; use ![legenda](arquivo){#fig-id}")
            src = PurePosixPath(m[2])
            if src.is_absolute() or ".." in src.parts or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", m[2]):
                raise _error(number, f"caminho de figura {m[2]!r} deve ser relativo e ficar dentro da pasta do manuscrito")
            new(type="figure", text=m[1], src=m[2], fig_id=m[3])
        elif _BULLET.fullmatch(line) or _NUMBERED.fullmatch(line):
            ordered = bool(_NUMBERED.fullmatch(line))
            pattern = _NUMBERED if ordered else _BULLET
            items = [pattern.fullmatch(line)[1]]
            while i < len(lines) and (m := pattern.fullmatch(lines[i].rstrip())):
                items.append(m[1])
                i += 1
            new(type="list", ordered=ordered, items=items)
        else:
            parts = [line.strip()]
            while i < len(lines) and lines[i].strip() and not _starts_block(lines[i].rstrip()):
                parts.append(lines[i].strip())
                i += 1
            new(type="paragraph", text=" ".join(parts))
    return blocks


def _texts(block: Block):
    yield block.text
    yield from block.items
    yield from (data for _, data in block.entries)
    if block.kind == "faq":
        yield from (question for question, _ in block.entries)


def walk(blocks):
    for block in blocks:
        yield block
        yield from walk(block.children)


def parse(text: str) -> Manuscript:
    lines = text.splitlines()
    meta, last = _meta(lines)
    blocks = _parse_blocks(lines[last:], last + 1, [0])
    keys = [k for b in blocks if b.type == "references" for k, _ in b.entries]
    figures = [b.fig_id for b in walk(blocks) if b.type == "figure"]
    for fig in {f for f in figures if figures.count(f) > 1}:
        raise ManuscriptError(f"identificador de figura repetido: {fig}")
    for block in walk(blocks):
        for cited in (c for t in _texts(block) for c in _CITATION.findall(t)):
            if cited not in keys:
                raise ManuscriptError(f"citação [@{cited}] sem entrada em '## Referências'")
    refs = {k: d for b in blocks if b.type == "references" for k, d in b.entries}
    return Manuscript(meta, blocks, refs)


def cite(text: str, refs: dict[str, str]) -> str:
    """Troque cada [@chave] pela citação autor-data da ABNT, ex.: (SILVA, 2024)."""

    def one(m):
        data = refs[m[1]]
        years = re.findall(r"\b(?:1[5-9]|20)\d\d\b", data)
        return f"({re.split(r'[,.;]', data)[0].strip()}, {years[-1] if years else 's.d.'})"

    return _CITATION.sub(one, text)
