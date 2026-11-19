# Diagnóstico: imagens, duplicação e tempo de inserção no ensaio 3.8 (Preenchedores)

Data: 19/11/2026. Worktree de depuração `/var/tmp/editorial-wt/dbg-c` (HEAD `393554c`). Sem trecho do livro neste arquivo.

## Relato

No ensaio 3.8 (`docs/medicoes/2026-11-ensaio-preenchedores.md`), a composição do livro de Preenchedores sai com:

1. `image-low-resolution`: 30 erros e 3 avisos. A figura é esticada à largura da coluna.
2. `duplicate-paragraph`: 19 erros, com a hipótese fraca de que o cabeçalho corrido entra na comparação.
3. `insert_images.py` recompõe o livro inteiro a cada imagem candidata e, com 50 candidatas, passou de 8 min.

Esperado: imagem herdada no tamanho do original (vira aviso, spec seção 8.2); nenhuma duplicação falsa; inserção que cabe no teto do ensaio, com a mesma garantia de paginação e âncoras iguais (plano, cartão 3.x, `insert_images.py`).

## Reprodução

Livro real, na máquina Linux, com saída em `/var/tmp/dbg-c-work`:

| Passo | Comando | Resultado |
|---|---|---|
| Extração | `extract_pdf.py` + `fill_metadata` do `run_sample.py` | 6,4 s, 34 arquivos (33 figuras e o `origem.json`) |
| Composição v1 | `build_book.py m/manuscrito.md --out v1` | 7,3 s, 117 páginas, 737 blocos, 175 MB de pico |
| Checagem | `check_layout.py v1/livro.pdf --inherited .../origem.json` | os mesmos 30 erros e 3 avisos de imagem e 19 de duplicação do relatório |
| Uma composição | `HTML(...).render()` e `write_pdf()` do v1 | render 2,9 a 3,2 s; `write_pdf` 2,1 s |
| Inserção, 10 candidatas | `insert_images.py ... img10` | 103 s (cerca de 8,6 s por recomposição), 9 inseridas |
| Inserção, 50 candidatas | `insert_images.py ... img50` | código atual: interrompido pelo PID com 2 min 29 s ou mais, sem terminar (projeção: 50 × 8,6 s ≈ 7 min); com a hipótese: 43,7 s, 49 inseridas, nenhuma retirada |

Testes que falham, sem PDF real (manuscrito e PDF sintéticos gerados no teste):

- `tests/test_figure_resolution.py`: 2 falhas (67,9 ppi efetivos na figura herdada de 444 px a 136 ppi, o mesmo valor da página 17 do livro; 137,7 ppi na figura nova de 900 px).
- `tests/test_checks_duplicates_noise.py`: 2 falhas (cabeçalho corrido mais abertura igual: páginas 2, 3 e 4 acusadas; pontilhado do sumário: página 1 acusada).
- `tests/test_insert_images_renders.py`: 1 falha (6 composições para 5 imagens que cabem).

## Defeito 1: figura esticada à largura da coluna

**Causa raiz:** `skills/diagramador/assets/livro.css:98`, `figure img { width: 100%; }`. Toda figura do manuscrito, gerada em `skills/diagramador/scripts/build_book.py:60` sem tamanho próprio, ocupa a largura útil da página (210 − 22 − 22 mm = 470,6 pt). Uma figura de 444 px passa a 444 / 470,6 × 72 = 67,9 ppi, contra 136 ppi no original. O `check_images` só rebaixa para aviso a imagem herdada mantida a 95% do ppi de origem ou mais (`lib/pdfcheck/checks.py:176-178`), e por isso a ampliação vira erro abaixo de 150 ppi. Os 3 avisos atuais são as figuras que, por acaso, ficaram com 95% do ppi de origem ou mais. Sem o `width: 100%`, o WeasyPrint usaria 96 dpi (1 px = 0,75 pt, `image_resolution` padrão de 1 dppx), e a maioria continuaria abaixo de 150 ppi: só tirar a regra não basta.

**Prova da hipótese** (cópia em `/var/tmp/dbg-c-work/hyp1`, fora do repositório): `figure img { max-width: 100%; }` e a figura com `width` em pt igual a `pixels / ppi × 72`, sendo o ppi o do `origem.json` ao lado da imagem ou, sem ele, o `error_ppi` das regras (150). Resultado: os 2 testes novos e os 14 de `test_build_book.py` e `test_insert_images.py` passam. No livro real, os erros `image-low-resolution` caem de 30 para 0, e os avisos ficam em 32: a lista de imagens herdadas abaixo de 300 ppi para a Paula, como a spec prevê. O livro passa de 117 para 98 páginas, porque as figuras voltam ao tamanho do original.

