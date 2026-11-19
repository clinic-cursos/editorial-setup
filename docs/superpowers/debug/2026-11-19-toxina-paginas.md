# CLI-514: paginação na recomposição do Toxina

## Relato

Na base `feat/wave-3b` (`45390a2`), o PDF A4 de 80 páginas gera um composto A4 de 297 páginas. O esperado é que o texto visível e a hierarquia editorial do original sobrevivam à extração e que cada figura herdada caiba no tamanho em que foi colocada na origem. A paginação pode mudar com a diagramação.

Limitar as figuras ao tamanho original reduziu a saída de **297 para 203 páginas**, uma diferença de **94 das 217 páginas a mais (43,3%)**. Restaram **123 páginas a mais (56,7%)** naquele cenário. Dois defeitos explicam esse restante: a promoção de subtítulos e outros blocos a capítulos, que aciona quebras de página, e a extração de texto e imagens inteiramente escondidos pelo recorte do PDF.

## Reprodução

Python 3.12.16, pdfplumber 0.11.10, pypdf 7.1.1 e WeasyPrint 70.0, conforme o ambiente local e o `uv.lock`. O original foi aberto em leitura. A sessão bloqueou a criação de pasta em `/var/tmp`, então os protótipos rodaram em uma pasta privada em `/tmp`.

1. Na raiz da worktree, com as dependências travadas disponíveis, rode:

   ```sh
   export EDITORIAL_SAMPLES_DIR=/home/alify/Downloads/livros-paula
   export PYTHONDONTWRITEBYTECODE=1
   umask 077
   work=$(mktemp -d /tmp/cli514-toxina.XXXXXXXX)
   export TMPDIR="$work"
   source_pdf=$(find "$EDITORIAL_SAMPLES_DIR" -maxdepth 1 -iname '*toxina*.pdf' -print -quit)
   pdfinfo "$source_pdf" | awk '/^(Pages:|Page size:)/'
   uv run --locked python skills/diagramador/scripts/extract_pdf.py "$source_pdf" \
     --out "$work/manuscrito.md" --images "$work/img"
   uv run --locked python skills/diagramador/scripts/build_book.py "$work/manuscrito.md" \
     --out "$work/base"
   ```

   Na execução, usei o Python do ambiente já instalado da base (`/var/tmp/editorial-wt/wave3b/.venv/bin/python` no lugar de `uv run --locked python`). Resultado observado: `Pages: 80`, `Page size: 595.276 x 841.89 pts (A4)`, `297 páginas, 743 blocos`. A extração levou 24,18 s e a composição 17,41 s.

2. Leia `PdfReader.outline` e as páginas dos três destinos de nível 0. Use a página de origem e o texto normalizado para achar o título equivalente entre os blocos do manuscrito. Consulte `layout.json` para localizar esses blocos no composto. Na base, os IDs são `b0038`, `b0104` e `b0659`. Os três números de abertura estão isolados na página imediatamente anterior a cada título do composto. A tabela usa a âncora do título como início do capítulo, com intervalos inclusivos e sem dupla contagem. A página 80 do original está no intervalo final e gerou zero blocos.

   | Trecho | Original | Composto | Figuras limitadas | Figuras, níveis e recortes controlados |
   |---|---:|---:|---:|---:|
   | Pré-texto, até a primeira âncora | 1 a 7 (7) | 1 a 14 (14) | 1 a 14 (14) | 1 a 7 (7) |
   | Capítulo 1 | 8 a 17 (10) | 15 a 46 (32) | 15 a 38 (24) | 8 a 16 (9) |
   | Capítulo 2 | 18 a 66 (49) | 47 a 261 (215) | 39 a 177 (139) | 17 a 61 (45) |
   | Capítulo 3 até o fim | 67 a 80 (14) | 262 a 297 (36) | 178 a 203 (26) | 62 a 73 (12) |
   | **Total** | **80** | **297** | **203** | **73** |

3. Em uma cópia temporária do HTML ou por transformação em memória, renderize com `HTML(...).render()`, conservando o diretório da base para resolver CSS e imagens. Conte `len(document.pages)`. Faça as mudanças da tabela uma por vez. Atribua cada delta ao cenário em que foi medido, pois a paginação depende da ordem das mudanças.

   | Mudança acumulada | Páginas | Delta |
   |---|---:|---:|
   | Base | 297 | |
   | Limite físico de cada ocorrência da figura | 203 | −94 |
   | Remove a quebra automática de todos os `h1` fora dos três títulos do índice | 156 | −47 |
   | Dá aos demais títulos o estilo de `h2`, inclusive no sumário | 145 | −11 |
   | Filtra glifos inteiramente fora do recorte antes de extrair linhas | 94 | −51 |
   | Retira também as ocorrências de imagem inteiramente fora do recorte | 73 | −21 |

   Controles independentes: desativar apenas as quebras na base deu 251 páginas. Excluir apenas as imagens ocultas partindo de 145 deu 123 páginas. Aplicar o recorte de texto e imagens com as figuras limitadas e os níveis ainda originais deu 104. O protótipo combinado termina sete páginas abaixo do original. Esse saldo compara dois layouts e depende da hierarquia experimental.

