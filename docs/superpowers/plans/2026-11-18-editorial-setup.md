# Setup editorial V1 da Clinic Editora: plano

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Os cartões seguem o formato da skill `delegate`.

**Goal:** construir o time editorial (seis papéis) como skills de fonte única, com os scripts de checagem de PDF, a diagramação por HTML e WeasyPrint e o empacotamento para ChatGPT, claude.ai, Claude Code e Codex.

**Architecture:** cada papel é uma pasta em `skills/` no padrão Agent Skills; o código comum de PDF fica em `lib/pdfcheck/` e as referências comuns em `shared/`, e o `scripts/package.py` copia os dois para dentro das skills (cópia versionada, conferida contra deriva). O repositório é o próprio plugin do Claude Code e do Codex; os zips do ChatGPT e do claude.ai saem em `dist/`.

**Tech Stack:** Python 3.12 com `uv`; pdfplumber, pypdf, WeasyPrint, python-docx; ReportLab e pytest só nos testes; padrão Agent Skills; manifestos `.claude-plugin/` e `.codex-plugin/`.

**Spec:** `/home/alify/projetos/clinic-cursos/editorial-setup/docs/superpowers/specs/2026-11-18-editorial-setup-design.md` (forma A escolhida pelo Alify em 18/11/2026; "pode criar esse repo do setup editorial, com os agentes e tudo mais").

**Issue:** CLI-514 https://linear.app/clinic-cursos/issue/CLI-514

## Global Constraints
- Skill: `name` com 1 a 64 caracteres, só `[a-z0-9-]`, sem hífen no início, no fim ou duplo, igual ao nome da pasta, sem `claude` nem `anthropic`; `description` de 1 a 1.024 caracteres; `SKILL.md` com menos de 500 linhas; pastas `references/`, `scripts/`, `assets/`.
- Nenhuma pasta `bin/` no topo do repositório.
- Bibliotecas dos scripts das skills: biblioteca padrão, pdfplumber, pypdf, WeasyPrint, python-docx. PyMuPDF proibido (AGPL). ReportLab só em `tests/`. Sem biblioteca de Markdown: o leitor do manuscrito é próprio e cobre só a convenção de `shared/references/manuscrito.md`.
- Idioma: `SKILL.md`, referências, guias e mensagens para a Paula em português; código, nomes de função, chaves de JSON e commits em inglês. Nomes de skill e de agente em português sem acento: `editor-chefe`, `editor-cientifico`, `auditor-cientifico`, `diagramador`, `imagens`, `auditor-grafico`.
- Fontes da marca: Montserrat (títulos) e Source Sans 3 (texto), licença OFL, com o arquivo de licença junto.
- Paleta das imagens complementares: bordô, rosa claro, marsala, cinza; estilo conceitual e clean; sem texto dentro da imagem; nunca anatomia, pele, procedimento, produto de marca ou resultado de tratamento.
- Valores provisórios, num arquivo só, `shared/rules/graphic-rules.json`: `free_space_fraction` 0,25; `error_ppi` 150; `warning_ppi` 300; imagem herdada do original é sempre aviso; `safe_zone_mm` 10; `distortion_tolerance` 0,02; página A4 de 595,28 × 841,89 pt com tolerância de 1 pt.
- Fidelidade do texto: saída igual à entrada em pelo menos 0,995 dos caracteres, sem cabeçalho, rodapé e número de página.
- Nada de conteúdo de livro, foto clínica ou dado de aluno no git. Livros reais vêm de `EDITORIAL_SAMPLES_DIR` (nesta máquina, `~/Downloads/livros-paula/`, com os PDFs de Toxina e de Preenchedores).
- Sem travessão em nenhum texto entregue.

## Review Focus
1. Página sem camada de texto (escaneada ou só imagem): a checagem marca `page-without-text` como aviso e segue, sem quebrar nem passar em silêncio. Teste no cartão 2.1.
2. Nome de fonte com prefixo de subconjunto (`ABCDEF+SourceSans3-Roman`) ou fonte Type3 sem nome: o prefixo é normalizado e a fonte sem nome é aviso, não erro. Teste no cartão 2.1.
3. Texto com acento, ligadura (`ﬁ`), hífen de fim de linha e hífen suave: a fidelidade normaliza (NFC, ligaduras, hifenização) antes de comparar. Teste no cartão 3.2.
4. Imagem girada ou recortada por máscara: a resolução usa o tamanho exibido, e recorte não conta como distorção. Teste no cartão 2.2.
5. Página em branco proposital e abertura de capítulo: não entram como candidatas a imagem complementar. Teste no cartão 2.2.

## Convenções
- Repositório: `clinic-cursos/editorial-setup`, checkout `/home/alify/projetos/clinic-cursos/editorial-setup`, base `main`. `git` e `gh` com `GH_TOKEN=$(gh auth token --user fde1-clinic)`.
- **Formato que a ponte lê ao pé da letra:** "Arquivos permitidos" e "Verificação" vão sem crases; "Arquivos permitidos" separado por vírgula e espaço; a "Verificação" é um comando só, em /bin/sh, na worktree, depois do commit, com teto de 10 minutos, e sai com 0 quando o critério passa.
- Campos fixos de todo cartão: `Issue: CLI-514 https://linear.app/clinic-cursos/issue/CLI-514`, `Repositório: /home/alify/projetos/clinic-cursos/editorial-setup`, `Base: main`, `Risco: normal`, `Executor:` vazio, `Spec/plano:` o caminho absoluto da spec. `Requer:` vazio, salvo onde o cartão diz.
- `Requer: internet` em todo cartão que muda dependência (`pyproject.toml` e `uv.lock`), porque a sandbox do Codex não tem rede para o `uv lock`.
- Testes: `uv run --locked pytest`. PDFs, imagens, DOCX e capítulos de teste são gerados por código em `tests/conftest.py` (ReportLab, python-docx, Pillow do próprio ReportLab), sem binário no git.
- Cartão que roda `package.py --sync` traz a própria pasta da skill inteira nos "Arquivos permitidos" (`skills/<skill>/**`), o que inclui as cópias de `scripts/pdfcheck/` e `references/comum/`.
- Cartão que muda `shared/` ou `lib/pdfcheck/` (inclusive um ajuste de valor em `graphic-rules.json`) roda `package.py --sync`, traz `skills/*/references/comum/**` e `skills/*/scripts/pdfcheck/**` nos "Arquivos permitidos" e termina a Verificação com `uv run --locked python scripts/package.py --check`. Assim a `main` nunca fica com cópia divergente.
- Cartão `manual` é feito por uma pessoa (ou pela sessão de execução, quando o cartão diz) e registrado em `docs/medicoes/`; a ponte não o despacha.
- Linha de comando dos scripts: código de saída 0 sem erro, 1 com erro encontrado, 2 com uso errado ou arquivo ilegível.

