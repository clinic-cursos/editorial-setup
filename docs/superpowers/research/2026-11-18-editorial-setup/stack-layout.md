# Pesquisa: diagramação, auditoria gráfica e ABNT da Clinic Editora (stack, bloco B)

Data: 2026-11-18. Agente: stack-researcher. Modelo: claude-opus-5-5.

Regras deste documento:
- Toda afirmação factual leva `[Fn]` na linha e uma entrada na Tabela de fontes.
- Padrão de evidência, em ordem: medição própria, documentação oficial datada, página oficial de preço, benchmark reproduzível. Fonte secundária só serve de pista e leva `[secundária]`. Memória do modelo nunca conta como prova.
- Afirmação sem trecho que a sustente sai do texto e vai para "Não sei".
- Todas as opções deste bloco são gratuitas (licenças abertas). Nenhuma tem preço; as colunas de preço ficam como "grátis".

## Pergunta e escopo
B1: que ferramenta compõe um livro A4 de cerca de 80 páginas e roda no Python do ChatGPT, na execução de código do claude.ai e numa VPS. B2 e B4: como auditar o PDF renderizado (sobreposição, corte, duplicação, imagem, DPI efetivo, margens, espaço vazio) e inserir imagem sem mover o texto. B3: quais normas ABNT valem para livro técnico-didático.
Fica de fora: hospedagem e custo da VPS (eixo de infra), análise jurídica de AGPL e direito autoral das normas (eixo de risco), plataformas e skills (bloco A, `stack-platforms.md`).

Repositório da demanda: só `README.md` e o brief; não há `package.json`, lockfile nem ADR em `docs/decisoes/`. A linha de base da casa (Next.js, Node, Postgres, Auth.js, shadcn) não tem ferramenta de composição de livro; o brief já aponta para Python. A "linha de base" deste bloco é, então, o que já vem instalado nos dois sandboxes: python-docx, ReportLab, pypdf e pdfplumber [F1][F3].

## Premissas numéricas
Copiadas do brief.
- Documento: livro A4, cerca de 80 páginas; entrada real é um PDF A4 de 84 páginas já composto, com espaços vazios no fim de várias páginas.
- Usuários: equipe interna (Paula na aprovação editorial); número de livros por mês: não informado no brief.
- Dados: conteúdo de cursos; tipo pessoal ou sensível: não informado no brief.
- Orçamento (BRL/mês): o padrão é grátis; API paga só com preço e alternativa grátis.
- Latência-alvo: não informado no brief.

## Requisitos derivados
| Requisito | Conta | Valor | Limite publicado | Fonte | Folga (limite ÷ valor) |
|---|---|---|---|---|---|
| Arquivo de entrada no claude.ai | PDF de 84 páginas | tamanho não informado | 30 MB por arquivo; PDF maior pode ser processado pelo ambiente de computação | [F4] | depende do tamanho real do PDF |
| RAM do sandbox de código (API do Claude) | renderizar 84 páginas uma a uma | não medido | 5 GiB de RAM, 5 GiB de disco, 1 CPU | [F3] | não medida; ver "Medições" |
| Pacotes fora da lista no sandbox da API do Claude | WeasyPrint, Typst, LaTeX, PyMuPDF | 4 ferramentas | sem internet, só pacotes pré-instalados | [F3] | 0: não rodam lá |
| Pacotes fora da lista no claude.ai (Free, Pro, Max, Ultra) | pip install | 1 por ferramenta | rede ligada, PyPI aprovado | [F4] | possível; dependências de sistema não conferidas |
| Pacotes fora da lista no claude.ai (Enterprise; Team divergente) | pip install | 1 por ferramenta | rede desligada por padrão; dono liga | [F4] | 0 até o dono ligar |
| Página A4 | largura × altura | 210 × 297 mm | Typst `paper: "a4"` = 210,0 × 297,0 mm | [F11] | exato |

## Candidatos

### B1. Composição do livro
Disponibilidade: "API Claude" é a lista oficial do sandbox de execução de código da API [F3]; "claude.ai" é a ferramenta de criar arquivos do app, que não publica lista própria de bibliotecas e permite `pip` quando a rede está ligada [F4]; "ChatGPT" vem de uma lista comunitária de março de 2026, sem lista oficial da OpenAI encontrada [F2, secundária].

