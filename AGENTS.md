# Regras do time: editorial-setup

Setup editorial de IA da Clinic Editora com oito papéis como skills de fonte única (`skills/`), empacotados para ChatGPT, claude.ai, Claude Code e Codex.

## Governança (spec, seção 2)
- Agente nunca aprova no lugar de pessoa. João aprova o conteúdo técnico; Paula aprova a versão e libera a impressão. Nota alta não libera nada para impressão.
- Texto científico aprovado não muda em silêncio pela diagramação.
- Nada de referência inventada nem de afirmação clínica sem fonte apresentada como fato.
- Imagem com conteúdo anatômico ou clínico só entra com validação científica.
- Divergência com o Board vai para avaliação humana.

## Idioma
- `SKILL.md`, referências, guias e mensagens para a Paula em português.
- Código, nomes de função, chaves de JSON e commits em inglês (Conventional Commits). Nomes de skill e de agente em português sem acento.
- Sem travessão em nenhum texto entregue.

## Repositório
- Nada de conteúdo de livro, foto clínica ou dado de aluno no git. Livros reais vêm de `EDITORIAL_SAMPLES_DIR`; `projetos/` é ignorado.
- Sem pasta `bin/` no topo. Bibliotecas dos scripts: biblioteca padrão, pdfplumber, pypdf, WeasyPrint, python-docx. PyMuPDF proibido (AGPL); ReportLab só em `tests/`.
- Cópias em `skills/*/references/comum/` e `skills/*/scripts/pdfcheck/` são geradas: `uv run python scripts/package.py --sync`; conferidas por `--check`.
- Testes: `uv run --locked pytest`. Commit atômico, `git add` pelo nome do arquivo.
