"""Validate, sync, and package the editorial skills and agents."""
import argparse
import filecmp
import json
import re
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
PDFCHECK_SKILLS = ("diagramador", "imagens", "auditor-grafico")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")
REFERENCE_PATH = re.compile(
    r"(?<![\w./-])(?P<quote>`?)(?:(?P<skill>[a-z0-9-]+)/)?"
    r"(?P<path>references/(?:[\w.-]+/)*(?:[\w.-]*[\w-])?)(?P=quote)"
)


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
    """Copy destination inside the skill -> source dirs that feed it (empty when the source is gone)."""
    out: dict[Path, list[Path]] = {}
    if skill.name in PDFCHECK_SKILLS:
        src = root / "lib" / "pdfcheck"
        out[skill / "scripts" / "pdfcheck"] = [src] if src.is_dir() else []
    common = [root / "shared" / d for d in ("references", "rules")]
    out[skill / "references" / "comum"] = [d for d in common if d.is_dir()]
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
            for d in sorted((p for p in dst.rglob("*") if p.is_dir()), reverse=True):
                if not any(d.iterdir()):
                    d.rmdir()


def read_manifest(root: Path, relative_path: str) -> dict:
    try:
        manifest = json.loads((root / relative_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"{relative_path}: {error}") from error
    if not isinstance(manifest, dict):
        raise ValueError(f"{relative_path}: expected a JSON object")
    return manifest


def check_manifests(root: Path, agents: list[Path]) -> None:
    claude = read_manifest(root, ".claude-plugin/plugin.json")
    marketplace = read_manifest(root, ".claude-plugin/marketplace.json")
    codex = read_manifest(root, ".codex-plugin/plugin.json")
    for platform, manifest in (("claude", claude), ("codex", codex)):
        if manifest.get("name") != "clinic-editorial" or any(
            not isinstance(manifest.get(key), str) or not manifest[key].strip()
            for key in ("version", "description")
        ):
            raise ValueError(f".{platform}-plugin/plugin.json: invalid plugin metadata")
    if claude["version"] != codex["version"]:
        raise ValueError("Claude and Codex plugin versions differ")
    agent_paths = sorted(f"./{path.relative_to(root).as_posix()}" for path in agents)
    listed_agents = claude.get("agents")
    if not isinstance(listed_agents, list) or sorted(listed_agents, key=str) != agent_paths:
        raise ValueError(".claude-plugin/plugin.json: agents must match agents/editorial/")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not any(
        isinstance(plugin, dict)
        and plugin.get("name") == claude["name"]
        and plugin.get("source") == "./"
        for plugin in plugins
    ):
        raise ValueError(".claude-plugin/marketplace.json: clinic-editorial must point to ./")
    if codex.get("skills") != "./skills/":
        raise ValueError(".codex-plugin/plugin.json: skills must point to ./skills/")


def codex_agent(source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    if not fields or fields.get("name") != source.stem or not fields.get("description"):
        raise ValueError(f"{source}: expected matching name and nonempty description")
    _, _, body = re.split(r"(?m)^[ \t]*---[ \t]*$", text, maxsplit=2)
    fields = {
        "name": fields["name"],
        "description": fields["description"],
        "developer_instructions": body.lstrip("\n"),
    }
    if not body.strip():
        raise ValueError(f"{source}: missing agent instructions")
    if source.stem == "revisor-aulas":
        fields.update(model="gpt-6.2-sol", sandbox_mode="read-only")
    # JSON string escapes also work in TOML basic strings. Escape DEL for TOML.
    return "".join(
        f"{key} = " + json.dumps(value, ensure_ascii=False).replace("\x7f", r"\u007F") + "\n"
        for key, value in fields.items()
    )


def write_project(skills_dir: Path, project: Path, files: dict[Path, str]) -> None:
    references: dict[str, dict[str, str]] = {}
    for source, name in files.items():
        skill, folder, *_ = source.parts
        if folder == "references":
            references.setdefault(skill, {})[source.relative_to(skill).as_posix()] = name

    for source, name in files.items():
        original = skills_dir / source
        target = project / name
        if source.suffix != ".md":
            shutil.copyfile(original, target)
            continue

        def replace(match: re.Match[str]) -> str:
            path = match["path"]
            explicit_skill = match["skill"]
            owner = explicit_skill or source.parts[0]

            def find_names(paths: dict[str, str]) -> list[str]:
                if path.endswith("/"):
                    return [name for key, name in paths.items() if key.startswith(path)]
                return [paths[path]] if path in paths else []

            names = find_names(references.get(owner, {}))
            if not names and not explicit_skill:
                matches = [
                    candidate for paths in references.values() if (candidate := find_names(paths))
                ]
                if len(matches) == 1:
                    names = matches[0]
            if not names:
                raise ValueError(f"{source}: unresolved Project reference {match[0]}")
            quote = match["quote"]
            labels = [f"{quote}{name}{quote}" for name in names]
            return " e ".join((", ".join(labels[:-1]), labels[-1])) if len(labels) > 1 else labels[0]

        text = original.read_text(encoding="utf-8")
        target.write_text(REFERENCE_PATH.sub(replace, text), encoding="utf-8")


def build(root: Path) -> None:
    skills = sorted(path.parent for path in (root / "skills").glob("*/SKILL.md") if path.is_file())
    agents = sorted((root / "agents" / "editorial").glob("*.md"))
    check_manifests(root, agents)
    instructions = root / "skills" / "editor-chefe" / "SKILL.md"
    if not instructions.is_file():
        raise ValueError("skills/editor-chefe/SKILL.md: missing project instructions")

    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=dist) as staging:
        output = Path(staging)
        platforms = (output / "chatgpt", output / "claude-ai")
        project = output / "chatgpt-projeto"
        codex = output / "codex" / "agents"
        for directory in (*platforms, project, codex):
            directory.mkdir(parents=True)
        project_files = {}
        skills_dir = root / "skills"
        for skill in skills:
            files = sorted(tree_files(skill))
            archive = platforms[0] / f"{skill.name}.zip"
            with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
                for relative in files:
                    bundle.write(skill / relative, relative.as_posix())
            shutil.copyfile(archive, platforms[1] / archive.name)

            skill_file = (skill / "SKILL.md").relative_to(skills_dir)
            project_files[skill_file] = (
                "instrucoes.md" if skill == instructions.parent else f"{skill.name}-SKILL.md"
            )
            for relative in files:
                folder, *parts = relative.parts
                if folder != "references" or not parts:
                    continue
                if parts[0] == "comum":
                    # The build checks that each skill has the same shared copies.
                    if skill != instructions.parent:
                        continue
                    name = "-".join(parts[1:])
                else:
                    name = "-".join((skill.name, *parts))
                project_files[(skill / relative).relative_to(skills_dir)] = name

        write_project(skills_dir, project, project_files)
        for source in agents:
            (codex / f"{source.stem}.toml").write_text(codex_agent(source), encoding="utf-8")

        for directory in sorted(output.iterdir()):
            target = dist / directory.name
            if target.exists():
                shutil.rmtree(target)
            directory.rename(target)


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--sync", action="store_true")
    g.add_argument("--build", action="store_true")
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
    if errs:
        return 1
    if args.build:
        try:
            build(root)
        except (OSError, ValueError) as error:
            print(f"error: {error}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