| Opção | O que é | Versão e data | Licença | ChatGPT (Python) | API Claude | claude.ai | VPS | Saída editável | Sumário automático | Cabeçalho e rodapé | Fontes próprias | Fontes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| python-docx (linha de base) | gera DOCX | 1.2.0, 2025-06-16 | MIT | listado (1.2.0) [secundária] | sim | sim (via pip ou pré-instalado, ver Não sei) | sim | sim (DOCX abre no Word) | não documentado na página de cabeçalho e rodapé (ver Não sei) | sim, `section.header` e `section.footer` por seção; número de página não tem método documentado | Não sei | [F1][F2][F3][F5][F6][F27] |
| ReportLab (linha de base) | gera PDF por código Python | 5.1.0, 2026-10-22 | BSD | listado (4.4.9) [secundária] | sim, `reportlab[pycairo]` | sim | sim | não (PDF final) | Não sei | Não sei | Não sei | [F2][F3][F7][F8] |
| WeasyPrint | HTML e CSS de impressão para PDF | 70.0, 2026-09-08 | BSD-3-Clause | listado (68.0) [secundária] | não (fora da lista, sem internet) | só com rede ligada; dependências de sistema: Não sei | sim | HTML-fonte editável; PDF final | sim, `target-counter()` e marcadores de `<h1>` a `<h6>` | sim, caixas de margem do `@page` | sim, `@font-face` | [F2][F3][F4][F9][F10][F12] |
| Typst | linguagem de composição própria, compilador em Rust | v0.15.1, 2026-07-17 | Apache-2.0 | ausente da lista [secundária] | não | Não sei (pacote Python não conferido) | sim | fonte `.typ` editável; PDF final | sim, `outline` lista títulos | sim, `header` e `footer` da página; margens `inside`/`outside` para encadernação | Não sei | [F2][F3][F11][F13][F14] |
| LaTeX com abnTeX2 | classe LaTeX para documentos técnicos brasileiros segundo a ABNT | 1.9.7, 2018-11-24 | LPPL 1.3 | não conferido | não (TeX fora da lista) | Não sei | sim (TeX Live e MiKTeX trazem o pacote) | fonte `.tex` editável; PDF final | Não sei (não lido nesta sessão) | Não sei | Não sei | [F3][F15] |
| Paged.js | polyfill JS de mídia paginada no navegador | 0.4.3, 2023-07-06 (beta 0.5.0-beta.2 de 2024-10-04) | MIT | não (Node/navegador; não conferido) | não | não conferido | sim, com navegador headless | HTML-fonte; PDF pelo navegador | Não sei | Não sei | Não sei | [F16][F17] |

Observações por candidato, só com fonte:
- WeasyPrint: a geração de PDF/A e PDF/UA é suportada, mas "os documentos gerados não têm validade garantida" [F12]. Texto da direita para a esquerda não é suportado [F12]. Contadores de página têm "limitações conhecidas" [F12].
- Typst: o padrão de papel já é `"a4"` e as margens têm lados `inside` e `outside` ligados à encadernação [F11]. O `outline` gera a lista de títulos e pode listar figuras [F13].
- abnTeX2: último release em 2018-11-24 [F15]; para normas ABNT de 2023 e 2025 (B3), a classe pode estar desatualizada. Conferir é item de "Não sei".
- Paged.js: a versão estável é de 2023-07-06 e o último beta de 2024-10-04; o registro não mudou desde 2024-10-04 [F17].

### B2. Inspeção do PDF renderizado
| Opção | O que é | Versão e data | Licença | API Claude | ChatGPT | O que expõe (com fonte) | Fontes |
|---|---|---|---|---|---|---|---|
| pdfplumber (linha de base) | extrai cada caractere, retângulo, linha e imagem com posição | 0.11.10, 2026-06-15 | MIT | sim | listado (0.11.9) [secundária] | `.images` com `x0`, `top` e `srcsize` (dimensão original); `to_image(resolution=...)` em pixels por polegada; `dedupe_chars` remove caracteres duplicados; `extract_words` dá palavras com caixa delimitadora; melhor em PDF gerado por máquina, sem OCR | [F2][F3][F18][F19][F20] |
| pypdfium2 + pdf2image (linha de base) | renderizam página para imagem | não conferido | não conferido | sim | pdf2image listado [secundária] | não lido nesta sessão | [F2][F3] |
| PyMuPDF | leitura, renderização e edição de PDF | 2.1, 2026-11-02 | "Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License" | não (fora da lista) | listado (1.26.7) [secundária] | `get_image_info()` devolve `bbox`, `width`, `height`, `xres`, `yres`, `transform`; `get_pixmap(dpi=...)`; `get_drawings()` dá os vetores; `insert_image(rect, keep_proportion=...)` | [F2][F3][F21][F22][F23] |

