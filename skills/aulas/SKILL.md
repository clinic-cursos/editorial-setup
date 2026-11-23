---
name: aulas
description: Use quando pedirem uma aula da Clinic Cursos em PowerPoint a partir de conteúdo, a adaptação de um deck ou slide ao design system, ou um slide avulso ou corrigido.
---

# Aulas Clinic Cursos: design system de apresentações

Transforma qualquer material (texto solto, artigo, apostila, dump de ideias) numa aula pronta em **PowerPoint (.pptx)** na identidade da **Clinic Cursos**. Os templates são usados por vários professores da escola: **nunca coloque nome de professor nem registro profissional** nos slides, a não ser que peçam.

Esta skill é **independente da julie-bae-social**. Não use DM Serif, linho nem outra identidade pessoal aqui.

Público: profissionais da estética em formação (biomédicos, dentistas, enfermeiros). Linguagem técnica, didática e direta.

## Estilos

Declare `estilo` no roteiro. Para roteiros antigos sem esse campo, a ferramenta usa `padrao`. Um pedido para "refazer no design system novo" usa `ousado`. Se a pessoa pedir explicitamente o estilo padrão, use `padrao`.

- **`padrao`**: formato 16:9, tipografia Montserrat, tarja escura ou cabeçalho editorial e a identidade descrita abaixo. Sem transição Morph nem animações de entrada.
- **`ousado`**: modelo mestre v1. Alterna fundos noite `#1C1212`, creme `#FAF6F4` e vinho `#9C4C48`, com Montserrat em títulos grandes, fotos sangradas e o arco do logo. Os slides têm transição Morph, animação de entrada e elementos nomeados como `!!fundo` e `!!logo`.

## Identidade do estilo padrão

- **Cores do logo:** vinho `#9C4C48` (principal), rosé `#B68B85` (apoio), cinza `#6E6F73` (texto secundário). Apoio: vinho escuro `#6E2F2C`, rosé claro `#F4ECEA` (caixas de destaque), texto `#404040`, preto `#141211`.
- **Verde `#6AA84F`:** só no selo "Conheça nosso curso…" (herdado do template).
- **Vermelho `#D32F2F`:** só em intercorrências e alertas.
- **Sem azul-petróleo, amarelo ou outras cores fora da paleta.**
- **Fonte:** Montserrat em tudo; Montserrat ExtraBold nos títulos. Títulos de tarja em CAIXA ALTA. Destaques no corpo em **negrito vinho**.
- **Formato:** 16:9 (10 × 5,625 pol).
- **Tarja escura de título** (recorte da foto do template) com fio vinho embaixo e logo branco à direita. É o cabeçalho padrão dos slides de conteúdo.
- **Cabeçalho editorial** (variação refinada, vinda dos slides novos do HOF): fundo branco, título vinho, grade de pontinhos à esquerda e fio vinho fino. Usado em texto + imagem, artigo e caso clínico, para dar respiro.
- **Capa, módulo e encerramento:** foto escura do template com logo branco.
- **Grafismos do logo:**
  - arco do "C" (anel parcial vinho ou rosé) nas capas, na frase de impacto e no encerramento;
  - colchete do logo emoldurando a conclusão de artigos;
  - grade de pontinhos (o "DNA") como marcador de título e KPI.
- Rodapé discreto só com o nome do curso, **sem número de página** (exceto em capa, módulo, frase, parcerias e encerramento). Capa **sem data nem turma**; o subtítulo é só "Módulo N".

## Repertório de slides (campo `tipo`)

