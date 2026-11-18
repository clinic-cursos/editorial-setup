import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import package  # noqa: E402


def make_skill(root, name="demo", desc="Uma skill de teste.", total_lines=None, md_name=None, raw=None):
    d = root / "skills" / name
    d.mkdir(parents=True)
    lines = ["---", f"name: {md_name or name}", f"description: {desc}", "---", "# Demo"]
    lines += ["linha"] * ((total_lines or 0) - len(lines))
    (d / "SKILL.md").write_text(raw if raw is not None else "\n".join(lines) + "\n", encoding="utf-8")
    return d


def run(root):
    return package.check(root)


def test_valid_skill_passes(tmp_path):
    make_skill(tmp_path)
    assert run(tmp_path) == ([], [])
    assert package.main(["--check"], root=tmp_path) == 0


def test_name_with_claude_fails(tmp_path):
    make_skill(tmp_path, name="meu-claude-helper")
    errs, _ = run(tmp_path)
    assert any("claude" in e for e in errs)
    assert package.main(["--check"], root=tmp_path) == 1


def test_description_over_1024_fails(tmp_path):
    make_skill(tmp_path, desc="x" * 1025)
    errs, _ = run(tmp_path)
    assert any("description" in e for e in errs)


def test_skill_md_500_lines_fails(tmp_path):
    make_skill(tmp_path, total_lines=500)
    errs, _ = run(tmp_path)
    assert any("lines" in e for e in errs)


def test_skill_md_499_lines_passes(tmp_path):
    make_skill(tmp_path, total_lines=499)
    assert run(tmp_path) == ([], [])


def test_unclosed_frontmatter_fails(tmp_path):
    make_skill(tmp_path, raw="---\nname: demo\ndescription: ok\n# Demo\n")
    assert run(tmp_path)[0]


def test_comment_only_description_fails(tmp_path):
    make_skill(tmp_path, desc="# comentario")
    errs, _ = run(tmp_path)
    assert any("description" in e for e in errs)


def _shared_tree(tmp_path):
    make_skill(tmp_path, name="diagramador")
    (tmp_path / "lib" / "pdfcheck").mkdir(parents=True)
    (tmp_path / "lib" / "pdfcheck" / "a.py").write_text("x = 1\n")
    (tmp_path / "shared" / "references").mkdir(parents=True)
    (tmp_path / "shared" / "references" / "g.md").write_text("regra\n")
    package.sync(tmp_path)
    return tmp_path / "skills" / "diagramador"


def test_extra_file_in_copy_fails(tmp_path):
    skill = _shared_tree(tmp_path)
    (skill / "references/comum/sobra.md").write_text("x\n")
    assert any("sobra.md" in e for e in run(tmp_path)[0])


def test_sync_removes_stale_file(tmp_path):
    skill = _shared_tree(tmp_path)
    (skill / "scripts/pdfcheck/velho.py").write_text("x\n")
    (skill / "references/comum/sobra.md").write_text("x\n")
    package.sync(tmp_path)
    assert not (skill / "scripts/pdfcheck/velho.py").exists()
    assert not (skill / "references/comum/sobra.md").exists()
    assert run(tmp_path) == ([], [])


def test_top_level_bin_fails(tmp_path):
    make_skill(tmp_path)
    (tmp_path / "bin").mkdir()
    errs, _ = run(tmp_path)
    assert any("bin/" in e for e in errs)


def test_drifted_copy_fails(tmp_path):
    make_skill(tmp_path, name="diagramador")
    (tmp_path / "lib" / "pdfcheck").mkdir(parents=True)
    (tmp_path / "lib" / "pdfcheck" / "a.py").write_text("x = 1\n")
    (tmp_path / "shared" / "references").mkdir(parents=True)
    (tmp_path / "shared" / "references" / "g.md").write_text("regra\n")
    (tmp_path / "shared" / "rules").mkdir()
    (tmp_path / "shared" / "rules" / "r.json").write_text("{}\n")
    assert run(tmp_path)[0], "missing copies must fail before sync"
    package.sync(tmp_path)
    skill = tmp_path / "skills" / "diagramador"
    assert (skill / "scripts/pdfcheck/a.py").is_file()
    assert (skill / "references/comum/g.md").is_file()
    assert (skill / "references/comum/r.json").is_file()
    assert run(tmp_path) == ([], [])
    (skill / "references/comum/g.md").write_text("alterada\n")
    errs, _ = run(tmp_path)
    assert any("g.md" in e for e in errs)


def test_sync_pdfcheck_only_in_fixed_skills(tmp_path):
    make_skill(tmp_path, name="editor-chefe")
    (tmp_path / "lib" / "pdfcheck").mkdir(parents=True)
    (tmp_path / "lib" / "pdfcheck" / "a.py").write_text("x = 1\n")
    package.sync(tmp_path)
    assert not (tmp_path / "skills/editor-chefe/scripts/pdfcheck").exists()


def test_folder_without_skill_md_warns(tmp_path):
    (tmp_path / "skills" / "vazia").mkdir(parents=True)
    errs, warns = run(tmp_path)
    assert errs == [] and len(warns) == 1
    assert package.main(["--check"], root=tmp_path) == 0


def test_null_description_fails(tmp_path):
    for i, val in enumerate(("null", "~", '""', "''")):
        make_skill(tmp_path, name=f"s{i}", desc=val)
    errs, _ = run(tmp_path)
    assert len([e for e in errs if "description" in e]) == 4
    make_skill(tmp_path, name="outra", md_name="null")
    assert any("name" in e for e in run(tmp_path)[0])
