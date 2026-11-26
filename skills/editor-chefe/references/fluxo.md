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

## Frente Slides

A frente Slides tem três modos, definidos pelo pedido:

- **Produção:** aula do zero com conteúdo. A skill `aulas` aplica estrutura e densidade de cerca de 40 palavras por slide de conteúdo.
- **Refatoração ou verificação:** deck enviado com conteúdo preservado integralmente, sem redução, corte, alteração, reordenação nem desvio de sentido. Se não couber, `aulas` divide em mais slides do modelo. Na refatoração, exige `conferir --origem <deck enviado>` e fidelidade de conteúdo e imagens 100%. O Editor-Chefe decide e registra na ficha cada omissão de imagem antes de passá-la em `--imagens-omitidas slide:índice`, usando o índice do arquivo em `img/` criado por `extrair`. Na verificação sem refazer, `aulas` devolve o placar e os gaps.
- **Ajuste pontual:** muda apenas o campo pedido, parte do roteiro da versão anterior e usa `conferir --origem <versão anterior>`. Cada divergência deve decorrer da mudança pedida.

Em qualquer modo, só encaminhe uma entrega com `model_score.min` igual a 100. Abaixo disso, `aulas` completa o gap pelo roteiro e gera de novo, sem alterar o modelo. A revisão tem como eliminatórios placar abaixo de 100 em qualquer slide e qualquer divergência do conteúdo indicado por `--origem`. `PRONTO` exige nota de ao menos 90, placar 100 e conteúdo 100% fiel.

## Produção de aulas
- Preserve sempre o modelo mestre v1 e exija que todo slide siga o modelo do estilo, inclusive o conteúdo copiado por `preservado`. Só o Alify pode abrir uma versão explícita do modelo v2, com arquivos novos ao lado dos da v1.
- O Editor-Chefe aciona `aulas` em três entradas: aula do zero com conteúdo; deck ou slide de referência para adaptar com `extrair`, direção do roteiro e `gerar`; slide avulso ou correção de slide. Use os materiais do pedido, sem exigir fase concluída de livro.
- `aulas` dirige o roteiro e gera o PowerPoint pela ferramenta. Após a checagem automática e a inspeção da prévia, devolve o .pptx, o roteiro JSON, o relatório do `conferir` e a prévia no bloco de `references/comum/retorno.md`.
- Quando houver `pending_images`, o retorno da entrega informa os quadros de prompt ainda pendentes para a pessoa saber quais imagens faltam gerar.
- O Editor-Chefe encaminha esses arquivos e a descrição do estilo da skill `aulas` ao `revisor-aulas`. Registre o status, a nota e os achados na ficha para a versão examinada. Exija nota de pelo menos 90, placar 100 em todos os slides e fidelidade de conteúdo 100% quando houver `--origem`.
- Encaminhe o PowerPoint à pessoa para conferência após o retorno `PRONTO` do `revisor-aulas`, com nota de pelo menos 90 e sem eliminatórios. Na reprovação, devolva a `aulas` com os achados e reencaminhe a nova versão para revisão. Na terceira reprovação, pare e encaminhe à pessoa as notas, os achados e as pendências para decisão.
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
