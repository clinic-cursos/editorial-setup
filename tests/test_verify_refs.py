import importlib.util
import http.client
import io
import json
from pathlib import Path
import urllib.error

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/auditor-cientifico/scripts/verify_refs.py"
spec = importlib.util.spec_from_file_location("verify_refs", SCRIPT)
verify_refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_refs)

CROSSREF = {
    "message": {
        "title": ["Deep learning"],
        "author": [{"family": "LeCun", "given": "Yann"}],
        "issued": {"date-parts": [[2015, 5, 28]]},
    }
}
REF = {"key": "lecun2015", "title": "Deep learning", "authors": ["LeCun, Yann"], "year": 2015, "doi": "10.1038/nature14539"}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_urlopen(routes, calls):
    def urlopen(request, timeout=None):
        calls.append(request)
        for prefix, payload in routes.items():
            if request.full_url.startswith(prefix):
                if isinstance(payload, Exception):
                    raise payload
                return FakeResponse(json.dumps(payload).encode())
        raise AssertionError(f"unexpected url {request.full_url}")

    return urlopen


def run(monkeypatch, tmp_path, refs, routes, *args):
    calls = []
    monkeypatch.setattr(verify_refs.urllib.request, "urlopen", fake_urlopen(routes, calls))
    path = tmp_path / "refs.json"
    path.write_text(json.dumps(refs), encoding="utf-8")
    return path, calls


