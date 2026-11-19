"""Regras gráficas provisórias, lidas de graphic-rules.json."""

import json
from dataclasses import dataclass, field
from pathlib import Path


def _default_rules_path() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here / ".." / ".." / "references" / "comum" / "graphic-rules.json",  # cópia numa skill
        here / ".." / ".." / "shared" / "rules" / "graphic-rules.json",  # raiz do repositório
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "graphic-rules.json não encontrado; procurei em: " + ", ".join(str(c.resolve()) for c in candidates)
    )


def _default_rule(name: str) -> float:
    return json.loads(_default_rules_path().read_text(encoding="utf-8"))[name]


@dataclass
class Rules:
    allowed_fonts: list[str]
    safe_zone_mm: float
    error_ppi: int
    warning_ppi: int
    free_space_fraction: float
    distortion_tolerance: float
    page_size_pt: tuple[float, float]
    allowed_repeats: list[str] = field(default_factory=list)  # textos que se repetem de propósito
    chapter_title_min_pt: float = field(default_factory=lambda: _default_rule("chapter_title_min_pt"))
    chapter_title_min_width_fraction: float = field(
        default_factory=lambda: _default_rule("chapter_title_min_width_fraction")
    )
    front_matter_max_pages: int = field(default_factory=lambda: int(_default_rule("front_matter_max_pages")))  # páginas iniciais sem fólio
    page_margins_mm: dict = field(default_factory=lambda: _default_rule("page_margins_mm"))  # top/bottom, iguais ao tokens.css


def load_rules(path: str | None = None) -> Rules:
    source = _default_rules_path() if path is None else Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    data["page_size_pt"] = tuple(data["page_size_pt"])
    return Rules(**data)
