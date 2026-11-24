# Histórico de versões

## 0.2.7

- No `texto_imagem` em `conter` sem corpo, o título fica em uma linha, o kicker mantém a posição do modelo e a imagem ocupa a maior área livre.
- A imagem em `conter` fica fora da área do logo.
- Números e suas unidades ficam juntos na mesma linha. Faixas numéricas com espaços também ficam juntas.
- `**` sem par permanece visível como texto, e `\*\*` exibe os dois asteriscos literalmente.
- Tópicos sem título e marcações de anatomia sem nome deixam de exibir asteriscos extras.

## 0.2.6

- O estilo ousado mantém a moldura do modelo nos tipos de fallback.
- A imagem do `texto_imagem` no modo `conter` ocupa o espaço livre.

## 0.2.5

- A exceção clínica do `preservado` mantém as cores de marcadores pequenos e de marcações sobre imagem, inclusive ilustração anatômica. A legenda cromática mantém no texto e nos marcadores de lista a cor da marcação do mesmo slide, com ajuste de contraste quando necessário. O `conferir` reprova cores de texto fora da paleta sem correspondência com uma marcação.
- O `preservado` ajusta os rótulos do original que estouram. Caixas com ajuste automático crescem quando há espaço. Nos demais casos, a fonte diminui até caber ou chegar ao limite previsto. O `conferir` reprova estouro de altura que persiste após o ajuste.
- O `extrair` sugere `preservado` para marcações sobre imagem, tabelas ou composições de três ou mais imagens. Em aulas completas, o `gerar` recusa `preservado` de imagem simples e indica `texto_imagem` com `imagem_modo` igual a `conter`.

## 0.2.4

- O slide `preservado` recebe a mesma moldura do slide 8 do modelo mestre v1.
- O `gerar` valida o esqueleto da aula completa, aponta cada violação por slide e numera os módulos pela posição; com `"avulso": true`, dispensa essa validação.
- No slide avulso, o `gerar` mantém o `numero` declarado para o módulo.
- O hook protege a impressão digital, o roteiro e os recursos visuais do modelo mestre v1. Os testes fixam os hashes dos dois arquivos JSON. Só o Alify pode abrir o modelo v2, com arquivos novos ao lado dos da v1.
- A adaptação prefere tipos nativos e reserva `preservado` para marcações sobre foto, tabelas e composições de três ou mais imagens. O revisor reprova desvios de fonte, cor ou fundo, inclusive no conteúdo copiado, e o uso de `preservado` em slides só de texto ou de texto com até duas imagens.
- O `extrair` mantém o recorte original das imagens PNG e JPEG e sinaliza as imagens recortadas no roteiro.
- O texto de `preservado` usa Montserrat e ganha contraste sobre fundos sólidos conhecidos. Os preenchimentos e contornos sujeitos à normalização adotam a paleta do estilo.
- No estilo ousado, `numero` ajusta o valor para caber dentro do arco, e `pilares` recorta a foto para preencher o painel.

## 0.2.3

- Nas listas sem painel de imagem do estilo ousado, passo a passo, alerta, pilares e texto com imagem, a letra cresce até ocupar a área útil; em duas colunas, mantém o tamanho do modelo.
- No passo a passo, o primeiro passo fica abaixo de um título de duas linhas e o espaço entre passos é uniforme.
- O comparativo aceita `imagem_modo` e a altura dos itens acompanha o texto.
- O `preservado` reconhece título com quebra de linha e remove o fio que o acompanha, ignora formas vazias ou invisíveis ao calcular a escala e garante que o texto copiado fique dentro da área de conteúdo.
- O `conferir` reprova título sobre o primeiro passo e itens sobrepostos no comparativo.

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