def test_matching_doi_ok(monkeypatch, tmp_path, capsys):
    path, calls = run(monkeypatch, tmp_path, [REF], {"https://api.crossref.org/works/": CROSSREF})
    assert verify_refs.main([str(path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out[0]["key"] == "lecun2015" and out[0]["status"] == "ok"
    assert calls[0].get_header("User-agent") == "clinic-editorial-setup/0.1"


def test_unknown_doi_not_found(monkeypatch, tmp_path, capsys):
    err = urllib.error.HTTPError("u", 404, "Not Found", {}, None)
    path, _ = run(monkeypatch, tmp_path, [REF], {"https://api.crossref.org/works/": err})
    assert verify_refs.main([str(path)]) == 1
    assert json.loads(capsys.readouterr().out)[0]["status"] == "not-found"


def test_title_mismatch_divergent(monkeypatch, tmp_path, capsys):
    ref = {**REF, "title": "Um tema completamente diferente"}
    path, _ = run(monkeypatch, tmp_path, [ref], {"https://api.crossref.org/works/": CROSSREF})
    assert verify_refs.main([str(path)]) == 1
    out = json.loads(capsys.readouterr().out)[0]
    assert out["status"] == "divergent" and "title" in out["detail"]


def test_offline_unverified(monkeypatch, tmp_path, capsys):
    path, calls = run(monkeypatch, tmp_path, [REF], {})
    assert verify_refs.main([str(path), "--offline"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["status"] == "unverified"
    assert calls == []


def test_rate_limited_unverified(monkeypatch, tmp_path, capsys):
    err = urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None)
    path, _ = run(monkeypatch, tmp_path, [REF], {"https://api.crossref.org/works/": err})
    assert verify_refs.main([str(path)]) == 0
    out = json.loads(capsys.readouterr().out)[0]
    assert out["status"] == "unverified" and out["reason"] == "http 429"


def test_author_prefix_divergent(monkeypatch, tmp_path, capsys):
    crossref = {"message": {**CROSSREF["message"], "author": [{"family": "Liu", "given": "Ming"}]}}
    ref = {**REF, "authors": ["Li, Ming"]}
    path, _ = run(monkeypatch, tmp_path, [ref], {"https://api.crossref.org/works/": crossref})
    assert verify_refs.main([str(path)]) == 1
    assert json.loads(capsys.readouterr().out)[0]["status"] == "divergent"


def test_pubmed_initials_and_accents_match(monkeypatch, tmp_path, capsys):
    pubmed = {"result": {"1": {"title": "Deep learning.", "authors": [{"name": "Muñoz AB"}], "pubdate": "2015 May"}}}
    ref = {**REF, "authors": ["Munoz, Ana"], "pmid": "1"}
    del ref["doi"]
    path, _ = run(monkeypatch, tmp_path, [ref], {"https://eutils.ncbi.nlm.nih.gov/": pubmed})
    assert verify_refs.main([str(path)]) == 0
    assert json.loads(capsys.readouterr().out)[0]["status"] == "ok"


def test_missing_year_unverified(monkeypatch, tmp_path, capsys):
    crossref = {"message": {k: v for k, v in CROSSREF["message"].items() if k != "issued"}}
    path, _ = run(monkeypatch, tmp_path, [REF], {"https://api.crossref.org/works/": crossref})
    assert verify_refs.main([str(path)]) == 0
    out = json.loads(capsys.readouterr().out)[0]
    assert out["status"] == "unverified" and "ano" in out["detail"]


def test_compound_surname_divergent(monkeypatch, tmp_path, capsys):
    ref = {**REF, "authors": ["Silva Santos, Ana"]}
    crossref = {"message": {**CROSSREF["message"], "author": [{"family": "Pereira Santos"}]}}
    path, _ = run(monkeypatch, tmp_path, [ref], {"https://api.crossref.org/works/": crossref})
    assert verify_refs.main([str(path)]) == 1
    assert json.loads(capsys.readouterr().out)[0]["status"] == "divergent"
    pubmed = {"result": {"1": {"title": "Deep learning.", "authors": [{"name": "Pereira Santos AB"}], "pubdate": "2015"}}}
    ref = {**ref, "pmid": "1"}
    del ref["doi"]
    path, _ = run(monkeypatch, tmp_path, [ref], {"https://eutils.ncbi.nlm.nih.gov/": pubmed})
    assert verify_refs.main([str(path)]) == 1
    assert json.loads(capsys.readouterr().out)[0]["status"] == "divergent"


def test_particles_ignored(monkeypatch, tmp_path, capsys):
    pubmed = {"result": {"1": {"title": "Deep learning.", "authors": [{"name": "de Costa AB"}], "pubdate": "2015"}}}
    ref = {**REF, "authors": ["da Costa, Ana"], "pmid": "1"}
    del ref["doi"]
    path, _ = run(monkeypatch, tmp_path, [ref], {"https://eutils.ncbi.nlm.nih.gov/": pubmed})
    assert verify_refs.main([str(path)]) == 0
    assert json.loads(capsys.readouterr().out)[0]["status"] == "ok"


def test_crossref_family_kept_whole(monkeypatch, tmp_path, capsys):
    crossref = {"message": {**CROSSREF["message"], "author": [{"family": "Kim LI"}]}}
    ref = {**REF, "authors": ["Kim, Ana"]}
    path, _ = run(monkeypatch, tmp_path, [ref], {"https://api.crossref.org/works/": crossref})
    assert verify_refs.main([str(path)]) == 1
    assert json.loads(capsys.readouterr().out)[0]["status"] == "divergent"


@pytest.mark.parametrize(
    "author, family, expected",
    [
        ("Ana Silva Santos", "Silva Santos", 0),
        ("Ana Pereira Santos", "Silva Santos", 1),
        ("Ana Santos", "Silva Santos", 1),
        ("Ana Silva Santos", "Santos", 0),
    ],
)
def test_no_comma_name_suffix(monkeypatch, tmp_path, capsys, author, family, expected):
    crossref = {"message": {**CROSSREF["message"], "author": [{"family": family}]}}
    path, _ = run(monkeypatch, tmp_path, [{**REF, "authors": [author]}], {"https://api.crossref.org/works/": crossref})
    assert verify_refs.main([str(path)]) == expected
    status = json.loads(capsys.readouterr().out)[0]["status"]
    assert status == ("ok" if expected == 0 else "divergent")


def test_incomplete_read_unverified(monkeypatch, tmp_path, capsys):
    err = http.client.IncompleteRead(b"par")
    path, _ = run(monkeypatch, tmp_path, [REF], {"https://api.crossref.org/works/": err})
    assert verify_refs.main([str(path)]) == 0
    out = json.loads(capsys.readouterr().out)[0]
    assert out["status"] == "unverified" and out["reason"] == "IncompleteRead"
