# Roteiro do teste no ChatGPT da Clinic

Este teste verifica as bibliotecas Python e o acesso à imagem gerada na conversa. Anote o resultado em `docs/medicoes/2026-11-teste-chatgpt.md`.

## Preparar e executar

1. Confira se o plano do ChatGPT da Clinic permite ligar skills no workspace. Se permitir, ligue as skills no workspace. Se não tiver essa opção, anote isso no resultado.
2. Compacte a pasta `docs/medicoes/teste-plataforma/` em um arquivo ZIP.
3. No ChatGPT, envie o ZIP pela área de Skills e ative a skill `teste-plataforma`.
4. Abra uma conversa nova.
5. Cole este pedido:

   > Siga a skill teste-plataforma. Faça todas as verificações pedidas, mostre as saídas observadas e não invente resultados.

6. Copie o resultado da conversa para `docs/medicoes/2026-11-teste-chatgpt.md` e preencha o modelo abaixo. Marque como presente somente o que foi confirmado pela saída.

## Modelo do resultado

```markdown
# Teste do ChatGPT da Clinic

Data:

## Plano do ChatGPT


## Skills disponíveis


## Bibliotecas Python

- WeasyPrint: presente / ausente
- pdfplumber: presente / ausente
- pypdf: presente / ausente
- python-docx (`docx`): presente / ausente

Saída do `pip list` e dos imports:


## Aulas

- python-pptx: presente / ausente
- lxml: presente / ausente
- Pillow: presente / ausente
- LibreOffice (`soffice`): presente / ausente
- `pdftoppm`: presente / ausente
- Montserrat: presente / ausente
- Produz aulas com prévia: sim / não

Saída dos imports, versões e comandos:


## Imagem gerada


## Python enxerga a imagem

- Resultado: sim / não
- Caminho:
- Tamanho em bytes:

## Observações

```

Sem `soffice` ou `pdftoppm`, a produção de aulas deve ser feita pela equipe no Claude Code ou no Codex, conforme o guia da Paula.

Se o Python não enxergar a imagem, registre isso como resultado. O roteiro não exige que a imagem seja baixada ou reenviada.