**Chamadores** (`git grep -n "figure img\|<figure\|_render(\|build(" -- ':!docs'`):

- `build_book.py:60` (`_render`, ramo `figure`): o único ponto que gera a figura do manuscrito; chamado por `_render` recursivo (quadros, linha 52) e por `_compose` (linha 77). É o ponto por onde todos passam.
- `build_book.build` (linha 96): chamada por `build_book.main` (linha 125), `insert_images.insert` (linha 82), `scripts/run_sample.py` (por subprocesso) e os testes. Todos herdam a correção.
- `insert_images._figure` (linha 51): a figura complementar já usa `width:auto;max-width:100%;max-height` em estilo próprio, que vale mais que a regra do CSS. Não sofre do defeito, e trocar `width: 100%` por `max-width: 100%` não a afeta.
- `tests/samples/amostra.html:69`: amostra estática, não passa pelo `build_book`.
- `extract_pdf.py:205` grava o `origem.json` na pasta das figuras; `check_layout.py --inherited` o lê. O formato não muda.

**Correção sugerida** (mínima, no ponto compartilhado):

```diff
--- a/skills/diagramador/assets/livro.css
-figure img { width: 100%; }
+figure img { max-width: 100%; }
--- a/skills/diagramador/scripts/build_book.py
+def _figure_width_pt(image: Path, min_ppi: float) -> float:
+    """Largura natural da figura: o ppi do original (origem.json ao lado dela) ou, sem ele, o mínimo das regras."""
+    origin = image.parent / "origem.json"
+    entry = json.loads(origin.read_text(encoding="utf-8")).get(image.name, {}) if origin.is_file() else {}
+    with Image.open(image) as picture:
+        return picture.width / entry.get("ppi", min_ppi) * 72
 ...
-        return (f'<figure id="{block.id}"><img src="{_url(image, out_dir)}" alt="{e(block.text)}">'
+        width = _figure_width_pt(image, load_rules().error_ppi)
+        return (f'<figure id="{block.id}"><img src="{_url(image, out_dir)}" style="width:{width:.1f}pt" alt="{e(block.text)}">'
```

`load_rules` entra com o mesmo `try/except ImportError` do `insert_images.py` (cópia `pdfcheck` na skill, `lib.pdfcheck` no repositório), e `Image` vem do Pillow, que já é dependência do WeasyPrint. O `max-width: 100%` continua limitando a figura grande à coluna.

## Defeito 2: duplicação falsa

**Os 19 achados**, classificados por `/var/tmp/dbg-c-work/dups.py`, que refaz as janelas de 100 caracteres do `check_duplicates` e marca as que tocam a faixa de cabeçalho ou rodapé (26 mm em cima, 24 mm embaixo):

| Grupo | Achados | Páginas (v1) | Causa |
|---|---|---|---|
| Pontilhado do sumário gerado | 12 | 3 a 7 (3←3, 4←3, 4←4, 5←3, 5←4, 5←5, 6←3, 6←4, 6←5, 6←6, 7←3, 7←6) | `leader(".")` (`livro.css:59`) desenha até 167 pontos seguidos. Janelas feitas só de pontos (ou de uma letra e 99 pontos) se repetem em todas as entradas. |
| Cabeçalho corrido | 3 | 89←84, 93←84, 97←84 | Todas as janelas começam no cabeçalho corrido ("CLINIC EDITORA" e o título) e seguem por uma abertura de página igual, mais curta que 100 caracteres. Nenhuma janela só de corpo se repete. |
| Repetição real do conteúdo | 4 | 58←57, 74←73, 107←106, 117←116 | Trechos do corpo com mais de 100 caracteres que aparecem 2 vezes no PDF original: perguntas frequentes e textos de quadro repetidos, e nas referências a mesma fonte do aprofundamento. |

No PDF original, o `check_duplicates` acusa 6 achados (42←41, 55←54, 56←43, 64←62, 75←74, 76←43). Cinco são a mesma repetição real de conteúdo; um (64←62) é de faixa.

