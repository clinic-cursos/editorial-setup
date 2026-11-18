# Pesquisa: setup editorial de IA, Bloco A, plataformas (stack)

Data: 2026-11-18. Agente: stack-researcher. Modelo: claude-opus-5-5.

Regras deste documento:
- Toda afirmação factual leva `[Fn]` na linha e uma entrada na Tabela de fontes.
- Padrão de evidência, em ordem: medição própria, documentação oficial datada, página oficial de preço, benchmark reproduzível. Fonte secundária só serve de pista e leva `[secundária]`. Memória do modelo nunca conta como prova.
- Afirmação sem trecho que a sustente sai do texto e vai para "Não sei".
- Preço sempre em duas colunas, promoção e renovação, com prazo de contrato e moeda. Opção gratuita sempre aparece.
- Limite sempre com o plano (Free, Pro, Enterprise) e se é "padrão, ajustável".

Observação de leitura: as páginas do OpenAI Help Center (`help.openai.com`, inglês e pt-br) devolveram HTTP 403 ao WebFetch em 2026-11-18. As respostas sobre ChatGPT vêm da documentação oficial em `learn.chatgpt.com` (para onde `developers.openai.com/codex` redireciona com 308), de `developers.openai.com/plugins` e da OpenAI Academy. Trechos marcados "média" foram citados pelo extrator do WebFetch entre aspas, não lidos em HTML bruto.

## Pergunta e escopo
Quais plataformas recebem o time editorial (Editor-Chefe, Diagramador, Editor Científico-Didático, Auditor Científico, Auditor Gráfico, agente de imagens) empacotado como skills: ChatGPT, Codex e Claude; o que o padrão Agent Skills garante de portabilidade; e quanto custa gerar imagem por API fora da interface. Fora deste relatório: ferramentas de diagramação e ABNT (Bloco B, `stack-layout.md`), hospedagem da VPS e LGPD (eixos de infra e risco). Não escolhe a solução.

## Premissas numéricas
Copiadas do brief.
- Pico: não informado no brief (uso interno; número de usuários simultâneos não informado). Equipe: a Paula na aprovação editorial e "a equipe interna".
- Dados: entrada típica de 1 PDF A4 de 84 páginas por livro; saída de cerca de 80 páginas. Volume de livros por mês: não informado no brief.
- Imagens: "espaços muito vazios" em "várias páginas"; número de imagens por livro não informado no brief.
- Região e LGPD: não informado no brief (fora deste eixo).
- Orçamento (BRL/mês): padrão grátis, usar o que as assinaturas do ChatGPT e do Claude já incluem; API paga só com preço e alternativa grátis. Planos das assinaturas atuais: não informado no brief.

## Requisitos derivados
| Requisito | Conta | Valor | Limite publicado | Fonte | Folga (limite ÷ valor) |
|---|---|---|---|---|---|
| Nº de skills do time | 6 papéis, 1 skill cada | 6 | Codex: lista inicial de skills usa no máximo 2% da janela de contexto, ou 8.000 caracteres sem janela conhecida; ajustável até 10.000 tokens | [F6] | 8.000 ÷ (6 × ~1.090 car. de `name`+`description` no máximo) ≈ 1,2 no pior caso; com descrições de ~300 car. ≈ 4,4 |
| `name` de cada skill | nome em kebab-case | ex.: `editor-chefe` (12 car.) | 64 caracteres, minúsculas, números e hífen | [F1][F16] | 5,3 |
| `description` | o que faz e quando usar | não medido | 1.024 caracteres | [F1][F16] | depende do texto |
| Corpo do `SKILL.md` | manual técnico da editora | não informado no brief (tamanho do manual) | recomendado < 5.000 tokens e < 500 linhas; resto em `references/` | [F2][F16] | medir o manual |
| Imagens por livro via API | imagens × preço por imagem | não informado no brief | preço por token publicado; preço por imagem não lido | [F18] | ver "Não sei" |

Folga abaixo de 2,0: a lista de skills no Codex só fica apertada se as seis `description` chegarem perto de 1.024 caracteres; manter cada uma abaixo de ~300 caracteres dá folga acima de 4.

## Candidatos

