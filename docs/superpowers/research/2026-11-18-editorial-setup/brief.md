# Brief: setup editorial de IA da Clinic Editora (V1)

Data: 2026-11-18. Sessão de decisão do Alify. Pesquisa de fatos para o desenho; não escolhe a solução.

## Problema
A Clinic Editora transforma slides e apostilas de cursos de estética em livros A4 de cerca de 80 páginas. Hoje a Paula (aprovação editorial) faz isso à mão no ChatGPT, com o manual técnico da editora. Queremos um time de agentes de IA (Editor-Chefe orquestrador, Diagramador, Editor Científico-Didático, Auditor Científico, Auditor Gráfico e um agente de imagens) empacotado como **skills** reutilizáveis, para a equipe interna usar primeiro no ChatGPT e também no Codex e no Claude. Depois, o mesmo time vai rodar num serviço próprio em Python numa VPS.

Exemplo real de uso, enviado pela Paula ao ChatGPT depois da revisão técnica humana:
"Fase concluída: validação de conteúdo. Próxima fase: 1. Diagramação: coloque esse conteúdo em diagramação (conforme manual enviado). 2. Criação de imagens complementares: após diagramado, veja espaços muito vazios nas páginas e crie imagens complementares, conceituais e clean, nas cores bordô, rosa claro, marsala e cinza, em sintonia com o conteúdo da página."
A entrada é um PDF A4 de 84 páginas já composto (texto, títulos, boxes), com espaços vazios no fim de várias páginas.

## Restrições
- Custo: o padrão é grátis; usar o que as assinaturas do ChatGPT e do Claude já incluem. API paga só com preço e alternativa grátis.
- Não presumir que a geração de imagem da interface do ChatGPT equivale a uma API com os mesmos recursos.
- Fonte oficial primeiro (documentação do fornecedor, página de preço, norma). Toda afirmação com fonte e data de leitura; sem fonte, vai para "Não sei".

## Perguntas

### Bloco A: plataformas (relatório `stack-platforms.md`)
A1. ChatGPT (web e app), hoje: existe suporte a skills no formato Agent Skills (`SKILL.md`)? Em quais planos (Plus, Pro, Business, Enterprise)? Como se instala (upload de zip, pasta, repositório)? Limites (tamanho, número de skills, scripts executáveis)? Uma skill consegue usar a geração nativa de imagens e o ambiente Python do ChatGPT?
A2. Alternativas no ChatGPT para o mesmo fim: Projetos (instruções e arquivos do projeto, memória do projeto), GPTs personalizados, apps (Apps SDK, MCP). O que cada um guarda entre conversas e quais limites de arquivos e instruções tem.
A3. Codex (CLI, extensão, app desktop, Codex dentro do ChatGPT): onde ficam as skills, se existe formato de plugin ou marketplace, se há subagentes ou papéis, se o Codex gera imagem (ferramenta nativa ou skill) e com que custo.
A4. Claude: formato de plugin do Claude Code (`.claude-plugin/plugin.json`, `marketplace.json`, skills, agents, commands), uso no Claude Desktop e no Cowork, upload de skills no claude.ai (planos, limites), se subagentes funcionam fora do Claude Code. O Claude gera imagem raster nativamente?
A5. Agent Skills como padrão aberto: especificação atual (campos do frontmatter, limites de `name` e `description`, tamanho recomendado do `SKILL.md`, pastas `references/`, `scripts/`, `assets/`) e quais produtos a adotam. Um mesmo `SKILL.md` roda sem mudança no ChatGPT, no Codex e no Claude?
A6. Geração de imagem por API, para quando o time rodar fora da interface (Claude Code, VPS): modelo atual de imagem da OpenAI e preço por imagem; alternativas.

### Bloco B: diagramação, auditoria gráfica e ABNT (relatório `stack-layout.md`)
B1. Que ferramentas de composição de livro A4 dão resultado profissional e rodam (a) no ambiente Python do ChatGPT, (b) na execução de código do claude.ai, (c) numa máquina local ou VPS: DOCX (python-docx), PDF por HTML e CSS de impressão (WeasyPrint, Paged.js), Typst, LaTeX com abnTeX2, ReportLab. Para cada uma: licença, se está disponível em cada ambiente (lista oficial de bibliotecas, quando houver), saída editável, suporte a sumário automático, cabeçalho e rodapé, fontes próprias.
B2. Como inspecionar um PDF renderizado para achar sobreposição de texto, texto cortado, parágrafo duplicado, imagem distorcida, imagem em baixa resolução (DPI efetivo), margens, paginação e espaço vazio por página (PyMuPDF/pdfplumber, renderização para imagem). Licenças (atenção ao AGPL do PyMuPDF).
B3. Normas ABNT vigentes que se aplicam a livro técnico-didático: apresentação de livros, referências, citações, numeração progressiva, sumário, índice. Número e ano de cada norma em vigor, pela fonte oficial da ABNT ou fonte que a cite.
B4. Como medir "espaço vazio" numa página de PDF para decidir onde cabe uma imagem complementar, e como inserir a imagem sem mover o texto.

## Saída
Relatório no modelo da casa (`~/.claude/skills/plan-with-proof/research-report.md`), com tabela de fontes e seção "Não sei". Grave cedo e complete por seções.
