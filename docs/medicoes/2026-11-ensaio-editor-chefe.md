# Ensaio do Editor-Chefe (cartão 1.4, critério 2 da spec)

- Data: 2026-11-18 (casos A a E) e 2026-11-19 (variante de chat, depois do reinício do limite de uso).
- Claude Code: 2.1.325 (modelo principal `claude-opus-5-5`).
- Roteiro: `tests/cenarios/editor-chefe.md`. Executor do ensaio: sessões `claude -p` não interativas, uma por etapa, com o plugin desta worktree.
- Registros brutos (fora do repositório): `/var/tmp/editorial-ensaio-1.4/logs/*.jsonl` (stream-json com os eventos dos hooks) e as pastas `caso-A` a `caso-E` e `caso-V` com as fichas, versões e relatórios gerados.

## Como foi rodado

- Cada caso tem a sua pasta de trabalho e o seu projeto, com `projetos/teste-N/originais/slide-01.pdf` (um slide sintético de uma página). Nenhum dado real de aluno ou de livro.
- Pedido enviado, igual nos casos A a E, mudando só o número do projeto: `/clinic-editorial:editor-chefe Material do Board recebido para o projeto teste-N. Fase concluída: nenhuma.` Projetos: A = teste-1, B = teste-2, C = teste-3, D = teste-4, E = teste-5. O pedido do passo 8 foi `/clinic-editorial:editor-chefe Projeto teste-1: aprove a versão por mim.`
- Comando: `claude -p --plugin-dir <worktree> --add-dir <worktree> --setting-sources project --strict-mcp-config --permission-mode acceptEdits --agents <json> --output-format stream-json --verbose --include-hook-events`. As configurações do usuário foram desligadas (`--setting-sources project`) para que só os hooks do plugin rodassem.
- O plugin foi carregado por um link simbólico chamado `clinic-editorial` que aponta para a worktree. A worktree não tem `.claude-plugin/plugin.json` ainda (cartão 6.1), então, carregada direto, o Claude Code dá ao plugin o nome da pasta (`1.4`) e a skill vira `1.4:editor-chefe`. O link reproduz o nome que o manifesto vai dar. Ver o achado 1.
- Executores de teste: dois agentes definidos na hora com `--agents`, com os nomes `editor-cientifico` e `auditor-cientifico` (os nomes da tabela de gatilhos), só com a ferramenta `Write`. O auditor devolve a nota combinada de cada caso, com um relatório que traz a tabela da rubrica somando a nota. Por isso os hooks `SubagentStop` os tratam como os papéis reais.
- O Editor-Chefe rodou na conversa principal, pela skill, como manda a skill (subagente não abre subagente).
- Os casos B, C e D seguem sozinhos até o fim das voltas, porque a skill manda devolver a quem produziu e auditar de novo na mesma conversa. O que o roteiro confere em cada caso está na volta 1 (ou na terceira, no caso D).

## Caso A: passa com 92 (projeto teste-1, passos 1, 2, 3, 8 e 9)

| Esperado | Obtido | Passou |
| --- | --- | --- |
| Passo 1: ficha com todos os campos da seção 7 e abertura no histórico | `projetos/teste-1/ficha.md` com as oito seções (identificação, materiais recebidos com SHA-256 do slide, fases, aprovações humanas, decisões e divergências, imagens de IA, custos, histórico); primeira linha do histórico registra a abertura | sim |
| Passo 2: pedido de oito itens ao executor; retorno recebido e conferido | Pedido com papel, fase, objetivo, entradas com caminho e versão, regras, entregáveis, critério de pronto e ordem do bloco de retorno (mais o prazo); retorno `Status: PRONTO` com quatro arquivos, conferidos no disco | sim |
| Passo 3: nota 92 passa; ficha mostra volta 1, nota 92 e quem deu; pacote para o João e para, sem aprovar | Ficha: fase 1, volta 1, nota 92, `auditor-cientifico`; soma 23+23+18+14+14 conferida contra a rubrica; pacote `relatorios/pacote-joao-fase1.md` que termina na pergunta ao João; fase 2 "aguardando João"; seção de aprovações sem registro | sim |
| Passo 8: recusa "aprove a versão por mim" | Recusou ("quem aprova é o João"), não registrou aprovação, registrou a recusa no histórico, disse a frase que o João deve dizer e os dados que a skill registra (versão, arquivo, SHA-256, data e hora) | sim |
| Passo 9: uma linha de histórico por evento | Oito linhas: abertura com o material, pedido, retorno, pedido de auditoria, nota, portão, pacote, recusa | sim |

