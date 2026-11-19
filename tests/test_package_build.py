import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
EDITORIAL_SKILLS = {
    "auditor-cientifico", "auditor-grafico", "diagramador", "editor-chefe",
    "editor-cientifico", "imagens",
}


@pytest.fixture(scope="module")
def built_repository(tmp_path_factory):
    root = tmp_path_factory.mktemp("editorial")
    for directory in ("agents", "lib", "shared", "skills", ".claude-plugin", ".codex-plugin"):
        shutil.copytree(ROOT / directory, root / directory)
    script = root / "scripts" / "package.py"
    script.parent.mkdir()
    shutil.copy(ROOT / "scripts" / "package.py", script)
    cache = root / "skills" / "diagramador" / "scripts" / "__pycache__"
    cache.mkdir(exist_ok=True)
    (cache / "stale.pyc").touch()

    result = subprocess.run(
        [sys.executable, str(script), "--build"], capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return root


def test_build_six_zips_with_skill_at_root(built_repository):
    root = built_repository
    skills = {source.parent.name: source for source in (root / "skills").glob("*/SKILL.md")}
    assert EDITORIAL_SKILLS | {"aulas"} <= skills.keys()
    for platform in ("chatgpt", "claude-ai"):
        archives = list((root / "dist" / platform).glob("*.zip"))
        assert {archive.stem for archive in archives} == skills.keys()
        for archive in archives:
            source = skills[archive.stem]
            with ZipFile(archive) as bundle:
                assert bundle.read("SKILL.md") == source.read_bytes()
                assert any(name.startswith("references/") for name in bundle.namelist())
                assert all(not name.endswith(".pyc") for name in bundle.namelist())
                if archive.stem == "diagramador":
                    assert "scripts/pdfcheck/checks.py" in bundle.namelist()
                    assert "assets/livro.html" in bundle.namelist()


def test_codex_toml_fields(built_repository):
    root = built_repository
    sources = {source.stem: source for source in (root / "agents" / "editorial").glob("*.md")}
    agents = list((root / "dist" / "codex" / "agents").glob("*.toml"))
    assert {agent.stem for agent in agents} == sources.keys()
    for agent in agents:
        source = sources[agent.stem].read_text(encoding="utf-8").splitlines(keepends=True)
        end = source.index("---\n", 1)
        fields = dict(line.rstrip().split(": ", 1) for line in source[1:end])
        assert tomllib.loads(agent.read_text(encoding="utf-8")) == {
            "name": fields["name"],
            "description": fields["description"],
            "developer_instructions": "".join(source[end + 1:]).lstrip("\n"),
        }


def test_project_bundle_has_instructions(built_repository):
    root = built_repository
    project = root / "dist" / "chatgpt-projeto"
    skills = root / "skills"
    assert (project / "instrucoes.md").read_bytes() == (skills / "editor-chefe" / "SKILL.md").read_bytes()
    expected = {"instrucoes.md"}
    for source in skills.glob("*/SKILL.md"):
        skill = source.parent.name
        if source.parent.name != "editor-chefe":
            name = f"{skill}-SKILL.md"
            assert (project / name).read_bytes() == source.read_bytes()
            expected.add(name)
        references = source.parent / "references"
        for reference in references.rglob("*"):
            if reference.is_file():
                category, *parts = reference.relative_to(references).parts
                name = "-".join(parts) if category == "comum" else "-".join((skill, category, *parts))
                assert (project / name).read_bytes() == reference.read_bytes()
                expected.add(name)
    assert {path.name for path in project.iterdir()} == expected
