# Setup editorial de IA da Clinic Editora, V1: desenho

Data: 2026-11-18. Sessão de decisão do Alify. Aprovação: o Alify escolheu a forma A ("skills como fonte única, empacotadas para cada plataforma") e pediu a construção em 18/11/2026 ("Pode criar esse repo do setup editorial, com os agentes e tudo mais").

Fontes: [instrução da Paula](../../fontes/2026-11-18-instrucao-paula.md) (prevalece), [briefing do Bruno](../../fontes/2026-11-16-briefing-bruno.md), pesquisa em [`../research/2026-11-18-editorial-setup/`](../research/2026-11-18-editorial-setup/) ([plataformas](../research/2026-11-18-editorial-setup/stack-platforms.md) e [diagramação e ABNT](../research/2026-11-18-editorial-setup/stack-layout.md)).

## 1. Intenção
A Clinic Editora transforma slides e apostilas dos cursos em livros A4 de cerca de 80 páginas, entregues aos alunos. Hoje a Paula faz isso à mão no ChatGPT, fase por fase, com o manual técnico da editora; ela e o João gastam tempo em trabalho operacional que agentes podem antecipar, organizar e filtrar.

A V1 é um time de agentes empacotado como skills, para a equipe interna usar já no ChatGPT, e também no Codex e no Claude. Cada papel segue regras fixas, entrega um artefato verificável e passa por nota antes de chegar a uma pessoa. Depois, o mesmo time roda no `agent-service` da VPS, reaproveitando estas skills como fonte única dos prompts (combinado com a sessão do ADR do orquestrador em 18/11/2026).

Sucesso: a Paula manda um pedido como o de hoje e recebe o livro diagramado conforme o manual, com as imagens complementares no lugar, sem erro técnico de layout e com a lista do que precisa da decisão dela. Menos retrabalho, mesmo padrão em todos os livros.

Exemplo real de entrada (Paula, depois da revisão técnica do João):
> Fase concluída: validação de conteúdo. Próxima fase: 1. Diagramação: coloque esse conteúdo em diagramação (conforme manual enviado). 2. Criação de imagens complementares: após diagramado, veja espaços muito vazios nas páginas e crie imagens complementares, conceituais e clean, nas cores bordô, rosa claro, marsala e cinza, em sintonia com o conteúdo da página.

## 2. Objetivos, não objetivos, anti-objetivos
Objetivos da V1:
- Seis papéis com skill própria, regras fiéis à instrução da Paula e saída verificável.
- Editor-Chefe que conduz as fases, mantém a ficha do projeto e aplica o portão de nota.
- Diagramação A4 conforme o manual da Clinic e a ABNT, com checagem automática de layout.
- Imagens complementares nos espaços vazios, na paleta e no estilo pedidos.
- Pacotes instaláveis no ChatGPT, no claude.ai, no Claude Code e no Codex, gerados de uma fonte só.

Não objetivos da V1 (ficam para depois, sem bloquear):
- Serviço na VPS, interface web, banco e fila (o ADR do orquestrador cuida disso).
- Sincronizador Curso–Livro avançado (comparar versões de slides). A V1 só confere a correspondência slide a capítulo numa tabela.
- Produção gráfica (ISBN, gabarito da gráfica, prova física), marketing editorial e vídeo.
- Os papéis extras do briefing do Bruno (Editor de Projetos, de Desenvolvimento, Revisor de Originais, Diretor de Arte, Produção Gráfica, Marketing): a instrução da Paula os absorveu ou adiou.

Anti-objetivos (falha mesmo que "funcione"):
- Agente aprovando no lugar de pessoa: nota de 90% não libera nada para impressão.
- Texto científico aprovado mudado em silêncio pela diagramação.
- Referência inventada ou afirmação clínica sem fonte apresentada como fato.
- Imagem com conteúdo anatômico ou clínico entrando sem validação científica.
- Conteúdo de livro, dado de aluno ou foto clínica dentro deste repositório.

