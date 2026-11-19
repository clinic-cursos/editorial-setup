# Briefing e registro das imagens complementares

## Briefing de uma página

Um bloco por página, em `imagens/briefings.md`. Os seis campos são obrigatórios.

```text
Página: NN
Tema: <assunto da página em poucas palavras>
Conceito: <forma, textura, objeto simbólico ou composição abstrata que evoca o tema>
Troca por conceito mais abstrato: <conceito original e o que o substituiu, ou "Não houve">
Paleta: bordô #87082E, rosa claro #EAD4DB, marsala #955251, cinza #625E61 (valores em paleta.md)
Estilo: conceitual e clean, fundo claro, muito espaço vazio, sem sombra pesada
Proporção: <largura> x <altura> mm (<razão>:1), do `free_space.py`
Restrições: sem texto, número ou logotipo na imagem; sem rosto, pele, anatomia, procedimento nem produto
```

Texto de pedido para a ferramenta de imagem (monte a partir do briefing, em português ou inglês):

> Imagem conceitual e limpa, <conceito>, em tons de bordô, rosa claro, marsala e cinza sobre fundo claro. Composição abstrata, sem texto, sem letras, sem pessoas, sem rostos. Proporção <razão>:1, alta resolução.

Exemplos de troca por conceito mais abstrato:

| Página pede | Conceito entregue |
| --- | --- |
| Aplicação de toxina botulínica na testa | Linhas paralelas suaves que relaxam em curvas, em rosa e cinza |
| Preenchimento de sulco nasogeniano | Camadas translúcidas de rosa e bordô em ondas |
| Antes e depois de tratamento | Duas formas geométricas que se alinham, sem comparação visual |
| Frasco ou marca de produto | Esfera lisa em marsala sobre fundo cinza claro |

## Registro de cada imagem

Uma linha por imagem em `relatorios/imagens-registro.md`. O Editor-Chefe copia para a ficha do projeto (seção de imagens de IA) e para a nota editorial de uso de IA do livro, que fica na nota editorial e não na página da imagem.

| Página | Arquivo | Ferramenta | Data | Conceito | Troca de conceito | SHA-256 | Inserida |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NN | `imagens/pagina-NN.png` | ChatGPT ou Codex, geração nativa | AAAA-MM-DD | <uma frase> | <sim ou não> | <quando o ambiente calcula> | <sim, não ou retirada por paginação> |

Imagem gerada por IA tem direito de uso e identificação própria: diga na nota editorial que as imagens complementares são conceituais e geradas por IA. Fotografia clínica e material de terceiros não entram aqui.
