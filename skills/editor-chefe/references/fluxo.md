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

## Independência
- Claude Code, Cowork e Codex: cada papel roda como subagente, com só os arquivos do pedido.
- Chat do ChatGPT e do claude.ai: papéis em sequência na mesma conversa, exceto a auditoria científica, que roda em conversa nova com o pacote de auditoria.
- A auditoria gráfica usa o script de checagem, que não depende da conversa, mais a inspeção visual das páginas apontadas.
