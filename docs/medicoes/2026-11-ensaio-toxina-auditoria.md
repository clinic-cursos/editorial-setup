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

A conferência visual por amostragem nas páginas 4, 34 e 36 não confirmou as sobreposições apontadas nessas páginas. Na página 4, a repetição automática também ficou sem confirmação visual. A detecção usa a camada de texto, e os achados precisam de validação visual antes de serem tratados como defeitos de impressão. O ensaio mede a checagem técnica do original. A nota editorial fica para uma auditoria completa.
