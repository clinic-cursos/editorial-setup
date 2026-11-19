import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_sample  # noqa: E402


@pytest.fixture
def samples(tmp_path):
    folder = tmp_path / "amostras"
    folder.mkdir()
    (folder / "livro.pdf").write_bytes(b"%PDF-1.4")
    return folder


def exit_code(call):
    with pytest.raises(SystemExit) as stop:
        call()
    return stop.value.code


@pytest.fixture
def entry(samples, monkeypatch):
    """main() com a primeira etapa pesada trocada por um erro: a recusa precisa vir antes dela."""
    def heavy(*args, **kwargs):
        raise AssertionError("a etapa pesada rodou")
    monkeypatch.setattr(run_sample, "sample", heavy)
    monkeypatch.setattr(run_sample, "run", heavy)
    monkeypatch.setenv("EDITORIAL_SAMPLES_DIR", str(samples))
    return run_sample.main


def test_main_refuses_report_equal_to_input(entry, samples):
    assert exit_code(lambda: entry(["livro.pdf", str(samples / "livro.pdf")])) == 2


def test_main_refuses_report_inside_samples_dir(entry, samples):
    assert exit_code(lambda: entry(["livro.pdf", str(samples / "relatorio.md")])) == 2


def test_main_refuses_report_through_symlink_to_original(entry, samples, tmp_path):
    link = tmp_path / "relatorio.md"
    link.symlink_to(samples / "livro.pdf")
    assert exit_code(lambda: entry(["livro.pdf", str(link)])) == 2


def test_main_refuses_report_without_md(entry, tmp_path):
    assert exit_code(lambda: entry(["livro.pdf", str(tmp_path / "relatorio.txt")])) == 2


def test_main_refuses_input_outside_samples(entry, tmp_path):
    (tmp_path / "fora.pdf").write_bytes(b"%PDF-1.4")
    assert exit_code(lambda: entry(["../fora.pdf", str(tmp_path / "r.md")])) == 2


def test_main_accepts_input_resolving_inside_samples(entry, tmp_path):
    # passa pelas validações e só então chega à etapa pesada, que o fixture faz levantar
    with pytest.raises(AssertionError, match="etapa pesada"):
        entry(["../amostras/livro.pdf", str(tmp_path / "r.md")])


def test_write_report_never_writes_through_a_hard_link(samples, tmp_path):
    original = samples / "livro.pdf"
    link = tmp_path / "relatorio.md"
    link.hardlink_to(original)
    run_sample.write_report(link, "# relatório\n")
    assert original.read_bytes() == b"%PDF-1.4"
    assert link.read_text(encoding="utf-8") == "# relatório\n"
    assert not list(tmp_path.glob(".relatorio-*"))


def test_verdict_with_zero_images_fails():
    result, problems = run_sample.verdict([], inserted=0)
    assert result == "REPROVADO" and "nenhuma imagem" in problems[0]


def test_verdict_approves_with_an_image_and_no_problems():
    assert run_sample.verdict([], inserted=1) == ("APROVADO", [])


def test_verdict_keeps_other_problems():
    assert run_sample.verdict(["x"], inserted=2) == ("REPROVADO", ["x"])


def fake_fidelity(monkeypatch, code, stdout, stderr):
    monkeypatch.setattr(run_sample, "run", lambda *a, **k: subprocess.CompletedProcess(a, code, stdout, stderr))
    return run_sample.fidelity(Path("a"), Path("b"))


def test_stderr_alone_does_not_fail_fidelity(monkeypatch):
    result = fake_fidelity(monkeypatch, 0, "0.9990 0.9995\n", "trecho perdido: x\ntrecho a mais: y\n")
    assert result == ([0.999, 0.9995], 0, 2)
    assert not run_sample.fidelity_failed(result)


def test_fidelity_fails_by_exit_code_or_ratio(monkeypatch):
    assert run_sample.fidelity_failed(fake_fidelity(monkeypatch, 1, "1.0000 1.0000\n", "número alterado: x\n"))
    assert run_sample.fidelity_failed(([0.9, 1.0], 0, 0))


def test_pages_line_lists_only_page_numbers():
    rows = [{"page": 3, "width_mm": 190.0}, {"page": 17, "width_mm": 190.0}]
    assert run_sample.pages_line(rows) == "- Números das páginas candidatas: 3, 17"
    assert run_sample.pages_line([]) == "- Números das páginas candidatas: nenhuma"


def work(tmp_path):
    (tmp_path / "work").mkdir()
    return tmp_path / "work"


def fake_steps(monkeypatch, inserted_stdout, ratios="1.0000 1.0000\n", fidelity_stderr=""):
    """Respostas fixas de cada script do fluxo; os arquivos que o sample lê são criados aqui."""
    class Doc:
        pages = [object()]
        def __enter__(self): return self
        def __exit__(self, *exc): return False

    def fake_run(script, *args):
        args = [str(a) for a in args]
        out = lambda flag: Path(args[args.index(flag) + 1])
        done = lambda stdout="", code=0: subprocess.CompletedProcess(args, code, stdout, "")
        if script.name == "extract_pdf.py":
            out("--out").write_text("title: x\ncourse: A preencher\nauthors: A preencher\nversion: A preencher\n", encoding="utf-8")
        elif script.name == "build_book.py":
            (out("--out")).mkdir(parents=True)
            (out("--out") / "layout.json").write_text('{"b0001": 1}', encoding="utf-8")
        elif script.name == "free_space.py":
            out("--json").write_text('[{"page": 1, "width_mm": 190.0, "height_mm": 100.0, "ratio": 1.9, "fraction": 0.5}]', encoding="utf-8")
        elif script.name == "insert_images.py":
            (out("--out")).mkdir(parents=True)
            (out("--out") / "layout.json").write_text('{"b0001": 1}', encoding="utf-8")
            return done(inserted_stdout)
        elif script.name == "text_fidelity.py":
            return subprocess.CompletedProcess(args, 0, ratios, fidelity_stderr)
        elif script.name == "check_layout.py":
            return done("Nenhum achado.\n")
        return done()

    monkeypatch.setattr(run_sample, "run", fake_run)
    monkeypatch.setattr(run_sample.pdfplumber, "open", lambda *a, **k: Doc())
    monkeypatch.setattr(run_sample, "fonts", lambda path: run_sample.collections.Counter({"Montserrat": 1}))


def test_sample_with_zero_inserted_images_writes_reprovado(monkeypatch, tmp_path):
    fake_steps(monkeypatch, "")
    body = run_sample.sample(tmp_path / "livro.pdf", work(tmp_path))
    assert body[0] == "Resultado: REPROVADO"
    assert any("nenhuma imagem" in line for line in body)
    assert any("Números das páginas candidatas: 1" in line for line in body)


def test_sample_approves_when_everything_passes_with_an_image(monkeypatch, tmp_path):
    fake_steps(monkeypatch, "imagem inserida na página 1\n")
    assert run_sample.sample(tmp_path / "livro.pdf", work(tmp_path))[0] == "Resultado: APROVADO"


def test_sample_does_not_fail_on_informative_fidelity_stderr(monkeypatch, tmp_path):
    fake_steps(monkeypatch, "imagem inserida na página 1\n", ratios="0.9990 0.9990\n", fidelity_stderr="trecho perdido: a\ntrecho a mais: b\n")
    body = run_sample.sample(tmp_path / "livro.pdf", work(tmp_path))
    assert body[0] == "Resultado: APROVADO"
    assert any("0.9990 0.9990 (2 linhas de diferença)" in line for line in body)
