# Ensaio científico (cartão 4.4, critério 6 da spec)

Resultado: APROVADO, com ressalvas para o João.

Rodada feita pela sessão de execução em 19/11/2026, depois do merge do cartão 4.4 na `feat/wave-4`. Os testes automáticos (`tests/test_science_sample.py`) cobrem o material sem rede; esta rodada usou rede de verdade.

## Material

`tests/samples/capitulo-teste/`: 8 slides sintéticos (fonte A), manuscrito sintético 1.0, tabela slide a capítulo e `referencias.json` com uma referência inventada plantada (`inventado2099`, DOI 10.9999/planted.2024.0001).

## Como foi rodado

- Claude Code, dois agentes separados, cada um seguindo o arquivo do papel em `agents/editorial/` e a skill dele.
- Editor Científico em Opus: revisar e ampliar o capítulo como pedido real, com rede, sem inventar referência e sem mudar decisão do Board em silêncio.
- Auditor Científico em Sonnet, em contexto novo: auditar a entrega do Editor pela rubrica da fase 1, com o `verify_refs.py` e leitura das fontes.
- As saídas ficaram fora do repositório (`/var/tmp/editorial-ensaio-cientifico/`), por serem de um ensaio.

## Editor Científico

| Esperado | Obtido | Passou |
| --- | --- | --- |
| Os 8 slides na tabela slide a capítulo, sem órfão | 8 slides, na ordem, sem órfão | sim |
| Nenhuma referência inventada no manuscrito | `inventado2099` achada (404 no Crossref, 0 no PubMed, nada no OpenAlex) e retirada do texto e da lista | sim |
| Referências conferidas com rede | 6 de 6 conferidas (DOI e PMID); 3 lidas no texto completo, 3 só no resumo | sim |
| Decisão do Board mudada em silêncio | nenhuma; uma divergência (slide 7 contra a Recommendation 1 do CDC 2022) encaminhada ao João | sim |

Entregou plano de ampliação, manuscrito 1.1, tabela slide a capítulo e rastreabilidade com 20 afirmações novas, todas com trecho da fonte. Status `PRONTO_COM_RESSALVAS`, com 11 pendências (P1 a P11) para o Board e o João.

## Auditor Científico

| Esperado | Obtido | Passou |
| --- | --- | --- |
| `verify_refs.py` marca `inventado2099` como `not-found` | `not-found`, saída 1, com a entrada do `referencias.json` | sim |
| Relatório separa "conferido" de "juízo do auditor" | separado, no modelo da skill | sim |
| Nota pela rubrica da fase 1, com os eliminatórios um a um | 92 (fidelidade 25, rastreabilidade 23, correção científica 18, clareza didática 13, terminologia 13); nenhum eliminatório | sim |
| Cada afirmação cruzada com a fonte | 22 de 22 cruzadas com o trecho, todas `sustentada` | sim |

Achados do auditor: 8 não conformidades sem eliminatório (pergunta de estudo sem resposta no texto, localização anatômica sem apoio na fonte, bloco de evidência lido só no resumo, vigência do CDC e da IASP não conferida por HTTP 403, extrapolação leve, convenção de siglas, três localizadores errados na rastreabilidade, `referencias.json` 1.0 desatualizado).

## Achados para o setup

- Referência sem DOI nem PMID: o `verify_refs.py` dá só `unverified` (saída 0). O auditor pegaria `inventado2099` pela busca por título e pelo ano 2099, mas isso depende do agente, não do script. Melhoria candidata: o script buscar pelo título quando não há identificador e acusar ano no futuro.
- Sites de diretriz (cdc.gov, iasp-pain.org) e o texto completo de uma revista responderam HTTP 403 ao agente: a vigência de diretriz fica para conferência humana, como a skill já prevê.
