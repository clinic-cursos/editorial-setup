# Histórico de versões

## 0.2.2

- O tipo `preservado` amplia o conteúdo copiado até a área útil, mantém a imagem de fundo do próprio slide, adiciona painel escuro quando o original tinha fundo escuro e evita duplicar o título.
- Nas listas do estilo ousado, passo a passo, duas colunas, alerta e sumário, a altura dos itens acompanha o texto.
- Sem imagem e sem prompt, não há painel nem quadro de prompt.
- `pilares` aceita `selo`.
- O `conferir` reprova texto sobreposto, agrupa os avisos de conteúdo preservado e inclui `preserved_findings` e `preserved_warnings` no JSON.
- O rascunho do `extrair` grava `imagens` como lista de objetos com `caminho` e `decorativa`, formato aceito pelo gerador.

## 0.2.1

- A skill de aulas documenta os campos do estilo ousado e inclui um roteiro de exemplo validado pelo `conferir`.

## 0.2.0

- A ferramenta `aulas.py` gera o PowerPoint nos estilos padrão e ousado. O ousado segue o modelo mestre v1.
- O Editor-Chefe recebe aulas do zero, adaptações de decks e slides avulsos ou corrigidos. O `revisor-aulas` confere cada slide e devolve nota e achados antes do encaminhamento à pessoa.

## 0.1.0

- Primeira versão do setup editorial da Clinic Editora, com sete papéis para livros e aulas.
- Fluxo de livros com ficha por projeto, auditorias científica e gráfica e aprovações humanas.
- Guias de instalação e uso para a Paula e a equipe, com registro de melhorias.
