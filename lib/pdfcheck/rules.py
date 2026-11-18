"""Regras gráficas provisórias, lidas de graphic-rules.json."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Rules:
    allowed_fonts: list[str]
    safe_zone_mm: float
    error_ppi: int
    warning_ppi: int
    free_space_fraction: float
    distortion_tolerance: float
    page_size_pt: tuple[float, float]


def load_rules(path: str | None = None) -> Rules:
    if path is None:
        here = Path(__file__).resolve().parent
        candidates = [
            here / ".." / ".." / "references" / "comum" / "graphic-rules.json",  # cópia numa skill
            here / ".." / ".." / "shared" / "rules" / "graphic-rules.json",  # raiz do repositório
        ]
        found = next((c for c in candidates if c.is_file()), None)
        if found is None:
            raise FileNotFoundError(
                "graphic-rules.json não encontrado; procurei em: " + ", ".join(str(c.resolve()) for c in candidates)
            )
        path = str(found)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    data["page_size_pt"] = tuple(data["page_size_pt"])
    return Rules(**data)
