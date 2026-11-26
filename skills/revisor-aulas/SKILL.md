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
5. Marque como eliminatório qualquer reprovação do `conferir`, placar abaixo de 100 em qualquer slide, qualquer divergência de conteúdo indicada por `--origem`, imagem de conteúdo da origem ausente sem omissão decidida pelo Editor-Chefe, slide incorreto ou ausente, desvio da identidade requerida ou corte ou sobreposição que impeça a leitura. Devolva `PRONTO` somente com nota de pelo menos 90, placar 100 em todos os slides e conteúdo e imagens 100% fiéis à origem, descontadas as omissões registradas. Em `Achados:`, cite as imagens omitidas e os quadros pendentes indicados em `pending_images`, mesmo quando não forem eliminatórios. Se reprovar, devolva `BLOQUEADO` com os achados da versão para o Editor-Chefe devolver a `aulas`.
   - Elimine slides com fonte fora da tipografia do modelo, ou cor ou fundo fora da paleta do modelo do estilo. Aplique o critério também ao conteúdo copiado por `preservado`, inclusive quando o `conferir` só emitir aviso. A exceção clínica preserva as cores de marcadores pequenos e linhas sobre imagem, seja foto ou ilustração anatômica. Na legenda cromática, texto e marcadores de lista mantêm a cor da marcação correspondente no mesmo slide, com ajuste de contraste quando necessário.
   - Elimine o uso de `preservado` em slides sem marcação desenhada sobre imagem, tabela ou composição de três ou mais imagens de conteúdo.
   - Elimine qualquer imagem gerada para antes e depois, caso clínico, foto de paciente ou print de artigo. Imagem anatômica, de área de risco ou diagrama científico gerado sem o aviso `Imagem gerada por IA: conferir com atlas ou professor antes de usar.` nas notas do slide e sem estar listado como pendente de validação pelo professor também é eliminatória. Na prévia, confira se cada imagem gerada corresponde ao `prompt_imagem` e ao conteúdo do slide.
6. Se a tarefa for verificar um deck enviado sem refazê-lo, devolva o placar do modelo e os gaps por slide, além dos achados visuais e de conteúdo.

Use o [bloco de retorno](references/comum/retorno.md), sempre com `Nota:` e `Achados:`. Se faltar material, use `Nota: Não atribuída`. Em `Arquivos entregues:`, escreva `Nenhum.` e informe as pendências no bloco. Faça toda a revisão em modo de leitura e peça a correção no retorno. A avaliação libera o encaminhamento da versão à pessoa para conferência.