Métodos de auditoria montados sobre os dados acima (desenho deste relatório, não afirmação de fornecedor; cada um precisa de teste na medição proposta):
- Sobreposição de texto: interseção entre caixas de palavras de linhas diferentes (`extract_words`) [F19].
- Texto cortado: caractere com caixa fora da área da página ou da área útil (margens do manual).
- Parágrafo duplicado: comparar o texto normalizado de blocos consecutivos; `dedupe_chars` cobre só caractere repetido na mesma posição [F19], não parágrafo repetido.
- Imagem distorcida: razão largura/altura de `srcsize` [F19] (ou `width`/`height` [F22]) contra a razão da caixa exibida na página.
- DPI efetivo: `pixels da imagem ÷ (largura exibida em pt ÷ 72)`. Os dados vêm de `srcsize` e `x0`/`x1` no pdfplumber [F19] ou de `width` e `bbox` no PyMuPDF [F22]. `xres`/`yres` do PyMuPDF são metadados gravados no arquivo, não o DPI na página.
- Margens e paginação: menor `x0` e maior `x1`/`bottom` dos objetos de cada página, contra as margens do manual.
- Espaço vazio: ver B4.

### B4. Medir espaço vazio e inserir imagem sem mover o texto
- Medição por objetos: na área útil da página, o espaço livre no fim é a distância entre o maior `bottom` de todos os objetos (caracteres, retângulos, imagens) e a margem inferior [F19]. Pega texto e imagem; vetor desenhado também entra se `rects`/`lines` (pdfplumber) ou `get_drawings()` (PyMuPDF) [F21] forem somados.
- Medição por pixels: renderizar a página (`to_image(resolution=...)` [F19] ou `get_pixmap(dpi=...)` [F22]) e contar linhas de pixels brancos na área útil. Pega tudo o que aparece, inclusive fundo e fio decorativo.
- Inserir sem mover o texto: o PDF já composto não reflui; desenhar a imagem por cima, num retângulo livre, não altera o texto existente. Com PyMuPDF: `insert_image(rect, keep_proportion=True)` [F21]; `show_pdf_page` insere uma página de outro PDF sem rasterizar [F22]. Alternativa sem AGPL (pypdf, já instalado [F3]): gerar uma página com a imagem no ReportLab e carimbá-la sobre a página do livro com `merge_page(..., over=True)` [F26]; a documentação descreve o carimbo como "adicionar algo por cima do documento" [F26]. A licença do pypdf não foi lida nesta sessão.
- Caminho alternativo: recompor o livro (B1) com a imagem no fluxo; aí o texto se move por definição.

### B3. Normas ABNT para livro técnico-didático
| Norma | Assunto | Edição em vigor | Fonte | Confiança |
|---|---|---|---|---|
| ABNT NBR 6029 | Livros e folhetos, apresentação | 2023, terceira edição de 22.03.2023 | [F24] capa da norma; [F25] | alta |
| ABNT NBR 6023 | Referências, elaboração | 2025 | [F25] [secundária: guia universitário de 2026] | média |
| ABNT NBR 10520 | Citações em documentos | 2023 | [F25] [secundária] | média |
| ABNT NBR 6024 | Numeração progressiva das seções | 2012 | [F25] [secundária] | média |
| ABNT NBR 6027 | Sumário | 2012 | [F25] [secundária] | média |
| ABNT NBR 6034 | Índice | 2004 | [F25] [secundária] | média |
| ABNT NBR 6028 | Resumo | 2021 | [F25] [secundária] | média |
| ABNT NBR 12225 | Lombada | 2023 | [F25] [secundária] | média |
| ABNT NBR 14724 | Trabalhos acadêmicos (não se aplica a livro; citada para não confundir) | 2024 | [F25] [secundária] | média |

[F25] é um guia de normalização de 2026 da Editora UniFil, com ISBN, que lista essas edições como "Normas Brasileiras vigentes". A situação de cada uma no catálogo da ABNT não foi lida (o catálogo devolveu 403), por isso a confiança fica média.