### Visão geral
| Opção | O que é | Preço promoção | Preço renovação | Limites relevantes | Saída e dependência | Fontes |
|---|---|---|---|---|---|---|
| Agent Skills (padrão aberto) | Pasta com `SKILL.md` (frontmatter YAML + Markdown) e pastas opcionais `scripts/`, `references/`, `assets/` | grátis (especificação aberta) | grátis | `name` 1-64, `description` 1-1024, `compatibility` 1-500; corpo < 500 linhas | Base comum; cada produto acrescenta campos próprios | [F1][F2] |
| Claude (claude.ai, Claude Code, API) | Skills customizadas em zip no claude.ai; pasta `~/.claude/skills/` ou `.claude/skills/` no Claude Code; plugins com `.claude-plugin/plugin.json` | já incluído nos planos Pro, Max, Ultra, Team e Enterprise (preço do plano não lido) | idem | skills não sincronizam entre superfícies; `name` sem `anthropic`/`claude`; no claude.ai precisa de execução de código ligada | Plugin com `skills/`, `agents/`, `commands/`, `hooks/`; `bin/` impede instalação no claude.ai e no Cowork | [F16][F17] |
| Codex (CLI, IDE, app, ChatGPT Work) | Skills em `.agents/skills` (repo) e `$HOME/.agents/skills` (usuário); subagentes em TOML; plugins `.codex-plugin/plugin.json` | Plus US$ 20/mês; Business US$ 20/usuário/mês anual ou US$ 25 mensal; Pro a partir de US$ 100/mês | mesmos valores (sem promoção publicada para o plano) | lista inicial de skills ≤ 2% do contexto; geração de imagem consome o limite 3 a 5 vezes mais rápido; sem imagem no Free | Skills seguem o padrão aberto; subagentes só nos clientes locais via arquivo | [F6][F9][F10][F12] |
| ChatGPT (web, desktop, mobile) | Skills (`@` mention), Projetos, plugins (diretório universal com o Codex), GPTs | incluído no plano (plano por recurso: ver "Não sei") | idem | skills em beta, desligadas por padrão no workspace; skills só usam ferramentas que o ChatGPT já tem | Plugin com skills funciona em Chat e Work na web, desktop e mobile | [F5][F7][F8] |
| Geração de imagem por API (OpenAI) | `gpt-image-2` e família | sem promoção; Batch pela metade | US$ 8/1M tokens de entrada de imagem, US$ 30/1M de saída (`gpt-image-2`); por imagem 1024×1536: US$ 0,005 baixa, 0,041 média, 0,165 alta | prompt complexo até 2 min | API paga, chave `OPENAI_API_KEY` | [F18][F23][F9] |
| Geração de imagem por API (Google Gemini) | `gemini-nano-banana-2.1` e outros | Batch US$ 0,0168 por imagem 1K | US$ 0,0336 por imagem 1K; US$ 0,0504 por 2K | sem nível gratuito para imagem | API paga | [F24] |
| Alternativa gratuita para imagem | geração dentro das assinaturas (ChatGPT web, Codex) | grátis dentro do limite do plano | idem | Codex: conta no limite geral, 3 a 5 vezes mais rápido; Free sem imagem; Claude não gera imagem | não é API; não roda na VPS | [F9][F12][F20] |

### A1. ChatGPT: skills no formato Agent Skills
- Formato: a skill tem um `SKILL.md` com nome, descrição e instruções [F4]; a documentação do Codex/ChatGPT diz que "Skills build on the open agent skills standard" [F6].
- Invocação: "ChatGPT supports `@` mentions, while Codex supports `$` mentions for skills." [F7]
- Criação: pelo criador nativo `@skill-creator` no ChatGPT [F15][F7], ou "you can also build skills outside of ChatGPT and upload them" [F5].
- Estado: "During the initial beta, skills are off by default—workspace owners can enable them in workspace settings." (página publicada em 25/02/2026, atualizada em 17/09/2026) [F5].
- Superfícies: skills avulsas no app desktop do ChatGPT, no Codex CLI e na extensão de IDE; skills dentro de plugins também em Chat e Work na web, desktop e mobile [F6]. Plugins funcionam em "Chat and Work across ChatGPT on the web, desktop, and mobile" e "They aren't available in the IDE extension" [F8].
- Ferramentas: "Skills only instruct ChatGPT to use the tools and apps it already has access to" [F5]. Ou seja, a skill não traz ferramenta nova; usa a geração de imagem e o Python do ChatGPT só se a conversa já os tiver. Se uma skill dispara de fato a geração nativa e o Python dentro dela: não lido (ver "Não sei").
- Planos e upload em zip: o Help Center oficial bloqueou a leitura (403). Fontes secundárias divergem: um guia lista upload para "Plus / Pro / Business" [F19 secundária]; outros dizem que só Business, Enterprise, Edu e Healthcare têm skills [F19 secundária]. Ver "Não sei".
- Limites de tamanho, número de skills e arquivos no ChatGPT: não publicados nas páginas lidas [F5][F7].

