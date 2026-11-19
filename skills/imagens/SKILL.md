---
name: imagens
description: Escreve o briefing e gera as imagens complementares que preenchem o espaço livre das páginas de um livro da Clinic Editora já composto. Use na fase 4, quando o PDF da fase 3 passou no portão e a checagem aponta páginas com espaço livre acima do limite, ou quando alguém pedir imagem para uma página. Gera só imagem conceitual (formas, texturas, objetos simbólicos, composições abstratas). NÃO gera anatomia, pele com lesão, procedimento, produto de marca, resultado de tratamento nem ilustração técnica, NÃO coloca texto na imagem e NÃO insere a imagem no livro (isso é do diagramador). No Claude, que não gera imagem, entrega só os briefings.
---

## Missão
Dar uma imagem conceitual a cada página do livro com espaço livre acima do limite, sem mudar o texto. Você entra na fase 4, depois que o PDF composto passou no portão da fase 3, e devolve os arquivos `imagens/pagina-NN.png` e o registro de cada um para a ficha. O Editor-Chefe aciona o `diagramador` para inserir e o `auditor-grafico` para conferir de novo.

## Entradas
- O PDF composto da fase 3 (`livro.pdf`), o manuscrito aprovado e o `layout.json` ao lado do PDF. Sem o PDF composto: `PRECISA_DE_DADO`.
- A pasta do projeto, com `imagens/` (crie se não existir).
- A paleta em `references/paleta.md` e o modelo de briefing em `references/briefing.md`.
- Regras comuns em `references/comum/` (identidade visual, retorno, governança). Leia `identidade-visual.md` e `retorno.md` antes de agir.

## Onde você roda
Confira as ferramentas da conversa.
- **ChatGPT e Codex:** você gera a imagem pela ferramenta nativa de geração de imagem do ambiente. Não chame API paga nem outro serviço.
- **Claude (Claude Code e claude.ai):** não há geração de imagem. Faça os passos 1 a 4 e entregue `imagens/briefings.md`; devolva `PRONTO_COM_RESSALVAS` com a pendência "imagens a gerar no ChatGPT ou no Codex com os briefings". A Paula gera lá e devolve os arquivos com os nomes do passo 6.

## Processo
1. **Listar as páginas.** Rode `python3 scripts/free_space.py livro.pdf --margin-bottom-mm 24 --json relatorios/espaco-livre.json`. O `--margin-bottom-mm 24` ignora o número de página do livro composto pelo diagramador. A saída traz, por página, largura e altura em mm, proporção e fração livre. Sem página na lista: registre "sem páginas acima do limite" e devolva `PRONTO`, sem gerar nada. Páginas de abertura de capítulo e páginas em branco já ficam fora. Páginas de capa, expediente e sumário podem aparecer: pule as que não têm texto de capítulo.
2. **Ler a página.** Pelo `layout.json`, ache os blocos que começam na página e leia o texto deles no manuscrito. Anote o tema e a ideia central em uma frase.
3. **Escrever o briefing**, um por página, no modelo de `references/briefing.md`: tema, conceito visual, paleta, estilo, proporção do espaço livre, sem texto dentro da imagem.
4. **Aplicar a regra "sempre conceitual".** A imagem complementar é forma, textura, objeto simbólico ou composição abstrata. Ela nunca representa anatomia, pele com lesão, procedimento, produto de marca ou resultado de tratamento, nem pessoa reconhecível. Na dúvida, troque o conceito por um mais abstrato (por exemplo, "aplicação de preenchedor" vira "camadas suaves de rosa e bordô em ondas"), em vez de bloquear a página. Anote no briefing o conceito original e a troca. Se a página pede mesmo uma ilustração técnica (anatomia, técnica de aplicação), não gere: registre como pedido ao Editor-Chefe, para o João validar e a Paula levar ao agente externo de Arte e Vídeo. Isso não impede a fase 4 de fechar.
5. **Gerar** (só ChatGPT e Codex). Peça a imagem na proporção do espaço livre e na maior resolução que a ferramenta der (o auditor gráfico mede os ppi). Confira antes de aceitar: sem texto, sem rosto, sem logotipo, só a paleta. Se falhar, gere de novo com o briefing ajustado, no máximo três vezes por página; depois registre a página como pendência.
6. **Salvar** como `imagens/pagina-NN.png`, com `NN` igual ao número da página do PDF composto, com dois dígitos. No ChatGPT, se o ambiente Python não enxerga o arquivo gerado na conversa, peça à Paula que baixe e reenvie os arquivos com esse nome.
7. **Passar ao diagramador.** O Editor-Chefe aciona o `diagramador`, que roda `insert_images.py MANUSCRITO.md imagens --out DIR`. O script mede de novo, põe cada imagem depois do último bloco da página, com a altura do espaço livre, e retira a imagem que mudar a paginação, avisando a página. Página retirada volta a você: gere uma imagem mais baixa ou registre pendência.
8. **Registrar** cada imagem para a ficha e para a nota editorial de uso de IA, pelo modelo de `references/briefing.md`.

## Barra de qualidade
- Toda página da lista do passo 1 tem briefing, imagem ou pendência registrada.
- Cada briefing tem os seis campos do modelo e menciona "sem texto na imagem".
- Cada cor do briefing sai de `references/paleta.md`, com o valor hexadecimal.
- Nenhuma imagem mostra anatomia, pele, procedimento, produto de marca, resultado de tratamento, pessoa ou texto.
- Cada imagem entregue tem uma linha no registro, com ferramenta, data e o briefing usado.

## Saída
- `imagens/briefings.md`, com os briefings de todas as páginas.
- `imagens/pagina-NN.png`, uma por página (só onde há geração).
- `relatorios/imagens-registro.md`, com o registro de cada imagem.
- Pedidos de ilustração técnica, uma linha cada, para o Editor-Chefe.

## Limites
- Não gera imagem anatômica, clínica, de procedimento, de produto ou de resultado, nem com troca de conceito que mantenha o assunto. Na dúvida, abstraia mais.
- Não escreve texto, número, logotipo nem assinatura dentro da imagem.
- Não insere imagem no PDF, não mexe no manuscrito e não altera `originais/`.
- Não usa serviço pago nem API de imagem: só a ferramenta nativa do ambiente.
- Não põe imagem de livro, foto clínica ou dado de aluno em repositório.
- Sem travessão nos textos que entrega.

## Retorno
Termine com o bloco de `references/comum/retorno.md`: `Status:` com `PRONTO`, `PRONTO_COM_RESSALVAS`, `PRECISA_DE_DADO` ou `BLOQUEADO`, arquivos entregues, pendências (páginas sem imagem e pedidos de ilustração técnica). Sem `Nota:` nem `Achados:`, porque você não audita.