## Medições
Nenhuma medição feita: este agente não tem shell. Proposta de medição para quem tiver (VPS ou máquina local), com o PDF de 84 páginas do brief:
1. `pdfplumber`: por página, listar `bottom` máximo dos objetos e a altura livre até a margem inferior; tempo total e pico de RAM.
2. Mesma conta por pixels a 150 DPI com `to_image(resolution=150)`; comparar as duas listas página a página.
3. Repetir 1 e 2 dentro da execução de código do claude.ai e do ChatGPT, registrando `pip list` e o tempo; isso fecha os itens de disponibilidade marcados como secundários ou "Não sei".
4. Para cada imagem: DPI efetivo pela fórmula de B2; marcar abaixo do mínimo do manual da editora (valor não informado no brief).

## Riscos observados
| Risco | Opção | Probabilidade | Impacto | Mitigação | Fonte |
|---|---|---|---|---|---|
| Licença AGPL 3.0 ou licença comercial da Artifex; uso no serviço Python da VPS pode trazer obrigação de abrir código | PyMuPDF | média | alto | usar pdfplumber (MIT) + pypdf + ReportLab (BSD) [F3]; ou análise do eixo de risco antes de adotar | [F23] |
| Ambiente do ChatGPT sem lista oficial; a lista comunitária diz ser "não um contrato estável" | todas no ChatGPT | alta | médio | skill roda `pip list` no início e cai para a opção instalada | [F2] |
| Sandbox da API do Claude sem internet: só pacotes pré-instalados | WeasyPrint, Typst, LaTeX, PyMuPDF | certa | alto para quem depende delas | compor fora (VPS) ou usar ReportLab/python-docx | [F3] |
| Rede desligada por padrão no claude.ai Enterprise (Team com texto divergente) | WeasyPrint, Typst via pip | média | médio | dono da organização liga "package managers" | [F4] |
| abnTeX2 sem release desde 2018-11-24, antes de NBR 6029:2023 e NBR 6023:2025 | LaTeX + abnTeX2 | média | médio | conferir a classe contra as normas de 2023/2025 | [F15][F24][F25] |
| Paged.js sem release estável desde 2023-07-06 | Paged.js | média | médio | preferir WeasyPrint para HTML/CSS de impressão | [F17] |
| PDF/A e PDF/UA do WeasyPrint sem validade garantida | WeasyPrint | média | baixo (só se a gráfica exigir PDF/A) | validar com verificador externo | [F12] |
| pdfplumber não faz OCR; página escaneada não é auditável por texto | pdfplumber | baixa (a entrada é PDF composto) | médio | auditoria por pixels | [F20] |
| Texto das normas ABNT é protegido: "nenhuma parte desta publicação pode ser reproduzida ... sem permissão por escrito da ABNT" | skill que embuta norma | alta se embutir | alto | a skill traz só regras resumidas e referência ao número da norma; a editora compra as normas | [F24] |

