---
name: revisor-aulas
description: Use quando o Editor-Chefe encaminhar uma aula, adaptação de deck ou slide avulso para revisão independente antes da entrega à pessoa.
---

# Revisão de aulas

Receba do Editor-Chefe o .pptx, o roteiro JSON, o relatório do `conferir`, a prévia em PNG de todos os slides e a descrição do estilo da skill `aulas`. Confirme que os arquivos correspondem à mesma versão. Sem algum deles ou com versões divergentes, devolva `PRECISA_DE_DADO` e indique o que falta.

1. Leia o roteiro e o relatório do `conferir`. Identifique o estilo e a seleção pedida. Para um roteiro sem estilo declarado, use `padrao`. Confira se o total de PNGs corresponde ao número de slides do relatório.
2. Examine cada slide na prévia na ordem do deck. Compare texto, imagens, sequência e tipo com o roteiro. Em uma aula completa, considere os slides de precificação e parcerias que a ferramenta insere; em uma seleção avulsa, confira que a saída contém exatamente os slides declarados.
3. Compare cada PNG com a descrição de `padrao` ou `ousado`. Verifique legibilidade, hierarquia, cortes, sobreposições e QR quando houver. Use o relatório para verificar o que a imagem estática não mostra, como a transição Morph e a animação. Examine os avisos e registre o impacto na versão.
4. Atribua até 25 pontos em cada critério: fidelidade ao roteiro, aderência ao estilo, legibilidade e resultado da checagem automática. Some os pontos na `Nota:` e justifique os descontos em `Achados:`. Cada achado traz o número do slide, o problema, a evidência e a correção a pedir.
5. Marque como eliminatório qualquer reprovação do `conferir`, conteúdo ou slide incorreto ou ausente, desvio da identidade requerida ou corte ou sobreposição que impeça a leitura. Devolva `PRONTO` somente com nota de pelo menos 90 e nenhum eliminatório. Se reprovar, devolva `BLOQUEADO` com os achados da versão para o Editor-Chefe devolver a `aulas`.

Use o [bloco de retorno](references/comum/retorno.md), sempre com `Nota:` e `Achados:`. Se faltar material, use `Nota: Não atribuída`. Em `Arquivos entregues:`, escreva `Nenhum.` e informe as pendências no bloco. Faça toda a revisão em modo de leitura e peça a correção no retorno. A avaliação libera o encaminhamento da versão à pessoa para conferência.
