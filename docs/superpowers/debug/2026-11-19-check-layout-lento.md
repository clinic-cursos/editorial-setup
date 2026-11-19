# CLI-514 | Lentidão ao checar o layout

## Relato

Em 19/11/2026, o diagnóstico A registrou que `check_layout.py` passou de três minutos no livro recomposto de 297 páginas e foi interrompido. A ferramenta deve concluir as nove checagens técnicas e emitir o relatório em Markdown antes da entrega do Diagramador. [Diagnóstico A](2026-11-19-extract-pdf-toxina-lento.md)

## Reprodução

Usei a base `feat/wave-3b` no SHA `45390a2`, em um AMD Ryzen 7 5825U com Python 3.12.16, pdfplumber 0.11.10, pdfminer.six 20260107 e WeasyPrint 70.0, nas versões do lock. O radar local não tem seção para essa stack. O sandbox montou `/var/tmp` como somente leitura, então gerei o PDF em `/tmp/cli-514.ZG02i2/large/livro.pdf`. Usei o ambiente já instalado no checkout principal com `uv run --locked --offline --no-sync` e `UV_CACHE_DIR` em `/tmp`.

1. Gere o manuscrito, componha o PDF e verifique a quantidade de páginas e figuras. Com 287 capítulos, observei 300 páginas A4, 57 imagens distribuídas por 57 páginas e texto selecionável. A página 18 renderizada com Poppler contém 10 parágrafos, figura e legenda.

   ```bash
   work=$(mktemp -d /tmp/cli-514.XXXXXX)
   uv run --locked python - "$work" <<'PY'
   from pathlib import Path
   import sys
   from tests.test_check_layout_perf import write_manuscript

   write_manuscript(Path(sys.argv[1]), chapters=287)
   PY
   uv run --locked python skills/diagramador/scripts/build_book.py "$work/manuscrito.md" --out "$work"
   pdfinfo "$work/livro.pdf"
   pdfimages -list "$work/livro.pdf"
   ```

2. Meça as funções na ordem da CLI e na mesma instância do PDF para manter o efeito do cache do pdfplumber. A composição ficou fora da medição. O perfil abaixo envolve as funções chamadas por `main`, incluindo a checagem de imagens que roda depois de `CHECKS`.

   ```bash
   PYTHONPATH="$PWD/skills/diagramador/scripts" uv run --locked python - "$work/livro.pdf" <<'PY'
   import sys
   from time import perf_counter
   import check_layout

   def timed(check):
       def run(*args):
           start = perf_counter()
           findings = check(*args)
           print(f"{check.__name__} {perf_counter() - start:.3f} s ({len(findings)} achados)",
                 file=sys.stderr, flush=True)
           return findings
       return run

   check_layout.CHECKS = tuple(map(timed, check_layout.CHECKS))
   check_layout.checks.check_images = timed(check_layout.checks.check_images)
   start = perf_counter()
   code = check_layout.main(sys.argv[1:])
   print(f"total {perf_counter() - start:.3f} s, saída {code}", file=sys.stderr)
   sys.exit(code)
   PY
   ```

   | Checagem | Tempo de parede (s) | Achados |
   | --- | ---: | ---: |
   | `check_overlaps` | 84,109 | 0 |
   | `check_safe_zone` | 0,788 | 0 |
   | `check_duplicates` | 38,659 | 0 |
   | `check_fonts` | 0,034 | 0 |
   | `check_text_layer` | < 0,001 | 0 |
   | `check_page_size` | < 0,001 | 0 |
   | `check_page_numbers` | 43,676 | 0 |
   | `check_toc` | 48,284 | 0 |
   | `check_images` | 0,085 | 57 avisos |
   | **CLI completa, saída 0** | **215,898** | **57 avisos** |

3. Rode a regressão opt-in. No PDF menor, a CLI produziu o relatório de 44 páginas com zero erros e falhou na asserção de tempo em `tests/test_check_layout_perf.py:62`.

   ```console
   $ EDITORIAL_PERF=1 uv run --locked --offline --no-sync pytest -q tests/test_check_layout_perf.py
   E       AssertionError: check_layout took 33.38 s for 44 pages (budget: 24 s)
   E       assert 33.37732131400003 < 24
   FAILED tests/test_check_layout_perf.py::test_check_layout_finishes_dense_book_within_budget
   1 failed in 36.95s
   ```