A hipótese do relatório explica só 3 dos 19. A maior parte (12) vem do pontilhado do sumário que o próprio `build_book` gera.

**Causa raiz:** `lib/pdfcheck/checks.py:93`. O texto da página é montado com todas as linhas (`_lines(page)`), inclusive as da faixa de cabeçalho e rodapé, e sem tirar o pontilhado de guia. O `free_space` (`checks.py:302-311`) já separa o texto corrido das faixas com `_running_lines`, mas o `check_duplicates` não usa isso.

**Prova da hipótese** (cópia em `/var/tmp/dbg-c-work/hyp2`): o `check_duplicates` passa a usar as linhas de `_band_lines` (a montagem de páginas extraída do `free_space`), sem as de `_running_lines`, e troca `[.·…]{3,}` por espaço. Resultado: os 2 testes novos passam, e os 48 de `test_checks_text.py`, `test_checks_layout.py` (com 19 de `free_space`) e `test_checks_duplicates_noise.py` também. No livro composto, os achados caem de 19 para 4: exatamente os 4 de repetição real. No original, caem de 6 para 5.

**Chamadores** (`git grep -n "check_duplicates\|free_space(\|_running_lines" -- ':!docs'`):

- `skills/diagramador/scripts/check_layout.py:15` (lista `CHECKS`), com a cópia `skills/diagramador/scripts/pdfcheck/`. Sofre do defeito.
- `skills/imagens/scripts/pdfcheck/checks.py`: cópia sincronizada. Não chama `check_duplicates`, mas recebe a refatoração do `free_space`.
- `free_space` (se a montagem das linhas for extraída): `insert_images.py:46`, `skills/imagens/scripts/free_space.py:18`, `tests/test_checks_layout.py` (19 chamadas). O comportamento não muda; os testes passam na cópia.
- `tests/test_checks_text.py` (linhas 39, 80, 86-87, 91, 101): continuam passando.
- `scripts/run_sample.py:101`: a hipótese em `CAUSES["duplicate-paragraph"]` deve citar também o pontilhado.

**Correção sugerida:**

```diff
--- a/lib/pdfcheck/checks.py
 _MIN_PARAGRAPH = 100  # caracteres
+_LEADER = re.compile(r"[.·…]{3,}")  # pontilhado do sumário
 ...
 def check_duplicates(pdf, rules: Rules) -> list[Finding]:
     ...
+    pages = _band_lines(pdf, rules)
+    running = _running_lines(pages)  # cabeçalho e rodapé corridos não são parágrafo
     for page in pdf.pages:
-        text = " ".join(" ".join(l["text"] for l in _lines(page)).split()).casefold()
+        kept = (l["text"] for l, _, _ in pages[page.page_number] if id(l) not in running)
+        text = _LEADER.sub(" ", " ".join(" ".join(kept).split()).casefold())
 ...
+def _band_lines(pdf, rules: Rules) -> dict:
+    """Página -> [(linha, texto normalizado, está na faixa de cabeçalho ou rodapé)]."""
+    (o laço que hoje abre o free_space, sem mudança)
+
 def free_space(pdf, rules: Rules) -> list[FreeSpace]:
-    (laço que monta pages)
+    pages = _band_lines(pdf, rules)
     running = _running_lines(pages)
```

Depois, `uv run python scripts/package.py --sync` e `--check` para as cópias em `skills/*/scripts/pdfcheck/`.

Os 4 achados restantes são repetição que já existe no original. Não são defeito de código: viram decisão editorial (a Paula corta a repetição ou o trecho entra em `allowed_repeats`).

## Defeito 3: uma recomposição por imagem candidata

**Medida:** cada recomposição custa cerca de 5 s de WeasyPrint (render de 2,9 a 3,2 s e `write_pdf` de 2,1 s) e, no fluxo real com imagens, cerca de 8,6 s. Com 10 candidatas, foram 103 s; com 50, o código atual não terminou em 2 min 29 s e foi interrompido (projeção: cerca de 7 min).

**Causa raiz:** `skills/diagramador/scripts/insert_images.py:106-115`. O laço compõe o livro uma vez por imagem do plano (`_render` em `_place(base_html, trial)`, linha 109) e mais uma no fim (linha 115): N + 1 composições, além da do `build()`. O teste `test_insert_images_renders.py` conta 6 composições para 5 imagens que cabem todas.