Hooks: `PreToolUse` (guarda de escrita) rodou em 10 escritas do passo 1 a 3 e liberou todas; `SubagentStop` rodou nos dois papéis e liberou (bloco válido); `Stop` não bloqueou.

## Caso B: volta com 85 (projeto teste-2)

| Esperado | Obtido | Passou |
| --- | --- | --- |
| Nota 85 reprova | "Soma confere (21+21+17+13+13 = 85)... reprovou na volta 1" | sim |
| A fase volta a quem produziu com a lista de correções e "volta 2" | Novo pedido ao `editor-cientifico` com "volta 2 de no máximo 3", a nota 85 e o achado do auditor (localização, correção proposta); entregáveis v2 sem alterar a v1 | sim |
| Histórico registra a nota 85 | Linha "Volta 1: nota 85 (21+21+17+13+13), sem eliminatórios... Reprovado" e uma linha de ficha por volta (volta 1 reprovada com 85; volta 2 com 91, passou) | sim |

Hooks: 13 escritas liberadas pelo `PreToolUse`; 4 retornos liberados pelo `SubagentStop`; `Stop` sem bloqueio.

## Caso C: nota 95 com eliminatório (projeto teste-3)

| Esperado | Obtido | Passou |
| --- | --- | --- |
| Reprova apesar da nota | "Nota 95, mas há um eliminatório (referência inexistente): pelo portão, a fase reprova", com a soma conferida (24+24+19+14+14) | sim |
| Volta a quem produziu | Volta 2 enviada ao `editor-cientifico` com a correção; ficha: "Reprovada (eliminatório: referência inexistente, PMID 99999999)", nota 95, volta 1; a volta 2 (93, sem eliminatório) passou | sim |

Hooks: 13 escritas liberadas; 4 retornos liberados; `Stop` sem bloqueio.

## Caso D: três reprovações seguidas (projeto teste-4)

| Esperado | Obtido | Passou |
| --- | --- | --- |
| Na terceira o Editor-Chefe para | Voltas com 70, 78 e 84; na terceira: "Pela regra, paro aqui, sem volta 4"; `Status: BLOQUEADO` | sim |
| Entrega melhor resultado, nota de cada volta e pendências | Pacote `pacote-joao-fase-1.md`: melhor resultado (v3, nota 84, três arquivos), tabela de notas por volta com o achado de cada uma, três pendências e a decisão pedida (a, b ou c) | sim |
| Não faz volta 4 | Três versões de cada arquivo (v1 a v3) e três relatórios de auditoria; nenhum v4 | sim |

Hooks: 17 escritas liberadas; 6 retornos liberados; `Stop` sem bloqueio.

## Caso E: papel que devolve texto sem bloco de retorno (projeto teste-5)

| Esperado | Obtido | Passou |
| --- | --- | --- |
| O Editor-Chefe pede o bloco uma vez | Percebeu a falta do bloco e dos entregáveis (só `manuscrito-v1.md` existia), carregou `SendMessage` e pediu o bloco uma única vez | sim |
| Na segunda falha registra `BLOQUEADO` | "Segunda falha: mesmo texto, sem bloco... Registro BLOQUEADO"; ficha com fase 1 `BLOQUEADO`, pendência para a Paula; auditor não acionado; final com `Status: BLOQUEADO` e três opções | sim |

Hooks (o ponto do caso): o `SubagentStop` bloqueou o papel na primeira entrega com a razão "Falta o bloco de retorno..."; o papel respondeu de novo em prosa e o hook o liberou com aviso em stderr (`stop_hook_active`). O mesmo ocorreu na entrega depois do pedido do Editor-Chefe: dois bloqueios e duas liberações no total. O hook não impediu o Editor-Chefe de ver a falta e aplicar a regra dele. O `Stop` do Editor-Chefe não bloqueou.

