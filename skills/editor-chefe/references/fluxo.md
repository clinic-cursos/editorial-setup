# Fluxo editorial

| # | Fase | Quem faz | Quem dá a nota | Portão humano |
| --- | --- | --- | --- | --- |
| 0 | Abertura: ficha do projeto, materiais recebidos, fase de entrada | `editor-chefe` | Não se aplica | Nenhum |
| 1 | Ampliação científica: plano, manuscrito, rastreabilidade, tabela slide a capítulo | `editor-cientifico` | `auditor-cientifico` | Nenhum |
| 2 | Revisão técnica | João | Não se aplica | **João aprova o conteúdo** |
| 3 | Diagramação | `diagramador` | `auditor-grafico` | Nenhum |
| 4 | Imagens complementares e reinserção | `imagens`, depois `diagramador` | `auditor-grafico` | Nenhum |
| 5 | Aprovação editorial e gráfica | Paula | Não se aplica | **Paula aprova a versão** |
| 6 | Produção gráfica (ISBN, gráfica, prova física) | Paula | Não se aplica | **Paula libera a impressão** (fora da V1) |

## Regras de entrada
- O Editor-Chefe aceita entrar em qualquer fase, desde que a ficha ou o pedido diga a fase concluída.
- Pedido típico da Paula: "Fase concluída: validação de conteúdo. Próxima fase: 1. Diagramação. 2. Criação de imagens complementares." Entra na fase 3, com a fase 2 marcada como concluída por ela. Registre na ficha que a aprovação do João veio por declaração da Paula, com data.
- Fases 5 e 6 são de pessoas. O Editor-Chefe só prepara o pacote e registra a decisão.

## Produção de aulas
- O Editor-Chefe aciona `aulas` quando a pessoa pede para produzir ou refazer uma aula. A entrada usa os materiais do pedido e dispensa fase concluída do livro.
- `aulas` entrega o PowerPoint e o roteiro em JSON ao Editor-Chefe pelo [bloco de retorno](comum/retorno.md). O Editor-Chefe encaminha a entrega e as pendências à pessoa para conferência, sem portão de nota na V1.
- Quando a aula servir de base para a ampliação científica de um livro, o Editor-Chefe pode entregar o roteiro em JSON ao `editor-cientifico` como fonte estruturada dos slides para a tabela slide a capítulo.

## Independência
- Claude Code, Cowork e Codex: cada papel roda como subagente, com só os arquivos do pedido.
- Chat do ChatGPT e do claude.ai: papéis em sequência na mesma conversa, exceto a auditoria científica, que roda em conversa nova com o pacote de auditoria.
- A auditoria gráfica usa o script de checagem, que não depende da conversa, mais a inspeção visual das páginas apontadas.

## Encaminhamento entre fases
Todo "passou" abaixo significa passou no portão: nota 90 ou mais e nenhum critério eliminatório. Com eliminatório, a fase volta a quem produziu, qualquer que seja a nota.
- Passou a fase 1: pacote para o João (portão humano da fase 2).
- Passou a fase 3: segue para a fase 4 se a checagem do PDF achar espaço livre acima do limite; se nenhuma página passa do limite, a fase 4 fica registrada como "sem páginas acima do limite" e o pacote vai para a Paula.
- Passou a fase 4: pacote para a Paula (portão humano da fase 5).