### A2. Alternativas no ChatGPT
- Projetos: "A ChatGPT project gives its chats access to the same uploaded files, project instructions, and connected sources." [F11]. Um projeto "doesn't provide direct access to a folder on your computer" [F11]. Limites de arquivos por plano e de instruções: não lidos em fonte oficial; uma fonte secundária fala em 5 arquivos no Free, 25 no Plus/Go e 40 no Pro/Business [F19 secundária].
- Plugins (antigos apps/conectores + skills): "an installable bundle that can include skills and Model Context Protocol (MCP) servers" [F7]; "ChatGPT and Codex share one universal plugin directory." [F7]. Plugins podem ser criados e editados na web quando o workspace permite [F13].
- GPTs personalizados: "Custom GPTs in ChatGPT Enterprise are being retired." [F13]; a OpenAI publica um guia de migração de GPTs para plugins (`migrate-custom-gpts.md`, não lido). Limites de instruções e arquivos de GPT: não lidos.
- Memória entre conversas: o Projeto guarda arquivos, instruções e fontes conectadas [F11]; memória própria do projeto não aparece na página lida [F11].

### A3. Codex
- Onde ficam as skills: `$CWD/.agents/skills` subindo até a raiz do repositório, `$HOME/.agents/skills`, `/etc/codex/skills` e as do sistema (`skill-creator`, `skill-installer`) [F6].
- Metadado próprio opcional: `agents/openai.yaml` (interface, `policy.allow_implicit_invocation`, `dependencies.tools`) [F6][F15].
- Plugin e diretório: plugins empacotam skills e servidores MCP; diretório único com o ChatGPT [F7]. Manifesto `.codex-plugin/plugin.json`; o portal converte `.claude-plugin/plugin.json` num upload direto de plugin do Claude [F14].
- Subagentes: "add standalone TOML files under `~/.codex/agents/` for personal agents or `.codex/agents/` for project-scoped agents." [F10]; campos obrigatórios `name`, `description`, `developer_instructions` [F10]; ChatGPT Work também roda subagentes no ambiente hospedado, mas arquivos de agente customizado valem só nos clientes locais [F10]; "subagent workflows consume more tokens than comparable single-agent runs" [F10].
- Imagem: "Built-in image generation uses `gpt-image-2`." [F9], no app, CLI, IDE e ChatGPT web; `$imagegen` invoca a skill de imagem [F9]. Custo: "counts toward your general Codex usage limits", 3 a 5 vezes mais rápido que um turno sem imagem [F9]; depois do limite, consome créditos (GPT-Image-2: 200 entrada, 50 entrada em cache, 750 saída créditos por milhão de tokens); sem imagem no Free [F12]; com `OPENAI_API_KEY`, cobra pelo preço da API [F9][F12].
- Planos (USD/mês): Free US$ 0; Go US$ 8; Plus US$ 20; Pro a partir de US$ 100 (US$ 100, 200 ou 500); Business US$ 20 por usuário no anual (2+ usuários) ou US$ 25 no mensal; Enterprise e Edu sob consulta [F12].