Na suíte comum, observei 200 testes aprovados, a regressão opt-in pulada e uma falha em `tests/test_run_sample.py:60`, pois `scripts/run_sample.py:292-293` escolhe `/var/tmp`. Esse teste passou isoladamente quando redirecionei a pasta temporária para `/tmp` dentro do processo do pytest.

## Causa raiz

`lib/pdfcheck/checks.py:43` roda `page.dedupe_chars()` em toda página para checar sobreposição. `lib/pdfcheck/checks.py:27` repete a operação ao extrair as linhas para duplicação, paginação e sumário. As quatro checagens consumiram 214,728 dos 215,898 s. A de sobreposição foi a mais cara (39% do total), incluiu o primeiro parse das páginas e ainda comparou caixas de letras.

O custo que domina o conjunto está em `pdfplumber/utils/text.py:819`, na versão instalada. Após agrupar os caracteres, `sorted(deduped, key=chars.index)` chama `list.index` uma vez por caractere preservado. Cada chamada procura a posição por comparação linear desde o começo da lista. Com a maioria dos caracteres preservada, essa etapa custa O(n²) por página e é repetida pelas quatro checagens. Em uma segunda execução instrumentada sobre as 44 páginas, as chamadas a `Page.dedupe_chars` consumiram 30,766 dos 37,546 s (82%). Foram 44 chamadas em sobreposição, 44 em duplicação, 46 em paginação (duas extras para achar o primeiro fólio) e 44 em sumário. O tempo da primeira checagem inclui o parse disparado por `page.objects`.

Para separar o parse dos laços, medi as páginas 14 a 19 do PDF de 300 páginas, com 1.809 a 1.846 caracteres e `page.chars` materializado antes do relógio. O `cProfile` registrou 2,352 s em `check_overlaps`, 0,666 s de tempo próprio em `sorted` e 364.722 chamadas a `_inter` (0,645 s cumulativos) no laço de pares em `checks.py:46-53`. Esse laço explica custo adicional da sobreposição. Para testar a hipótese da deduplicação, chamei a função instalada nas mesmas seis páginas, substituindo só a implementação de `index` por um mapa de posições por identidade. Em cada variação, as listas de identidades selecionadas foram iguais, na mesma ordem.

| Proporção dos caracteres de cada página | Caracteres na primeira página | `list.index` (s) | Mapa de posições (s) |
| --- | ---: | ---: | ---: |
| 25% | 462 | 0,048 | 0,011 |
| 50% | 923 | 0,179 | 0,020 |
| 100% | 1.846 | 0,699 | 0,044 |

Lição do diagnóstico. Em páginas densas, meça separadamente deduplicação e comparação de caixas, com o parse fora da medição, antes de alterar a geometria.

## Chamadores

```bash
git grep -n -e 'dedupe_chars' -e '_lines(' -e 'check_overlaps' -e 'check_duplicates' -e 'check_page_numbers' -e 'check_toc' -e 'free_space(' -e 'check_layout' -- '*.py'
```

| Resultado do rastreamento | Impacto |
| --- | --- |
| `skills/diagramador/scripts/check_layout.py:14-16,34-36` | `check_overlaps` chama a deduplicação diretamente. `check_duplicates` chama via `_band_lines` e `_lines`. `check_page_numbers` e `check_toc` chamam via `_lines`. Zona de segurança, fontes, camada de texto, tamanho de página e imagens não passam pelo laço da deduplicação. |
| `scripts/run_sample.py:200,226` e `skills/diagramador/SKILL.md:24` | O ensaio roda a CLI duas vezes, na composição e depois da inserção. O fluxo manual do Diagramador também chama a CLI. Ambos sofrem do atraso. |
| `lib/pdfcheck/checks.py:275,316,323,342` | `free_space` passa por `_band_lines` em toda página e, nas candidatas, também por `_chapter_opening`. Ambos chamam `_lines` e pagam pela deduplicação. |
| `skills/imagens/scripts/free_space.py:18`, `skills/diagramador/scripts/insert_images.py:46,85` e `scripts/run_sample.py:209,216` | Os fluxos de medir espaço e inserir imagens herdam o custo de `free_space`. |
| `skills/diagramador/scripts/pdfcheck/checks.py` e `skills/imagens/scripts/pdfcheck/checks.py` | Ambas as cópias geradas tinham o mesmo código da fonte. São as cópias usadas pelas CLIs. A skill do Auditor Gráfico prevista na spec ainda não existe neste SHA. |
| `tests/test_checks_text.py`, `tests/test_checks_layout.py`, `tests/test_checks_duplicates_noise.py`, `tests/test_check_toc_titles.py`, `tests/test_template.py` | Chamam as funções da biblioteca sobre PDFs pequenos. Exercitam os caminhos afetados, com tempo absoluto baixo. |
| `tests/test_check_layout.py`, `tests/test_free_space_cli.py`, `tests/test_insert_images.py` e `tests/test_check_layout_perf.py` | Passam pelas CLIs ou pela inserção. Só a regressão opt-in usa o volume que faz o custo aparecer. `tests/test_run_sample.py` substitui as chamadas de processo por respostas de teste. |
| `skills/diagramador/scripts/extract_pdf.py:91,98` | Usa `extract_text_lines` diretamente e não chama `dedupe_chars`. |

