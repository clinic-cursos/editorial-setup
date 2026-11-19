from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "skills/editor-chefe/references/rubricas/fase-1-ampliacao.md"
COPY = ROOT / "skills/auditor-cientifico/references/relatorio.md"


def rows(path, header):
    """Critério, Peso e O que conta de cada linha da tabela que começa em `header`."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(header))
    out = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        out.append(tuple(c.strip() for c in line.strip("|").split("|"))[:3])
    return out


def test_rubric_copy_matches_official():
    official = rows(OFFICIAL, "| Critério | Peso | O que conta |")
    assert len(official) == 5
    assert rows(COPY, "| Critério | Peso | O que conta |") == official


def official_disqualifiers(text):
    section = text.split("## Eliminatórios")[1].split("\n## ")[0]
    return {l[2:].strip().rstrip(".") for l in section.splitlines() if l.startswith("- ")}


def copy_disqualifiers(text):
    """Nome -> valor de 'Avaliado' na tabela de eliminatórios da cópia."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("| Eliminatório | Avaliado"))
    cells = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        cells.append([c.strip() for c in line.strip("|").split("|")])
    return {c[0]: c[1] for c in cells}, len(cells)


def check_disqualifiers(official_text, copy_text):
    copy, count = copy_disqualifiers(copy_text)
    assert count == len(copy), "eliminatório repetido na cópia"
    assert set(copy) == official_disqualifiers(official_text)
    assert set(copy.values()) == {"sim"}


def test_copy_disqualifiers_match_official():
    check_disqualifiers(OFFICIAL.read_text(encoding="utf-8"), COPY.read_text(encoding="utf-8"))


def test_disqualifier_check_catches_drift():
    official, copy = OFFICIAL.read_text(encoding="utf-8"), COPY.read_text(encoding="utf-8")
    for bad in (
        copy.replace("| Divergência com o Board não sinalizada | sim |", "| Divergência com o Board não sinalizada | não |"),
        copy.replace("| Divergência com o Board não sinalizada | sim | |", "| Divergência com o Board não sinalizada | sim | |\n| Eliminatório falso | sim | |"),
    ):
        assert bad != copy
        try:
            check_disqualifiers(official, bad)
        except AssertionError:
            continue
        raise AssertionError("a deriva passou despercebida")