### A4. Claude
- Upload no claude.ai: "Upload your own Skills as zip files. Available on Pro, Max, Ultra, Team, and Enterprise plans with code execution enabled." [F16]
- Claude Code: skills em `~/.claude/skills/` (pessoal) ou `.claude/skills/` (projeto), sem upload [F16].
- Não sincroniza: "Custom Skills do not sync across surfaces" [F16]; claude.ai, API e Claude Code são geridos separadamente [F16].
- Restrições do `name` além do padrão: não pode conter tags XML nem as palavras reservadas `anthropic` e `claude` [F16].
- Ambiente: no claude.ai a rede da skill pode ser total, parcial ou nenhuma, conforme configuração [F16]; na API, sem rede e sem instalar pacote [F16]; no Claude Code, rede total [F16].
- Plugin do Claude Code: "Save the manifest at `.claude-plugin/plugin.json` under the plugin root." [F17]; "The manifest is optional." [F17]; só `name` é obrigatório [F17]; pastas padrão `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json` [F17]; `commands/` vem com a nota "Prefer `skills/` for new plugins" [F17].
- Claude Desktop e Cowork: a referência diz que "claude.ai and Cowork don't install a plugin that has this directory" sobre `bin/` [F17]; a distribuição pelas configurações da organização rejeita plugin com `bin/` no topo [F21].
- Subagentes fora do Claude Code: "Hooks and agents load in Cowork and Claude Code and not in chat, and a local MCP server doesn't run in chat." [F22]. Ou seja, `agents/` funciona no Cowork e no Claude Code; no chat do claude.ai, não.
- Distribuição para a equipe: sincronizar um repositório GitHub privado com `.claude-plugin/marketplace.json` em Configurações da organização > Plugins & skills; os membros recebem o plugin no chat, no Cowork e no Claude Code [F21][F22]. Essa rota é descrita para planos Team ou Enterprise [F22]; o repositório do marketplace precisa ser privado ou interno no github.com [F21].
- Varredura de conteúdo: organizações Enterprise podem ligar a varredura de skills enviadas no claude.ai e no Cowork [F16].
- Imagem raster nativa: não. "No, Claude is an image understanding model only. It can interpret and analyze images, but it cannot generate, produce, edit, manipulate, or create images." [F20]. Para imagem, o time no Claude precisa de ferramenta externa (API de imagem via script ou MCP).

### A5. Agent Skills como padrão aberto
- Campos: `name` (obrigatório, 1-64, minúsculas, números e hífen, sem hífen no início, no fim ou duplo, igual ao nome da pasta), `description` (obrigatório, 1-1024), `license`, `compatibility` (1-500), `metadata` (mapa texto→texto), `allowed-tools` (experimental) [F1].
- Tamanho: metadados ~100 tokens; corpo "< 5000 tokens recommended"; "Keep your main `SKILL.md` under 500 lines." [F2]
- Pastas: `scripts/` (código executável; linguagens dependem do agente), `references/` (carregadas sob demanda), `assets/` (modelos, imagens, dados) [F2].
- Quem adota: OpenAI declara que as skills do Codex/ChatGPT se baseiam no padrão [F6]; a Anthropic usa o mesmo par `name`/`description` com os mesmos limites de 64 e 1.024 [F16]. A página "Client Showcase" do agentskills.io não renderizou a lista no WebFetch [F3].
- Mesmo `SKILL.md` sem mudança nos três: não há garantia publicada. Diferenças documentadas: Claude proíbe `claude`/`anthropic` no `name` [F16]; Codex lê `agents/openai.yaml` à parte [F6]; o guia da OpenAI para portar plugin do Claude manda "replace Claude-specific references in skill instructions with provider-neutral language" (citação do extrator) e testar num ambiente limpo [F14]; comandos e agentes do Claude não são suportados como tais no lado OpenAI e viram skills [F14]; no claude.ai e na API, script só roda com execução de código, e na API sem rede [F16].

### A6. Geração de imagem por API
- Modelo atual da OpenAI usado pelo Codex: `gpt-image-2` [F9].
- Preço por token (USD, padrão): `gpt-image-2` imagem US$ 8,00 entrada, US$ 30,00 saída, US$ 2,00 entrada em cache; texto US$ 5,00 entrada [F18]. Batch de `gpt-image-2`: US$ 4,00 entrada e US$ 15,00 saída de imagem [F18]. `gpt-image-1-mini`: US$ 2,50 entrada, US$ 8,00 saída de imagem [F18]. A página lista também `gpt-image-2.5-*` e `gpt-image-2.6-*` (`sunburst`, `flare`) com os mesmos US$ 8/US$ 30 [F18].
- Preço por imagem (USD, tabela "Historical output costs" do guia) [F23]:

