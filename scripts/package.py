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


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Return the fields, or None when the closing '---' is missing."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    data: dict[str, str] = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            return data
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("#") or val in (">", "|", ">-", "|-", "null", "Null", "NULL", "~", '""', "''"):
                val = ""
            data[key] = val.strip("\"'")
        elif key and line.strip() and not line.strip().startswith("#"):
            data[key] = (data[key] + " " + line.strip()).strip()
    return None


def check_skill(skill: Path) -> list[str]:
    errs = []
    md = (skill / "SKILL.md").read_text(encoding="utf-8")
    fm = parse_frontmatter(md)
    if fm is None:
        return [f"skills/{skill.name}: SKILL.md frontmatter missing or not closed with '---'"]
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


def tree_files(root: Path) -> set[Path]:
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def targets(root: Path, skill: Path) -> dict[Path, list[Path]]:
    """Copy destination inside the skill -> source dirs that feed it."""
    out: dict[Path, list[Path]] = {}
    if skill.name in PDFCHECK_SKILLS and (root / "lib" / "pdfcheck").is_dir():
        out[skill / "scripts" / "pdfcheck"] = [root / "lib" / "pdfcheck"]
    common = [root / "shared" / d for d in ("references", "rules") if (root / "shared" / d).is_dir()]
    if common:
        out[skill / "references" / "comum"] = common
    return out


def compare(dst: Path, srcs: list[Path], label: str) -> list[str]:
    errs, expected = [], set()
    for src in srcs:
        for rel in sorted(tree_files(src)):
            expected.add(rel)
            copy = dst / rel
            if not copy.is_file() or not filecmp.cmp(src / rel, copy, shallow=False):
                errs.append(f"{label}: {copy} differs from {src / rel} (run --sync)")
    for rel in sorted(tree_files(dst) - expected if dst.is_dir() else set()):
        errs.append(f"{label}: {dst / rel} has no source (run --sync)")
    return errs


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
        for dst, srcs in targets(root, skill).items():
            errs += compare(dst, srcs, f"skills/{skill.name}")
    return errs, warns


def sync(root: Path) -> None:
    skills_dir = root / "skills"
    for skill in sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []:
        if not (skill / "SKILL.md").is_file():
            continue
        for dst, srcs in targets(root, skill).items():
            for src in srcs:
                shutil.copytree(src, dst, dirs_exist_ok=True, ignore=IGNORE)
            expected = set().union(*(tree_files(src) for src in srcs))
            for rel in tree_files(dst) - expected:
                (dst / rel).unlink()


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
