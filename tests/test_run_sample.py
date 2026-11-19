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


def test_report_equal_to_input_is_refused(samples):
    assert exit_code(lambda: run_sample.report_path(str(samples / "livro.pdf"), samples / "livro.pdf", samples)) == 2


def test_report_inside_samples_dir_is_refused(samples):
    assert exit_code(lambda: run_sample.report_path(str(samples / "relatorio.md"), samples / "livro.pdf", samples)) == 2


def test_report_through_symlink_to_original_is_refused(samples, tmp_path):
    link = tmp_path / "relatorio.md"
    link.symlink_to(samples / "livro.pdf")
    assert exit_code(lambda: run_sample.report_path(str(link), samples / "livro.pdf", samples)) == 2


def test_report_must_end_in_md(samples, tmp_path):
    assert exit_code(lambda: run_sample.report_path(str(tmp_path / "relatorio.txt"), samples / "livro.pdf", samples)) == 2


def test_report_outside_samples_is_accepted(samples, tmp_path):
    assert run_sample.report_path(str(tmp_path / "out/relatorio.md"), samples / "livro.pdf", samples) == tmp_path / "out/relatorio.md"


def test_input_with_dotdot_is_refused(samples, tmp_path):
    (tmp_path / "fora.pdf").write_bytes(b"%PDF-1.4")
    assert exit_code(lambda: run_sample.input_path("../fora.pdf", samples)) == 2


def test_absolute_input_is_refused(samples, tmp_path):
    (tmp_path / "fora.pdf").write_bytes(b"%PDF-1.4")
    assert exit_code(lambda: run_sample.input_path(str(tmp_path / "fora.pdf"), samples)) == 2


def test_input_inside_samples_is_accepted(samples):
    assert run_sample.input_path("livro.pdf", samples) == (samples / "livro.pdf").resolve()


def test_verdict_with_zero_images_fails():
    assert run_sample.image_problems(inserted=0) == ["nenhuma imagem de teste foi inserida (sem candidatas ou todas recusadas)"]
    assert run_sample.image_problems(inserted=1) == []
