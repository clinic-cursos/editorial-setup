# Frente Slides: placar de fidelidade ao modelo e conteúdo intocado

Issue: CLI-716. Pedido do Alify em 26/11/2026, aprovado na conversa ("aprovado sua proposta. pode aplicar").

## Por quê

O setup passa a ter duas frentes: **Editorial** (livros) e **Slides**. Na frente Slides, a regra da Paula é dupla:

1. Todo slide entregue segue fielmente o modelo mestre v1 (`/var/tmp/aulas-render/in/modelo.pptx`, igual ao "Exploração ousada - HOF básico.pptx" enviado em 26/11, mesmo MD5 `d41f4576...`). A fidelidade vira um placar de 0 a 100 e a entrega só sai com 100; o que faltar do modelo é completado.
2. Na refatoração ou verificação de um deck enviado, o conteúdo não muda: nada é reduzido, cortado, reescrito, reordenado nem desviado de sentido. No ajuste pontual, muda só o que foi pedido.

Hoje a skill `aulas` autoriza "ajustar o texto sem alterar o sentido" e "cerca de 40 palavras" também na adaptação, o revisor libera com nota 90, e nenhuma checagem compara o texto do original com o refeito.

## Desenho

- **Três modos na frente Slides:** produção (aula do zero, fluxo atual, densidade de 40 palavras vale só aqui); refatoração ou verificação de deck enviado (conteúdo intocado; se não couber, divide em mais slides no modelo, nunca reduz); ajuste pontual (só o pedido, o resto idêntico).
- **Placar do modelo no `conferir`:** nota por slide de 0 a 100, calculada pelas regras que o `conferir` já tem, agrupadas em categorias com peso. Só reprovação (`error`) desconta; aviso não desconta. Toda reprovação desconta de alguma categoria, então nota 100 significa nenhuma reprovação no slide. A saída lista a nota de cada slide abaixo de 100 e o que falta (o gap).
- **Fidelidade de conteúdo:** `conferir --origem <deck original>` compara as palavras e números do texto dos slides do original com os do deck refeito, em ordem. Faltou, trocou ou mudou de ordem: reprova, com o slide de origem e o trecho. Acréscimo (kicker, rodapé, slides inseridos) não reprova. Diferença de caixa, de espaço (NBSP) e de pontuação não conta, porque o modelo aplica caixa alta e espaços não separáveis.
- **Revisor:** entrega só com placar 100 em todos os slides e sem divergência de conteúdo; as duas viram eliminatórias. O modelo v1 não muda.

Fora do escopo: identificar a composição do mestre de cada slide gerado (o gerador não marca o tipo no slide; as regras atuais de elementos-base valem para todos); checar acréscimo indevido no ajuste pontual (o `--origem` contra a versão anterior mostra só o que saiu ou mudou, e o revisor confere o resto pela prévia).

### Categorias do placar

| Categoria | Regras do `conferir` | Peso |
|---|---|---|
| elementos-base | `morph_shape` (`!!fundo`, `!!logo`) | 20 |
| transicao | `morph` | 15 |
| animacao | `animation` | 15 |
| fonte | `font` | 15 |
| paleta | `fill_color`, `outline_color`, `text_color`, `marker` | 15 |
| leitura | `bounds`, `overflow`, `text_overlap`, `contrast` e qualquer regra nova não listada | 20 |

No estilo `padrao`, transição e animação não se aplicam: a nota é a soma das categorias aplicáveis sem reprovação, dividida pela soma dos pesos aplicáveis, vezes 100, arredondada para baixo.

## Tarefa única, três cartões em série, um PR

Gravidade média: afeta as aulas entregues pelo time; o erro aparece no `conferir`, na prévia e no revisor; desfaz-se revertendo o PR. Risco normal. Base do primeiro cartão: `feat/slides-fidelity` (este plano).

### Cartão 1: placar do modelo no `conferir`

- **Função:** backend
- **Objetivo:** acrescentar ao `conferir` o placar de 0 a 100 por slide e do deck, com as categorias e pesos da tabela do plano, e listar o gap de cada slide abaixo de 100. Sem mudar regra existente nem o código de saída.
- **Arquivos permitidos:** `skills/aulas/scripts/conferir.py`, `tests/test_aulas_conferir.py`
- **Critérios de aceite:**
  - O JSON do `conferir` ganha `scores` (lista com `slide`, `score`, `gaps`, cada gap com `category`, `rule`, `message`) e `model_score` (`{"min": int, "mean": int, "slides_below_100": int}`).
  - O terminal imprime `Placar do modelo: <min>/100 (<n> de <total> slides com 100)` e uma linha por slide abaixo de 100 com as categorias faltantes.
  - Teste: deck ousado gerado do `references/exemplo_ousado.json` tem todos os slides com 100.
  - Teste: o mesmo deck sem o `!!logo` de um slide dá 80 nesse slide, com o gap `elementos-base`.
  - Teste: fonte fora da Montserrat num slide dá 85 nesse slide, com o gap `fonte`.
  - Teste: um aviso sem reprovação não desconta.