| Modelo | Qualidade | 1024×1024 | 1024×1536 | 1536×1024 |
|---|---|---|---|---|
| GPT-Image-2 | baixa | 0,006 | 0,005 | 0,005 |
| GPT-Image-2 | média | 0,053 | 0,041 | 0,041 |
| GPT-Image-2 | alta | 0,211 | 0,165 | 0,165 |
| GPT Image 1 mini | baixa | 0,005 | 0,006 | 0,006 |
| GPT Image 1 mini | média | 0,011 | 0,015 | 0,015 |
| GPT Image 1 mini | alta | 0,036 | 0,052 | 0,052 |

  O guia trata a família 2.6 como atual ("Image output costs $30 per million billable tokens") e não dá tokens por imagem do `gpt-image-2`, só uma calculadora [F23]. Latência: "Complex prompts may take up to 2 minutes to process." [F23]. Data de lançamento de `gpt-image-2.6`: não lida.
- Conta de exemplo (não é medição): 20 imagens por livro em qualidade média 1024×1536 no GPT-Image-2 = 20 × US$ 0,041 = US$ 0,82 por livro [F23]; em qualidade alta, 20 × US$ 0,165 = US$ 3,30. O número de imagens por livro não está no brief.
- Alternativa Google (API Gemini, só nível pago): `gemini-nano-banana-2.1` US$ 0,0336 por imagem 1K e US$ 0,0504 por 2K (Batch US$ 0,0168 por 1K); `gemini-3.1-flash-image` US$ 0,067 por 1K; `gemini-3-pro-image` US$ 0,134 por imagem 1K/2K; nível gratuito "Not available" em todos; `gemini-2.5-flash-image` será desligado em 15/03/2027 [F24]. Preço do Imagen: não lido (página truncada).
- Alternativa gratuita por API: nenhuma encontrada nas páginas oficiais lidas (OpenAI sem nível grátis de imagem na tabela; Google "Not available") [F18][F24]. Alternativa grátis dentro da assinatura: geração nativa no ChatGPT web e no Codex, sem API, consumindo o limite do plano [F9][F12]. Modelo aberto rodando na própria máquina: não pesquisado (ver "Não sei").

## Medições
Nenhuma medição feita. Este agente não tem shell nesta tarefa e não pode logar no ChatGPT nem no claude.ai. Teste proposto, a rodar por quem tiver as contas:
1. Criar a pasta `editor-chefe/SKILL.md` só com `name` e `description` do padrão e corpo neutro (sem citar produto).
2. Zipar com `SKILL.md` na raiz e enviar no ChatGPT (Skills → Create → Upload) e no claude.ai (configurações → Skills); copiar para `.agents/skills/` (Codex) e `.claude/skills/` (Claude Code).
3. Registrar: aceitou ou não, mensagem de erro, se a skill disparou por `@`/`$`/nome, e se pediu a geração de imagem e o Python dentro da skill.

## Riscos observados
| Risco | Opção | Probabilidade | Impacto | Mitigação | Fonte |
|---|---|---|---|---|---|
| Skills no ChatGPT em beta e desligadas por padrão no workspace | ChatGPT | alta | alto | confirmar no painel do plano atual antes do desenho | [F5] |
| Plano da assinatura atual pode não ter upload de skill (fontes divergem) | ChatGPT | média | alto | teste da seção Medições; plano B: Projeto com instruções e arquivos | [F19 secundária][F11] |
| Skills não sincronizam entre claude.ai, API e Claude Code | Claude | certa | médio | repositório único como fonte e upload por superfície | [F16] |
| `name` com `claude` ou `anthropic` é recusado no Claude | Claude | baixa | baixo | nomes em português sem essas palavras | [F16] |
| Subagentes (`agents/`) do plugin do Claude não viram agentes no lado OpenAI; viram skills | Codex/ChatGPT | certa | médio | papéis do time como skills; orquestração descrita no `SKILL.md` do Editor-Chefe | [F14] |
| Subagentes do Codex por arquivo TOML só nos clientes locais | Codex | certa | médio | no ChatGPT Work, depender do subagente hospedado | [F10] |
| Geração de imagem consome o limite do Codex 3 a 5 vezes mais rápido | Codex | alta | médio | lote grande pela API com preço aprovado | [F9] |
| Imagem por API é paga | API OpenAI | certa | médio | aprovar preço; alternativa grátis é gerar na interface | [F18] |
| GPTs no Enterprise em aposentadoria | ChatGPT | certa | médio | não usar GPT como base | [F13] |
| Claude não gera imagem; o agente de imagens não roda só com a assinatura do Claude | Claude | certa | alto | imagem pelo ChatGPT/Codex (assinatura) ou API paga aprovada | [F20] |
| Subagentes do plugin não carregam no chat do claude.ai (só Cowork e Claude Code) | Claude | certa | médio | usar Cowork ou Claude Code para o time; no chat, orquestração por skill | [F22] |
| Distribuição pela organização do claude.ai exige Team/Enterprise e repositório privado | Claude | média | médio | sem esses planos, upload de zip por pessoa | [F21][F22] |
| `gemini-2.5-flash-image` será desligado em 15/03/2027 | Google | certa | baixo | não depender desse modelo | [F24] |
| Skill de fonte externa pode executar código malicioso | todos | baixa | alto | só skills próprias; varredura do Enterprise no Claude | [F16] |
| Licenças: especificação Agent Skills e plataformas não exigem licença da skill; `license` é opcional | todos | — | — | marcar `license: Proprietary` nas skills da editora | [F1] |

