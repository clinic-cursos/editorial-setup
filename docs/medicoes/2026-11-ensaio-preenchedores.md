# Ensaio de diagramação: Preenchedores_Dermicos_Consolidado_40_Alteracoes

Resultado: REPROVADO

- Motivos: erro de layout na composição; erro de layout depois da inserção das imagens; fidelidade do texto abaixo de 0,995 ou com diferenças listadas
- Metadados preenchidos a partir da capa e do expediente: authors, course, title, version

## Composição (v1)
- Páginas: 117
- Fontes encontradas: Montserrat (117 pág.), Montserrat-Bold (40 pág.), Montserrat-Semi-Bold (99 pág.), SourceSans3 (96 pág.)
- DejaVu: nenhuma
- Erros: 62; avisos: 3
- aviso `image-low-resolution`: 3
- erro `duplicate-paragraph`: 19
- erro `image-low-resolution`: 30
- erro `toc-mismatch`: 13

## Fidelidade do texto (mínimo aceito 0,995)
- PDF original contra manuscrito extraído: 0.9028 0.9038 (108 linhas de diferença)
- Manuscrito contra PDF composto (v1): 0.9949 0.9966 (17 linhas de diferença)

## Imagens sintéticas (retângulos na paleta)
- Páginas candidatas (espaço livre acima do limite): 50
- Imagens de teste geradas (as primeiras candidatas, no máximo 3): 3
- Imagens inseridas: 2; retiradas por mudar a paginação: 0

## Depois das imagens (v2)
- Paginação: 117 páginas antes, 117 depois; âncoras dos blocos iguais
- Erros: 62; avisos: 3
- aviso `image-low-resolution`: 3
- erro `duplicate-paragraph`: 19
- erro `image-low-resolution`: 30
- erro `toc-mismatch`: 13
- Fidelidade (manuscrito contra v2): 0.9949 0.9966 (17 linhas de diferença)

## Causa provável e correção sugerida (por script)
- `duplicate-paragraph`: `lib/pdfcheck` (`check_duplicates`): o texto repetido começa na linha do cabeçalho corrido e passa de 100 caracteres. Correção: tirar cabeçalho e rodapé da comparação.
- `image-low-resolution`: `build_book.py` e `assets/` (CSS): a figura extraída é esticada à largura da coluna e cai abaixo do ppi do original. Correção: limitar a largura da figura ao tamanho do original (pixels pelo ppi herdado).
- `toc-mismatch`: `extract_pdf.py` mantém o sumário do original como texto do corpo, com entradas partidas em linhas e números de página antigos, e `check_toc` o lê como sumário. Correção: descartar capa, expediente e sumário do original na extração e deixar o `build_book.py` gerar o sumário.
- fidelidade: perdas e acréscimos de palavras e números alterados em URLs e referências (`text_fidelity.py` lista os trechos). A causa provável é `extract_pdf.py` (rótulos de bloco como «Ponto-chave» e «Perguntas frequentes», quebra de linha em URL). Correção: conferir a lista no cartão de correção.

