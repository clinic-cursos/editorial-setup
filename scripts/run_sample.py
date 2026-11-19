"""Rode o fluxo do Diagramador num PDF real de EDITORIAL_SAMPLES_DIR e grave um relatório sem conteúdo do livro.

Uso: run_sample.py NOME_DO_PDF RELATORIO
Saída: 0 sempre que o relatório é gravado (aprovado ou não); 2 em erro de uso ou de leitura.
O original só é lido. O trabalho fica numa pasta temporária fora do repositório (em /var/tmp, se existir).
"""

import collections
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import pdfplumber
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "skills/diagramador/scripts"
IMAGENS = ROOT / "skills/imagens/scripts"
PALETTE = ["#87082E", "#EAD4DB", "#955251", "#625E61"]  # skills/imagens/references/paleta.md
STEP_TIMEOUT = 180  # segundos por script: o cartão tem teto de 10 min para os dois livros
MAX_IMAGES = 3  # shortcut: insert_images.py recompõe o livro inteiro por imagem; 5 mantém o ensaio dentro do teto de 10 min
ROW = re.compile(r"^\| (\d+) \| (erro|aviso) \| (\S+) \|", re.M)
SUBSET = re.compile(r"^[A-Z]{6}\+")


class StepTimeout(Exception):
    pass


def run(script: Path, *args) -> subprocess.CompletedProcess:
    try:
        return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, timeout=STEP_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise StepTimeout(script.name) from None


def fail(message: str):
    print(message, file=sys.stderr)
    sys.exit(2)


def input_path(name: str, samples: Path) -> Path:
    """O argumento é o nome de um PDF dentro da pasta de amostras; link, caminho absoluto e `..` que saem dela são recusados."""
    pdf = (samples / name).resolve()
    if not pdf.is_relative_to(samples.resolve()) or not pdf.is_file():
        fail(f"PDF não encontrado em EDITORIAL_SAMPLES_DIR: {name}")
    return pdf


def report_path(name: str, pdf: Path, samples: Path) -> Path:
    """O relatório nunca pode cair sobre o original nem dentro da pasta de amostras."""
    report = Path(name).resolve()
    if report == pdf.resolve() or report.is_relative_to(samples.resolve()) or report.suffix != ".md":
        fail(f"Relatório recusado: precisa terminar em .md e ficar fora de EDITORIAL_SAMPLES_DIR ({name})")
    return report


def image_problems(inserted: int) -> list[str]:
    if inserted < 1:
        return ["nenhuma imagem de teste foi inserida (sem candidatas ou todas recusadas)"]
    return []


def fill_metadata(manuscript: Path) -> dict:
    """Preencha título, curso e autores a partir da capa e do expediente que o extrator pôs no Markdown."""
    text = manuscript.read_text(encoding="utf-8")
    meta = {}
    m = re.search(r"^# (?!Expediente)(.+)$", text, re.M)
    if m:
        meta["title"] = m[1].strip()
    m = re.search(r"^### AUTORES\s*\n+(.+)$", text, re.M)
    if m:
        meta["authors"] = ", ".join(a.strip() for a in m[1].split("•") if a.strip())
    m = re.search(r"^### CLINIC EDITORA / (.+)$", text, re.M)
    if m:
        meta["course"] = m[1].strip().capitalize()
    meta["version"] = "1.0"
    for key, value in meta.items():
        text = re.sub(rf"^{key}:.*$", lambda _: f"{key}: {value}", text, count=1, flags=re.M)
    manuscript.write_text(text, encoding="utf-8")
    return meta


def fonts(pdf_path: Path) -> collections.Counter:
    found = collections.Counter()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for name in {c.get("fontname") or "sem nome" for c in page.chars}:
                found[SUBSET.sub("", name)] += 1
            page.flush_cache()
    return found


def layout_counts(report_text: str) -> collections.Counter:
    return collections.Counter((sev, kind) for _, sev, kind in ROW.findall(report_text))


def fidelity(original: Path, output: Path) -> tuple[list[float], int]:
    """Razões por comparação e número de linhas de diferença (o conteúdo do livro não vai ao relatório)."""
    done = run(DIAG / "text_fidelity.py", original, output)
    if done.returncode == 2:
        fail(f"Fidelidade ilegível: {done.stderr.strip()}")
    ratios = [float(r) for r in done.stdout.split()]
    return ratios, len([line for line in done.stderr.splitlines() if line.strip()])


def synthetic_images(candidates: list, out: Path) -> None:
    out.mkdir()
    for number, row in enumerate(candidates):
        # 300 ppi no tamanho do espaço livre; a cor lisa pesa pouco no disco
        size = (max(1, round(row["width_mm"] * 300 / 25.4)), max(1, round(row["height_mm"] * 300 / 25.4)))
        Image.new("RGB", size, PALETTE[number % len(PALETTE)]).save(out / f"pagina-{row['page']:02d}.png")


