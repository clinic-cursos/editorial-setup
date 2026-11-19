"""Modelo de achados e de relatório das checagens de PDF."""

import json
from dataclasses import asdict, dataclass, field
from typing import Literal


@dataclass
class Finding:
    page: int  # começa em 1
    kind: str
    severity: Literal["error", "warning"]
    detail: str
    bbox: tuple[float, float, float, float] | None = None


@dataclass
class FreeSpace:
    page: int
    x0: float
    top: float
    x1: float
    bottom: float
    fraction: float


@dataclass
class Report:
    pdf: str
    pages: int
    findings: list[Finding] = field(default_factory=list)

    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        names = {"error": "erro", "warning": "aviso"}
        lines = [
            f"# Relatório de checagem: {self.pdf}",
            "",
            f"Páginas: {self.pages}. Erros: {len(self.errors())}. "
            f"Avisos: {len(self.findings) - len(self.errors())}.",
            "",
        ]
        if not self.findings:
            return "\n".join(lines + ["Nenhum achado."]) + "\n"
        lines += ["| Página | Gravidade | Tipo | Detalhe |", "| --- | --- | --- | --- |"]
        for f in sorted(self.findings, key=lambda f: f.page):
            detail = f.detail.replace("|", "\\|")
            lines.append(f"| {f.page} | {names[f.severity]} | {f.kind} | {detail} |")
        return "\n".join(lines) + "\n"
