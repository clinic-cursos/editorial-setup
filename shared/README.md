# Referências comuns da Clinic Editora

Todos os papéis consultam estas referências antes de executar uma tarefa editorial.

- [Governança](references/governanca.md) define as responsabilidades, as aprovações humanas e o tratamento de divergências.
- [Identidade visual](references/identidade-visual.md) reúne os padrões do miolo e dos componentes editoriais.
- [Glossário](references/glossario.md) fixa o vocabulário do fluxo.
- [Manuscrito](references/manuscrito.md) define o formato que o Editor Científico-Didático produz e que segue para a diagramação após a aprovação técnica.
- [Retorno](references/retorno.md) define o bloco que os papéis devolvem ao Editor-Chefe.

## Cópia para as skills

As partes comuns são copiadas para dentro de cada skill por `uv run python scripts/package.py --sync`:

- `shared/references/` e `shared/rules/` vão para `skills/<skill>/references/comum/` (toda skill com `SKILL.md`).
- `lib/pdfcheck/` vai para `skills/<skill>/scripts/pdfcheck/` (`diagramador`, `imagens`, `auditor-grafico`).

Não edite as cópias: edite a origem e rode `--sync`. O `--check` falha se houver deriva.