## 3. Restrições
- Custo: R$ 0 além das assinaturas que a Clinic já tem. Imagem pela geração nativa do ChatGPT ou do Codex, dentro do plano. API de imagem só na VPS, com preço e ok do Alify (GPT-Image-2: US$ 0,005 a 0,165 por imagem 1024×1536, `stack-platforms.md`, A6).
- Formato: padrão aberto Agent Skills. `name` com 1 a 64 caracteres em minúsculas, números e hífen, sem `claude` nem `anthropic`; `description` até 1.024 caracteres; `SKILL.md` abaixo de 500 linhas; pastas `references/`, `scripts/`, `assets/` (`stack-platforms.md`, A5).
- Plugin distribuído pela organização no Claude não pode ter pasta `bin/` no topo (`stack-platforms.md`, A4).
- Scripts em Python, com bibliotecas de licença permissiva: pdfplumber (MIT), pypdf, WeasyPrint (BSD-3) e python-docx (MIT); ReportLab (BSD) só nos testes, para gerar PDFs sintéticos. PyMuPDF fica fora, por ser AGPL e pesar na versão da VPS (`stack-layout.md`, B2).
- Normas: citar a regra e o número da norma, nunca copiar o texto da ABNT (direitos reservados, `stack-layout.md`, B3).
- Idioma: skills, regras e documentação em português; código dos scripts, nomes de função e mensagens de commit em inglês. Nomes das skills e dos agentes em português sem acento (`editor-chefe`), porque são o vocabulário da equipe e aparecem na tela da Paula (decisão desta sessão).

## 4. Abordagens consideradas
| | Forma | Escolha |
|---|---|---|
| A | Skills como fonte única, um papel por skill; um script gera o plugin do Claude, o do Codex e os zips para o ChatGPT e o claude.ai | **Escolhida pelo Alify.** Única que serve à Paula agora e à VPS depois, com uma versão só |
| B | Só um Projeto do ChatGPT com instruções e arquivos | Mais rápida, mas sem versão, sem Claude, sem Codex, sem VPS; os GPTs estão sendo aposentados no Enterprise |
| C | Só plugin do Claude Code com subagentes | Orquestração mais forte, mas a Paula usa o ChatGPT e o Claude não gera imagem |

O Projeto do ChatGPT (B) continua como plano de contingência: se as skills não estiverem disponíveis no plano da Clinic, os mesmos arquivos de `skills/` entram como arquivos e instruções de um Projeto (seção 9).

## 5. O time
Seis papéis: o Editor-Chefe e os quatro subagentes da instrução da Paula, mais o agente de imagens pedido pelo Alify em 18/11/2026. A instrução da Paula põe Arte e Vídeo como agente **externo** e pede para não criar agente a mais sem justificativa e aprovação. Justificativa: o pedido real dela (seção 1) inclui gerar imagens complementares logo depois da diagramação, e isso precisa de um papel com regras próprias. O `imagens` deste setup faz só imagens conceituais de preenchimento; ilustração anatômica, didática, infográfico e vídeo continuam com o agente externo de Arte e Vídeo. A aprovação da Paula a este papel entra na apresentação a ela (seção 13). Cada um tem uma skill em `skills/<papel>/` e uma definição de agente em `agents/editorial/<papel>.md`, no molde da casa (`~/.claude/docs/agent-template.md`, adaptado: o corpo da definição carrega a skill do papel e não repete as regras).

| Papel (skill) | Origem | Entrega | Nunca faz |
|---|---|---|---|
| `editor-chefe` | Agente Mestre da instrução da Paula; Editor-Chefe do briefing | Ficha do projeto, plano de fases, pedidos aos papéis, consolidação de nota, pacote para revisão humana | Aprovar no lugar do João ou da Paula; alterar conteúdo científico; liberar impressão |
| `editor-cientifico` | Editor Científico-Didático (unifica Pesquisador, Escritor e Preparador de Originais) | Plano de ampliação, manuscrito estruturado, tabela slide a capítulo, tabela de rastreabilidade das afirmações | Inventar referência; mudar decisão clínica do Board em silêncio; apagar conteúdo dos slides |
| `auditor-cientifico` | Auditor Científico | Relatório de não conformidades com localização, evidência e recomendação; nota da fase | Reescrever o manuscrito; confirmar o autor sem conferir a fonte |
| `diagramador` | Diagramador | Fonte editável do livro (HTML com CSS de impressão), PDF A4, relatório da checagem técnica | Criar imagem; alterar texto aprovado sem autorização registrada |
| `imagens` | Agente de Arte (externo na instrução; dentro do setup por pedido do Alify) | Imagens complementares com briefing, prompt usado, modelo usado quando disponível e marca de uso de IA | Aprovar a própria imagem; gerar imagem anatômica ou clínica sem passar pela validação científica |
| `auditor-grafico` | Auditor Gráfico | Relatório de erros por página (sobreposição, corte, duplicação, fonte de reserva, imagem em baixa resolução ou distorcida, margens, paginação, sumário, legenda) e nota da fase | Gerar ou editar imagem; corrigir o layout (só aponta) |