## Causas e correções sugeridas

### 1. Toda figura ocupa a largura útil

`skills/diagramador/assets/livro.css:98` impõe `width: 100%`, e `skills/diagramador/scripts/build_book.py:56-61` emite a figura sem tamanho físico. O composto oferece 470,55 pt de largura útil. Em 168 das 188 ocorrências, esse valor excede o limite que mantém a proporção do arquivo e cabe na caixa de transformação original. A largura original por ocorrência tem mediana de 170,8 pt e mínimo de 15,87 pt. A redução de 94 páginas concentra-se no capítulo 2 (76 páginas), seguido pelos capítulos 3 (10) e 1 (8).

Para reproduzir o controle, no retorno de `page_items` associe o `fig-N` a `page.images` na ordem em que o contador é incrementado, antes da ordenação por leitura. As 188 ocorrências casaram com 63 arquivos. Para cada caixa de largura `W` e altura `H` em pontos, use a proporção intrínseca `r = pixels_w / pixels_h` e insira `width: min(W, H*r)pt; max-width:100%; height:auto` como estilo do `img`, substituindo `min(W, H*r)` pelo valor em pontos. A largura e a altura renderizadas ficaram dentro da caixa original em todas as 188 ocorrências. Esse controle usa a caixa transformada do objeto. O recorte efetivamente visível foi medido à parte.

Correção mínima sugerida no ramo `figure` de `_render`: passar dimensões em pontos por ocorrência extraída e aplicar esse teto com preservação da proporção. Na regra comum, trocar `width:100%` por `max-width:100%; height:auto`. Preservar a leitura do `origem.json` por arquivo pelo auditor. O mesmo arquivo pode aparecer em escalas diferentes, então o teto precisa acompanhar o identificador da ocorrência.

### 2. O extrator infere capítulos pelo tamanho do primeiro glifo

`skills/diagramador/scripts/extract_pdf.py:44-55` usa 1,6 vezes o corpo como limiar de `#`, e `render` aplica a mesma regra a todas as linhas (:166 e :199-201). `skills/diagramador/scripts/build_book.py:69-76` abre uma seção `.capitulo` para cada `#`, com `break-before: page` em `skills/diagramador/assets/livro.css:65`. O original tem três capítulos no índice interno. O manuscrito criou 95 `h1`, dos quais três títulos reais nas páginas esperadas, três números de abertura isolados e pelo menos dez títulos que coincidem com entradas subordinadas do índice. A extração também traz pré-texto do original, enquanto o modelo gera capa, expediente e sumário próprios. O primeiro bloco extraído aparece na página 8 do composto.

No controle de 203 → 156, acrescente `break-before:auto` às 92 seções cujo primeiro `h1` não é um dos três IDs do passo 2. No controle de 156 → 145, troque também a tag desses títulos por `h2` e tire a classe `nivel-1` dos seus itens de sumário. Os 92 blocos e seus textos continuam presentes nas duas renderizações.

Correção mínima sugerida em `extract_pdf.render`: quando existir índice interno confiável, promover a `#` só o título que coincide com a página e o texto de um destino de nível 0. Mapear entradas de nível inferior a subtítulos e tratar número isolado e pré-texto conforme a estrutura do manuscrito. Em PDFs sem índice confiável, encaminhar níveis incertos para conferência editorial antes de virar capítulo. Preservar a quebra de capítulos reais do compositor, inclusive em manuscritos e DOCX.

### 3. Os objetos que o recorte esconde entram na leitura

`skills/diagramador/scripts/extract_pdf.py:96-103` filtra a altura das linhas, e :123-143 converte cada imagem listada em figura. As caixas fornecidas por pdfplumber descrevem objetos do fluxo, inclusive objetos que o PDF esconde com clipping. No pdfminer.six instalado, `PDFPageInterpreter.do_W` e `do_W_a` não aplicam o recorte ao inventário geométrico. A página 21 desenha o mesmo objeto duas vezes na mesma caixa de 510,4 × 287,3 pt. Na segunda ocorrência, o limite superior da região efetiva está em 51,9 pt a partir da base e a imagem começa em 463,2 pt: a interseção é vazia. O extrator emite as duas figuras. Nas páginas 30 e 43, filtrar glifos ocultos derrubou as linhas classificadas como `#` de 26 e 19 para uma em cada.

