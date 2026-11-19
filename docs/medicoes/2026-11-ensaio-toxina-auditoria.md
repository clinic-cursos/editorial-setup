# Ensaio do Auditor Gráfico no PDF de Toxina

Rodada local de 19/11/2026 para o critério 6a da spec. A entrada foi o PDF original `Toxina_Botulinica_Miolo_Alta_Resolucao.pdf`, com 80 páginas, lido de `EDITORIAL_SAMPLES_DIR`.

## Reprodução

Na raiz do repositório, com `EDITORIAL_SAMPLES_DIR` definido:

```sh
out_dir=$(mktemp -d)
uv run --locked python skills/auditor-grafico/scripts/audit_pdf.py \
  "$EDITORIAL_SAMPLES_DIR/Toxina_Botulinica_Miolo_Alta_Resolucao.pdf" \
  --json "$out_dir/auditoria.json" --md "$out_dir/auditoria.md"
```

A rodada usa as regras gráficas padrão. Sem `origem.json`, a checagem aplica os limites de resolução de imagem sem origem documentada: erro abaixo de 150 ppi e aviso de 150 até abaixo de 300 ppi. Os relatórios completos ficam fora do repositório.

## Resultado

A CLI terminou com código 1 em 381,05 s. Foram 336 erros e 32 avisos automáticos. As contagens são de achados, e a numeração abaixo é a página física do PDF, a partir de 1.

| Tipo | Erros | Avisos |
| --- | ---: | ---: |
| `overlap` | 240 | 0 |
| `outside-safe-zone` | 7 | 0 |
| `duplicate-paragraph` | 16 | 0 |
| `font-not-allowed` | 45 | 0 |
| `font-unnamed` | 0 | 0 |
| `page-without-text` | 0 | 3 |
| `page-size` | 0 | 0 |
| `image-low-resolution` | 5 | 29 |
| `image-distorted` | 14 | 0 |
| `page-number` | 1 | 0 |
| `toc-mismatch` | 8 | 0 |

- **Sobreposição.** 62 páginas sinalizadas: 4, 9 a 12, 14 a 17, 19 a 25, 28 a 31, 34 a 46, 48 a 51, 53 a 55, 57 a 66 e 68 a 79.
- **Repetição na própria página.** Páginas 4, 30, 42, 43, 58, 62, 64, 69 e 78.
- **Repetição entre páginas.** Nas páginas 34, 35 e 36, com origem na 33. Na 52, com origem na 47. Na 56, com origem nas páginas 47 e 52. Na 79, com origem na 64.
- **Resolução.** Erros nas páginas 42 e 50. Avisos nas páginas 11, 12, 14, 15, 18 a 22, 30, 32, 38, 54, 67 e 69. As contagens de imagem por faixa também coincidiram com as de `pdfimages -list`.
- **Sem camada de texto.** Páginas 1, 2 e 80.

## Conferência visual a 150 ppi

Renderizei com `pdftoppm -f N -l N -r 150 -png` e abri cada imagem. A amostra inclui as páginas 4, 34 e 36 e as cinco com mais achados de sobreposição ou repetição (30, 36, 63, 42 e 66). Incluí também 38 e 69, que empatam na quinta posição se a contagem considerar todos os tipos, e a página 33 para comparar as repetições de 34 e 36. As imagens de trabalho ficaram em diretório privado em `/tmp`, pois a sandbox bloqueou a gravação em `/var/tmp`.

Para a sobreposição, a localização é a caixa `(x0, topo, x1, base)` em pontos, arredondada, com origem no canto superior esquerdo. Para a repetição, confrontei as posições dos trechos extraídos com as linhas visíveis. Cada linha da tabela corresponde a um achado de sobreposição ou repetição nas páginas selecionadas.