Pastas por time: `agents/editorial/` segue a estrutura combinada para o `agent-service` (um diretório por time). Os demais times não entram nesta V1. As definições em `agents/editorial/` são no formato do Claude Code; a versão da VPS reaproveita o texto das skills e decide o próprio formato de agente no ADR do orquestrador (`clinic-cursos/infra`, `docs/decisoes/2026-11-18-agents-orchestrator.md`, em proposta).

## 6. Fluxo, portões e nota
### 6.1 Fases
| # | Fase | Quem faz | Quem dá a nota | Portão humano |
|---|---|---|---|---|
| 0 | Abertura: ficha do projeto, materiais recebidos, fase de entrada | `editor-chefe` | — | — |
| 1 | Ampliação científica: plano, manuscrito, rastreabilidade, tabela slide a capítulo | `editor-cientifico` | `auditor-cientifico` | — |
| 2 | Revisão técnica | João | — | **João aprova o conteúdo** |
| 3 | Diagramação | `diagramador` | `auditor-grafico` | — |
| 4 | Imagens complementares e reinserção | `imagens`, depois `diagramador` | `auditor-grafico` | — |
| 5 | Aprovação editorial e gráfica | Paula | — | **Paula aprova a versão** |
| 6 | Produção gráfica (ISBN, gráfica, prova física) | Paula | — | **Paula libera a impressão** (fora da V1) |

O Editor-Chefe aceita entrar em qualquer fase, desde que a ficha ou o pedido diga a fase concluída. O pedido de exemplo da Paula entra na fase 3, com a fase 2 marcada como concluída por ela.

### 6.2 Portão de nota (pedido do Alify)
- Toda fase com nota termina com uma nota de 0 a 100, dada por quem não produziu (coluna "Quem dá a nota").
- **Passa com 90 ou mais e nenhum critério eliminatório.** Critério eliminatório reprova com qualquer nota.
- Abaixo disso, o Editor-Chefe devolve a quem produziu, com a lista de correções do auditor, e a fase roda de novo. **Até 3 voltas.** Na terceira reprovação, o Editor-Chefe para e entrega à Paula (ou ao João, na fase 1) o melhor resultado, a nota de cada volta e as pendências.
- Passar no portão de nota só libera a fase seguinte ou a revisão humana. Nunca substitui a aprovação do João ou da Paula.

Cada fase com nota tem a rubrica em `skills/editor-chefe/references/rubricas/<fase>.md`, com critérios, pesos que somam 100 e a lista de eliminatórios. Ponto de partida, a ajustar com a Paula:

- **Fase 1, ampliação científica:** fidelidade aos slides e à apostila 25; rastreabilidade (toda afirmação com fonte verificável, DOI ou PMID quando houver) 25; correção científica conferida pelo auditor 20; clareza didática 15; terminologia e padronização 15. Eliminatórios: referência que não existe; conteúdo de slide ausente sem justificativa; divergência com o Board não sinalizada.
- **Fases 3 e 4, diagramação e imagens:** conformidade com o manual da Clinic 30; hierarquia e consistência (fontes, tamanhos, espaçamentos) 20; ABNT 15; imagens e legendas 15; sumário e paginação 10; aproveitamento da página (sem vazios grandes depois da fase 4) 10. Eliminatórios: texto sobreposto; texto cortado; parágrafo duplicado; fonte de reserva no lugar da fonte do manual; texto aprovado diferente do original; imagem distorcida; imagem anatômica ou clínica sem validação.

### 6.3 Independência
- No Claude Code, no Cowork e no Codex local, cada papel roda como subagente, com só os arquivos de entrada do dispatch.
- No chat do ChatGPT e do claude.ai, que não têm subagente, os papéis rodam um depois do outro. A auditoria científica (fase 1) roda numa **conversa nova**: o Editor-Chefe monta o "pacote de auditoria" (manuscrito, tabela de rastreabilidade, materiais originais) e orienta a Paula a abri-lo numa conversa separada com a skill `auditor-cientifico`. A auditoria gráfica é feita pelo script, que não depende da conversa, mais a inspeção visual das páginas apontadas.

