# Ensaio de diagramação: Toxina_Botulinica_Miolo_Alta_Resolucao

Resultado: REPROVADO

- Motivos: `extract_pdf.py` passou de 180 s e foi interrompido; o resto do fluxo não rodou

## Causa provável e correção sugerida (por script)
- `extract_pdf.py`: o pypdf recodifica cada imagem JPEG 2000 do PDF pelo codificador do Pillow (`Jpeg2KImagePlugin`), que é muito lento em imagem grande; no Toxina (80 páginas, 36 MB) a extração passou de 30 min sem terminar, contra 5 s do Preenchedores (117 páginas, 4,8 MB).
- Correção sugerida: gravar o fluxo JPX original sem recodificar, ou limitar a extração ao tamanho exibido, e medir o tempo por página.
