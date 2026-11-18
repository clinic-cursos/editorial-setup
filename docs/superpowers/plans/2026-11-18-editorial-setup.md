# Setup editorial V1 da Clinic Editora: plano

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** construir o time editorial (seis papéis) como skills de fonte única, com os scripts de checagem de PDF, a diagramação por HTML e WeasyPrint e o empacotamento para ChatGPT, claude.ai, Claude Code e Codex.

**Architecture:** cada papel é uma pasta em `skills/` no padrão Agent Skills; o código comum de PDF fica em `lib/pdfcheck/` e as referências comuns em `shared/`, e o `scripts/package.py` copia os dois para dentro de cada skill (cópia versionada, conferida contra deriva). O repositório é o próprio plugin do Claude Code e do Codex; os zips do ChatGPT e do claude.ai saem em `dist/`.

**Tech Stack:** Python 3.12 com `uv`; pdfplumber, pypdf, WeasyPrint, ReportLab (só nos testes, para gerar PDFs sintéticos); pytest; padrão Agent Skills; manifestos `.claude-plugin/` e `.codex-plugin/`.

**Spec:** `/home/alify/projetos/clinic-cursos/editorial-setup/docs/superpowers/specs/2026-11-18-editorial-setup-design.md` (aprovada pelo Alify em 18/11/2026: forma A e "pode criar esse repo do setup editorial, com os agentes e tudo mais").

**Issue:** CLI-514 https://linear.app/clinic-cursos/issue/CLI-514

## Global Constraints
- Skill: `name` com 1 a 64 caracteres, só `[a-z0-9-]`, sem hífen no início, no fim ou duplo, igual ao nome da pasta, sem `claude` nem `anthropic`; `description` de 1 a 1.024 caracteres; `SKILL.md` com menos de 500 linhas; pastas `references/`, `scripts/`, `assets/`.
- Nenhuma pasta `bin/` no topo do repositório.
- Bibliotecas permitidas nos scripts das skills: biblioteca padrão, pdfplumber, pypdf, WeasyPrint, python-docx; python-pptx só se um cartão pedir. PyMuPDF proibido (AGPL). ReportLab só em `tests/`.
- Idioma: `SKILL.md`, referências, guias e mensagens para a Paula em português; código, nomes de função, chaves de JSON e commits em inglês. Nomes de skill e de agente em português sem acento: `editor-chefe`, `editor-cientifico`, `auditor-cientifico`, `diagramador`, `imagens`, `auditor-grafico`.
- Fontes da marca: Montserrat (títulos) e Source Sans 3 (texto), licença OFL, com o arquivo de licença junto.
- Paleta das imagens complementares: bordô, rosa claro, marsala, cinza; estilo conceitual e clean; sem texto dentro da imagem.
- Valores provisórios (a confirmar com a Paula, num arquivo só, `shared/rules/graphic-rules.json`): espaço livre que pede imagem 0,25 da altura útil; imagem nova ou ampliada é erro abaixo de 150 ppi e aviso abaixo de 300 ppi; imagem herdada do original é sempre aviso; zona de segurança de 10 mm da borda da página.
- Fidelidade do texto: saída igual à entrada em pelo menos 0,995 dos caracteres, sem cabeçalho, rodapé e número de página.
- Nada de conteúdo de livro, foto clínica ou dado de aluno no git. Livros reais vêm de `EDITORIAL_SAMPLES_DIR`.
- Sem travessão em nenhum texto entregue.

## Review Focus
1. PDF com página sem camada de texto (página escaneada ou só imagem): a checagem marca `page-without-text` como aviso e segue, sem quebrar nem passar em silêncio. Teste no cartão 1.2.
2. Nome de fonte com prefixo de subconjunto (`ABCDEF+SourceSans3-Roman`) ou fonte Type3 sem nome: a checagem normaliza o prefixo e trata fonte sem nome como aviso, não como erro. Teste no cartão 1.2.
3. Texto com acento, ligadura (`ﬁ`), hífen de quebra de linha e hífen suave: a fidelidade normaliza (NFC, ligaduras, hifenização de fim de linha) antes de comparar, para não reprovar texto igual. Teste no cartão 3.2.
4. Imagem girada ou recortada por máscara: a resolução usa o tamanho exibido na página, e recorte não conta como distorção. Teste no cartão 1.3.
5. Página em branco proposital (verso de abertura) e página de abertura de capítulo: não entram como candidatas a imagem complementar. Teste no cartão 1.3.

