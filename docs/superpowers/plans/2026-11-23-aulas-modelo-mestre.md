# Aulas: slides só pela tool, no modelo mestre v1

Issue: CLI-645 (filha da CLI-514). Pedido do Alify em 23/11/2026, a partir do retorno da Paula. Aprovado por ele na conversa: "vamos seguir sua recomendação [...] não separe em ondas, cria e mergeia".

## Por quê

A Paula pediu para refazer o deck "HOF básico" no design system novo. O Codex editou o deck original à mão, slide a slide, e o resultado não seguiu o modelo mestre v1. O setup só tinha tool para aula do zero, no estilo padrão, sem aprovador e sem caminho para um deck já pronto.

## Fatos conferidos em 23/11/2026

Arquivos de referência (fora do repositório, não versionar: são grandes e têm fotos):

- `/var/tmp/aulas-render/in/modelo.pptx`: o **modelo mestre v1** ("MODELO - HOF básico", 16 slides). É o estilo "editorial ousado" do design system da Julie: fundos noite `#1C1212`, creme `#FAF6F4` e vinho `#9C4C48` em ritmo, tipografia grande, foto sangrando, arco do logo. Todos os slides têm transição Morph, animação de entrada e formas com nome `!!fundo`, `!!logo`, `!!arco`, `!!arco2`, `!!painel`, `!!foto`, `!!barra`, `!!kpi`. A estrutura é a de `skills/aulas/scripts/bold_deck.py`, com conteúdo e fotos reais.
- `/var/tmp/aulas-render/in/aula.pptx`: a **aula nova aprovada** pela Paula (Laser de CO₂, 49 slides). Está no estilo padrão de `clinic_deck.py`, sem Morph nem animação.
- `/var/tmp/aulas-render/in/hof-original.pptx`: o deck **original** do HOF básico (103 slides, 8 mestres, feito à mão). É a entrada real do `restyle`.

Os dois estilos estão aprovados. O roteiro passa a declarar qual usa.

## Desenho

1. **Dois estilos, um roteiro.** Campo `estilo` no roteiro: `"padrao"` (o de hoje, sem mudança visual) ou `"ousado"` (o modelo mestre v1). Sem o campo, vale `padrao`, para não quebrar roteiros existentes.
2. **Uma entrada só:** `skills/aulas/scripts/aulas.py`, com os subcomandos `gerar`, `extrair`, `conferir` e `previa`. O `clinic_deck.py roteiro.json saida.pptx` continua funcionando.
3. **Estilo ousado dirigido por roteiro.** As funções de slide de `bold_deck.py` hoje têm conteúdo fixo; passam a receber o dicionário do slide. O conteúdo fixo do HOF vira `references/modelo_hof_roteiro.json`.
4. **Restyle em três passos:** `extrair` lê um deck pronto e grava um roteiro rascunho; o agente dirige (escolhe o tipo de cada slide e ajusta o texto); `gerar` produz o deck. Slide com desenho feito à mão sobre foto usa o tipo `preservado`: a tool copia as formas do slide original para dentro da moldura do estilo.
5. **Avulso:** `"avulso": true` no roteiro gera só os slides pedidos, sem capa, precificação, parcerias nem encerramento automáticos.
6. **Conferir:** checagem automática do .pptx, com código de saída diferente de zero quando reprova. O `gerar` roda o `conferir` no fim.
7. **Papéis:** `aulas` vira diretor (monta roteiro, roda a tool, nunca escreve python-pptx nem edita o .pptx). Papel novo `revisor-aulas` aprova pela prévia e pelo relatório do `conferir`.

Fora do escopo: mestre de PowerPoint com espaços reservados (o modelo v1 é desenhado por código, e a fidelidade vem do teste contra ele); hook que impeça python-pptx à mão (o hook só enxerga Write e Edit; quem barra é o `conferir` mais o revisor); mudar o visual do estilo padrão.

## Tarefa única, quatro cartões em série, um PR

Função `backend` nos quatro. Gravidade média: afeta as aulas geradas pelo time; o erro aparece na prévia e no `conferir`; desfaz-se revertendo o PR. Risco normal.

Verificação comum (todo cartão): `uv run --locked pytest -q tests/test_aulas.py tests/test_aulas_ousado.py tests/test_aulas_restyle.py tests/test_aulas_conferir.py && uv run --locked python scripts/package.py --check` (cada cartão roda os arquivos de teste que já existem até ele).

### Cartão 1: estilo ousado dirigido por roteiro