## Tabela de fontes
| Id | URL | Acesso | Trecho literal (até 25 palavras) | Tipo | Confiança |
|---|---|---|---|---|---|
| F1 | https://agentskills.io/specification | 2026-11-18 | "`name` \| Yes \| Max 64 characters. Lowercase letters, numbers, and hyphens only. Must not start or end with a hyphen." | oficial | alta |
| F2 | https://agentskills.io/specification | 2026-11-18 | "Keep your main `SKILL.md` under 500 lines. Move detailed reference material to separate files." | oficial | alta |
| F3 | https://agentskills.io/clients.md | 2026-11-18 | "Agent products that support the Agent Skills format." (lista não renderizou) | oficial | baixa |
| F4 | https://developers.openai.com/plugins/concepts/skills | 2026-11-18 | "folders of instructions and resources that teach ChatGPT and Codex how to complete repeatable workflows" | oficial | média |
| F5 | https://academy.openai.com/public/clubs/work-users-ynjqu/resources/skills | 2026-11-18 | "During the initial beta, skills are off by default—workspace owners can enable them in workspace settings." | oficial | média |
| F6 | https://learn.chatgpt.com/docs/build-skills.md | 2026-11-18 | "Skills build on the open agent skills standard" | oficial | média |
| F7 | https://learn.chatgpt.com/docs/skills-and-plugins.md | 2026-11-18 | "ChatGPT supports `@` mentions, while Codex supports `$` mentions for skills." | oficial | média |
| F8 | https://learn.chatgpt.com/docs/enterprise/skills.md | 2026-11-18 | "They aren't available in the IDE extension." | oficial | média |
| F9 | https://learn.chatgpt.com/docs/image-generation.md | 2026-11-18 | "Built-in image generation uses `gpt-image-2`." | oficial | média |
| F10 | https://learn.chatgpt.com/docs/agent-configuration/subagents.md | 2026-11-18 | "add standalone TOML files under `~/.codex/agents/` for personal agents or `.codex/agents/` for project-scoped agents." | oficial | média |
| F11 | https://learn.chatgpt.com/docs/projects.md | 2026-11-18 | "A ChatGPT project gives its chats access to the same uploaded files, project instructions, and connected sources." | oficial | média |
| F12 | https://learn.chatgpt.com/docs/pricing.md | 2026-11-18 | Plus ($20) ... Pro (from $100) ... Business ($20 per user, billed annually ... $25 billed monthly); "Image generation isn't available on the Free plan" | preço | média |
| F13 | https://learn.chatgpt.com/docs/build-plugins.md | 2026-11-18 | "Custom GPTs in ChatGPT Enterprise are being retired." | oficial | média |
| F14 | https://developers.openai.com/plugins/guides/submit-claude-plugin.md | 2026-11-18 | "Claude marketplace listings and approvals don't transfer." | oficial | média |
| F15 | https://developers.openai.com/plugins/build/skills.md | 2026-11-18 | "The fastest way to start is with the built-in skill creator." | oficial | média |
| F16 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | 2026-11-18 | "Upload your own Skills as zip files. Available on Pro, Max, Ultra, Team, and Enterprise plans with code execution enabled." | oficial | alta |
| F17 | https://code.claude.com/docs/en/plugins-reference | 2026-11-18 | "Save the manifest at `.claude-plugin/plugin.json` under the plugin root." | oficial | alta |
| F18 | https://developers.openai.com/api/docs/pricing | 2026-11-18 | gpt-image-2 \| Image \| $8.00 \| $30.00 \| $2.00 | preço | média |
| F20 | https://platform.claude.com/docs/en/build-with-claude/vision | 2026-11-18 | "No, Claude is an image understanding model only. It can interpret and analyze images, but it cannot generate, produce, edit, manipulate, or create images." | oficial | alta |
| F21 | https://claude.com/docs/plugins/org-sync | 2026-11-18 | "Don't include a top-level `bin/` directory in any plugin you distribute through organization settings." | oficial | alta |
| F22 | https://claude.com/docs/plugins/org-rollout.md | 2026-11-18 | "Hooks and agents load in Cowork and Claude Code and not in chat, and a local MCP server doesn't run in chat." | oficial | alta |
| F23 | https://developers.openai.com/api/docs/guides/image-generation (offset 100000) | 2026-11-18 | GPT-Image-2 \| Medium \| $0.053 \| $0.041 \| $0.041; "Complex prompts may take up to 2 minutes to process." | preço | média |
| F24 | https://aistudio.google.com/docs/pricing (redirecionado de ai.google.dev/gemini-api/docs/pricing) | 2026-11-18 | gemini-nano-banana-2.1: "Equivalent to $0.0336 per 1K image"; Free tier: "Not available." | preço | média |
| F19 | https://help.talkpush.com/en/articles/15283736-adding-skills-to-your-ai-platform ; https://www.social-media-skills.com/install/desktop/chatgpt | 2026-11-18 | "Individual user (Plus / Pro / Business)" (resumo da busca, não lido na página) | secundária | baixa |