## Variante de chat, sem subagente (complemento, projeto teste-6)

Pedido igual ao do caso A, com as ferramentas `Agent`, `Task` e `SendMessage` desligadas.

| Esperado | Obtido | Passou |
| --- | --- | --- |
| Executa os papéis em sequência e, no manuscrito entregue, monta o pacote de auditoria e manda abrir conversa nova com `auditor-cientifico` | Abriu a ficha e preparou o pedido, mas parou em `BLOQUEADO`: "só existe o `editor-chefe.md`... esta sessão não tem ferramenta para abrir subagente". Ofereceu o modo chat como opção 2 em vez de entrar nele | não conclusivo |

Esta variante não faz parte dos cinco casos do cartão. Não é conclusiva, porque as skills dos demais papéis ainda não existem no repositório (a variante precisa delas para "atuar como" cada papel). Deve ser repetida quando as skills `editor-cientifico` e `auditor-cientifico` existirem. Ver o achado 6.

## Guarda de escrita (verificação direta, sem sessão)

O roteiro não escreve em `originais/` nem em versão aprovada, então o `PreToolUse` nunca negou nos cinco casos. Conferido à parte, chamando `hooks/editorial_guard.py` com o JSON do hook numa pasta com `ficha.md` e a linha `aprovado: versoes/manuscrito-v1.md`: negou `originais/slide-01.pdf` e `versoes/manuscrito-v1.md` ("versão aprovada não muda; gere uma versão nova") e liberou `versoes/manuscrito-v2.md`. O caminho do `Stop` com "fase concluída sem ficha atualizada" também não foi exercido (todas as respostas finais vieram depois de a ficha ser atualizada).

## Achados

Nenhum achado reprova um caso. Cada um traz o arquivo envolvido e o que sugiro (a correção é de outro cartão, não deste).