## Convenções
- Repositório: `clinic-cursos/editorial-setup`, checkout `/home/alify/projetos/clinic-cursos/editorial-setup`, base `main`. `git` e `gh` com `GH_TOKEN=$(gh auth token --user fde1-clinic)`.
- **Formato que a ponte lê ao pé da letra:** "Arquivos permitidos" e "Verificação" vão sem crases; "Arquivos permitidos" separado por vírgula e espaço; a "Verificação" é um comando só, em /bin/sh, na worktree, depois do commit, com teto de 10 minutos, e sai com 0 quando o critério passa.
- Campos fixos de todo cartão: `Issue: CLI-514 https://linear.app/clinic-cursos/issue/CLI-514`, `Repositório: /home/alify/projetos/clinic-cursos/editorial-setup`, `Base: main`, `Risco: normal`, `Requer:` vazio salvo indicação, `Executor:` vazio, `Spec/plano:` o caminho absoluto da spec. Cada cartão abaixo traz só os campos que variam.
- Testes: `uv run --locked pytest`. PDFs, imagens e capítulos de teste são gerados por código em `tests/conftest.py` (ReportLab), sem binário no git.
- Cartão `manual` é feito por uma pessoa e registrado em `docs/medicoes/`; a sessão de execução não o despacha.
- Interface da linha de comando dos scripts: código de saída 0 sem erro, 1 com erro encontrado, 2 com uso errado ou arquivo ilegível.

## Interfaces comuns (definidas nos cartões 1.1 a 1.3, usadas pelos seguintes)
- `lib/pdfcheck/model.py`:
  - `Finding(page: int, kind: str, severity: Literal["error", "warning"], detail: str, bbox: tuple[float, float, float, float] | None = None)` (dataclass, `page` começa em 1).
  - `Report(pdf: str, pages: int, findings: list[Finding])` com `errors() -> list[Finding]`, `to_json() -> str`, `to_markdown() -> str` (tabela em português por página).
  - `FreeSpace(page: int, x0: float, top: float, x1: float, bottom: float, fraction: float)`.
- `lib/pdfcheck/rules.py`: `Rules` (dataclass) com `allowed_fonts: list[str]`, `safe_zone_mm: float`, `error_ppi: int`, `warning_ppi: int`, `free_space_fraction: float`, `distortion_tolerance: float`; `load_rules(path: str | None = None) -> Rules`, que lê `shared/rules/graphic-rules.json` quando `path` é `None`.
- `lib/pdfcheck/checks.py` (cada função recebe `pdf: pdfplumber.PDF` e `rules: Rules`): `check_overlaps`, `check_safe_zone`, `check_duplicates`, `check_fonts`, `check_text_layer` (cartão 1.2); `check_images(pdf, rules, inherited: set[str] | None = None)`, `check_page_numbers`, `check_toc`, `free_space(pdf, rules) -> list[FreeSpace]` (cartão 1.3). Todas devolvem `list[Finding]`, salvo `free_space`.
- Tipos de achado (`kind`): `overlap`, `outside-safe-zone`, `duplicate-paragraph`, `font-not-allowed`, `font-unnamed`, `page-without-text`, `image-low-resolution`, `image-distorted`, `page-number`, `toc-mismatch`.

## Ondas
Ordem: onda 1, depois as ondas 2 e 3 (podem correr em paralelo), depois 4, 5 e 6. O cartão 1.5 (teste do ChatGPT, manual) precisa ficar pronto antes do cartão 3.4.

### Onda 1: base, checagem de PDF e teste de plataforma

