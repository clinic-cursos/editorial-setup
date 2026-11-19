import json
from pathlib import Path
import subprocess
import sys

import pytest
from pypdf import PdfWriter
from pypdf.generic import NameObject

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "auditor-grafico" / "scripts" / "audit_pdf.py"


def run_audit(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True, text=True, check=False,
    )


def test_audit_pdf_all_kinds(
    tmp_path, clean_pdf, overlap_pdf, safe_zone_pdf, duplicate_pdf, image_only_pdf,
    letter_pdf, layout_pdf, placed_image_pdf,
):
    def toc(document):
        document.drawString(60, 740, "Sumário")
        document.drawString(60, 710, "Introdução ..... 5")
        document.drawString(60, 40, "1")

    def introduction(document):
        document.drawString(60, 740, "Introdução")
        document.drawString(60, 40, "3")

    toc_pdf = tmp_path / "toc.pdf"
    layout_pdf(toc, introduction).rename(toc_pdf)
    image_pdf = placed_image_pdf(144, 144, pixels=(600, 200))

    unnamed_pdf = tmp_path / "unnamed.pdf"
    writer = PdfWriter(clone_from=clean_pdf)
    font = writer.pages[0]["/Resources"]["/Font"]["/F1"]
    font[NameObject("/BaseFont")] = NameObject("/unknown")
    writer.write(unnamed_pdf)

    cases = (
        (clean_pdf, {("font-not-allowed", 1)}),
        (overlap_pdf, {("overlap", 2)}),
        (safe_zone_pdf, {("outside-safe-zone", 1)}),
        (duplicate_pdf, {("duplicate-paragraph", 2)}),
        (image_only_pdf, {("page-without-text", 2)}),
        (letter_pdf, {("page-size", 1)}),
        (unnamed_pdf, {("font-unnamed", 1)}),
        (image_pdf, {("image-low-resolution", 1), ("image-distorted", 1)}),
        (toc_pdf, {("page-number", 2), ("toc-mismatch", 1)}),
    )
    for pdf, expected in cases:
        json_path = tmp_path / "report.json"
        md_path = tmp_path / "report.md"
        result = run_audit(pdf, "--json", json_path, "--md", md_path)
        assert result.returncode in (0, 1), result.stderr
        report = json.loads(json_path.read_text(encoding="utf-8"))
        found = {(item["kind"], item["page"]) for item in report["findings"]}
        assert expected <= found, pdf.name
        assert result.returncode == int(any(f["severity"] == "error" for f in report["findings"]))
        markdown = md_path.read_text(encoding="utf-8")
        for finding in report["findings"]:
            severity = {"error": "erro", "warning": "aviso"}[finding["severity"]]
            assert f"| {finding['page']} | {severity} | {finding['kind']} |" in markdown


def test_rules_and_image_origin(placed_image_pdf, tmp_path):
    pdf = placed_image_pdf(144, 72, pixels=(100, 50))
    rules = tmp_path / "rules.json"
    source = ROOT / "shared" / "rules" / "graphic-rules.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    data["error_ppi"] = 40
    rules.write_text(json.dumps(data), encoding="utf-8")
    origins = tmp_path / "origem.json"
    origins.write_text('{"figura.png": {"pixels": [100, 50], "ppi": 50}}', encoding="utf-8")

    result = run_audit(pdf, "--inherited", origins)
    assert result.returncode == 0, result.stderr
    assert "| aviso | image-low-resolution |" in result.stdout

    result = run_audit(pdf, "--rules", rules)
    assert result.returncode == 0, result.stderr
    assert "| aviso | image-low-resolution |" in result.stdout

    result = run_audit(pdf)
    assert result.returncode == 1, result.stderr
    assert "| erro | image-low-resolution |" in result.stdout


def test_output_does_not_overwrite_pdf(clean_pdf):
    original = clean_pdf.read_bytes()
    result = run_audit(clean_pdf, "--json", clean_pdf)
    assert result.returncode == 2
    assert clean_pdf.read_bytes() == original


@pytest.mark.parametrize("invalid", ["pdf", "--rules", "--inherited", "--json", "--md"])
def test_invalid_file_returns_two(clean_pdf, tmp_path, invalid):
    missing = tmp_path / "missing" / "file"
    args = [missing] if invalid == "pdf" else [clean_pdf, invalid, missing]
    result = run_audit(*args)
    assert result.returncode == 2
    assert "Não foi possível auditar" in result.stderr
