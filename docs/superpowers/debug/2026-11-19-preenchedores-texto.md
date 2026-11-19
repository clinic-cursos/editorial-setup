# Diagnóstico B (debugger, 19/11/2026): texto do Preenchedores

Testes que falham hoje (não rastreados, na worktree dbg-b):
- /var/tmp/editorial-wt/dbg-b/tests/test_toc_mismatch_extracted.py (4 testes)
- /var/tmp/editorial-wt/dbg-b/tests/test_fidelity_extracted_order.py (3 testes)
Scripts dos protótipos: /var/tmp/dbg-b-work/edits/h1.py a h5.py

## toc-mismatch (13 erros), duas causas provadas
- h1 (6 erros): extract_pdf.py, laço de render() (~linha 146), copia a página do sumário do original para o corpo. Correção: detectar página cujo primeiro texto do corpo é "Sumário" (regex TOC_TITLE igual ao do check_toc), pular com aviso; text_fidelity._pdf_text descarta a mesma página do original só fora do modo template (no template o filtro desloca capa/expediente/sumário do modelo e derruba a razão para 0,8694). Capa e expediente ficam (run_sample.fill_metadata depende deles). Atalho: sumário de continuação sem título não é descartado.
- h2 (7 erros, falsos positivos): lib/pdfcheck/checks.py check_toc (~250-252) registra título do corpo linha a linha; título quebrado em 2 linhas ou terminado em ponto não casa. Correção: juntar até 3 linhas consecutivas e tirar " .·…" do fim, como já faz na entrada. check_layout.py importa a CÓPIA em skills/*/scripts/pdfcheck: rodar package.py --sync.

## Fidelidade 0,9028 / 0,9038 (108 linhas): quase tudo é medição
Multiconjunto: só 10 tokens perdidos de verdade (7 = "Referências bibliográficas" x4 virando um "## Referências"; 3 = anos).
- h3 (103 linhas, 3.496 car.): text_fidelity._pdf_pages (47-52) lê a página inteira linha a linha e mistura as 2 colunas; extract_pdf lê coluna a coluna (certo). Correção: usar gutter() do extract_pdf e ler coluna a coluna. Risco: medidor perde independência do vão.
- h4 (5 linhas, 5.828 car.): referências movidas para o fim (exigido pela convenção) contadas como perdidas e como "número alterado". Correção: 2ª passada que casa bloco movido de >= 8 palavras. DECISÃO DO ORQUESTRADOR: tolerância a bloco movido só na comparação fonte -> manuscrito; nas comparações manuscrito -> PDF composto (v1, v2) a ordem continua conferida. Bloco movido é listado como "trecho movido" no stderr, sem reprovar.
- h5 (3 anos perdidos, dado real): extract_pdf.py:17 LIST_ITEM com (\d+) sem limite lê "2024. " como marcador de lista; nas referências corta o ano e abre entrada nova. Correção: (\d{1,3}).
- h3+h4 juntas no livro real: 0,9965 / 0,9976. h1 a h5: 0,9960 / 0,9969, 13 linhas restantes a conferir.

## Defeitos vistos de passagem (fora das 108 linhas)
- referências: linha de URL vira entrada própria (25 chaves [@https-N]); linha "PMID/PMCID" e a introdução "Fontes do aprofundamento..." também.
- rodapé "CLINIC EDITORA" entra como referência.
- 2 URLs quebradas no meio ficam com espaço dentro.
- cabeçalho corrido "01 / FUNDAMENTOS" vira ### repetido.
- in_references só fecha em # ou ##: título de capítulo na faixa do cabeçalho faz o corpo virar referência (visto em PDF sintético).