## 7. Ficha do projeto (memória da V1)
Um arquivo `ficha-<projeto>.md` por livro, com modelo em `skills/editor-chefe/references/ficha-projeto.md`. Campos obrigatórios:
- identificação: título, curso, autores, data de abertura, fase atual;
- materiais recebidos, com versão e data;
- fases: estado, quem fez, nota de cada volta, pendências;
- aprovações humanas: quem, qual versão (nome do arquivo e SHA-256 quando o ambiente calcula), data e hora;
- decisões e divergências levadas ao Board;
- imagens geradas por IA: página, briefing, modelo quando disponível, estado de validação (alimenta a nota editorial do livro);
- custos, quando o ambiente mostra: imagens geradas, tokens ou mensagens gastas, tempo de cada fase;
- histórico, uma linha por evento.

Regras: versão aprovada não muda; mudança gera versão nova. O Editor-Chefe começa toda conversa lendo a ficha e termina toda fase entregando a ficha atualizada.

Onde a ficha fica:
- ChatGPT e claude.ai: nos arquivos do Projeto da Clinic Editora. A Paula substitui o arquivo pela versão nova que o Editor-Chefe entrega no fim de cada fase (o chat não grava arquivo do Projeto sozinho; limitação registrada na seção 11).
- Claude Code e Codex: em `<pasta de trabalho>/projetos/<projeto>/`, fora deste repositório, com `ficha.md`, `originais/`, `versoes/` e `relatorios/`.
- VPS (depois): no PostgreSQL, pelo desenho do ADR do orquestrador.

## 8. Diagramação e imagens, por dentro
### 8.1 Fonte do livro
O Diagramador gera uma fonte editável em HTML com CSS de impressão (`@page`, cabeçalho e rodapé, sumário com `target-counter()`) e o PDF sai dela pelo WeasyPrint (`stack-layout.md`, B1). Motivos: o texto fica versionável e comparável; o mesmo modelo serve a todos os livros; o WeasyPrint aceita as fontes da marca por `@font-face`. A instrução da Paula aceita "DOCX ou outro formato editável definido tecnicamente"; DOCX fica como exportação opcional, se a Paula pedir.

- Modelo e estilo em `skills/diagramador/assets/` (`livro.html`, `livro.css`), com as fontes da marca embutidas: Montserrat e Source Sans 3 (licença OFL). No PDF de Preenchedores, a capa usa essas fontes, mas as páginas internas saíram em DejaVu Sans, fonte de reserva (conferido com `pdffonts` em 18/11/2026). A V1 elimina esse defeito.
- Componentes editoriais da Clinic, como classes do CSS: Estudo e Prática, Leitura e Aprofundamento, Aplicação Clínica, Ponto-chave, Atenção, Evidência, Perguntas frequentes, legenda padrão de antes e depois, módulo de QR code (do briefing, seção 8, e do PDF "Padrões e Pendências Visuais").
- Manual de diagramação da Paula: entra em `skills/diagramador/references/manual-clinic.md` quando chegar. Até lá, o arquivo diz "aguardando o manual" e a skill usa os padrões já conhecidos (identidade bordô, branco e cinza; A4; legenda Source Sans 9/11,5 pt cinza), marcando no relatório cada regra que veio de inferência.
- ABNT: `skills/diagramador/references/abnt.md` resume, com o número da norma, o que se aplica a livro técnico-didático: NBR 6029:2023 (apresentação de livros, confirmada na capa da norma) e, com confiança média até conferir no catálogo da ABNT, NBR 6023 (referências), 10520 (citações), 6024 (numeração progressiva), 6027 (sumário), 6034 (índice) (`stack-layout.md`, B3).

Entradas (decisão desta sessão):
- **Caminho de produção:** o manuscrito em Markdown que o Editor Científico entrega e o João aprova. As convenções (metadados no topo, blocos editoriais como `:::ponto-chave`, marca de origem `<!-- slide: 12 -->`) ficam em `shared/references/manuscrito.md`, definidas por quem constrói. DOCX entra convertido para esse Markdown.
- **Livros já compostos em PDF** (caso de Preenchedores e de Toxina): o PDF é extraído para o Markdown com o pdfplumber, preservando ordem, títulos e blocos; a fidelidade é conferida comparando o texto de entrada com o de saída (seção 10). É o caminho dos livros que já existem, não o principal.
- Slides e apostila do Board: PDF exportado (padrão). PPTX entra pelo python-pptx (MIT) se a equipe mandar nesse formato.

