---
name: teste-plataforma
description: Verifica quais bibliotecas Python e recursos de arquivos estão disponíveis nesta conversa do ChatGPT. Use para executar o teste de plataforma da Clinic Editora.
---

# Teste de plataforma

Faça as verificações nesta conversa e mostre a saída observada. Não presuma que um recurso está disponível.

1. No Python da conversa, execute `import weasyprint, pdfplumber, pypdf, docx` e depois `pip list`. Mostre a saída dos comandos. Se algum import falhar, indique qual biblioteca falhou e mostre o erro.
2. Gere uma imagem simples, por exemplo, um quadrado colorido sobre fundo branco. Diga se a imagem foi gerada.
3. Verifique se o Python desta conversa consegue acessar o arquivo da imagem gerada. Se conseguir, mostre o caminho do arquivo e o tamanho em bytes. Se não conseguir, diga claramente que o Python não enxerga esse arquivo.
4. Verifique se o ambiente consegue produzir aulas. No Python da conversa, execute `import pptx, lxml, PIL` e mostre a versão de `python-pptx`, `lxml` e Pillow. Depois execute `soffice --version` e `pdftoppm -v` (ou `which soffice` e `which pdftoppm`); mostre a saída observada ou o erro de cada comando. Se `fc-list` existir, execute `fc-list | grep -i montserrat` e mostre a saída ou informe que nenhuma fonte Montserrat foi encontrada.

Não invente saídas, caminhos ou tamanhos. Registre limitações encontradas nas observações.
