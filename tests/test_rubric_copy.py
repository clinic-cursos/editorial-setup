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


def test_copy_lists_official_disqualifiers():
    text = OFFICIAL.read_text(encoding="utf-8")
    items = [l[2:].strip().rstrip(".") for l in text.split("## Eliminatórios")[1].split("##")[0].splitlines() if l.startswith("- ")]
    copy = COPY.read_text(encoding="utf-8").lower()
    assert items and all(i.lower() in copy for i in items)
