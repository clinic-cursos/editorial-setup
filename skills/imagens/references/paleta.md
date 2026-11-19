# Paleta das imagens complementares

Cores que a Paula pediu (bordô, rosa claro, marsala e cinza), com o valor e de onde vem cada um. Estilo: conceitual e clean, fundo claro, muito espaço vazio.

Amostragem feita em 19/11/2026, por contagem de pixels exatos em páginas renderizadas dos PDFs de referência da Clinic (`Toxina_Botulinica_Miolo_Alta_Resolucao.pdf`, `Preenchedores_Dermicos_Consolidado_40_Alteracoes.pdf` e `Capa do livro teste.pdf`), a 30 e 40 ppp. Os PDFs ficam fora do repositório.

| Cor | Valor | Origem |
| --- | --- | --- |
| Bordô | `#87082E` | Fundo chapado da capa e da contracapa de Toxina e de Preenchedores (páginas 1 e 2, 100% dos pixels); também o texto de títulos no miolo. A capa de teste tem `#831431` no logotipo e gradiente de `#671224` a `#7B142F` no fundo. |
| Rosa claro | `#EAD4DB` | Preenchimento chapado de caixa no miolo de Toxina e de Preenchedores. Mais pálido, para fundo: `#F3EDEF` (maior área rosada do miolo, mais de 100 mil pixels). Mais escuro, para acento: `#D4A6B4`. |
| Marsala | `#955251` | Referência pública, não amostrada; a confirmar com a Paula. Não aparece como preenchimento chapado em nenhum PDF; o valor é o Marsala da Pantone (18-1438). O tom amostrado mais próximo é a transição `#AE5872` entre o bordô e o rosa. |
| Cinza | `#625E61` | Texto cinza da capa de teste (4,2% dos pixels). Cinza claro de fundo e filete: `#D9D7D7` e `#F8F7F7` (contracapa da capa de teste). |

Fundo da imagem: branco `#FFFFFF` ou `#F3EDEF`. O livro usa o bordô do design system em `#87082E` (`--color-brand`); as imagens seguem o mesmo valor para não destoar da página.

Uso: bordô e marsala como cores fortes, rosa claro como massa de cor e cinza como apoio. Máximo de quatro cores por imagem, sem degradê com cores fora desta tabela.