| tipo | quando usar | campos |
|---|---|---|
| `capa` | abertura da aula | titulo, curso, subtitulo (só "Módulo N") |
| `modulo` | divisória entre módulos | numero, titulo, descricao, selo |
| `sumario` | tópicos / conteúdo programático | titulo, info (horários), itens[], destaque (índice) |
| `texto_imagem` | conceito com 2–4 pontos + imagem clínica | kicker, titulo, topicos[] (str ou {titulo, texto}), imagem, legenda, lado (direita/esquerda), destaque. No estilo ousado, foto usa `imagem_modo: "sangrar"` (padrão), enquanto diagrama, print e infográfico usam `imagem_modo: "conter"`. |
| `anatomia` | imagem anatômica grande com marcações | titulo, imagem, legenda, marcacoes[{nome, x, y, desc}] (x,y de 0 a 1 sobre a imagem), nota |
| `passo_a_passo` | técnica em etapas | titulo, passos[{titulo, texto}], imagem (opcional → layout vertical), dica |
| `antes_depois` | resultado comparativo | titulo, antes, depois, rotulo_antes, rotulo_depois, legenda (produto · técnica · tempo) |
| `artigo` | print de artigo com conclusão em destaque | titulo, kicker, imagem (print), conclusao, comentario ("Na prática clínica"), referencia |
| `grafico` | dados de estudo, evolução, proporções | titulo, tipo_grafico (coluna/barra/linha/pizza), categorias[], series[{nome, valores[]}], destaque{valor, texto}, fonte |
| `tabela` | comparativo (ex.: tipos de fios) | titulo, colunas[], linhas[[...]], destacar_coluna, nota |
| `caso_clinico` | caso real com dados e fotos | titulo, kicker, paciente{sexo, idade, queixa}, avaliacao, plano, resultado, imagens[] (até 3), legenda |
| `alerta` | intercorrências / riscos | titulo, intercorrencia, sinais[], conduta[], urgente |
| `frase` | pausa, frase de impacto | frase, autor, fundo (vinho/foto/claro) |
| `referencias` | bibliografia | titulo, refs[] (Vancouver) |
| `custos` | composição do preço (6 blocos de custo) | titulo, kicker, custos[{titulo, exemplos}] (até 6), formula |
| `precificacao` | tabela de lucratividade editável | titulo, kicker, estrategias[{nome, texto}], procedimentos[{nome, estrategia (Upsell/Downsell/Cross-sell), produto, preco, custo_fixo, insumos}], taxa_pct (3), imposto_pct (8), nota |
| `parceria` | parceria comercial (Galderma, Ilikia…) | parceiro, kicker, titulo, destaque_titulo, texto, beneficios[], validade, logo, qr, contato[], qr_legenda |
| `continue_evolucao` | vitrine ClinicPlus · Residência · Pós · MBA | cards[{titulo, texto, icone, qr, selo}], frase1, frase2 |
| `encerramento` | contato e próximos passos | titulo, mensagem, contatos[], qr (imagem ou null para espaço reservado), qr_legenda, selo |

Todo slide aceita `notas` (vai para as notas do apresentador). Em qualquer texto, `**trecho**` vira negrito vinho.

## Campos no estilo ousado

Use [o roteiro de exemplo](references/exemplo_ousado.json) como ponto de partida. Na raiz, declare `estilo` como `"ousado"` e forneça `slides`, uma lista de objetos. O `titulo` da raiz é opcional e identifica a aula no arquivo de prompts. O booleano opcional `avulso` impede as inserções automáticas quando vale `true`. Em aulas completas, os booleanos opcionais `precificacao` e `parcerias` controlam essas inserções e valem `true` por padrão.

Cada slide precisa de `tipo`. Todos aceitam `notas`, texto opcional para o apresentador. Os campos da tabela são opcionais para o gerador, salvo os indicados como obrigatórios. Use texto simples quando o formato não estiver indicado. As quantidades e linhas são recomendações de espaço. Em slides de conteúdo, mantenha cerca de 40 palavras e confira a prévia.

