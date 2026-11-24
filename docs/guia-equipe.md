# Guia da equipe

## Preparar os pacotes

Use Python 3.12 e `uv`. Na raiz do repositório, com o cartão 6.1 de empacotamento integrado, rode:

```sh
uv run --locked python scripts/package.py --check
uv run --locked pytest
uv run --locked python scripts/package.py --build
```

Se você alterou as fontes compartilhadas em `shared/` ou `lib/pdfcheck/`, rode `uv run --locked python scripts/package.py --sync` antes de validar e gerar os pacotes. Faça as alterações nas fontes para que as cópias em cada skill sejam atualizadas juntas.

| Saída | Uso |
| --- | --- |
| `dist/chatgpt/<papel>.zip` | Skills do ChatGPT. |
| `dist/chatgpt-projeto/` | Instruções e fontes para Projetos do ChatGPT sem upload de skills. |
| `dist/claude-ai/<papel>.zip` | Skills do claude.ai. |
| `dist/codex/agents/<papel>.toml` | Definições dos agentes do Codex. As pastas das skills vêm de `skills/`. |
| `.claude-plugin/` na raiz | Manifestos do plugin e do marketplace para Claude Code e Cowork. |
| `.codex-plugin/` na raiz | Manifesto do plugin para Codex. |

Distribua os pacotes de uma mesma versão. Mantenha `dist/` fora do Git. Para o fluxo do ChatGPT, envie também o [guia da Paula](guia-paula.md).

## Claude Code

Para produzir aulas com prévia, o computador precisa de Python 3.12 com `uv`, LibreOffice com `soffice` e `pdftoppm` no `PATH`, além da fonte Montserrat instalada. Confira com `uv run --locked python skills/aulas/scripts/aulas.py previa <deck> <pasta>`.

1. Na raiz do checkout, valide o plugin com `claude plugin validate .`.
2. Para uma sessão com o plugin local, rode `claude --plugin-dir .` na raiz. Para instalar pelo catálogo da equipe, use `/plugin marketplace add /caminho/para/editorial-setup` em uma sessão, abra `/plugin` e instale `clinic-editorial` na aba **Discover** do marketplace `clinic-editora`.
3. Inicie o livro com `/clinic-editorial:editor-chefe` na conversa principal. Informe o caminho da ficha e a fase desejada. O Editor-Chefe aciona os demais papéis como subagentes.

Se a sessão não interativa negar a leitura das referências, passe também o diretório absoluto do plugin em `--add-dir` ou use uma sessão interativa. O [ensaio do Editor-Chefe](medicoes/2026-11-ensaio-editor-chefe.md) registrou esse caso.

[Plugins no Claude Code](https://code.claude.com/docs/en/plugins) · [Configurar um marketplace](https://code.claude.com/docs/en/plugin-marketplaces)

## Cowork

1. A administração da organização conecta o repositório privado do plugin em **Organization settings > Plugins & skills > Marketplaces**. Selecione a versão com o manifesto `.claude-plugin/marketplace.json`.
2. Com a conta da Clinic no Claude Desktop, abra **Customize > Plugins > Discover**, selecione `clinic-editorial` e clique em **Add**.
3. Abra uma sessão no Cowork e selecione a pasta de trabalho do livro. Na conversa principal, peça ao Editor-Chefe que leia a ficha e conduza a próxima fase com os agentes do plugin.

[Publicar no marketplace da organização](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization) · [Instalar plugins no Claude](https://support.claude.com/en/articles/14328846-browse-skills-connectors-and-plugins-in-one-directory)

## claude.ai

1. Confirme que a execução de código e a criação de arquivos estão habilitadas para a conta.
2. Abra **Customize > Skills**, clique em **+ > Create skill > Upload a skill**, envie um ZIP por papel de `dist/claude-ai/` e ative cada skill. Se o upload rejeitar o ZIP por faltar a pasta da skill, compacte a pasta inteira de `skills/<papel>/`, com seu nome e o `SKILL.md` dentro, e envie esse ZIP.
3. Crie um Projeto por livro. Peça explicitamente a skill `editor-chefe` na conversa principal. Os papéis rodam em sequência no chat. Abra uma conversa nova para a auditoria científica e leve apenas o pacote de auditoria. Substitua manualmente a ficha nos arquivos do Projeto ao fim de cada fase.

[Carregar skills no Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude)

## Codex local

Para produzir aulas com prévia, o computador precisa de Python 3.12 com `uv`, LibreOffice com `soffice` e `pdftoppm` no `PATH`, além da fonte Montserrat instalada. Confira com `uv run --locked python skills/aulas/scripts/aulas.py previa <deck> <pasta>`.

1. Na pasta de trabalho que você vai abrir no Codex, copie as pastas completas dos papéis de `skills/` para `.agents/skills/`. Cada papel deve ficar em `.agents/skills/<papel>/SKILL.md`, com suas referências, scripts e recursos.
2. Copie os arquivos `.toml` de `dist/codex/agents/` para `.codex/agents/` na pasta de trabalho. Para disponibilizar os agentes em todas as sessões locais, use `~/.codex/agents/` e mantenha as skills acessíveis a partir de cada pasta de trabalho.
3. Abra o Codex na pasta de trabalho e selecione `$editor-chefe` na conversa principal. Informe o caminho da ficha e peça a fase seguinte. O Editor-Chefe aciona os demais agentes conforme a fase.

[Skills locais do Codex](https://learn.chatgpt.com/docs/build-skills) · [Subagentes do Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents)

## Trabalhar com livros

Em ambiente local, use `<pasta de trabalho>/projetos/<projeto>/` fora deste repositório. Guarde a `ficha.md` junto de `originais/`, `versoes/` e `relatorios/`. Preserve os originais e as versões aprovadas. Faça alterações em versões novas.

Para diagramação local, prepare as dependências com `uv sync --locked` na raiz do repositório. No terminal, ative o ambiente Python gerado antes de abrir a sessão que vai rodar os scripts. Em Bash, use `source /caminho/para/editorial-setup/.venv/bin/activate`. Se o ChatGPT ou o claude.ai não executar o WeasyPrint, rode a diagramação e a auditoria gráfica no Claude Code ou no Codex e devolva o pacote da fase a quem conduz o livro.

Comece com material sintético para conferir se o Editor-Chefe lê as regras, encaminha o pedido e devolve a ficha. Registre a plataforma e o resultado em `docs/medicoes/`, sem trechos de livro, fotos clínicas ou dados de alunos.

## Trabalhar com aulas

Envie um destes pedidos ao Editor-Chefe com os arquivos do projeto:

- “Crie uma aula do zero para [curso] a partir do conteúdo anexado, no estilo padrão da Clinic.”
- “Refaça o deck ou slide anexado no design system novo. Preserve o sentido do conteúdo.”
- “Entregue só um slide sobre [tema] usando o material anexado. Para uma correção, use o slide [número] e aplique [ajuste].”

`aulas` dirige o roteiro e usa `aulas.py` para produzir a versão, o relatório e a prévia. Para gerar a prévia, o ambiente precisa de `soffice` e `pdftoppm`. O Editor-Chefe envia a versão ao `revisor-aulas` antes de encaminhar o .pptx à pessoa.
