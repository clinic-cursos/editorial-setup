import dataclasses
from types import SimpleNamespace

from lib.pdfcheck import checks
from lib.pdfcheck.rules import load_rules

ALL = [
    checks.check_overlaps,
    checks.check_safe_zone,
    checks.check_duplicates,
    checks.check_fonts,
    checks.check_text_layer,
    checks.check_page_size,
]


def _fake_pdf(*fontnames):
    page = SimpleNamespace(page_number=1, chars=[{"fontname": n} for n in fontnames])
    return SimpleNamespace(pages=[page])


def test_clean_pdf_has_no_errors(clean_pdf, open_pdf, test_rules):
    pdf = open_pdf(clean_pdf)
    findings = [f for check in ALL for f in check(pdf, test_rules)]
    assert [f for f in findings if f.severity == "error"] == []


def test_overlap_detected(overlap_pdf, open_pdf, test_rules):
    found = checks.check_overlaps(open_pdf(overlap_pdf), test_rules)
    assert [(f.kind, f.page) for f in found] == [("overlap", 2)]


def test_safe_zone_detected(safe_zone_pdf, open_pdf, test_rules):
    found = checks.check_safe_zone(open_pdf(safe_zone_pdf), test_rules)
    assert [(f.kind, f.page, f.severity) for f in found] == [("outside-safe-zone", 1, "error")]


def test_duplicate_paragraph_detected(duplicate_pdf, open_pdf, test_rules):
    found = checks.check_duplicates(open_pdf(duplicate_pdf), test_rules)
    assert [(f.kind, f.page) for f in found] == [("duplicate-paragraph", 2)]


def test_font_not_allowed_detected(clean_pdf, open_pdf):
    found = checks.check_fonts(open_pdf(clean_pdf), load_rules())
    assert found and all(f.kind == "font-not-allowed" and f.severity == "error" for f in found)
    assert "Helvetica" in found[0].detail


def test_subset_prefix_normalized(test_rules):
    assert checks.check_fonts(_fake_pdf("ABCDEF+SourceSans3-Roman", "GHIJKL+Montserrat-Bold"), load_rules()) == []
    found = checks.check_fonts(_fake_pdf("ABCDEF+Arial-Bold"), load_rules())
    assert "ABCDEF" not in found[0].detail and "Arial-Bold" in found[0].detail


def test_unnamed_font_is_warning():
    found = checks.check_fonts(_fake_pdf("", None), load_rules())
    assert [(f.kind, f.severity) for f in found] == [("font-unnamed", "warning")]


def test_page_without_text_is_warning(image_only_pdf, open_pdf, test_rules):
    found = checks.check_text_layer(open_pdf(image_only_pdf), test_rules)
    assert [(f.kind, f.page, f.severity) for f in found] == [("page-without-text", 2, "warning")]


def test_letter_size_is_page_size_error(letter_pdf, open_pdf, test_rules):
    found = checks.check_page_size(open_pdf(letter_pdf), test_rules)
    assert [(f.kind, f.severity) for f in found] == [("page-size", "error")]


def test_near_coincident_lines_overlap(near_overlap_pdf, open_pdf, test_rules):
    found = checks.check_overlaps(open_pdf(near_overlap_pdf), test_rules)
    assert [f.kind for f in found] == ["overlap"]

def test_similar_family_name_not_allowed():
    found = checks.check_fonts(_fake_pdf("MontserratAlternates-Regular"), load_rules())
    assert [f.kind for f in found] == ["font-not-allowed"]


def test_duplicate_paragraph_under_different_titles(duplicate_under_titles_pdf, open_pdf, test_rules):
    found = checks.check_duplicates(open_pdf(duplicate_under_titles_pdf), test_rules)
    assert [(f.kind, f.page) for f in found] == [("duplicate-paragraph", 2)]


def test_standard_caption_repeat_is_allowed(caption_repeat_pdf, open_pdf, test_rules):
    pdf = open_pdf(caption_repeat_pdf)
    assert checks.check_duplicates(pdf, test_rules) == []
    assert checks.check_duplicates(pdf, dataclasses.replace(test_rules, allowed_repeats=[]))


def test_duplicate_within_same_page(same_page_duplicate_pdf, open_pdf, test_rules):
    found = checks.check_duplicates(open_pdf(same_page_duplicate_pdf), test_rules)
    assert [(f.kind, f.page) for f in found] == [("duplicate-paragraph", 1)]


def test_coincident_baselines_overlap_in_one_region(coincident_baselines_pdf, open_pdf, test_rules):
    found = checks.check_overlaps(open_pdf(coincident_baselines_pdf), test_rules)
    assert [f.kind for f in found] == ["overlap"]