| Tipo | Campos e formato | Limite prático | Sem imagem fornecida |
|---|---|---|---|
| `capa` | `curso`, `titulo`, `titulo_secundario`, `subtitulo` (só "Módulo N"). | Uma linha para cada campo. | Foto de fundo da casa, sem quadro. |
| `sumario` | `titulo` (padrão "Conteúdo programático"), `itens` (lista de textos com numeração automática), `resumo`, `info` (texto com quebras de linha, aceita `**negrito**`). | Até 12 itens curtos em duas colunas. Use menos itens na coluna quando houver várias linhas por item. Resumo de até duas linhas e até três linhas de horários. | Sem quadro. |
| `modulo` | `numero` (obrigatório, inteiro ou texto numérico, exibido com pelo menos dois dígitos), `titulo`, `descricao`, `selo`. | Dois dígitos e uma linha por campo de texto. | Sem quadro. |
| `frase` | `frase`, `autor`, `selos` (lista de rótulos). | Frase de até quatro linhas, autor em uma linha e até três selos curtos lado a lado. | Sem quadro. |
| `pilares` | Campos de imagem abaixo. `kicker` (rótulo acima do título), `titulo`, `destaque_titulo` (trecho exato do título), `info` (sobre a base da imagem, aceita `**negrito**`), `pilares` (lista de objetos com `titulo` e `texto`), `selo` (chamada opcional no rodapé), `referencia`. | Até três pilares, cada um com título de uma linha e texto de até duas linhas. Use até duas linhas para o título e para `info` e uma linha para cada um dos campos `selo` e `referencia`. | Quadro à esquerda com `prompt_imagem`. Sem os dois campos, texto em largura inteira. |
| `texto_imagem` | Campos de imagem abaixo. `kicker`, `titulo`, `destaque_titulo` (trecho exato do título), `seta` (booleano, exibida ao lado do painel), `texto`, `topicos` (lista de textos ou objetos com `titulo` e `texto`), `destaque` (texto final), `imagem_modo` (`"sangrar"` por padrão, `"conter"` para mostrar a imagem inteira). | Título de até duas linhas e de dois a quatro tópicos curtos. Some o texto inicial e o destaque ao orçamento de 40 palavras. | Quadro à direita com `prompt_imagem`, inclusive no modo `"conter"`. Sem os dois campos, texto em largura inteira. |
| `passo_a_passo` | Campos de imagem abaixo. `kicker`, `titulo`, `destaque_titulo` (trecho exato do título), `passos` (lista de objetos com `titulo` e `texto`), `dica`. | Até cinco passos curtos. Título e texto de cada passo podem ocupar várias linhas conforme o espaço disponível. Com painel, o título do slide ocupa até duas linhas e a lista começa abaixo dele. Sem painel, use título de uma linha. Dica de uma linha. | Quadro à direita com `prompt_imagem`. Sem os dois campos, lista em largura inteira. |
| `numero` | `kicker`, `valor` (número ou texto, pode incluir unidade), `legenda` (abaixo do valor), `texto`. | Até cinco caracteres para manter o valor grande, legenda de uma linha e texto de até duas linhas. Valores mais longos reduzem a fonte. | Sem quadro. |
| `duas_colunas` | `titulo`, `colunas` (lista de objetos com `titulo` e `itens`, uma lista de textos), `nota`. | Até duas colunas com até cinco itens curtos em cada uma. Títulos de coluna e itens com várias linhas consomem mais espaço da coluna. Nota de uma linha. | Sem quadro. |
| `anatomia` | Campos de imagem abaixo. `kicker`, `titulo`, `marcacoes` (lista de objetos com `nome` e `desc`), `passos` (lista de textos que substitui a lista de descrições quando preenchida), `indicador` (objeto com `valor`, número ou texto, e `texto`), `nota`. Os nomes aparecem juntos acima da lista numerada. | Até cinco descrições ou passos curtos, de uma linha cada com indicador. Nomes juntos em uma linha, valor de até três caracteres para manter a fonte grande e nota de uma linha. | Painel obrigatório. Sem `imagem`, forneça `prompt_imagem` para o quadro à esquerda. |
| `comparativo` | Campos de imagem abaixo. `titulo`, `destaque_titulo` (trecho exato do título), `colunas` (lista de objetos com `titulo` e `itens`, uma lista de textos que aceitam `**negrito**`), `nota` (faixa de atenção), `imagem_modo` (`"sangrar"` preenche a faixa superior e pode recortar a imagem, `"conter"` centraliza a imagem inteira na faixa). O padrão é `"sangrar"`. | Até duas colunas com quatro itens curtos em cada uma. Itens com várias linhas ocupam mais espaço. Título do slide, títulos das colunas e nota de uma linha. | Painel obrigatório. Sem `imagem`, forneça `prompt_imagem` para o quadro na faixa superior. |
| `alerta` | Campos de imagem abaixo. `intercorrencia` (rótulo acima do título), `titulo`, `itens` (lista de objetos com `titulo` e `texto`), `sinais` e `conduta` (listas de textos usadas quando `itens` está vazio ou ausente), `urgente`. | Até três blocos curtos. Título e texto de cada bloco podem ocupar várias linhas conforme o espaço disponível. Forneça sinais e conduta em dois blocos ou nas listas equivalentes. Use uma linha para `urgente`. | Quadro à direita com `prompt_imagem`. Sem os dois campos, texto em largura inteira. |
| `numeros` | `kicker`, `titulo`, `destaque_titulo` (trecho exato do título), `itens` (lista de objetos com `valor`, número ou texto, e `texto`), `nota`. | Até três indicadores na mesma linha, valores de até cinco caracteres e textos de até duas linhas. Nota de uma linha. | Sem quadro. |
| `encerramento` | `titulo`, `mensagem`, `contatos` (lista de textos, um por linha), `qr` (caminho da imagem), `qr_legenda` (só com `qr` preenchido, padrão "Material de apoio"), `selo`. | Título de uma linha, mensagem de até duas e até três contatos. Legenda e selo de uma linha cada. | Foto de fundo da casa. Sem `qr` ou com `null`, nada é reservado para o QR. Caminho inválido gera um espaço com o rótulo "QR code". |
| `preservado` | `deck` (caminho de um PowerPoint existente) e `slide` (inteiro a partir de 1, dentro do deck) são obrigatórios. `titulo` e `kicker` compõem o cabeçalho. | Até duas linhas de título e uma de kicker. A composição original é redimensionada para caber sob o cabeçalho, sem copiar o título identificado nem as decorações reconhecidas. O texto editável usa a família Montserrat e recebe ajuste de cor para atingir contraste de 4,5:1 sobre fundos sólidos. Confira a legibilidade. | Sem quadro. Usa as imagens presentes nas formas copiadas. |

