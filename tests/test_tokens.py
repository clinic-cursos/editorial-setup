import json
import re
from pathlib import Path

ASSETS = Path(__file__).parent.parent / "skills" / "diagramador" / "assets"
LITERAL_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\(|\b(?:white|black|gray|grey|red|blue|green)\b", re.I)


def _css(name):
    text = (ASSETS / name).read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def test_no_literal_colors_outside_tokens():
    assert LITERAL_COLOR.findall(_css("livro.css")) == []


def test_every_variable_used_is_defined_in_tokens():
    used = set(re.findall(r"var\((--[\w-]+)", _css("livro.css")))
    defined = set(re.findall(r"(--[\w-]+)\s*:", _css("tokens.css")))
    assert used and used <= defined, sorted(used - defined)


def test_tokens_hold_the_reference_colors():
    tokens = _css("tokens.css").lower()
    for color in ("#87082e", "#910032", "#232323", "#f6f1f3"):
        assert color in tokens


def test_fonts_ship_with_licenses():
    fonts = ASSETS / "fonts"
    assert (fonts / "OFL.txt").is_file() and (fonts / "OFL-SourceSans3.txt").is_file()
    assert len(list(fonts.glob("*.ttf"))) == 7


MEASURE = re.compile(r"(?<![\w.#-])\d*\.?\d+(?:pt|mm|em|%)(?![\w])|/\s*\d*\.?\d+(?![\w.%])")
# 100% is a proportion of the container, not a typographic measure.
ALLOWED_MEASURES = {"100%"}


def test_no_literal_measures_outside_tokens():
    found = {m.group(0) for m in MEASURE.finditer(_css("livro.css"))} - ALLOWED_MEASURES
    assert found == set()


def test_margins_match_tokens():
    tokens = _css("tokens.css")
    rules = json.loads((ASSETS.parents[2] / "shared" / "rules" / "graphic-rules.json").read_text(encoding="utf-8"))
    for side in ("top", "bottom"):
        css = float(re.search(rf"--page-margin-{side}:\s*([\d.]+)mm", tokens).group(1))
        assert rules["page_margins_mm"][side] == css