## Não sei
| Pergunta | O que foi tentado (URL e erro, busca feita) | Como resolver (medição, pergunta ao fornecedor, eixo responsável) |
|---|---|---|
| Quais planos do ChatGPT (Plus, Pro, Business, Enterprise) têm skills e upload de zip | https://help.openai.com/en/articles/20001066-skills-in-chatgpt e /pt-br/: HTTP 403; busca "Skills in ChatGPT Plus Pro Business upload zip": só fontes secundárias, que divergem | abrir o artigo no navegador logado; ou o teste da seção Medições no plano atual |
| Limites de skill no ChatGPT (tamanho do zip, nº de skills, nº de arquivos) | F5, F7, F8 não publicam números; Help Center 403 | Help Center no navegador; teste de upload |
| Uma skill no ChatGPT aciona a geração nativa de imagem e o Python | F5 diz que skills usam as ferramentas que o ChatGPT já tem; não há frase explícita sobre imagem e Python | teste: skill que pede "gere imagem" e "rode Python" numa conversa com as ferramentas ligadas |
| Limites de Projetos (arquivos por plano, tamanho das instruções, memória do projeto) e de GPTs | F11 não traz números; Help Center 403; número só em fonte secundária | Help Center no navegador |
| Upload de skill em zip no claude.ai: tamanho máximo e nº de skills; plugins (não só skills) para Pro/Max individuais | F16 não traz números; F22 descreve só Team/Enterprise; Help Center do Claude não aberto | ler https://support.claude.com/en/articles/12512180-using-skills-in-claude e https://claude.com/docs/plugins/platform-support.md |
| Claude Desktop (app de chat) carrega `agents/` e hooks | F22 fala de "chat" e "Cowork", sem citar o app desktop à parte | ler https://claude.com/docs/plugins/platform-support.md |
| Tokens por imagem do `gpt-image-2` e data de lançamento do `gpt-image-2.6` | F23 só dá a calculadora para o 2 e a tabela "Historical output costs" | calculadora do guia; changelog da API da OpenAI |
| Preço do Imagen (Google) e modelos abertos de imagem rodando local (grátis, sem API) | F24 truncado em 100.000 caracteres antes do Imagen; modelos abertos não buscados | WebFetch com offset 100000 em F24; pesquisa de modelo aberto com licença comercial |
| Se a geração de imagem nativa do ChatGPT segue a "paleta" e o "clean" pedidos com a mesma qualidade da API | brief proíbe presumir equivalência; nenhuma fonte compara | teste lado a lado com o mesmo prompt |
| Lista de produtos que adotam Agent Skills | https://agentskills.io/clients.md renderizou só o título | abrir no navegador ou o repositório `agentskills/agentskills` |
| Hospedagem e custo da VPS para o serviço Python | fora do eixo | eixo de infra (`infra-researcher`) |
