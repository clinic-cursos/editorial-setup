# Guia da Paula

## Prepare o ChatGPT

Peça ao Alify os pacotes da versão atual. Escolha o caminho conforme o [teste do ChatGPT da Clinic](medicoes/teste-plataforma/roteiro.md), que também verifica se o ambiente consegue diagramar o livro e acessar as imagens geradas.

1. **Se houver upload de skills na conta da Clinic**, peça à administração do workspace para habilitar o recurso, se necessário. Na área de Skills, envie um ZIP por vez da pasta `dist/chatgpt/` e ative as skills. Na conversa do livro, selecione `editor-chefe` quando for pedir a próxima fase.
2. **Se o upload de skills estiver indisponível**, use o pacote `dist/chatgpt-projeto/`. Nos ajustes do Projeto de cada livro, cole o conteúdo de `instrucoes.md` nas instruções do Projeto. Adicione os arquivos de papéis e referências às fontes, com os nomes do pacote. Se o Projeto atingir o limite de arquivos, guarde ali a ficha e as referências do Editor-Chefe e anexe as instruções e referências específicas do papel na conversa de cada fase. Na primeira conversa, peça ao Editor-Chefe que leia as fontes e siga as regras do papel correspondente a cada etapa.

[Projetos no ChatGPT](https://learn.chatgpt.com/docs/projects) · [Controles de skills](https://learn.chatgpt.com/docs/enterprise/skills)

## Abra um Projeto por livro

1. Crie um Projeto em **Projetos** e dê a ele o título do livro.
2. Adicione os slides, a apostila e o manual de diagramação, se disponíveis. Identifique a versão dos arquivos. Se o João já revisou o conteúdo, anexe a versão aprovada e informe a data da aprovação.
3. Abra a primeira conversa dentro do Projeto. Informe título, curso, autores, a última fase concluída e a próxima fase desejada. Se o livro estiver começando, diga que nenhuma fase foi concluída e peça a abertura da ficha.
4. Baixe a ficha `ficha-<projeto>.md` que o Editor-Chefe devolver. Guarde-a nos **arquivos do Projeto**. Ao fim de cada fase, baixe a ficha atualizada e substitua ali a anterior. Na retomada, peça que o Editor-Chefe leia a ficha antes de continuar. Preserve também os arquivos das versões aprovadas. Uma correção gera uma versão nova.

## Peça a fase que precisa

Use o formato **Fase concluída** e **Próxima fase**, com os arquivos da versão correspondente.

| Fase desejada | Pedido e arquivos |
| --- | --- |
| 0. Abertura | “Nenhuma fase concluída. Abra a ficha deste livro.” Informe título, curso e autores e envie os materiais recebidos. |
| 1. Ampliação científica | “Fase concluída: abertura. Próxima fase: ampliação científica.” Envie os materiais originais do Board. Depois da ampliação, abra a auditoria em uma conversa nova. |
| 2. Revisão técnica | “Fase concluída: ampliação científica auditada. Prepare o pacote para o João revisar.” Envie a versão auditada e o relatório. Após a aprovação, informe ao Editor-Chefe quem aprovou, qual arquivo e versão, e a data e hora. |
| 3. Diagramação | “Fase concluída: validação de conteúdo pelo João. Próxima fase: diagramação.” Envie o manuscrito aprovado e o manual, se disponível. |
| 4. Imagens complementares | “Fase concluída: diagramação auditada. Próxima fase: imagens complementares.” Envie a versão diagramada e seu relatório. O Diagramador reinsere as imagens e o Auditor Gráfico confere o novo PDF. |
| 5. Aprovação editorial e gráfica | Peça o pacote para sua conferência após a fase 4, ou após a fase 3 quando nenhuma página precisar de imagem. Confira o PDF, os relatórios e as pendências. Informe explicitamente se aprova aquela versão e quando. |
| 6. Produção gráfica | A liberação de impressão é sua e ocorre fora deste setup. Registre a decisão na ficha com a versão liberada. |

### Pedido da Paula, depois da revisão do João

> Fase concluída: validação de conteúdo. Próxima fase: 1. Diagramação: coloque esse conteúdo em diagramação (conforme manual enviado). 2. Criação de imagens complementares: após diagramado, veja espaços muito vazios nas páginas e crie imagens complementares, conceituais e clean, nas cores bordô, rosa claro, marsala e cinza, em sintonia com o conteúdo da página.

Esse pedido entra na fase 3 e segue para a fase 4 se houver espaço suficiente e a diagramação passar na auditoria. Enquanto o manual estiver pendente, confira as regras inferidas no relatório e a marca “provisória: manual ausente” na nota.

## Peça uma aula ou um slide

Fale com o Editor-Chefe e anexe os materiais citados no pedido. Escolha uma das frases para colar:

- “Crie uma aula do zero para [curso] usando o conteúdo anexado. Use o estilo padrão da Clinic.”
- “Refaça o deck ou slide anexado no design system novo, preservando o sentido do conteúdo.”
- “Verifique o deck anexado sem refazê-lo. Devolva o placar do modelo e os gaps de cada slide.”
- “Refatore o deck anexado no modelo. Preserve todo o conteúdo e compare com a origem.”
- “Ajuste somente [campo] no deck anexado, usando o roteiro da versão anterior.”
- “Crie um slide avulso sobre [tema] com o material anexado, ou corrija o slide [número] conforme [ajuste] e entregue só esse slide.”

O pedido de design system novo usa o estilo ousado do modelo mestre v1. Na refatoração, o conteúdo não pode ser reduzido, cortado, alterado, reordenado nem ter o sentido desviado; se não couber, o conteúdo é distribuído por mais slides do modelo. O ajuste pontual muda somente o campo pedido. O placar do modelo deve ser 100 em todos os slides. O Editor-Chefe encaminha o PowerPoint para sua conferência depois da revisão dos slides. A entrega também informa quantos quadros de prompt de imagem continuam pendentes, para você saber o que falta gerar.

### Antes do primeiro pedido de aula

Rode o [teste de plataforma](medicoes/teste-plataforma/roteiro.md) e confira a seção **Aulas**. Se o resultado for **“Produz aulas com prévia: não”**, peça a aula à equipe, que pode rodar a produção no Claude Code ou no Codex. O deck exige a fonte Montserrat instalada no computador que vai apresentar, pois a fonte não vem embutida.

## Abra a auditoria científica em uma conversa nova

1. Na conversa do livro, peça ao Editor-Chefe o pacote de auditoria da fase 1. Ele inclui o manuscrito, a tabela de rastreabilidade, a tabela slide a capítulo, os materiais originais e a rubrica da fase.
2. Abra uma conversa nova no ChatGPT, fora do Projeto do livro, para começar só com o material da auditoria. Passe o pacote e as regras de auditoria. Selecione `auditor-cientifico` ou, se estiver usando o pacote de Projeto, anexe `auditor-cientifico-SKILL.md` e as referências desse papel. Peça uma auditoria independente com achados, nota e critérios eliminatórios.
3. Volte à conversa do Editor-Chefe e cole o retorno do auditor, com o relatório e a versão auditada. Ele registra o resultado na ficha e encaminha o manuscrito ao João quando passar.

## Quando o Editor-Chefe parar

As fases 1, 3 e 4 passam com **90 pontos ou mais e nenhum critério eliminatório**. Na terceira reprovação, o Editor-Chefe entrega a melhor versão, as três notas e as pendências. Na fase 1, passe o pacote ao João. Nas fases 3 e 4, confira você mesma os achados e decida quais correções encaminhar. Leve divergências com o Board para avaliação humana e registre a decisão na ficha antes de retomar. A aprovação do João e a sua aprovação continuam sendo decisões expressas sobre uma versão identificada.

## Quando a diagramação precisar rodar fora do ChatGPT

Se o teste mostrar que o ChatGPT não consegue executar o WeasyPrint, ou se a conversa não tiver acesso aos scripts de diagramação e auditoria, peça à equipe para rodar o **Diagramador e o Auditor Gráfico no Claude Code ou no Codex**. Passe a ficha, o manuscrito aprovado, o manual disponível e as imagens já aprovadas para uso, se houver. Peça de volta a fonte editável, o PDF, os relatórios e a ficha da fase, e leve o retorno à conversa do Editor-Chefe.

Quando o Python da conversa não enxergar uma imagem gerada pelo ChatGPT, baixe-a com o nome indicado, como `pagina-12.png`, e anexe o arquivo à conversa para a reinserção. Se a diagramação estiver com a equipe, envie os PNGs junto com o briefing e a página de destino. Imagens complementares são conceituais. Se uma página precisar de ilustração técnica, encaminhe o pedido para validação científica com o João antes de qualquer inclusão.

## O que a V1 ainda não faz bem

- **Já testado:** o Editor-Chefe organiza a ficha e encaminha as fases. A ampliação e a auditoria científica passaram no ensaio com um capítulo de teste, com pontos para o João avaliar. [Ensaio do Editor-Chefe](medicoes/2026-11-ensaio-editor-chefe.md) · [Ensaio científico](medicoes/2026-11-ensaio-cientifico.md)
- **Diagramação:** o Diagramador gera um PDF, mas os ensaios com livros reais ainda não passaram. No livro de Preenchedores, houve problemas no sumário, nas imagens e na preservação do texto. Use o PDF como rascunho para revisão. [Ensaio de Preenchedores](medicoes/2026-11-ensaio-preenchedores.md)
- **Auditoria gráfica:** o Auditor Gráfico pode apontar texto sobreposto ou repetido em páginas que estão corretas. Abra o PDF e confira visualmente as páginas sinalizadas antes de pedir correção. [Ensaio do Auditor Gráfico](medicoes/2026-11-ensaio-toxina-auditoria.md)

## Como melhorar o setup

Dite a sugestão ao Editor-Chefe e peça uma linha com data, papel, o que mudar, por quê e exemplo. Envie a linha ao Alify ou use diretamente o [modelo de melhorias](melhorias.md). Use exemplos sem trechos de livro, fotos clínicas ou dados de alunos.

A equipe registra a mudança no repositório, roda os testes, gera o pacote e publica a nova versão no [histórico](../CHANGELOG.md). Quando receber a versão, reinstale as skills ou atualize as instruções e fontes do Projeto. Edições feitas diretamente na skill instalada se perdem na próxima atualização.

## Atualizar para uma nova versão

Os pacotes de cada versão ficam nas [releases do repositório](https://github.com/clinic-cursos/editorial-setup/releases). No ChatGPT, reenvie os ZIPs mais recentes de `dist/chatgpt/` ou atualize o Projeto com os arquivos de `dist/chatgpt-projeto/`, incluindo a nova skill `revisor-aulas`. No Claude Code ou no Codex, rode `git pull` no checkout do editorial-setup e reinicie a sessão. No Claude Code, use `/plugin` para atualizar o plugin instalado pelo catálogo.