- **Objetivo:** gerar o estilo do modelo mestre v1 a partir de roteiro JSON, com Morph e animações, e provar a fidelidade contra o modelo.
- **Arquivos permitidos:** `skills/aulas/scripts/bold_deck.py`, `skills/aulas/scripts/clinic_deck.py`, `skills/aulas/scripts/aulas.py`, `skills/aulas/references/modelo_hof_roteiro.json`, `tests/test_aulas_ousado.py`, `tests/fixtures/aulas/modelo-v1.json`, `tests/test_aulas.py`
- **Critérios de aceite:**
  - `aulas.py gerar roteiro.json saida.pptx` gera pelo estilo do campo `estilo`; sem o campo, o resultado é o do `clinic_deck.py` de hoje (os testes atuais de `tests/test_aulas.py` passam sem mudança de expectativa).
  - No estilo ousado existem, dirigidos pelo dicionário do slide, os tipos: `capa`, `sumario`, `modulo`, `frase`, `pilares`, `texto_imagem`, `passo_a_passo`, `numero`, `duas_colunas`, `anatomia`, `comparativo`, `alerta`, `numeros`, `encerramento`. Cada um corresponde a um slide do modelo (1 a 16, na ordem: capa, sumario, modulo, frase, pilares, texto_imagem, modulo, passo_a_passo, numero, duas_colunas, anatomia, modulo, comparativo, alerta, numeros, encerramento).
  - Os demais tipos do repertório (`tabela`, `grafico`, `antes_depois`, `artigo`, `caso_clinico`, `referencias`, `custos`, `precificacao`, `parceria`, `continue_evolucao`) saem no estilo ousado pelo caminho que `s_from_layout` já usa (layout padrão com Morph e animação).
  - Nenhum conteúdo clínico fica fixo no código: o texto do HOF sai de `bold_deck.py` e vai para `references/modelo_hof_roteiro.json`, copiado do modelo (`/var/tmp/aulas-render/in/modelo.pptx`). Caminho fixo `/tmp/hof/img/` sai do código; imagem vem do campo do slide, e sem imagem entra o quadro de prompt.
  - `tests/fixtures/aulas/modelo-v1.json` é a impressão digital do modelo, extraída de `/var/tmp/aulas-render/in/modelo.pptx` por um script do próprio teste ou de `aulas.py`: por slide, cor do fundo, nomes, posição e tamanho das formas `!!`, e os textos. Sem imagem nem binário.
  - Teste de fidelidade: gerar `modelo_hof_roteiro.json` produz 16 slides em que, por slide, a cor de fundo, o conjunto de formas `!!` (nome, posição e tamanho com tolerância de 0,02 pol) e o conjunto de textos batem com a impressão digital. Todo slide tem transição Morph e `p:timing`. Diferença só é aceita onde o modelo tem foto e o roteiro de teste não tem (quadro de prompt), e o teste diz quais slides são.
  - Tipo que não existe no estilo pedido encerra com erro que lista os tipos válidos.
- **Verificação:** `uv run --locked pytest -q tests/test_aulas.py tests/test_aulas_ousado.py`

### Cartão 2: restyle (extrair e preservado) e avulso

- **Objetivo:** levar um deck pronto para o modelo sem ninguém editar o .pptx à mão, e permitir slide avulso.
- **Arquivos permitidos:** `skills/aulas/scripts/aulas.py`, `skills/aulas/scripts/restyle.py`, `skills/aulas/scripts/bold_deck.py`, `skills/aulas/scripts/clinic_deck.py`, `tests/test_aulas_restyle.py`
- **Critérios de aceite:**
  - `aulas.py extrair deck.pptx pasta/ [--slides 3,5-9]` grava `pasta/roteiro-rascunho.json` e `pasta/img/`. Para cada slide: `origem` (número do slide), título detectado, textos na ordem de leitura, imagens exportadas com o caminho, contagem de formas desenhadas (linhas, setas, formas livres, grupos) e `tipo` sugerido por regra simples e documentada. Slide com imagem mais 4 ou mais formas desenhadas sobre ela recebe `tipo: "preservado"`.
  - O rascunho não inventa nem resume texto: todo texto do slide original aparece nele.
  - Tipo `preservado` (campos `deck`, `slide`, `titulo`, `kicker`): a tool copia as formas do slide original, menos título, logo, número de página e fundo, para a área de conteúdo da moldura do estilo, com escala única e proporção mantida. Imagens, tabelas, grupos e conectores continuam editáveis; as imagens são religadas ao pacote novo.
  - `"avulso": true` gera exatamente os slides do roteiro, nos dois estilos.
  - Testes com um deck sintético criado no próprio teste (sem depender de arquivo externo): extrair acha título, textos e imagem; `--slides` filtra; `preservado` mantém a contagem de formas e as imagens abrem; avulso não insere slide.
  - Ensaio manual registrado no retorno (não é teste): `extrair` em `/var/tmp/aulas-render/in/hof-original.pptx` termina sem erro e diz quantos slides caíram em cada tipo.
- **Verificação:** `uv run --locked pytest -q tests/test_aulas.py tests/test_aulas_ousado.py tests/test_aulas_restyle.py`