Aparência do modelo: o `livro.css` reproduz o visual dos livros e documentos de referência que a Paula já aprovou (capa bordô, Montserrat nos títulos, Source Sans no texto, títulos e rótulos em bordô). Cores, fontes, tamanhos e espaçamentos ficam como variáveis num arquivo só, `assets/tokens.css`, porque o design system dos documentos está sendo criado pelo Alify com a Paula e a Julie (informado em 18/11/2026); quando ele chegar, um cartão novo troca os valores desse arquivo, sem mexer no resto. Antes do teste real, o Diagramador renderiza três páginas de amostra (abertura de capítulo, página de texto com caixas, página com imagem e legenda) e o Alify confere contra as referências aprovadas (regra da casa: mudança visível só com mockup aprovado). Enquanto o manual da Paula não chegar, a nota da fase 3 sai marcada "provisória: manual ausente", e o Editor-Chefe repete essa marca ao reportar.

Motor: só o WeasyPrint na V1, sem segundo motor. Se o teste de plataforma (critério 0) mostrar que o ChatGPT não roda o WeasyPrint, o Diagramador e o Auditor Gráfico rodam no Claude Code ou no Codex, e o ChatGPT fica com os demais papéis.

### 8.2 Checagem técnica (scripts)
- `skills/auditor-grafico/scripts/audit_pdf.py`: lê o PDF com pdfplumber e pypdf e lista, por página, sobreposição de caixas de texto, texto fora da área útil, parágrafo duplicado, fonte fora da lista do manual, imagem com DPI efetivo abaixo do mínimo (pixels ÷ (largura exibida em pt ÷ 72)), imagem com proporção alterada, margens, número de página e entradas do sumário. Saída em JSON e Markdown.
- `skills/diagramador/scripts/check_layout.py`: a mesma checagem em modo rápido, que o Diagramador roda antes de entregar (exigência da instrução da Paula, fase 2).
- `skills/imagens/scripts/free_space.py`: mede o espaço livre de cada página (do fim do último objeto de texto, imagem ou desenho até a zona de segurança inferior, na largura útil) e lista as páginas com espaço acima do limite, com largura, altura e proporção do retângulo livre.

Os três compartilham uma biblioteca pequena (`lib/pdfcheck/`), copiada para dentro de cada skill pelo script de empacotamento, porque uma skill não lê arquivo de outra.

Regra de resolução (provisória, a confirmar com a Paula): imagem herdada do original e usada no tamanho dela entra como **aviso**, porque o Diagramador não melhora fotografia; imagem nova, ou ampliada pelo Diagramador, entra como **erro** abaixo de 150 ppi efetivos e como aviso abaixo de 300 ppi. No PDF de Preenchedores, 32 das 33 imagens estão abaixo de 150 ppi (medido com `pdfimages -list` em 18/11/2026); elas viram uma lista de avisos para a Paula pedir originais melhores, como o PDF de padrões visuais já faz nas páginas 50 e 54.

- `skills/auditor-cientifico/scripts/verify_refs.py`: confere cada referência pelas APIs gratuitas do Crossref (DOI) e do PubMed (PMID), comparando título, autores e ano. Sem rede, a referência sai "não verificada" e vai para a lista do João; não é eliminatória sozinha, mas tira os pontos de rastreabilidade dela. "Conferir" é existir e bater os metadados; dizer se a fonte sustenta a afirmação é juízo do auditor, registrado como juízo, não como fato.