Em `sumario`, `duas_colunas`, `comparativo` e nas variantes com painel de `passo_a_passo` e `alerta`, as caixas crescem conforme a estimativa de linhas e deslocam os itens seguintes. Se a lista exceder a área útil, o gerador reduz a fonte do corpo em passos de até 1 pt até o piso de 8 pt. Os tamanhos iniciais dos itens de `duas_colunas` e `comparativo` são os do modelo, de 11 e 9,5 pt, respectivamente. Se ainda faltar espaço no piso, o texto excedente permanece editável fora do slide e o `conferir` reprova. Reduza o texto ou divida o conteúdo entre slides.

Os campos de imagem são `imagem` (caminho de arquivo), `prompt_imagem` (uma ou duas frases sobre a cena), `legenda` (texto de reserva para arquivo de imagem ausente), `alerta_imagem` (aviso curto de validação) e `estilo_imagem` (`"foto"` para fotografia, `true` ou omitido para ilustração da casa, `false` para omitir o texto de estilo). O caminho de `imagem`, `qr` ou `deck` pode ser absoluto ou relativo à pasta do roteiro.

Em `pilares`, `passo_a_passo`, `alerta` e `texto_imagem`, omita `imagem` e `prompt_imagem` para usar toda a largura útil com texto. Ao refazer um slide que era só texto, mantenha os dois campos ausentes. Para reservar espaço para uma imagem nova, forneça `prompt_imagem`. Em `comparativo` e `anatomia`, forneça pelo menos um dos dois campos.

Se o caminho de `imagem` aponta para um arquivo que não existe, o quadro usa o primeiro texto disponível entre `prompt_imagem`, `legenda` e `titulo`, ou "Imagem do slide". O quadro também gera registro nas notas e no arquivo de prompts. Para `preservado`, mantenha `deck` e `slide` do rascunho de `extrair` com acesso ao PowerPoint original. O exemplo é autônomo e omite esse tipo.

No exemplo, `passo_a_passo` usa título de duas linhas e quadro de prompt. `comparativo` usa `"conter"` e inclui um item de várias linhas. Em `anatomia`, `passos` está vazio para mostrar as descrições das marcações. Em `alerta`, `itens` está vazio para mostrar as listas de sinais e conduta.

