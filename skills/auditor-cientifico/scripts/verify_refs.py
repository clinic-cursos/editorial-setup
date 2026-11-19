"""Confira DOI e PMID de uma lista de referências no Crossref e no PubMed (APIs gratuitas)."""

import argparse
from difflib import SequenceMatcher
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "clinic-editorial-setup/0.1"  # sem e-mail nem nome de ninguém
CROSSREF = "https://api.crossref.org/works/{doi}"
PUBMED = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
TITLE_RATIO = 0.9
TIMEOUT = 15


class NotFound(Exception):
    pass


def _get(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code in (400, 404):
            raise NotFound(url) from error
        raise


def _year(text: str) -> int | None:
    match = re.search(r"\d{4}", text or "")
    return int(match.group()) if match else None


def _crossref(doi: str) -> dict:
    msg = _get(CROSSREF.format(doi=urllib.parse.quote(doi, safe="/")))["message"]
    parts = (msg.get("issued") or {}).get("date-parts") or [[None]]
    return {
        "title": (msg.get("title") or [""])[0],
        "first_author": ((msg.get("author") or [{}])[0]).get("family", ""),
        "year": parts[0][0],
    }


def _pubmed(pmid: str) -> dict:
    result = _get(PUBMED.format(pmid=urllib.parse.quote(pmid, safe="")))["result"]
    item = result.get(str(pmid))
    if not item or "error" in item:
        raise NotFound(pmid)
    return {
        "title": item.get("title", ""),
        "first_author": ((item.get("authors") or [{}])[0]).get("name", ""),
        "year": _year(item.get("pubdate", "")),
    }


def _surname(authors) -> str:
    first = authors if isinstance(authors, str) else (authors or [""])[0]
    if "," in first:
        return first.split(",")[0].strip()
    return first.split()[-1] if first.split() else ""


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().rstrip(".").casefold()


def _last_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    tokens = _norm(name).split()
    if len(tokens) > 1 and re.fullmatch(r"[a-z]{1,3}", tokens[-1]) and name.split()[-1].isupper():
        tokens.pop()  # PubMed: "Sobrenome Iniciais"
    return tokens[-1] if tokens else ""


def _compare(ref: dict, remote: dict) -> tuple[list[str], list[str]]:
    """Devolve (divergências, o que a fonte não trouxe)."""
    problems, missing = [], []
    if SequenceMatcher(None, _norm(ref.get("title", "")), _norm(remote["title"])).ratio() < TITLE_RATIO:
        problems.append(f"title: '{ref.get('title')}' x '{remote['title']}'")
    if remote["year"] is None:
        missing.append("a fonte não trouxe o ano")
    elif ref.get("year") != remote["year"]:
        problems.append(f"year: {ref.get('year')} x {remote['year']}")
    if _last_name(_surname(ref.get("authors"))) != _last_name(remote["first_author"]):
        problems.append(f"first author: '{_surname(ref.get('authors'))}' x '{remote['first_author']}'")
    return problems, missing


def check(ref: dict, offline: bool) -> dict:
    out = {"key": ref.get("key"), "status": "unverified", "detail": ""}
    ids = [(name, ref[name], fn) for name, fn in (("doi", _crossref), ("pmid", _pubmed)) if ref.get(name)]
    if offline or not ids:
        out["detail"] = "offline" if offline else "sem doi nem pmid"
        return out
    statuses = []
    for name, value, fetch in ids:
        try:
            problems, missing = _compare(ref, fetch(str(value)))
            status = "divergent" if problems else "unverified" if missing else "ok"
            statuses.append((status, f"{name} {value}: " + "; ".join(problems + missing)))
        except NotFound:
            statuses.append(("not-found", f"{name} {value}: não encontrado"))
        except urllib.error.HTTPError as error:  # 429, 5xx: a API não respondeu, a referência não foi julgada
            out["reason"] = f"http {error.code}"
            statuses.append(("unverified", f"{name} {value}: {out['reason']}"))
        except (OSError, json.JSONDecodeError, KeyError) as error:  # URLError e timeout são OSError
            out["reason"] = type(error).__name__
            statuses.append(("unverified", f"{name} {value}: sem resposta utilizável ({error})"))
    for wanted in ("not-found", "divergent", "unverified", "ok"):
        hit = [detail for status, detail in statuses if status == wanted]
        if hit:
            out["status"], out["detail"] = wanted, " | ".join(hit)
            return out
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("refs", help="JSON com a lista de referências")
    parser.add_argument("--offline", action="store_true", help="não abre conexão; tudo sai unverified")
    args = parser.parse_args(argv)
    try:
        with open(args.refs, encoding="utf-8") as handle:
            refs = json.load(handle)
        results = [check(ref, args.offline) for ref in refs]
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(f"Não consegui ler {args.refs}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if any(r["status"] in ("not-found", "divergent") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
