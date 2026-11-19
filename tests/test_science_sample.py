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
        "title": ['The revised International Association for the Study of Pain definition of pain: concepts, challenges, and compromises'],
        "author": [{"family": "Raja", "given": "Srinivasa N"}],
        "issued": {"date-parts": [[2020, 9, 1]]},
    }
}
PUBMED = {
    "result": {
        "26827847": {
            "title": "Management of Postoperative Pain: A Clinical Practice Guideline From the American Pain Society, the American Society of Regional Anesthesia and Pain Medicine, and the American Society of Anesthesiologists' Committee on Regional Anesthesia, Executive Committee, and Administrative Council",
            "authors": [{"name": "Chou R"}],
            "pubdate": "2016 Feb",
        }
    }
}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_urlopen(request, timeout=None):
    url = request.full_url
    if url.startswith(verify_refs.CROSSREF.format(doi="") + PLANTED_DOI):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
    if url.startswith("https://api.crossref.org/works/10.1097/j.pain.0000000000001939"):
        return FakeResponse(json.dumps(CROSSREF).encode())
    if url.startswith("https://eutils.ncbi.nlm.nih.gov/") and "id=26827847" in url:
        return FakeResponse(json.dumps(PUBMED).encode())
    raise AssertionError(f"unexpected url {url}")


def test_sample_has_eight_slides():
    assert len(list((SAMPLE / "slides").glob("slide-*.md"))) == 8


def test_every_slide_mapped():
    slides = {int(p.stem.split("-")[1]) for p in (SAMPLE / "slides").glob("slide-*.md")}
    table = (SAMPLE / "slide-a-capitulo.md").read_text(encoding="utf-8")
    manuscript = (SAMPLE / "manuscrito.md").read_text(encoding="utf-8")
    # slide number -> heading it sits under, from the markers in the manuscript
    under, heading = {}, None
    for line in manuscript.splitlines():
        if re.match(r"#{1,2} ", line):
            heading = line.lstrip("#").strip()
        elif m := re.match(r"<!-- slide: (\d+) -->", line):
            under[int(m.group(1))] = heading
    rows = {}
    for line in table.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[1].isdigit():
            rows[int(cells[1])] = cells
    assert slides - rows.keys() == set(), "orphan slides"
    for n, cells in rows.items():
        destination, justification = cells[3], cells[4]
        if destination == "Sem texto próprio":
            assert justification, f"slide {n} has no text and no justification"
            assert n not in under, f"slide {n} is marked as textless but has a manuscript marker"
        else:
            assert under.get(n) == destination, f"slide {n}: destination {destination!r} is not the heading it sits under ({under.get(n)!r})"


def test_planted_reference_flagged(monkeypatch, capsys):
    monkeypatch.setattr(verify_refs.urllib.request, "urlopen", fake_urlopen)
    assert verify_refs.main([str(SAMPLE / "referencias.json")]) == 1
    status = {r["key"]: r["status"] for r in json.loads(capsys.readouterr().out)}
    assert status == {"raja2020": "ok", "chou2016": "ok", "inventado2099": "not-found"}


def test_manuscript_citations_match_references():
    manuscript = (SAMPLE / "manuscrito.md").read_text(encoding="utf-8")
    refs = {r["key"] for r in json.loads((SAMPLE / "referencias.json").read_text(encoding="utf-8"))}
    assert set(re.findall(r"\[@([\w-]+)\]", manuscript)) == refs
