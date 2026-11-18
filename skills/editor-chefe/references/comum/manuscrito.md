# Formato do manuscrito

O manuscrito usa somente as construções a seguir.

- Abra o arquivo com os quatro campos de metadados do exemplo, um por linha. Separe os nomes dos autores com vírgula e deixe uma linha em branco após `version`.
- Use títulos de nível 1 a 3 (`#`, `##` e `###`), parágrafos separados por uma linha em branco e listas com `-` ou numeração iniciada em `1.`.
- Abra cada bloco editorial com seu identificador sozinho em uma linha e feche com `:::` sozinho em outra linha. Os identificadores são `:::ponto-chave`, `:::atencao`, `:::evidencia`, `:::estudo-pratica`, `:::aprofundamento`, `:::aplicacao-clinica` e `:::faq`.
- Coloque `<!-- slide: N -->` em uma linha antes do trecho correspondente, com `N` igual ao número do slide de origem.
- Cite com `[@chave]` e encerre o manuscrito com `## Referências`. Use uma entrada `- [@chave] Dados bibliográficos` por fonte e faça cada citação corresponder a uma entrada da lista.
- Insira figuras em uma linha com `![legenda](arquivo){#fig-id}`. Use um caminho relativo ao manuscrito e um identificador único por figura com prefixo `fig-`.

```text
title: Exemplo de manuscrito
course: Curso de demonstração
authors: Ana Silva, Rui Costa
version: 1.0

# Capítulo de exemplo

## Objetivo

<!-- slide: 12 -->
Parágrafo introdutório com uma citação [@exemplo].

### Atividade

- Material de leitura.

1. Leia o material.
2. Anote as dúvidas.

:::ponto-chave
Síntese da seção.
:::

![Esquema de exemplo](imagens/esquema.png){#fig-esquema}

## Referências

- [@exemplo] Dados bibliográficos da fonte citada.
```
