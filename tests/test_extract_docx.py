from io import BytesIO
from pathlib import Path
import subprocess
import sys

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts/extract_docx.py"


def run_extractor(source, output, images):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(source), "--out", str(output), "--images", str(images)],
        capture_output=True,
        text=True,
    )


def extract(document, tmp_path):
    source = tmp_path / "original.docx"
    output = tmp_path / "texto" / "manuscrito.md"
    images = tmp_path / "imagens"
    document.save(source)
    result = run_extractor(source, output, images)
    assert result.returncode == 0, result.stderr
    return output.read_text(encoding="utf-8"), images


def test_docx_headings_recovered(tmp_path):
    document = Document()
    document.core_properties.title = "Demonstração"
    document.core_properties.subject = "Curso de exemplo"
    document.core_properties.author = "Ana, Rui"
    document.core_properties.version = "1.0"
    document.add_heading("Abertura", level=0)
    document.add_heading("Capítulo", level=1)
    style = document.styles.add_style("Seção editorial", WD_STYLE_TYPE.PARAGRAPH)
    style.base_style = document.styles["Heading 2"]
    document.add_paragraph("Seção", style)
    localized = document.styles.add_style("Título local", WD_STYLE_TYPE.PARAGRAPH)
    localized.element.get_or_add_pPr().get_or_add_outlineLvl().val = 2
    document.add_paragraph("Subseção", localized)
    document.add_heading("Detalhes", level=4)
    document.add_paragraph("Primeiro parágrafo.")
    document.add_paragraph("Segundo parágrafo.")

    markdown, _ = extract(document, tmp_path)

    assert markdown == (
        "title: Demonstração\ncourse: Curso de exemplo\nauthors: Ana, Rui\nversion: 1.0\n\n"
        "# Abertura\n\n# Capítulo\n\n## Seção\n\n### Subseção\n\n### Detalhes\n\n"
        "Primeiro parágrafo.\n\nSegundo parágrafo.\n"
    )


def test_docx_lists_recovered(tmp_path):
    document = Document()
    document.add_paragraph("Item A", "List Bullet")
    document.add_paragraph("Item B", "List Bullet 2")
    document.add_paragraph("Primeiro passo", "List Number")
    direct_item = document.add_paragraph("Segundo passo")
    num_pr = direct_item._p.get_or_add_pPr().get_or_add_numPr()
    num_pr.get_or_add_numId().val = document.styles["List Number"].element.pPr.numPr.numId.val
    document.add_paragraph("Texto entre listas.")
    document.add_paragraph("Outra lista", "List Number 2")

    markdown, _ = extract(document, tmp_path)

    assert markdown.split("\n\n", 1)[1] == (
        "- Item A\n- Item B\n\n1. Primeiro passo\n2. Segundo passo\n\n"
        "Texto entre listas.\n\n1. Outra lista\n"
    )


def test_docx_image_extracted(tmp_path):
    stream = BytesIO()
    Image.new("RGB", (2, 2), "white").save(stream, format="PNG")
    document = Document()
    document.add_paragraph("Antes.")
    shape = document.add_picture(stream)
    shape._inline.docPr.set("descr", "Imagem de exemplo")
    document.add_paragraph("Depois.")
    document.add_picture(stream)

    markdown, images = extract(document, tmp_path)

    assert markdown.split("\n\n", 1)[1] == (
        "Antes.\n\n![Imagem de exemplo](../imagens/fig-1.png){#fig-1}\n\n"
        "Depois.\n\n![](../imagens/fig-2.png){#fig-2}\n"
    )
    assert (images / "fig-1.png").read_bytes() == stream.getvalue()
    assert (images / "fig-2.png").read_bytes() == stream.getvalue()


def test_unreadable_docx_exits_with_usage_error(tmp_path):
    source = tmp_path / "invalido.docx"
    source.write_text("Arquivo inválido", encoding="utf-8")
    output = tmp_path / "manuscrito.md"

    result = run_extractor(source, output, tmp_path / "imagens")

    assert result.returncode == 2
    assert "invalido.docx" in result.stderr
    assert not output.exists()
