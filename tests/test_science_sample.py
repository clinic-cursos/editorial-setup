import importlib.util
import io
import json
import re
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tests/samples/capitulo-teste"
spec = importlib.util.spec_from_file_location("verify_refs", ROOT / "skills/auditor-cientifico/scripts/verify_refs.py")
verify_refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_refs)

PLANTED_DOI = "10.9999/planted.2024.0001"  # invented on purpose; never swap for a real one
CROSSREF = {
    "message": {
        "title": ["Deep learning"],
        "author": [{"family": "LeCun", "given": "Yann"}],
        "issued": {"date-parts": [[2015, 5, 28]]},
    }
}
PUBMED = {"result": {"26017442": {"title": "Deep learning.", "authors": [{"name": "LeCun Y"}], "pubdate": "2015 May 28"}}}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_urlopen(request, timeout=None):
    url = request.full_url
    if url.startswith(verify_refs.CROSSREF.format(doi="") + PLANTED_DOI):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
    if url.startswith("https://api.crossref.org/works/10.1038/nature14539"):
        return FakeResponse(json.dumps(CROSSREF).encode())
    if url.startswith("https://eutils.ncbi.nlm.nih.gov/") and "id=26017442" in url:
        return FakeResponse(json.dumps(PUBMED).encode())
    raise AssertionError(f"unexpected url {url}")


def test_sample_has_eight_slides():
    assert len(list((SAMPLE / "slides").glob("slide-*.md"))) == 8


def test_every_slide_mapped():
    slides = {int(p.stem.split("-")[1]) for p in (SAMPLE / "slides").glob("slide-*.md")}
    table = (SAMPLE / "slide-a-capitulo.md").read_text(encoding="utf-8")
    mapped = {int(m) for m in re.findall(r"^\|[^|]*\|\s*(\d+)\s*\|", table, re.M)}
    assert slides - mapped == set(), "orphan slides"
    manuscript = (SAMPLE / "manuscrito.md").read_text(encoding="utf-8")
    marked = {int(m) for m in re.findall(r"<!-- slide: (\d+) -->", manuscript)}
    cover_like = {int(m) for m in re.findall(r"^\|[^|]*\|\s*(\d+)\s*\|[^|]*\|\s*Sem texto próprio", table, re.M)}
    assert slides - marked - cover_like == set(), "slides without a manuscript marker"


def test_planted_reference_flagged(monkeypatch, capsys):
    monkeypatch.setattr(verify_refs.urllib.request, "urlopen", fake_urlopen)
    assert verify_refs.main([str(SAMPLE / "referencias.json")]) == 1
    status = {r["key"]: r["status"] for r in json.loads(capsys.readouterr().out)}
    assert status == {"lecun2015": "ok", "pubmed2015": "ok", "inventado2099": "not-found"}


def test_manuscript_citations_match_references():
    manuscript = (SAMPLE / "manuscrito.md").read_text(encoding="utf-8")
    refs = {r["key"] for r in json.loads((SAMPLE / "referencias.json").read_text(encoding="utf-8"))}
    assert set(re.findall(r"\[@([\w-]+)\]", manuscript)) == refs