- **Verificação:** `uv run --locked pytest -q tests/test_aulas_conferir.py tests/test_aulas.py tests/test_aulas_ousado.py`

### Cartão 2: fidelidade de conteúdo com `--origem`

- **Função:** backend
- **Objetivo:** `aulas.py conferir <deck> --origem <original.pptx> [--origem-slides 3,5-9]` compara o texto do original com o do deck e reprova palavra ou número faltando, trocado ou fora de ordem.
- **Arquivos permitidos:** `skills/aulas/scripts/conferir.py`, `skills/aulas/scripts/aulas.py`, `tests/test_aulas_conferir.py`
- **Critérios de aceite:**
  - Texto lido de todas as formas dos slides (grupos e tabelas, recursivo), sem as notas e sem os espaços reservados de número de slide, rodapé e data.
  - Tokens: NFC, `casefold`, `re.findall(r"\w+")`. Comparação por `difflib.SequenceMatcher(None, origem, saida, autojunk=False)`. `delete` e `replace` do lado da origem reprovam; `insert` não.
  - JSON ganha `content` com `origin`, `origin_tokens`, `kept_tokens`, `fidelity_pct` e `divergences` (`origin_slide`, `missing`, `replaced_by`). Cada divergência também entra em `findings` com `rule: "content"` e `severity: "error"`, então o código de saída vira 1.
  - `--origem-slides` usa a mesma sintaxe do `extrair --slides`.
  - Testes: mesmo texto com caixa alta, NBSP e `**` passa com 100%; palavra removida reprova e aponta o slide de origem; número trocado reprova; frase reordenada reprova; kicker acrescentado passa; texto dividido em dois slides passa.
- **Verificação:** `uv run --locked pytest -q tests/test_aulas_conferir.py tests/test_aulas.py tests/test_aulas_ousado.py tests/test_aulas_restyle.py`

### Cartão 3: frente Slides nas skills, agentes e guias

- **Função:** docs
- **Objetivo:** escrever as regras da frente Slides e dos três modos nas skills e nos agentes, ligar o placar e o `--origem` ao fluxo, sincronizar o pacote e subir a versão para 0.2.9.
- **Arquivos permitidos:** `skills/aulas/SKILL.md`, `skills/revisor-aulas/SKILL.md`, `skills/editor-chefe/SKILL.md`, `skills/editor-chefe/references/fluxo.md`, `agents/editorial/aulas.md`, `agents/editorial/revisor-aulas.md`, `agents/editorial/editor-chefe.md`, `README.md`, `docs/guia-paula.md`, `CHANGELOG.md`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, e as cópias que `scripts/package.py --sync` regenerar (listadas no retorno).
- **Critérios de aceite:**
  - README e editor-chefe falam em duas frentes: Editorial (livros) e Slides.
  - `skills/aulas/SKILL.md` tem a seção "Modos da frente Slides" com produção, refatoração ou verificação e ajuste pontual. Refatoração: não reduzir, cortar, alterar, reordenar nem desviar o sentido; se não couber, dividir em mais slides do modelo; rodar `conferir --origem <deck enviado>` e entregar só com 100% de fidelidade de conteúdo. Ajuste pontual: mudar só o campo pedido, partir do roteiro da versão anterior, rodar `conferir --origem <versão anterior>` e explicar cada divergência como a mudança pedida. As frases das linhas 78, 120 e 144 de hoje ficam restritas à produção.
  - Placar: entrega só com `model_score.min` igual a 100; abaixo disso, completar o gap pelo roteiro e gerar de novo. Nunca mudar o modelo para fechar o placar.
  - `revisor-aulas` (skill e agente): eliminatório placar abaixo de 100 em qualquer slide e qualquer divergência de conteúdo do `--origem`; `PRONTO` exige nota do revisor de pelo menos 90, placar 100 e conteúdo 100%. Na verificação de deck enviado sem refazer, o revisor devolve o placar e os gaps.
  - `fluxo.md` e o guia da Paula trazem exemplos de pedido para os três modos.
  - `uv run --locked python scripts/package.py --sync` rodado; versão 0.2.9 nos dois `plugin.json` e no `CHANGELOG.md`.
  - Sem travessão.
- **Verificação:** `uv run --locked python scripts/package.py --check && uv run --locked pytest -q`

## Teste de ponta a ponta (orquestrador, depois do merge)

Com Docker para a prévia: deck "cagado" de propósito, gerado a partir do roteiro de referência e estragado (logo removido, fonte trocada, palavra cortada, frase reordenada). Fluxo: editor-chefe → `aulas` em modo verificação (placar e gaps) → `aulas` em modo refatoração (`extrair`, `gerar`, `conferir --origem`) → `revisor-aulas` → ajuste pontual de um texto. Prova: placar 100 em todos os slides, conteúdo 100% e só o texto pedido mudou no ajuste.

## Status

- Feito: plano escrito; issue CLI-716 aberta.
- Em andamento: cartão 1.
- Travado: nada.
- Próximo passo: despachar os cartões 1 a 3 em série, revisão pelo `cross-reviewer`, PR, merge e o teste de ponta a ponta.
