"""Imagens dentro de Form XObjects: só as desenhadas são convertidas, cada uma casada pelo próprio objeto."""

from io import BytesIO
import json
from pathlib import Path
import sys

from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/diagramador/scripts"
sys.path.insert(0, str(SCRIPTS))

from extract_pdf import render  # noqa: E402


def stream(writer, data, **entries):
    obj = DecodedStreamObject()
    obj.set_data(data)
    obj.update({NameObject(f"/{key}"): value for key, value in entries.items()})
    return writer._add_object(obj)


def image(writer, size, color):
    return stream(
        writer, Image.new("RGB", size, color).tobytes(), Type=NameObject("/XObject"), Subtype=NameObject("/Image"),
        Width=NumberObject(size[0]), Height=NumberObject(size[1]), ColorSpace=NameObject("/DeviceRGB"),
        BitsPerComponent=NumberObject(8),
    )


def form(writer, content, xobjects):
    return stream(
        writer, content, Type=NameObject("/XObject"), Subtype=NameObject("/Form"),
        BBox=ArrayObject([NumberObject(n) for n in (0, 0, 595, 842)]),
        Resources=DictionaryObject({NameObject("/XObject"): xobjects}),
    )


def page_with_forms(tmp_path, build):
    """PDF de uma página com texto; `build(writer)` devolve (conteúdo anexado à página, dicionário /XObject dela)."""
    base = tmp_path / "base.pdf"
    c = canvas.Canvas(str(base), pagesize=A4)
    c.setFont("Helvetica", 10)
    c.drawString(60, 760, "Texto do corpo da pagina com figuras dentro de formularios.")
    c.save()
    writer = PdfWriter(clone_from=str(base))
    page = writer.pages[0]
    content, xobjects = build(writer)
    page[NameObject("/Resources")][NameObject("/XObject")] = xobjects
    page[NameObject("/Contents")] = stream(writer, page.get_contents().get_data() + content)
    path = tmp_path / "forms.pdf"
    writer.write(str(path))
    return path


def extract(path, tmp_path):
    out = tmp_path / "texto" / "manuscrito.md"
    markdown, files, _ = render(path, out, out.parent / "imagens")
    return markdown, {filename.name: data for filename, data in files}


def test_only_placed_images_are_converted(tmp_path, monkeypatch):
    # Como no Toxina (Forms fzFrm do MuPDF): vários Forms partilham o dicionário /XObject com todas as imagens,
    # e o pypdf lista cada imagem uma vez por Form. Só uma está desenhada.
    def build(writer):
        shared = DictionaryObject()
        shared_ref = writer._add_object(shared)
        for n in range(10):
            shared[NameObject(f"/Im{n}")] = image(writer, (8, 8), (n * 20, 0, 0))
        for n in range(10):
            shared[NameObject(f"/F{n}")] = form(writer, b"q 80 0 0 60 60 600 cm /Im0 Do Q" if n == 0 else b"", shared_ref)
        return b"\nq /F0 Do Q\n", shared_ref

    path = page_with_forms(tmp_path, build)
    saves = []  # cada conversão do pypdf termina num Image.save
    original_save = Image.Image.save
    monkeypatch.setattr(Image.Image, "save", lambda self, *a, **k: saves.append(1) or original_save(self, *a, **k))
    markdown, _ = extract(path, tmp_path)
    assert markdown.count("![](") == 1
    assert len(saves) <= 1, f"{len(saves)} imagens convertidas para 1 desenhada"


def test_same_name_in_different_forms_keeps_each_image(tmp_path):
    # Dois Forms com recursos próprios, cada um com a sua /Im1: o nome sozinho não identifica a imagem.
    def build(writer):
        red = form(writer, b"q 80 0 0 60 60 600 cm /Im1 Do Q", DictionaryObject({NameObject("/Im1"): image(writer, (40, 30), "red")}))
        blue = form(writer, b"q 40 0 0 40 60 400 cm /Im1 Do Q", DictionaryObject({NameObject("/Im1"): image(writer, (20, 20), "blue")}))
        return b"\nq /F1 Do Q q /F2 Do Q\n", DictionaryObject({NameObject("/F1"): red, NameObject("/F2"): blue})

    _, files = extract(page_with_forms(tmp_path, build), tmp_path)
    origin = json.loads(files.pop("origem.json"))
    assert origin == {"fig-1.png": {"pixels": [40, 30], "ppi": 36.0}, "fig-2.png": {"pixels": [20, 20], "ppi": 36.0}}
    for name, entry in origin.items():  # o arquivo gravado tem os pixels que o origem.json declara
        assert list(Image.open(BytesIO(files[name])).size) == entry["pixels"], name