| Página | Tipo | Real ou falso | Motivo |
| --- | --- | --- | --- |
| 4 | Sobreposição (54, 344, 518, 517) | Falso positivo | A nota editorial visível tem linhas separadas e legíveis nessa faixa. |
| 4 | Repetição | Falso positivo | Os pares de linhas extraídos de duas posições na nota editorial aparecem uma vez na imagem. |
| 30 | Sobreposição (44, 64, 74, 120) | Falso positivo | O rótulo da seção e o título têm espaço entre si. |
| 30 | Sobreposição (45, 175, 159, 255) | Falso positivo | O bloco superior esquerdo tem linhas separadas. |
| 30 | Sobreposição (378, 259, 529, 366) | Falso positivo | O texto no topo da coluna direita e o destaque logo abaixo estão legíveis. |
| 30 | Sobreposição (54, 336, 183, 363) | Falso positivo | As últimas linhas do bloco superior esquerdo estão separadas. |
| 30 | Sobreposição (284, 424, 476, 449) | Falso positivo | O subtítulo ocupa uma linha legível no lado direito. |
| 30 | Sobreposição (59, 424, 250, 449) | Falso positivo | O subtítulo e sua quebra de linha estão separados no lado esquerdo. |
| 30 | Sobreposição (54, 552, 120, 562) | Falso positivo | O intertítulo da lista aparece sozinho e legível. |
| 30 | Sobreposição (54, 586, 152, 598) | Falso positivo | O início da lista numerada está legível. |
| 30 | Sobreposição (54, 620, 254, 768) | Falso positivo | A lista e o exemplo abaixo têm linhas separadas. |
| 30 | Sobreposição (54, 798, 65, 812) | Falso positivo | A caixa incide no rodapé e o fólio aparece uma vez e legível. |
| 30 | Sobreposição (53, 844, 249, 920) | Falso positivo | A caixa inteira está abaixo do limite visível de 841,89 pt. |
| 30 | Sobreposição (54, 978, 248, 1036) | Falso positivo | A caixa inteira está abaixo do limite visível de 841,89 pt. |
| 30 | Sobreposição (48, 1066, 247, 1235) | Falso positivo | A caixa inteira está abaixo do limite visível de 841,89 pt. |
| 30 | Sobreposição (284, 844, 533, 1238) | Falso positivo | A caixa inteira está abaixo do limite visível de 841,89 pt. |
| 30 | Sobreposição (47, 1260, 251, 1311) | Falso positivo | A caixa inteira está abaixo do limite visível de 841,89 pt. |
| 30 | Repetição | Falso positivo | As ocorrências extraídas incluem cópias deslocadas 522 pt para baixo. Os trechos comparados não aparecem duas vezes na imagem, e parte das caixas excede a área visível. |
| 34 | Sobreposição (299, 112, 527, 722) | Falso positivo | Os parágrafos da coluna direita têm linhas distintas e legíveis. |
| 34 | Sobreposição (54, 110, 282, 734) | Falso positivo | Os parágrafos e intertítulos da coluna esquerda estão separados. |
| 34 | Repetição | Falso positivo | A sequência repetida com a página 33 está no cabeçalho corrido e no título de seção. O texto corrido visível é distinto. |
| 36 | Sobreposição (299, 112, 511, 170) | Falso positivo | As primeiras entradas da coluna direita estão separadas. |
| 36 | Sobreposição (54, 110, 282, 174) | Falso positivo | O intertítulo e o primeiro parágrafo da coluna esquerda estão separados. |
| 36 | Sobreposição (299, 206, 317, 218) | Falso positivo | O início da nota da coluna direita está legível. |
| 36 | Sobreposição (377, 206, 476, 218) | Falso positivo | A primeira linha da nota da coluna direita está legível. |
| 36 | Sobreposição (62, 235, 88, 248) | Falso positivo | A entrada da coluna esquerda tem caracteres separados. |
| 36 | Sobreposição (377, 235, 482, 296) | Falso positivo | As linhas da nota e do parágrafo seguinte são legíveis. |
| 36 | Sobreposição (60, 326, 88, 339) | Falso positivo | A entrada correspondente da coluna esquerda está legível. |
| 36 | Sobreposição (220, 326, 273, 339) | Falso positivo | O fim da linha da coluna esquerda está legível. |
| 36 | Sobreposição (375, 326, 445, 366) | Falso positivo | O intertítulo e o texto seguinte da coluna direita estão separados. |
| 36 | Sobreposição (299, 350, 354, 411) | Falso positivo | A margem interna da coluna direita está livre de colisões visíveis. |
| 36 | Sobreposição (375, 400, 477, 426) | Falso positivo | As linhas da síntese na coluna direita estão separadas. |
| 36 | Sobreposição (61, 443, 94, 454) | Falso positivo | A última linha da coluna esquerda está legível. |
| 36 | Sobreposição (296, 444, 330, 455) | Falso positivo | O início das últimas linhas da coluna direita está legível. |
| 36 | Sobreposição (375, 444, 503, 469) | Falso positivo | O fim do texto da coluna direita tem linhas distintas. |
| 36 | Repetição | Falso positivo | A sequência repetida com a página 33 foi extraída da faixa do cabeçalho e do título corrido. Na página 36 só o cabeçalho aparece nessa faixa. |
| 38 | Sobreposição (299, 447, 364, 506) | Falso positivo | O início do texto abaixo das figuras na coluna direita está legível. |
| 38 | Sobreposição (54, 447, 282, 512) | Falso positivo | O parágrafo abaixo das figuras na coluna esquerda tem linhas distintas. |
| 42 | Sobreposição (446, 29, 527, 41) | Falso positivo | O cabeçalho direito é legível e aparece uma vez. |
| 42 | Sobreposição (54, 64, 91, 74) | Falso positivo | O rótulo de seção aparece uma vez, longe do cabeçalho. |
| 42 | Sobreposição (50, 98, 345, 130) | Falso positivo | O título é legível, com espaço acima e abaixo. |
| 42 | Sobreposição (128, 149, 307, 220) | Falso positivo | Os itens da lista superior têm linhas separadas. |
| 42 | Sobreposição (51, 361, 240, 391) | Falso positivo | A figura e a primeira linha da coluna esquerda estão separadas. |
| 42 | Sobreposição (259, 351, 527, 431) | Falso positivo | A figura e o bloco de texto da direita estão separados. |
| 42 | Sobreposição (54, 412, 228, 439) | Falso positivo | As linhas de texto da coluna esquerda estão separadas. |
| 42 | Repetição | Falso positivo | A extração traz duas ocorrências, uma com coordenada horizontal negativa. O corpo de texto aparece uma vez abaixo da figura. |
| 63 | Sobreposição (313, 151, 541, 290) | Falso positivo | A primeira pergunta e sua resposta na coluna direita estão separadas. |
| 63 | Sobreposição (68, 151, 296, 302) | Falso positivo | Os dois primeiros blocos da coluna esquerda têm linhas distintas. |
| 63 | Sobreposição (313, 307, 541, 335) | Falso positivo | A pergunta seguinte na coluna direita tem duas linhas legíveis. |
| 63 | Sobreposição (68, 321, 189, 352) | Falso positivo | A segunda resposta da coluna esquerda está legível. |
| 63 | Sobreposição (68, 379, 187, 394) | Falso positivo | A pergunta da coluna esquerda está legível. |
| 63 | Sobreposição (68, 411, 296, 440) | Falso positivo | A resposta correspondente da coluna esquerda tem linhas distintas. |
| 63 | Sobreposição (68, 459, 278, 473) | Falso positivo | A pergunta seguinte da coluna esquerda está legível. |
| 63 | Sobreposição (313, 351, 541, 474) | Falso positivo | A resposta e a pergunta seguinte da coluna direita estão separadas. |
| 63 | Sobreposição (313, 493, 541, 585) | Falso positivo | As linhas da resposta na coluna direita estão separadas. |
| 63 | Sobreposição (68, 489, 296, 601) | Falso positivo | Os blocos inferiores da coluna esquerda mantêm espaço entre linhas. |
| 63 | Sobreposição (313, 601, 541, 614) | Falso positivo | A pergunta inferior direita é legível e está separada da resposta. |
| 66 | Sobreposição (54, 162, 270, 191) | Falso positivo | A primeira referência da coluna esquerda tem linhas distintas. |
| 66 | Sobreposição (299, 150, 525, 228) | Falso positivo | A primeira referência da coluna direita tem linhas distintas. |
| 66 | Sobreposição (54, 209, 269, 236) | Falso positivo | A referência seguinte da coluna esquerda está legível. |
| 66 | Sobreposição (299, 254, 527, 310) | Falso positivo | A segunda referência da coluna direita está legível. |
| 66 | Sobreposição (54, 253, 257, 314) | Falso positivo | A terceira referência da coluna esquerda tem linhas separadas. |
| 66 | Sobreposição (54, 340, 268, 386) | Falso positivo | A referência do meio da coluna esquerda é legível. |
| 66 | Sobreposição (299, 328, 523, 414) | Falso positivo | Os registros do meio da coluna direita são legíveis. |
| 66 | Sobreposição (54, 401, 190, 471) | Falso positivo | As referências da parte inferior esquerda mantêm espaço entre linhas. |
| 69 | Sobreposição (61, 138, 348, 153) | Falso positivo | O primeiro parágrafo abaixo do título tem linhas separadas. |
| 69 | Sobreposição (66, 174, 539, 205) | Falso positivo | O segundo parágrafo tem linhas separadas. |
| 69 | Sobreposição (60, 226, 454, 263) | Falso positivo | O terceiro parágrafo e a chamada em bordô estão separados. |
| 69 | Sobreposição (470, 242, 489, 263) | Falso positivo | O fim da linha e a chamada abaixo estão separados. |
| 69 | Sobreposição (313, 448, 541, 500) | Falso positivo | As linhas da coluna direita abaixo da ilustração estão separadas. |
| 69 | Sobreposição (68, 448, 296, 529) | Falso positivo | As linhas da coluna esquerda abaixo da ilustração estão separadas. |
| 69 | Repetição | Falso positivo | A extração traz cópias dos parágrafos iniciais deslocadas para cima, com caixas que excedem a área visível na horizontal. Os parágrafos aparecem uma vez na imagem. |

**Critério 6a: não demonstrado.** Os 66 alertas de sobreposição e os 6 de repetição da amostra foram falsos positivos em relação ao PDF renderizado. A checagem de resolução produziu 29 avisos, corroborados por `pdfimages -list`. Nas demais páginas, a condição visual dos alertas segue sem verificação. O ensaio não atribui nota editorial.