# Hipóteses de causa por tipo de achado, escritas na leitura dos dois livros reais (a confirmar no cartão de correção).
CAUSES = {
    "image-low-resolution": "`build_book.py` e `assets/` (CSS): a figura extraída é esticada à largura da coluna e cai abaixo do ppi do original. Correção: limitar a largura da figura ao tamanho do original (pixels pelo ppi herdado).",
    "toc-mismatch": "`extract_pdf.py` mantém o sumário do original como texto do corpo, com entradas partidas em linhas e números de página antigos, e `check_toc` o lê como sumário. Correção: descartar capa, expediente e sumário do original na extração e deixar o `build_book.py` gerar o sumário.",
    "duplicate-paragraph": "`lib/pdfcheck` (`check_duplicates`): o texto repetido começa na linha do cabeçalho corrido e passa de 100 caracteres. Correção: tirar cabeçalho e rodapé da comparação.",
    "image-distorted": "`build_book.py`: a figura é redimensionada sem manter a proporção. Correção: fixar só uma dimensão.",
    "font-not-allowed": "`assets/` (CSS): fonte de reserva usada no lugar da marca. Correção: conferir as fontes embutidas.",
}


TIMEOUT_CAUSES = {
    "extract_pdf.py": [
        "- `extract_pdf.py`: o pypdf recodifica cada imagem JPEG 2000 do PDF pelo codificador do Pillow (`Jpeg2KImagePlugin`), que é muito lento em imagem grande; no Toxina (80 páginas, 36 MB) a extração passou de 30 min sem terminar, contra 5 s do Preenchedores (117 páginas, 4,8 MB).",
        "- Correção sugerida: gravar o fluxo JPX original sem recodificar, ou limitar a extração ao tamanho exibido, e medir o tempo por página.",
    ],
}


def causes(problems: list, counts: collections.Counter, diffs: int) -> list[str]:
    out = [f"- `{kind}`: {CAUSES[kind]}" for kind in sorted({k for (s, k) in counts if s == "erro"} & CAUSES.keys())]
    if diffs:
        out.append("- fidelidade: perdas e acréscimos de palavras e números alterados em URLs e referências (`text_fidelity.py` lista os trechos). A causa provável é `extract_pdf.py` (rótulos de bloco como «Ponto-chave» e «Perguntas frequentes», quebra de linha em URL). Correção: conferir a lista no cartão de correção.")
    return out or ["- nenhuma"]


def table(counts: collections.Counter) -> list[str]:
    if not counts:
        return ["- nenhum achado"]
    return [f"- {sev} `{kind}`: {n}" for (sev, kind), n in sorted(counts.items())]