## Tabela de fontes
| Id | URL | Acesso | Trecho literal (até 25 palavras) | Tipo | Confiança |
|---|---|---|---|---|---|
| F1 | https://pypi.org/pypi/python-docx/json | 2026-11-18 | "version": "1.2.0", "license": "MIT", "License :: OSI Approved :: MIT License" | oficial | alta |
| F2 | https://gist.github.com/hyle/5c240a6343b7d4f3401e27dc75f72420 | 2026-11-18 | "python-docx==1.2.0", "reportlab==4.4.9", "weasyprint==68.0", "PyMuPDF==1.26.7", "pdfplumber==0.11.9"; ambiente "not a stable contract" | secundária | baixa |
| F3 | https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool | 2026-11-18 | "File processing: ... python-docx, pypdf, pdfplumber, pypdfium2, pdf2image, pdfkit, tabula-py, reportlab[pycairo], Img2pdf"; "The container has 5 GiB of RAM." | oficial | alta |
| F4 | https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude.md | 2026-11-18 | "Network access is enabled, allowing Claude to install packages from approved sources"; "The maximum file size is 30MB per file" | oficial | alta |
| F5 | https://pypi.org/pypi/python-docx/1.2.0/json | 2026-11-18 | python_docx-1.2.0-py3-none-any.whl, upload_time 2025-06-16T20:46:22 | oficial | alta |
| F6 | https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude.md | 2026-11-18 | "Claude can create Excel spreadsheets (.xlsx), PowerPoint presentations (.pptx), Word documents (.docx), and PDF files." | oficial | alta |
| F7 | https://pypi.org/pypi/reportlab/json | 2026-11-18 | "version": "5.1.0"; "BSD license (see license.txt for details), Copyright (c) 2000-2025, ReportLab Inc." | oficial | alta |
| F8 | https://pypi.org/pypi/reportlab/5.1.0/json | 2026-11-18 | reportlab-5.1.0-py3-none-any.whl, upload_time 2026-10-22T07:26:40 | oficial | alta |
| F9 | https://pypi.org/pypi/weasyprint/json | 2026-11-18 | "version": "70.0", "requires_python": ">=3.10"; weasyprint-70.0-py3-none-any.whl upload_time 2026-09-08T12:25:39 | oficial | alta |
| F10 | https://api.github.com/repos/Kozea/WeasyPrint/license | 2026-11-18 | "spdx_id": "BSD-3-Clause" | oficial | alta |
| F11 | https://typst.app/docs/reference/layout/page/ | 2026-11-18 | "The page's header. Fills the top margin of each page."; "a4": "210.0 × 297.0 millimeters"; inside: "The margin at the inner side" | oficial | alta |
| F12 | https://doc.courtbouillon.org/weasyprint/stable/api_reference.html | 2026-11-18 | "target-counter() and target-text() are useful when it comes to tables of contents."; "WeasyPrint supports the @font-face rule." | oficial | alta |
| F13 | https://typst.app/docs/reference/model/outline/ | 2026-11-18 | "A table of contents, figures, or other elements." "generates a list of all occurrences of an element in the document, up to a given depth." | oficial | alta |
| F14 | https://api.github.com/repos/typst/typst/releases/latest e /license | 2026-11-18 | "tag_name": "v0.15.1", "published_at": "2026-07-17T11:12:06Z"; "spdx_id": "Apache-2.0" | oficial | alta |
| F15 | https://ctan.org/pkg/abntex2 | 2026-11-18 | "1.9.7 2018-11-24"; "The LaTeX Project Public License 1.3"; "Typeset technical and scientific Brazilian documents based on ABNT rules"; "TeX Live as abntex2" | oficial | alta |
| F16 | https://registry.npmjs.org/pagedjs/latest | 2026-11-18 | "version": "0.4.3", "license": "MIT", "Chunks up a document into paged media flows and applies print styles" | oficial | alta |
| F17 | https://registry.npmjs.org/pagedjs (offset 200000) | 2026-11-18 | "0.4.3": "2023-07-06T15:56:38.255Z"; "0.5.0-beta.2": "2024-10-04T17:33:41.242Z"; "modified": "2024-10-04T17:33:41.453Z" | oficial | alta |
| F18 | https://pypi.org/pypi/pdfplumber/json e /0.11.10/json | 2026-11-18 | "version": "0.11.10"; "License :: OSI Approved :: MIT License"; upload_time 2026-06-15T03:31:29 | oficial | alta |
| F19 | https://raw.githubusercontent.com/jsvine/pdfplumber/stable/README.md | 2026-11-18 | srcsize: "The image original dimensions, as a (width, height) tuple."; resolution: "The desired number pixels per inch. Default: 72." | oficial | alta |
| F20 | https://raw.githubusercontent.com/jsvine/pdfplumber/stable/README.md | 2026-11-18 | "Works best on machine-generated, rather than scanned, PDFs."; não oferece "Optical character recognition (OCR)" | oficial | alta |
| F21 | https://pymupdf.readthedocs.io/en/latest/page.html | 2026-11-18 | keep_proportion: "maintain the aspect ratio of the image."; rect: "where to put the image. Must be finite and not empty."; get_drawings: "get vector graphics on page." | oficial | alta |
| F22 | https://pymupdf.readthedocs.io/en/latest/page.html (offset 100000) | 2026-11-18 | bbox "image bbox on page"; transform "transforming image rect to bbox"; dpi "desired resolution in x and y direction"; show_pdf_page "will not be rasterized" | oficial | alta |
| F23 | https://pypi.org/pypi/PyMuPDF/json e /2.1/json | 2026-11-18 | "version": "2.1"; "Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License"; upload_time 2026-11-02T17:15:19 | oficial | alta |
| F24 | https://www.ufsm.br/app/uploads/sites/566/2026/05/ABNT-6029-2023.pdf | 2026-11-18 | "ABNT NBR 6029 Terceira edição 22.03.2023 Informação e documentação — Livros e folhetos — Apresentação"; "nenhuma parte desta publicação pode ser reproduzida" | oficial (cópia da norma) | alta |
| F25 | https://unifil.br/assets/uploads/2026/04/Ebook-ABNT-2026.pdf | 2026-11-18 | "Normas Brasileiras vigentes: NBR 6023 / 2025 ... NBR 6024 / 2012 ... NBR 6027 / 2012 ... NBR 6034 / 2004 ... NBR 10520 / 2023" | secundária | média |
| F26 | https://pypdf.readthedocs.io/en/stable/user/add-watermark.html | 2026-11-18 | "set `over` parameter to `True` for stamping"; carimbo é "adding something on top of the document" | oficial | alta |
| F27 | https://python-docx.readthedocs.io/en/latest/user/hdrftr.html | 2026-11-18 | "Each section object has a `.header` property providing access to a `_Header` object for that section" | oficial | alta |

