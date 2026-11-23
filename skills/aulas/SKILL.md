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

No `texto_imagem` ousado, o gerador reduz o título de 46 até 18 pt e o corpo de 11 até 8 pt, em passos de 1 pt, conforme a largura das palavras e a altura estimada. Se ainda houver excesso no tamanho mínimo, o texto inteiro segue para o `conferir`.

## Escolha a entrada

1. **Aula do zero com conteúdo.** Leia os materiais e monte o roteiro JSON seguindo a seção abaixo. Rode `gerar`.
2. **Deck ou slide de referência.** Rode `extrair` no PowerPoint recebido. Use `--slides` para selecionar números ou intervalos. A ferramenta grava `roteiro-rascunho.json` e a pasta `img/`. Dirija o roteiro: confira a ordem e a integridade dos textos, escolha o tipo de cada slide, ajuste o texto sem alterar o sentido e declare o estilo. Use `preservado` para manter composições complexas, como marcações desenhadas sobre uma foto. Rode `gerar` com o roteiro ajustado. O rascunho vem com `"avulso": true` para conservar a seleção sem inserções automáticas.
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
   - sequência de ações → `passo_a_passo` (até 5 passos na horizontal; mais que isso ou com foto, vertical);
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

- **Como usar:** nos tipos com imagem (`texto_imagem`, `anatomia`, `passo_a_passo`), preencha `prompt_imagem` com a descrição da cena.
  - `estilo_imagem: "foto"` serve para retratos e cenas realistas; o padrão é ilustração médica 3D.
  - `alerta_imagem` traz um aviso que aparece no quadro.
- **O que o gerador faz sozinho:**
  - desenha o quadro tracejado no lugar da imagem, com o prompt completo;
  - acrescenta o **estilo da casa** (`ESTILO_CASA` ou `ESTILO_FOTO`) e o **formato certo** para o tamanho do espaço (16:9, 3:2, 1:1, 2:3, 9:16);
  - copia o prompt nas notas do apresentador;
  - salva `<nome> - prompts de imagem.md` com todos os prompts numerados. Se o gerador gravou o arquivo nesta execução, entregue-o junto com o .pptx; senão, diga que nenhum prompt foi gerado (`prompt_imagem` ausente ou vazio não gera arquivo).
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