Para reproduzir a prova, acompanhe em um interpretador temporário o recorte inicial da página, a pilha de `q/Q`, as matrizes de transformação, os operadores `W/W*` e a `BBox` de cada Form. Transforme os pontos de cada recorte para coordenadas da página e interseccione as caixas envolventes sucessivas. Marque um objeto como oculto se a interseção for vazia ou se a caixa do objeto ficar inteira fora dela (tolerância de 0,02 pt). Para o texto, filtre os glifos antes de `gutter` e `extract_text_lines`. Para as figuras, associe por página, ordem, objeto e caixa antes de excluir as ocorrências ocultas. Aplique de novo o limite de tamanho e mantenha a hierarquia do controle anterior, usando os mesmos três destinos de nível 0.

O protótipo contou 211.296 glifos não brancos inteiramente fora do recorte já dentro da faixa vertical considerada pelo extrator e 93 das 188 imagens inteiramente ocultas. Outras 43 imagens tinham interseção parcial. Descontadas as linhas Markdown das figuras, a contagem de tokens alfanuméricos caiu de 43.327 para 21.157. O manuscrito passou de 95 para 62 `h1` antes do controle de hierarquia. Igualdade de objeto e caixa é um critério diferente: fundir as 76 ocorrências geométricas repetidas e excluir uma fora da página deu 128 páginas a partir de 145, pois o recorte pode variar mesmo quando a caixa é a mesma. A filtragem de texto e imagens por recorte reduziu 72 páginas no cenário de 145.

Correção mínima sugerida antes de `page_items` montar linhas e figuras: usar a geometria visível de cada ocorrência, excluir só o que tem interseção comprovadamente vazia e preservar ocorrências parcialmente visíveis para conferir o recorte no resultado. Use o mesmo conjunto de glifos visíveis para estimar o corpo. Para recortes ambíguos, retenha o conteúdo e indique a página para conferência. Essa abordagem mantém usos repetidos legítimos e evita retirar texto só porque sua geometria coincide com outra ocorrência.

Mudanças propostas para os cartões, em pseudodiff:

```diff
--- skills/diagramador/scripts/extract_pdf.py
- page_items(page, ...) lê caixas de texto e imagem do inventário bruto
+ page_items(visible_page, ...) lê ocorrências com interseção visível ou incerta
- tag = classify(payload, body)
+ tag = classify(payload, body, outline_level_at_matching_destination)
--- skills/diagramador/scripts/build_book.py
- <img src="..." alt="...">
+ <img src="..." alt="..." com teto físico por ocorrência herdada>
--- skills/diagramador/assets/livro.css
- figure img { width: 100%; }
+ figure img { max-width: 100%; height: auto; }
```

## Tipografia, tabelas, quadros e listas

| Medida | Original | Composto |
|---|---|---|
| Família e tamanho modal do corpo | Source Sans 3 (SourceSans3-Roman), 11 pt | Source Sans 3 (SourceSans3), 9,5 pt |
| Distância modal entre linhas de base do corpo | 13,5 pt | 14 pt |
| Tabelas e quadros por geometria | `find_tables()`: 28 regiões em 20 páginas, sendo 10 multicoluna e 18 de uma coluna, candidatas a quadros ou tabelas de uma coluna | 0 elementos `table`, 0 blocos editoriais tipados |
| Rótulos exatos de tipos de quadro recuperados como títulos | 13 após filtrar recorte, em quatro tipos da convenção do projeto | 7 na extração da base, em dois tipos, todos como títulos |
| Listas | 78 linhas com marcador reconhecido na faixa do corpo bruto | 31 listas no manuscrito e no HTML do corpo, sendo 17 ordenadas e 14 com marcadores, 80 itens no total |

A entrelinha é a moda da diferença de coordenadas Y entre linhas sucessivas com pelo menos 20 glifos da fonte e do tamanho modal, diferença de início horizontal de até 10 pt e distância vertical de 9 a 21 pt. O CSS confirma 9,5/14 pt em `skills/diagramador/assets/tokens.css:21-22` e `skills/diagramador/assets/livro.css:40`. Usar 11/13,5 pt no composto de 73 elevou a saída para 76 páginas. Portanto a tipografia do corpo escolhida pelo modelo atenuou o aumento nesse controle.

