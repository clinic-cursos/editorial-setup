# Relatório de auditoria científica

Versão do manuscrito auditada: <arquivo e versão>
Data: AAAA-MM-DD
Ambiente: <Claude Code, Codex ou chat>, com ou sem rede. `verify_refs.py`: <rodou, rodou com --offline ou não rodou, e por quê>.

## Resumo
Nota: <0 a 100>. Resultado: <passa ou reprova>. Eliminatórios: <nenhum ou lista>.

## Nota pela rubrica da fase 1
Rubrica usada: <a do pacote, ou esta cópia (data da cópia: 2026-11-19), se a do pacote faltou>. Cópia de `fase-1-ampliacao.md` de 2026-11-19; um teste a compara com a oficial. Pesos iniciais, a ajustar com a Paula.

| Critério | Peso | O que conta | Pontos | Justificativa |
| --- | --- | --- | --- | --- |
| Fidelidade aos slides e à apostila | 25 | Todo slide tem correspondente no manuscrito (tabela slide a capítulo sem órfão); sequência didática preservada | | |
| Rastreabilidade | 25 | Toda afirmação nova com fonte verificável (DOI ou PMID quando houver), na tabela de rastreabilidade | | |
| Correção científica conferida pelo auditor | 20 | Afirmações conferidas contra a fonte; juízo registrado como juízo, não como fato | | |
| Clareza didática | 15 | Texto compreensível ao aluno, blocos editoriais usados com função | | |
| Terminologia e padronização | 15 | Termos do glossário e do Board, siglas e unidades padronizadas | | |

Soma dos pontos: <igual à nota>.

| Eliminatório | Avaliado | Achado |
| --- | --- | --- |
| Referência que não existe | [sim ou não] | <nenhum ou número do achado; só vale se todas as consultas, inclusive a busca pelo título citado quando o DOI ou PMID dá `not-found` ou `divergent` por título, deram `not-found` definitivo; com qualquer `unverified`, a referência fica `não verificada`, sem eliminatório> |
| Conteúdo de slide ausente sem justificativa | [sim ou não] | |
| Divergência com o Board não sinalizada | [sim ou não] | |

## Conferido
Só fatos verificáveis: metadados, resultado do `verify_refs.py` e trechos consultados. Sustentar ou não a afirmação é juízo e fica na seção abaixo.

| Referência ou trecho | Como foi conferido | Resultado (`ok`, `divergent`, `not-found`, trecho localizado) | Evidência |
| --- | --- | --- | --- |

## Referências não verificadas
Entram aqui as `unverified` (sem rede, sem DOI nem PMID, resposta malformada). Vão para a conferência humana do João e perdem os pontos de rastreabilidade.

| Chave | Motivo | O que o João precisa conferir |
| --- | --- | --- |

## Não conformidades
Uma por item, numeradas.

### N1. <título curto>
- **Tipo:** referência inexistente, identificador errado (não eliminatório), metadado divergente, afirmação sem suporte, extrapolação, divergência com o Board, slide órfão, informação regulatória a atualizar, terminologia, outro.
- **Eliminatório:** sim ou não.
- **Localização:** <capítulo, seção, slide ou linha da tabela>.
- **Evidência:** <o que a fonte ou o original diz, com a localização>.
- **Recomendação:** <o que o Editor Científico deve fazer>.

## Juízo do auditor
Por afirmação, um destes resultados: `sustentada`, `sem suporte suficiente` (ambos só com o trecho lido, evidência citada) ou `não verificada` (trecho inacessível, com o motivo; vai para a conferência humana e não conta como conferida). Também afirmações do manuscrito sem entrada na tabela (cada uma é não conformidade). Interpretações que não são fato conferido: suficiência da evidência, extrapolações, risco clínico, informação regulatória possivelmente desatualizada. Cada item diz o que o auditor viu, por que julga assim e o que o João deve decidir.

## Divergências com o Board para o João
| Localização | Posição do Board | Evidência contrária e limitação | Decisão pedida |
| --- | --- | --- | --- |