## Interfaces comuns
- `lib/pdfcheck/model.py` (cartão 2.1):
  - `Finding(page: int, kind: str, severity: Literal["error", "warning"], detail: str, bbox: tuple[float, float, float, float] | None = None)` (dataclass; `page` começa em 1).
  - `Report(pdf: str, pages: int, findings: list[Finding])` com `errors() -> list[Finding]`, `to_json() -> str`, `to_markdown() -> str` (tabela em português por página).
  - `FreeSpace(page: int, x0: float, top: float, x1: float, bottom: float, fraction: float)`.
- `lib/pdfcheck/rules.py` (cartão 2.1): `Rules` (dataclass) com `allowed_fonts: list[str]`, `safe_zone_mm: float`, `error_ppi: int`, `warning_ppi: int`, `free_space_fraction: float`, `distortion_tolerance: float`, `page_size_pt: tuple[float, float]`; `load_rules(path: str | None = None) -> Rules`; com `path` `None`, procura nesta ordem: `../../references/comum/graphic-rules.json` a partir da pasta da cópia (dentro de uma skill) e `shared/rules/graphic-rules.json` a partir da raiz do repositório.
- `lib/pdfcheck/checks.py` (cada função recebe `pdf: pdfplumber.PDF` e `rules: Rules` e devolve `list[Finding]`): `check_overlaps`, `check_safe_zone`, `check_duplicates`, `check_fonts`, `check_text_layer`, `check_page_size` (cartão 2.1); `check_images(pdf, rules, inherited: set[str] | None = None)`, `check_page_numbers`, `check_toc` (cartão 2.2). E `free_space(pdf, rules) -> list[FreeSpace]` (cartão 2.2).
- Tipos de achado (`kind`): `overlap`, `outside-safe-zone`, `duplicate-paragraph`, `font-not-allowed`, `font-unnamed`, `page-without-text`, `page-size`, `image-low-resolution`, `image-distorted`, `page-number`, `toc-mismatch`.
- `skills/diagramador/scripts/build_book.py` (cartão 3.2): `build(manuscript_path: str, out_dir: str) -> BuildResult`, com `BuildResult(html: str, pdf: str, layout: dict[str, int], pages: int)`; `layout` mapeia o `id` de cada bloco (`b0001`...) para a página onde ele começa.
- Skills que recebem a cópia de `lib/pdfcheck/` (lista fixa em `package.py`): `diagramador`, `imagens`, `auditor-grafico`.

## Ondas
Ordem obrigatória da instrução da Paula: Editor-Chefe, Diagramador, Editor Científico, Auditor Científico, Auditor Gráfico.
- Onda 2 pode começar junto com o 1.2 (só código de PDF e o teste do ChatGPT, sem papel novo).
- Onda 1: 1.1, 1.2, 1.3 e 1.6, depois o manual 1.4. O 1.5 (apresentação à Paula) não trava mais a construção: em 18/11/2026 o Alify pediu para construir tudo e vai mandar o repositório à Paula, com a spec (seção 13) junto.
- Onda 3 só depois do 1.4 (ensaio do Editor-Chefe aprovado). O 2.4 (teste no ChatGPT, com a Paula) não trava a onda 3: o Diagramador roda localmente, e o resultado do 2.4 entra no 3.5 e na onda 6. Dentro da onda 3, a ordem é a dos números.
- Ondas 4, 5 e 6 na ordem.

### Onda 1: base e Editor-Chefe