### 8.3 Imagens complementares
1. `free_space.py` lista as páginas com espaço livre acima do limite (ponto de partida: 25% da altura útil; a Paula confirma).
2. Para cada página, a skill `imagens` lê o conteúdo da página e escreve o briefing: tema, conceito, paleta (bordô, rosa claro, marsala, cinza), estilo conceitual e clean, proporção do espaço livre, sem texto dentro da imagem.
3. Gera a imagem pela ferramenta nativa do ambiente (ChatGPT ou Codex). No Claude, que não gera imagem, entrega os briefings para gerar no ChatGPT ou no Codex.
4. **Imagem complementar é sempre conceitual** (formas, texturas, objetos simbólicos, composições abstratas), como o pedido da Paula diz. Ela nunca representa anatomia, pele com lesão, procedimento, produto de marca ou resultado de tratamento. Na dúvida, a skill troca o conceito por um mais abstrato, em vez de bloquear. Se a página pedir uma ilustração técnica de verdade, isso vira pedido ao Editor-Chefe para o João validar, fora da fase 4, e não impede a fase de fechar (decisão desta sessão, a confirmar com a Paula).
5. Caminho do arquivo até o Diagramador: no Codex local e no Claude Code, a imagem fica na pasta do projeto (`imagens/pagina-NN.png`). No ChatGPT, se o ambiente Python não enxergar a imagem gerada na conversa, a Paula baixa e reenvia os arquivos com esse nome; o guia dela explica o passo. O teste de plataforma (critério 0) diz qual caso vale.
6. O Diagramador insere a imagem no espaço medido, sem mover o texto, e roda a checagem de novo.
7. Cada imagem entra na ficha (seção 7) e na nota editorial de uso de IA do livro.

Paleta e estilo em `skills/imagens/references/paleta.md`, com os valores de cor tirados dos PDFs da Clinic.

## 9. Repositório e empacotamento
```
editorial-setup/
  README.md                 o que é, como instalar em cada plataforma
  AGENTS.md                 regras do time (lido pelo Codex); CLAUDE.md aponta para ele
  skills/                   fonte única, uma pasta por papel
    editor-chefe/  editor-cientifico/  auditor-cientifico/
    diagramador/  imagens/  auditor-grafico/
  shared/references/        governança, identidade visual e glossário, copiados para cada skill no empacotamento
  lib/pdfcheck/             código comum dos scripts de PDF
  agents/editorial/         definição de cada agente (Claude Code); o empacotamento gera os TOML do Codex
  .claude-plugin/           plugin.json e marketplace.json
  .codex-plugin/plugin.json
  scripts/package.py        valida e empacota
  tests/                    testes dos scripts com PDFs pequenos de exemplo
  docs/guia-paula.md        instalar e usar no ChatGPT, fase por fase, com o pedido de exemplo
  docs/guia-equipe.md       instalar e usar no Claude Code, no Cowork, no claude.ai e no Codex
  docs/fontes/  docs/superpowers/
```
`scripts/package.py`:
- valida cada skill: frontmatter, limites de `name` e `description`, `SKILL.md` abaixo de 500 linhas, nome sem `claude` nem `anthropic`, nenhuma pasta `bin/` no topo;
- copia `shared/references/` e `lib/pdfcheck/` para dentro de cada skill, em `dist/`;
- gera `dist/chatgpt/<skill>.zip` e `dist/claude-ai/<skill>.zip` (com `SKILL.md` na raiz do zip), os TOML dos agentes do Codex em `dist/codex/agents/` a partir de `agents/editorial/` (o guia da equipe manda copiar para `.codex/agents/` do projeto ou para `~/.codex/agents/`), e confere os manifestos dos dois plugins;
- sai com código diferente de 0 se algo falhar. `dist/` não vai para o git.

Contingência sem skills no ChatGPT: o `package.py` também gera `dist/chatgpt-projeto/`, com as instruções do Projeto (o `SKILL.md` do Editor-Chefe) e os demais `SKILL.md` e referências como arquivos do Projeto.


### 9.1 A Paula trabalha e melhora o setup
O objetivo é a Paula já trabalhar com o setup no ChatGPT, que ela usa todo dia, e melhorá-lo com o uso (Alify, 18/11/2026). Para a fonte continuar única:
- Cada melhoria vira uma linha em `docs/melhorias.md` (data, papel, o que mudar, por quê, exemplo). A Paula pode ditar a melhoria ao Editor-Chefe, que devolve a linha pronta para ela mandar ao Alify, ou mandar direto.
- A mudança entra no repositório, passa pelos testes e pelo `package.py`, sobe a versão do plugin e ganha uma linha em `CHANGELOG.md`; a Paula reinstala o pacote novo.
- Mudança feita direto na skill instalada no ChatGPT se perde no próximo pacote; o guia dela diz para mandar de volta.

