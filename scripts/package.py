"""Validate skills and sync the shared parts into them."""
import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDFCHECK_SKILLS = ("diagramador", "imagens", "auditor-grafico")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, str] = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            key, val = m.group(1), m.group(2).strip()
            data[key] = "" if val in (">", "|", ">-", "|-") else val.strip("\"'")
        elif key and line.strip():
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def check_skill(skill: Path) -> list[str]:
    errs = []
    md = (skill / "SKILL.md").read_text(encoding="utf-8")
    fm = parse_frontmatter(md)
    name, desc = fm.get("name", ""), fm.get("description", "")
    tag = f"skills/{skill.name}"
    if not (1 <= len(name) <= 64 and NAME_RE.match(name)):
        errs.append(f"{tag}: invalid name '{name}' (1-64 chars, [a-z0-9-], no leading, trailing or double hyphen)")
    if name != skill.name:
        errs.append(f"{tag}: name '{name}' differs from folder name")
    if re.search(r"claude|anthropic", name):
        errs.append(f"{tag}: name must not contain 'claude' or 'anthropic'")
    if not 1 <= len(desc) <= 1024:
        errs.append(f"{tag}: description has {len(desc)} chars (1-1024)")
    n = len(md.splitlines())
    if n >= 500:
        errs.append(f"{tag}: SKILL.md has {n} lines (limit 499)")
    return errs


def compare_tree(src: Path, dst: Path, label: str) -> list[str]:
    errs = []
    for f in sorted(p for p in src.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"):
        copy = dst / f.relative_to(src)
        if not copy.is_file() or not filecmp.cmp(f, copy, shallow=False):
            errs.append(f"{label}: {copy} differs from {f} (run --sync)")
    return errs


def common_sources(root: Path):
    """(source dir, relative destination inside the skill) pairs that exist."""
    return [
        (root / "shared" / "references", Path("references/comum")),
        (root / "shared" / "rules", Path("references/comum")),
    ]


def check(root: Path) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    if (root / "bin").exists():
        errs.append("bin/ at repository top is not allowed")
    skills_dir = root / "skills"
    for skill in sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []:
        if not (skill / "SKILL.md").is_file():
            warns.append(f"skills/{skill.name}: no SKILL.md, skipped")
            continue
        errs += check_skill(skill)
        if skill.name in PDFCHECK_SKILLS and (root / "lib" / "pdfcheck").is_dir():
            errs += compare_tree(root / "lib" / "pdfcheck", skill / "scripts" / "pdfcheck", f"skills/{skill.name}")
        for src, rel in common_sources(root):
            if src.is_dir():
                errs += compare_tree(src, skill / rel, f"skills/{skill.name}")
    return errs, warns


def sync(root: Path) -> None:
    skills_dir = root / "skills"
    for skill in sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []:
        if not (skill / "SKILL.md").is_file():
            continue
        pairs = [(src, skill / rel) for src, rel in common_sources(root) if src.is_dir()]
        if skill.name in PDFCHECK_SKILLS and (root / "lib" / "pdfcheck").is_dir():
            pairs.append((root / "lib" / "pdfcheck", skill / "scripts" / "pdfcheck"))
        for src, dst in pairs:
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=IGNORE)


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--sync", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 2
    if args.sync:
        sync(root)
        return 0
    errs, warns = check(root)
    for w in warns:
        print(f"warning: {w}")
    for e in errs:
        print(f"error: {e}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