#### Cartão 1.1: Base do repositório e validação das skills
Função: backend
Requer: internet
Objetivo: criar a base Python do repositório e o `scripts/package.py` nos modos de validação e de cópia das partes comuns.
Arquivos permitidos: pyproject.toml, uv.lock, .gitignore, .python-version, AGENTS.md, CLAUDE.md, scripts/package.py, lib/__init__.py, lib/pdfcheck/__init__.py, shared/README.md, tests/__init__.py, tests/test_package.py, tests/fixtures_skills/**
Critérios de aceite:
- `pyproject.toml` com pdfplumber, pypdf, weasyprint e python-docx; no grupo de desenvolvimento, pytest e reportlab; `uv.lock` gerado.
- `.gitignore` com `dist/`, `.venv/`, `__pycache__/`, `projetos/`.
- `AGENTS.md` com as regras do time (governança da seção 2 da spec, idioma, nada de conteúdo de livro no git); `CLAUDE.md` com uma linha que aponta para o `AGENTS.md`.
- `package.py --check` valida cada pasta de `skills/` que tem `SKILL.md` (regras de nome, `description`, linhas do `SKILL.md`), avisa sem falhar sobre pasta sem `SKILL.md`, falha com `bin/` no topo do repositório e confere que as cópias de `lib/pdfcheck/`, `shared/references/` e `shared/rules/` dentro das skills são iguais às originais; sai com 1 e lista cada problema.
- `package.py --sync` copia `lib/pdfcheck/` para `skills/<skill>/scripts/pdfcheck/` só nas três skills da lista fixa, e `shared/references/` e `shared/rules/` para `skills/<skill>/references/comum/` em toda skill com `SKILL.md`.
- Testes: `test_valid_skill_passes`, `test_name_with_claude_fails`, `test_description_over_1024_fails`, `test_skill_md_500_lines_fails`, `test_top_level_bin_fails`, `test_drifted_copy_fails`, `test_folder_without_skill_md_warns`.
Verificação: uv run --locked pytest tests/test_package.py -q

#### Cartão 1.2: Referências comuns
Função: ai
Objetivo: escrever as referências que todos os papéis leem.
Arquivos permitidos: shared/references/governanca.md, shared/references/identidade-visual.md, shared/references/glossario.md, shared/references/manuscrito.md, shared/references/retorno.md, shared/README.md
Critérios de aceite:
- `governanca.md`: autoridade do Board; João aprova o conteúdo técnico; Paula aprova a versão, cuida do ISBN e libera a impressão; nenhum agente libera impressão; versão aprovada não muda; divergência com o Board vai para avaliação humana (seções 2 e 6 da spec e seção 7 da instrução da Paula).
- `identidade-visual.md`: A4; bordô, branco e cinza; fontes da marca; componentes editoriais (Estudo e Prática, Leitura e Aprofundamento, Aplicação Clínica, Ponto-chave, Atenção, Evidência, Perguntas frequentes, legenda de antes e depois com o texto padrão, módulo de QR code), do briefing e do PDF "Padrões e Pendências Visuais".
- `manuscrito.md`: metadados no topo (título, curso, autores, versão), títulos `#` a `###`, parágrafos, listas com `-` e `1.`, blocos `:::ponto-chave`, `:::atencao`, `:::evidencia`, `:::estudo-pratica`, `:::aprofundamento`, `:::aplicacao-clinica`, `:::faq` fechados por `:::`, marca de origem `<!-- slide: N -->`, citação `[@chave]` com a lista de referências no fim, figura `![legenda](arquivo){#fig-id}`. Nada além disso.
- `retorno.md`: bloco fixo que todo papel devolve ao Editor-Chefe (status `PRONTO`, `PRONTO_COM_RESSALVAS`, `PRECISA_DE_DADO`, `BLOQUEADO`; arquivos entregues; pendências; nota e achados quando o papel é auditor).
Verificação: for f in governanca identidade-visual glossario manuscrito retorno; do test -s shared/references/$f.md || exit 1; done; grep -q ":::ponto-chave" shared/references/manuscrito.md

#### Cartão 1.3: Skill e agente do Editor-Chefe
Função: ai
Objetivo: escrever a skill `editor-chefe` com o fluxo, o portão de nota, a ficha e as rubricas, e a definição do agente.
Arquivos permitidos: skills/editor-chefe/**, agents/editorial/editor-chefe.md, tests/cenarios/editor-chefe.md
Critérios de aceite:
- `SKILL.md`: missão, quando acionar, entradas, processo numerado (ler a ficha, identificar a fase concluída e a próxima, delegar com pedido estruturado, receber o bloco de retorno, aplicar o portão, atualizar a ficha, preparar o pacote para a pessoa), limites e retorno; menos de 500 linhas.
- Portão: passa com 90 ou mais e nenhum eliminatório; nota dada por quem não produziu; até 3 voltas; na terceira reprovação entrega o melhor resultado, a nota de cada volta e as pendências; nota da fase 3 marcada "provisória: manual ausente" enquanto `diagramador/references/manual-clinic.md` disser "aguardando o manual".
- No chat sem subagente: roda os papéis em sequência e manda a auditoria científica para conversa nova, montando o "pacote de auditoria".
- Tabela de gatilhos no `SKILL.md` (pedido do Alify em 18/11/2026: "todos os agentes precisam se chamar nas suas devidas atividades"): para cada evento, quem é acionado. Material do Board recebido → `editor-cientifico`; manuscrito entregue → `auditor-cientifico`; nota da fase 1 de 90 ou mais → pacote para o João; aprovação do João registrada → `diagramador`; PDF composto → `auditor-grafico`; espaço livre acima do limite → `imagens`, depois `diagramador` para inserir; nota da fase 3 e 4 de 90 ou mais → pacote para a Paula; reprovação → volta a quem produziu; terceira reprovação → pessoa. Os papéis nunca se chamam entre si: todo retorno volta ao Editor-Chefe, que aciona o próximo.
- No Claude Code e no Codex o Editor-Chefe roda na conversa principal (`/editor-chefe`), porque subagente não abre subagente; os demais papéis rodam como subagentes.
- `references/fluxo.md` (tabela 6.1 da spec), `references/ficha-projeto.md` (todos os campos da seção 7, custos inclusive), `references/rubricas/fase-1-ampliacao.md` e `references/rubricas/fase-3-4-diagramacao.md` (pesos e eliminatórios da seção 6.2).
- `agents/editorial/editor-chefe.md` no molde da casa: `name`, `description`, `tools`, `model: opus`, `effort: medium`, `maxTurns: 60`, `skills: [editor-chefe]`; corpo curto que manda seguir a skill.
- `tests/cenarios/editor-chefe.md`: roteiro do critério 2 da spec, para o cartão 1.4.
- `package.py --sync` rodado.
Verificação: uv run --locked python scripts/package.py --check && grep -q "90" skills/editor-chefe/SKILL.md && test -s skills/editor-chefe/references/rubricas/fase-3-4-diagramacao.md

#### Cartão 1.6: Hooks do plugin do Claude Code
Função: backend
Objetivo: travas automáticas do time no Claude Code e no Cowork, pedidas pelo Alify em 18/11/2026 ("com os respectivos hooks").
Arquivos permitidos: hooks/hooks.json, hooks/editorial_guard.py, hooks/subagent_return.py, tests/test_hooks.py
Critérios de aceite:
- `hooks/hooks.json` no formato de hooks de plugin do Claude Code, com três ganchos, todos em Python só com a biblioteca padrão:
  - `PreToolUse` em `Write`, `Edit` e `MultiEdit` (`editorial_guard.py`): nega escrita dentro de `originais/` de um projeto e em arquivo listado como versão aprovada na `ficha.md` do projeto (linha `aprovado:` com o caminho), com a mensagem em português "versão aprovada não muda; gere uma versão nova";
  - `SubagentStop` (`subagent_return.py`): quando o subagente é um dos cinco papéis do time, confere que a última mensagem tem o bloco de `retorno.md` (linha `Status:` com um dos quatro valores); sem o bloco, pede uma vez para o papel devolver o bloco, e na segunda deixa passar com aviso, para nunca prender o agente;
  - `Stop` (`subagent_return.py --stop`): na conversa do Editor-Chefe, lembra de entregar a ficha atualizada quando houve fase concluída sem atualização da ficha.
- Os hooks falham abertos: erro de leitura ou de JSON deixa passar e escreve o aviso no stderr.
- Testes, com o JSON de entrada de cada evento simulado: `test_guard_blocks_originais`, `test_guard_blocks_approved_version`, `test_guard_allows_new_version`, `test_return_missing_asks_once`, `test_return_present_passes`, `test_hook_fails_open_on_bad_json`.
- No ChatGPT e no claude.ai não há hook: as mesmas regras ficam no texto das skills (tabela de gatilhos do Editor-Chefe e limites de cada papel).
Verificação: uv run --locked pytest tests/test_hooks.py -q

#### Cartão 1.4 (manual, sessão de execução): Ensaio do Editor-Chefe
Objetivo: provar o critério 2 da spec (critério de aceite da fase 1 da instrução da Paula) no Claude Code, com o plugin carregado do checkout.
Critérios de aceite: `docs/medicoes/2026-11-ensaio-editor-chefe.md` com `Resultado: APROVADO` ou `REPROVADO`, mostrando a ficha criada com todos os campos, a delegação a um executor de teste, o caso que passa com 92, o caso que volta com 85 e o histórico completo. Reprovado volta ao 1.3.

#### Cartão 1.5 (manual, Alify): Apresentação à Paula
Objetivo: apresentar à Paula a seção 13 da spec (resposta à primeira entrega que ela pediu) antes da onda 3.
Critérios de aceite: `docs/medicoes/2026-11-apresentacao-paula.md` com a data e as respostas dela sobre o papel `imagens`, os valores provisórios de `graphic-rules.json`, a regra das imagens só conceituais e o prazo do manual de diagramação. Valor mudado por ela entra em `graphic-rules.json` antes da onda 3, num cartão `mechanical` que segue a convenção de mudança em `shared/`.

### Onda 2: checagem de PDF e teste de plataforma

#### Cartão 2.1: Checagens de texto, fonte e página
Função: backend
Objetivo: implementar o modelo de achados, as regras e as checagens de sobreposição, zona de segurança, duplicação, fonte, camada de texto e tamanho de página.
Arquivos permitidos: lib/pdfcheck/model.py, lib/pdfcheck/rules.py, lib/pdfcheck/checks.py, shared/rules/graphic-rules.json, skills/*/references/comum/**, skills/*/scripts/pdfcheck/**, tests/conftest.py, tests/test_checks_text.py
Critérios de aceite:
- `graphic-rules.json` com todos os valores das Global Constraints e `allowed_fonts: ["Montserrat", "SourceSans3", "SourceSansPro"]`; `model.py` já com `FreeSpace`.
- `tests/conftest.py` gera, com ReportLab, PDFs A4 sintéticos: limpo; com duas linhas sobrepostas; com texto a 5 mm da borda; com um parágrafo de 120 caracteres repetido; com uma página só de imagem; e um PDF em tamanho Carta. Os testes usam uma fixture `test_rules` com `allowed_fonts` que inclui a Helvetica do ReportLab, salvo o teste de fonte.
- Testes: `test_clean_pdf_has_no_errors`, `test_overlap_detected` (um `overlap` na página certa), `test_safe_zone_detected`, `test_duplicate_paragraph_detected`, `test_font_not_allowed_detected` (com as regras reais, `font-not-allowed` com `Helvetica` no `detail`), `test_subset_prefix_normalized`, `test_unnamed_font_is_warning`, `test_page_without_text_is_warning`, `test_letter_size_is_page_size_error`.
- Sobreposição: caixas de linhas de texto de blocos diferentes que se cruzam em mais de 1 pt nos dois eixos; letras repetidas no mesmo lugar (negrito simulado) não contam, usando `dedupe_chars`.
Verificação: uv run --locked pytest tests/test_checks_text.py -q && uv run --locked python scripts/package.py --check

#### Cartão 2.2: Checagens de imagem, paginação, sumário e espaço livre
Função: backend
Objetivo: completar `checks.py` com resolução e distorção de imagem, número de página, sumário e espaço livre.
Arquivos permitidos: lib/pdfcheck/checks.py, skills/*/scripts/pdfcheck/**, tests/conftest.py, tests/test_checks_layout.py
Critérios de aceite:
- PPI efetivo = pixels ÷ (tamanho exibido em pt ÷ 72), pelo menor dos dois eixos. Imagem com nome em `inherited` é sempre `warning`; as demais são `error` abaixo de `error_ppi` e `warning` abaixo de `warning_ppi`.
- Distorção: proporção exibida difere da proporção em pixels em mais de `distortion_tolerance`; imagem girada usa a matriz de transformação; recorte por máscara não conta.
- `check_page_numbers`: número impresso no rodapé em sequência; falta ou salto vira `page-number`.
- `check_toc`: cada entrada do sumário (linha com título e número no fim) aponta para a página onde o título aparece; diferença vira `toc-mismatch`.
- `free_space`: retângulo entre o fim do último objeto (texto, imagem ou desenho) e a margem inferior da mancha de texto (`page_margins_mm`, cartão 3.12), na largura útil, sem contar o fólio e o cabeçalho corrido; entra quando a altura passa de `free_space_fraction` da altura útil. Página sem objeto e abertura de capítulo (maior título no terço de cima, ocupando a largura) ficam fora.
- Testes: `test_low_ppi_new_image_is_error`, `test_low_ppi_inherited_image_is_warning`, `test_distorted_image_detected`, `test_rotated_image_not_distorted`, `test_page_number_gap_detected`, `test_toc_mismatch_detected`, `test_free_space_listed_with_fraction`, `test_blank_page_not_candidate`, `test_chapter_opening_not_candidate`.
Verificação: uv run --locked pytest tests/test_checks_layout.py -q && uv run --locked python scripts/package.py --check

#### Cartão 2.3: Skill de teste de plataforma e roteiro
Função: docs
Objetivo: preparar a skill descartável e o roteiro do teste no ChatGPT da Clinic (critério 0 da spec).
Arquivos permitidos: docs/medicoes/teste-plataforma/SKILL.md, docs/medicoes/teste-plataforma/roteiro.md
Critérios de aceite:
- `SKILL.md` com `name: teste-plataforma`, que pede ao modelo: rodar no Python da conversa `import weasyprint, pdfplumber, pypdf, docx` e `pip list` e mostrar a saída; gerar uma imagem simples; dizer se o Python enxerga o arquivo da imagem gerada (caminho e tamanho) ou não.
- `roteiro.md` em português simples: ligar skills no workspace (se o plano tiver), compactar a pasta em zip, enviar em Skills, abrir conversa nova, colar o pedido pronto e copiar o resultado para `docs/medicoes/2026-11-teste-chatgpt.md` no modelo do roteiro (plano do ChatGPT; skills disponíveis; WeasyPrint, pdfplumber, pypdf e python-docx presentes; imagem gerada; Python enxerga a imagem; observações).
Verificação: grep -q "name: teste-plataforma" docs/medicoes/teste-plataforma/SKILL.md && grep -q "WeasyPrint" docs/medicoes/teste-plataforma/roteiro.md

#### Cartão 2.4 (manual, Paula, quando puder): Teste no ChatGPT da Clinic
Objetivo: a Paula roda o roteiro do cartão 2.3 no ChatGPT dela e o resultado é gravado em `docs/medicoes/2026-11-teste-chatgpt.md`.
Critérios de aceite: arquivo com todos os campos. Sem skills no plano: o cartão 6.1 gera a versão em Projeto como caminho principal. Sem WeasyPrint: a skill do Diagramador (3.5, ou um ajuste dela se o 3.5 já tiver saído) diz que a diagramação roda no Claude Code ou no Codex, e o 6.2 diz isso no guia da Paula.

### Onda 3: Diagramador e imagens (fase 2 da instrução da Paula)

#### Cartão 3.1: Modelo visual do livro e amostra
Função: frontend
Objetivo: criar o modelo HTML e o CSS de impressão do livro, com as fontes da marca, e as três páginas de amostra.
Arquivos permitidos: skills/diagramador/assets/**, tests/samples/amostra.html, tests/test_template.py, tests/test_tokens.py, docs/medicoes/amostra/**
Critérios de aceite:
- `assets/livro.html` (esqueleto com capa, expediente, sumário e corpo, com o lugar onde o `build_book.py` põe o conteúdo) e `assets/livro.css` com `@page` A4, cabeçalho "CLINIC EDITORA" à esquerda e título do livro à direita, número de página no rodapé, sumário por `target-counter()`, uma classe por componente editorial de `identidade-visual.md`, legenda Source Sans 9 pt / 11,5 pt cinza, cores tiradas dos PDFs de referência.
- Cores, fontes, tamanhos e espaçamentos só como variáveis CSS em `assets/tokens.css`, para o design system (Alify, Paula e Julie) trocar depois; `test_no_literal_colors_outside_tokens` confere que `livro.css` não tem cor literal.
- Fontes Montserrat e Source Sans 3 em `assets/fonts/` com `OFL.txt`.
- `tests/samples/amostra.html`: HTML sintético escrito à mão, com todos os componentes, ligado ao `livro.css`.
- `test_template_renders_with_brand_fonts`: renderiza a amostra pelo WeasyPrint; `check_fonts` e `check_page_size` não acusam nada.
- Três páginas em PNG em `docs/medicoes/amostra/` (abertura de capítulo, texto com caixas, imagem com legenda) para o cartão 3.6.
Verificação: uv run --locked pytest tests/test_template.py tests/test_tokens.py -q

#### Cartão 3.2: Leitor do manuscrito, composição e fidelidade
Função: backend
Objetivo: ler o manuscrito na convenção da casa, compor HTML e PDF com o mapa de blocos por página e medir a fidelidade do texto.
Arquivos permitidos: skills/diagramador/scripts/manuscript.py, skills/diagramador/scripts/build_book.py, skills/diagramador/scripts/text_fidelity.py, tests/test_manuscript.py, tests/test_build_book.py, tests/test_text_fidelity.py
Critérios de aceite:
- `manuscript.py` lê só a convenção de `manuscrito.md` e devolve blocos tipados; um teste por construção: `test_parse_headings`, `test_parse_lists`, `test_parse_blocks`, `test_parse_slide_marker`, `test_parse_citation_and_references`, `test_parse_figure_with_id`, `test_unknown_block_is_error`.
- `build_book.py MANUSCRITO.md --out DIR` chama `build()` (Interfaces comuns), grava `livro.html`, `livro.pdf` e `layout.json`, com as âncoras das páginas do WeasyPrint.
- `text_fidelity.py ORIGINAL SAIDA` aceita `.md` ou `.pdf` dos dois lados, normaliza (NFC, ligaduras, hífen de fim de linha, hífen suave, espaços), descarta cabeçalho, rodapé e número de página, imprime a razão com 4 casas e sai com 1 abaixo de 0,995.
- Testes: `test_build_writes_three_files`, `test_layout_maps_every_block`, `test_fidelity_identical_is_one`, `test_fidelity_ligature_and_hyphenation_normalized`, `test_fidelity_missing_paragraph_fails`.
Verificação: uv run --locked pytest tests/test_manuscript.py tests/test_build_book.py tests/test_text_fidelity.py -q

#### Cartão 3.3: Extração de PDF composto
Função: backend
Objetivo: levar livros já compostos em PDF para o manuscrito.
Arquivos permitidos: skills/diagramador/scripts/extract_pdf.py, tests/test_extract_pdf.py
Critérios de aceite:
- `extract_pdf.py PDF --out manuscrito.md --images DIR` usa o pdfplumber para texto, tamanho e cor da fonte e o pypdf para as imagens; títulos pelo tamanho em relação ao corpo; rótulos em caixa alta e bordô viram `###`; cabeçalho, rodapé e número de página fora; imagens salvas em `DIR` e referenciadas no lugar.
- Testes, num PDF sintético: `test_headings_recovered`, `test_header_footer_dropped`, `test_image_extracted_and_referenced`, `test_round_trip_fidelity` (extrair, compor pelo `build()` e `text_fidelity.py` passa).
Verificação: uv run --locked pytest tests/test_extract_pdf.py -q

#### Cartão 3.4: Extração de DOCX
Função: backend
Objetivo: levar manuscritos em DOCX para a convenção da casa.
Arquivos permitidos: skills/diagramador/scripts/extract_docx.py, tests/test_extract_docx.py
Critérios de aceite:
- `extract_docx.py DOCX --out manuscrito.md --images DIR` com python-docx: títulos pelos estilos de título, parágrafos, listas e imagens.
- Testes num DOCX sintético: `test_docx_headings_recovered`, `test_docx_lists_recovered`, `test_docx_image_extracted`.
Verificação: uv run --locked pytest tests/test_extract_docx.py -q

#### Cartão 3.5: Skill e agente do Diagramador
Função: ai
Objetivo: escrever a skill `diagramador`, o `check_layout.py` e a definição do agente.
Arquivos permitidos: skills/diagramador/**, agents/editorial/diagramador.md, tests/test_check_layout.py
Critérios de aceite:
- `SKILL.md`: entrada (manuscrito aprovado, DOCX ou PDF composto), processo (extrair quando preciso, compor, rodar `check_layout.py` e `text_fidelity.py`, corrigir até zero erro, entregar), limites (não cria imagem; não altera texto aprovado sem autorização registrada na ficha), retorno no bloco de `retorno.md`; onde o motor roda conforme `docs/medicoes/2026-11-teste-chatgpt.md`.
- `references/manual-clinic.md` com "aguardando o manual" e a lista dos padrões já conhecidos; `references/abnt.md` com a NBR 6029:2023 (confirmada) e as NBR 6023, 10520, 6024, 6027 e 6034 marcadas "confiança média, conferir no catálogo da ABNT", só com as regras, sem copiar a norma.
- `scripts/check_layout.py PDF [--inherited LISTA]` roda `check_overlaps`, `check_safe_zone`, `check_duplicates`, `check_fonts`, `check_text_layer`, `check_page_size`, `check_page_numbers`, `check_toc` e `check_images` (exigência da instrução da Paula: sobreposição, corte, fontes, paginação e resolução), imprime o relatório em Markdown e segue os códigos de saída. Testes: `test_check_layout_exit_codes` (0 no limpo, 1 no sobreposto, 2 em arquivo inexistente), `test_check_layout_reports_toc_and_images`.
- `agents/editorial/diagramador.md`: `model: sonnet`, `effort: medium`, `maxTurns: 60`, `skills: [diagramador]`.
- `package.py --sync` rodado.
Verificação: uv run --locked pytest tests/test_check_layout.py -q && uv run --locked python scripts/package.py --check

#### Cartão 3.6 (manual, Alify): Conferência das páginas de amostra
Objetivo: conferir as três páginas de `docs/medicoes/amostra/` contra os livros e documentos de referência que a Paula já aprovou (regra da casa: mudança visível só com mockup aprovado).
Critérios de aceite: `docs/medicoes/amostra/aprovacao.md` com quem conferiu, a data e os ajustes pedidos. Ajuste pedido volta ao 3.1 antes do 3.8.

#### Cartão 3.7: Imagens complementares
Função: ai
Objetivo: escrever a skill `imagens`, o script de espaço livre e o script que insere a imagem sem mover o texto.
Arquivos permitidos: skills/imagens/**, skills/diagramador/scripts/insert_images.py, agents/editorial/imagens.md, tests/test_free_space_cli.py, tests/test_insert_images.py
Critérios de aceite:
- `skills/imagens/scripts/free_space.py PDF [--json OUT]` imprime as páginas candidatas (página, largura e altura em mm, proporção, fração) pela `free_space`.
- `insert_images.py MANUSCRITO.md IMAGENS_DIR --out DIR`: compõe com `build()`, mede `free_space` no PDF composto, põe cada `pagina-NN.png` logo depois do último bloco que começa na página NN, com altura máxima igual à do espaço livre e classe `complementar`, recompõe e confere que o número de páginas e a página de cada bloco não mudaram; se mudaram, tira a imagem daquela página e avisa.
- `SKILL.md`: processo da seção 8.3 da spec, regra "sempre conceitual" e troca por conceito mais abstrato na dúvida; briefing por página; geração pela ferramenta nativa do ambiente; no Claude, só os briefings; registro de cada imagem para a ficha.
- `references/paleta.md` com os valores de cor tirados dos PDFs.
- `agents/editorial/imagens.md`: `model: sonnet`, `effort: low`, `maxTurns: 30`, `skills: [imagens]`.
- Testes: `test_free_space_cli_lists_candidates`, `test_insert_keeps_pagination`, `test_insert_reverts_when_page_breaks`.
- `package.py --sync` rodado.
Verificação: uv run --locked pytest tests/test_free_space_cli.py tests/test_insert_images.py -q && uv run --locked python scripts/package.py --check

#### Cartão 3.8: Ensaio com Toxina e Preenchedores
Função: backend
Objetivo: rodar o Diagramador no caso inicial da Paula (Toxina) e o fluxo do pedido dela (Preenchedores) nos PDFs reais (critérios 4 e 5 da spec).
Arquivos permitidos: scripts/run_sample.py, docs/medicoes/2026-11-ensaio-toxina-diagramacao.md, docs/medicoes/2026-11-ensaio-preenchedores.md
Critérios de aceite:
- `run_sample.py NOME_DO_PDF RELATORIO` sai com 0 sempre que grava o relatório, aprovado ou não, e com 2 em erro de uso ou de leitura; lê de `EDITORIAL_SAMPLES_DIR`, nunca escreve nos originais, trabalha em pasta temporária fora do repositório e roda: extrair, compor, `check_layout`, `text_fidelity`, `free_space`, inserir imagens sintéticas de teste (retângulos na paleta) e conferir de novo.
- Cada relatório com `Resultado: APROVADO` ou `REPROVADO` e os números: páginas, fontes encontradas (nenhuma DejaVu), erros e avisos por tipo, fidelidade, páginas candidatas, paginação antes e depois. Sem trecho do livro.
Verificação: test -n "$EDITORIAL_SAMPLES_DIR" && uv run --locked python scripts/run_sample.py Toxina_Botulinica_Miolo_Alta_Resolucao.pdf docs/medicoes/2026-11-ensaio-toxina-diagramacao.md && uv run --locked python scripts/run_sample.py Preenchedores_Dermicos_Consolidado_40_Alteracoes.pdf docs/medicoes/2026-11-ensaio-preenchedores.md && grep -q "Resultado: APROVADO" docs/medicoes/2026-11-ensaio-toxina-diagramacao.md && grep -q "Resultado: APROVADO" docs/medicoes/2026-11-ensaio-preenchedores.md

### Onda 4: Editor Científico e Auditor Científico

#### Cartão 4.1: Conferência de referências
Função: backend
Objetivo: conferir DOI e PMID pelas APIs gratuitas do Crossref e do PubMed.
Arquivos permitidos: skills/auditor-cientifico/scripts/verify_refs.py, tests/test_verify_refs.py
Critérios de aceite:
- `verify_refs.py REFS.json [--offline]` lê uma lista de `{key, title, authors, year, doi?, pmid?}`; consulta `https://api.crossref.org/works/{doi}` e `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json` com `urllib` e User-Agent `clinic-editorial-setup/0.1`, sem e-mail nem nome; compara título (razão do `difflib` de 0,9 ou mais), ano e sobrenome do primeiro autor.
- Saída JSON por referência com `status`: `ok`, `divergent`, `not-found`, `unverified` (sem rede ou com `--offline`); sai com 1 se houver `not-found` ou `divergent`.
- Testes com respostas HTTP simuladas: `test_matching_doi_ok`, `test_unknown_doi_not_found`, `test_title_mismatch_divergent`, `test_offline_unverified`.
Verificação: uv run --locked pytest tests/test_verify_refs.py -q

#### Cartão 4.2: Skill e agente do Editor Científico
Função: ai
Objetivo: escrever a skill `editor-cientifico` e a definição do agente.
Arquivos permitidos: skills/editor-cientifico/**, agents/editorial/editor-cientifico.md
Critérios de aceite:
- `SKILL.md`: separa as fontes A (original do Board), B (ministrado) e C (complementação); preserva a sequência didática; entrega plano de ampliação, manuscrito na convenção de `manuscrito.md`, tabela slide a capítulo e tabela de rastreabilidade (afirmação, fonte, DOI ou PMID, tipo de estudo, data de consulta, limitação, trecho, estado); proíbe referência inventada e mudança silenciosa de decisão clínica do Board.
- `references/rastreabilidade.md` e `references/fontes.md` (PubMed, Crossref, OpenAlex e bases oficiais, nessa ordem).
- `agents/editorial/editor-cientifico.md`: `model: opus`, `effort: high`, `maxTurns: 80`, `skills: [editor-cientifico]`.
- `package.py --sync` rodado.
Verificação: uv run --locked python scripts/package.py --check && grep -q "slide" skills/editor-cientifico/SKILL.md

#### Cartão 4.3: Skill e agente do Auditor Científico
Função: ai
Objetivo: escrever a skill `auditor-cientifico` e a definição do agente.
Arquivos permitidos: skills/auditor-cientifico/**, agents/editorial/auditor-cientifico.md
Critérios de aceite:
- `SKILL.md`: confere cada afirmação contra a fonte (rodando `verify_refs.py` quando há rede), a coerência com o material do Board, divergências, extrapolações e informação regulatória a atualizar; relatório de não conformidades com localização, evidência e recomendação; nota pela rubrica da fase 1; não reescreve o manuscrito; separa "conferido" de "juízo do auditor".
- `references/relatorio.md` com o modelo do relatório.
- `agents/editorial/auditor-cientifico.md`: `tools: Read, Grep, Glob, Bash, Write` (sem `Edit`; o texto diz que o `Write` serve só ao relatório), `model: sonnet`, `effort: high`, `maxTurns: 60`, `skills: [auditor-cientifico]`.
- `package.py --sync` rodado.
Verificação: uv run --locked python scripts/package.py --check && grep -q "verify_refs.py" skills/auditor-cientifico/SKILL.md

#### Cartão 4.4: Ensaio científico com capítulo sintético
Função: test
Objetivo: provar o critério 6 da spec com material escrito para o teste.
Arquivos permitidos: tests/samples/capitulo-teste/**, tests/test_science_sample.py, docs/medicoes/2026-11-ensaio-cientifico.md
Critérios de aceite:
- `tests/samples/capitulo-teste/`: 8 slides sintéticos em Markdown, um manuscrito sintético com tabela slide a capítulo e a lista de referências em JSON com uma referência inventada plantada.
- `test_every_slide_mapped` (nenhum slide órfão) e `test_planted_reference_flagged` (`verify_refs.py` sem `--offline`, com as respostas HTTP simuladas do 4.1, marca a plantada como `not-found`).
- `docs/medicoes/2026-11-ensaio-cientifico.md` com o resultado de uma rodada do Editor Científico e do Auditor Científico no Claude Code sobre esse material (feita pela sessão de execução depois do merge do cartão).
Verificação: uv run --locked pytest tests/test_science_sample.py -q

### Onda 5: Auditor Gráfico

#### Cartão 5.1: Skill, agente e ensaio do Auditor Gráfico
Função: ai
Objetivo: escrever o `audit_pdf.py`, a skill `auditor-grafico` e a definição do agente, e rodar o ensaio no livro de Toxina (critério 6a).
Arquivos permitidos: skills/auditor-grafico/**, agents/editorial/auditor-grafico.md, tests/test_audit_pdf.py, docs/medicoes/2026-11-ensaio-toxina-auditoria.md
Critérios de aceite:
- `audit_pdf.py PDF [--rules JSON] [--inherited LISTA] [--json OUT] [--md OUT]` roda todas as checagens e segue os códigos de saída; `test_audit_pdf_all_kinds` acha cada tipo nos PDFs sintéticos dos cartões 2.1 e 2.2.
- `SKILL.md`: inspeção pelo script e leitura visual das páginas apontadas; relatório por página; nota pela rubrica da fase 3 e 4; não gera nem edita imagem; não corrige layout.
- `agents/editorial/auditor-grafico.md`: `tools: Read, Grep, Glob, Bash`, `model: sonnet`, `effort: medium`, `maxTurns: 40`, `skills: [auditor-grafico]`.
- `docs/medicoes/2026-11-ensaio-toxina-auditoria.md`: rodada no PDF original de Toxina, com erros e avisos por tipo e as páginas de repetição ou sobreposição encontradas; sem trecho do livro.
- `package.py --sync` rodado.
Verificação: uv run --locked pytest tests/test_audit_pdf.py -q && uv run --locked python scripts/package.py --check

### Onda 6: empacotamento, guias e instalação

#### Cartão 6.1: Plugins, zips e versão em Projeto
Função: devops
Objetivo: completar o `package.py` com a saída para cada plataforma e os manifestos dos plugins.
Arquivos permitidos: scripts/package.py, .claude-plugin/plugin.json, .claude-plugin/marketplace.json, .codex-plugin/plugin.json, tests/test_package_build.py
Critérios de aceite:
- `.claude-plugin/plugin.json` com `name: clinic-editorial`, versão, descrição e a lista de agentes de `agents/editorial/`; `.claude-plugin/marketplace.json` apontando para a raiz; `claude plugin validate .` passa.
- `.codex-plugin/plugin.json` com as skills.
- `package.py --build` grava em `dist/`: `chatgpt/<skill>.zip` e `claude-ai/<skill>.zip` com o `SKILL.md` na raiz do zip; `codex/agents/<agente>.toml` com `name`, `description` e `developer_instructions` gerados de `agents/editorial/`; `chatgpt-projeto/` com `instrucoes.md` (o `SKILL.md` do Editor-Chefe) e os demais `SKILL.md` e referências como arquivos.
- Testes: `test_build_six_zips_with_skill_at_root`, `test_codex_toml_fields`, `test_project_bundle_has_instructions`.
Verificação: uv run --locked pytest tests/test_package_build.py -q && claude plugin validate .

#### Cartão 6.2: Guias e README
Função: docs
Objetivo: escrever o guia da Paula, o guia da equipe e o README.
Arquivos permitidos: README.md, docs/guia-paula.md, docs/guia-equipe.md, docs/melhorias.md, CHANGELOG.md
Critérios de aceite:
- `guia-paula.md`: instalar no ChatGPT (ou montar o Projeto, conforme o 2.4), abrir projeto de livro, pedido por fase com o pedido de exemplo dela, onde guardar a ficha, como abrir a auditoria científica em conversa nova, o que fazer quando o Editor-Chefe parar na terceira volta, quem roda a diagramação se ela não rodar no ChatGPT, e a seção "Como melhorar o setup" (seção 9.1 da spec).
- `docs/melhorias.md` com o modelo de linha (data, papel, o que mudar, por quê, exemplo) e `CHANGELOG.md` com a versão 0.1.0.
- `guia-equipe.md`: instalar no Claude Code (plugin), no Cowork, no claude.ai (zip) e no Codex (skills em `.agents/skills/` e TOML de `dist/codex/agents/` copiados para `.codex/agents/` ou `~/.codex/agents/`), e rodar o `package.py`.
- `README.md`: o que é, os seis papéis, onde está cada coisa, comandos de teste e de empacotamento, links para a spec e o plano.
Verificação: grep -q "Fase concluída" docs/guia-paula.md && grep -q "Como melhorar o setup" docs/guia-paula.md && grep -q "codex/agents" docs/guia-equipe.md && grep -q "editor-chefe" README.md && test -s docs/melhorias.md

#### Cartão 6.3 (manual, Paula): Instalação e uso real no ChatGPT
Objetivo: a Paula instala os zips do 6.1 (ou a versão em Projeto) no ChatGPT dela e passa a trabalhar com o setup, começando pelo pedido de exemplo num livro real (critério 7 da spec).
Critérios de aceite: `docs/medicoes/2026-11-instalacao.md` com plataforma, plano, o que funcionou, o que não funcionou e o tempo gasto; sem trecho de livro.

### Onda 7: aulas e estilo da casa da Julie (spec 9.2)
Pode correr em paralelo às ondas 4 a 6. Fonte: `docs/fontes/2026-11-19-julie-design-system/`; os arquivos extraídos do HTML (SKILL.md original, `clinic_deck.py`, `bold_deck.py`, `assets_b64.json`, `exemplo_roteiro.json`) são reconstruídos a partir dele.

#### Cartão 7.1: Skill e agente de aulas
Função: ai
Requer: internet
Objetivo: trazer a skill de aulas da Julie para o repositório como papel `aulas`, com o gerador e os assets como arquivos, testada.
Arquivos permitidos: skills/aulas/**, agents/editorial/aulas.md, pyproject.toml, uv.lock, tests/test_aulas.py
Critérios de aceite:
- `skills/aulas/SKILL.md` com o conteúdo da skill da Julie, adaptado só onde o ambiente muda: os caminhos apontam para `scripts/` e `assets/` da própria skill, sem ler do Project; `name: aulas`; description até 1.024 caracteres. O visual e as regras dela não mudam.
- `skills/aulas/scripts/clinic_deck.py` e `bold_deck.py` como a Julie entregou, mudando só o caminho dos assets; `skills/aulas/assets/` com os 16 arquivos de `assets_b64.json` decodificados; `skills/aulas/references/exemplo_roteiro.json`.
- `python-pptx` no `pyproject.toml` (Pillow já vem pelo WeasyPrint); `uv.lock` atualizado.
- `agents/editorial/aulas.md`: `model: sonnet`, `effort: medium`, `maxTurns: 40`, `skills: [aulas]`.
- Testes: `test_example_script_builds_pptx` (o roteiro de exemplo gera um .pptx que abre no python-pptx, com os slides do roteiro mais os inseridos automaticamente), `test_prompts_markdown_written`, `test_partnership_slides_inserted_by_default`, `test_partnerships_can_be_disabled`.
- `package.py --sync` rodado.
Verificação: uv run --locked pytest tests/test_aulas.py -q && uv run --locked python scripts/package.py --check

#### Cartão 7.2: Estilo da casa nas imagens
Função: ai
Objetivo: a skill `imagens` adota a paleta do logo e o texto de estilo da casa da Julie.
Arquivos permitidos: skills/imagens/SKILL.md, skills/imagens/references/**, shared/references/identidade-visual.md, skills/*/references/comum/**
Critérios de aceite:
- `paleta.md` com a paleta do logo da spec 9.2, cada valor com a origem (design system da Julie); o marsala do pedido da Paula é o vinho `#9C4C48`; sai a marca "a confirmar com a Paula".
- O briefing termina todo prompt com o texto de estilo da casa da Julie, versão ilustração ou versão foto, copiado literalmente do design system.
- A regra dos livros continua: imagem complementar só conceitual, sem anatomia, pele, procedimento, produto de marca ou resultado.
- `identidade-visual.md` registra a paleta do logo e diz que a cor dos livros espera a escolha do Alify (spec 9.2).
- `package.py --sync` rodado.
Verificação: grep -q "9C4C48" skills/imagens/references/paleta.md && ! grep -q "a confirmar com a Paula" skills/imagens/references/paleta.md && uv run --locked python scripts/package.py --check

#### Cartão 7.3: Páginas de amostra nas duas paletas
Função: frontend
Objetivo: renderizar as três páginas de amostra do livro com a paleta do logo, ao lado das atuais, para o Alify escolher a cor dos livros.
Arquivos permitidos: docs/medicoes/paleta/**, scripts/render_palette_samples.py
Critérios de aceite:
- `scripts/render_palette_samples.py` renderiza `tests/samples/amostra.html` duas vezes, com o `tokens.css` atual e com uma cópia temporária em que as cores vêm da paleta do logo, sem alterar o `tokens.css` do repositório.
- `docs/medicoes/paleta/` com as três páginas em PNG de cada paleta e um `comparacao.md` com as duas lado a lado e a lista de cores trocadas.
Verificação: test -s docs/medicoes/paleta/comparacao.md && ls docs/medicoes/paleta/*.png | wc -l | grep -q 6

#### Cartão 7.4: Editor-Chefe aciona as aulas
Função: ai
Objetivo: a tabela de gatilhos do Editor-Chefe passa a acionar `aulas`.
Arquivos permitidos: skills/editor-chefe/SKILL.md, skills/editor-chefe/references/fluxo.md
Critérios de aceite:
- Gatilho novo: pedido de produzir ou refazer uma aula aciona `aulas`; a aula gerada volta ao Editor-Chefe pelo bloco de retorno e vai para a pessoa conferir (não há portão de nota para aulas na V1).
- O fluxo diz que o roteiro em JSON da aula pode ser entregue ao `editor-cientifico` como fonte estruturada dos slides.
Verificação: grep -q "aulas" skills/editor-chefe/SKILL.md && uv run --locked python scripts/package.py --check

## Status
- Feito (18 e 19/11/2026, onda 1 e onda 2, PR da `feat/wave-1`):
  - 1.1 base do repositório e `package.py --check` e `--sync`; 1.2 referências comuns; 1.3 skill e agente do Editor-Chefe; 1.6 hooks do plugin; 1.7 ajustes vindos do ensaio (cartão novo, achados 3 a 7 de `docs/medicoes/2026-11-ensaio-editor-chefe.md`).
  - 1.4 ensaio do Editor-Chefe no Claude Code 2.1.325: `Resultado: APROVADO` nos cinco casos; a variante de chat ficou não conclusiva até existirem as skills dos outros papéis.
  - 2.1 e 2.2 checagens de PDF (`lib/pdfcheck/`), 2.3 skill e roteiro do teste no ChatGPT.
- Em andamento: revisão final do PR da onda 1.
- Travado: 1.5 (apresentação à Paula) fica com o Alify, junto com o envio do repositório, sem travar a construção; 2.4 e 6.3 esperam a Paula, sem travar a construção; 3.6 espera o Alify; o manual de diagramação (a Paula manda depois) e o design system dos documentos (Alify, Paula e Julie) ainda não existem: o 3.5 nasce com o lugar do manual e o 3.1 com os valores visuais em `tokens.css`, e cada um vira um cartão novo quando chegar.
- Pendências para cartões seguintes: achado 1 do ensaio (manifesto do plugin) no 6.1; achado 2 (leitura de `references/` em sessão não interativa precisa de `--add-dir` ou sessão interativa) no guia da equipe, 6.2; o lembrete da ficha no `Stop` não foi exercido no ensaio; repetir a variante de chat depois da onda 4.
- Próximo passo: merge da onda 1 depois da revisão final; onda 3 (Diagramador e imagens) numa branch `feat/wave-3`, com os cartões 3.1 a 3.8.