## Correção sugerida

Centralizar a página deduplicada em `lib/pdfcheck/checks.py` e usar um índice por identidade para a restauração de ordem. O diff mantém o agrupamento do pdfplumber, a tolerância padrão e a seleção do caractere que representa cada grupo. A página filtrada conserva a ordem original, da qual a checagem de kerning depende, e preserva objetos que não são caracteres.

```diff
--- a/lib/pdfcheck/checks.py
+++ b/lib/pdfcheck/checks.py
@@ -9,0 +10 @@
+from pdfplumber.utils import dedupe_chars
@@ -24,0 +26,15 @@
+class _IndexedChars(list):
+    def __init__(self, chars):
+        super().__init__(chars)
+        self._positions = {id(char): i for i, char in enumerate(chars)}
+
+    def index(self, char):
+        # pdfplumber usa index para restaurar a ordem dos objetos selecionados.
+        return self._positions[id(char)]
+
+
+def _deduped_page(page):
+    kept = {id(char) for char in dedupe_chars(_IndexedChars(page.chars))}
+    return page.filter(lambda obj: obj["object_type"] != "char" or id(obj) in kept)
+
+
@@ -27 +43 @@
-    return page.dedupe_chars().extract_text_lines(y_tolerance=1, return_chars=return_chars)
+    return _deduped_page(page).extract_text_lines(y_tolerance=1, return_chars=return_chars)
@@ -43 +59 @@
-        chars = [c for c in page.dedupe_chars().chars if c["text"].strip() and _area(c) > 0]
+        chars = [c for c in _deduped_page(page).chars if c["text"].strip() and _area(c) > 0]
```

Em uma cópia temporária com esse diff, as nove checagens das 300 páginas levaram 113,135 s (47,6% a menos), com saída 0 e os mesmos 57 avisos no perfil. A sobreposição continuou sendo a maior fatia, com 92,162 s naquela execução. No mesmo PDF de 44 páginas, a CLI instrumentada levou 37,546 s na base e 20,766 s na cópia, com relatórios idênticos byte a byte. Fixei o limite do teste em 24 s para acomodar a variação observada entre execuções. Com esse limite, o teste na cópia passou em 12,03 s, incluindo a composição.

O índice funciona porque o pdfplumber 0.11.10 chama o método `index` da lista recebida e conserva a identidade dos caracteres. Na atualização da dependência, confirme a seleção e a ordem dos caracteres, sobretudo negrito simulado, sobreposição real, rotação e páginas sem camada de texto.

## Critério de aceite do cartão

- Incluir `tests/test_check_layout_perf.py` e passar em `EDITORIAL_PERF=1 uv run --locked pytest -q tests/test_check_layout_perf.py`. A CLI deve produzir o relatório completo com saída 0 em menos de 24 s no PDF de 44 páginas desta máquina. O limite mede só a checagem e a execução sem a variável deve pular esse teste.
- Rodar `uv run --locked python scripts/package.py --sync` após mudar a fonte e verificar com `uv run --locked python scripts/package.py --check`.
- Passar a suíte usual e repetir o perfil das 300 páginas com as nove checagens, os mesmos achados e tempo total abaixo dos três minutos do relato.