### Cartão 3: conferir e prévia

- **Objetivo:** barrar por máquina o deck que foge do padrão, antes de chegar em quem revisa.
- **Arquivos permitidos:** `skills/aulas/scripts/aulas.py`, `skills/aulas/scripts/conferir.py`, `tests/test_aulas_conferir.py`
- **Critérios de aceite:**
  - `aulas.py conferir deck.pptx [--estilo padrao|ousado] [--json]` devolve achados por slide e sai com código 1 quando há reprovação.
  - Reprova: fonte fora da família Montserrat em texto visível; cor de texto ou preenchimento fora da paleta do estilo (as constantes do gerador são a fonte da paleta; imagem e gráfico não contam; o conteúdo de um `preservado` vira aviso, não reprovação); forma fora dos limites do slide; texto estourado (estimativa por largura média do caractere, documentada como estimativa); no estilo ousado, slide sem `!!fundo`, sem `!!logo`, sem Morph ou sem animação; marcador `[EXEMPLO` ou `[confirmar]` no texto vira aviso.
  - O `gerar` roda o `conferir` no fim, imprime o resumo e devolve o código dele; `--sem-conferir` existe só para teste.
  - Um deck gerado pela tool nos dois estilos passa; o modelo de referência passa no estilo ousado (ensaio manual no retorno, com `/var/tmp/aulas-render/in/modelo.pptx`); um deck com Arial e cor fora da paleta reprova, com o slide apontado.
  - `aulas.py previa deck.pptx pasta/` gera um PNG por slide quando existem `soffice` e `pdftoppm`; sem eles, sai com mensagem clara e código 2.
- **Verificação:** `uv run --locked pytest -q tests/test_aulas.py tests/test_aulas_ousado.py tests/test_aulas_restyle.py tests/test_aulas_conferir.py`

### Cartão 4: papéis, skill, fluxo e pacotes

- **Objetivo:** o time passa a usar a tool: `aulas` dirige, `revisor-aulas` aprova, o Editor-Chefe conhece as três entradas.
- **Arquivos permitidos:** `skills/aulas/SKILL.md`, `agents/editorial/aulas.md`, `agents/editorial/revisor-aulas.md`, `skills/revisor-aulas/SKILL.md`, `skills/editor-chefe/SKILL.md`, `skills/editor-chefe/references/fluxo.md`, `scripts/package.py`, `.claude-plugin/plugin.json`, `tests/test_aulas.py`, `tests/cenarios/editor-chefe.md`, `docs/guia-paula.md`, `docs/guia-equipe.md`, `README.md`, `CHANGELOG.md`, `docs/superpowers/plans/2026-11-23-aulas-modelo-mestre.md`, mais os arquivos gerados que `scripts/package.py` sincroniza (referências comuns copiadas e `dist/`), listados um a um no retorno
- **Critérios de aceite:**
  - `skills/aulas/SKILL.md` descreve os dois estilos e as três entradas: aula do zero com conteúdo; deck ou slide de referência para deixar no padrão (`extrair`, direção, `gerar`); slide avulso por pedido ou correção de um slide. Diz que o modelo mestre v1 é o estilo `ousado` e que pedido de "refazer no design system novo" usa esse estilo, salvo pedido explícito do padrão.
  - `agents/editorial/aulas.md`: missão de diretor. Monta ou ajusta o roteiro, roda `aulas.py`, lê o relatório do `conferir` e a prévia. Limites explícitos: não escreve python-pptx, não abre nem edita o .pptx por outro meio, não entrega com `conferir` reprovado. O retorno traz o resumo do `conferir`.
  - `agents/editorial/revisor-aulas.md` (modelo `sonnet`, só leitura mais Bash; no Codex, Sol) e a skill dele: recebe o .pptx, o roteiro, o relatório do `conferir` e a prévia; confere slide a slide contra o roteiro e a descrição do estilo; devolve o bloco de retorno com `Nota` e `Achados`, e `PRONTO` só sem reprovação. Não edita nada.
  - `fluxo.md` e a skill do Editor-Chefe: `aulas` produz, `revisor-aulas` aprova, só então a entrega vai à pessoa; o trecho "sem portão de nota na V1" sai.
  - `uv run --locked python scripts/package.py --check` passa com o papel novo nos pacotes; `CHANGELOG.md` ganha a versão; os guias da Paula e da equipe ganham um trecho curto com os três pedidos prontos para colar.
  - O `## Status` deste plano fica atualizado.
- **Verificação:** `uv run --locked pytest -q && uv run --locked python scripts/package.py --check`

## Status

- Feito: verificação dos três arquivos de referência, plano e cartões 1 a 4.
- Em andamento: nada.
- Travado: nada.
- Próximo passo: revisão única do `cross-reviewer`, integração, PR e merge.