## Não sei
| Pergunta | O que foi tentado (URL e erro, busca feita) | Como resolver (medição, pergunta ao fornecedor, eixo responsável) |
|---|---|---|
| Lista oficial de bibliotecas do Python do ChatGPT | help.openai.com/en/articles/8437071 deu 403; busca não achou lista oficial; só a lista comunitária [F2] | rodar `pip list` numa conversa do plano em uso e anexar ao relatório (medição 3) |
| O ChatGPT instala pacote com `pip` (internet no sandbox)? | sem fonte oficial lida | testar `pip install weasyprint` na conversa; bloco A pode ter a resposta |
| Lista de bibliotecas pré-instaladas do claude.ai (app), distinta da API | o artigo [F4] diz só "common code packages" | `pip list` numa conversa do claude.ai |
| WeasyPrint instala e roda no claude.ai via pip (depende de bibliotecas de sistema, como Pango)? | dependências de sistema não lidas nesta sessão | ler a página de instalação do WeasyPrint e testar na conversa |
| Typst por pacote Python (PyPI) e se roda nos sandboxes | não pesquisado (teto de chamadas) | `pypi.org/pypi/typst/json` e teste na conversa |
| python-docx: sumário automático (campo TOC), número de página, primeira página e páginas pares/ímpares diferentes, fontes próprias | a página de cabeçalho e rodapé [F27] não trata desses pontos | ler a API de `Section` e de estilos do python-docx; testar gerando um DOCX com campo TOC e abrir no Word |
| pypdf: licença e se `merge_page` preserva o conteúdo de baixo | só a página de marca d'água [F26] lida | `pypi.org/pypi/pypdf/json` e teste com 1 página |
| ReportLab: sumário (`TableOfContents`), cabeçalho e rodapé, fontes TTF | doc não lida nesta sessão | ler o guia do usuário do ReportLab (Platypus) |
| abnTeX2 e LaTeX: sumário, cabeçalho e fontes; aderência às normas de 2023 e 2025 | só a página do CTAN [F15] foi lida | ler a documentação do abnTeX2 e comparar com NBR 6029:2023 |
| Paged.js: recursos (sumário, margens) e como roda sem navegador | só o registro npm lido | ler pagedjs.org/documentation |
| pypdfium2 e pdf2image: versão e licença | não lido | `pypi.org/pypi/pypdfium2/json` e `pypi.org/pypi/pdf2image/json` |
| Situação "em vigor" de cada norma no catálogo da ABNT (só NBR 6029:2023 foi lida na capa) | normas.com.br deu 403; guia UniFil de 2026 [F25] é secundário | consulta no catálogo da ABNT (abntcatalogo.com.br) ou pela bibliotecária; NBR 6023:2025 vale conferir a capa |
| Obrigações da AGPL no serviço da VPS | fora deste eixo | eixo de risco (`risk-researcher`) |
| DPI mínimo e margens do manual técnico da editora | não está no brief | perguntar à Paula ou anexar o manual |
| Tamanho em MB do PDF de 84 páginas (limite de 30 MB do claude.ai) | não informado | medir o arquivo real |