O original não tem árvore de estrutura PDF. Os 28 contornos são candidatos geométricos. Em `extract_pdf.py:104-105` o reconhecimento resulta em aviso e o conteúdo segue como linhas, enquanto `manuscript.py:115-131` exige a marcação editorial para produzir caixas. O controle de recorte deixou 25 listas com 70 itens antes da composição. No cenário de 73 páginas, tirar das listas de corpo suas linhas próprias, margens e recuo rendeu 72 páginas. Isso mede apenas o custo da formatação atual de listas. A diferença de estrutura de tabelas e quadros foi medida pelo inventário. Os protótipos de texto não reconstroem células nem permitem atribuir um delta isolado de paginação a esses dois tipos. Qualquer recuperação da estrutura deve conferir se o texto pertence à célula ou ao quadro certo.

## Chamadores

Buscas `git grep -n -E 'classify\(|page_items\(|extract_pdf|_compose\(|build_book|figure img' -- '*.py' '*SKILL.md' '*.css'` e `git grep -n -E '\.capitulo|def _figure|origem.json' -- '*.py' '*.css' '*SKILL.md'`.

| Chamador ou consumidor | Impacto |
|---|---|
| `extract_pdf.main` (:257) → `render` (:157, :166) → `page_items` e `classify` | Caminho comum dos dois defeitos de extração. O CLI é usado por `scripts/run_sample.py:183` e pelo fluxo em `skills/diagramador/SKILL.md:22`. |
| `build_book.main` (:125) → `build` (:102) → `_compose` (:77) → `_render` (:52, :56) | Toda figura de manuscrito, inclusive em quadro, passa pelo mesmo tamanho. A saída depende da hierarquia de entrada. Usado pelo ensaio em `scripts/run_sample.py:191` e pelo CLI documentado na skill. |
| `insert_images.insert` (:82) e `insert_images._figure` (:49) | A composição-base sofre com figuras herdadas ampliadas e capítulos espúrios. A figura complementar já tem largura automática e limites próprios. Comparar paginação e âncoras com a nova base. |
| `check_layout.py:23-36` e `text_fidelity.py` | O primeiro consome a origem para auditar imagens. Preservar o contrato. O segundo importa `LABELS` e compara texto. Para este PDF, validar contra texto visível ou fonte editorial aprovada, pois a extração bruta de referência também pode incluir camadas recortadas. |
| `tests/test_extract_pdf.py`, `test_extract_pdf_forms.py`, `test_build_book.py`, `test_insert_images.py`, `test_insert_images_renders.py`, `test_run_sample.py` e `test_text_fidelity.py` | Cobrem os caminhos direto, CLI, Forms, inserção e ensaio. Adicionar os casos sintéticos de subnível no índice, tamanho herdado por ocorrência e recorte total/parcial. `extract_docx.py` usa o compositor no fluxo documentado e deve conservar seus níveis de origem. |

## Critério de aceite do cartão

1. Com PDF sintético com índice de dois níveis, um subtítulo maior que 1,6 vezes o corpo continua subordinado. Só a entrada de nível 0 inicia capítulo. Conferir abertura e sumário no PDF, e preservar os casos legados de Markdown e DOCX.
2. Com duas colocações do mesmo bitmap em escalas diferentes, medir no PDF composto a largura e altura de cada ocorrência. Ambas cabem nas respectivas caixas originais e mantêm a proporção. Conferir também imagem nova e inserção complementar.
3. Com texto e imagens em Forms e com `q/Q` e `W/W*`, extrair o conteúdo visível uma vez por colocação legítima. Omitir a colocação totalmente recortada e conferir a parcial em vez de omiti-la. Repetir o ensaio real e registrar a paginação por capítulo, a geometria das figuras e a fidelidade do conteúdo visível.

Prova sintética executada fora do Git. Em um A4 ReportLab, crie um título de capítulo 24 pt em (72, 742), subtítulo 22 pt em (72, 680), ambos no índice com níveis 0 e 1, e um parágrafo Helvetica 11 pt em (72, 650) com pelo menos 70 caracteres. Coloque um PNG quadrado de 100 px em (72, 610) com 20 pt de lado. Abra `saveState`, aplique `clipPath` de 20 × 20 pt em (390, 390), desenhe mais um texto de 11 pt em (72, 570) e o mesmo PNG de 20 pt em (72, 520), e restaure o estado. Rode `extract_pdf.render`, grave o manuscrito e as imagens que ele retorna, rode `build_book.build` e conte os `h1` do manuscrito, a presença do texto recortado e as larguras do PDF via pdfplumber. A asserção falhou com `actual=(2, True, [470.6, 470.6]) expected=(1, False, [20.0])`.
