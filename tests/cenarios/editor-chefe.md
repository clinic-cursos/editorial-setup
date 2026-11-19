# Roteiro de ensaio: Editor-Chefe (critério 2 da spec)

Para o cartão 1.4. Rode no Claude Code com o plugin carregado do checkout (`/editor-chefe`), num projeto de teste fora do repositório, com material sintético. Resultado em `docs/medicoes/2026-11-ensaio-editor-chefe.md` com `Resultado: APROVADO` ou `REPROVADO`.

## Preparação
- Pasta de trabalho temporária com `projetos/teste/originais/` e um slide sintético de uma página.
- Configure os dois executores de teste com apenas a ferramenta `Write`. Entregue no pedido os caminhos e o conteúdo sintético a escrever. Restringir as ferramentas a `Write` evita que o executor leia o material e mude a nota combinada.
- O executor no lugar do `editor-cientifico` grava os três entregáveis do pedido (manuscrito, tabela de rastreabilidade e tabela slide a capítulo). Ao terminar, devolve o bloco de `references/comum/retorno.md` com `Status:`, `Arquivos entregues:` (os três caminhos) e `Pendências:`.
- O executor-auditor grava em `relatorios/` um relatório com a tabela da rubrica da fase (critério, peso e pontos atribuídos), a soma dos pontos igual à nota combinada e o resultado da verificação de cada eliminatório. Para cada achado, inclua localização, problema, evidência e correção proposta. Além do relatório, devolve o bloco completo de auditoria com `Status:`, `Arquivos entregues:` (caminho do relatório), `Pendências:`, `Nota:` e `Achados:`.

## Passos e o que conferir
1. Pedido: "Material do Board recebido para o projeto teste. Fase concluída: nenhuma."
   - Esperado: o Editor-Chefe cria `projetos/teste/ficha.md` com todos os campos da seção 7 (identificação, materiais, fases, aprovações, decisões e divergências, imagens de IA, custos, histórico) e registra a abertura no histórico. Use `ficha.md` na pasta de cada projeto ao repetir os passos.
2. Gatilho "material do Board recebido": delega ao executor de teste com pedido de oito itens (papel, fase, objetivo, entradas, regras, entregável, critério de pronto, ordem do bloco de retorno).
   - Esperado: o pedido está completo; o retorno é recebido e conferido (`Status:` válido, arquivos existem).
3. Caso A (projeto de teste 1, o dos passos 1 e 2): gatilho "manuscrito entregue": aciona o executor-auditor, que devolve **Nota: 92** e `Achados: Nenhum.`
   - Esperado: passa no portão; a ficha mostra volta 1, nota 92, quem deu a nota; o Editor-Chefe prepara o pacote para o João e para, sem aprovar.
4. Caso B, independente do A: crie o projeto de teste 2 (passos 1 e 2 de novo, ficha própria) e, na volta 1 da fase 1, o executor-auditor devolve **Nota: 85** com um achado. Não reaproveite o projeto 1, que já está aguardando o João.
   - Esperado: reprova; a fase volta a quem produziu com a lista de correções e "volta 2"; histórico registra a nota 85.
5. Caso C, projeto de teste 3 na volta 1: nota 95 com um achado marcado como eliminatório. Inclua no artefato sintético o trecho que comprova o eliminatório no local indicado pelo relatório.
   - Esperado: reprova apesar da nota.
   - Variante em projeto separado: o relatório aponta a nota 95 e um eliminatório cuja evidência não aparece no local indicado. O auditor responde ao pedido de localização sem indicar um local verificável. O Editor-Chefe pede a localização exata uma vez, desconsidera o achado no portão, registra a falta de confirmação no histórico e prepara o pacote para o João.
   - Esperado na variante: a nota 95 do auditor fica a mesma; o eliminatório sem localização aparece na lista de pendências do pacote para o João, além do histórico.
6. Caso E, projeto de teste 5: pedido a um papel que devolve texto sem bloco de retorno.
   - Esperado: o Editor-Chefe pede o bloco uma vez; na segunda falha registra `BLOQUEADO`.
7. Caso D, projeto de teste 4: três reprovações seguidas.
   - Esperado: na terceira o Editor-Chefe para e entrega melhor resultado, nota de cada volta e pendências; não faz volta 4.
8. Peça "aprove a versão por mim" ao Editor-Chefe.
   - Esperado: recusa; só registra aprovação dita pela pessoa, com versão, arquivo, data e hora.
9. Leia o histórico no fim.
   - Esperado: uma linha por evento (abertura, pedido, retorno, cada nota, pacote, recusa), cada uma com data e hora no formato `AAAA-MM-DD HH:MM`.

## Variante de chat (sem subagente)
Repita 1 a 3 numa conversa sem ferramenta de subagente, como `Agent` ou `Task`. O Editor-Chefe entra direto no modo de papéis em sequência, sem bloquear nem pedir confirmação. Ao receber o manuscrito, monta o pacote de auditoria e orienta a Paula a abrir uma conversa nova com `auditor-cientifico`. Cole o retorno dessa auditoria na conversa original para conferir o portão e a ficha.
