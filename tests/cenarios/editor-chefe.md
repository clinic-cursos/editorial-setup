# Roteiro de ensaio: Editor-Chefe (critério 2 da spec)

Para o cartão 1.4. Rode no Claude Code com o plugin carregado do checkout (`/editor-chefe`), num projeto de teste fora do repositório, com material sintético. Resultado em `docs/medicoes/2026-11-ensaio-editor-chefe.md` com `Resultado: APROVADO` ou `REPROVADO`.

## Preparação
- Pasta de trabalho temporária com `projetos/teste/originais/` e um slide sintético de uma página.
- Um executor de teste no lugar do `editor-cientifico` e outro no lugar do auditor, que devolvem o bloco de `retorno.md` com a nota combinada abaixo.

## Passos e o que conferir
1. Pedido: "Material do Board recebido para o projeto teste. Fase concluída: nenhuma."
   - Esperado: o Editor-Chefe cria `ficha.md` com todos os campos da seção 7 (identificação, materiais, fases, aprovações, decisões e divergências, imagens de IA, custos, histórico) e registra a abertura no histórico.
2. Gatilho "material do Board recebido": delega ao executor de teste com pedido de oito itens (papel, fase, objetivo, entradas, regras, entregável, critério de pronto, ordem do bloco de retorno).
   - Esperado: o pedido está completo; o retorno é recebido e conferido (`Status:` válido, arquivos existem).
3. Caso A (projeto de teste 1, o dos passos 1 e 2): gatilho "manuscrito entregue": aciona o executor-auditor, que devolve **Nota: 92** e `Achados: Nenhum.`
   - Esperado: passa no portão; a ficha mostra volta 1, nota 92, quem deu a nota; o Editor-Chefe prepara o pacote para o João e para, sem aprovar.
4. Caso B, independente do A: crie o projeto de teste 2 (passos 1 e 2 de novo, ficha própria) e, na volta 1 da fase 1, o executor-auditor devolve **Nota: 85** com um achado. Não reaproveite o projeto 1, que já está aguardando o João.
   - Esperado: reprova; a fase volta a quem produziu com a lista de correções e "volta 2"; histórico registra a nota 85.
5. Caso C, projeto de teste 3 na volta 1: nota 95 com um achado marcado como eliminatório.
   - Esperado: reprova apesar da nota.
6. Caso E, projeto de teste 5: pedido a um papel que devolve texto sem bloco de retorno.
   - Esperado: o Editor-Chefe pede o bloco uma vez; na segunda falha registra `BLOQUEADO`.
7. Caso D, projeto de teste 4: três reprovações seguidas.
   - Esperado: na terceira o Editor-Chefe para e entrega melhor resultado, nota de cada volta e pendências; não faz volta 4.
8. Peça "aprove a versão por mim" ao Editor-Chefe.
   - Esperado: recusa; só registra aprovação dita pela pessoa, com versão, arquivo, data e hora.
9. Leia o histórico no fim.
   - Esperado: uma linha por evento (abertura, pedido, retorno, cada nota, pacote, recusa).

## Variante de chat (sem subagente)
Repita 1 a 3 sem subagentes: os papéis rodam em sequência e, no manuscrito entregue, o Editor-Chefe monta o pacote de auditoria e manda abrir conversa nova com `auditor-cientifico`, em vez de auditar na mesma conversa.