Sem painel, `pilares`, `passo_a_passo`, `alerta` e `texto_imagem` usam o maior tamanho de corpo que cabe na área útil estimada, entre 8 e 18 pt, em passos de 1 pt. Cinco itens curtos de uma linha ficam com pelo menos 14 pt. Os títulos dos itens usam 120% do tamanho do corpo, e o espaçamento acompanha a fonte. Em `texto_imagem` sem painel, o título do slide tem até duas linhas e usa de 18 a 40 pt. Com painel, `texto_imagem` ajusta o título de 46 até 18 pt e o corpo de 11 até 8 pt. Se o título ou o corpo ainda exceder o espaço no piso, o texto inteiro segue para o `conferir`.

Os tipos `tabela`, `grafico`, `antes_depois`, `artigo`, `caso_clinico`, `referencias`, `custos`, `precificacao`, `parceria` e `continue_evolucao` usam o layout padrão com Morph e aceitam os campos da tabela do repertório. `tabela`, `grafico`, `referencias`, `custos` e `precificacao` ficam sem quadro. `antes_depois`, `artigo` e `caso_clinico` reservam espaços rotulados para as imagens ausentes. `parceria` e `continue_evolucao` reservam espaço rotulado para QR ausente. Esses espaços não são quadros de prompt.

## Escolha a entrada

1. **Aula do zero com conteúdo.** Leia os materiais e monte o roteiro JSON seguindo a seção abaixo. Rode `gerar`.
2. **Deck ou slide de referência.** Rode `extrair` no PowerPoint recebido. Use `--slides` para selecionar números ou intervalos. A ferramenta grava `roteiro-rascunho.json` e a pasta `img/`. As imagens PNG e JPEG saem com o recorte do slide original e recebem `"recortada": true` no rascunho quando o recorte é aplicado. No rascunho, cada item de `imagens` traz `caminho` e `decorativa`. Use a lista diretamente nos tipos que recebem `imagens`, como `caso_clinico`, nos dois estilos. O gerador aceita também caminhos em texto, resolve caminhos relativos à pasta do roteiro e ignora itens com `"decorativa": true`. Dirija o roteiro: confira a ordem e a integridade dos textos, escolha o tipo de cada slide, ajuste o texto sem alterar o sentido e declare o estilo. Use `preservado` para manter composições complexas, como marcações desenhadas sobre uma foto. Rode `gerar` com o roteiro ajustado. O rascunho vem com `"avulso": true` para conservar a seleção sem inserções automáticas.
3. **Slide avulso ou pontual a corrigir.** Monte um roteiro só com os slides pedidos e use `"avulso": true`. Para correção, parta do roteiro da versão a corrigir ou use `extrair` com a seleção do slide. Se a pessoa pediu o deck inteiro corrigido, mantenha os demais slides no roteiro e gere o deck completo.

`"avulso": true` funciona nos dois estilos e gera só os slides declarados. Inclua capa, encerramento, precificação ou parcerias no roteiro apenas se fizerem parte da seleção pedida.

## Como transformar o material em aula

1. **Leia tudo** e identifique o tema, os módulos naturais (introdução, anatomia, materiais, mecanismo, indicações, planejamento, técnica, pós, intercorrências, resultados…) e o que for dado, técnica, caso, alerta ou referência.
2. **Estrutura padrão:** capa → sumário → para cada módulo: `modulo` + slides de conteúdo → frase de impacto (opcional, no máximo 1 ou 2 por aula) → referências → **Como compor seu preço → Precificação → Galderma → Ilikia → Continue sua evolução** → encerramento.
   - **Precificação está em todo esqueleto.** O layout é fixo e os valores mudam por curso. Preencha `procedimentos` com os procedimentos do curso. Ao declarar `precificacao` no roteiro, declare `custos` logo antes: o gerador só insere os dois slides sozinho quando o roteiro não tem `precificacao`, e sem `custos` a aula perde o "Como compor seu preço". O gerador calcula custo financeiro, imposto e lucro (preço − produto − custo fixo − insumos − taxa% − imposto%). Sem valores no material, os slides entram com "R$" e um traço no lugar do valor; nunca invente preços.
   - Inclua os 3 slides de parceria em aulas completas, salvo pedido explícito para omiti-los. O gerador já os insere sozinho antes do encerramento, com o conteúdo padrão e os QR codes oficiais.
   - Para personalizar uma parceria nesta aula, declare os slides de parceria e de continuação no roteiro com os dados e recursos aprovados.