**Por que compor uma vez preserva a garantia:** a imagem da página p entra depois do último bloco que começa em p. Ela só pode mudar a página dos blocos de p em diante. A garantia da spec (plano, `insert_images.py`: "recompõe e confere que o número de páginas e a página de cada bloco não mudaram; se mudaram, tira a imagem daquela página e avisa") é conferida no PDF final, que é o mesmo que sai. Compor com todas as imagens, conferir e, se algo mudou, tirar a imagem da primeira página afetada e recompor mantém a conferência integral. No caso comum, é uma composição em vez de N + 1; no pior caso, continua N + 1.

**Prova da hipótese** (cópia em `/var/tmp/dbg-c-work/hyp3`): o laço passa a compor com todas e, a cada desvio, tira uma imagem, a mais tardia até a primeira página afetada. Uma âncora que saiu da página n culpa uma imagem antes de n; a figura fora da página dela culpa a própria. Os 7 testes de `test_insert_images.py` passam, inclusive `test_earlier_image_does_not_discard_later_one` (a imagem que estoura sai e a seguinte fica), e também o teste novo (1 composição). No livro real, com 50 candidatas: 43,7 s, 49 inseridas e nenhuma retirada. A paginação e as âncoras finais não foram conferidas contra o v1 nesta rodada.

**Chamadores** (`git grep -n "insert_images\|_render(" -- ':!docs'`):

- `insert_images.main` (linha 125), `scripts/run_sample.py:166` (subprocesso; hoje limita a 3 imagens por `MAX_IMAGES`, o atalho que existe por causa deste defeito), `skills/imagens/SKILL.md` e `skills/diagramador/SKILL.md` (fluxo documentado) e `tests/test_insert_images.py`.
- `insert_images._render` só é chamado dentro de `insert`. `build_book.build` tem a própria composição e não muda.

**Correção sugerida:**

```diff
--- a/skills/diagramador/scripts/insert_images.py
-    accepted: dict[int, tuple[str, str]] = {}
-    for page in sorted(plan):  # uma por vez: a que estoura sai, as seguintes são avaliadas sobre as aceitas
-        trial = {**accepted, page: plan[page]}
-        layout, pages = _render(_place(base_html, trial), out)
-        if layout.get(f"comp-{page:02d}") == page and pages == base.pages \
-                and all(layout.get(i) == n for i, n in base.layout.items()):
-            accepted = trial
-        else:
-            warnings.append(f"página {page}: a imagem mudaria a paginação; foi retirada")
-    layout, pages = _render(_place(base_html, accepted), out)
+    accepted = dict(plan)
+    while True:  # compõe com todas; se algo mudou, tira a imagem da primeira página afetada e recompõe
+        layout, pages = _render(_place(base_html, accepted), out)
+        # âncora que saiu da página n: culpa de imagem antes de n; figura fora da página dela: culpa dela;
+        # página a mais ou a menos: culpa da última imagem
+        broken = [n - 1 for i, n in base.layout.items() if layout.get(i) != n]
+        broken += [p for p in accepted if layout.get(f"comp-{p:02d}") != p]
+        broken += [base.pages] if pages != base.pages else []
+        if not broken or not accepted:
+            break
+        culprit = max((p for p in accepted if p <= min(broken)), default=min(accepted))
+        del accepted[culprit]
+        warnings.append(f"página {culprit}: a imagem mudaria a paginação; foi retirada")
     plan = accepted
```

Depois da correção, o `MAX_IMAGES = 3` de `scripts/run_sample.py:23` pode subir para todas as candidatas. Isso é outro cartão, com nova medição.

## Critério de aceite do cartão

- Defeito 1: `uv run --locked pytest tests/test_figure_resolution.py tests/test_build_book.py tests/test_insert_images.py -q` passa; no ensaio, `image-low-resolution` sem erro.
- Defeito 2: `uv run --locked pytest tests/test_checks_duplicates_noise.py tests/test_checks_text.py tests/test_checks_layout.py tests/test_free_space_cli.py -q` passa e `uv run --locked python scripts/package.py --check` sai com 0; no ensaio, `duplicate-paragraph` cai para os 4 de repetição real.
- Defeito 3: `uv run --locked pytest tests/test_insert_images_renders.py tests/test_insert_images.py -q` passa; no ensaio com as 50 candidatas, paginação e âncoras iguais e o tempo medido.
