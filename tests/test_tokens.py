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