## 10. Critérios de aceite
Em ordem de construção, seguindo a ordem oficial da Paula (Editor-Chefe, Diagramador, Editor Científico, Auditor Científico, Auditor Gráfico) e pondo o agente de imagens logo depois do Diagramador, porque o pedido de exemplo usa os dois juntos.

Livros de teste, fora do repositório (fotos clínicas e conteúdo do Board não entram no git): o caminho vem da variável `EDITORIAL_SAMPLES_DIR` (nesta máquina, `~/Downloads/livros-paula/`, com os dois PDFs). **Preenchedores** é o caso positivo, porque é o fluxo do pedido da Paula. **Toxina** é o caso negativo do Auditor Gráfico, porque o briefing diz que ele tem repetição e sobreposição em várias páginas, e o caso inicial que a instrução da Paula pede para o Diagramador. Os testes do repositório usam só PDFs, imagens e capítulos sintéticos.

0. **Teste de plataforma no ChatGPT**, feito pela Paula quando puder (ela já usa o ChatGPT), sem travar a construção do Diagramador, que roda localmente: instalar uma skill de teste, rodar `import weasyprint` e `pip list` pelo Python da conversa, gerar uma imagem e ver se o Python enxerga o arquivo dela. O resultado decide o motor no ChatGPT (seção 8.1) e o passo 5 da seção 8.3. Registrado em `docs/medicoes/`.
1. **Empacotamento:** `python scripts/package.py` sai com código 0, gera os zips das seis skills e os TOML dos seis agentes; um teste com uma skill inválida (nome com `claude`, `description` acima de 1.024) faz o script sair com erro.
2. **Editor-Chefe** (critério da instrução da Paula, fase 1): num projeto de teste, cria a ficha com todos os campos da seção 7, delega uma tarefa a um papel, recebe o resultado, aplica o portão de nota (um caso que passa com 92 e outro que volta com 85) e registra tudo no histórico.
3. **Checagem de PDF** (`tests/`): em PDFs pequenos de exemplo, acusa uma sobreposição injetada, um texto fora da margem, um parágrafo duplicado, uma fonte de reserva e uma imagem abaixo do DPI mínimo; num PDF limpo, zero erros.
4. **Diagramador**, com o PDF de Toxina (caso inicial da instrução da Paula, com os originais preservados) e depois o de Preenchedores: três páginas de amostra conferidas pelo Alify contra as referências aprovadas pela Paula, antes do livro inteiro; PDF A4; só as fontes do manual (nenhuma DejaVu); zero sobreposição, corte e duplicação na checagem; números do sumário iguais à paginação; texto de saída igual ao de entrada em pelo menos 99,5% dos caracteres, sem contar cabeçalho, rodapé e números de página.
5. **Imagens**, no mesmo livro: lista das páginas com espaço livre acima do limite; uma imagem por página selecionada, na proporção do espaço; depois da reinserção, a checagem continua com zero erros e a paginação não muda.
6. **Editor Científico e Auditor Científico**, com um capítulo sintético (slides de teste em PDF, escritos para o teste): tabela slide a capítulo sem slide órfão; toda afirmação nova com fonte; o `verify_refs.py` confere cada DOI ou PMID e acusa uma referência inventada plantada no texto.
6a. **Auditor Gráfico** no PDF de Toxina: acusa erros de repetição ou sobreposição nas páginas onde existem, e os avisos de resolução.
7. **Instalação:** o Alify (ou a Paula) instala os zips no ChatGPT e no claude.ai e o plugin no Claude Code e no Codex, e roda o pedido de exemplo no ChatGPT. Teste manual, registrado em `docs/medicoes/`.