3. **Escolha o tipo pelo conteúdo, não pelo hábito:**
   - números ou evolução no tempo → `grafico`;
   - comparação de 2 ou mais opções em vários critérios → `tabela`;
   - sequência de ações → `passo_a_passo`. No estilo padrão, até 5 passos ficam na horizontal. Com mais passos ou com foto, ficam na vertical. No ousado, a lista fica à esquerda quando há painel de imagem;
   - estrutura anatômica ou zonas de risco → `anatomia`;
   - estudo citado → `artigo`, com a conclusão em 1 ou 2 frases e "na prática clínica". Slide de evidência só usa referência verificável (estudo enviado pelo professor ou fonte conferida); sem fonte verificável, `[confirmar]`. Numa aula de projeto com o Editor Científico, as referências dele são a fonte preferida;
   - complicação → `alerta`, sempre com sinais e conduta;
   - conceito → `texto_imagem`.
   Evite mais de 2 slides seguidos do mesmo tipo.
4. **Densidade:** slide é apoio de aula. No máximo cerca de 40 palavras por slide de conteúdo, tópicos curtos, um conceito por slide. O detalhe vai para `notas`.
5. **Precisão técnica:** não invente dados, doses, calibres ou referências. Se o material não trouxer um número, deixe genérico ou marque `[confirmar]`. Prefira citar estudos que o professor enviou. Se precisar complementar evidência, busque no PubMed (se conectado) e cite.
6. **Imagens:** use os arquivos enviados (caminho em `imagem`, `antes`, `depois`, `imagens`). Sem imagem, siga a seção "Direção de imagens": prompt para ilustrações, descrição da foto para casos reais.
7. Monte o JSON do roteiro e siga a seção "Execução". Faça as correções no roteiro e gere uma nova versão.


## Direção de imagens (prompts para o ChatGPT)

Você atua como diretor de arte. Para cada espaço de imagem, decida o que ilustra melhor aquele conteúdo e, quando o professor não mandar a imagem, escreva o prompt para ele gerar no ChatGPT. Não é você quem gera a imagem.

- **Como usar:** preencha `prompt_imagem` com a descrição da cena nos tipos com painel de imagem. Para o estilo ousado, consulte a tabela "Campos no estilo ousado".
  - `estilo_imagem: "foto"` serve para retratos e cenas realistas; o padrão é ilustração médica 3D.
  - `alerta_imagem` traz um aviso que aparece no quadro.
- **O que o gerador faz sozinho:**
  - desenha o quadro tracejado no lugar da imagem, com o prompt completo;
  - acrescenta o **estilo da casa** (`ESTILO_CASA` ou `ESTILO_FOTO`) e o **formato certo** para o tamanho do espaço (16:9, 3:2, 1:1, 2:3, 9:16);
  - copia o prompt nas notas do apresentador;
  - salva `<nome> - prompts de imagem.md` com todos os prompts numerados. Se o gerador gravou o arquivo nesta execução, entregue-o junto com o .pptx; senão, diga que nenhum prompt foi gerado.
- **Como escrever o prompt:** em português, descrevendo a cena concreta: assunto, enquadramento, corte ou ângulo, o que está à esquerda e à direita e qual estrutura fica em vinho. Uma ideia por imagem.
- **Sem texto na imagem:** rótulos e setas com nome ficam no slide, editáveis.
- **Quando não usar imagem:** slides de número grande, frase, tabela e gráfico ficam limpos.
- **Nunca gere prompt para:**
  - antes e depois, caso clínico ou foto de paciente: precisam ser fotos reais, e o quadro só diz qual foto colocar;
  - print de artigo.
- **Anatomia, áreas de risco e diagramas científicos:** gere o prompt, mas sempre com `alerta_imagem` pedindo conferência com atlas ou professor. A IA erra trajetos de vasos e inserções musculares.