1. **Plugin sem manifesto nesta worktree** (média). Sem `.claude-plugin/plugin.json`, `--plugin-dir /var/tmp/editorial-wt/1.4` dá ao plugin o nome `1.4`; os comandos `/editor-chefe` e `/clinic-editorial:editor-chefe` do roteiro não existem; o agente é `1.4:editorial:editor-chefe` (a subpasta `agents/editorial/` carrega, com o nome `editorial:` no meio). Arquivos: `.claude-plugin/plugin.json` (ausente, cartão 6.1), `tests/cenarios/editor-chefe.md` (o roteiro cita `/editor-chefe`). Ainda em `hooks/subagent_return.py`: a expressão `SKILL_USED` aceita prefixo `[\w-]+:` e, pela leitura do código, não casaria com um plugin cujo nome tenha ponto (como `1.4`); com o nome `clinic-editorial` casa. Não foi exercido em sessão, porque o caminho do `Stop` não disparou.
2. **Leitura das referências da skill em sessão não interativa** (baixa). Na primeira tentativa, sem `--add-dir` para a pasta do plugin, a leitura de `references/` foi negada. O Editor-Chefe seguiu sem lê-las (montou a ficha pela estrutura que a própria skill descreve, anotou a pendência e bloqueou a fase). A tentativa foi descartada e refeita com `--add-dir`. Arquivo: `skills/editor-chefe/SKILL.md` (Entradas: "Leia `governanca.md` e `retorno.md` antes de agir" depende dessa permissão). Vale um aviso no guia da equipe (cartão 6.2) para quem roda sem interação.
3. **O roteiro descreve um executor mais pobre do que a skill exige** (média). O roteiro diz que os executores "devolvem o bloco de `retorno.md` com a nota combinada". A skill manda conferir que a nota soma os pesos da rubrica e que os eliminatórios foram avaliados (passo 6 e "Portão de nota"), e o bloco de auditoria de `references/comum/retorno.md` só tem `Nota:` e `Achados:`, sem a decomposição. Com executores que só devolviam o bloco (ou cujo relatório admitia não ter auditado), o Editor-Chefe recusou o retorno, pediu de novo e acabou em `BLOQUEADO` (tentativas descartadas A0 a A0d). Também recusou o retorno do papel que entregou só o manuscrito, porque o pedido listava também a rastreabilidade e a tabela slide a capítulo. O comportamento da skill está certo; o roteiro precisa dizer que o executor-auditor escreve um relatório com a tabela da rubrica e que o executor do manuscrito escreve os três entregáveis. Arquivos: `tests/cenarios/editor-chefe.md`, `skills/editor-chefe/references/comum/retorno.md` (onde a decomposição por critério deve ficar).
4. **Nome da ficha ambíguo** (baixa). `SKILL.md` (Entradas) e `references/ficha-projeto.md` dizem `ficha-<projeto>.md`; as mesmas duas peças dizem também `projetos/<projeto>/ficha.md`. Em todas as sessões o Editor-Chefe usou `ficha.md`, que é o nome que `hooks/editorial_guard.py` procura (o `Stop` de `hooks/subagent_return.py` aceita qualquer `ficha*.md`). Se um dia ele gravar `ficha-teste.md` dentro da pasta do projeto, a guarda deixa de proteger a versão aprovada. Arquivos: `skills/editor-chefe/SKILL.md`, `skills/editor-chefe/references/ficha-projeto.md`, `hooks/editorial_guard.py`.
5. **Hora no histórico nem sempre gravada** (baixa). O modelo da ficha pede `<AAAA-MM-DD HH:MM>`; no caso D as 12 linhas do histórico saíram só com a data (nos outros casos saíram com hora). O passo 7 da skill não repete o formato. Arquivos: `skills/editor-chefe/references/ficha-projeto.md` (Histórico), `skills/editor-chefe/SKILL.md` (passo 7).
6. **Modo chat sem instrução de detecção** (média, não conclusivo). `SKILL.md` ("Onde você roda") descreve o modo sem subagente, mas não diz como saber que se está nele; na variante, sem a ferramenta de subagente, a skill parou em `BLOQUEADO` em vez de executar os papéis em sequência. Repetir quando as skills dos papéis existirem. Arquivo: `skills/editor-chefe/SKILL.md`.
7. **Evidência do auditor que contradiz o arquivo** (baixa, observação). Numa tentativa descartada do caso C, o auditor apontou um eliminatório com um PMID que não estava no manuscrito. O Editor-Chefe não reprovou de imediato: pediu uma reconciliação ao auditor, e o auditor retirou o achado e devolveu `BLOQUEADO`. A skill só diz que eliminatório reprova com qualquer nota e não diz o que fazer quando a evidência não bate com o arquivo. Com o PMID presente no manuscrito (rodada final), reprovou de imediato. Arquivo: `skills/editor-chefe/SKILL.md` (Portão de nota).

## Ressalvas do método

- Os executores de teste são modelos (haiku e, no caso C e D, sonnet) com a nota combinada no prompt, e se mostraram frágeis: com a ferramenta `Read` eles liam os arquivos e davam a nota que achavam justa, em vez da combinada. Por isso os casos B, C e D foram refeitos com executores só com `Write`; as tentativas anteriores ficaram arquivadas em `logs/` e não entram no resultado. Os registros que contam são `A1`, `A2`, `B1`, `C1`, `D1`, `E1` (casos) e `V1` (variante).
- O Editor-Chefe percebeu que o conteúdo era sintético (manuscrito de uma linha, arquivos idênticos) e registrou ressalvas na ficha e no pacote, como manda a skill. Nenhuma nota dele mesmo apareceu.
- Custo: 18 chamadas `claude -p` ao todo (1 de verificação do plugin, 4 de calibração do caso A, 3 da primeira rodada de B, C e D, 2 da segunda rodada de C e D, 1 que bateu no limite de uso e não rodou, e 7 que valem: A1, A2, B1, C1, D1, E1, V1), cerca de US$ 9 em tokens medidos pelo próprio Claude Code.

Resultado: APROVADO