## 11. Limites conhecidos e o que fica em aberto
- Skills no ChatGPT estão em beta e vêm desligadas; quem administra o workspace liga. Os planos que têm o recurso não foram confirmados em fonte oficial (a página de ajuda deu 403). O critério 7 confirma; se não houver, vale a contingência do Projeto.
- Não há fonte dizendo que uma skill do ChatGPT aciona a geração de imagem ou o Python por conta própria; a skill pede ao modelo, que usa as ferramentas da conversa. O critério 7 confirma.
- A lista de bibliotecas do ambiente Python do ChatGPT não é publicada; o WeasyPrint aparece só em lista da comunidade. Se faltar, vale a seção 8.1: o Diagramador e o Auditor Gráfico rodam no Claude Code ou no Codex.
- O chat do ChatGPT e do claude.ai não grava a ficha nos arquivos do Projeto; a Paula substitui à mão.
- Limite de 30 MB por arquivo no claude.ai; o PDF de Preenchedores tem 4,8 MB.
- Manual de diagramação da Paula: não chegou. Limite de espaço livre (25%), regra de resolução (seção 8.2) e a regra das imagens só conceituais (seção 8.3): valores provisórios desta sessão, a confirmar com ela.
- A auditoria de referências depende de rede: o sandbox da API do Claude não tem internet, e no claude.ai Enterprise a rede vem desligada por padrão (`stack-layout.md`, B1).
- A conta `miguel-fd2` tem leitura no repositório pela permissão base da org; o Alify a usa em outra máquina e decidiu mantê-la.

## 12. Por que não passou pelo planejamento com prova completo
A regra da casa pede ADR, `verifier` e pre-mortem para escolha de stack. Aqui o caminho foi o curto (brainstorming, pesquisa com fonte, spec, revisão de construção e revisão final), porque a escolha é reversível e sem custo: as skills são texto, e o motor de PDF fica atrás dos scripts de uma skill só. Se a V1 mostrar que o WeasyPrint ou o pdfplumber não servem, a troca fica dentro do `diagramador` e do `lib/pdfcheck/`. A escolha que pesa de verdade, a peça de orquestração da VPS, passa pelo Fluxo 1 completo no ADR do orquestrador.

## 13. Resposta à primeira entrega pedida pela Paula
A instrução da Paula (seção 8) pede dez itens antes de implementações extensas. Este documento é a resposta; o Alify apresenta a ela antes da onda do Diagramador (cartão manual do plano).

1. **Diagnóstico do setup atual:** não havia setup editorial implementado. O `agent-service` da VPS tem só o README; existe um ADR proposto da peça de orquestração da VPS (Pydantic AI com DBOS) e uma proposta de MVP de outra sessão, com cinco papéis tirados do briefing do Bruno, já marcada como desatualizada por aquela sessão em 18/11/2026. O trabalho de hoje é feito à mão pela Paula no ChatGPT.
2. **Estrutura definitiva:** seção 5.
3. **O que já está implementado:** nada além deste desenho, da pesquisa e do repositório.
4. **O que precisa ser modificado:** a lista de papéis da proposta de MVP da outra sessão cai; a versão da VPS reaproveita estas skills.
5. **Redundâncias eliminadas:** os dez papéis do briefing do Bruno viram seis. Pesquisador Científico, Escritor Técnico-Didático e Revisor de Originais viram o Editor Científico (como a Paula pediu); Editor de Projetos e Editor de Desenvolvimento ficam com o Editor-Chefe; Diretor de Arte, Produção Gráfica e Marketing ficam para depois.
6. **Comunicação e delegação:** seção 6 (pedido estruturado do Editor-Chefe, bloco de retorno fixo de cada papel, portão de nota, independência).
7. **Memória persistente:** seção 7 (ficha do projeto; na VPS, o PostgreSQL do ADR do orquestrador).
8. **Plano de execução:** `docs/superpowers/plans/2026-11-18-editorial-setup.md`, com o Editor-Chefe primeiro e o Diagramador em seguida.
9. **Critérios de teste e aceite:** seção 10 (critério 2 para o Editor-Chefe, 4 e 5 para o Diagramador).
10. **Integração com o ChatGPT para imagens:** seções 8.3 e 11. A geração nativa existe na interface do ChatGPT e no Codex, dentro do plano; não há API com o mesmo recurso grátis, e a API paga (GPT-Image-2) fica para a VPS, com preço e ok.

Pontos para a Paula decidir na apresentação: o papel `imagens` dentro do setup; os valores provisórios (25% de página vazia, regra de resolução, imagens só conceituais); o envio do manual de diagramação.

## 14. O que fica com quem constrói
- O texto de cada `SKILL.md`, dentro destas regras: missão, quando acionar, entradas, processo numerado, barra de qualidade, saída, limites e retorno, no espírito do molde da casa.
- Os pesos finos das rubricas, partindo dos da seção 6.2.
- Os valores exatos de cor da paleta, tirados dos PDFs.
- A heurística de extração de PDF para HTML, desde que passe no critério 4.