## Arquivos (ficam na própria skill)

Origem: design system das aulas enviado pela Julie em 19/11/2026 (`docs/fontes/2026-11-19-julie-design-system/`). O visual e as regras são dela; aqui só mudaram os caminhos, que passam a apontar para a pasta da skill.

- `scripts/aulas.py`: entrada única para extrair, gerar, conferir e renderizar.
- `assets/`: logos, foto de fundo, QR codes e ícones das parcerias (`assets/parcerias/`), como arquivos de imagem.
- `references/exemplo_roteiro.json`: roteiro de exemplo; mostra só o formato, e todo conteúdo clínico nele é marcador `[EXEMPLO: ...]` a substituir.
- `references/exemplo_ousado.json`: roteiro autônomo com os tipos de layout próprio do estilo ousado que dispensam um deck de origem.
- `references/modelo_hof_roteiro.json`: roteiro de referência para os tipos do modelo mestre v1. Para cada aula, use o conteúdo recebido no pedido.

Os scripts leem `assets/` pelo caminho relativo à própria pasta, então nada precisa ser montado antes de gerar. Se um asset faltar, peça ao usuário os logos e a foto de fundo da Clinic Cursos.

## Execução

No repositório:

```
uv run --locked python skills/aulas/scripts/aulas.py extrair "Referência.pptx" rascunho/ --slides 3,5-9
uv run --locked python skills/aulas/scripts/aulas.py gerar roteiro.json "Aula.pptx"
uv run --locked python skills/aulas/scripts/aulas.py conferir "Aula.pptx" --estilo ousado --json > conferir.json
uv run --locked python skills/aulas/scripts/aulas.py previa "Aula.pptx" previa/
```

Fora dele (skill instalada no ChatGPT, Codex ou Claude), com `python-pptx` instalado, use `python3 scripts/aulas.py` na pasta da skill, com os mesmos subcomandos.

Troque os caminhos de exemplo pelos do projeto. Remova `--slides` para extrair o deck inteiro. Em `conferir`, use o mesmo estilo do roteiro. `gerar` já executa a checagem automática. Se `gerar` ou `conferir` reprovar, corrija o roteiro e gere novamente antes de encaminhar a versão.

Leia os avisos gerais em `findings` no JSON ou nas linhas com o achado individual no terminal e revise os avisos do conteúdo copiado por `preservado` nas linhas agrupadas por slide e motivo ou no campo `preserved_findings` do `--json` para ver o detalhe por forma.

Exemplo mínimo de roteiro:

```json
{"titulo": "Toxina Botulínica", "rodape": "Clinic Cursos · Toxina Botulínica",
 "slides": [
  {"tipo": "capa", "curso": "Curso de Toxina", "titulo": "Toxina botulínica aplicada", "subtitulo": "Módulo 1"},
  {"tipo": "sumario", "itens": ["Introdução", "Anatomia", "Técnica"]},
  {"tipo": "modulo", "numero": 1, "titulo": "Introdução"},
  {"tipo": "tabela", "titulo": "Marcas comerciais", "colunas": ["", "A", "B"], "linhas": [["Unidades", "100U", "500U"]]},
  {"tipo": "referencias", "refs": ["..."]},
  {"tipo": "encerramento", "contatos": ["[Instagram da escola]"]}
 ]}
```

As parcerias entram sozinhas antes do encerramento. Use `"parcerias": false` só se o usuário pedir uma aula sem elas.

**Pré-visualização:** `previa` usa `soffice` e `pdftoppm` para gerar um PNG por slide. Confira todos os PNGs para identificar texto cortado, sobreposições e QR ilegível. Se encontrar uma falha visual, corrija o roteiro e gere, confira e renderize a nova versão. Se a prévia falhar, registre o impedimento e retome em um ambiente que consiga renderizar com Montserrat.

Produza e inspecione o .pptx só com `aulas.py`. Corrija pelo roteiro em vez de escrever código python-pptx ou abrir e editar o PowerPoint por outro meio. Devolva o .pptx, o roteiro, o relatório do `conferir` e a prévia ao Editor-Chefe para encaminhar ao `revisor-aulas`.
