# Setup editorial da Clinic Editora

Oito papéis de IA ajudam a transformar slides e apostilas em livros e a produzir aulas no padrão da Clinic. As mesmas skills são distribuídas para ChatGPT, Claude Code, Cowork, claude.ai e Codex.

- [Guia da Paula](docs/guia-paula.md) para instalar no ChatGPT e conduzir um livro.
- [Guia da equipe](docs/guia-equipe.md) para empacotar e instalar nas demais plataformas.

## Papéis

| Papel | Skill | Entrega |
| --- | --- | --- |
| Editor-Chefe | [`editor-chefe`](skills/editor-chefe/SKILL.md) | Ficha do livro, encaminhamento de cada fase e pacote para decisão humana. |
| Editor Científico | [`editor-cientifico`](skills/editor-cientifico/SKILL.md) | Manuscrito ampliado, rastreabilidade das fontes e correspondência entre slides e capítulos. |
| Auditor Científico | [`auditor-cientifico`](skills/auditor-cientifico/SKILL.md) | Relatório independente com achados e nota da ampliação. |
| Diagramador | [`diagramador`](skills/diagramador/SKILL.md) | Fonte editável em HTML, PDF A4, mapa de páginas e checagem de layout. |
| Imagens | [`imagens`](skills/imagens/SKILL.md) | Imagens conceituais ou briefings para preencher espaços do livro. |
| Auditor Gráfico | [`auditor-grafico`](skills/auditor-grafico/SKILL.md) | Relatório por página e nota da diagramação e da reinserção de imagens. |
| Aulas | [`aulas`](skills/aulas/SKILL.md) | PowerPoint editável, roteiro, checagem automática e prévia, gerados pela ferramenta de aulas. |
| Revisor de Aulas | [`revisor-aulas`](skills/revisor-aulas/SKILL.md) | Revisão independente de cada slide, com nota e achados antes da entrega. |

João aprova o conteúdo técnico. Paula aprova a versão editorial e gráfica e libera a impressão. As notas das auditorias orientam o fluxo entre fases.

## Onde fica cada coisa

| Caminho | Conteúdo |
| --- | --- |
| [`skills/`](skills/) | Fonte das instruções, referências, scripts e recursos de cada papel. |
| [`agents/editorial/`](agents/editorial/) | Definições dos agentes do Claude, usadas para gerar os TOML do Codex. |
| [`shared/`](shared/) e [`lib/pdfcheck/`](lib/pdfcheck/) | Referências, regras e checagens compartilhadas. |
| [`hooks/`](hooks/) | Travas do plugin do Claude Code. |
| [`scripts/package.py`](scripts/package.py) e `dist/` | Empacotador e saídas geradas. Os manifestos dos plugins ficam em `.claude-plugin/` e `.codex-plugin/`. |
| [`tests/`](tests/) e [`docs/medicoes/`](docs/medicoes/) | Testes automatizados e registros dos ensaios. |
| [`docs/fontes/`](docs/fontes/) | Instruções e referências editoriais. |
| [Melhorias](docs/melhorias.md) e [histórico de versões](CHANGELOG.md) | Sugestões da equipe e mudanças publicadas. |

Guarde livros reais, fotos clínicas e dados de alunos fora do Git. Para ensaios com livros reais, aponte `EDITORIAL_SAMPLES_DIR` para a pasta autorizada com as amostras.

## Testar e empacotar

Na raiz do repositório, com Python 3.12 e `uv`:

```sh
uv run --locked pytest
uv run --locked python scripts/package.py --check
uv run --locked python scripts/package.py --build
```

O `--build` requer a versão com o cartão 6.1 integrado. Depois de editar as fontes compartilhadas, rode `uv run --locked python scripts/package.py --sync` para atualizar as cópias nas skills. O [guia da equipe](docs/guia-equipe.md#preparar-os-pacotes) descreve as saídas de cada plataforma.

[Spec editorial](docs/superpowers/specs/2026-11-18-editorial-setup-design.md) · [Plano de execução](docs/superpowers/plans/2026-11-18-editorial-setup.md)