def sample(pdf: Path, work: Path) -> list[str]:
    manuscript, originals = work / "manuscrito.md", work / "imagens-originais"
    steps = []

    done = run(DIAG / "extract_pdf.py", pdf, "--out", manuscript, "--images", originals)
    if done.returncode != 0:
        fail(f"Extração falhou: {done.stderr.strip()}")
    meta = fill_metadata(manuscript)
    source_ratios, source_diffs = fidelity(pdf, manuscript)

    v1 = work / "versoes/v1"
    done = run(DIAG / "build_book.py", manuscript, "--out", v1)
    if done.returncode != 0:
        fail(f"Composição falhou (código {done.returncode}): {done.stderr.strip()}")
    layout1 = json.loads((v1 / "layout.json").read_text(encoding="utf-8"))
    with pdfplumber.open(v1 / "livro.pdf") as doc:
        pages1 = len(doc.pages)

    origin = originals / "origem.json"
    args = ["--inherited", origin] if origin.exists() else []
    check1 = run(DIAG / "check_layout.py", v1 / "livro.pdf", *args)
    if check1.returncode == 2:
        fail(f"Checagem falhou: {check1.stderr.strip()}")
    counts1 = layout_counts(check1.stdout)
    fonts1 = fonts(v1 / "livro.pdf")
    ratios1, diffs1 = fidelity(manuscript, v1 / "livro.pdf")

    spaces = work / "espaco-livre.json"
    done = run(IMAGENS / "free_space.py", v1 / "livro.pdf", "--json", spaces)
    if done.returncode != 0:
        fail(f"Espaço livre falhou: {done.stderr.strip()}")
    candidates = json.loads(spaces.read_text(encoding="utf-8"))

    synthetic_images(candidates[:MAX_IMAGES], work / "imagens")
    v2 = work / "versoes/v2"
    done = run(DIAG / "insert_images.py", manuscript, work / "imagens", "--out", v2)
    if done.returncode != 0:
        fail(f"Inserção falhou (código {done.returncode}): {done.stderr.strip()}")
    removed = len([w for w in done.stderr.splitlines() if "mudaria a paginação" in w])
    inserted = len(re.findall(r"^imagem inserida", done.stdout, re.M))
    layout2 = json.loads((v2 / "layout.json").read_text(encoding="utf-8"))
    with pdfplumber.open(v2 / "livro.pdf") as doc:
        pages2 = len(doc.pages)
    same_layout = all(layout2.get(k) == v for k, v in layout1.items())

    check2 = run(DIAG / "check_layout.py", v2 / "livro.pdf", *args)
    if check2.returncode == 2:
        fail(f"Segunda checagem falhou: {check2.stderr.strip()}")
    counts2 = layout_counts(check2.stdout)
    ratios2, diffs2 = fidelity(manuscript, v2 / "livro.pdf")

    dejavu = sorted(n for n in set(fonts1) if "dejavu" in n.casefold())
    problems = []
    if check1.returncode:
        problems.append("erro de layout na composição")
    if check2.returncode:
        problems.append("erro de layout depois da inserção das imagens")
    if min(source_ratios + ratios1 + ratios2) < 0.995 or source_diffs or diffs1 or diffs2:
        problems.append("fidelidade do texto abaixo de 0,995 ou com diferenças listadas")
    if dejavu:
        problems.append("fonte DejaVu no PDF")
    if pages1 != pages2 or not same_layout:
        problems.append("a paginação mudou depois das imagens")
    problems += image_problems(inserted)

    steps += [
        f"Resultado: {'REPROVADO' if problems else 'APROVADO'}",
        "",
        f"- Motivos: {'; '.join(problems) if problems else 'nenhum'}",
        f"- Metadados preenchidos a partir da capa e do expediente: {', '.join(sorted(meta))}",
        "",
        "## Composição (v1)",
        f"- Páginas: {pages1}",
        f"- Fontes encontradas: {', '.join(f'{n} ({c} pág.)' for n, c in sorted(fonts1.items())) or 'nenhuma'}",
        f"- DejaVu: {'sim, ' + ', '.join(dejavu) if dejavu else 'nenhuma'}",
        f"- Erros: {sum(n for (s, _), n in counts1.items() if s == 'erro')}; avisos: {sum(n for (s, _), n in counts1.items() if s == 'aviso')}",
        *table(counts1),
        "",
        "## Fidelidade do texto (mínimo aceito 0,995)",
        f"- PDF original contra manuscrito extraído: {' '.join(f'{r:.4f}' for r in source_ratios)} ({source_diffs} linhas de diferença)",
        f"- Manuscrito contra PDF composto (v1): {' '.join(f'{r:.4f}' for r in ratios1)} ({diffs1} linhas de diferença)",
        "",
        "## Imagens sintéticas (retângulos na paleta)",
        f"- Páginas candidatas (espaço livre acima do limite): {len(candidates)}",
        f"- Imagens de teste geradas (as primeiras candidatas, no máximo {MAX_IMAGES}): {min(len(candidates), MAX_IMAGES)}",
        f"- Imagens inseridas: {inserted}; retiradas por mudar a paginação: {removed}",
        "",
        "## Depois das imagens (v2)",
        f"- Paginação: {pages1} páginas antes, {pages2} depois; âncoras dos blocos {'iguais' if same_layout else 'DIFERENTES'}",
        f"- Erros: {sum(n for (s, _), n in counts2.items() if s == 'erro')}; avisos: {sum(n for (s, _), n in counts2.items() if s == 'aviso')}",
        *table(counts2),
        f"- Fidelidade (manuscrito contra v2): {' '.join(f'{r:.4f}' for r in ratios2)} ({diffs2} linhas de diferença)",
        "",
        "## Causa provável e correção sugerida (por script)" if problems else "## Causas",
        *(causes(problems, counts1, source_diffs + diffs1 + diffs2) if problems else ["- nenhuma"]),
        "",
    ]
    return steps


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        fail("Uso: run_sample.py NOME_DO_PDF RELATORIO")
    samples = os.environ.get("EDITORIAL_SAMPLES_DIR")
    if not samples:
        fail("Defina EDITORIAL_SAMPLES_DIR com a pasta dos livros.")
    pdf = input_path(argv[0], Path(samples))
    report = report_path(argv[1], pdf, Path(samples))
    scratch = "/var/tmp" if Path("/var/tmp").is_dir() else None  # /tmp pode ficar na memória
    with tempfile.TemporaryDirectory(prefix="editorial-sample-", dir=scratch) as tmp:
        try:
            body = sample(pdf, Path(tmp))
        except StepTimeout as step:
            body = [
                "Resultado: REPROVADO", "",
                f"- Motivos: `{step}` passou de {STEP_TIMEOUT} s e foi interrompido; o resto do fluxo não rodou",
                "",
                "## Causa provável e correção sugerida (por script)",
                *TIMEOUT_CAUSES.get(str(step), ["- sem hipótese registrada para este script"]),
            ]
    try:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(f"# Ensaio de diagramação: {Path(argv[0]).stem}\n\n" + "\n".join(body) + "\n", encoding="utf-8")
    except OSError as error:
        fail(f"Não foi possível gravar {report}: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