#### Cartão 1.1: Base do repositório e validação das skills
Função: backend
Objetivo: criar a base Python do repositório e o `scripts/package.py` no modo de validação e de cópia das partes comuns.
Arquivos permitidos: pyproject.toml, uv.lock, .gitignore, .python-version, AGENTS.md, CLAUDE.md, scripts/package.py, lib/__init__.py, lib/pdfcheck/__init__.py, shared/README.md, tests/__init__.py, tests/test_package.py, tests/fixtures_skills/**
Critérios de aceite:
- `pyproject.toml` com dependências pdfplumber, pypdf, weasyprint e, no grupo de desenvolvimento, pytest e reportlab; `uv.lock` gerado.
- `.gitignore` com `dist/`, `.venv/`, `__pycache__/`.
- `AGENTS.md` com as regras do time (governança da seção 2 da spec, idioma, nada de conteúdo de livro no git); `CLAUDE.md` com uma linha que aponta para o `AGENTS.md`.
- `package.py --check` valida cada pasta de `skills/` (regras de nome, `description`, linhas do `SKILL.md`, ausência de `bin/` no topo) e confere que as cópias de `lib/pdfcheck/` e de `shared/` dentro de cada skill são iguais às originais; sai com 1 e lista cada problema.
- `package.py --sync` copia `lib/pdfcheck/` para `skills/<skill>/scripts/pdfcheck/` (só nas skills que têm `scripts/`) e `shared/references/` e `shared/rules/` para `skills/<skill>/references/comum/`.
- Testes: `test_valid_skill_passes`, `test_name_with_claude_fails`, `test_description_over_1024_fails`, `test_skill_md_500_lines_fails`, `test_top_level_bin_fails`, `test_drifted_copy_fails` (usam skills de exemplo em `tests/fixtures_skills/`).
Verificação: uv run --locked pytest tests/test_package.py -q

#### Cartão 1.2: Checagens de texto e fonte do PDF
Função: backend
Objetivo: implementar o modelo de achados, as regras e as checagens de sobreposição, zona de segurança, duplicação, fonte e camada de texto.
Arquivos permitidos: lib/pdfcheck/model.py, lib/pdfcheck/rules.py, lib/pdfcheck/checks.py, shared/rules/graphic-rules.json, tests/conftest.py, tests/test_checks_text.py
Critérios de aceite:
- `graphic-rules.json` com os valores provisórios das Global Constraints e `allowed_fonts: ["Montserrat", "SourceSans3", "SourceSansPro"]`.
- `tests/conftest.py` gera, com ReportLab, PDFs A4 sintéticos: limpo; com duas linhas sobrepostas; com texto a 5 mm da borda; com um parágrafo de 120 caracteres repetido; com Helvetica no corpo; com uma página só de imagem.
- Testes: `test_clean_pdf_has_no_errors` (`errors() == []`), `test_overlap_detected` (um `overlap` na página certa), `test_safe_zone_detected`, `test_duplicate_paragraph_detected`, `test_font_not_allowed_detected` (`font-not-allowed` com `Helvetica` no `detail`), `test_subset_prefix_normalized` (nome `ABCDEF+SourceSans3-Roman` não gera achado), `test_unnamed_font_is_warning`, `test_page_without_text_is_warning`.
- Sobreposição: caixas de linhas de texto de blocos diferentes que se cruzam em mais de 1 pt nos dois eixos; letras repetidas no mesmo lugar (texto em negrito simulado) não contam, usando `dedupe_chars`.
Verificação: uv run --locked pytest tests/test_checks_text.py -q

#### Cartão 1.3: Checagens de imagem, paginação, sumário e espaço livre
Função: backend
Objetivo: completar `checks.py` com resolução e distorção de imagem, número de página, sumário e medição de espaço livre.
Arquivos permitidos: lib/pdfcheck/checks.py, tests/conftest.py, tests/test_checks_layout.py
Critérios de aceite:
- PPI efetivo = largura da imagem em pixels ÷ (largura exibida em pt ÷ 72), pelo menor dos dois eixos. Imagem com nome em `inherited` é sempre `warning`; as demais são `error` abaixo de `error_ppi` e `warning` abaixo de `warning_ppi`.
- Distorção: proporção exibida difere da proporção em pixels em mais de `distortion_tolerance` (0,02); imagem girada usa a matriz de transformação; imagem recortada por máscara não conta.
- `check_page_numbers`: o número impresso no rodapé segue a sequência; falta ou salto vira `page-number`.
- `check_toc`: cada entrada do sumário (linha com título e número no fim) aponta para a página onde o título aparece; diferença vira `toc-mismatch`.
- `free_space`: retângulo entre o fim do último objeto e a zona de segurança inferior, na largura útil; entra na lista quando a altura passa de `free_space_fraction` da altura útil. Página sem nenhum objeto e página cujo maior título está no terço de cima e ocupa a largura (abertura de capítulo) ficam fora.
- Testes: `test_low_ppi_new_image_is_error`, `test_low_ppi_inherited_image_is_warning`, `test_distorted_image_detected`, `test_rotated_image_not_distorted`, `test_page_number_gap_detected`, `test_toc_mismatch_detected`, `test_free_space_listed_with_fraction`, `test_blank_page_not_candidate`, `test_chapter_opening_not_candidate`.
Verificação: uv run --locked pytest tests/test_checks_layout.py -q

#### Cartão 1.4: Skill de teste de plataforma e roteiro
Função: docs
Objetivo: preparar a skill descartável e o roteiro que o Alify usa no ChatGPT da Clinic (critério 0 da spec).
Arquivos permitidos: docs/medicoes/teste-plataforma/SKILL.md, docs/medicoes/teste-plataforma/roteiro.md
Critérios de aceite:
- `SKILL.md` com `name: teste-plataforma`, que pede ao modelo: rodar no Python da conversa `import weasyprint, pdfplumber, pypdf` e `pip list`, mostrar a saída; gerar uma imagem simples; dizer se o Python enxerga o arquivo da imagem gerada (caminho e tamanho) ou não.
- `roteiro.md` em português simples, passo a passo: ligar skills no workspace (se o plano tiver), compactar a pasta em zip, enviar em Skills, abrir conversa nova, colar o pedido pronto, copiar o resultado para `docs/medicoes/2026-11-teste-chatgpt.md` no modelo que o roteiro traz (campos: plano do ChatGPT, skills disponíveis sim/não, WeasyPrint sim/não, pdfplumber sim/não, imagem gerada sim/não, Python enxerga a imagem sim/não, observações).
Verificação: grep -q "name: teste-plataforma" docs/medicoes/teste-plataforma/SKILL.md && grep -q "WeasyPrint" docs/medicoes/teste-plataforma/roteiro.md

#### Cartão 1.5 (manual, Alify): Teste no ChatGPT da Clinic
Objetivo: rodar o roteiro do cartão 1.4 e gravar `docs/medicoes/2026-11-teste-chatgpt.md`.
Critérios de aceite: arquivo gravado com todos os campos do modelo. Se o ChatGPT não tiver skills no plano, o campo diz isso e o cartão 6.1 gera a versão em Projeto como caminho principal. Se o WeasyPrint não rodar, o `guia-paula.md` (cartão 6.2) manda a diagramação para o Claude Code ou o Codex.

### Onda 2: Editor-Chefe (fase 1 da instrução da Paula)

#### Cartão 2.1: Referências comuns
Função: ai
Objetivo: escrever as referências que todos os papéis leem.
Arquivos permitidos: shared/references/governanca.md, shared/references/identidade-visual.md, shared/references/glossario.md, shared/references/manuscrito.md, shared/references/retorno.md, shared/README.md
Critérios de aceite:
- `governanca.md`: autoridade do Board, João aprova o conteúdo técnico, Paula aprova a versão e libera a impressão, nenhum agente libera impressão, versão aprovada não muda, divergência com o Board vai para avaliação humana (seções 2 e 6 da spec e seção 7 da instrução da Paula).
- `identidade-visual.md`: A4, bordô, branco e cinza, fontes da marca, componentes editoriais (Estudo e Prática, Leitura e Aprofundamento, Aplicação Clínica, Ponto-chave, Atenção, Evidência, Perguntas frequentes, legenda de antes e depois com o texto padrão, módulo de QR code), tirados do briefing e do PDF "Padrões e Pendências Visuais".
- `manuscrito.md`: convenção do manuscrito em Markdown: metadados no topo (título, curso, autores, versão), títulos `#` a `###`, blocos `:::ponto-chave`, `:::atencao`, `:::evidencia`, `:::estudo-pratica`, `:::aprofundamento`, `:::aplicacao-clinica`, `:::faq`, marca de origem `<!-- slide: N -->`, referência por chave `[@chave]` com a lista no fim, figura `![legenda](arquivo){#fig-id}`.
- `retorno.md`: bloco fixo que todo papel devolve ao Editor-Chefe (status `PRONTO`, `PRONTO_COM_RESSALVAS`, `PRECISA_DE_DADO`, `BLOQUEADO`; arquivos entregues; pendências; nota quando o papel é auditor).
Verificação: for f in governanca identidade-visual glossario manuscrito retorno; do test -s shared/references/$f.md || exit 1; done; grep -q ":::ponto-chave" shared/references/manuscrito.md

#### Cartão 2.2: Skill e agente do Editor-Chefe
Função: ai
Objetivo: escrever a skill `editor-chefe` com o fluxo, o portão de nota, a ficha e as rubricas, e a definição do agente.
Arquivos permitidos: skills/editor-chefe/**, agents/editorial/editor-chefe.md, tests/cenarios/editor-chefe.md
Critérios de aceite:
- `SKILL.md` com missão, quando acionar, entradas, processo numerado (ler a ficha, identificar a fase concluída e a próxima, delegar com pedido estruturado, receber o retorno, aplicar o portão, atualizar a ficha, preparar o pacote para a pessoa), limites e retorno, abaixo de 500 linhas.
- Portão: passa com 90 ou mais e nenhum eliminatório; até 3 voltas; na terceira reprovação entrega o melhor resultado, as notas de cada volta e as pendências; nota da fase 3 marcada "provisória: manual ausente" enquanto `diagramador/references/manual-clinic.md` disser "aguardando o manual".
- No chat sem subagente: roda os papéis em sequência e manda a auditoria científica para conversa nova, montando o "pacote de auditoria".
- `references/fluxo.md` (tabela de fases da spec, 6.1), `references/ficha-projeto.md` (todos os campos da seção 7), `references/rubricas/fase-1-ampliacao.md` e `references/rubricas/fase-3-4-diagramacao.md` (pesos e eliminatórios da seção 6.2).
- `agents/editorial/editor-chefe.md` no molde da casa: frontmatter `name`, `description`, `tools`, `model: opus`, `effort: medium`, `maxTurns: 60`, `skills: [editor-chefe]`; corpo curto que manda seguir a skill.
- `tests/cenarios/editor-chefe.md`: roteiro do critério 2 da spec (projeto de teste, delegação a um executor de teste, caso que passa com 92, caso que volta com 85, histórico completo), para rodar no Claude Code. Depois do merge, a sessão de execução roda o roteiro e grava `docs/medicoes/2026-11-ensaio-editor-chefe.md` com `Resultado: APROVADO` ou `REPROVADO`.
- `package.py --sync` rodado e cópias comuns incluídas.
Verificação: uv run --locked python scripts/package.py --check && grep -q "90" skills/editor-chefe/SKILL.md && test -s skills/editor-chefe/references/rubricas/fase-3-4-diagramacao.md

### Onda 3: Diagramador e imagens (fase 2 da instrução da Paula)

#### Cartão 3.1: Modelo visual do livro e amostra
Função: frontend
Objetivo: criar o modelo HTML e o CSS de impressão do livro, com as fontes da marca, e gerar as três páginas de amostra.
Arquivos permitidos: skills/diagramador/assets/**, tests/samples/manuscrito-amostra.md, tests/test_template.py, docs/medicoes/amostra/**
Critérios de aceite:
- `assets/livro.html` (esqueleto com capa, expediente, sumário e corpo) e `assets/livro.css` com `@page` A4, cabeçalho "CLINIC EDITORA" à esquerda e título do livro à direita, número de página no rodapé, sumário por `target-counter()`, classes dos componentes editoriais, legenda Source Sans 9 pt / 11,5 pt cinza, cores tiradas dos PDFs de referência.
- Fontes Montserrat e Source Sans 3 em `assets/fonts/` com `OFL.txt`.
- `tests/samples/manuscrito-amostra.md`: texto sintético que usa todos os blocos de `manuscrito.md`.
- `test_template_renders_with_brand_fonts`: renderiza a amostra pelo WeasyPrint e `check_fonts` não acusa nada.
- Três páginas de amostra em PNG em `docs/medicoes/amostra/` (abertura de capítulo, texto com caixas, imagem com legenda) para o cartão 3.5.
Verificação: uv run --locked pytest tests/test_template.py -q

#### Cartão 3.2: Composição do livro e fidelidade do texto
Função: backend
Objetivo: gerar HTML e PDF a partir do manuscrito, com mapa de blocos por página, e medir a fidelidade do texto.
Arquivos permitidos: skills/diagramador/scripts/build_book.py, skills/diagramador/scripts/text_fidelity.py, tests/test_build_book.py, tests/test_text_fidelity.py
Critérios de aceite:
- `build_book.py MANUSCRITO.md --out DIR` grava `DIR/livro.html`, `DIR/livro.pdf` e `DIR/layout.json`; cada bloco do HTML recebe `id` `b0001`, `b0002`...; `layout.json` mapeia `id` para a página onde o bloco começa, pelas âncoras das páginas do WeasyPrint.
- `text_fidelity.py ORIGINAL SAIDA` aceita `.md` ou `.pdf` nos dois lados, normaliza (NFC, ligaduras, hífen de fim de linha, hífen suave, espaços), descarta cabeçalho, rodapé e número de página, imprime a razão com 4 casas e sai com 1 abaixo de 0,995.
- Testes: `test_build_writes_three_files`, `test_layout_maps_every_block`, `test_fidelity_identical_is_one`, `test_fidelity_ligature_and_hyphenation_normalized`, `test_fidelity_missing_paragraph_fails`.
Verificação: uv run --locked pytest tests/test_build_book.py tests/test_text_fidelity.py -q

#### Cartão 3.3: Extração de PDF composto para manuscrito
Função: backend
Objetivo: levar livros já compostos em PDF para o manuscrito em Markdown.
Arquivos permitidos: skills/diagramador/scripts/extract_pdf.py, skills/diagramador/scripts/extract_docx.py, pyproject.toml, uv.lock, tests/test_extract_pdf.py, tests/test_extract_docx.py
Critérios de aceite:
- `extract_pdf.py PDF --out manuscrito.md --images DIR` usa o pdfplumber para texto e tamanhos de fonte e o pypdf para as imagens; títulos por tamanho e cor da fonte em relação ao corpo; rótulos em caixa alta e bordô viram títulos `###`; cabeçalho, rodapé e número de página fora; imagens salvas em `DIR` e referenciadas no lugar.
- `extract_docx.py DOCX --out manuscrito.md --images DIR` com python-docx (MIT, entra no `pyproject.toml`): títulos pelos estilos de título, parágrafos, listas e imagens; teste `test_docx_headings_recovered` num DOCX sintético.
- Testes, em PDF sintético com títulos, corpo, um rótulo e uma imagem: `test_headings_recovered`, `test_header_footer_dropped`, `test_image_extracted_and_referenced`, `test_round_trip_fidelity` (extrair, compor pelo `build_book.py` e `text_fidelity.py` passa).
Verificação: uv run --locked pytest tests/test_extract_pdf.py -q

#### Cartão 3.4: Skill e agente do Diagramador
Função: ai
Objetivo: escrever a skill `diagramador` e a definição do agente, depois do cartão 1.5.
Arquivos permitidos: skills/diagramador/SKILL.md, skills/diagramador/references/**, skills/diagramador/scripts/check_layout.py, agents/editorial/diagramador.md, tests/test_check_layout.py
Critérios de aceite:
- `SKILL.md`: entrada (manuscrito aprovado ou PDF composto), processo (extrair se for PDF, compor, rodar `check_layout.py` e `text_fidelity.py`, corrigir até zero erro, entregar), limites (não cria imagem, não altera texto aprovado sem autorização registrada na ficha), retorno no bloco de `retorno.md`. O motor no ChatGPT segue o resultado do cartão 1.5.
- `references/manual-clinic.md` com "aguardando o manual" e a lista dos padrões já conhecidos; `references/abnt.md` com NBR 6029:2023 (confirmada) e NBR 6023, 10520, 6024, 6027 e 6034 marcadas "confiança média, conferir no catálogo da ABNT", só com as regras, sem copiar a norma.
- `check_layout.py PDF` roda `check_overlaps`, `check_safe_zone`, `check_duplicates`, `check_fonts` e `check_text_layer`, imprime o relatório em Markdown e segue os códigos de saída das Convenções. Teste `test_check_layout_exit_codes` (0 no limpo, 1 no sobreposto, 2 em arquivo inexistente).
- `agents/editorial/diagramador.md`: `model: sonnet`, `effort: medium`, `maxTurns: 60`, `skills: [diagramador]`.
- `package.py --sync` rodado.
Verificação: uv run --locked pytest tests/test_check_layout.py -q && uv run --locked python scripts/package.py --check

#### Cartão 3.5 (manual, Alify ou Paula): Aprovação das páginas de amostra
Objetivo: aprovar ou pedir ajuste nas três páginas de `docs/medicoes/amostra/` (regra da casa: mudança visível só com mockup aprovado).
Critérios de aceite: `docs/medicoes/amostra/aprovacao.md` com quem aprovou, a data e os ajustes pedidos. Ajuste pedido volta ao cartão 3.1 antes do 3.7.

#### Cartão 3.6: Imagens complementares
Função: ai
Objetivo: escrever a skill `imagens`, o script de espaço livre e o script que insere a imagem sem mover o texto.
Arquivos permitidos: skills/imagens/**, skills/diagramador/scripts/insert_images.py, agents/editorial/imagens.md, tests/test_free_space_cli.py, tests/test_insert_images.py
Critérios de aceite:
- `skills/imagens/scripts/free_space.py PDF [--json OUT]` imprime a tabela de páginas candidatas (página, largura e altura em mm, proporção, fração) pela `free_space`.
- `insert_images.py MANUSCRITO.md LAYOUT.json IMAGENS_DIR --out NOVO.md`: para cada `pagina-NN.png`, põe a figura logo depois do último bloco que começa na página NN, com altura máxima igual à do espaço livre e classe `complementar`; recompõe e confere que o número de páginas e a página de cada bloco não mudaram, senão desfaz a imagem daquela página e avisa.
- `SKILL.md`: processo da seção 8.3 da spec, com a regra "sempre conceitual" (nunca anatomia, pele, procedimento, produto de marca ou resultado) e a troca por conceito mais abstrato na dúvida; briefing por página; geração pela ferramenta nativa do ambiente; no Claude, entrega só os briefings; registro de cada imagem para a ficha.
- `references/paleta.md` com os valores de cor de bordô, rosa claro, marsala e cinza tirados dos PDFs.
- `agents/editorial/imagens.md`: `model: sonnet`, `effort: low`, `maxTurns: 30`, `skills: [imagens]`.
- Testes: `test_free_space_cli_lists_candidates`, `test_insert_keeps_pagination`, `test_insert_reverts_when_page_breaks`.
- `package.py --sync` rodado.
Verificação: uv run --locked pytest tests/test_free_space_cli.py tests/test_insert_images.py -q && uv run --locked python scripts/package.py --check

#### Cartão 3.7: Ensaio com o livro de Preenchedores
Função: backend
Objetivo: rodar o fluxo do pedido da Paula no PDF real e registrar o resultado (critérios 4 e 5 da spec).
Arquivos permitidos: scripts/run_sample.py, docs/medicoes/2026-11-ensaio-preenchedores.md
Critérios de aceite:
- `run_sample.py NOME_DO_PDF` lê de `EDITORIAL_SAMPLES_DIR`, trabalha em pasta temporária fora do repositório e roda: extrair, compor, `check_layout`, `text_fidelity`, `free_space`, inserir imagens sintéticas de teste (retângulos na paleta) e conferir de novo.
- `docs/medicoes/2026-11-ensaio-preenchedores.md` com `Resultado: APROVADO` ou `REPROVADO` e os números: páginas, fontes encontradas (nenhuma DejaVu), erros por tipo, fidelidade, páginas candidatas, paginação antes e depois. Sem trecho do livro.
Verificação: test -n "$EDITORIAL_SAMPLES_DIR" && uv run --locked python scripts/run_sample.py Preenchedores_Dermicos_Consolidado_40_Alteracoes.pdf && grep -q "Resultado: APROVADO" docs/medicoes/2026-11-ensaio-preenchedores.md

### Onda 4: Editor Científico e Auditor Científico (fases 3 e 4 da instrução da Paula)

#### Cartão 4.1: Conferência de referências
Função: backend
Objetivo: conferir DOI e PMID pelas APIs gratuitas do Crossref e do PubMed.
Arquivos permitidos: skills/auditor-cientifico/scripts/verify_refs.py, tests/test_verify_refs.py
Critérios de aceite:
- `verify_refs.py REFS.json [--offline]` lê uma lista de `{key, title, authors, year, doi?, pmid?}`; consulta `https://api.crossref.org/works/{doi}` e `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json` com `urllib` e User-Agent `clinic-editorial-setup/0.1`, sem e-mail nem nome; título parecido (razão do `difflib` de 0,9 ou mais), mesmo ano, mesmo sobrenome do primeiro autor.
- Saída JSON por referência com `status`: `ok`, `divergent`, `not-found`, `unverified` (sem rede ou `--offline`); sai com 1 se houver `not-found` ou `divergent`.
- Testes com respostas HTTP simuladas: `test_matching_doi_ok`, `test_unknown_doi_not_found`, `test_title_mismatch_divergent`, `test_offline_unverified`.
Verificação: uv run --locked pytest tests/test_verify_refs.py -q

#### Cartão 4.2: Skill e agente do Editor Científico
Função: ai
Objetivo: escrever a skill `editor-cientifico` e a definição do agente.
Arquivos permitidos: skills/editor-cientifico/**, agents/editorial/editor-cientifico.md
Critérios de aceite:
- `SKILL.md`: separa as fontes A (original do Board), B (ministrado) e C (complementação), preserva a sequência didática, entrega plano de ampliação, manuscrito no formato de `manuscrito.md`, tabela slide a capítulo e tabela de rastreabilidade (afirmação, fonte, DOI ou PMID, tipo de estudo, data de consulta, limitação, trecho, estado), proíbe referência inventada e mudança silenciosa de decisão clínica do Board.
- `references/rastreabilidade.md` e `references/fontes.md` (PubMed, Crossref, OpenAlex e bases oficiais, nessa ordem de preferência).
- `agents/editorial/editor-cientifico.md`: `model: opus`, `effort: high`, `maxTurns: 80`, `skills: [editor-cientifico]`.
- `package.py --sync` rodado.
Verificação: uv run --locked python scripts/package.py --check && grep -q "slide" skills/editor-cientifico/SKILL.md

#### Cartão 4.3: Skill e agente do Auditor Científico
Função: ai
Objetivo: escrever a skill `auditor-cientifico` e a definição do agente.
Arquivos permitidos: skills/auditor-cientifico/SKILL.md, skills/auditor-cientifico/references/**, agents/editorial/auditor-cientifico.md
Critérios de aceite:
- `SKILL.md`: confere cada afirmação contra a fonte (rodando `verify_refs.py` quando há rede), coerência com o material do Board, divergências e extrapolações, informação regulatória a atualizar; relatório de não conformidades com localização, evidência e recomendação; nota pela rubrica da fase 1; não reescreve o manuscrito; separa "conferido" de "juízo do auditor".
- `references/relatorio.md` com o modelo do relatório.
- `agents/editorial/auditor-cientifico.md`: `tools` sem `Edit` nem `Write` além do relatório, `model: sonnet`, `effort: high`, `maxTurns: 60`, `skills: [auditor-cientifico]`.
- `package.py --sync` rodado.
Verificação: uv run --locked python scripts/package.py --check && grep -q "verify_refs.py" skills/auditor-cientifico/SKILL.md

#### Cartão 4.4: Ensaio científico com capítulo sintético
Função: test
Objetivo: provar o critério 6 da spec com material de teste escrito para isso.
Arquivos permitidos: tests/samples/capitulo-teste/**, tests/test_science_sample.py, docs/medicoes/2026-11-ensaio-cientifico.md
Critérios de aceite:
- `tests/samples/capitulo-teste/` com slides sintéticos em Markdown (8 slides), um manuscrito sintético com tabela slide a capítulo e lista de referências em JSON com uma referência inventada plantada.
- `test_every_slide_mapped` (nenhum slide órfão na tabela) e `test_planted_reference_flagged` (`verify_refs.py --offline` com respostas simuladas marca a plantada como `not-found`).
- `docs/medicoes/2026-11-ensaio-cientifico.md` com o resultado de uma rodada manual do Editor Científico e do Auditor Científico no Claude Code sobre esse material.
Verificação: uv run --locked pytest tests/test_science_sample.py -q

### Onda 5: Auditor Gráfico (fase 5 da instrução da Paula)

#### Cartão 5.1: Skill, agente e ensaio do Auditor Gráfico
Função: ai
Objetivo: escrever o `audit_pdf.py` completo, a skill `auditor-grafico` e a definição do agente, e rodar o ensaio no livro de Toxina.
Arquivos permitidos: skills/auditor-grafico/**, agents/editorial/auditor-grafico.md, tests/test_audit_pdf.py, docs/medicoes/2026-11-ensaio-toxina.md
Critérios de aceite:
- `audit_pdf.py PDF [--rules JSON] [--inherited LISTA] [--json OUT] [--md OUT]` roda todas as checagens de `checks.py` e segue os códigos de saída; `test_audit_pdf_all_kinds` usa os PDFs sintéticos dos cartões 1.2 e 1.3 e acha cada tipo.
- `SKILL.md`: inspeção pelo script mais a leitura visual das páginas apontadas; relatório por página; nota pela rubrica da fase 3 e 4; não gera nem edita imagem; não corrige layout.
- `agents/editorial/auditor-grafico.md`: sem `Edit`, `model: sonnet`, `effort: medium`, `maxTurns: 40`, `skills: [auditor-grafico]`.
- `docs/medicoes/2026-11-ensaio-toxina.md`: rodada no `Toxina_Botulinica_Miolo_Alta_Resolucao.pdf` de `EDITORIAL_SAMPLES_DIR`, com erros por tipo e as páginas de repetição ou sobreposição encontradas; sem trecho do livro.
- `package.py --sync` rodado.
Verificação: uv run --locked pytest tests/test_audit_pdf.py -q && uv run --locked python scripts/package.py --check

### Onda 6: empacotamento, guias e instalação

#### Cartão 6.1: Plugins, zips e versão em Projeto
Função: devops
Objetivo: completar o `package.py` com a saída para cada plataforma e os manifestos dos plugins.
Arquivos permitidos: scripts/package.py, .claude-plugin/plugin.json, .claude-plugin/marketplace.json, .codex-plugin/plugin.json, tests/test_package_build.py
Critérios de aceite:
- `.claude-plugin/plugin.json` com `name: clinic-editorial`, versão, descrição e a lista de agentes de `agents/editorial/`; `.claude-plugin/marketplace.json` apontando para a raiz do repositório; `claude plugin validate .` passa.
- `.codex-plugin/plugin.json` com as skills.
- `package.py --build` grava em `dist/`: `chatgpt/<skill>.zip` e `claude-ai/<skill>.zip` com o `SKILL.md` na raiz do zip; `codex/agents/<agente>.toml` com `name`, `description` e `developer_instructions` gerados de `agents/editorial/`; `chatgpt-projeto/` com `instrucoes.md` (o `SKILL.md` do Editor-Chefe) e os demais `SKILL.md` e referências como arquivos.
- Testes: `test_build_six_zips_with_skill_at_root`, `test_codex_toml_fields`, `test_project_bundle_has_instructions`.
Verificação: uv run --locked pytest tests/test_package_build.py -q && claude plugin validate .

#### Cartão 6.2: Guias e README
Função: docs
Objetivo: escrever o guia da Paula, o guia da equipe e o README.
Arquivos permitidos: README.md, docs/guia-paula.md, docs/guia-equipe.md
Critérios de aceite:
- `guia-paula.md`: instalar no ChatGPT (ou montar o Projeto, conforme o cartão 1.5), abrir projeto de livro, pedido por fase com o pedido de exemplo dela, onde guardar a ficha, como abrir a auditoria científica em conversa nova, o que fazer quando o Editor-Chefe parar na terceira volta; se a diagramação não rodar no ChatGPT, quem roda e como.
- `guia-equipe.md`: instalar no Claude Code (plugin), no Cowork, no claude.ai (zip) e no Codex (skills e TOML), e rodar `package.py`.
- `README.md`: o que é, os seis papéis, onde está cada coisa, comandos de teste e de empacotamento, link para a spec e o plano.
Verificação: grep -q "Fase concluída" docs/guia-paula.md && grep -q "package.py" docs/guia-equipe.md && grep -q "editor-chefe" README.md

#### Cartão 6.3 (manual, Alify ou Paula): Instalação e pedido real no ChatGPT
Objetivo: instalar os zips do cartão 6.1 (ou a versão em Projeto) no ChatGPT e rodar o pedido de exemplo da Paula num livro real (critério 7 da spec).
Critérios de aceite: `docs/medicoes/2026-11-instalacao.md` com plataforma, plano, o que funcionou, o que não funcionou e o tempo gasto; sem trecho de livro.

## Status
- Feito: spec aprovada (forma A); pesquisa de plataformas e de diagramação; repositório `clinic-cursos/editorial-setup` criado (privado); issue CLI-514.
- Em andamento: nada.
- Travado: 1.5 e 6.3 esperam o Alify (teste e instalação no ChatGPT); 3.5 espera o Alify ou a Paula (páginas de amostra); o manual de diagramação da Paula ainda não chegou (o 3.4 nasce com o lugar dele); 3.7 e 5.1 precisam de `EDITORIAL_SAMPLES_DIR` apontando para os PDFs reais nesta máquina.
- Próximo passo: sessão de execução da onda 1 (1.1 a 1.4) pela skill `delegate`; em paralelo, o Alify roda o 1.5 assim que o 1.4 estiver pronto.
