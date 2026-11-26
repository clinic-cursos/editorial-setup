# Frente Slides: coberturas que faltaram no teste de ponta a ponta

Issue: CLI-716 (continuação). Pedido do Alify em 26/11/2026: "Pode implementar essas coberturas que você acredita serem benéficas para o setup, com a medição das notas."

## Por quê

O teste de ponta a ponta de 26/11 (plano `2026-11-26-slides-fidelidade.md`) deixou quatro lacunas:

1. O `conferir --origem` confere só texto. A foto do slide 4 do HOF e os ícones do slide 8 sumiram sem alerta.
2. O `texto_imagem` do estilo ousado não tem campo de referência. A referência Hexsel entrou no corpo, do tamanho dos itens.
3. Ruído: ao reordenar uma frase no slide 7, o título "Toxina botulínica", que não mudou, também reprovou.
4. O deck sai com quadros de prompt no lugar das imagens, e o relatório não diz quantos faltam.

## Desenho

- **Imagens no `--origem`.** Cada imagem de conteúdo do slide de origem (forma de imagem, também dentro de grupo) precisa aparecer na saída. A comparação usa um hash perceptual (dHash de 64 bits, Pillow, que já vem com o python-pptx) da área visível da imagem de origem (com o recorte do slide aplicado) contra a área visível da imagem na saída ou contra a imagem inteira embutida nela (emenda C1b: o modo `sangrar` recorta de novo, e um deck editado no lugar mantém o recorte original). Casa com distância de Hamming de até 10, e cada imagem da saída serve a uma só imagem da origem (emenda C6). Imagem com menos de 2% da área do slide, medida pela parte dentro do slide, é ícone: não conta na origem e não satisfaz imagem de conteúdo na saída (emenda C6). Imagem que cobre 90% ou mais do slide é fundo: sua ausência vira aviso, não reprovação. Omissão decidida pelo Editor-Chefe entra por `--imagens-omitidas 8:3,8:4` (slide de origem e índice da imagem, o mesmo índice dos arquivos `img/` do `extrair`) e aparece no relatório como omitida.
- **Referência no `texto_imagem` ousado:** campo `referencia`, com o mesmo estilo e posição do `referencia` do `pilares`.
- **Ruído do título:** passa pelo `debugger`; a correção entra como cartão com o teste dele.
- **Quadros de prompt pendentes:** o relatório conta os quadros de prompt de imagem por slide (`pending_images`), como informação, sem reprovar, para a entrega listar o que falta gerar.

Fora do escopo: geração de imagem por API (decisão de provedor e dinheiro, vai para o Fluxo 1 se o Alify quiser).

## Tarefas

Gravidade média em todas (afeta as entregas da frente Slides; aparece no `conferir`, na prévia e no revisor; desfaz-se revertendo o PR). Risco normal.

- **Tarefa 1 (PR próprio), cartões em série:** C1 imagens no `--origem`; C2 quadros pendentes; C3 correção do ruído (depois do diagnóstico); C1b correção do recorte da saída (falso alarme achado na medição num deck editado no lugar); C4 textos da skill, do revisor e do fluxo sobre imagens, omissões e quadros pendentes, versão 0.3.0; C6 miniatura na saída, uso único de cada imagem da saída e área dentro do slide (achados da revisão do Codex).
- **Tarefa 2 (PR próprio):** C5 `referencia` no `texto_imagem` ousado, com a linha da tabela da skill.

## Medição

Depois do merge, rodar de novo o `conferir` nos mesmos decks do teste (deck estragado, HOF à mão, HOF 0.2.8, refatorações v1 a v4) e registrar, por deck: placar do modelo, conteúdo de texto, imagens de conteúdo mantidas e quadros pendentes.

## Status

- Feito: C5 (`referencia` no `texto_imagem`) mergeado no PR #19. C1, C2, C3, C1b, C4 e C6 na branch do PR #20; o C6 foi redespachado depois de um reinício da máquina, a partir do patch parcial salvo. Limite conhecido: imagem no layout do PowerPoint (fora do slide) não é conferida.
- Em andamento: 2ª rodada de revisão do PR #20.
- Travado: nada.
- Próximo passo: merge do PR #20, medição final das notas e release 0.3.0 para a Paula.
